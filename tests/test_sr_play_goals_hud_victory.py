# -*- coding: utf-8
"""sr_play_goals HUD 键通关/失败判定。"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from core.VitaLoom.viewports.game_viewport import (
    sr_all_play_goals_satisfied,
    sr_hud_victory_satisfied,
)


class SrPlayGoalsHudVictoryTests(unittest.TestCase):
    def test_hud_key_detected(self) -> None:
        ent = MagicMock()
        ent.sr_debug_hud = {"dungeon_clear": 1}
        self.assertTrue(sr_hud_victory_satisfied("dungeon_clear", [ent]))

    def test_only_hud_goal(self) -> None:
        ent = MagicMock()
        ent.sr_debug_hud = {"dungeon_clear": 1}
        goals = {"hud_victory_key": "dungeon_clear", "pause_on_complete": True}
        self.assertTrue(sr_all_play_goals_satisfied(goals, 0.0, 0, [ent]))

    def test_hud_goal_not_met(self) -> None:
        goals = {"hud_victory_key": "dungeon_clear"}
        self.assertFalse(sr_all_play_goals_satisfied(goals, 0.0, 0, []))

    def test_defeat_key(self) -> None:
        ent = MagicMock()
        ent.sr_debug_hud = {"player_dead": 1}
        self.assertTrue(sr_hud_victory_satisfied("player_dead", [ent]))


if __name__ == "__main__":
    unittest.main()
