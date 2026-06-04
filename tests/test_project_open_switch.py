# -*- coding: utf-8 -*-
"""切换项目：持久化 active_scene、clear_scene 与恢复上次场景。

职责: 断言/回归 ProjectManager.open_project 切换行为。
时机: pytest 全量或单文件执行。
不变量: 不依赖 GUI；使用临时目录模拟两个项目。
排错: 失败见 core/VitaLoom/project/project_manager.py。
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from PyQt6.QtWidgets import QApplication


class ProjectOpenSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        from core.VitaLoom.core.editor_context import get_editor_context
        from core.VitaLoom.kernel.event_bus import EventBus

        ctx = get_editor_context()
        ctx._ensure_qobject_initialized()
        if not getattr(ctx, "event_bus", None):
            ctx.event_bus = EventBus()
    def _write_project(self, root: str, name: str, active_scene: str, pond_name: str) -> str:
        proj = os.path.join(root, name)
        scenes = os.path.join(proj, "scenes")
        os.makedirs(scenes, exist_ok=True)
        pond_path = os.path.join(scenes, pond_name)
        with open(pond_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": pond_name.replace(".pond", ""),
                    "entities": [{"id": f"e_{name}", "type": "organism", "position": [1.0, 2.0]}],
                    "connections": [],
                },
                f,
            )
        with open(os.path.join(proj, "project.json"), "w", encoding="utf-8") as f:
            json.dump({"name": name, "active_scene": active_scene}, f)
        return proj

    def test_switch_restores_each_project_active_scene(self) -> None:
        from core.VitaLoom.project.project_manager import ProjectManager
        from core.VitaLoom.scene.scene_manager import SceneManager

        pm = ProjectManager()
        sm = SceneManager()
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write_project(tmp, "projA", "a.pond", "a.pond")
            b = self._write_project(tmp, "projB", "b.pond", "b.pond")
            self.assertTrue(pm.open_project(a))
            self.assertEqual(os.path.basename(sm.get_current_scene_path() or ""), "a.pond")
            ents = (sm.get_scene_data() or {}).get("entities") or []
            self.assertEqual(ents[0].get("id"), "e_projA")

            self.assertTrue(pm.open_project(b))
            self.assertEqual(os.path.basename(sm.get_current_scene_path() or ""), "b.pond")
            ents_b = (sm.get_scene_data() or {}).get("entities") or []
            self.assertEqual(ents_b[0].get("id"), "e_projB")

            with open(os.path.join(a, "project.json"), encoding="utf-8") as f:
                cfg_a = json.load(f)
            self.assertEqual(cfg_a.get("active_scene"), "a.pond")

            self.assertTrue(pm.open_project(a))
            self.assertEqual(os.path.basename(sm.get_current_scene_path() or ""), "a.pond")

    def test_reopen_same_project_reads_active_scene_from_disk(self) -> None:
        from core.VitaLoom.project.project_manager import ProjectManager
        from core.VitaLoom.scene.scene_manager import SceneManager

        pm = ProjectManager()
        sm = SceneManager()
        with tempfile.TemporaryDirectory() as tmp:
            proj = self._write_project(tmp, "projReload", "a.pond", "a.pond")
            b_pond = os.path.join(proj, "scenes", "b.pond")
            with open(b_pond, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "name": "b",
                        "entities": [{"id": "e_b", "type": "organism", "position": [0.0, 0.0]}],
                        "connections": [],
                    },
                    f,
                )
            self.assertTrue(pm.open_project(proj))
            self.assertEqual(os.path.basename(sm.get_current_scene_path() or ""), "a.pond")

            cfg_path = os.path.join(proj, "project.json")
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["active_scene"] = "b.pond"
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f)

            self.assertTrue(pm.open_project(proj))
            self.assertEqual(os.path.basename(sm.get_current_scene_path() or ""), "b.pond")
            ents = (sm.get_scene_data() or {}).get("entities") or []
            self.assertEqual(ents[0].get("id"), "e_b")


    def test_last_opened_project_persisted(self) -> None:
        import shutil

        from core.VitaLoom.project.project_manager import ProjectManager

        pm = ProjectManager()
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace = os.path.join(repo_root, "projects", "_maint_test_last_opened")
        cfg_path = os.path.join(workspace, "editor_config.json")
        os.makedirs(workspace, exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"recent_projects": []}, f)
        orig_cfg = pm._get_config_file
        pm._get_config_file = lambda: cfg_path  # type: ignore[method-assign]
        try:
            proj = self._write_project(workspace, "lastOpen", "a.pond", "a.pond")
            self.assertFalse(pm._is_ephemeral_project_path(proj))
            self.assertTrue(pm.open_project(proj))
            last = pm.get_last_opened_project()
            self.assertIsNotNone(last)
            self.assertEqual(
                os.path.normcase(last or ""),
                os.path.normcase(proj),
            )
        finally:
            pm._get_config_file = orig_cfg  # type: ignore[method-assign]
            shutil.rmtree(workspace, ignore_errors=True)

    def test_sanitize_removes_invalid_last_opened(self) -> None:
        from core.VitaLoom.project.project_manager import ProjectManager

        pm = ProjectManager()
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "editor_config.json")
            bad_last = os.path.join(
                os.environ.get("TEMP", tmp), "tmp_invalid_proj"
            )
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"recent_projects": [], "last_opened_project": bad_last},
                    f,
                )
            orig_cfg = pm._get_config_file
            pm._get_config_file = lambda: cfg_path  # type: ignore[method-assign]
            try:
                pm._sanitize_editor_config()
                cfg = pm._read_editor_config()
                self.assertNotIn("last_opened_project", cfg)
            finally:
                pm._get_config_file = orig_cfg  # type: ignore[method-assign]

    def test_ephemeral_paths_not_in_recent(self) -> None:
        from core.VitaLoom.project.project_manager import ProjectManager

        pm = ProjectManager()
        with tempfile.TemporaryDirectory() as tmp:
            proj = self._write_project(tmp, "ephemeral", "a.pond", "a.pond")
            self.assertTrue(pm._is_ephemeral_project_path(proj))
            pytest_dir = os.path.join(tmp, "_pytest_marker")
            self.assertTrue(pm._is_ephemeral_project_path(pytest_dir))
            pm._add_to_recent_projects(proj)
            self.assertNotIn(proj, pm.get_recent_projects())


if __name__ == "__main__":
    unittest.main()
