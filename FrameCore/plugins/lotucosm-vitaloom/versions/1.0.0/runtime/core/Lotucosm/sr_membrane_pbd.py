# -*- coding: utf-8
"""质膜轮廓轻量 PBD 约束（可选，性能不足时自动跳过）。"""

from __future__ import annotations

import math
import time
from typing import Any, Sequence


def refine_membrane_offsets_pbd(
    offsets: list[float],
    *,
    hub: Any,
    anchors: Sequence[tuple[float, float, float]],
    segments: int,
    base_radius: float,
    dt: float,
    iterations: int = 2,
    stiffness: float = 0.35,
    budget_ms: float = 2.0,
) -> list[float]:
    """在径向 offset 上施加距离约束，稳定大变形。"""
    if not offsets or segments < 8 or dt <= 0.0:
        return offsets
    t0 = time.perf_counter()
    n = len(offsets)
    cx = float(hub.position[0])
    cy = float(hub.position[1])
    rest_r = max(20.0, float(base_radius))
    pts: list[list[float]] = []
    for i in range(n):
        ang = (i / n) * math.tau
        r = rest_r + float(offsets[i])
        pts.append([cx + math.cos(ang) * r, cy + math.sin(ang) * r])

    for _ in range(max(1, iterations)):
        if (time.perf_counter() - t0) * 1000.0 > budget_ms:
            break
        for i in range(n):
            j = (i + 1) % n
            dx = pts[j][0] - pts[i][0]
            dy = pts[j][1] - pts[i][1]
            dist = math.hypot(dx, dy) + 1e-9
            target = 2.0 * math.pi * rest_r / n
            err = dist - target
            corr = err * 0.5 * stiffness
            nx, ny = dx / dist, dy / dist
            pts[i][0] += nx * corr * 0.5
            pts[i][1] += ny * corr * 0.5
            pts[j][0] -= nx * corr * 0.5
            pts[j][1] -= ny * corr * 0.5
        for ax, ay, ar in anchors:
            best_i = 0
            best_d = 1e18
            for i in range(n):
                d = (pts[i][0] - ax) ** 2 + (pts[i][1] - ay) ** 2
                if d < best_d:
                    best_d = d
                    best_i = i
            tx = ax + (ax - cx) * 0.08
            ty = ay + (ay - cy) * 0.08
            pts[best_i][0] += (tx - pts[best_i][0]) * stiffness * 0.4
            pts[best_i][1] += (ty - pts[best_i][1]) * stiffness * 0.4

    out: list[float] = []
    for i in range(n):
        ang = (i / n) * math.tau
        pr = math.hypot(pts[i][0] - cx, pts[i][1] - cy)
        out.append(pr - rest_r)
    return out
