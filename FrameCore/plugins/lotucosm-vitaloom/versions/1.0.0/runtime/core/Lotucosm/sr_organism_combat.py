# -*- coding: utf-8 -*-
"""SR 生物互攻近战：扇形判定（泛化自 sr_game_combat）。"""
from __future__ import annotations

import math
from typing import Any, Mapping, Optional


def _peer_pos_radius(peer: Any) -> tuple[float, float, float]:
    pos = getattr(peer, "position", (0.0, 0.0))
    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
        px, py = float(pos[0]), float(pos[1])
    else:
        px, py = 0.0, 0.0
    er = float(getattr(peer, "radius", 16.0))
    return px, py, er


def organism_in_melee_arc(
    px: float,
    py: float,
    angle: float,
    reach: float,
    arc_half: float,
    tx: float,
    ty: float,
    target_radius: float,
) -> bool:
    dx = tx - px
    dy = ty - py
    dist = math.hypot(dx, dy)
    if dist > reach + target_radius:
        return False
    a = math.atan2(dy, dx)
    diff = a - angle
    while diff > math.pi:
        diff -= math.pi * 2.0
    while diff < -math.pi:
        diff += math.pi * 2.0
    return abs(diff) <= arc_half


def attack_angle_from_entity(ent: Any, peers: tuple, *, fallback_peer: Any = None) -> float:
    vel = getattr(ent, "velocity", None)
    if isinstance(vel, (list, tuple)) and len(vel) >= 2:
        vx, vy = float(vel[0]), float(vel[1])
        if math.hypot(vx, vy) > 2.0:
            return math.atan2(vy, vx)
    if fallback_peer is not None:
        px, py = float(ent.position[0]), float(ent.position[1])
        tx, ty, _ = _peer_pos_radius(fallback_peer)
        return math.atan2(ty - py, tx - px)
    best_ang = 0.0
    best_gap = 1e18
    px, py = float(ent.position[0]), float(ent.position[1])
    my_id = str(getattr(ent, "id", ""))
    for p in peers:
        if str(getattr(p, "id", "")) == my_id:
            continue
        if str(getattr(p, "entity_type", "")) != "organism":
            continue
        gap = float(getattr(p, "surface_gap", 1e9))
        if gap < best_gap:
            best_gap = gap
            tx, ty, _ = _peer_pos_radius(p)
            best_ang = math.atan2(ty - py, tx - px)
    return best_ang


def pick_organism_melee_target(
    attacker: Any,
    peers: tuple,
    *,
    reach: float,
    arc_half: float,
    exclude_ids: frozenset[str] | None = None,
) -> Optional[Any]:
    """选取最近且在扇形内的敌对 organism peer。"""
    exclude = exclude_ids or frozenset()
    my_id = str(getattr(attacker, "id", ""))
    px, py = float(attacker.position[0]), float(attacker.position[1])
    ar = float(getattr(attacker, "radius", 18.0))
    angle = attack_angle_from_entity(attacker, peers)
    best = None
    best_gap = 1e18
    for p in peers:
        pid = str(getattr(p, "id", ""))
        if pid == my_id or pid in exclude:
            continue
        if str(getattr(p, "entity_type", "")) != "organism":
            continue
        tx, ty, tr = _peer_pos_radius(p)
        if not organism_in_melee_arc(px, py, angle, reach, arc_half, tx, ty, tr):
            continue
        gap = float(getattr(p, "surface_gap", math.hypot(tx - px, ty - py) - ar - tr))
        if gap < best_gap:
            best_gap = gap
            best = p
    return best


def hub_id_for_entity(entity_id: str, membrane_attach: Mapping[str, tuple[str, float, float]]) -> str:
    """膜组件 → 所属 hub；organism 自身返回 id。"""
    if entity_id in membrane_attach:
        return str(membrane_attach[entity_id][0])
    return entity_id
