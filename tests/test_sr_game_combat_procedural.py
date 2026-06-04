# -*- coding: utf-8
"""近战扇形与程序化障碍。"""
from __future__ import annotations

import math
import unittest

from core.Lotucosm.sr_game_combat import enemy_in_melee_arc, pick_melee_target_in_arc
from core.Lotucosm.sr_game_procedural import generate_wall_spawns, is_spawn_clear
from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot


class SrGameCombatTests(unittest.TestCase):
    def test_arc_in_front_not_behind(self) -> None:
        px, py = 100.0, 100.0
        angle = 0.0
        self.assertTrue(enemy_in_melee_arc(px, py, angle, 40.0, 0.7, 130.0, 100.0, 16.0))
        self.assertFalse(enemy_in_melee_arc(px, py, angle, 40.0, 0.7, 70.0, 100.0, 16.0))

    def test_pick_closest_in_arc(self) -> None:
        peers = (
            RuntimePeerSnapshot("enemy_far", "game_actor", (140.0, 100.0), 16.0, 40.0, 8.0),
            RuntimePeerSnapshot("enemy_near", "game_actor", (120.0, 100.0), 16.0, 20.0, 0.0),
        )
        t = pick_melee_target_in_arc(100.0, 100.0, 0.0, 40.0, 0.7, peers)
        self.assertIsNotNone(t)
        assert t is not None
        self.assertEqual(t.id, "enemy_near")


class SrGameProceduralTests(unittest.TestCase):
    def test_generate_respects_reserved(self) -> None:
        spawns = generate_wall_spawns(
            920,
            620,
            4,
            seed=99,
            reserved=[(460.0, 310.0, 80.0)],
        )
        self.assertGreaterEqual(len(spawns), 1)
        for s in spawns:
            x, y = s["position"]
            self.assertGreater(math.hypot(x - 460.0, y - 310.0), 60.0)

    def test_same_seed_same_layout(self) -> None:
        a = generate_wall_spawns(920, 620, 3, seed=7)
        b = generate_wall_spawns(920, 620, 3, seed=7)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
