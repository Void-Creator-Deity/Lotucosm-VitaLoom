"""
main 启动链：内核与插件加载冒烟。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest


class StartupSmokeTests(unittest.TestCase):
    def test_main_module_importable(self):
        import main  # noqa: F401

    def test_kernel_modules_importable(self):
        from core.VitaLoom.kernel import editor_kernel, plugin_loader, layout_manager  # noqa: F401
        self.assertIsNotNone(editor_kernel)
        self.assertIsNotNone(plugin_loader)
        self.assertIsNotNone(layout_manager)


if __name__ == "__main__":
    unittest.main()
