"""
序列化降级：未知组件类型可跳过或占位。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.systems.component_serializer import ComponentSerializer
from builtin.systems.organism_serializer import OrganismSerializer
from builtin.systems.memory_storage import MemoryStorage


class SerializerDegradeTests(unittest.TestCase):
    def test_component_deserialize_invalid_returns_none(self):
        serializer = ComponentSerializer()
        invalid_data = {"id": "comp_1"}
        with self.assertLogs("ComponentSerializer", level="WARNING") as cm:
            result = serializer.deserialize_component(invalid_data)
        self.assertIsNone(result)
        self.assertTrue(any("component_data缺少字段" in entry for entry in cm.output))

    def test_organism_deserialize_invalid_returns_none(self):
        serializer = OrganismSerializer()
        invalid_data = {"id": "org_1", "type": "SimpleOrganism"}
        with self.assertLogs("OrganismSerializer", level="WARNING") as cm:
            result = serializer.deserialize_organism(invalid_data)
        self.assertIsNone(result)
        self.assertTrue(any("organism_data缺少字段" in entry for entry in cm.output))

    def test_memory_deserialize_missing_fields_raises_value_error(self):
        storage = MemoryStorage()
        with self.assertRaises(ValueError):
            storage.deserialize_memory({"situation": "x"})


if __name__ == "__main__":
    unittest.main()
