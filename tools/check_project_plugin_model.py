#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the project-level plugin model."""
from __future__ import annotations

import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def main() -> int:
    violations: list[str] = []

    from core.VitaLoom.core.bundle_paths import default_plugin_layer_dirs

    layers = default_plugin_layer_dirs()
    user_mod = layers.get("user_mod", [])
    if user_mod:
        violations.append(
            "workspace/extensions must be plugin sources by default, not global user_mod scan roots"
        )

    standard_ui = RUNTIME / "builtin" / "editor_extensions" / "standard_ui_plugin.py"
    text = standard_ui.read_text(encoding="utf-8")
    menu_block = text.split("def get_toolbar_items", 1)[0]
    if "menu.open_project" in menu_block:
        violations.append("Editor StandardUI must not expose cross-project open; use Hub")
    forbidden_standard_ui = [
        '"action": self.new_project',
        '"action": self.open_project',
        '"action": self.save_project_as',
        ".open_project(project_path)",
        ".open_project(new_path)",
        "pm.open_project(project_path)",
    ]
    for snippet in forbidden_standard_ui:
        if snippet in text:
            violations.append("Editor StandardUI must not create/open/switch projects; use Hub")
            break

    ui_mutation_files = [
        RUNTIME / "builtin" / "editor_extensions" / "package_manager_plugin.py",
        RUNTIME / "builtin" / "editor_extensions" / "plugin_runtime_ops.py",
        RUNTIME / "core" / "VitaLoom" / "docks" / "library_browser.py",
        RUNTIME / "core" / "VitaLoom" / "docks" / "ps_experiment_panel.py",
    ]
    forbidden_snippets = [
        'update_project_config_fields({"disabled_plugins"',
        "update_project_config_fields({'disabled_plugins'",
        'update_project_config_fields({"package_state"',
        "update_project_config_fields({'package_state'",
        'update_project_config_fields({"active_scene"',
        "update_project_config_fields({'active_scene'",
        'update_project_config_fields({"ps_experiment_preset"',
        "update_project_config_fields({'ps_experiment_preset'",
        'update_project_config_fields({"evolution_defaults"',
        "update_project_config_fields({'evolution_defaults'",
        ".write_disabled_plugins(",
    ]
    for path in ui_mutation_files:
        file_text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            if snippet in file_text:
                violations.append(
                    f"{path.relative_to(ROOT)} must mutate project plugin state through plugin.* commands"
                )
                break

    scene_ui_files = [
        RUNTIME / "builtin" / "editor_extensions" / "project_browser_plugin.py",
        RUNTIME / "builtin" / "editor_extensions" / "standard_ui_plugin.py",
        RUNTIME / "core" / "VitaLoom" / "docks" / "scene_outline.py",
        RUNTIME / "core" / "VitaLoom" / "scene" / "scene_switcher.py",
        RUNTIME / "core" / "VitaLoom" / "viewports" / "scene_viewport.py",
    ]
    forbidden_scene_snippets = [
        ".load_scene(",
        ".save_scene(",
    ]
    for path in scene_ui_files:
        file_text = path.read_text(encoding="utf-8")
        for snippet in forbidden_scene_snippets:
            if snippet in file_text:
                violations.append(
                    f"{path.relative_to(ROOT)} must open/save scenes through scene.* commands"
                )
                break

    asset_ui_files = [
        RUNTIME / "builtin" / "editor_extensions" / "project_browser_plugin.py",
    ]
    forbidden_asset_write_snippets = [
        ".write_text(",
        ".write_bytes(",
        "os.makedirs(",
        ".mkdir(",
    ]
    for path in asset_ui_files:
        file_text = path.read_text(encoding="utf-8")
        for snippet in forbidden_asset_write_snippets:
            if snippet in file_text:
                violations.append(
                    f"{path.relative_to(ROOT)} must create project assets through asset.* commands"
                )
                break
        if re.search(r"\bopen\s*\([^)]*,\s*['\"][wax]", file_text):
            violations.append(
                f"{path.relative_to(ROOT)} must create project assets through asset.* commands"
            )

    editor_project_switch_files = [
        RUNTIME / "builtin" / "editor_extensions" / "project_browser_plugin.py",
    ]
    for path in editor_project_switch_files:
        file_text = path.read_text(encoding="utf-8")
        if ".open_project(" in file_text:
            violations.append(
                f"{path.relative_to(ROOT)} must not switch projects inside an editor session; use Hub"
            )

    loader_text = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py"
    ).read_text(encoding="utf-8")
    if "target |= self._user_mod_plugin_ids()" in loader_text:
        violations.append(
            "PluginLoader must not auto-enable user_mod; workspace/extensions are project plugin sources"
        )

    lifecycle_path = (
        RUNTIME / "core" / "VitaLoom" / "project" / "plugin_host_lifecycle.py"
    )
    if not lifecycle_path.is_file():
        violations.append(
            "L1 engine plugin Host must provide Qt-free plugin_host_lifecycle.py authority"
        )
    else:
        lifecycle_text = lifecycle_path.read_text(encoding="utf-8")
        for snippet in (
            "def build_plugin_lifecycle_plan(",
            "def discover_project_addons(",
            'addons_raw = project / "addons"',
            "addon_runtime_incompatible",
            "plugin_dependency_cycle",
        ):
            if snippet not in lifecycle_text:
                violations.append(
                    f"plugin lifecycle authority is missing required contract marker: {snippet}"
                )
        if "PyQt6" in lifecycle_text or "QWidget" in lifecycle_text:
            violations.append(
                "plugin_host_lifecycle.py must remain Qt-free; UI belongs to Host Adapters"
            )
    project_host_path = (
        RUNTIME / "core" / "VitaLoom" / "project" / "project_scoped_plugin_host.py"
    )
    if not project_host_path.is_file():
        violations.append(
            "L1 engine plugin Host must provide Qt-free project_scoped_plugin_host.py orchestration"
        )
    else:
        project_host_text = project_host_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "class ProjectScopedPluginHost:",
            "def scan_project_addons(self, project_path",
            "def sync_plugins_for_project(",
            "def resolve_plugin_host_recovery(",
            "discover_project_addons(",
        ):
            if snippet not in project_host_text:
                violations.append(
                    f"project-scoped plugin Host is missing required contract marker: {snippet}"
                )
        for forbidden in ("PyQt6", "kernel.plugin_loader", "kernel.plugin_interfaces"):
            if forbidden in project_host_text:
                violations.append(
                    "project_scoped_plugin_host.py must remain Qt-free and independent of legacy adapters"
                )
                break

    nested_host_path = (
        RUNTIME / "core" / "VitaLoom" / "core" / "nested_plugin_host.py"
    )
    nested_host_text = ""
    if not nested_host_path.is_file():
        violations.append(
            "L1 engine plugin Host must provide Qt-free nested_plugin_host.py composition"
        )
    else:
        nested_host_text = nested_host_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "class NestedPluginHost:",
            "RuntimePluginHost(",
            "ProjectScopedPluginHost(",
            "ManualPluginReloadHost(",
            "def load_from_directories(",
            "def load_from_layered_directories(",
            "def execute_lifecycle_target(",
            "return self.project_scoped_plugin_host.scan_project_addons(project_path)",
            "return self.manual_plugin_reload_host.reload_plugin(plugin_name)",
        ):
            if snippet not in nested_host_text:
                violations.append(
                    f"nested plugin Host is missing required composition marker: {snippet}"
                )
        for forbidden in (
            "PyQt6",
            "EditorKernel",
            "LayoutManager",
            "kernel.plugin_loader",
            "kernel.plugin_interfaces",
        ):
            if forbidden in nested_host_text:
                violations.append(
                    "nested_plugin_host.py must remain Qt-free and independent of legacy adapters"
                )
                break

    editor_adapter_path = (
        RUNTIME
        / "core"
        / "VitaLoom"
        / "kernel"
        / "legacy_editor_plugin_adapter.py"
    )
    editor_adapter_text = ""
    if not editor_adapter_path.is_file():
        violations.append(
            "legacy Editor Host must provide legacy_editor_plugin_adapter.py"
        )
    else:
        editor_adapter_text = editor_adapter_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "class LegacyEditorPluginAdapter",
            "RuntimePluginHostAdapter",
            "def activation_context_for(",
            "def after_plugin_load(",
            "def before_plugin_unload(",
            "def after_plugin_deactivated(",
            "process_pending_dock_tabify",
        ):
            if snippet not in editor_adapter_text:
                violations.append(
                    f"legacy Editor plugin Adapter is missing required marker: {snippet}"
                )
        for stale_command_marker in (
            "registry.register(owned_spec)",
            "def after_plugin_unload_callback(",
            "def after_plugin_shutdown_callback(",
        ):
            if stale_command_marker in editor_adapter_text:
                violations.append(
                    "legacy Editor plugin Adapter must not own command publication "
                    f"or release: {stale_command_marker}"
                )

    runtime_host_path = (
        RUNTIME / "core" / "VitaLoom" / "core" / "runtime_plugin_host.py"
    )
    if not runtime_host_path.is_file():
        violations.append("Qt-free RuntimePluginHost authority is missing")
    else:
        runtime_host_text = runtime_host_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "class RuntimePluginHost",
            "ICommandProvider",
            "def _publish_plugin_commands(",
            "registry.register(spec)",
            "def _release_plugin_commands(",
            "_command_publications",
        ):
            if snippet not in runtime_host_text:
                violations.append(
                    f"RuntimePluginHost command authority is missing required marker: {snippet}"
                )
        for forbidden in ("PyQt6", "QWidget", "LegacyEditorPluginAdapter"):
            if forbidden in runtime_host_text:
                violations.append(
                    "runtime_plugin_host.py must remain Qt-free and independent of the legacy Editor Adapter"
                )
                break

    # PluginLoader is a narrow compatibility facade.  NestedPluginHost owns
    # sub-Host composition and the concrete Adapter owns Editor contributions.
    for snippet in (
        "NestedPluginHost(",
        "return self.nested_plugin_host.load_from_directories(dirs)",
        "return self.nested_plugin_host.load_from_layered_directories(layered_dirs)",
        "return self.nested_plugin_host.scan_project_addons(project_path)",
        "return self.nested_plugin_host.sync_plugins_for_project(",
        "return self.nested_plugin_host.resolve_plugin_host_recovery(",
        "LegacyEditorPluginAdapter(editor_kernel)",
        "runtime_adapter=self.legacy_editor_plugin_adapter",
    ):
        if snippet not in loader_text:
            violations.append(
                f"PluginLoader composition Adapter is missing required delegation marker: {snippet}"
            )
    for concrete_marker in (
        "create_dock_widget",
        "create_viewport_widget",
        "add_menu_items",
        "add_toolbar_items",
        "get_theme_manager",
        "registry.register(owned_spec)",
        "def after_plugin_unload_callback(",
        "def after_plugin_shutdown_callback(",
        "process_pending_dock_tabify",
    ):
        if concrete_marker in loader_text:
            violations.append(
                f"PluginLoader facade must not implement legacy Editor contribution marker: {concrete_marker}"
            )
    if "runtime_adapter=self," in loader_text:
        violations.append(
            "PluginLoader must pass the exact LegacyEditorPluginAdapter to NestedPluginHost"
        )

    for forbidden_constructor in (
        "RuntimePluginHost(",
        "ProjectScopedPluginHost(",
        "ManualPluginReloadHost(",
    ):
        if forbidden_constructor in loader_text:
            violations.append(
                f"PluginLoader must not construct nested Host authority directly: {forbidden_constructor}"
            )
    if "discover_project_addons(" in loader_text:
        violations.append(
            "PluginLoader must delegate manifest-authorized project addon discovery to NestedPluginHost"
        )

    reload_host_path = (
        RUNTIME / "core" / "VitaLoom" / "core" / "manual_plugin_reload_host.py"
    )
    if not reload_host_path.is_file():
        violations.append(
            "L1 engine plugin Host must provide Qt-free manual_plugin_reload_host.py orchestration"
        )
    else:
        reload_host_text = reload_host_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "class ManualPluginReloadHost:",
            "def list_reloadable_plugins(",
            "def reload_plugin(",
            "build_plugin_reload_plan(",
            "instantiate_plugin_from_file",
            '"source": "hot_reload"',
            '"registry_replaced": False',
        ):
            if snippet not in reload_host_text:
                violations.append(
                    f"manual reload Host is missing required contract marker: {snippet}"
                )
        for forbidden in (
            "PyQt6",
            "EditorKernel",
            "LayoutManager",
            "kernel.plugin_loader",
            "kernel.plugin_interfaces",
        ):
            if forbidden in reload_host_text:
                violations.append(
                    "manual_plugin_reload_host.py must remain Qt-free and independent of legacy adapters"
                )
                break

    if nested_host_text and "ManualPluginReloadHost(" not in nested_host_text:
        violations.append(
            "NestedPluginHost must compose ManualPluginReloadHost over its one runtime Host"
        )
    for snippet in (
        "return self.nested_plugin_host.list_reloadable_plugins()",
        "return self.nested_plugin_host.reload_plugin(plugin_name)",
    ):
        if snippet not in loader_text:
            violations.append(
                f"PluginLoader Reload Adapter is missing required delegation marker: {snippet}"
            )
    for forbidden in (
        "def _new_reload_report(",
        "def _block_reload(",
        "build_plugin_reload_plan(",
        'code="reload_candidate_import_failed"',
    ):
        if forbidden in loader_text:
            violations.append(
                f"PluginLoader must not own manual reload orchestration marker: {forbidden}"
            )

    operator_path = (
        RUNTIME / "core" / "VitaLoom" / "project" / "plugin_host_operator.py"
    )
    if not operator_path.is_file():
        violations.append(
            "L1 engine plugin Host must provide Qt-free plugin_host_operator.py authority"
        )
    else:
        operator_text = operator_path.read_text(encoding="utf-8-sig")
        for snippet in (
            "def build_plugin_host_inspection(",
            "def validate_plugin_host_recovery(",
            "retry_project_lifecycle",
            "plugin_host_report_stale",
        ):
            if snippet not in operator_text:
                violations.append(
                    f"plugin Host operator authority is missing required marker: {snippet}"
                )
        if "PyQt6" in operator_text or "EditorContext" in operator_text:
            violations.append(
                "plugin_host_operator.py must remain Qt-free; UI belongs to Host Adapters"
            )
    for snippet in (
        "bind_plugin_host_operator_adapter(self)",
        "def inspect_plugin_host(",
        "def resolve_plugin_host_recovery(",
    ):
        if snippet not in loader_text:
            violations.append(
                f"PluginLoader operator Adapter is missing required marker: {snippet}"
            )
    manager_text = (
        RUNTIME / "core" / "VitaLoom" / "project" / "project_manager.py"
    ).read_text(encoding="utf-8")
    if '"project_plugin_lifecycle_failed"' not in manager_text:
        violations.append(
            "ProjectManager must publish truthful failed downstream-extension lifecycle reports"
        )

    catalog_path = RUNTIME / "builtin" / "package_index.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    package_ids = {
        str(pkg.get("id", "")).strip()
        for pkg in catalog.get("packages", [])
        if isinstance(pkg, dict) and str(pkg.get("id", "")).strip()
    }
    catalog_command_ids: set[str] = set()
    for pkg in catalog.get("packages", []):
        if not isinstance(pkg, dict):
            continue
        pkg_id = str(pkg.get("id", "<unknown>"))
        for field in ("commands", "resources", "export_entries"):
            if not isinstance(pkg.get(field), list):
                violations.append(f"{pkg_id} must declare {field} as a list")
        for command_id in pkg.get("commands", []):
            command_id = str(command_id).strip()
            if command_id:
                catalog_command_ids.add(command_id)
        if pkg.get("plugins") and not pkg.get("commands") and not str(pkg.get("ui_only_reason", "")).strip():
            violations.append(
                f"{pkg_id} contributes editor plugins without commands; declare ui_only_reason or command ids"
            )

    from core.VitaLoom.commands.registry import reset_command_registry

    registry = reset_command_registry()
    for command_id in (
        "plugin.host.inspect",
        "plugin.host.recovery.list",
        "plugin.host.recovery.resolve",
    ):
        try:
            registry.describe(command_id)
        except KeyError:
            violations.append(
                f"shared command registry is missing downstream Host operator command {command_id}"
            )
    for command_id in sorted(catalog_command_ids):
        try:
            spec = registry.describe(command_id)
        except KeyError:
            violations.append(f"{command_id} is declared in builtin package_index.json but not registered")
            continue
        capability = str(spec.get("capability", "")).strip()
        if capability not in package_ids:
            violations.append(
                f"{command_id} declares unresolved command capability {capability!r}; "
                "capability must match a builtin package id"
            )

    doc_forbidden_snippets = [
        "冷启动仅激活 `vitalloom.editor_essentials` 内插件 + `workspace/extensions/user|community`",
        "workspace/extensions/user|community`；打开工程后",
    ]
    for path in (ROOT / "docs").rglob("*.md"):
        file_text = path.read_text(encoding="utf-8")
        for snippet in doc_forbidden_snippets:
            if snippet in file_text:
                violations.append(
                    f"{path.relative_to(ROOT)} must describe workspace/extensions as sources, not global enabled plugins"
                )
                break

    if violations:
        print("project plugin model violations:")
        for item in violations:
            print(f"  - {item}")
        return 1
    print("project plugin model OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

