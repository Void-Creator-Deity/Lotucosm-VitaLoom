"""
Inspector 属性映射：组件字段与 UI 键对齐。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import os
import unittest

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.docks.inspector import InspectorPanel


class _DummyNode:
    def __init__(self):
        self.id = "node_1"
        self.x = 1.0
        self.y = 2.0
        self.name = "old_name"

    def update_position(self, x, y):
        self.x = x
        self.y = y


class InspectorPropertyMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.panel = InspectorPanel()

    def test_position_x_maps_to_node_x(self):
        node = _DummyNode()
        self.panel._on_property_changed("position_x", 123.0, [node])
        self.assertEqual(node.x, 123.0)

    def test_string_field_uses_text_submit(self):
        node = _DummyNode()
        self.panel._on_property_changed("name", "new_name", [node])
        self.assertEqual(node.name, "new_name")


if __name__ == "__main__":
    unittest.main()
