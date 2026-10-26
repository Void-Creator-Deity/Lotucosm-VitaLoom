# -*- coding: utf-8
"""包管理器列表筛选与空状态说明。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PROJECT_WORLD_READ_MODEL


class PackageManagerFilterTests(unittest.TestCase):
    def test_community_tab_excludes_builtin_catalog(self):
        plugin = PackageManagerPlugin()
        pkg = {"id": "x", "source": "builtin", "category": "official"}
        self.assertFalse(plugin._matches_tab_filter(pkg, "community"))
        ext = {"id": "y", "source": "url", "category": "community"}
        self.assertTrue(plugin._matches_tab_filter(ext, "community"))

    def test_core_tab_includes_core_platform(self):
        plugin = PackageManagerPlugin()
        core = {"id": "vitalloom.core.platform", "source": "core", "category": "core", "origin": "core"}
        self.assertTrue(plugin._matches_tab_filter(core, "core"))
        self.assertFalse(plugin._matches_tab_filter(core, "official"))

    def test_implicitly_enabled_core_package(self):
        plugin = PackageManagerPlugin()
        core = {"id": "vitalloom.core.platform", "status": "required", "category": "core", "plugins": []}
        self.assertTrue(plugin._is_implicitly_enabled_package(core))
        self.assertTrue(plugin._matches_status_filter(False, False, "enabled", core))

    def test_empty_hint_community_mentions_registry(self):
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.i18n_tr = lambda k, d="": d or k
        plugin.operation_service = None
        plugin._packages = []
        plugin.detail_text = MagicMock()
        plugin._render_empty_list_hint(
            tab_filter="community",
            status_filter="enabled",
            keyword="",
            total_loaded=8,
        )
        text = plugin.detail_text.setPlainText.call_args[0][0]
        self.assertIn("package_registries", text)
        self.assertIn("已启用", text)

    def test_package_display_name_prefers_zh(self):
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.i18n_get_language = lambda: "zh_CN"
        pkg = {"id": "demo", "display_name": "Demo Pack", "display_name_zh": "演示包"}
        self.assertEqual(plugin._package_display_name(pkg), "演示包")

    def test_project_lock_status_marks_package_issue(self):
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.i18n_tr = lambda k, d="": d or k
        plugin.operation_service = None
        plugin._packages = []
        missing = {"id": "vitalloom.engine.sr2d", "project_lock_status": "missing"}
        stale = {"id": "vitalloom.engine.sr2d", "project_lock_status": "stale"}
        optional = {"id": "vitalloom.assets.demo", "project_lock_status": "optional"}
        self.assertTrue(plugin._package_has_issues(missing))
        self.assertTrue(plugin._package_has_issues(stale))
        self.assertFalse(plugin._package_has_issues(optional))
        self.assertEqual(plugin._project_lock_label(missing), "能力缺失")

    def test_get_source_filter_uses_item_data(self):
        plugin = PackageManagerPlugin()
        combo = MagicMock()
        combo.currentData.return_value = "file"
        plugin.source_filter = combo
        self.assertEqual(plugin._get_source_filter(), "file")

    def test_on_tab_changed_resets_status_on_community(self):
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.i18n_tr = lambda k, d="": d or k
        plugin.status_filter = MagicMock()
        plugin.status_filter.currentIndex.return_value = 1
        plugin.result_text = MagicMock()
        plugin._append_result = MagicMock()
        plugin._refresh = MagicMock()
        plugin.tab_bar = MagicMock()
        plugin._on_tab_changed(3)
        plugin.status_filter.setCurrentIndex.assert_called_with(0)
        plugin._refresh.assert_called_once()

    def test_should_auto_align_manifest_default_true(self):
        plugin = PackageManagerPlugin()
        read_model = SimpleNamespace(
            current_project_world_path=lambda: "",
            current_project_world_config=lambda: {},
        )
        registry = InMemoryRuntimeCapabilityRegistry()
        registry.register(PROJECT_WORLD_READ_MODEL, read_model)
        plugin.context = SimpleNamespace(services=registry)
        self.assertTrue(plugin._should_auto_align_manifest())

    def test_manifest_issues_auto_align_skips_dialog(self):
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.i18n_tr = lambda k, d="": d or k
        plugin.kernel = MagicMock()
        plugin.kernel.layout_manager.statusbar = MagicMock()
        plugin.package_list = MagicMock()
        plugin._should_auto_align_manifest = MagicMock(return_value=True)
        plugin._align_manifest_packages = MagicMock(return_value=True)
        plugin._refresh = MagicMock()
        result = MagicMock()
        result.missing_packages = ["vitalloom.pvaec.simulation"]
        plugin._on_project_manifest_issues(result)
        plugin._align_manifest_packages.assert_called_once()
        plugin.kernel.layout_manager.statusbar.showMessage.assert_called_once()


    def test_refresh_populates_package_list_after_dock_create(self):
        """Dock 创建后列表应显示 catalog 包（修复 language_changed 重建竞态）。"""
        try:
            from PyQt6.QtWidgets import QApplication
        except Exception:
            self.skipTest("PyQt6 not available")
        import sys

        app = QApplication.instance() or QApplication(sys.argv)
        plugin = PackageManagerPlugin()
        plugin.context = MagicMock()
        plugin.context.kernel = MagicMock()
        type(plugin.context).repo_root = None
        plugin.context.event_bus = MagicMock()
        plugin.context.event_bus.subscribe = MagicMock()
        plugin.context.i18n_tr = lambda k, d="": d or k
        plugin.context.i18n_get_language = lambda: "zh_CN"
        plugin.context.services = MagicMock()
        plugin.context.services.register = MagicMock()
        plugin.context.services.get = MagicMock(return_value=None)
        plugin.on_load(plugin.context)
        plugin.create_dock_widget()
        self.assertGreater(len(plugin._packages), 0)
        self.assertGreater(plugin.package_list.count(), 0)


if __name__ == "__main__":
    unittest.main()
