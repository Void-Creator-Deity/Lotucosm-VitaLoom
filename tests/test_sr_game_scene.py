# -*- coding: utf-8
"""游戏场景归一化：旧 PVAEC 实体迁移为 game_actor/game_prop。"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_game_scene import normalize_entity_for_game, normalize_game_scene_data

_TUTORIAL = "workspace/projects/samples/织机教程-迷你Roguelike"


class SrGameSceneTests(unittest.TestCase):
    def test_migrate_legacy_wall_well(self) -> None:
        raw = {
            "id": "wall_n",
            "name": "墙·北",
            "type": "environment_well",
            "position": [460.0, 120.0],
            "radius": 200.0,
            "scripts": [],
        }
        out = normalize_entity_for_game(raw)
        self.assertEqual(out["type"], "game_prop")
        self.assertEqual(out["radius"], 28.0)
        self.assertTrue(out["pinned"])
        self.assertEqual(out["sr_visual"]["sprite"], "wall")

    def test_migrate_player_and_exit(self) -> None:
        player = normalize_entity_for_game(
            {"id": "player_rl", "type": "organism", "position": [0, 0], "energy": 100}
        )
        self.assertEqual(player["type"], "game_actor")
        self.assertNotIn("energy", player)
        self.assertEqual(player["sr_visual"]["sprite"], "player")

        exit_e = normalize_entity_for_game({"id": "exit_gate", "type": "nutrient", "position": [0, 0]})
        self.assertEqual(exit_e["type"], "game_prop")
        self.assertEqual(exit_e["sr_visual"]["sprite"], "exit")

    def test_normalize_scene_preserves_configured_completion_pause(self) -> None:
        scene = {
            "entities": [
                {"id": "player_rl", "type": "organism", "position": [0, 0]},
                {"id": "wall_n", "name": "墙", "type": "environment_well", "position": [0, 0], "radius": 200},
            ],
            "sr_play_goals": {"pause_on_complete": True, "hud_victory_key": "dungeon_clear"},
            "sr_pause_on_extinction": True,
        }
        out = normalize_game_scene_data(scene, _TUTORIAL)
        self.assertTrue(out["sr_game_mode"])
        self.assertFalse(out["sr_pause_on_extinction"])
        self.assertTrue(out["sr_play_goals"]["pause_on_complete"])
        self.assertEqual(out["entities"][0]["type"], "game_actor")


if __name__ == "__main__":
    unittest.main()
