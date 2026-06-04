"""
LayoutManager：Dock 布局保存/恢复与默认工作区。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import json
import os
import tempfile
import unittest

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget

from core.VitaLoom.kernel.layout_manager import LayoutManager


class _DummyViewportProvider:
    def __init__(self, name: str):
        self._name = name
        self.activated = 0
        self.deactivated = 0

    def get_viewport_name(self):
        return self._name

    def on_viewport_activated(self):
        self.activated += 1

    def on_viewport_deactivated(self):
        self.deactivated += 1


class LayoutManagerBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.main_window = QMainWindow()
        self.main_window.central_stack = QStackedWidget()
        self.main_window.setCentralWidget(self.main_window.central_stack)
        self.layout = LayoutManager(self.main_window)

    def test_restore_layout_tolerates_partial_geometry_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "layout.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "geometry": {"width": 100, "height": 100},
                        "window_state": "",
                        "dock_states": {},
                        "viewport_state": {},
                    },
                    f,
                )
            self.layout.layout_config_path = config_path
            result = self.layout.restore_layout()
            self.assertTrue(result)

    def test_remove_plugin_ui_cleans_menu_and_toolbar_actions(self):
        self.layout.add_menu_items(
            [{"path": "Tools/TestAction", "action": lambda: None}],
            plugin_name="plugin_test",
        )
        self.layout.add_toolbar_items(
            [{"text": "ToolAction", "action": lambda: None}],
            plugin_name="plugin_test",
        )
        tools_menu = None
        for action in self.layout.menubar.actions():
            if action.text() == "Tools" and action.menu():
                tools_menu = action.menu()
                break
        self.assertIsNotNone(tools_menu)
        self.assertTrue(any(action.text() == "TestAction" for action in tools_menu.actions()))
        self.layout.remove_plugin_ui("plugin_test")
        after_toolbar = len(self.layout.toolbar.actions())
        self.assertEqual(after_toolbar, 0)
        self.assertFalse(any(action.text() == "TestAction" for action in tools_menu.actions()))

    def test_remove_plugin_ui_cleans_separators_and_empty_menu_shell(self):
        self.layout.add_menu_items(
            [
                {"path": "Tools/TestAction", "action": lambda: None},
                {"path": "Tools/", "separator": True},
                {"path": "Tools/OtherAction", "action": None},
            ],
            plugin_name="plugin_sep",
        )
        self.layout.add_toolbar_items(
            [
                {"text": "ToolAction", "action": lambda: None},
                {"separator": True},
            ],
            plugin_name="plugin_sep",
        )

        before_toolbar = len(self.layout.toolbar.actions())
        self.assertGreater(before_toolbar, 0)
        self.layout.remove_plugin_ui("plugin_sep")

        self.assertEqual(len(self.layout.toolbar.actions()), 0)
        self.assertFalse(any(action.text() == "Tools" for action in self.layout.menubar.actions()))

    def test_viewport_switch_updates_current_consistently(self):
        first_provider = _DummyViewportProvider("First")
        second_provider = _DummyViewportProvider("Second")

        self.layout.add_viewport("vp1", QWidget(), first_provider)
        self.layout.add_viewport("vp2", QWidget(), second_provider)
        self.layout.switch_viewport("vp2")

        self.assertEqual(self.layout.current_viewport, "vp2")
        self.assertGreaterEqual(first_provider.deactivated, 1)
        self.assertGreaterEqual(second_provider.activated, 1)


    def test_menu_and_toolbar_accept_icon_field_without_error(self):
        from PyQt6.QtGui import QIcon

        icon = QIcon()
        self.layout.add_menu_items(
            [{"path": "Edit/IconProbe", "action": lambda: None, "icon": icon}],
            plugin_name="icon_probe",
        )
        self.layout.add_toolbar_items(
            [{"text": "IcoProbe", "action": lambda: None, "icon": icon}],
            plugin_name="icon_probe",
        )
        self.layout.remove_plugin_ui("icon_probe")


if __name__ == "__main__":
    unittest.main()
