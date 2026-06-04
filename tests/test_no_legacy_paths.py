"""
仓库无遗留路径/模块名（架构收敛守卫）。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import importlib
import unittest


class TestNoLegacyPaths(unittest.TestCase):
    def test_legacy_plugin_paths_not_importable(self):
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin.interface")

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin.manager")

    def test_legacy_editor_entry_removed(self):
        vitalloom = importlib.import_module("core.VitaLoom")
        self.assertFalse(
            hasattr(vitalloom, "PyQtOrganismEditor"),
            "旧入口 PyQtOrganismEditor 不应再暴露",
        )


if __name__ == "__main__":
    unittest.main()
