# -*- coding: utf-8 -*-
"""Guard the nested FrameCore -> engine-plugin extension topology without Qt."""
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRAMECORE = ROOT / "FrameCore"
ENGINE_PLUGIN = FRAMECORE / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = ENGINE_PLUGIN / "versions" / "1.0.0"
RUNTIME = VERSION_ROOT / "runtime"


class EnginePluginHostArchitectureTests(unittest.TestCase):
    def test_framecore_has_exactly_one_l1_engine_plugin_manifest(self) -> None:
        manifests = sorted((FRAMECORE / "plugins").rglob("plugin_manifest.json"))
        self.assertEqual(manifests, [ENGINE_PLUGIN / "plugin_manifest.json"])

        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        self.assertEqual(manifest["plugin_id"], "lotucosm-vitaloom")
        self.assertEqual(manifest["entry"], "hub")
        self.assertEqual(manifest["default_version"], "1.0.0")
        self.assertEqual(manifest["versions"], ["1.0.0"])

    def test_engine_runtime_owns_capability_catalog_not_framecore(self) -> None:
        version = json.loads((VERSION_ROOT / "version_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(version["builtin_capability_index"], "runtime/builtin/package_index.json")
        self.assertTrue((RUNTIME / "builtin" / "package_index.json").is_file())

        catalog = json.loads((RUNTIME / "builtin" / "package_index.json").read_text(encoding="utf-8"))
        package_ids = {str(package["id"]) for package in catalog["packages"]}
        self.assertIn("vitalloom.core.platform", package_ids)
        self.assertNotIn("lotucosm-vitaloom", package_ids)

    def test_project_addons_are_orchestrated_through_the_exact_host_capability(self) -> None:
        loader = (RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py").read_text(
            encoding="utf-8"
        )
        nested_host = (
            RUNTIME / "core" / "VitaLoom" / "core" / "nested_plugin_host.py"
        ).read_text(encoding="utf-8-sig")
        project_host = (
            RUNTIME / "core" / "VitaLoom" / "project" / "project_scoped_plugin_host.py"
        ).read_text(encoding="utf-8-sig")
        lifecycle = (
            RUNTIME / "core" / "VitaLoom" / "project" / "plugin_host_lifecycle.py"
        ).read_text(encoding="utf-8")
        manager = (RUNTIME / "core" / "VitaLoom" / "project" / "project_manager.py").read_text(
            encoding="utf-8"
        )
        capability = (
            RUNTIME / "core" / "VitaLoom" / "core" / "plugin_host_capabilities.py"
        ).read_text(encoding="utf-8-sig")

        # Project World discovery remains reachable only from project-open flow,
        # but its L4 state and authority are now Qt-free and below the L1 engine plugin.
        self.assertIn("class ProjectScopedPluginHost:", project_host)
        self.assertIn("def scan_project_addons(self, project_path", project_host)
        self.assertIn("discover_project_addons(", project_host)
        self.assertIn("def clear_embedded_plugins(self)", project_host)
        self.assertNotIn("PyQt6", project_host)
        self.assertNotIn("kernel.plugin_loader", project_host)

        # The Qt-free composition root owns Project Host construction; the
        # PluginLoader remains only the legacy Editor/UI compatibility Adapter.
        self.assertIn("ProjectScopedPluginHost(", nested_host)
        self.assertIn("NestedPluginHost(", loader)
        self.assertNotIn("ProjectScopedPluginHost(", loader)
        self.assertIn("def scan_project_addons(self, project_path", loader)
        self.assertIn(
            "return self.nested_plugin_host.scan_project_addons(project_path)",
            loader,
        )
        self.assertNotIn("discover_project_addons(", loader)
        self.assertIn('addons_raw = project / "addons"', lifecycle)
        self.assertIn("addon_manifest_missing", lifecycle)
        self.assertIn("class PluginHostControlObservation(Protocol):", capability)
        self.assertIn("def resolve_plugin_host(", capability)
        self.assertNotIn("PyQt6", capability)
        self.assertIn("resolve_plugin_host", manager)
        self.assertIn("host.scan_project_addons(project_path)", manager)
        self.assertIn("host.sync_plugins_for_project(", manager)
        self.assertIn("host.scan_project_addons(None)", manager)
        self.assertNotIn("kernel.plugin_loader", manager)
        self.assertNotIn("ProjectScopedPluginHost(", manager)
        self.assertIn("plugin_lifecycle_report = self._sync_project_plugins(", manager)
        self.assertIn('"project_plugin_lifecycle_failed"', manager)

    def test_operator_recovery_authority_remains_qt_free_and_below_l1(self) -> None:
        operator_path = (
            RUNTIME / "core" / "VitaLoom" / "project" / "plugin_host_operator.py"
        )
        self.assertTrue(operator_path.is_file())
        operator = operator_path.read_text(encoding="utf-8-sig")
        loader = (RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py").read_text(
            encoding="utf-8-sig"
        )
        commands = (
            RUNTIME / "core" / "VitaLoom" / "commands" / "runtime_commands.py"
        ).read_text(encoding="utf-8-sig")

        self.assertNotIn("PyQt6", operator)
        self.assertNotIn("EditorContext", operator)
        self.assertIn("def build_plugin_host_inspection(", operator)
        self.assertIn("def validate_plugin_host_recovery(", operator)
        self.assertIn("bind_plugin_host_operator_adapter(self)", loader)
        self.assertIn("def resolve_plugin_host_recovery(", loader)
        for command_id in (
            "plugin.host.inspect",
            "plugin.host.recovery.list",
            "plugin.host.recovery.resolve",
        ):
            self.assertIn(f'id="{command_id}"', commands)



    def test_nested_plugin_host_is_the_only_loader_composition_root(self) -> None:
        nested_path = RUNTIME / "core" / "VitaLoom" / "core" / "nested_plugin_host.py"
        self.assertTrue(nested_path.is_file())
        nested = nested_path.read_text(encoding="utf-8-sig")
        loader = (RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py").read_text(
            encoding="utf-8-sig"
        )

        for marker in (
            "class NestedPluginHost:",
            "RuntimePluginHost(",
            "ProjectScopedPluginHost(",
            "ManualPluginReloadHost(",
            "def load_from_layered_directories(",
            "def execute_lifecycle_target(",
        ):
            self.assertIn(marker, nested)
        for forbidden in (
            "PyQt6",
            "EditorKernel",
            "LayoutManager",
            "kernel.plugin_loader",
            "kernel.plugin_interfaces",
        ):
            self.assertNotIn(forbidden, nested)

        self.assertIn("NestedPluginHost(", loader)
        self.assertEqual(loader.count("NestedPluginHost("), 1)
        for forbidden_constructor in (
            "RuntimePluginHost(",
            "ProjectScopedPluginHost(",
            "ManualPluginReloadHost(",
        ):
            self.assertNotIn(forbidden_constructor, loader)
        self.assertIn(
            "return self.nested_plugin_host.load_from_directories(dirs)", loader
        )
        self.assertIn(
            "return self.nested_plugin_host.load_from_layered_directories(layered_dirs)",
            loader,
        )
        adapter = (
            RUNTIME
            / "core"
            / "VitaLoom"
            / "kernel"
            / "legacy_editor_plugin_adapter.py"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("LegacyEditorPluginAdapter(editor_kernel)", loader)
        self.assertIn(
            "runtime_adapter=self.legacy_editor_plugin_adapter", loader
        )
        self.assertNotIn("runtime_adapter=self,", loader)
        self.assertIn("def after_plugin_load(", loader)
        self.assertIn("def before_plugin_unload(", loader)
        self.assertIn("class LegacyEditorPluginAdapter", adapter)
        self.assertIn("RuntimePluginHostAdapter", adapter)
        self.assertIn("process_pending_dock_tabify", adapter)
        for concrete_marker in (
            "create_dock_widget",
            "create_viewport_widget",
            "add_menu_items",
            "add_toolbar_items",
            "get_theme_manager",
        ):
            self.assertIn(concrete_marker, adapter)
            self.assertNotIn(concrete_marker, loader)

        runtime_host = (
            RUNTIME / "core" / "VitaLoom" / "core" / "runtime_plugin_host.py"
        ).read_text(encoding="utf-8-sig")
        for command_marker in (
            "ICommandProvider",
            "def _publish_plugin_commands(",
            "registry.register(spec)",
            "def _release_plugin_commands(",
            "_command_publications",
        ):
            self.assertIn(command_marker, runtime_host)
        for stale_adapter_marker in (
            "registry.register(owned_spec)",
            "def after_plugin_unload_callback(",
            "def after_plugin_shutdown_callback(",
        ):
            self.assertNotIn(stale_adapter_marker, adapter)
            self.assertNotIn(stale_adapter_marker, loader)

    def test_manual_reload_orchestration_is_qt_free_and_loader_delegated(self) -> None:
        reload_host_path = (
            RUNTIME / "core" / "VitaLoom" / "core" / "manual_plugin_reload_host.py"
        )
        self.assertTrue(reload_host_path.is_file())
        reload_host = reload_host_path.read_text(encoding="utf-8-sig")
        nested_host = (
            RUNTIME / "core" / "VitaLoom" / "core" / "nested_plugin_host.py"
        ).read_text(encoding="utf-8-sig")
        loader = (RUNTIME / "core" / "VitaLoom" / "kernel" / "plugin_loader.py").read_text(
            encoding="utf-8-sig"
        )

        self.assertIn("class ManualPluginReloadHost:", reload_host)
        self.assertIn("build_plugin_reload_plan(", reload_host)
        self.assertIn("instantiate_plugin_from_file", reload_host)
        self.assertIn('"source": "hot_reload"', reload_host)
        for forbidden in (
            "PyQt6",
            "EditorKernel",
            "LayoutManager",
            "kernel.plugin_loader",
            "kernel.plugin_interfaces",
        ):
            self.assertNotIn(forbidden, reload_host)

        self.assertIn("ManualPluginReloadHost(", nested_host)
        self.assertNotIn("ManualPluginReloadHost(", loader)
        self.assertIn(
            "return self.nested_plugin_host.list_reloadable_plugins()", loader
        )
        self.assertIn(
            "return self.nested_plugin_host.reload_plugin(plugin_name)", loader
        )
        self.assertNotIn("def _new_reload_report(", loader)
        self.assertNotIn("def _block_reload(", loader)
        self.assertNotIn("build_plugin_reload_plan(", loader)

if __name__ == "__main__":
    unittest.main()

