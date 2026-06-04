"""
包治理策略与注册表规则。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.editor_extensions.package_services import PackageOperationService


class _PM:
    def __init__(self):
        self.cfg = {"disabled_plugins": [], "package_version_overrides": {}}

    def get_current_project_config(self):
        return dict(self.cfg)

    def update_project_config_fields(self, fields):
        self.cfg.update(fields)
        return True

    def get_current_project_path(self):
        return "."


class TestPackageGovernance(unittest.TestCase):
    def test_resolve_transaction_block(self):
        ops = PackageOperationService(_PM())
        packages = [
            {"id": "base", "version": "1.0.0", "dependencies": [], "conflicts": []},
            {"id": "app", "version": "1.0.0", "dependencies": ["base>=1.1.0"], "conflicts": []},
        ]
        out = ops.resolve_transaction("app", packages, enabled_ids={"base"}, mode="block")
        self.assertTrue(out.get("should_block"))
        self.assertTrue(any("incompatible" in s for s in out.get("issues", [])))


if __name__ == "__main__":
    unittest.main()

