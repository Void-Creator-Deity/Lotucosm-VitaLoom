# -*- coding: utf-8
"""游戏轨接触：边墙 AABB + 程序化柱圆盘 + mover 互斥（织机教程与任意 game_mode 场景）。"""

from __future__ import annotations

import math
from typing import Any, Sequence, Tuple

from core.Lotucosm.sr_game_entity_kind import is_game_mover, is_game_wall
from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.pvaec_contacts import _circle_hit


def is_game_wall_bar(entity: Any) -> bool:
    """固定边墙：横条 AABB（wall_n1 / wall_s1 等）。"""
    if not is_game_wall(entity):
        return False
    eid = str(getattr(entity, "id", ""))
    return not eid.startswith("proc_wall_")


def is_game_wall_disk(entity: Any) -> bool:
    """程序化障碍柱：圆盘静态体（rift-delve 风格）。"""
    eid = str(getattr(entity, "id", ""))
    return eid.startswith("proc_wall_") or (
        is_game_wall(entity) and eid.startswith("proc_")
    )


def wall_aabb(entity: Any) -> Tuple[float, float, float, float]:
    cx = float(entity.position[0])
    cy = float(entity.position[1])
    r = max(4.0, float(getattr(entity, "radius", 18.0)))
    hw = r
    hh = max(4.0, r * 0.35)
    return cx - hw, cy - hh, cx + hw, cy + hh


def _circle_vs_aabb(
    cx: float,
    cy: float,
    radius: float,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> Tuple[float, float, float] | None:
    closest_x = max(xmin, min(cx, xmax))
    closest_y = max(ymin, min(cy, ymax))
    dx = cx - closest_x
    dy = cy - closest_y
    dist_sq = dx * dx + dy * dy
    r_sq = radius * radius
    if dist_sq >= r_sq:
        return None
    if dist_sq > 1e-12:
        dist = math.sqrt(dist_sq)
        nx, ny = dx / dist, dy / dist
        push = radius - dist
        return nx, ny, push
    left = cx - xmin
    right = xmax - cx
    top = cy - ymin
    bottom = ymax - cy
    best = min(left, right, top, bottom)
    if best == left:
        return -1.0, 0.0, radius + left
    if best == right:
        return 1.0, 0.0, radius + right
    if best == top:
        return 0.0, -1.0, radius + top
    return 0.0, 1.0, radius + bottom


def _game_inv_mass(entity: Any) -> float:
    if entity is None or not is_game_mover(entity):
        return 0.0
    r = max(4.0, float(getattr(entity, "radius", 18.0)))
    return 1.0 / (r * r)


def _apply_game_impulse(
    a: Any,
    b: Any,
    nx: float,
    ny: float,
    *,
    restitution: float,
    friction: float,
) -> None:
    im_a = _game_inv_mass(a)
    im_b = _game_inv_mass(b)
    if im_a <= 0.0 and im_b <= 0.0:
        return

    vax = float(a.velocity[0])
    vay = float(a.velocity[1])
    vbx = float(b.velocity[0]) if hasattr(b, "velocity") else 0.0
    vby = float(b.velocity[1]) if hasattr(b, "velocity") else 0.0
    rvx = vax - vbx
    rvy = vay - vby
    vn = rvx * nx + rvy * ny
    if vn > 0.0:
        return

    inv_sum = im_a + im_b
    if inv_sum <= 1e-12:
        return
    j = -(1.0 + restitution) * vn / inv_sum
    ix = j * nx
    iy = j * ny
    if im_a > 0.0:
        a.velocity[0] = vax + ix * im_a
        a.velocity[1] = vay + iy * im_a
    if im_b > 0.0 and hasattr(b, "velocity"):
        b.velocity[0] = vbx - ix * im_b
        b.velocity[1] = vby - iy * im_b


class _StaticDisk:
    """占位静态圆，供冲量/位置修正（无 velocity/position 写回）。"""

    __slots__ = ("position", "radius", "velocity")

    def __init__(self, x: float, y: float, r: float) -> None:
        self.position = [x, y]
        self.radius = r
        self.velocity = [0.0, 0.0]


def _hard_push_game(a: Any, b: Any, nx: float, ny: float, pen: float) -> None:
    im_a = _game_inv_mass(a)
    im_b = _game_inv_mass(b)
    inv_sum = im_a + im_b
    if inv_sum <= 1e-12:
        if im_a > 0.0:
            a.position[0] += nx * pen
            a.position[1] += ny * pen
        return
    if im_a > 0.0:
        a.position[0] += nx * pen * (im_a / inv_sum)
        a.position[1] += ny * pen * (im_a / inv_sum)
    if im_b > 0.0 and hasattr(b, "position"):
        b.position[0] -= nx * pen * (im_b / inv_sum)
        b.position[1] -= ny * pen * (im_b / inv_sum)


def _resolve_mover_vs_static_disk(mover: Any, ox: float, oy: float, orad: float, config: SrPhysics2DConfig) -> None:
    hit = _circle_hit(
        float(mover.position[0]),
        float(mover.position[1]),
        float(mover.radius),
        ox,
        oy,
        orad,
    )
    if hit is None:
        return
    nx, ny, pen = hit
    if _game_inv_mass(mover) <= 0.0:
        return
    _apply_game_impulse(
        mover,
        _StaticDisk(ox, oy, orad),
        nx,
        ny,
        restitution=config.restitution,
        friction=config.friction,
    )
    _hard_push_game(mover, _StaticDisk(ox, oy, orad), nx, ny, pen)


def resolve_game_wall_bars(entities: Sequence[Any], *, config: SrPhysics2DConfig) -> None:
    bars = [e for e in entities if is_game_wall_bar(e)]
    movers = [e for e in entities if is_game_mover(e)]
    if not bars or not movers:
        return
    bounce = max(0.0, min(1.0, config.boundary_bounce))
    for mover in movers:
        cx = float(mover.position[0])
        cy = float(mover.position[1])
        r = max(2.0, float(getattr(mover, "radius", 18.0)))
        vx = float(mover.velocity[0])
        vy = float(mover.velocity[1])
        for wall in bars:
            hit = _circle_vs_aabb(cx, cy, r, *wall_aabb(wall))
            if hit is None:
                continue
            nx, ny, push = hit
            cx += nx * push
            cy += ny * push
            vn = vx * nx + vy * ny
            if vn < 0.0:
                vx -= vn * nx * (1.0 + bounce * 0.2)
                vy -= vn * ny * (1.0 + bounce * 0.2)
        mover.position[0] = cx
        mover.position[1] = cy
        mover.velocity[0] = vx
        mover.velocity[1] = vy


def resolve_game_wall_disks(entities: Sequence[Any], *, config: SrPhysics2DConfig) -> None:
    disks = [e for e in entities if is_game_wall_disk(e)]
    movers = [e for e in entities if is_game_mover(e)]
    if not disks or not movers:
        return
    for mover in movers:
        for disk in disks:
            _resolve_mover_vs_static_disk(
                mover,
                float(disk.position[0]),
                float(disk.position[1]),
                float(disk.radius),
                config,
            )


def resolve_game_mover_separation(
    entities: Sequence[Any],
    *,
    padding: float = 8.0,
    config: SrPhysics2DConfig | None = None,
) -> None:
    movers = [e for e in entities if is_game_mover(e)]
    cfg = config or SrPhysics2DConfig()
    for i in range(len(movers)):
        for j in range(i + 1, len(movers)):
            a = movers[i]
            b = movers[j]
            hit = _circle_hit(
                float(a.position[0]),
                float(a.position[1]),
                float(a.radius),
                float(b.position[0]),
                float(b.position[1]),
                float(b.radius),
            )
            if hit is None:
                continue
            nx, ny, pen = hit
            min_extra = max(0.0, padding)
            if pen < min_extra:
                pen = min_extra
            _apply_game_impulse(
                a,
                b,
                nx,
                ny,
                restitution=cfg.restitution * 0.5,
                friction=cfg.friction,
            )
            _hard_push_game(a, b, nx, ny, pen)


def resolve_game_contacts(entities: Sequence[Any], *, config: SrPhysics2DConfig) -> None:
    """游戏轨统一接触（教程 Roguelike / 任意 sr_game_mode）。"""
    iters = max(1, int(config.game_contact_iterations))
    for _ in range(iters):
        resolve_game_wall_bars(entities, config=config)
        resolve_game_wall_disks(entities, config=config)
        resolve_game_mover_separation(
            entities,
            padding=float(config.game_mover_padding),
            config=config,
        )


# 兼容旧 API（无 config 时用默认）
def resolve_game_wall_collisions(entities: Sequence[Any], *, config: SrPhysics2DConfig | None = None) -> None:
    resolve_game_wall_bars(entities, config=config or SrPhysics2DConfig())
