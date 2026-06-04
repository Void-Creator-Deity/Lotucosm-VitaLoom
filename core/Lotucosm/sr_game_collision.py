# -*- coding: utf-8
"""游戏模式：圆 vs 墙 — 兼容层，实现已迁入 ``sr_physics2d.game_contacts``。"""

from __future__ import annotations

from core.Lotucosm.sr_physics2d.game_contacts import (
    is_game_wall_bar,
    is_game_wall_disk,
    resolve_game_contacts,
    resolve_game_mover_separation,
    resolve_game_wall_bars,
    resolve_game_wall_collisions,
    resolve_game_wall_disks,
    wall_aabb,
)

__all__ = [
    "wall_aabb",
    "resolve_game_wall_collisions",
    "resolve_game_wall_bars",
    "resolve_game_wall_disks",
    "resolve_game_mover_separation",
    "resolve_game_contacts",
    "is_game_wall_bar",
    "is_game_wall_disk",
]
