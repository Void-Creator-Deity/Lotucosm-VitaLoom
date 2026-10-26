# -*- coding: utf-8
"""PVAEC 轨圆体接触（organism / central_brain vs 静态营养/场域锚）。"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, Sequence

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig

_DYNAMIC_TYPES = frozenset({"organism", "central_brain"})
_STATIC_TYPES = frozenset({"nutrient", "environment_well"})


def _entity_type(entity: Any) -> str:
    return str(getattr(entity, "entity_type", ""))


def is_pvaec_dynamic_body(entity: Any) -> bool:
    if getattr(entity, "pinned", False) or getattr(entity, "membrane_locked", False):
        return False
    return _entity_type(entity) in _DYNAMIC_TYPES


def is_pvaec_static_disk(entity: Any) -> bool:
    return _entity_type(entity) in _STATIC_TYPES


def normalize_pvaec_broadphase(value: Any) -> str:
    """Return the canonical broadphase label used by every SR2D Adapter."""
    return str(value or "spatial_hash").strip().lower()


def inv_mass(entity: Any) -> float:
    if not is_pvaec_dynamic_body(entity):
        return 0.0
    r = max(8.0, float(getattr(entity, "radius", 18.0)))
    return 1.0 / (r * r)


def _circle_hit(
    ax: float,
    ay: float,
    ar: float,
    bx: float,
    by: float,
    br: float,
) -> tuple[float, float, float] | None:
    dx = ax - bx
    dy = ay - by
    dist = math.sqrt(dx * dx + dy * dy)
    min_dist = ar + br
    if dist >= min_dist:
        return None
    if dist > 1e-8:
        nx, ny = dx / dist, dy / dist
        return nx, ny, min_dist - dist
    return 1.0, 0.0, min_dist


def _apply_impulse(
    a: Any,
    b: Any,
    nx: float,
    ny: float,
    *,
    restitution: float,
    friction: float,
) -> None:
    im_a = inv_mass(a)
    im_b = inv_mass(b)
    if im_a <= 0.0 and im_b <= 0.0:
        return

    vax = float(a.velocity[0])
    vay = float(a.velocity[1])
    vbx = float(b.velocity[0])
    vby = float(b.velocity[1])
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
    if im_b > 0.0:
        b.velocity[0] = vbx - ix * im_b
        b.velocity[1] = vby - iy * im_b

    rvx = float(a.velocity[0]) - float(b.velocity[0])
    rvy = float(a.velocity[1]) - float(b.velocity[1])
    vt = rvx * (-ny) + rvy * nx
    jt = -vt / inv_sum if inv_sum > 1e-12 else 0.0
    jt = max(-abs(j * friction), min(abs(j * friction), jt))
    tx, ty = -ny, nx
    if im_a > 0.0:
        a.velocity[0] += tx * jt * im_a
        a.velocity[1] += ty * jt * im_a
    if im_b > 0.0:
        b.velocity[0] -= tx * jt * im_b
        b.velocity[1] -= ty * jt * im_b


def _separate(
    a: Any,
    b: Any,
    nx: float,
    ny: float,
    pen: float,
    *,
    slop: float,
    percent: float,
) -> None:
    im_a = inv_mass(a)
    im_b = inv_mass(b)
    corr = max(pen - slop, 0.0) * percent
    if corr <= 0.0:
        return
    inv_sum = im_a + im_b
    if inv_sum <= 1e-12:
        return
    if im_a > 0.0:
        a.position[0] += nx * corr * (im_a / inv_sum)
        a.position[1] += ny * corr * (im_a / inv_sum)
    if im_b > 0.0:
        b.position[0] -= nx * corr * (im_b / inv_sum)
        b.position[1] -= ny * corr * (im_b / inv_sum)


def _hard_push_apart(a: Any, b: Any, nx: float, ny: float, pen: float) -> None:
    im_a = inv_mass(a)
    im_b = inv_mass(b)
    inv_sum = im_a + im_b
    if inv_sum <= 1e-12:
        return
    if im_a > 0.0:
        share = im_a / inv_sum
        a.position[0] += nx * pen * share
        a.position[1] += ny * pen * share
    if im_b > 0.0:
        share = im_b / inv_sum
        b.position[0] -= nx * pen * share
        b.position[1] -= ny * pen * share


def _resolve_pair(
    a: Any,
    b: Any,
    config: SrPhysics2DConfig,
) -> None:
    hit = _circle_hit(
        float(a.position[0]),
        float(a.position[1]),
        float(a.radius),
        float(b.position[0]),
        float(b.position[1]),
        float(b.radius),
    )
    if hit is None:
        return
    nx, ny, pen = hit
    _apply_impulse(
        a,
        b,
        nx,
        ny,
        restitution=config.restitution,
        friction=config.friction,
    )
    _hard_push_apart(a, b, nx, ny, pen)
    _separate(
        a,
        b,
        nx,
        ny,
        pen,
        slop=config.contact_slop,
        percent=config.contact_correction,
    )


def _split_contact_bodies(
    entities: Sequence[Any],
) -> tuple[list[tuple[int, Any]], list[tuple[int, Any]]]:
    dynamics: list[tuple[int, Any]] = []
    statics: list[tuple[int, Any]] = []
    for index, entity in enumerate(entities):
        if is_pvaec_dynamic_body(entity):
            dynamics.append((index, entity))
        elif is_pvaec_static_disk(entity):
            statics.append((index, entity))
    return dynamics, statics


def _bruteforce_contact_pairs(
    dynamics: Sequence[tuple[int, Any]],
    statics: Sequence[tuple[int, Any]],
) -> list[tuple[Any, Any]]:
    pairs: list[tuple[Any, Any]] = []
    for i in range(len(dynamics)):
        for j in range(i + 1, len(dynamics)):
            pairs.append((dynamics[i][1], dynamics[j][1]))
        for _static_index, static in statics:
            pairs.append((dynamics[i][1], static))
    return pairs


def _body_radius(entity: Any) -> float:
    return max(0.0, float(getattr(entity, "radius", 18.0)))


def _covered_cells(
    entity: Any,
    cell_size: float,
    *,
    padding: float = 0.0,
) -> Iterable[tuple[int, int]]:
    px = float(entity.position[0])
    py = float(entity.position[1])
    radius = _body_radius(entity) + max(0.0, float(padding))
    min_x = math.floor((px - radius) / cell_size)
    max_x = math.floor((px + radius) / cell_size)
    min_y = math.floor((py - radius) / cell_size)
    max_y = math.floor((py + radius) / cell_size)
    for cell_x in range(int(min_x), int(max_x) + 1):
        for cell_y in range(int(min_y), int(max_y) + 1):
            yield cell_x, cell_y


def _pair_sort_key(
    pair: tuple[Any, Any],
    dynamic_order: dict[int, int],
    static_order: dict[int, int],
) -> tuple[int, int, int]:
    a, b = pair
    a_order = dynamic_order[id(a)]
    b_dynamic_order = dynamic_order.get(id(b))
    if b_dynamic_order is not None:
        return a_order, 0, b_dynamic_order
    return a_order, 1, static_order[id(b)]


def _spatial_hash_contact_pairs(
    dynamics: Sequence[tuple[int, Any]],
    statics: Sequence[tuple[int, Any]],
    *,
    contact_iterations: int,
) -> list[tuple[Any, Any]]:
    active = [entity for _index, entity in dynamics] + [entity for _index, entity in statics]
    if not active:
        return []
    max_radius = max(_body_radius(entity) for entity in active)
    cell_size = max(1.0, max_radius * 2.0)
    cells: dict[tuple[int, int], list[Any]] = defaultdict(list)
    for entity in active:
        for cell in _covered_cells(entity, cell_size):
            cells[cell].append(entity)

    dynamic_order = {id(entity): order for order, (_index, entity) in enumerate(dynamics)}
    static_order = {id(entity): order for order, (_index, entity) in enumerate(statics)}
    pair_by_ids: dict[tuple[int, int], tuple[Any, Any]] = {}
    query_padding = max_radius * max(0, int(contact_iterations)) * 4.0
    for dynamic_order_index, (_entity_index, dynamic) in enumerate(dynamics):
        nearby: dict[int, Any] = {}
        for cell in _covered_cells(dynamic, cell_size, padding=query_padding):
            for candidate in cells.get(cell, ()):
                nearby[id(candidate)] = candidate
        for candidate in nearby.values():
            if candidate is dynamic:
                continue
            candidate_dynamic_order = dynamic_order.get(id(candidate))
            if candidate_dynamic_order is not None:
                if candidate_dynamic_order <= dynamic_order_index:
                    continue
                pair = (dynamic, candidate)
            elif id(candidate) in static_order:
                pair = (dynamic, candidate)
            else:
                continue
            pair_by_ids[(id(pair[0]), id(pair[1]))] = pair

    return sorted(
        pair_by_ids.values(),
        key=lambda pair: _pair_sort_key(pair, dynamic_order, static_order),
    )


def build_pvaec_contact_pairs(
    entities: Sequence[Any],
    *,
    broadphase: str = "spatial_hash",
    contact_iterations: int = 1,
) -> list[tuple[Any, Any]]:
    dynamics, statics = _split_contact_bodies(entities)
    if not dynamics:
        return []
    mode = str(broadphase or "spatial_hash").strip().lower()
    if mode == "bruteforce":
        return _bruteforce_contact_pairs(dynamics, statics)
    if mode == "spatial_hash":
        return _spatial_hash_contact_pairs(
            dynamics,
            statics,
            contact_iterations=contact_iterations,
        )
    raise ValueError(f"unsupported PVAEC broadphase: {broadphase!r}")


def clamp_pvaec_bodies(
    entities: Iterable[Any],
    width: float,
    height: float,
    *,
    bounce: float,
) -> None:
    w, h = float(width), float(height)
    for e in entities:
        if not is_pvaec_dynamic_body(e):
            continue
        r = float(getattr(e, "radius", 18.0))
        px = float(e.position[0])
        py = float(e.position[1])
        vx = float(e.velocity[0])
        vy = float(e.velocity[1])
        if px < r:
            e.position[0] = r
            e.velocity[0] = abs(vx) * bounce
        elif px > w - r:
            e.position[0] = w - r
            e.velocity[0] = -abs(vx) * bounce
        if py < r:
            e.position[1] = r
            e.velocity[1] = abs(vy) * bounce
        elif py > h - r:
            e.position[1] = h - r
            e.velocity[1] = -abs(vy) * bounce


def resolve_pvaec_contacts(
    entities: Sequence[Any],
    *,
    width: float,
    height: float,
    config: SrPhysics2DConfig,
) -> None:
    dynamics = [e for e in entities if is_pvaec_dynamic_body(e)]
    if not dynamics:
        return

    pairs = build_pvaec_contact_pairs(
        entities,
        broadphase=getattr(config, "pvaec_broadphase", "spatial_hash"),
        contact_iterations=max(1, int(config.contact_iterations)),
    )

    iters = max(1, int(config.contact_iterations))
    for _ in range(iters):
        for a, b in pairs:
            _resolve_pair(a, b, config)

    clamp_pvaec_bodies(dynamics, width, height, bounce=config.boundary_bounce)
