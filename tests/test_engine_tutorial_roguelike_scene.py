# -*- coding: utf-8
"""织机教程 · dungeon_01.pond 场景契约。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCENE = _ROOT / "projects" / "织机教程-迷你Roguelike" / "scenes" / "dungeon_01.pond"
_MANIFEST = _ROOT / "projects" / "织机教程-迷你Roguelike" / "assets" / "manifest.json"


class EngineTutorialRoguelikeSceneTests(unittest.TestCase):
    def _load(self) -> dict:
        self.assertTrue(_SCENE.is_file(), f"missing {_SCENE}")
        return json.loads(_SCENE.read_text(encoding="utf-8"))

    def test_player_enemies_exit_scripts_and_visual(self) -> None:
        data = self._load()
        by_id = {e["id"]: e for e in data["entities"]}
        player = by_id["player_rl"]
        self.assertIn("sr_visual", player)
        self.assertEqual(player["sr_visual"].get("sprite"), "player")
        enemies = [e for e in data["entities"] if e.get("id", "").startswith("enemy_")]
        self.assertGreaterEqual(len(enemies), 2)
        for e in enemies:
            self.assertEqual(e.get("sr_visual", {}).get("sprite"), "slime")
        names = {s["name"] for s in player.get("scripts", [])}
        self.assertIn("player_controller", names)
        self.assertNotIn("game_director", names)
        level = by_id["level_01"]
        self.assertEqual(level.get("type"), "game_prop")
        dir_names = {s["name"] for s in level.get("scripts", [])}
        self.assertIn("game_director", dir_names)
        self.assertEqual(data["sr_play_goals"].get("player_id"), "player_rl")

    def test_hud_victory_goal_and_game_mode(self) -> None:
        data = self._load()
        self.assertTrue(data.get("sr_game_mode"))
        goals = data["sr_play_goals"]
        self.assertEqual(goals.get("hud_victory_key"), "dungeon_clear")
        self.assertEqual(goals.get("hud_defeat_key"), "player_dead")
        self.assertFalse(data.get("sr_pause_on_extinction"))
        self.assertFalse(data["sr_play_goals"].get("pause_on_complete"))
        player = next(e for e in data["entities"] if e["id"] == "player_rl")
        self.assertEqual(player.get("type"), "game_actor")
        self.assertNotIn("energy", player)

    def test_assets_manifest(self) -> None:
        self.assertTrue(_MANIFEST.is_file())
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("player", data.get("sprites", {}))
        self.assertIn("player_walk", data.get("animations", {}))


if __name__ == "__main__":
    unittest.main()
