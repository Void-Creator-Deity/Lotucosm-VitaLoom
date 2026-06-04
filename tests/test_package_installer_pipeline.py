"""
包安装流水线：下载/解压/登记冒烟。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import os
import tempfile
import unittest
import zipfile

from builtin.editor_extensions.package_services import PackageOperationService


class _PM:
    def __init__(self, root):
        self.root = root
        self.cfg = {"disabled_plugins": [], "package_version_overrides": {}}

    def get_current_project_config(self):
        return dict(self.cfg)

    def update_project_config_fields(self, fields):
        self.cfg.update(fields)
        return True

    def get_current_project_path(self):
        return self.root


class TestPackageInstallerPipeline(unittest.TestCase):
    def test_install_and_uninstall_zip_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            pkg_zip = os.path.join(td, "pkg_a.zip")
            with zipfile.ZipFile(pkg_zip, "w") as zf:
                zf.writestr("readme.txt", "hello")
            pm = _PM(td)
            ops = PackageOperationService(pm)
            packages = [
                {
                    "id": "pkg.a",
                    "version": "1.0.0",
                    "source": "file",
                    "dependencies": [],
                    "conflicts": [],
                    "artifact": {"type": "file", "path": pkg_zip},
                }
            ]
            result = ops.install_package("pkg.a", packages, enabled_ids=set(), mode="warn")
            self.assertTrue(result.get("ok"))
            state = pm.cfg.get("package_state", {})
            self.assertIn("pkg.a", state.get("installed", {}))
            un = ops.uninstall_package("pkg.a")
            self.assertTrue(un.get("ok"))


if __name__ == "__main__":
    unittest.main()

