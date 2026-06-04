# -*- coding: utf-8
"""教程工程推断与 Node sr_visual 序列化。"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_game_defaults import (
    default_sr_visual_for_entity,
    infer_engine_game_project,
    infer_sr_game_mode,
    normalize_sr_play_goals_for_game_mode,
)
from core.VitaLoom.tools.selection_tool import Node


class SrGameDefaultsTests(unittest.TestCase):
    def test_infer_tutorial_project(self) -> None:
        root = "projects/织机教程-迷你Roguelike"
        self.assertTrue(infer_engine_game_project(root))

    def test_infer_game_mode_from_project_even_if_scene_old(self) -> None:
        scene = {"entities": [{"id": "player_rl", "type": "organism"}]}
        self.assertTrue(
            infer_sr_game_mode(scene, "projects/织机教程-迷你Roguelike")
        )

    def test_default_visual_by_id(self) -> None:
        v = default_sr_visual_for_entity("enemy_01", "organism")
        self.assertEqual(v.sprite, "slime")

    def test_node_roundtrip_sr_visual(self) -> None:
        n = Node("player_rl", 1.0, 2.0, "game_actor")
        n.sr_visual = {"sprite": "player", "flip_x": True}
        d = n.to_dict()
        self.assertEqual(d["sr_visual"]["sprite"], "player")
        self.assertTrue(d["sr_visual"]["flip_x"])

    def test_game_mode_disables_victory_pause(self) -> None:
        goals = normalize_sr_play_goals_for_game_mode({"pause_on_complete": True})
        self.assertFalse(goals["pause_on_complete"])

    def test_resolve_player_id_from_goals(self) -> None:
        from core.Lotucosm.sr_game_contract import resolve_player_id

        scene = {"sr_play_goals": {"player_id": "hero_01"}}
        self.assertEqual(resolve_player_id(scene), "hero_01")
        self.assertEqual(resolve_player_id({}), "player_rl")


if __name__ == "__main__":
    unittest.main()
