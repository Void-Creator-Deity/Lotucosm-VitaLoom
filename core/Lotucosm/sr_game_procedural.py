# -*- coding: utf-8
"""游戏模式程序化障碍（参考 rift-delve terrain.js generateObstacles）。"""

from __future__ import annotations

import math
import random
from typing import Any, Mapping, Sequence


def _circle_hit(ax: float, ay: float, ar: float, bx: float, by: float, br: float) -> bool:
    return math.hypot(bx - ax, by - ay) < ar + br


def is_spawn_clear(
    x: float,
    y: float,
    radius: float,
    reserved: Sequence[tuple[float, float, float]],
) -> bool:
    for ox, oy, orad in reserved:
        if _circle_hit(x, y, radius, ox, oy, orad):
            return False
    return True


def generate_wall_spawns(
    width: float,
    height: float,
    count: int,
    *,
    seed: int = 42,
    reserved: Sequence[tuple[float, float, float]] = (),
    id_prefix: str = "proc_wall_",
    margin: float = 80.0,
) -> list[dict[str, Any]]:
    """在中部区域随机放置 pinned 墙条 game_prop。"""
    rng = random.Random(int(seed))
    spawns: list[dict[str, Any]] = []
    taken: list[tuple[float, float, float]] = list(reserved)
    for i in range(max(0, int(count))):
        placed = False
        for _ in range(48):
            x = margin + rng.random() * max(1.0, width - 2.0 * margin)
            y = margin + rng.random() * max(1.0, height - 2.0 * margin)
            r = 20.0 + rng.random() * 10.0
            pad = r + 14.0
            if not is_spawn_clear(x, y, pad, taken):
                continue
            spec: dict[str, Any] = {
                "type": "game_prop",
                "id": f"{id_prefix}{i + 1:02d}",
                "position": [round(x, 1), round(y, 1)],
                "radius": round(r, 1),
                "pinned": True,
                "sr_visual": {"sprite": "wall", "alpha": 0.92},
            }
            spawns.append(spec)
            taken.append((x, y, pad))
            placed = True
            break
        if not placed:
            break
    return spawns


def proc_seed_from_scene(scene_data: Mapping[str, Any]) -> tuple[int, int]:
    pond = scene_data.get("pond_config") if isinstance(scene_data.get("pond_config"), dict) else {}
    seed = int(pond.get("proc_seed", 12345))
    count = int(pond.get("proc_obstacles", 5))
    return seed, max(0, min(count, 12))
