"""
包域：版本冲突检测策略。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin


class TestPackageConflictChecks(unittest.TestCase):
    def test_normalize_package_conflicts_default(self):
        p = PackageManagerPlugin._normalize_package({"id": "a", "display_name": "A"}, "builtin")
        self.assertIn("conflicts", p)
        self.assertEqual(p["conflicts"], [])


if __name__ == "__main__":
    unittest.main()

