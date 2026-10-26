# -*- coding: utf-8
"""游戏模式墙碰撞。

职责: 锁定 Roguelike 墙体 AABB、玩家推出和敌人分离行为。
排错: 失败时检查 sr_game_collision 的半径、墙体 sprite 和 actor 分类。
"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_game_collision import resolve_game_wall_collisions, wall_aabb


class _Ent:
    def __init__(self, eid: str, et: str, x: float, y: float, r: float, *, pinned: bool = False, sprite: str = ""):
        self.id = eid
        self.entity_type = et
        self.position = [x, y]
        self.radius = r
        self.velocity = [40.0, 0.0]
        self.pinned = pinned
        if sprite:
            self.sr_visual = type("V", (), {"sprite": sprite})()


class SrGameCollisionTests(unittest.TestCase):
    def test_wall_aabb_is_flat(self) -> None:
        wall = _Ent("wall_n1", "game_prop", 100.0, 80.0, 28.0, pinned=True, sprite="wall")
        xmin, ymin, xmax, ymax = wall_aabb(wall)
        self.assertLess(ymax - ymin, xmax - xmin)

    def test_player_pushed_out_of_wall(self) -> None:
        from core.Lotucosm.sr_game_collision import resolve_game_wall_collisions

        wall = _Ent("wall_n1", "game_prop", 100.0, 80.0, 28.0, pinned=True, sprite="wall")
        player = _Ent("player_rl", "game_actor", 100.0, 80.0, 22.0)
        resolve_game_wall_collisions([wall, player])
        self.assertGreater(abs(player.position[0] - 100.0) + abs(player.position[1] - 80.0), 0.01)

    def test_mover_separation(self) -> None:
        from core.Lotucosm.sr_game_collision import resolve_game_mover_separation

        a = _Ent("enemy_01", "game_actor", 100.0, 100.0, 16.0)
        b = _Ent("enemy_02", "game_actor", 108.0, 100.0, 16.0)
        resolve_game_mover_separation([a, b])
        self.assertGreater(abs(a.position[0] - b.position[0]), 20.0)


if __name__ == "__main__":
    unittest.main()
