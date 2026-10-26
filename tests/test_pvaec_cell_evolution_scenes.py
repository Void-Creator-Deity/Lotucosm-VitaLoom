# -*- coding: utf-8 -*-
"""
PVAEC · 细胞演化场景 JSON：演示目标与实体契约。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCENES = _ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "scenes"


class PvaecFinalVisionSceneContractTests(unittest.TestCase):
    def _load(self, name: str) -> dict:
        path = _SCENES / name
        self.assertTrue(path.is_file(), f"missing {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_main_scene_play_goals(self) -> None:
        data = self._load("main_scene.pond")
        goals = data["sr_play_goals"]
        self.assertEqual(goals["survive_seconds"], 100)
        self.assertEqual(goals["peak_population"], 4)
        self.assertFalse(goals["pause_on_complete"])

    def test_challenge_scene_stricter_goals_and_fewer_nutrients(self) -> None:
        data = self._load("challenge_scene.pond")
        goals = data["sr_play_goals"]
        self.assertGreaterEqual(goals["survive_seconds"], 150)
        self.assertGreaterEqual(goals["peak_population"], 6)
        self.assertFalse(goals["pause_on_complete"])
        self.assertFalse(data["sr_pause_on_extinction"])
        nutrients = [e for e in data["entities"] if e.get("type") == "nutrient"]
        self.assertEqual(len(nutrients), 4)
        orgs = [e for e in data["entities"] if e.get("type") == "organism"]
        self.assertEqual(len(orgs), 1)
        evo = orgs[0]["scripts"][0]["properties"]["evo"]
        self.assertGreater(evo["base_metabolism"], 3.0)

    def test_both_scenes_share_evo_script_name(self) -> None:
        for name in ("main_scene.pond", "challenge_scene.pond"):
            data = self._load(name)
            brain = next(e for e in data["entities"] if e.get("id") == "ai_organism_01")
            self.assertEqual(brain["scripts"][0]["name"], "evo_central_brain_pvaec")


if __name__ == "__main__":
    unittest.main()
