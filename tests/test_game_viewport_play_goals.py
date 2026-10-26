# -*- coding: utf-8 -*-
"""
sr_play_goals 与胜利/灭绝暂停逻辑。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import (
    GameViewport,
    sr_all_play_goals_satisfied,
    sr_pause_on_complete_enabled,
    sr_play_goals_episode_config_snapshot,
)


class GameViewportPlayGoalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_sr_all_play_goals_satisfied_and(self) -> None:
        g = {"survive_seconds": 10, "peak_population": 3}
        self.assertFalse(sr_all_play_goals_satisfied(g, 5.0, 5))
        self.assertTrue(sr_all_play_goals_satisfied(g, 10.0, 3))

    def test_sr_pause_on_complete_strict(self) -> None:
        self.assertTrue(sr_pause_on_complete_enabled({"pause_on_complete": True}))
        self.assertFalse(sr_pause_on_complete_enabled({}))

    def test_episode_config_snapshot(self) -> None:
        s = sr_play_goals_episode_config_snapshot(
            {"survive_seconds": 1, "pause_on_complete": True, "evil": [1]}
        )
        self.assertEqual(s, {"survive_seconds": 1, "pause_on_complete": True})

    def test_victory_pause_calls_pause_once(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_demo_legend = None
        gv._sr_play_goals = {
            "survive_seconds": 10,
            "peak_population": 2,
            "pause_on_complete": True,
        }
        gv._scene_runtime_time = 15.0
        gv._sr_pop_peak = 3
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (10.0, 10.0), 12.0),
        ]
        gv._pause_simulation = MagicMock()
        gv._maybe_try_sr_victory_pause()
        gv._pause_simulation.assert_called_once()

    def test_game_hud_victory_pause_calls_pause_once(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_game_mode = True
        gv._sr_demo_legend = None
        gv._sr_play_goals = {
            "hud_victory_key": "dungeon_clear",
            "pause_on_complete": True,
        }
        gv._scene_runtime_time = 5.0
        gv._sr_pop_peak = 0
        ent = gv._SceneRuntimeEntity("level_01", "game_prop", (0.0, 0.0), 1.0)
        ent.sr_debug_hud = {"dungeon_clear": 1}
        gv.scene_runtime_entities = [ent]
        gv._pause_simulation = MagicMock()
        gv._maybe_try_sr_victory_pause()
        gv._pause_simulation.assert_called_once()

    def test_pvaec_goals_notice_does_not_pause_or_write_final_log(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_game_mode = False
        gv._sr_demo_legend = None
        gv._sr_victory_notice_done = False
        gv._sr_victory_pause_done = False
        gv._sr_play_goals = {
            "survive_seconds": 10,
            "peak_population": 2,
            "pause_on_complete": False,
        }
        gv._scene_runtime_time = 15.0
        gv._sr_pop_peak = 3
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("o1", "organism", (10.0, 10.0), 12.0),
        ]
        gv._pause_simulation = MagicMock()
        gv._write_sr_session_summary = MagicMock()
        gv._show_session_banner = MagicMock()
        gv._refresh_sr_hud = MagicMock()
        gv._maybe_try_sr_play_goals_notice()
        self.assertTrue(gv._sr_victory_notice_done)
        gv._pause_simulation.assert_not_called()
        gv._write_sr_session_summary.assert_not_called()

    def test_extinction_pause_when_no_orgs(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_pause_on_extinction = True
        gv._scene_runtime_time = 5.0
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("n1", "nutrient", (50.0, 50.0), 11.0),
        ]
        gv._pause_simulation = MagicMock()
        gv._maybe_try_sr_extinction_pause()
        gv._pause_simulation.assert_called_once()

    def test_pvaec_extinction_without_flag_does_not_pause_or_write_final_log(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_game_mode = False
        gv._sr_pause_on_extinction = False
        gv._sr_extinction_pause_done = False
        gv._sr_victory_pause_done = False
        gv._scene_runtime_time = 5.0
        gv.scene_runtime_entities = [
            gv._SceneRuntimeEntity("n1", "nutrient", (50.0, 50.0), 11.0),
        ]
        gv._pause_simulation = MagicMock()
        gv._write_sr_session_summary = MagicMock()
        gv._maybe_try_sr_extinction_pause()
        self.assertFalse(gv._sr_extinction_pause_done)
        gv._pause_simulation.assert_not_called()
        gv._write_sr_session_summary.assert_not_called()


if __name__ == "__main__":
    unittest.main()
