'Compatibility facade over the Qt-free NestedPluginHost and concrete legacy Editor plugin Adapter.'

from pathlib import Path
from typing import Any, Dict, List
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.nested_plugin_host import NestedPluginHost
from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
    LegacyEditorPluginAdapter,
)
from core.VitaLoom.project.plugin_host_lifecycle import PluginHostCatalogEntry
from core.VitaLoom.project.plugin_host_operator import bind_plugin_host_operator_adapter


class PluginLoader:
    'Narrow compatibility facade over NestedPluginHost and LegacyEditorPluginAdapter.'
    SCOPE_CORE = "core_mod"
    SCOPE_OFFICIAL = "official_mod"
    SCOPE_USER = "user_mod"
    SCOPE_EMBEDDED = "embedded_mod"
    SCOPE_UNKNOWN = "unknown"

    _SCOPE_PRIORITY = {
        SCOPE_UNKNOWN: 0,
        SCOPE_EMBEDDED: 1,
        SCOPE_USER: 2,
        SCOPE_OFFICIAL: 3,
        SCOPE_CORE: 4,
    }

    def __init__(self, editor_kernel):
        """Create the legacy UI Adapter over the Qt-free composition root."""
        self.kernel = editor_kernel
        self.legacy_editor_plugin_adapter = LegacyEditorPluginAdapter(editor_kernel)
        self.nested_plugin_host = NestedPluginHost(
            activation_context_resolver=(
                self.legacy_editor_plugin_adapter.activation_context_for
            ),
            runtime_adapter=self.legacy_editor_plugin_adapter,
            repo_root_resolver=self._project_repo_root,
            eager_mode_resolver=self._should_eager_load,
            after_lifecycle_transition=(
                self.legacy_editor_plugin_adapter.after_lifecycle_transition
            ),
            candidate_importer=lambda file_path: self._instantiate_plugin_from_file(
                file_path
            ),
        )
        self.runtime_plugin_host = self.nested_plugin_host.runtime_plugin_host
        self.project_scoped_plugin_host = (
            self.nested_plugin_host.project_scoped_plugin_host
        )
        self.manual_plugin_reload_host = self.nested_plugin_host.manual_plugin_reload_host
        self.legacy_editor_plugin_adapter.bind_active_plugin_items_resolver(
            lambda: tuple(self.nested_plugin_host.loaded_plugins.items())
        )
        self.legacy_editor_plugin_adapter.bind_active_plugin_metadata_resolver(
            lambda: tuple(
                (
                    plugin_id,
                    self.runtime_plugin_host.plugin_metadata.get(plugin_id, {}),
                )
                for plugin_id in self.nested_plugin_host.loaded_plugins
            )
        )

        # Compatibility attributes intentionally alias composition-root state.
        self.plugin_registry = self.nested_plugin_host.plugin_registry
        self.loaded_plugins = self.nested_plugin_host.loaded_plugins
        self.plugin_dependencies = self.nested_plugin_host.plugin_dependencies
        self.plugin_order = self.nested_plugin_host.plugin_order
        self.failed_plugins = self.nested_plugin_host.failed_plugins
        self.discovery_errors = self.nested_plugin_host.discovery_errors
        self.plugin_scopes = self.nested_plugin_host.plugin_scopes
        self.plugin_files = self.nested_plugin_host.plugin_files
        self.protected_plugins = self.nested_plugin_host.protected_plugins
        self.scope_overrides = self.nested_plugin_host.scope_overrides
        bind_plugin_host_operator_adapter(self)

    @property
    def _runtime_activation_context(self) -> object | None:
        """Legacy observation alias for the concrete Editor Adapter cache."""
        return self.legacy_editor_plugin_adapter.runtime_activation_context

    @_runtime_activation_context.setter
    def _runtime_activation_context(self, value: object | None) -> None:
        self.legacy_editor_plugin_adapter.runtime_activation_context = value

    def load_from_directories(self, dirs: List[str]):
        """Delegate unlayered discovery and bootstrap to the composition root."""
        # Standalone compatibility callers have no project lifecycle to sync;
        # preserve their historical direct-load behavior. Project-backed
        # editor startup remains bootstrap-only until project sync selects a
        # target set.
        if hasattr(self.kernel, "_project_root"):
            return self.nested_plugin_host.load_from_directories(dirs)
        return self.nested_plugin_host.load_from_directories(dirs, force_all=True)

    def load_from_layered_directories(self, layered_dirs: Dict[str, List[str]]):
        """Delegate layered discovery and bootstrap to the composition root."""
        return self.nested_plugin_host.load_from_layered_directories(layered_dirs)

    def set_scope_overrides(self, overrides: Dict[str, str]):
        """Compatibility Adapter entry for composition-root scope overrides."""
        return self.nested_plugin_host.set_scope_overrides(overrides)

    def _finalize_loading(self):
        """Compatibility Adapter entry for composition-root bootstrap."""
        return self.nested_plugin_host.finalize_loading()

    def _should_eager_load(self) -> bool:
        from core.VitaLoom.project.plugin_activation import eager_load_all_plugins

        return eager_load_all_plugins()

    def _user_mod_plugin_ids(self) -> set[str]:
        return self.nested_plugin_host.user_mod_plugin_ids()

    def is_plugin_active(self, plugin_name: str) -> bool:
        return self.nested_plugin_host.is_plugin_active(plugin_name)

    def _embedded_plugin_ids(self) -> set[str]:
        return self.nested_plugin_host.embedded_plugin_ids()

    def _catalog_entries(self) -> List[PluginHostCatalogEntry]:
        """Compatibility projection delegated to the composition root."""
        return self.nested_plugin_host.catalog_entries()

    @property
    def last_lifecycle_report(self) -> Dict[str, Any]:
        """Legacy observation alias for composition-root lifecycle state."""
        return self.nested_plugin_host.last_lifecycle_report

    @last_lifecycle_report.setter
    def last_lifecycle_report(self, report: Dict[str, Any]) -> None:
        self.nested_plugin_host.last_lifecycle_report = report

    def _after_lifecycle_transition(self, report: Dict[str, Any]) -> None:
        """Compatibility delegate for concrete legacy layout settling."""
        self.legacy_editor_plugin_adapter.after_lifecycle_transition(report)

    def _execute_lifecycle_target(
        self,
        target: set[str],
        *,
        source: str,
        allow_deactivate: bool,
    ) -> Dict[str, Any]:
        """Compatibility Adapter entry for composition-root lifecycle execution."""
        return self.nested_plugin_host.execute_lifecycle_target(
            set(target),
            source=source,
            allow_deactivate=allow_deactivate,
        )

    @property
    def _embedded_plugin_names(self) -> set[str]:
        """Legacy observation alias for Project Host-owned state."""
        return self.project_scoped_plugin_host.embedded_plugin_names

    @property
    def _operator_project_path(self) -> str:
        """Legacy observation alias for the current operator Project World."""
        return self.project_scoped_plugin_host.operator_project_path

    @property
    def _embedded_catalog_project_path(self) -> str:
        """Legacy observation alias for the retained L4 catalog owner."""
        return self.project_scoped_plugin_host.embedded_catalog_project_path

    @property
    def last_project_addon_discovery_report(self) -> Dict[str, Any]:
        return self.project_scoped_plugin_host.last_project_addon_discovery_report

    @last_project_addon_discovery_report.setter
    def last_project_addon_discovery_report(self, report: Dict[str, Any]) -> None:
        self.project_scoped_plugin_host.last_project_addon_discovery_report = report

    @property
    def last_operator_recovery_report(self) -> Dict[str, Any]:
        return self.project_scoped_plugin_host.last_operator_recovery_report

    @last_operator_recovery_report.setter
    def last_operator_recovery_report(self, report: Dict[str, Any]) -> None:
        self.project_scoped_plugin_host.last_operator_recovery_report = report

    def _project_repo_root(self) -> str | Path:
        """Concrete Editor Adapter resolver for the Qt-free Project Host."""
        ctx = self.kernel.get_context() if hasattr(self.kernel, "get_context") else None
        repo_root = getattr(ctx, "repo_root", None) if ctx else None
        if repo_root:
            return repo_root
        from core.VitaLoom.core.bundle_paths import resource_root

        return resource_root()

    def clear_embedded_plugins(self) -> Dict[str, Any]:
        """Compatibility Adapter entry for Project Host-owned L4 cleanup."""
        return self.nested_plugin_host.clear_embedded_plugins()

    def scan_project_addons(self, project_path: str | Path | None) -> Dict[str, Any]:
        """Compatibility Adapter entry for Project Host-owned L4 discovery."""
        return self.nested_plugin_host.scan_project_addons(project_path)

    def sync_plugins_for_project(
        self,
        project_data: Dict[str, Any],
        *,
        repo_root: str | Path | None = None,
    ) -> Dict[str, Any]:
        """Compatibility Adapter entry for Project Host-owned lifecycle sync."""
        return self.nested_plugin_host.sync_plugins_for_project(
            project_data, repo_root=repo_root
        )

    def inspect_plugin_host(self, project_path: str = "") -> Dict[str, Any]:
        """Compatibility Adapter entry for Project Host operator inspection."""
        return self.nested_plugin_host.inspect_plugin_host(project_path)

    def list_plugin_host_recoveries(self, project_path: str = "") -> Dict[str, Any]:
        """Compatibility Adapter entry for Project Host recovery listing."""
        return self.nested_plugin_host.list_plugin_host_recoveries(project_path)

    def resolve_plugin_host_recovery(
        self,
        *,
        project_path: str,
        report_id: str,
        action: str,
        operator_confirmation: str,
    ) -> Dict[str, Any]:
        """Compatibility Adapter entry for confirmation-bound normal retry."""
        return self.nested_plugin_host.resolve_plugin_host_recovery(
            project_path=project_path,
            report_id=report_id,
            action=action,
            operator_confirmation=operator_confirmation,
        )

    def _scan_directory(self, path: Path, scope: str):
        """Compatibility Adapter entry for Qt-free Host discovery."""
        return self.runtime_plugin_host.scan_directory(path, scope)

    def _discover_plugin(self, file_path: Path, scope: str):
        """Compatibility Adapter entry for one Host-owned plugin import."""
        return self.runtime_plugin_host.discover_plugin(file_path, scope)

    def _resolve_dependencies(self):
        """Compatibility Adapter entry for Host-owned dependency ordering."""
        return self.runtime_plugin_host.resolve_dependencies()

    def _activate_plugins_matching(self, target: set[str]) -> int:
        """Compatibility Adapter entry for composition-root activation."""
        return self.nested_plugin_host.activate_plugins_matching(set(target))
    def _load_all_plugins(self):
        'Compatibility adapter entry for lifecycle-authoritative activation of all registered plugins.'
        self._activate_plugins_matching(set(self.plugin_registry.keys()))

    def _activation_context_for(self, plugin_info: Dict[str, Any]):
        """Compatibility delegate for concrete Host context projection."""
        return self.legacy_editor_plugin_adapter.activation_context_for(plugin_info)

    def _load_plugin(self, plugin: IRuntimePlugin):
        """Compatibility Adapter entry for Qt-free runtime callback execution."""
        return self.runtime_plugin_host.load_plugin(plugin)

    def after_plugin_load(
        self,
        plugin: IRuntimePlugin,
        plugin_name: str,
        plugin_info: Dict[str, Any],
    ) -> None:
        """Compatibility delegate for legacy Editor contribution publication."""
        self.legacy_editor_plugin_adapter.after_plugin_load(
            plugin, plugin_name, plugin_info
        )

    def before_plugin_unload(
        self,
        plugin: IRuntimePlugin,
        plugin_name: str,
        plugin_info: Dict[str, Any],
    ) -> None:
        """Compatibility delegate for pre-unload contribution cleanup."""
        self.legacy_editor_plugin_adapter.before_plugin_unload(
            plugin, plugin_name, plugin_info
        )

    def after_plugin_deactivated(
        self,
        plugin: IRuntimePlugin,
        plugin_name: str,
        plugin_info: Dict[str, Any],
    ) -> None:
        """Compatibility delegate for legacy unload observation."""
        self.legacy_editor_plugin_adapter.after_plugin_deactivated(
            plugin, plugin_name, plugin_info
        )

    def _register_dock(self, plugin: Any) -> None:
        """Compatibility delegate for legacy dock providers."""
        self.legacy_editor_plugin_adapter.register_dock(plugin)

    def _register_viewport(self, plugin: Any) -> None:
        """Compatibility delegate for legacy viewport providers."""
        self.legacy_editor_plugin_adapter.register_viewport(plugin)

    def _register_theme(self, plugin: Any) -> None:
        """Compatibility delegate for legacy theme providers."""
        self.legacy_editor_plugin_adapter.register_theme(plugin)

    def unload_plugin(self, plugin_name: str):
        """Compatibility Adapter entry for Qt-free Host deactivation."""
        return self.runtime_plugin_host.unload_plugin(plugin_name)

    def shutdown_plugins(self) -> Dict[str, Any]:
        """Delegate complete Host shutdown to the nested composition root."""
        return self.nested_plugin_host.shutdown_plugins()

    def _cleanup_plugin_ui(self, plugin: IRuntimePlugin, plugin_name: str) -> None:
        """Compatibility delegate for concrete legacy UI cleanup."""
        self.legacy_editor_plugin_adapter.cleanup_plugin_ui(plugin, plugin_name)

    def _invalidate_plugin_bytecode(self, file_path: Path) -> None:
        """Compatibility Adapter entry for Host-owned import invalidation."""
        self.runtime_plugin_host.invalidate_plugin_bytecode(file_path)

    def _instantiate_plugin_from_file(self, file_path: Path) -> tuple[str, IRuntimePlugin]:
        """Compatibility Adapter entry for Host-owned candidate import."""
        return self.runtime_plugin_host.instantiate_plugin_from_file(file_path)

    @property
    def last_reload_report(self) -> Dict[str, Any]:
        """Legacy observation alias for ManualPluginReloadHost-owned state."""
        return self.nested_plugin_host.last_reload_report

    @last_reload_report.setter
    def last_reload_report(self, report: Dict[str, Any]) -> None:
        self.nested_plugin_host.last_reload_report = report

    def list_reloadable_plugins(self) -> List[str]:
        """Compatibility Adapter entry for Qt-free reload candidate listing."""
        return self.nested_plugin_host.list_reloadable_plugins()

    def reload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Compatibility Adapter entry for Qt-free manual reload orchestration."""
        return self.nested_plugin_host.reload_plugin(plugin_name)
