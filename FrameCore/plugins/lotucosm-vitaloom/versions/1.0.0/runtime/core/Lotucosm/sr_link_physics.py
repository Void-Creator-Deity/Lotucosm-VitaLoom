# -*- coding: utf-8
"""SR 连接物理：硬连接（骨架）· 软连接（仅信号/可选弹簧）· 独立扩散。

设计参考（粗粒化细胞模型常见做法）::
    - 硬连接 ≈ 刚性骨架 / 膜锚定（organism↔膜蛋白），位置随 hub 刚体同步
    - 软连接 ≈  viscoelastic spring（Kelvin-Voigt 风格）或 **纯信号边**（不传力）
    - 独立节点 ≈ 无拓扑边，靠场梯度扩散（sensor 脚本 nutrient_grad）

.pond 连接字段::
    link_kind: hard | soft | independent
    channel / weight: 软连接上的信号（chemo 等）
    stiffness / damping / rest_length: 软弹簧（可选；soft+organism↔膜蛋白 默认开启）
    transmission: wired | diffusion | none  （independent 时用 diffusion）
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


DEFAULT_SOFT_STIFFNESS = 85.0
DEFAULT_SOFT_DAMPING = 11.0


@dataclass
class SrSpringLink:
    start_id: str
    end_id: str
    rest_length: float
    stiffness: float
    damping: float


def _types(id_to_type: Mapping[str, str], a: str, b: str) -> tuple[str, str]:
    return id_to_type.get(a, ""), id_to_type.get(b, "")


def infer_link_kind(edge: dict[str, Any], id_to_type: Mapping[str, str]) -> str:
    raw = str(edge.get("link_kind", edge.get("coupling", "")) or "").strip().lower()
    if raw in ("hard", "rigid", "skeleton", "mechanical"):
        return "hard"
    if raw in ("soft", "signal", "flex"):
        return "soft"
    if raw in ("independent", "none", "free", "diffusion"):
        return "independent"
    ta, tb = _types(id_to_type, edge["start"], edge["end"])
    pair = {ta, tb}
    if "organism" in pair and pair & {"sensor", "actuator", "central_brain"}:
        return "hard"
    if pair <= {"sensor", "actuator"} or pair <= {"sensor", "central_brain"}:
        return "soft"
    return "hard"


def enrich_parsed_edges(
    edges: Iterable[dict[str, Any]],
    id_to_type: Mapping[str, str],
) -> list[dict[str, Any]]:
    """为每条边补全 link_kind / stiffness / damping / transmission。"""
    out: list[dict[str, Any]] = []
    for edge in edges or []:
        if not isinstance(edge, dict):
            continue
        row = dict(edge)
        row["link_kind"] = infer_link_kind(row, id_to_type)
        if row["link_kind"] == "independent":
            row.setdefault("transmission", "diffusion")
        else:
            row.setdefault("transmission", "wired")
        try:
            row["stiffness"] = float(row.get("stiffness", DEFAULT_SOFT_STIFFNESS))
        except (TypeError, ValueError):
            row["stiffness"] = DEFAULT_SOFT_STIFFNESS
        try:
            row["damping"] = float(row.get("damping", DEFAULT_SOFT_DAMPING))
        except (TypeError, ValueError):
            row["damping"] = DEFAULT_SOFT_DAMPING
        out.append(row)
    return out


def _is_signal_pair(ta: str, tb: str) -> bool:
    return (ta == "sensor" and tb == "actuator") or (tb == "sensor" and ta == "actuator")


def partition_link_edges(
    edges: Iterable[dict[str, Any]],
    id_to_type: Mapping[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """拆成：硬骨架边、软信号边、可弹簧化的软机械边。"""
    hard: list[dict[str, Any]] = []
    soft_signal: list[dict[str, Any]] = []
    soft_mechanical: list[dict[str, Any]] = []
    for row in enrich_parsed_edges(edges, id_to_type):
        kind = row["link_kind"]
        ta, tb = _types(id_to_type, row["start"], row["end"])
        if kind == "independent":
            continue
        if kind == "hard":
            hard.append(row)
            continue
        # soft
        if _is_signal_pair(ta, tb):
            soft_signal.append(row)
        pair = {ta, tb}
        if "organism" in pair and pair & {"sensor", "actuator"}:
            if row.get("mechanical", True) is not False:
                soft_mechanical.append(row)
    return hard, soft_signal, soft_mechanical


def build_spring_links(
    entities: list[Any],
    soft_mechanical_edges: Iterable[dict[str, Any]],
) -> list[SrSpringLink]:
    """从 soft+organism↔膜蛋白 边建立弹簧（rest_length 默认初始距离）。"""
    id_to_ent = {str(getattr(e, "id", "")): e for e in entities}
    springs: list[SrSpringLink] = []
    for edge in soft_mechanical_edges or []:
        a, b = str(edge["start"]), str(edge["end"])
        ea, eb = id_to_ent.get(a), id_to_ent.get(b)
        if ea is None or eb is None:
            continue
        dx = float(eb.position[0]) - float(ea.position[0])
        dy = float(eb.position[1]) - float(ea.position[1])
        rest = edge.get("rest_length")
        try:
            rest_f = float(rest) if rest is not None else math.hypot(dx, dy)
        except (TypeError, ValueError):
            rest_f = math.hypot(dx, dy)
        rest_f = max(4.0, rest_f)
        springs.append(
            SrSpringLink(
                start_id=a,
                end_id=b,
                rest_length=rest_f,
                stiffness=float(edge.get("stiffness", DEFAULT_SOFT_STIFFNESS)),
                damping=float(edge.get("damping", DEFAULT_SOFT_DAMPING)),
            )
        )
    return springs


def step_spring_network(
    entities: list[Any],
    springs: Iterable[SrSpringLink],
    dt: float,
) -> None:
    """Kelvin-Voigt 风格弹簧步进：软连接端点可相对运动（硬连接端不在此表）。"""
    if dt <= 0.0:
        return
    id_to_ent = {str(getattr(e, "id", "")): e for e in entities}
    accum: dict[str, list[float]] = {}

    def add_force(eid: str, fx: float, fy: float) -> None:
        if eid not in accum:
            accum[eid] = [0.0, 0.0]
        accum[eid][0] += fx
        accum[eid][1] += fy

    for sp in springs or []:
        ea = id_to_ent.get(sp.start_id)
        eb = id_to_ent.get(sp.end_id)
        if ea is None or eb is None:
            continue
        if getattr(ea, "pinned", False) and getattr(eb, "pinned", False):
            continue
        ax, ay = float(ea.position[0]), float(ea.position[1])
        bx, by = float(eb.position[0]), float(eb.position[1])
        dx, dy = bx - ax, by - ay
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            continue
        nx, ny = dx / dist, dy / dist
        stretch = dist - sp.rest_length
        avx, avy = float(ea.velocity[0]), float(ea.velocity[1])
        bvx, bvy = float(eb.velocity[0]), float(eb.velocity[1])
        rel_v = (bvx - avx) * nx + (bvy - avy) * ny
        force = sp.stiffness * stretch + sp.damping * rel_v
        fx, fy = force * nx, force * ny
        ma = max(0.5, float(getattr(ea, "radius", 12.0)))
        mb = max(0.5, float(getattr(eb, "radius", 12.0)))
        if not getattr(ea, "pinned", False) and not getattr(ea, "membrane_locked", False):
            add_force(sp.start_id, fx / ma, fy / ma)
        if not getattr(eb, "pinned", False) and not getattr(eb, "membrane_locked", False):
            add_force(sp.end_id, -fx / mb, -fy / mb)

    for eid, (fx, fy) in accum.items():
        ent = id_to_ent.get(eid)
        if ent is None:
            continue
        ent.velocity[0] = float(ent.velocity[0]) + fx * dt
        ent.velocity[1] = float(ent.velocity[1]) + fy * dt


def merge_signal_edge_lists(*lists: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lst in lists:
        for edge in lst or []:
            if isinstance(edge, dict):
                out.append(dict(edge))
    return out
