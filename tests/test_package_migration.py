"""
包清单迁移与合并兼容。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest

from builtin.editor_extensions.package_services import PackageOperationService


class _PM:
    def __init__(self):
        self.cfg = {"disabled_plugins": [], "package_version_overrides": {"a": "1.0.1"}}

    def get_current_project_config(self):
        return dict(self.cfg)

    def update_project_config_fields(self, fields):
        self.cfg.update(fields)
        return True

    def get_current_project_path(self):
        return "."


class TestPackageMigration(unittest.TestCase):
    def test_migrate_legacy_state(self):
        pm = _PM()
        ops = PackageOperationService(pm)
        ok = ops.migrate_legacy_state()
        self.assertTrue(ok)
        state = pm.cfg.get("package_state", {})
        self.assertEqual(state.get("version_overrides", {}).get("a"), "1.0.1")
        self.assertIn("installed", state)
        self.assertIn("rollback_points", state)


if __name__ == "__main__":
    unittest.main()

