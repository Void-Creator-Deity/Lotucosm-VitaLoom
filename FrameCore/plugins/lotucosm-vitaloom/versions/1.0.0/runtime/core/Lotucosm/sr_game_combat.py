# -*- coding: utf-8
"""游戏近战：扇形判定（参考 rift-delve combat/melee.js）。"""

from __future__ import annotations

import math


def enemy_in_melee_arc(
    px: float,
    py: float,
    angle: float,
    reach: float,
    arc_half: float,
    ex: float,
    ey: float,
    enemy_radius: float,
) -> bool:
    dx = ex - px
    dy = ey - py
    dist = math.hypot(dx, dy)
    if dist > reach + enemy_radius:
        return False
    a = math.atan2(dy, dx)
    diff = a - angle
    while diff > math.pi:
        diff -= math.pi * 2.0
    while diff < -math.pi:
        diff += math.pi * 2.0
    return abs(diff) <= arc_half


def pick_melee_target_in_arc(
    px: float,
    py: float,
    angle: float,
    reach: float,
    arc_half: float,
    peers: tuple,
) -> object | None:
    best = None
    best_gap = 1e18
    for p in peers:
        eid = str(getattr(p, "id", ""))
        if not eid.startswith("enemy_"):
            continue
        ex, ey = float(p.position[0]), float(p.position[1])
        er = float(getattr(p, "radius", 16.0))
        if not enemy_in_melee_arc(px, py, angle, reach, arc_half, ex, ey, er):
            continue
        gap = float(getattr(p, "surface_gap", 1e9))
        if gap < best_gap:
            best_gap = gap
            best = p
    return best
