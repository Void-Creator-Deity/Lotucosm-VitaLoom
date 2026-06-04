# -*- coding: utf-8 -*-
"""
get_sr_ecology_snapshot：暂停态仍有人口与扩展字段。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import os
import unittest

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import GameViewport


class GameViewportEcologySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_paused_snapshot_keeps_population(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = True
        gv._scene_runtime_time = 42.5
        gv._sr_pop_peak = 7
        gv._sr_play_goals = {"survive_seconds": 100, "peak_population": 5}
        o1 = gv._SceneRuntimeEntity("o1", "organism", (10.0, 10.0), 12.0)
        o1.energy = 50.0
        o1.generation = 2
        o1.sr_debug_hud = {"wander_amp": 1.0}
        o2 = gv._SceneRuntimeEntity("o2", "organism", (20.0, 20.0), 12.0)
        o2.energy = 30.0
        o2.generation = 4
        o2.sr_debug_hud = {"wander_amp": 3.0}
        s1 = gv._SceneRuntimeEntity("s1", "sensor", (5.0, 5.0), 8.0)
        a1 = gv._SceneRuntimeEntity("a1", "actuator", (15.0, 15.0), 8.0)
        gv._sr_signal_edges = [
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.2},
        ]
        gv.scene_runtime_entities = [o1, o2, s1, a1]
        snap = gv.get_sr_ecology_snapshot()
        self.assertTrue(snap["sim_running"])
        self.assertFalse(snap["active"])
        self.assertTrue(snap["paused"])
        self.assertAlmostEqual(snap["sim_time"], 42.5)
        self.assertEqual(snap["population"], 2)
        self.assertEqual(snap["population_peak"], 7)
        self.assertAlmostEqual(snap["avg_generation"], 3.0)
        self.assertAlmostEqual(snap["total_energy"], 80.0)
        self.assertFalse(snap["play_goals_satisfied"])
        self.assertEqual(snap["membrane_sensor_count"], 1)
        self.assertAlmostEqual(snap["mean_edge_weight"], 1.2)

    def test_not_running_snapshot_defaults(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = False
        gv.is_playing = False
        snap = gv.get_sr_ecology_snapshot()
        self.assertFalse(snap["sim_running"])
        self.assertFalse(snap["active"])
        self.assertEqual(snap["population"], 0)
        self.assertIsNone(snap["play_goals_satisfied"])


if __name__ == "__main__":
    unittest.main()
