# -*- coding: utf-8 -*-
"""Qt-free Project World orchestration for plugins nested under VitaLoom.

The L1 ``lotucosm-vitaloom`` engine plugin is also a downstream plugin Host.
This deep Module owns only Project-scoped L4 addon state and orchestration.  It
composes :class:`RuntimePluginHost` for registry/import/callback execution and
reuses the lifecycle, activation, and operator authorities already present in
the versioned runtime.  It does not know about PyQt, EditorKernel, LayoutManager,
or the legacy ``PluginLoader`` Adapter.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any, Callable, Dict, List, Mapping

from core.VitaLoom.core.plugin_activation_contract import (
    PluginActivationContractError,
    parse_plugin_activation_metadata,
    validate_plugin_activation_context_pair,
)
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
from core.VitaLoom.kernel.plugin_ids import normalize_dependency_ids
from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons
from core.VitaLoom.project.plugin_host_operator import (
    PluginHostOperatorError,
    build_plugin_host_inspection,
    canonical_project_path,
    list_plugin_host_recoveries,
    read_project_lifecycle_input,
    validate_plugin_host_recovery,
)


LifecycleExecutor = Callable[..., Dict[str, Any]]
LifecycleReportResolver = Callable[[], Mapping[str, Any]]
LifecycleReportPublisher = Callable[[Dict[str, Any]], None]
PathResolver = Callable[[], str | Path]
RuntimeVersionResolver = Callable[[], str]
ProjectTargetResolver = Callable[..., set[str]]
BooleanResolver = Callable[[], bool]


class ProjectScopedPluginHost:
    """Own Project World addon discovery, switching, sync, and recovery.

    The Interface receives only the Qt-free runtime Host and narrow resolver
    seams.  A headless caller can use all defaults.  A concrete editor Adapter
    may inject lifecycle execution to settle its own UI contributions after the
    Qt-free callback transition.
    """

    def __init__(
        self,
        runtime_plugin_host: RuntimePluginHost,
        *,
        runtime_version_resolver: RuntimeVersionResolver | None = None,
        repo_root_resolver: PathResolver | None = None,
        eager_mode_resolver: BooleanResolver | None = None,
        player_mode_resolver: BooleanResolver | None = None,
        active_plugin_ids_resolver: ProjectTargetResolver | None = None,
        player_plugin_ids_resolver: ProjectTargetResolver | None = None,
        lifecycle_executor: LifecycleExecutor | None = None,
        lifecycle_report_resolver: LifecycleReportResolver | None = None,
        lifecycle_report_publisher: LifecycleReportPublisher | None = None,
    ) -> None:
        self.runtime_plugin_host = runtime_plugin_host
        self._runtime_version_resolver = (
            runtime_version_resolver or self._default_runtime_version
        )
        self._repo_root_resolver = repo_root_resolver or self._default_repo_root
        self._eager_mode_resolver = eager_mode_resolver or self._default_eager_mode
        self._player_mode_resolver = player_mode_resolver or self._default_player_mode
        self._active_plugin_ids_resolver = active_plugin_ids_resolver
        self._player_plugin_ids_resolver = player_plugin_ids_resolver
        self._lifecycle_executor = (
            lifecycle_executor or runtime_plugin_host.execute_lifecycle_target
        )
        self._lifecycle_report_resolver = lifecycle_report_resolver
        self._lifecycle_report_publisher = lifecycle_report_publisher

        self.embedded_plugin_names: set[str] = set()
        self.operator_project_path = ""
        self.embedded_catalog_project_path = ""
        self._addon_runtime_receipts: list[dict[str, Any]] = []
        self.last_project_addon_discovery_report: Dict[str, Any] = {
            "status": "not_run",
            "sources": [],
            "diagnostics": [],
        }
        self.last_operator_recovery_report: Dict[str, Any] = {
            "status": "not_run",
            "diagnostics": [],
        }
        self._last_lifecycle_report: Dict[str, Any] = {
            "status": "not_run",
            "completed": {"deactivated": [], "activated": []},
            "diagnostics": [],
        }

    @staticmethod
    def _default_runtime_version() -> str:
        from core.VitaLoom.core.bundle_paths import editor_version

        return editor_version()

    @staticmethod
    def _default_repo_root() -> str | Path:
        from core.VitaLoom.core.bundle_paths import resource_root

        return resource_root()

    @staticmethod
    def _default_eager_mode() -> bool:
        from core.VitaLoom.project.plugin_activation import eager_load_all_plugins

        return eager_load_all_plugins()

    @staticmethod
    def _default_player_mode() -> bool:
        from core.VitaLoom.project.plugin_activation import is_player_mode

        return is_player_mode()

    def _active_target(self, project_data: Dict[str, Any], repo_root: str | Path) -> set[str]:
        resolver = self._active_plugin_ids_resolver
        if resolver is None:
            from core.VitaLoom.project import plugin_activation

            resolver = plugin_activation.collect_active_plugin_ids
        return set(resolver(project_data, repo_root=repo_root))

    def _player_target(self, project_data: Dict[str, Any], repo_root: str | Path) -> set[str]:
        resolver = self._player_plugin_ids_resolver
        if resolver is None:
            from core.VitaLoom.project import plugin_activation

            resolver = plugin_activation.collect_player_plugin_ids
        return set(resolver(project_data, repo_root=repo_root))

    @property
    def last_lifecycle_report(self) -> Dict[str, Any]:
        if self._lifecycle_report_resolver is not None:
            report = self._lifecycle_report_resolver()
            if isinstance(report, dict):
                return report
            return dict(report)
        return self._last_lifecycle_report

    def _publish_lifecycle_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        self._last_lifecycle_report = report
        if self._lifecycle_report_publisher is not None:
            self._lifecycle_report_publisher(report)
        return report

    def _execute_lifecycle_target(
        self,
        target: set[str],
        *,
        source: str,
        allow_deactivate: bool,
    ) -> Dict[str, Any]:
        report = self._lifecycle_executor(
            set(target),
            source=source,
            allow_deactivate=allow_deactivate,
        )
        return self._publish_lifecycle_report(report)

    def _build_addon_runtime_receipts(
        self, lifecycle: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        """Bind discovered addon digests to the actual lifecycle result."""
        discovery = self.last_project_addon_discovery_report
        sources = discovery.get("sources", []) if isinstance(discovery, Mapping) else []
        completed = lifecycle.get("completed", {}) if isinstance(lifecycle, Mapping) else {}
        activated = set(completed.get("activated", [])) if isinstance(completed, Mapping) else set()
        deactivated = set(completed.get("deactivated", [])) if isinstance(completed, Mapping) else set()
        loaded = set(self.runtime_plugin_host.loaded_plugins)
        receipts: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            plugin_id = str(source.get("plugin_id") or "")
            if not plugin_id:
                continue
            if plugin_id in activated or plugin_id in loaded:
                outcome = "runtime_loaded"
                action = "activate" if plugin_id in activated else "observe"
            elif plugin_id in deactivated:
                outcome = "runtime_unloaded"
                action = "deactivate"
            else:
                outcome = "declared_not_loaded"
                action = "observe"
            receipts.append({
                "path": str(source.get("entry_path") or ""),
                "kind": "project_addon",
                "plugin_id": plugin_id,
                "action": action,
                "outcome": outcome,
                "manifest_sha256": str(source.get("manifest_sha256") or ""),
                "entry_sha256": str(source.get("entry_sha256") or ""),
                "project_path": self.operator_project_path,
                "lifecycle_status": str(lifecycle.get("status") or "unknown"),
                "failed_action": dict(lifecycle.get("failed_action") or {})
                if isinstance(lifecycle.get("failed_action"), Mapping)
                else None,
            })
        return receipts

    def lifecycle_evidence(self) -> dict[str, Any]:
        """Return copy-safe project addon lifecycle evidence for checkpoint hosts."""
        evidence = {
            "schema_version": 1,
            "project_path": self.operator_project_path,
            "discovery": dict(self.last_project_addon_discovery_report),
            "lifecycle": dict(self.last_lifecycle_report),
            "addon_runtime_receipts": [dict(item) for item in self._addon_runtime_receipts],
        }
        evidence["digest"] = hashlib.sha256(
            json.dumps(
                {**evidence, "digest": ""},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return evidence

    def _validate_discovered_source_digests(self) -> list[dict[str, Any]]:
        report = self.last_project_addon_discovery_report
        sources = report.get("sources", []) if isinstance(report, Mapping) else []
        diagnostics: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            entry = Path(str(source.get("entry_path") or ""))
            manifest = Path(str(source.get("manifest_path") or ""))
            try:
                actual_entry = hashlib.sha256(entry.read_bytes()).hexdigest()
                actual_manifest = hashlib.sha256(manifest.read_bytes()).hexdigest()
            except OSError as exc:
                diagnostics.append({
                    "level": "error",
                    "code": "addon_source_unreadable",
                    "message": f"addon source is no longer readable: {type(exc).__name__}",
                    "plugin_id": str(source.get("plugin_id") or ""),
                    "source": str(entry),
                })
                continue
            if actual_entry != str(source.get("entry_sha256") or "") or actual_manifest != str(source.get("manifest_sha256") or ""):
                diagnostics.append({
                    "level": "error",
                    "code": "addon_source_digest_changed",
                    "message": "addon manifest or entry source changed after discovery",
                    "plugin_id": str(source.get("plugin_id") or ""),
                    "source": str(entry),
                })
        return diagnostics

    def embedded_plugin_ids(self) -> set[str]:
        host = self.runtime_plugin_host
        return {
            name
            for name, scope in host.plugin_scopes.items()
            if scope == host.SCOPE_EMBEDDED and name in host.plugin_registry
        }

    def clear_embedded_plugins(self) -> Dict[str, Any]:
        """Deactivate L4 addons in authority order, then remove their catalog."""

        host = self.runtime_plugin_host
        embedded = set(self.embedded_plugin_names) | self.embedded_plugin_ids()
        if not embedded:
            return {
                "status": "settled",
                "source": "project_addon_clear",
                "completed": {"deactivated": [], "activated": []},
                "diagnostics": [],
                "failed_action": None,
            }
        target = set(host.loaded_plugins).difference(embedded)
        report = self._execute_lifecycle_target(
            target,
            source="project_addon_clear",
            allow_deactivate=True,
        )
        if report.get("status") != "settled":
            return report
        for name in sorted(embedded):
            host.plugin_registry.pop(name, None)
            host.plugin_dependencies.pop(name, None)
            host.plugin_scopes.pop(name, None)
            host.plugin_files.pop(name, None)
            host.plugin_metadata.pop(name, None)
            if name in host.plugin_order:
                host.plugin_order.remove(name)
            host.protected_plugins.discard(name)
        self.embedded_plugin_names.clear()
        return report

    def scan_project_addons(self, project_path: str | Path | None) -> Dict[str, Any]:
        """Validate and import one Project World's manifest-authorized L4 addons."""

        host = self.runtime_plugin_host
        self.operator_project_path = canonical_project_path(project_path)
        if not project_path:
            clear_report = self.clear_embedded_plugins()
            report = {
                "status": (
                    "ready" if clear_report.get("status") == "settled" else "failed"
                ),
                "project_path": "",
                "sources": [],
                "diagnostics": list(clear_report.get("diagnostics", [])),
                "clear_report": clear_report,
            }
            self.last_project_addon_discovery_report = report
            if report["status"] == "ready":
                self.embedded_catalog_project_path = ""
            return report

        discovery = discover_project_addons(
            project_path,
            runtime_version=self._runtime_version_resolver(),
        )
        report = discovery.to_dict()
        if not discovery.ok:
            self._addon_runtime_receipts = []
            self.last_project_addon_discovery_report = report
            return report

        candidates: Dict[str, IRuntimePlugin] = {}
        candidate_dependencies: Dict[str, List[str]] = {}
        candidate_files: Dict[str, str] = {}
        candidate_metadata: Dict[str, Dict[str, Any]] = {}
        diagnostics: List[Dict[str, Any]] = []
        for source_fact in discovery.sources:
            existing_scope = host.plugin_scopes.get(source_fact.plugin_id)
            if (
                source_fact.plugin_id in host.plugin_registry
                and existing_scope != host.SCOPE_EMBEDDED
            ):
                diagnostics.append(
                    {
                        "level": "error",
                        "code": "addon_plugin_id_collision",
                        "message": (
                            f"project addon {source_fact.plugin_id} collides with "
                            f"{existing_scope or host.SCOPE_UNKNOWN}"
                        ),
                        "plugin_id": source_fact.plugin_id,
                        "source": str(source_fact.entry_path),
                    }
                )
                continue
            try:
                discovered_name, plugin_instance = host.instantiate_plugin_from_file(
                    source_fact.entry_path
                )
                info = plugin_instance.get_plugin_info()
                code_activation_metadata = parse_plugin_activation_metadata(
                    info,
                    plugin_id=source_fact.plugin_id,
                    source=str(source_fact.entry_path),
                )
                manifest_activation_metadata = parse_plugin_activation_metadata(
                    {"activation_context": source_fact.activation_context}
                    if source_fact.activation_context_explicit
                    else {},
                    plugin_id=source_fact.plugin_id,
                    source=str(source_fact.manifest_path),
                )
                validate_plugin_activation_context_pair(
                    manifest_activation_metadata,
                    code_activation_metadata,
                )
                discovered_dependencies = tuple(
                    normalize_dependency_ids(info.get("dependencies", []))
                )
                discovered_version = str(info.get("version", "") or "")
                if (
                    discovered_name != source_fact.plugin_id
                    or discovered_version != source_fact.version
                    or discovered_dependencies != source_fact.dependencies
                ):
                    raise ValueError(
                        "manifest id/version/dependencies do not match get_plugin_info"
                    )
                candidates[source_fact.plugin_id] = plugin_instance
                candidate_dependencies[source_fact.plugin_id] = list(
                    source_fact.dependencies
                )
                candidate_files[source_fact.plugin_id] = str(source_fact.entry_path)
                candidate_metadata[source_fact.plugin_id] = dict(info)
            except PluginActivationContractError as exc:
                diagnostics.append(
                    {
                        "level": "error",
                        "code": exc.code,
                        "message": exc.message,
                        "plugin_id": source_fact.plugin_id,
                        "source": str(source_fact.entry_path),
                        "details": dict(exc.details),
                    }
                )
            except Exception as exc:
                diagnostics.append(
                    {
                        "level": "error",
                        "code": "addon_metadata_mismatch",
                        "message": str(exc),
                        "plugin_id": source_fact.plugin_id,
                        "source": str(source_fact.entry_path),
                    }
                )

        if diagnostics:
            report["status"] = "blocked"
            report["sources"] = []
            report["diagnostics"] = sorted(
                diagnostics,
                key=lambda item: (item["code"], item["plugin_id"], item["source"]),
            )
            self.last_project_addon_discovery_report = report
            self._addon_runtime_receipts = []
            return report

        clear_report = self.clear_embedded_plugins()
        if clear_report.get("status") != "settled":
            report["status"] = "failed"
            report["diagnostics"] = list(clear_report.get("diagnostics", []))
            report["clear_report"] = clear_report
            self.last_project_addon_discovery_report = report
            self._addon_runtime_receipts = []
            return report

        for plugin_name in sorted(candidates):
            host.plugin_registry[plugin_name] = candidates[plugin_name]
            host.cache_plugin_metadata(
                plugin_name,
                candidate_metadata[plugin_name],
                source=candidate_files[plugin_name],
            )
            host.plugin_dependencies[plugin_name] = candidate_dependencies[plugin_name]
            host.plugin_scopes[plugin_name] = host.SCOPE_EMBEDDED
            host.plugin_files[plugin_name] = candidate_files[plugin_name]
            host.protected_plugins.discard(plugin_name)
        self.embedded_plugin_names.clear()
        self.embedded_plugin_names.update(candidates)
        self._addon_runtime_receipts = []
        host.resolve_dependencies()
        report["status"] = "ready"
        report["imported_plugin_ids"] = sorted(candidates)
        report["clear_report"] = clear_report
        self.embedded_catalog_project_path = self.operator_project_path
        self.last_project_addon_discovery_report = report
        return report

    def sync_plugins_for_project(
        self,
        project_data: Dict[str, Any],
        *,
        repo_root: str | Path | None = None,
    ) -> Dict[str, Any]:
        """Apply the current Project World's downstream-extension lifecycle plan."""

        if self._eager_mode_resolver():
            return self._publish_lifecycle_report(
                {
                    "status": "skipped_eager_mode",
                    "source": "project_sync",
                    "completed": {"deactivated": [], "activated": []},
                    "diagnostics": [],
                    "failed_action": None,
                }
            )
        if not isinstance(project_data, dict):
            return self._publish_lifecycle_report(
                {
                    "status": "blocked",
                    "source": "project_sync",
                    "completed": {"deactivated": [], "activated": []},
                    "diagnostics": [
                        {
                            "level": "error",
                            "code": "project_data_invalid",
                            "message": "project_data must be an object",
                            "plugin_id": "",
                            "source": "",
                        }
                    ],
                    "failed_action": None,
                }
            )
        if not repo_root:
            repo_root = self._repo_root_resolver()
        source_diagnostics = self._validate_discovered_source_digests()
        if source_diagnostics:
            return self._publish_lifecycle_report({
                "status": "blocked",
                "source": "project_sync",
                "completed": {"deactivated": [], "activated": []},
                "diagnostics": source_diagnostics,
                "failed_action": None,
                "addon_runtime_receipts": [],
            })
        if self._player_mode_resolver():
            target = self._player_target(project_data, repo_root)
        else:
            target = self._active_target(project_data, repo_root)
        target |= self.embedded_plugin_ids()
        lifecycle = self._execute_lifecycle_target(
            target,
            source="project_sync",
            allow_deactivate=True,
        )
        lifecycle["addon_runtime_receipts"] = self._build_addon_runtime_receipts(lifecycle)
        self._addon_runtime_receipts = [
            dict(item) for item in lifecycle["addon_runtime_receipts"]
        ]
        return self._publish_lifecycle_report(lifecycle)

    def inspect_plugin_host(self, project_path: str = "") -> Dict[str, Any]:
        """Project the current downstream Host into one operator report."""

        host = self.runtime_plugin_host
        inspection = build_plugin_host_inspection(
            project_path=self.operator_project_path,
            embedded_catalog_project_path=self.embedded_catalog_project_path,
            catalog_entries=host.catalog_entries(),
            active_plugin_ids=set(host.loaded_plugins),
            failed_plugins=host.failed_plugins,
            discovery_report=self.last_project_addon_discovery_report,
            lifecycle_report=self.last_lifecycle_report,
        )
        asserted_project = canonical_project_path(project_path)
        if asserted_project and asserted_project != inspection["project_path"]:
            raise PluginHostOperatorError(
                "plugin_host_project_mismatch",
                "Inspection must target the exact current Project World",
                details={
                    "current_project_path": inspection["project_path"],
                    "project_path": asserted_project,
                },
            )
        return inspection

    def list_plugin_host_recoveries(self, project_path: str = "") -> Dict[str, Any]:
        """List current recovery work without invoking plugin callbacks."""

        return list_plugin_host_recoveries(self.inspect_plugin_host(project_path))

    def resolve_plugin_host_recovery(
        self,
        *,
        project_path: str,
        report_id: str,
        action: str,
        operator_confirmation: str,
    ) -> Dict[str, Any]:
        """Execute one validated normal lifecycle retry, never a force action."""

        before = self.inspect_plugin_host()
        validate_plugin_host_recovery(
            before,
            project_path=project_path,
            report_id=report_id,
            action=action,
            operator_confirmation=operator_confirmation,
        )
        canonical_project, project_data = read_project_lifecycle_input(project_path)
        if canonical_project != before["project_path"]:
            raise PluginHostOperatorError(
                "plugin_host_project_mismatch",
                "Resolved Project World no longer matches the current Host report",
                details={
                    "current_project_path": before["project_path"],
                    "project_path": canonical_project,
                },
            )

        discovery = self.scan_project_addons(canonical_project)
        if discovery.get("status") != "ready":
            after = self.inspect_plugin_host()
            result = {
                "status": after["status"],
                "action": action,
                "project_path": canonical_project,
                "before_report_id": before["report_id"],
                "discovery": discovery,
                "lifecycle": None,
                "after": after,
            }
            self.last_operator_recovery_report = result
            return result

        lifecycle = self.sync_plugins_for_project(project_data)
        after = self.inspect_plugin_host()
        result = {
            "status": after["status"],
            "action": action,
            "project_path": canonical_project,
            "before_report_id": before["report_id"],
            "discovery": discovery,
            "lifecycle": lifecycle,
            "after": after,
        }
        self.last_operator_recovery_report = result
        return result


__all__ = ["ProjectScopedPluginHost"]
