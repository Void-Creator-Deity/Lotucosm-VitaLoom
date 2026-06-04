# -*- coding: utf-8 -*-
"""
资产依赖扫描插件：项目内引用收集与报告。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import json
import os
import tempfile
import unittest

from builtin.editor_extensions.asset_dependency_scan import (
    DependencyEdge,
    dependency_summary,
    format_dependency_scan_report,
    scan_project_dependencies,
    scan_scene_file,
)


class AssetDependencyScanTests(unittest.TestCase):
    def test_script_by_name_resolves_under_project_scripts(self):
        with tempfile.TemporaryDirectory() as td:
            root = td
            os.makedirs(os.path.join(root, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
            script_path = os.path.join(root, "scripts", "hello.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write("# user script\n")

            scene = {
                "name": "t",
                "entities": [{"id": "e1", "scripts": [{"name": "hello"}]}],
            }
            pond = os.path.join(root, "scenes", "a.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump(scene, f)

            edges = scan_project_dependencies(root)
            self.assertTrue(any(e.kind == "script" and e.resolved_path == script_path and e.exists for e in edges))

    def test_sprite_path_asset_edge(self):
        with tempfile.TemporaryDirectory() as td:
            root = td
            os.makedirs(os.path.join(root, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(root, "assets", "img"), exist_ok=True)
            png = os.path.join(root, "assets", "img", "x.png")
            with open(png, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")

            scene = {
                "entities": [{"sprite_path": "assets/img/x.png"}],
            }
            pond = os.path.join(root, "scenes", "b.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump(scene, f)

            edges = scan_scene_file(pond, root)
            self.assertTrue(any(e.kind == "asset" and e.resolved_path.replace("\\", "/").endswith("assets/img/x.png") for e in edges))

    def test_missing_script_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = td
            os.makedirs(os.path.join(root, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
            scene = {"entities": [{"scripts": [{"name": "nope"}]}]}
            pond = os.path.join(root, "scenes", "c.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump(scene, f)
            edges = scan_project_dependencies(root)
            self.assertTrue(any(e.kind == "script" and not e.exists for e in edges))

    def test_active_scene_from_project_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = td
            os.makedirs(os.path.join(root, "scenes"), exist_ok=True)
            pond = os.path.join(root, "scenes", "main_scene.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump({"name": "m", "entities": []}, f)
            pj = os.path.join(root, "project.json")
            with open(pj, "w", encoding="utf-8") as f:
                json.dump({"active_scene": "main_scene.pond"}, f)

            edges = scan_project_dependencies(root)
            act = [e for e in edges if e.kind == "active_scene"]
            self.assertEqual(len(act), 1)
            self.assertTrue(act[0].exists)
            self.assertEqual(os.path.normpath(act[0].resolved_path), os.path.normpath(pond))

    def test_script_string_without_py_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root = td
            os.makedirs(os.path.join(root, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
            sp = os.path.join(root, "scripts", "foo.py")
            with open(sp, "w", encoding="utf-8") as f:
                f.write("pass\n")
            pond = os.path.join(root, "scenes", "x.pond")
            with open(pond, "w", encoding="utf-8") as f:
                json.dump({"entities": [{"scripts": ["foo"]}]}, f)
            edges = scan_project_dependencies(root)
            self.assertTrue(any(e.kind == "script" and e.resolved_path == sp and e.exists for e in edges))
            s = dependency_summary(edges)
            self.assertIn("total_edges", s)
            self.assertGreaterEqual(s["total_edges"], 1)



class FormatDependencyReportTests(unittest.TestCase):
    def test_report_lists_missing_edges(self):
        edges = [
            DependencyEdge("s.pond", "$.x", "script", "a", "/abs/missing.py", False),
            DependencyEdge("s.pond", "$.y", "asset", "p.png", "/abs/ok.png", True),
        ]
        summ = dependency_summary(edges)
        text = format_dependency_scan_report("/proj", edges, summ)
        self.assertIn("/proj", text)
        self.assertIn("missing.py", text)
        self.assertNotIn("ok.png", text)

    def test_report_ok_when_all_exist(self):
        edges = [
            DependencyEdge("s.pond", "$.y", "asset", "p.png", "/abs/ok.png", True),
        ]
        summ = dependency_summary(edges)
        text = format_dependency_scan_report("/proj", edges, summ)
        self.assertIn("无缺失引用", text)


if __name__ == "__main__":
    unittest.main()
