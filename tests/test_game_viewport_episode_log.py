# -*- coding: utf-8 -*-
"""
GameViewport Episode 日志冒烟：验证 logs/episodes 下写出 JSON。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import GameViewport


class GameViewportEpisodeLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._proj = Path(__file__).resolve().parents[1]
        self._log_dir = self._proj / "logs" / "episodes"
        shutil.rmtree(self._log_dir, ignore_errors=True)

    def tearDown(self) -> None:
        shutil.rmtree(self._log_dir, ignore_errors=True)

    def test_maybe_log_scene_episode_writes_json(self) -> None:
        gv = GameViewport()
        gv._episode_log_enabled = True
        gv._episode_duration_sim_time = 0.001
        gv._using_scene_runtime = True
        gv._scene_runtime_time = 2.5
        gv.scene_runtime_entities = []
        gv._episode_sim_accumulator = 0.0
        gv._episode_index = 0

        gv._maybe_log_scene_episode(0.01)

        files = sorted(self._log_dir.glob("scene_episode_*.json"))
        self.assertEqual(len(files), 1, "应写入一条 Episode JSON")
        data = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(data.get("episode_index"), 1)
        self.assertIn("sim_time_end", data)
        self.assertIn("entity_count", data)
        self.assertIn("timestamp_utc", data)
        self.assertIn("sr_organism_peak", data)
        self.assertIsNone(data.get("sr_play_goals_config"))
        self.assertIsNone(data.get("sr_play_goals_satisfied"))
        self.assertFalse(data.get("sr_extinction_pause_triggered"))

    def test_episode_log_play_goals_and_extinction_flags(self) -> None:
        gv = GameViewport()
        gv._episode_log_enabled = True
        gv._episode_duration_sim_time = 0.001
        gv._using_scene_runtime = True
        gv._scene_runtime_time = 200.0
        gv._sr_pop_peak = 7
        gv._sr_play_goals = {"survive_seconds": 100, "peak_population": 5, "pause_on_complete": True}
        gv._sr_victory_pause_done = True
        gv._sr_extinction_pause_done = False
        gv.scene_runtime_entities = []
        gv._episode_sim_accumulator = 0.0
        gv._episode_index = 0
        gv._maybe_log_scene_episode(0.01)
        data = json.loads(
            sorted(self._log_dir.glob("scene_episode_*.json"))[0].read_text(encoding="utf-8")
        )
        self.assertTrue(data.get("sr_play_goals_satisfied"))
        self.assertTrue(data.get("sr_play_goals_victory_pause_triggered"))
        self.assertFalse(data.get("sr_extinction_pause_triggered"))

    def test_env_lotucosm_episode_log_enables_flag(self) -> None:
        with patch.dict(
            os.environ,
            {"LOTUCOSM_EPISODE_LOG": "1", "LOTUCOSM_EPISODE_DURATION": "60"},
            clear=False,
        ):
            gv = GameViewport()
        self.assertTrue(gv._episode_log_enabled)
        self.assertEqual(gv._episode_duration_sim_time, 60.0)


if __name__ == "__main__":
    unittest.main()
