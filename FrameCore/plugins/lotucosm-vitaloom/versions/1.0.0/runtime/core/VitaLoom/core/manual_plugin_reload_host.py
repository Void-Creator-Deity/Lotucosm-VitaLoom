# -*- coding: utf-8 -*-
"""Qt-free manual hot-reload orchestration for L3 engine extensions.

This deep Module composes :class:`RuntimePluginHost` for candidate import,
registry facts, dependency ordering, and lifecycle callbacks, while reusing the
reload-plan authority for deterministic affected-closure transitions.  It has
no dependency on an Editor shell or legacy plugin interfaces.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.plugin_activation_contract import (
    PluginActivationContractError,
    parse_plugin_activation_metadata,
)
from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id, normalize_dependency_ids
from core.VitaLoom.project.plugin_host_lifecycle import (
    PluginHostCatalogEntry,
    normalize_plugin_provides,
)
from core.VitaLoom.project.plugin_host_reload import build_plugin_reload_plan


logger = get_logger("ManualPluginReloadHost")


class ManualPluginReloadHost:
    """Own candidate-first manual reload from preflight through exact report.

    ``RuntimePluginHost`` remains the registry/import/callback authority.  This
    Module adds the reload transaction order and failure truth needed by any
    concrete Host Adapter, including headless tools and the legacy editor.
    """

    _ALLOWED_SCOPES = frozenset(
        {RuntimePluginHost.SCOPE_OFFICIAL, RuntimePluginHost.SCOPE_USER}
    )

    def __init__(
        self,
        runtime_plugin_host: RuntimePluginHost,
        *,
        candidate_importer: Callable[[Path], tuple[str, Any]] | None = None,
        lifecycle_report_publisher: Callable[[Dict[str, Any]], None] | None = None,
    ) -> None:
        self.runtime_plugin_host = runtime_plugin_host
        self._candidate_importer = candidate_importer
        self._lifecycle_report_publisher = lifecycle_report_publisher
        self.last_reload_report: Dict[str, Any] = {
            "status": "not_run",
            "source": "hot_reload",
            "completed": {
                "deactivated": [],
                "activated": [],
                "registry_replaced": False,
            },
            "diagnostics": [],
        }

    @staticmethod
    def _json_fact(value: Mapping[str, Any]) -> Dict[str, Any]:
        return json.loads(
            json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        )

    def _new_report(self, plugin_id: str) -> Dict[str, Any]:
        host = self.runtime_plugin_host
        return {
            "status": "blocked",
            "source": "hot_reload",
            "target_plugin_id": plugin_id,
            "target_was_active": plugin_id in host.loaded_plugins,
            "candidate": None,
            "catalog": [],
            "affected_plugin_ids": [],
            "deactivate_plugin_ids": [],
            "activate_plugin_ids": [],
            "completed": {
                "deactivated": [],
                "activated": [],
                "registry_replaced": False,
            },
            "skipped": {"activation": []},
            "failed_action": None,
            "diagnostics": [],
            "rollback": {
                "status": "not_needed",
                "message": "no lifecycle callback has been executed",
            },
        }

    def _publish(self, report: Mapping[str, Any]) -> Dict[str, Any]:
        canonical = self._json_fact(report)
        self.last_reload_report = canonical
        lifecycle_fact = self._json_fact(canonical)
        self.runtime_plugin_host.last_lifecycle_report = lifecycle_fact
        if self._lifecycle_report_publisher is not None:
            self._lifecycle_report_publisher(self._json_fact(lifecycle_fact))
        return canonical

    def _block(
        self,
        report: Dict[str, Any],
        *,
        code: str,
        message: str,
        plugin_id: str,
        source: str = "",
        error: str = "",
    ) -> Dict[str, Any]:
        report["status"] = "blocked"
        report["diagnostics"].append(
            {
                "level": "error",
                "code": code,
                "message": message,
                "plugin_id": plugin_id,
                "source": source,
            }
        )
        if error:
            report["failed_action"] = {
                "action": "candidate_preflight",
                "plugin_id": plugin_id,
                "error": error,
            }
        return self._publish(report)

    def list_reloadable_plugins(self) -> List[str]:
        """Return active regular-file L3 extensions accepted by this Interface."""
        host = self.runtime_plugin_host
        result: List[str] = []
        for plugin_id in sorted(host.loaded_plugins):
            if plugin_id in host.protected_plugins:
                continue
            if host.plugin_scopes.get(plugin_id) not in self._ALLOWED_SCOPES:
                continue
            source = host.plugin_files.get(plugin_id, "")
            path = Path(source) if source else None
            if path is None or path.is_symlink() or not path.is_file():
                continue
            result.append(plugin_id)
        return result

    def _candidate_entry(
        self,
        *,
        plugin_id: str,
        candidate: Any,
        scope: str,
        file_path: Path,
        report: Dict[str, Any],
    ) -> tuple[PluginHostCatalogEntry, Dict[str, Any]] | Dict[str, Any]:
        try:
            candidate_info = candidate.get_plugin_info()
        except Exception as exc:
            logger.exception("candidate metadata failed: %s", plugin_id)
            return self._block(
                report,
                code="reload_candidate_metadata_failed",
                message=f"candidate metadata failed for {plugin_id}",
                plugin_id=plugin_id,
                source=str(file_path),
                error=type(exc).__name__,
            )
        if not isinstance(candidate_info, dict):
            return self._block(
                report,
                code="reload_candidate_metadata_invalid",
                message="candidate plugin info must be a mapping",
                plugin_id=plugin_id,
                source=str(file_path),
            )
        candidate_info = deepcopy(candidate_info)
        try:
            activation = parse_plugin_activation_metadata(
                candidate_info,
                plugin_id=plugin_id,
                source=str(file_path),
            )
        except PluginActivationContractError as exc:
            return self._block(
                report,
                code=exc.code,
                message=exc.message,
                plugin_id=plugin_id,
                source=str(file_path),
            )
        raw_dependencies = candidate_info.get("dependencies", [])
        if not isinstance(raw_dependencies, (list, tuple, set)):
            return self._block(
                report,
                code="reload_candidate_dependencies_invalid",
                message="candidate dependencies must be a sequence",
                plugin_id=plugin_id,
                source=str(file_path),
            )
        dependencies = normalize_dependency_ids(raw_dependencies)
        return (
            PluginHostCatalogEntry(
                plugin_id=plugin_id,
                scope=scope,
                source=str(file_path),
                version=str(candidate_info.get("version", "0.0.0") or "0.0.0"),
                description=str(candidate_info.get("description", "") or ""),
                provides=normalize_plugin_provides(candidate_info.get("provides", [])),
                dependencies=tuple(dependencies),
                protected=bool(candidate_info.get("protected", False)),
                activation_context=activation.kind,
                activation_context_explicit=activation.explicit,
            ),
            candidate_info,
        )

    def _replace_registry_entry(
        self,
        plugin_id: str,
        candidate: Any,
        *,
        dependencies: List[str],
        scope: str,
        file_path: Path,
        catalog_entry: PluginHostCatalogEntry,
        candidate_info: Mapping[str, Any],
    ) -> None:
        host = self.runtime_plugin_host
        host.plugin_registry[plugin_id] = candidate
        host.cache_plugin_metadata(
            plugin_id,
            candidate_info,
            source=file_path,
        )
        host.plugin_dependencies[plugin_id] = list(dependencies)
        host.plugin_scopes[plugin_id] = scope
        host.plugin_files[plugin_id] = str(file_path)
        host.protected_plugins.discard(plugin_id)
        host.resolve_dependencies()

    def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Candidate-first manual hot reload for one L3 engine extension."""
        host = self.runtime_plugin_host
        plugin_id = canonical_plugin_id(str(plugin_name))
        report = self._new_report(plugin_id)
        current = host.plugin_registry.get(plugin_id)
        if current is None:
            return self._block(
                report,
                code="reload_target_not_found",
                message=f"reload target {plugin_id} is not present in the runtime catalog",
                plugin_id=plugin_id,
            )

        scope = host.plugin_scopes.get(plugin_id, host.SCOPE_UNKNOWN)
        source = host.plugin_files.get(plugin_id, "")
        if scope not in self._ALLOWED_SCOPES:
            return self._block(
                report,
                code="reload_scope_forbidden",
                message=f"scope {scope} must use its authoritative lifecycle path",
                plugin_id=plugin_id,
                source=source,
            )
        if plugin_id in host.protected_plugins:
            return self._block(
                report,
                code="reload_protected_plugin",
                message=f"protected plugin {plugin_id} cannot be hot reloaded",
                plugin_id=plugin_id,
                source=source,
            )
        if not source:
            return self._block(
                report,
                code="reload_source_missing",
                message=f"plugin {plugin_id} has no registered source",
                plugin_id=plugin_id,
            )
        file_path = Path(source)
        if file_path.is_symlink() or not file_path.is_file():
            return self._block(
                report,
                code="reload_source_not_regular_file",
                message=f"plugin source is not a regular file: {file_path}",
                plugin_id=plugin_id,
                source=str(file_path),
            )

        try:
            candidate_importer = (
                self._candidate_importer or host.instantiate_plugin_from_file
            )
            discovered_id, candidate = candidate_importer(file_path)
        except Exception as exc:
            logger.exception("candidate import failed: %s", plugin_id)
            return self._block(
                report,
                code="reload_candidate_import_failed",
                message=f"candidate import failed for {plugin_id}",
                plugin_id=plugin_id,
                source=str(file_path),
                error=type(exc).__name__,
            )
        if discovered_id != plugin_id:
            return self._block(
                report,
                code="reload_candidate_id_mismatch",
                message=f"candidate id {discovered_id} does not match target {plugin_id}",
                plugin_id=plugin_id,
                source=str(file_path),
            )

        candidate_preflight = self._candidate_entry(
            plugin_id=plugin_id,
            candidate=candidate,
            scope=scope,
            file_path=file_path,
            report=report,
        )
        if isinstance(candidate_preflight, dict):
            return candidate_preflight
        candidate_entry, candidate_info = candidate_preflight
        dependencies = list(candidate_entry.dependencies)
        plan = build_plugin_reload_plan(
            host.catalog_entries(),
            target_plugin_id=plugin_id,
            candidate=candidate_entry,
            active_plugin_ids=set(host.loaded_plugins),
        )
        report.update(plan.to_dict())
        report["source"] = "hot_reload"
        report["completed"] = {
            "deactivated": [],
            "activated": [],
            "registry_replaced": False,
        }
        report["skipped"] = {"activation": []}
        report["failed_action"] = None
        report["rollback"] = {
            "status": "not_needed",
            "message": "no lifecycle callback has been executed",
        }
        if not plan.ok:
            report["status"] = "blocked"
            return self._publish(report)

        if not plan.target_was_active:
            self._replace_registry_entry(
                plugin_id,
                candidate,
                dependencies=dependencies,
                scope=scope,
                file_path=file_path,
                catalog_entry=candidate_entry,
                candidate_info=candidate_info,
            )
            report["completed"]["registry_replaced"] = True
            report["status"] = "settled"
            logger.info("inactive plugin registry replacement settled: %s", plugin_id)
            return self._publish(report)

        for current_id in plan.deactivate_plugin_ids:
            if not host.unload_plugin(current_id):
                report["status"] = (
                    "partial" if report["completed"]["deactivated"] else "failed"
                )
                report["failed_action"] = {
                    "action": "deactivate",
                    "plugin_id": current_id,
                }
                report["rollback"] = {
                    "status": "not_available",
                    "message": (
                        "plugin callbacks may already have changed runtime state; "
                        "generic rollback is not claimed"
                    ),
                }
                return self._publish(report)
            report["completed"]["deactivated"].append(current_id)

        self._replace_registry_entry(
            plugin_id,
            candidate,
            dependencies=dependencies,
            scope=scope,
            file_path=file_path,
            catalog_entry=candidate_entry,
            candidate_info=candidate_info,
        )
        report["completed"]["registry_replaced"] = True

        failed_activation: set[str] = set()
        skipped_activation: set[str] = set()
        for current_id in plan.activate_plugin_ids:
            blocked_by = sorted(
                set(host.plugin_dependencies.get(current_id, []))
                & (failed_activation | skipped_activation)
            )
            if blocked_by:
                skipped_activation.add(current_id)
                report["skipped"]["activation"].append(
                    {"plugin_id": current_id, "blocked_by": blocked_by}
                )
                continue
            plugin = host.plugin_registry.get(current_id)
            if plugin is None:
                failed_activation.add(current_id)
                if report["failed_action"] is None:
                    report["failed_action"] = {
                        "action": "activate",
                        "plugin_id": current_id,
                        "error": "plugin_registry_missing",
                    }
                continue
            try:
                host.load_plugin(plugin, plugin_id=current_id)
                host.loaded_plugins[current_id] = plugin
                host.failed_plugins.pop(current_id, None)
                report["completed"]["activated"].append(current_id)
            except Exception as exc:
                logger.exception("reloaded plugin activation failed: %s", current_id)
                host.loaded_plugins.pop(current_id, None)
                host.failed_plugins[current_id] = str(exc)
                failed_activation.add(current_id)
                if report["failed_action"] is None:
                    report["failed_action"] = {
                        "action": "activate",
                        "plugin_id": current_id,
                        "error": type(exc).__name__,
                    }

        if failed_activation or skipped_activation:
            report["status"] = "partial"
            report["rollback"] = {
                "status": "not_available",
                "message": (
                    "the previous callback closure was already deactivated; "
                    "manual repair or process restart may be required"
                ),
            }
        else:
            report["status"] = "settled"
            report["rollback"] = {
                "status": "not_needed",
                "message": "candidate and affected dependents reached the planned active state",
            }
        logger.info("plugin reload completed: %s status=%s", plugin_id, report["status"])
        return self._publish(report)
