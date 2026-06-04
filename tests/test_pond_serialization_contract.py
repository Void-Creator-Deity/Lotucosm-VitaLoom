"""
莲池序列化 JSON 契约字段。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from core.Lotucosm.pond import Pond, LotusPond
from builtin.systems.pond_serializer import PondSerializer


class PondSerializationContractTests(unittest.TestCase):
    def test_lotus_pond_backward_compatible_alias(self):
        pond = LotusPond(initial_organisms=0)
        self.assertIsInstance(pond, Pond)

    def test_deserialize_pond_missing_required_fields_returns_none(self):
        serializer = PondSerializer()
        with self.assertLogs("PondSerializer", level="WARNING") as cm:
            result = serializer.deserialize_pond({"name": "demo"})
        self.assertIsNone(result)
        self.assertTrue(any("pond_data缺少字段" in entry for entry in cm.output))


if __name__ == "__main__":
    unittest.main()
