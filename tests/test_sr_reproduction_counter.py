# -*- coding: utf-8
"""SR 繁殖事件计数与 GameViewport 快照。"""
from __future__ import annotations

import os
import unittest

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.viewports.game_viewport import GameViewport


class SrReproductionCounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_spawn_increments_reproduction_events(self) -> None:
        gv = GameViewport()
        gv._sr_evo_pop_cap = 96
        req = {
            "type": "organism",
            "position": (10.0, 10.0),
            "energy": 80.0,
            "generation": 2,
        }
        gv._process_sr_spawn_requests([req], None)
        self.assertEqual(gv._sr_reproduction_events, 1)
        self.assertEqual(
            sum(1 for e in gv.scene_runtime_entities if str(e.entity_type) == "organism"),
            1,
        )

    def test_snapshot_exports_reproduction_events(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._sr_reproduction_events = 3
        ent = gv._SceneRuntimeEntity("o1", "organism", (0.0, 0.0), 12.0)
        gv.scene_runtime_entities = [ent]
        snap = gv.get_sr_ecology_snapshot()
        self.assertEqual(snap["reproduction_events"], 3)


if __name__ == "__main__":
    unittest.main()
