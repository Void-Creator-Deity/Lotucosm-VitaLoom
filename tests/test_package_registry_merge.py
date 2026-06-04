"""
多源包注册表合并。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest


from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin


class TestPackageRegistryMerge(unittest.TestCase):
    def test_merge_prefers_builtin_over_url(self):
        pkg_builtin = {"id": "pkg.a", "display_name": "A", "source": "builtin"}
        pkg_url = {"id": "pkg.a", "display_name": "A-remote", "source": "url"}

        merged = PackageManagerPlugin.merge_package_lists(
            package_lists=[[pkg_url], [pkg_builtin]],
            priority_sources=["builtin", "file", "url", "unknown"],
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["source"], "builtin")

    def test_merge_dedup_by_id(self):
        pkg1 = {"id": "pkg.a", "display_name": "A", "source": "file"}
        pkg2 = {"id": "pkg.b", "display_name": "B", "source": "file"}
        merged = PackageManagerPlugin.merge_package_lists(
            package_lists=[[pkg1, pkg2]],
            priority_sources=["builtin", "file", "url", "unknown"],
        )
        self.assertEqual({p["id"] for p in merged}, {"pkg.a", "pkg.b"})


if __name__ == "__main__":
    unittest.main()

