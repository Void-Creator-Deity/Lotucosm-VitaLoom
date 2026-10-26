# -*- coding: utf-8 -*-
"""Qt-free composition root for plugins nested under the VitaLoom engine plugin.

``lotucosm-vitaloom`` is the sole L1 FrameCore engine/product plugin and is
itself a downstream plugin-host framework.  This deep Module composes runtime
execution, Project World addon orchestration, and manual reload over exactly
one :class:`RuntimePluginHost`.  Concrete UI Hosts attach only through narrow
resolver and Adapter seams; no editor shell or legacy plugin Interface is
required here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.manual_plugin_reload_host import ManualPluginReloadHost
from core.VitaLoom.core.runtime_plugin_host import (
    RuntimePluginHost,
    RuntimePluginHostAdapter,
)
from core.VitaLoom.project.project_scoped_plugin_host import ProjectScopedPluginHost


logger = get_logger("NestedPluginHost")

PathResolver = Callable[[], str | Path]
BooleanResolver = Callable[[], bool]
BootstrapPluginIdsResolver = Callable[[str | Path], set[str]]
LifecycleObserver = Callable[[Dict[str, Any]], None]
CandidateImporter = Callable[[Path], tuple[str, Any]]
ProjectTargetResolver = Callable[..., set[str]]
RuntimeVersionResolver = Callable[[], str]


class NestedPluginHost:
    """Compose all downstream plugin Host authorities over one runtime registry.

    The Interface owns sub-Host construction, bootstrap target selection, and
    canonical lifecycle-report publication.  ``PluginLoader`` and future UI
    Hosts remain concrete Adapters at the activation-context and post-transition
    seams rather than composition authorities.
    """

    SCOPE_CORE = RuntimePluginHost.SCOPE_CORE
    SCOPE_OFFICIAL = RuntimePluginHost.SCOPE_OFFICIAL
    SCOPE_USER = RuntimePluginHost.SCOPE_USER
    SCOPE_EMBEDDED = RuntimePluginHost.SCOPE_EMBEDDED
    SCOPE_UNKNOWN = RuntimePluginHost.SCOPE_UNKNOWN
    _SCOPE_PRIORITY = {
        SCOPE_UNKNOWN: 0,
        SCOPE_EMBEDDED: 1,
        SCOPE_USER: 2,
        SCOPE_OFFICIAL: 3,
        SCOPE_CORE: 4,
    }

    def __init__(
        self,
        *,
        activation_context_resolver: Callable[[Mapping[str, Any]], object] | None = None,
        runtime_adapter: RuntimePluginHostAdapter | None = None,
        runtime_version_resolver: RuntimeVersionResolver | None = None,
        repo_root_resolver: PathResolver | None = None,
        eager_mode_resolver: BooleanResolver | None = None,
        player_mode_resolver: BooleanResolver | None = None,
        bootstrap_plugin_ids_resolver: BootstrapPluginIdsResolver | None = None,
        active_plugin_ids_resolver: ProjectTargetResolver | None = None,
        player_plugin_ids_resolver: ProjectTargetResolver | None = None,
        after_lifecycle_transition: LifecycleObserver | None = None,
        candidate_importer: CandidateImporter | None = None,
    ) -> None:
        self._repo_root_resolver = repo_root_resolver or self._default_repo_root
        self._eager_mode_resolver = eager_mode_resolver or self._default_eager_mode
        self._player_mode_resolver = player_mode_resolver or self._default_player_mode
        self._bootstrap_plugin_ids_resolver = (
            bootstrap_plugin_ids_resolver or self._default_bootstrap_plugin_ids
        )
        self._after_lifecycle_transition = after_lifecycle_transition

        self.runtime_plugin_host = RuntimePluginHost(
            activation_context_resolver=activation_context_resolver,
            adapter=runtime_adapter,
        )
        self._last_lifecycle_report = self.runtime_plugin_host.last_lifecycle_report
        self.manual_plugin_reload_host = ManualPluginReloadHost(
            self.runtime_plugin_host,
            candidate_importer=candidate_importer,
            lifecycle_report_publisher=self._publish_lifecycle_report,
        )
        self.project_scoped_plugin_host = ProjectScopedPluginHost(
            self.runtime_plugin_host,
            runtime_version_resolver=runtime_version_resolver,
            repo_root_resolver=self._repo_root_resolver,
            eager_mode_resolver=self._eager_mode_resolver,
            player_mode_resolver=self._player_mode_resolver,
            active_plugin_ids_resolver=active_plugin_ids_resolver,
            player_plugin_ids_resolver=player_plugin_ids_resolver,
            lifecycle_executor=self.execute_lifecycle_target,
            lifecycle_report_resolver=lambda: self.last_lifecycle_report,
            lifecycle_report_publisher=self._publish_lifecycle_report,
        )

        # Compatibility observations deliberately alias the one runtime Host.
        self.plugin_registry = self.runtime_plugin_host.plugin_registry
        self.loaded_plugins = self.runtime_plugin_host.loaded_plugins
        self.plugin_dependencies = self.runtime_plugin_host.plugin_dependencies
        self.plugin_order = self.runtime_plugin_host.plugin_order
        self.failed_plugins = self.runtime_plugin_host.failed_plugins
        self.discovery_errors = self.runtime_plugin_host.discovery_errors
        self.plugin_scopes = self.runtime_plugin_host.plugin_scopes
        self.plugin_files = self.runtime_plugin_host.plugin_files
        self.protected_plugins = self.runtime_plugin_host.protected_plugins
        self.scope_overrides = self.runtime_plugin_host.scope_overrides

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

    @staticmethod
    def _default_bootstrap_plugin_ids(repo_root: str | Path) -> set[str]:
        from core.VitaLoom.project.plugin_activation import get_bootstrap_plugin_ids

        return set(get_bootstrap_plugin_ids(repo_root))

    @property
    def last_lifecycle_report(self) -> Dict[str, Any]:
        return self._last_lifecycle_report

    @last_lifecycle_report.setter
    def last_lifecycle_report(self, report: Dict[str, Any]) -> None:
        self._publish_lifecycle_report(report)

    @property
    def last_reload_report(self) -> Dict[str, Any]:
        return self.manual_plugin_reload_host.last_reload_report

    @last_reload_report.setter
    def last_reload_report(self, report: Dict[str, Any]) -> None:
        self.manual_plugin_reload_host.last_reload_report = report

    def _publish_lifecycle_report(self, report: Dict[str, Any]) -> None:
        """Synchronize one lifecycle fact without replaying concrete Adapter work."""

        self._last_lifecycle_report = report
        self.runtime_plugin_host.last_lifecycle_report = report

    def execute_lifecycle_target(
        self,
        target: set[str],
        *,
        source: str,
        allow_deactivate: bool,
    ) -> Dict[str, Any]:
        """Execute one runtime transition and notify the concrete Host once."""

        report = self.runtime_plugin_host.execute_lifecycle_target(
            set(target),
            source=source,
            allow_deactivate=allow_deactivate,
        )
        self._publish_lifecycle_report(report)
        if self._after_lifecycle_transition is not None:
            self._after_lifecycle_transition(report)
        return report

    def shutdown_plugins(self) -> Dict[str, Any]:
        """Publish the Runtime Host shutdown fact and notify concrete Hosts once."""

        report = self.runtime_plugin_host.shutdown_plugins()
        self._publish_lifecycle_report(report)
        if (
            report.get("transition_attempted")
            and self._after_lifecycle_transition is not None
        ):
            self._after_lifecycle_transition(report)
        return report

    def load_from_directories(
        self,
        dirs: Iterable[str | Path],
        *,
        force_all: bool = False,
    ) -> Dict[str, Any]:
        """Discover one direct source set and activate its discovered plugins.

        This compatibility entry is used by callers that explicitly provide a
        plugin directory.  Discovery and activation remain separate; callers
        use the lifecycle synchronization entry to activate a target set.
        """

        materialized = list(dirs)
        logger.info("Scanning plugin directories: %s", materialized)
        for dir_path in materialized:
            path = Path(dir_path)
            if path.exists():
                self.runtime_plugin_host.scan_directory(path, self.SCOPE_UNKNOWN)
            else:
                logger.warning("Plugin directory does not exist: %s", dir_path)
        return self.finalize_loading(force_all=force_all)

    def load_from_layered_directories(
        self,
        layered_dirs: Mapping[str, Iterable[str | Path]],
    ) -> Dict[str, Any]:
        """Discover layered sources with runtime scope-priority semantics."""

        logger.info("Scanning layered plugin directories: %s", layered_dirs)
        for scope, dirs in layered_dirs.items():
            normalized_scope = (
                scope if scope in self._SCOPE_PRIORITY else self.SCOPE_UNKNOWN
            )
            for dir_path in dirs:
                path = Path(dir_path)
                if path.exists():
                    self.runtime_plugin_host.scan_directory(path, normalized_scope)
                else:
                    logger.warning(
                        "Plugin directory does not exist: scope=%s path=%s",
                        normalized_scope,
                        dir_path,
                    )
        return self.finalize_loading()

    def finalize_loading(self, *, force_all: bool = False) -> Dict[str, Any]:
        """Resolve dependencies and preserve eager/Player/bootstrap target rules."""

        from core.VitaLoom.project.plugin_activation import (
            PLAYER_EDITOR_PACKAGE_ALLOWLIST,
            expand_with_plugin_dependencies,
        )

        host = self.runtime_plugin_host
        host.resolve_dependencies()
        if force_all or self._eager_mode_resolver():
            target = set(host.plugin_registry)
        elif self._player_mode_resolver():
            target = {
                plugin_id
                for plugin_id in PLAYER_EDITOR_PACKAGE_ALLOWLIST
                if plugin_id in host.plugin_registry
            }
            target = expand_with_plugin_dependencies(target, host.plugin_dependencies)
        else:
            target = set(self._bootstrap_plugin_ids_resolver(self._repo_root_resolver()))
            target = expand_with_plugin_dependencies(target, host.plugin_dependencies)

        report = self.execute_lifecycle_target(
            set(target),
            source="activation_only",
            allow_deactivate=False,
        )
        logger.info(
            "Plugin discovery completed: registered=%s activated=%s discovery_errors=%s",
            len(host.plugin_registry),
            len(report.get("completed", {}).get("activated", [])),
            len(host.discovery_errors),
        )
        return report

    def set_scope_overrides(self, overrides: Mapping[str, str]) -> None:
        self.runtime_plugin_host.set_scope_overrides(overrides)

    def activate_plugins_matching(self, target: set[str]) -> int:
        report = self.execute_lifecycle_target(
            set(target),
            source="activation_only",
            allow_deactivate=False,
        )
        return len(report.get("completed", {}).get("activated", []))

    def is_plugin_active(self, plugin_name: str) -> bool:
        return plugin_name in self.loaded_plugins

    def user_mod_plugin_ids(self) -> set[str]:
        return {
            name
            for name, scope in self.plugin_scopes.items()
            if scope == self.SCOPE_USER and name in self.plugin_registry
        }

    def embedded_plugin_ids(self) -> set[str]:
        return self.project_scoped_plugin_host.embedded_plugin_ids()

    def catalog_entries(self):
        return self.runtime_plugin_host.catalog_entries()

    def clear_embedded_plugins(self) -> Dict[str, Any]:
        report = self.project_scoped_plugin_host.clear_embedded_plugins()
        self._publish_lifecycle_report(report)
        return report

    def scan_project_addons(self, project_path: str | Path | None) -> Dict[str, Any]:
        return self.project_scoped_plugin_host.scan_project_addons(project_path)

    def sync_plugins_for_project(
        self,
        project_data: Dict[str, Any],
        *,
        repo_root: str | Path | None = None,
    ) -> Dict[str, Any]:
        return self.project_scoped_plugin_host.sync_plugins_for_project(
            project_data,
            repo_root=repo_root,
        )

    def inspect_plugin_host(self, project_path: str = "") -> Dict[str, Any]:
        return self.project_scoped_plugin_host.inspect_plugin_host(project_path)

    def list_plugin_host_recoveries(self, project_path: str = "") -> Dict[str, Any]:
        return self.project_scoped_plugin_host.list_plugin_host_recoveries(project_path)

    def resolve_plugin_host_recovery(
        self,
        *,
        project_path: str,
        report_id: str,
        action: str,
        operator_confirmation: str,
    ) -> Dict[str, Any]:
        return self.project_scoped_plugin_host.resolve_plugin_host_recovery(
            project_path=project_path,
            report_id=report_id,
            action=action,
            operator_confirmation=operator_confirmation,
        )

    def observe_plugins(self) -> Dict[str, Any]:
        """Return fresh deterministic facts for capability consumers."""

        from core.VitaLoom.core.plugin_host_capabilities import (
            build_plugin_host_observation,
        )

        return build_plugin_host_observation(self)

    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Delegate ordinary one-plugin unload without shutdown privileges."""

        plugin_id = str(plugin_name).strip()
        if not plugin_id:
            return {"status": "blocked", "code": "plugin_id_required", "plugin_id": ""}
        if plugin_id in self.protected_plugins:
            return {"status": "blocked", "code": "plugin_protected", "plugin_id": plugin_id}
        if plugin_id not in self.loaded_plugins:
            return {"status": "blocked", "code": "plugin_not_active", "plugin_id": plugin_id}
        settled = self.runtime_plugin_host.unload_plugin(plugin_id)
        return {
            "status": "settled" if settled else "failed",
            "code": "plugin_unloaded" if settled else "plugin_unload_failed",
            "plugin_id": plugin_id,
            "active": plugin_id in self.loaded_plugins,
        }

    def list_reloadable_plugins(self) -> List[str]:
        return self.manual_plugin_reload_host.list_reloadable_plugins()

    def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        return self.manual_plugin_reload_host.reload_plugin(plugin_name)


__all__ = ["NestedPluginHost"]

