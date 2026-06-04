"""
包域：依赖声明与解析校验。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin


class TestPackageDependencyChecks(unittest.TestCase):
    def test_parse_dependency_expr(self):
        dep_id, op, ver = PackageManagerPlugin._parse_dependency_expr("pkg.core>=1.2.3")
        self.assertEqual(dep_id, "pkg.core")
        self.assertEqual(op, ">=")
        self.assertEqual(ver, "1.2.3")

    def test_version_gte(self):
        self.assertTrue(PackageManagerPlugin._version_gte("1.2.0", "1.1.9"))
        self.assertTrue(PackageManagerPlugin._version_gte("1.0.0", "1.0.0"))
        self.assertFalse(PackageManagerPlugin._version_gte("0.9.9", "1.0.0"))

    def test_should_block_enable(self):
        self.assertFalse(PackageManagerPlugin.should_block_enable("warn", True))
        self.assertTrue(PackageManagerPlugin.should_block_enable("block", True))
        self.assertFalse(PackageManagerPlugin.should_block_enable("block", False))

    def test_dependency_enabled_ids_logic(self):
        plugin = PackageManagerPlugin()
        plugin.context = None  # _t 回落到 default 即可
        plugin._packages = [
            {"id": "pkg.base", "version": "1.0.0", "plugins": ["BaseA"]},
            {"id": "pkg.target", "version": "1.0.0", "dependencies": ["pkg.base>=1.0.0"], "plugins": ["TargetA"]},
        ]
        plugin._get_project_disabled_plugins = lambda: ["BaseA"]  # type: ignore[method-assign]
        lines = plugin._evaluate_dependency_status(plugin._packages[1])
        self.assertTrue(any("DISABLED:" in line for line in lines))

    def test_matches_status_filter(self):
        self.assertTrue(PackageManagerPlugin._matches_status_filter(True, False, "enabled"))
        self.assertTrue(PackageManagerPlugin._matches_status_filter(False, False, "disabled"))
        self.assertTrue(PackageManagerPlugin._matches_status_filter(False, True, "issues"))
        self.assertFalse(PackageManagerPlugin._matches_status_filter(False, False, "issues"))

    def test_collect_update_candidates(self):
        loaded_lists = [
            [{"id": "pkg.a", "version": "1.0.0"}],
            [{"id": "pkg.a", "version": "1.2.0"}, {"id": "pkg.b", "version": "2.0.0"}],
        ]
        merged = [{"id": "pkg.a", "version": "1.0.0"}, {"id": "pkg.b", "version": "2.0.0"}]
        updates = PackageManagerPlugin._collect_update_candidates(loaded_lists, merged)
        self.assertEqual(updates.get("pkg.a"), "1.2.0")
        self.assertNotIn("pkg.b", updates)

    def test_apply_project_version_overrides(self):
        plugin = PackageManagerPlugin()
        plugin._get_project_version_overrides = lambda: {"pkg.a": "1.2.0"}  # type: ignore[method-assign]
        merged = [{"id": "pkg.a", "version": "1.0.0"}, {"id": "pkg.b", "version": "2.0.0"}]
        out = plugin._apply_project_version_overrides(merged)
        self.assertEqual(out[0]["version"], "1.2.0")
        self.assertEqual(out[1]["version"], "2.0.0")

    def test_matches_tab_filter_updates(self):
        plugin = PackageManagerPlugin()
        plugin._update_candidates = {"pkg.a": "1.2.0"}
        self.assertTrue(plugin._matches_tab_filter({"id": "pkg.a"}, "updates"))
        self.assertFalse(plugin._matches_tab_filter({"id": "pkg.b"}, "updates"))

    def test_select_target_updates(self):
        updates = {"pkg.a": "1.2.0", "pkg.b": "2.0.0"}
        selected = PackageManagerPlugin._select_target_updates(updates, {"pkg.b"})
        self.assertEqual(selected, {"pkg.b": "2.0.0"})
        all_selected = PackageManagerPlugin._select_target_updates(updates, set())
        self.assertEqual(all_selected, updates)

    def test_queue_buttons_enabled_only_updates_tab(self):
        class _Btn:
            def __init__(self):
                self.enabled = None

            def setEnabled(self, v):
                self.enabled = bool(v)

        plugin = PackageManagerPlugin()
        plugin.queue_select_all_btn = _Btn()
        plugin.queue_invert_btn = _Btn()
        plugin.queue_clear_btn = _Btn()
        plugin.queue_only_checked_cb = _Btn()
        plugin.queue_stats_label = None
        plugin._get_tab_filter = lambda: "installed"  # type: ignore[method-assign]
        plugin._set_queue_buttons_enabled()
        self.assertFalse(plugin.queue_select_all_btn.enabled)
        plugin._get_tab_filter = lambda: "updates"  # type: ignore[method-assign]
        plugin._set_queue_buttons_enabled()
        self.assertTrue(plugin.queue_select_all_btn.enabled)

    def test_select_target_updates_with_checked_subset(self):
        updates = {"a": "1.1.0", "b": "2.0.0", "c": "3.0.0"}
        out = PackageManagerPlugin._select_target_updates(updates, {"a", "c"})
        self.assertEqual(out, {"a": "1.1.0", "c": "3.0.0"})

    def test_confirm_update_plan_without_kernel(self):
        class _Ops:
            def create_update_plan(self, _target_updates, _lookup):
                return {"count": 1, "source_summary": {"builtin": 1}, "items": [{"id": "pkg.a"}]}

        plugin = PackageManagerPlugin()
        plugin.kernel = None
        plugin.operation_service = _Ops()
        plugin._packages = []
        plan = plugin._confirm_update_plan({"pkg.a": "1.2.0"})
        self.assertIsInstance(plan, dict)
        self.assertEqual(plan.get("count"), 1)

    def test_confirm_update_plan_content_params(self):
        class _Kernel:
            pass

        class _MsgBox:
            class Icon:
                Question = 1

            class ButtonRole:
                ActionRole = 0

            class StandardButton:
                Yes = 1
                No = 2

            captured = {}
            _clicked = None

            def __init__(self, *_args, **_kwargs):
                self._buttons = {}

            def setIcon(self, *_args, **_kwargs):
                return None

            def setWindowTitle(self, *_args, **_kwargs):
                return None

            def setText(self, content):
                type(self).captured["content"] = content

            def addButton(self, arg1, *_args):
                if arg1 == self.StandardButton.Yes:
                    btn = "yes"
                elif arg1 == self.StandardButton.No:
                    btn = "no"
                else:
                    btn = "export"
                self._buttons[btn] = btn
                return btn

            def setDefaultButton(self, *_args, **_kwargs):
                return None

            def exec(self):
                type(self)._clicked = self._buttons.get("yes")

            def clickedButton(self):
                return type(self)._clicked

            @classmethod
            def question(cls, _parent, _title, content, *_args):
                cls.captured["content"] = content
                return cls.StandardButton.Yes

        plugin = PackageManagerPlugin()
        plugin.kernel = _Kernel()
        plugin.context = None
        plugin.operation_service = type(
            "_Ops",
            (),
            {
                "create_update_plan": staticmethod(
                    lambda _target_updates, _lookup: {
                        "count": 1,
                        "source_summary": {"builtin": 1},
                        "items": [
                            {
                                "id": "pkg.a",
                                "current_version": "1.0.0",
                                "target_version": "1.2.0",
                                "source": "builtin",
                            }
                        ],
                    }
                )
            },
        )()
        plugin._packages = [{"id": "pkg.a", "version": "1.0.0", "source": "builtin"}]
        original = __import__("builtin.editor_extensions.package_manager_plugin", fromlist=["QMessageBox"]).QMessageBox
        try:
            import builtin.editor_extensions.package_manager_plugin as ppm

            ppm.QMessageBox = _MsgBox  # type: ignore[assignment]
            ok = plugin._confirm_update_plan({"pkg.a": "1.2.0"})
            self.assertIsInstance(ok, dict)
            self.assertIn("pkg.a", _MsgBox.captured.get("content", ""))
            self.assertIn("builtin", _MsgBox.captured.get("content", ""))
        finally:
            import builtin.editor_extensions.package_manager_plugin as ppm

            ppm.QMessageBox = original  # type: ignore[assignment]


if __name__ == "__main__":
    unittest.main()

