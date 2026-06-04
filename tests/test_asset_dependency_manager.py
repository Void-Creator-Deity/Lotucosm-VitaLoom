# -*- coding: utf-8 -*-
"""
资产依赖管理器：引用解析与循环检测契约。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from core.VitaLoom.project.asset_dependency import AssetDependencyManager


class AssetDependencyManagerTests(unittest.TestCase):
    def test_scene_uses_relative_sprite_path(self):
        mgr = AssetDependencyManager()
        root = os.path.abspath("/proj")
        scene = {"entities": [{"sprite_path": "assets/x.png"}]}
        target = os.path.normpath(os.path.join(root, "assets", "x.png"))
        self.assertTrue(mgr._scene_uses_asset(scene, target, root))

    def test_scene_uses_script_by_name(self):
        mgr = AssetDependencyManager()
        root = os.path.abspath("/proj")
        scene = {"entities": [{"scripts": [{"name": "foo"}]}]}
        target = os.path.normpath(os.path.join(root, "scripts", "foo.py"))
        self.assertTrue(mgr._scene_uses_asset(scene, target, root))

    def test_get_asset_references_integration(self):
        with tempfile.TemporaryDirectory() as root:
            scenes = os.path.join(root, "scenes")
            os.makedirs(scenes)
            png = os.path.join(root, "assets", "a.png")
            os.makedirs(os.path.dirname(png), exist_ok=True)
            with open(png, "wb") as f:
                f.write(b"x")
            pond = os.path.join(scenes, "s.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump({"entities": [{"sprite_path": "assets/a.png"}]}, f)

            mgr = AssetDependencyManager()
            fake_pm = MagicMock()
            fake_pm.get_current_project_path.return_value = root

            with patch("core.VitaLoom.project.asset_dependency.get_project_manager", return_value=fake_pm):
                refs = mgr.get_asset_references(png)
            self.assertEqual(len(refs), 1)
            self.assertTrue(refs[0].replace("\\", "/").endswith("scenes/s.pond"))


if __name__ == "__main__":
    unittest.main()
