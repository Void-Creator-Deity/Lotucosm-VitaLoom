"""
ComponentFactory：按类型名实例化 builtin 组件。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.components.component_factory import ComponentFactory
from builtin.components.component_library import get_component_class


class ComponentFactoryTests(unittest.TestCase):
    def test_create_sensor(self):
        f = ComponentFactory()
        c = f.create_component("Sensor", "s1", organism_id="o1", name="S")
        self.assertEqual(c.id, "s1")
        self.assertIs(get_component_class("Sensor"), type(c))


if __name__ == "__main__":
    unittest.main()
