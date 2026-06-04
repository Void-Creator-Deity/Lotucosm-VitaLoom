"""
示例 service provider/consumer 插件注册契约。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from plugins.example_service_consumer.service_consumer_plugin import ExampleServiceConsumerPlugin


class TestServiceRegistryExamples(unittest.TestCase):
    def test_version_compatible(self):
        self.assertTrue(
            ExampleServiceConsumerPlugin._is_version_compatible("1.2.0", "1.0.0")
        )
        self.assertTrue(
            ExampleServiceConsumerPlugin._is_version_compatible("1.0.0", "1.0.0")
        )
        self.assertFalse(
            ExampleServiceConsumerPlugin._is_version_compatible("0.9.9", "1.0.0")
        )

    def test_parse_version_invalid_fallback(self):
        self.assertEqual(ExampleServiceConsumerPlugin._parse_version("x.y.z"), (0, 0, 0))
        self.assertEqual(ExampleServiceConsumerPlugin._parse_version("2"), (2, 0, 0))


if __name__ == "__main__":
    unittest.main()

