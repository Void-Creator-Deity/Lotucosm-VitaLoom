# -*- coding: utf-8 -*-
"""SR 场景游戏化渲染：深空背景、整细胞质膜/细胞器、胞内信号与图例。

生物学映射（与 PVAEC 拓扑一致）::
    organism     → 细胞核 / 控制中心（演化中枢脚本宿主）
    sensor       → 跨膜化学受体（膜蛋白，胞外球头）
    actuator     → 纤毛效应器（膜上鞭毛束）
    signal_edges → 胞内趋化传导弧（第二信使流动粒子）
    structural   → 拓扑附着，不再画线框

供 GameViewport.paintEvent 调用；整细胞绘制读取 energy / emission / sr_channel_out 等当帧状态。
环境变量 ``VITALOOM_SR_GPU=1`` 可切换 OpenGL 画布（Qt GPU 合成，后续可接 shader）。
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from core.VitaLoom.viewports.sr_render_perf import SrBackgroundCache, sr_render_quality
from core.VitaLoom.viewports.sr_visual_state import (
    SrCellVisualState,
    SrEntityVisualState,
    extract_cell_visual_state,
    extract_entity_visual_state,
)


def _hash_phase(seed: str) -> float:
    return (hash(seed) % 997) / 997.0 * math.tau


def _clamp_alpha(value: float) -> int:
    return max(0, min(255, int(value)))


def _entity_maps(entities: list[Any]) -> tuple[dict[str, Any], dict[str, str]]:
    id_to_ent = {str(getattr(e, "id", "")): e for e in entities}
    id_to_type = {eid: str(getattr(ent, "entity_type", "")) for eid, ent in id_to_ent.items()}
    return id_to_ent, id_to_type


def _is_membrane_topology_edge(ta: str, tb: str) -> bool:
    """organism↔sensor/actuator 与 sensor↔actuator 为拓扑边，不画成线框。"""
    pair = {ta, tb}
    if pair <= {"sensor", "actuator"}:
        return True
    if "organism" in pair and pair & {"sensor", "actuator", "central_brain"}:
        return True
    return False


def _build_cell_groups(
    entities: list[Any],
    structural_edges: Iterable[tuple[str, str]],
) -> list[tuple[str, set[str]]]:
    """按 organism hub 聚合膜上组件，用于整细胞绘制。"""
    id_to_ent, id_to_type = _entity_maps(entities)
    hub_children: dict[str, set[str]] = {}
    for a, b in structural_edges or []:
        ta, tb = id_to_type.get(a, ""), id_to_type.get(b, "")
        if ta == "organism" and tb in ("sensor", "actuator", "central_brain"):
            hub_children.setdefault(a, set()).add(b)
        elif tb == "organism" and ta in ("sensor", "actuator", "central_brain"):
            hub_children.setdefault(b, set()).add(a)
    groups: list[tuple[str, set[str]]] = []
    seen_hubs: set[str] = set()
    for hub_id, child_ids in sorted(hub_children.items()):
        if hub_id not in id_to_ent:
            continue
        groups.append((hub_id, {hub_id} | child_ids))
        seen_hubs.add(hub_id)
    for eid, ent in id_to_ent.items():
        if id_to_type.get(eid) == "organism" and eid not in seen_hubs:
            groups.append((eid, {eid}))
    return groups


def _beauty_pulse(membrane_phase: float, scene_time: float, seed: str, vitality: float) -> float:
    """观感脉动：代谢相位 + 轻量 scene_time（幅度随 vitality）。"""
    ph = _hash_phase(seed)
    return 0.84 + 0.16 * math.sin(membrane_phase + scene_time * (1.6 + vitality * 0.8) + ph)


def _organic_membrane_path(
    cx: float,
    cy: float,
    anchors: list[tuple[float, float, float]],
    *,
    segments: int = 44,
    margin: float = 18.0,
    membrane_phase: float = 0.0,
    scene_time: float = 0.0,
    vitality: float = 0.5,
    energy: float = 0.5,
    stress: float = 0.0,
    seed: str = "cell",
    wobble_scale_mul: float = 1.0,
    flow_offsets: Optional[list[float]] = None,
) -> QPainterPath:
    """质膜：锚点包络 + 内外流体压差形变（flow_offsets）；无流场时保留轻量代谢律动。"""
    phase_seed = _hash_phase(seed)
    rhythm = membrane_phase + scene_time * (0.55 + 0.45 * vitality)
    n = max(16, segments)
    use_flow = isinstance(flow_offsets, list) and len(flow_offsets) >= n
    wobble_scale = (
        (2.5 + 5.5 * vitality * (0.4 + 0.6 * energy))
        * max(0.35, 1.0 - stress * 0.5)
        * max(0.15, float(wobble_scale_mul))
        * (0.22 if use_flow else 1.0)
    )
    pts: list[tuple[float, float]] = []
    for i in range(n):
        ang = (i / n) * math.tau
        r = 26.0
        for ax, ay, ar in anchors:
            dist = math.hypot(ax - cx, ay - cy)
            a_anchor = math.atan2(ay - cy, ax - cx)
            da = ang - a_anchor
            while da > math.pi:
                da -= math.tau
            while da < -math.pi:
                da += math.tau
            bump = math.exp(-(da * da) / 0.52) * (ar + margin)
            r = max(r, dist + ar * 0.58 + bump)
        if use_flow:
            r += float(flow_offsets[i])
        else:
            wobble = wobble_scale * math.sin(ang * 3.0 + rhythm + phase_seed)
            wobble += wobble_scale * 0.5 * math.sin(ang * 5.0 - rhythm * 1.35 + phase_seed * 0.65)
            r += wobble
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))

    path = QPainterPath()
    path.moveTo(pts[0][0], pts[0][1])
    for i in range(1, n):
        mx = (pts[i - 1][0] + pts[i][0]) * 0.5
        my = (pts[i - 1][1] + pts[i][1]) * 0.5
        path.quadTo(pts[i - 1][0], pts[i - 1][1], mx, my)
    path.closeSubpath()
    return path


def _dir_or_normal(
    dx: float,
    dy: float,
    cx: float,
    cy: float,
    px: float,
    py: float,
) -> tuple[float, float]:
    d = math.hypot(dx, dy)
    if d > 0.05:
        return dx / d, dy / d
    return _membrane_outward_normal(cx, cy, px, py)


def _membrane_outward_normal(cx: float, cy: float, px: float, py: float) -> tuple[float, float]:
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def _paint_cell_outer_glow(
    painter: QPainter,
    path: QPainterPath,
    cx: float,
    cy: float,
    *,
    vitality: float,
    pulse: float,
) -> None:
    """整细胞外晕（恢复早期发光观感）。"""
    rect = path.boundingRect()
    r = max(rect.width(), rect.height()) * 0.55
    grad = QRadialGradient(cx, cy, r)
    grad.setColorAt(0.0, QColor(100, 180, 240, _clamp_alpha(38 * pulse * vitality)))
    grad.setColorAt(0.55, QColor(60, 130, 210, _clamp_alpha(22 * pulse * vitality)))
    grad.setColorAt(1.0, QColor(20, 50, 100, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(grad))
    painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))


def _paint_cytoplasm(
    painter: QPainter,
    path: QPainterPath,
    cx: float,
    cy: float,
    *,
    energy: float = 0.5,
    stress: float = 0.0,
    pulse: float = 1.0,
    vitality: float = 0.5,
) -> None:
    bright = max(0.35, min(1.0, 0.42 + 0.58 * energy - 0.22 * stress)) * pulse
    grad = QRadialGradient(cx, cy, 130.0)
    grad.setColorAt(0.0, QColor(90, 160, 210, _clamp_alpha(115 * bright)))
    grad.setColorAt(0.42, QColor(55, 115, 175, _clamp_alpha(88 * bright)))
    grad.setColorAt(0.78, QColor(35, 80, 140, _clamp_alpha(52 * bright * vitality)))
    grad.setColorAt(1.0, QColor(18, 45, 85, _clamp_alpha(28 * bright)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(grad))
    painter.drawPath(path)


def _paint_extracellular_flow_particles(
    painter: QPainter,
    hub: Any,
    cx: float,
    cy: float,
    membrane_path: QPainterPath,
    *,
    fluid_strength: float,
    scene_time: float,
) -> None:
    """胞外水流粒子：沿营养/场域梯度漂移（缓存于 hub._sr_fluid_exo_particles）。"""
    raw = getattr(hub, "_sr_fluid_exo_particles", None)
    if not isinstance(raw, list) or not raw:
        return
    rect = membrane_path.boundingRect()
    r = max(rect.width(), rect.height()) * 0.52
    strength = max(0.0, min(1.0, fluid_strength))
    if strength < 0.03:
        return
    for p in raw:
        ang = float(p[2]) * math.tau + scene_time * 0.4
        px = cx + math.cos(ang) * (r * 1.05)
        py = cy + math.sin(ang) * (r * 1.05)
        drift = 3.0 + strength * 5.0
        px += float(p[0]) * drift
        py += float(p[1]) * drift
        alpha = _clamp_alpha(55 + 120 * strength)
        dot_r = 2 + int(strength * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(100, 190, 255, alpha)))
        painter.drawEllipse(int(px - dot_r), int(py - dot_r), dot_r * 2, dot_r * 2)


def _paint_intracellular_flow_particles(
    painter: QPainter,
    hub: Any,
    cx: float,
    cy: float,
    membrane_path: QPainterPath,
    *,
    energy: float,
    signal_flow: float,
    endo_vx: float,
    endo_vy: float,
) -> None:
    """胞内能量水流：核区向执行器汇聚的微粒。"""
    raw = getattr(hub, "_sr_fluid_endo_particles", None)
    if not isinstance(raw, list) or not raw:
        return
    flow = max(0.0, min(1.0, 0.35 * energy + 0.65 * signal_flow))
    if flow < 0.04:
        return
    rect = membrane_path.boundingRect()
    inner_r = min(rect.width(), rect.height()) * 0.22
    painter.setClipPath(membrane_path)
    for p in raw:
        t = float(p[2])
        px = cx + (float(p[0]) - 0.5) * inner_r * 2.2 * (1.0 - t * 0.35)
        py = cy + (float(p[1]) - 0.5) * inner_r * 2.2 * (1.0 - t * 0.35)
        px += endo_vx * 0.08 * t
        py += endo_vy * 0.08 * t
        alpha = _clamp_alpha(40 + 150 * flow * (1.0 - abs(t - 0.5)))
        dot_r = 2 + int(flow * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(140, 255, 200, alpha)))
        painter.drawEllipse(int(px - dot_r), int(py - dot_r), dot_r * 2, dot_r * 2)
    painter.setClipping(False)


def _paint_transmembrane_exchange(
    painter: QPainter,
    cx: float,
    cy: float,
    exchange_sites: Iterable[Any],
    *,
    scene_time: float,
) -> None:
    """跨膜交换：受体入流（绿）· 纤毛出流（橙）。"""
    for site in exchange_sites:
        sx = float(getattr(site, "x", 0.0))
        sy = float(getattr(site, "y", 0.0))
        strength = max(0.0, min(1.0, float(getattr(site, "strength", 0.0))))
        if strength < 0.06:
            continue
        direction = str(getattr(site, "direction", "in"))
        nx, ny = _membrane_outward_normal(cx, cy, sx, sy)
        pulse = 0.65 + 0.35 * math.sin(scene_time * 3.2 + sx * 0.02)
        span = 8.0 + strength * 14.0
        if direction == "in":
            hx, hy = sx + nx * span * pulse, sy + ny * span * pulse
            col = QColor(120, 255, 180, _clamp_alpha(90 + 100 * strength))
        else:
            hx, hy = sx + nx * span * pulse, sy + ny * span * pulse
            col = QColor(255, 180, 90, _clamp_alpha(80 + 110 * strength))
        path = QPainterPath()
        path.moveTo(sx, sy)
        path.lineTo(hx, hy)
        painter.setPen(QPen(col, 1.5 + strength, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(col))
        painter.drawEllipse(int(hx - 2), int(hy - 2), 4, 4)


def _paint_nucleus(
    painter: QPainter,
    hub: Any,
    *,
    cell: SrCellVisualState,
    pulse: float = 1.0,
    scene_time: float = 0.0,
) -> None:
    r = max(11.0, float(getattr(hub, "radius", 22.0)) * (0.84 + 0.14 * cell.energy))
    nx, ny = float(hub.position[0]), float(hub.position[1])
    glow = max(0.4, min(1.0, 0.5 * cell.energy + 0.5 * cell.arousal - 0.15 * cell.stress)) * pulse
    _draw_glow_disc(
        painter,
        nx,
        ny,
        r * 1.15,
        QColor(180, 230, 255, _clamp_alpha(200 * glow)),
        QColor(80, 160, 230, _clamp_alpha(90 * glow)),
        QColor(200, 240, 255, _clamp_alpha(180 * glow)),
    )
    nu_grad = QRadialGradient(nx, ny, r * 1.05)
    nu_grad.setColorAt(0.0, QColor(235, 248, 255, _clamp_alpha(245 * glow)))
    nu_grad.setColorAt(0.55, QColor(140, 200, 250, _clamp_alpha(195 * glow)))
    nu_grad.setColorAt(1.0, QColor(70, 130, 210, _clamp_alpha(70 * glow)))
    painter.setPen(QPen(QColor(190, 235, 255, _clamp_alpha(220 * glow)), 2))
    painter.setBrush(QBrush(nu_grad))
    painter.drawEllipse(int(nx - r), int(ny - r), int(r * 2), int(r * 2))
    nucleolus_r = r * (0.24 + 0.12 * cell.arousal)
    ph = _hash_phase(str(getattr(hub, "id", "hub")))
    drift = r * (0.08 + 0.1 * cell.arousal)
    nlx = nx + math.cos(cell.membrane_phase * 0.7 + scene_time * 0.45 + ph) * drift
    nly = ny + math.sin(cell.membrane_phase * 0.6 + scene_time * 0.38 + ph) * drift
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 150, 210, _clamp_alpha(220 * (0.55 + 0.45 * cell.arousal)))))
    painter.drawEllipse(int(nlx - nucleolus_r), int(nly - nucleolus_r), int(nucleolus_r * 2), int(nucleolus_r * 2))


def _paint_transmembrane_receptor(
    painter: QPainter,
    sensor: Any,
    cx: float,
    cy: float,
    *,
    est: SrEntityVisualState,
    membrane_phase: float = 0.0,
    scene_time: float = 0.0,
    pulse: float = 1.0,
) -> None:
    sx, sy = float(sensor.position[0]), float(sensor.position[1])
    nx, ny = _dir_or_normal(est.chemo_dir_x, est.chemo_dir_y, cx, cy, sx, sy)
    sr = max(5.0, float(getattr(sensor, "radius", 10.0)))
    chemo = max(0.0, min(1.0, est.chemo_out))
    if chemo < 0.05:
        nx, ny = _membrane_outward_normal(cx, cy, sx, sy)
    brightness = (0.45 + 0.55 * chemo) * pulse
    stem_out = sr * (0.48 + 0.3 * chemo)
    head_x = sx + nx * stem_out
    head_y = sy + ny * stem_out
    tail_x = sx - nx * sr * 0.38
    tail_y = sy - ny * sr * 0.38
    painter.setPen(QPen(QColor(120, 240, 180, _clamp_alpha(210 * brightness)), 2))
    painter.drawLine(int(sx), int(sy), int(head_x), int(head_y))
    painter.drawLine(int(sx), int(sy), int(tail_x), int(tail_y))
    head_r = sr * (0.38 + 0.18 * chemo)
    _draw_glow_disc(
        painter,
        head_x,
        head_y,
        head_r * 1.35 * pulse,
        QColor(170, 255, 210, _clamp_alpha(230 * brightness)),
        QColor(70, 200, 130, _clamp_alpha(100 * brightness)),
        QColor(210, 255, 230, _clamp_alpha(200 * brightness)),
    )
    head_grad = QRadialGradient(head_x, head_y, head_r)
    head_grad.setColorAt(0.0, QColor(210, 255, 225, _clamp_alpha(250 * brightness)))
    head_grad.setColorAt(1.0, QColor(80, 200, 140, _clamp_alpha(90 * brightness)))
    painter.setPen(QPen(QColor(220, 255, 235, _clamp_alpha(190 * brightness)), 1))
    painter.setBrush(QBrush(head_grad))
    painter.drawEllipse(int(head_x - head_r), int(head_y - head_r), int(head_r * 2), int(head_r * 2))


def _paint_cilia_effector(
    painter: QPainter,
    actuator: Any,
    cx: float,
    cy: float,
    *,
    est: SrEntityVisualState,
    cilia_count: int = 5,
    membrane_phase: float = 0.0,
    scene_time: float = 0.0,
    pulse: float = 1.0,
) -> None:
    ax, ay = float(actuator.position[0]), float(actuator.position[1])
    nx, ny = _dir_or_normal(est.chemo_dir_x, est.chemo_dir_y, cx, cy, ax, ay)
    ar = max(5.0, float(getattr(actuator, "radius", 10.0)))
    drive = max(0.35, min(1.0, 0.45 * est.chemo_in + 0.4 * est.thrust + 0.25))
    base_ang = math.atan2(ny, nx)
    count = max(3, cilia_count)
    phase = membrane_phase + scene_time * (2.5 + drive * 3.0)
    for i in range(count):
        spread = (i - (count - 1) * 0.5) * 0.2
        wave = math.sin(phase + i * 0.95) * (0.14 + 0.16 * drive)
        ang = base_ang + spread + wave
        len_c = ar * (1.35 + 0.55 * drive + 0.15 * math.sin(phase * 1.2 + i))
        ex = ax + math.cos(ang) * len_c
        ey = ay + math.sin(ang) * len_c
        ctrl_x = ax + math.cos(ang) * len_c * 0.48 + math.sin(ang) * 5
        ctrl_y = ay + math.sin(ang) * len_c * 0.48 - math.cos(ang) * 5
        path = QPainterPath()
        path.moveTo(ax, ay)
        path.quadTo(ctrl_x, ctrl_y, ex, ey)
        alpha = _clamp_alpha((140 + 90 * drive) * pulse)
        painter.setPen(QPen(QColor(255, 200, 110, alpha), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        tip_r = 2 + int(drive * 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 230, 150, alpha)))
        painter.drawEllipse(int(ex - tip_r), int(ey - tip_r), tip_r * 2, tip_r * 2)
    base_r = ar * (0.34 + 0.16 * drive)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 175, 85, _clamp_alpha(200 * pulse))))
    painter.drawEllipse(int(ax - base_r), int(ay - base_r), int(base_r * 2), int(base_r * 2))


def _paint_intracellular_signal_path(
    painter: QPainter,
    sx: float,
    sy: float,
    ax: float,
    ay: float,
    nx: float,
    ny: float,
    weight: float,
    *,
    chemo_flow: float = 0.0,
    signal_phase: float = 0.0,
    dots_max: int = 4,
    scene_time: float = 0.0,
    pulse: float = 1.0,
) -> None:
    flow = max(0.0, min(1.0, chemo_flow * max(0.3, weight)))
    if flow < 0.02:
        return
    flicker = 0.72 + 0.28 * math.sin(signal_phase * 3.0 + scene_time * 2.2 + weight)
    alpha = _clamp_alpha((55 + weight * 40 + 110 * flow) * pulse * flicker)
    cx = (sx + ax) * 0.5 * 0.35 + nx * 0.65
    cy = (sy + ay) * 0.5 * 0.35 + ny * 0.65
    path = QPainterPath()
    path.moveTo(sx, sy)
    path.quadTo(cx, cy, ax, ay)
    glow_pen = QPen(QColor(40, 200, 140, _clamp_alpha(alpha * 0.45)), max(3, int(2 + flow * 3)))
    painter.setPen(glow_pen)
    painter.drawPath(path)
    painter.setPen(
        QPen(QColor(120, 255, 190, alpha), 1.5 + 2.0 * flow, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    painter.drawPath(path)
    dot_count = min(dots_max, max(2, 2 + int(flow * dots_max)))
    for k in range(dot_count):
        t = (signal_phase + k * (0.82 / max(1, dot_count))) % 1.0
        px = (1 - t) * (1 - t) * sx + 2 * (1 - t) * t * cx + t * t * ax
        py = (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * cy + t * t * ay
        dot_a = _clamp_alpha(230 * flow * pulse * (1.0 - abs(t - 0.5) * 0.85))
        dot_r = 2 + int(flow * 2.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(160, 255, 210, dot_a)))
        painter.drawEllipse(int(px - dot_r), int(py - dot_r), dot_r * 2, dot_r * 2)


def _paint_plasma_membrane_bilayer(
    painter: QPainter,
    path: QPainterPath,
    *,
    vitality: float = 0.5,
    lipid_dots: int = 0,
    membrane_phase: float = 0.0,
    scene_time: float = 0.0,
    stress: float = 0.0,
    pulse: float = 1.0,
) -> None:
    glow = max(0.35, min(1.0, vitality)) * pulse
    line_pulse = 1.0 + 0.18 * glow * math.sin(membrane_phase + scene_time * 1.3)
    outer_w = max(2.0, 3.5 * line_pulse * max(0.55, 1.0 - stress * 0.35))
    halo = QPen(QColor(100, 190, 255, _clamp_alpha(55 * glow)), outer_w + 5)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(halo)
    painter.drawPath(path)
    outer = QPen(QColor(170, 240, 255, _clamp_alpha(220 * glow)), outer_w)
    inner = QPen(QColor(100, 175, 235, _clamp_alpha(150 * glow)), max(1.0, outer_w * 0.55))
    painter.setPen(outer)
    painter.drawPath(path)
    painter.setPen(inner)
    painter.drawPath(path)
    if lipid_dots <= 0:
        return
    rect = path.boundingRect()
    mcx, mcy = rect.center().x(), rect.center().y()
    for i in range(lipid_dots):
        ang = i * (math.tau / lipid_dots) + membrane_phase * 0.2 + scene_time * 0.12
        r = max(rect.width(), rect.height()) * 0.48
        px = mcx + math.cos(ang) * r
        py = mcy + math.sin(ang) * r
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(215, 245, 255, _clamp_alpha(150 * glow))))
        painter.drawEllipse(int(px - 2), int(py - 2), 4, 4)


def paint_composite_cell(
    painter: QPainter,
    hub: Any,
    member_ids: set[str],
    id_to_ent: dict[str, Any],
    id_to_type: dict[str, str],
    signal_edges: Iterable[dict[str, Any]],
    all_entities: list[Any],
    *,
    quality=None,
    scene_time: float = 0.0,
    spring_links: Optional[Iterable[Any]] = None,
    emissions_prev: Optional[Mapping[str, float]] = None,
    niche_pressure: float = 0.0,
) -> None:
    """整细胞：当帧 PVAEC 数据 + 内外流体场驱动（位置/能量/chemo/积分相位）。"""
    q = quality or sr_render_quality()
    cell = extract_cell_visual_state(
        hub, member_ids, id_to_ent, id_to_type, signal_edges, all_entities
    )
    cx, cy = float(hub.position[0]), float(hub.position[1])
    seed = str(getattr(hub, "id", "cell"))
    pulse = _beauty_pulse(cell.membrane_phase, scene_time, seed, cell.vitality)

    fluid_state = None
    flow_offsets: Optional[list[float]] = None
    if emissions_prev is not None:
        from core.Lotucosm.sr_fluid_flow import build_cell_fluid_state

        fluid_state = build_cell_fluid_state(
            hub,
            member_ids,
            id_to_ent,
            id_to_type,
            cell_energy=cell.energy,
            cell_signal_flow=cell.signal_flow,
            cell_speed=cell.speed,
            cell_stress=cell.stress,
            vel_x=cell.vel_x,
            vel_y=cell.vel_y,
            membrane_phase=cell.membrane_phase,
            by_entity=cell.by_entity,
            entities=all_entities,
            emissions_prev=emissions_prev,
            niche_pressure=niche_pressure,
            segments=q.membrane_segments,
        )
        flow_offsets = fluid_state.membrane_offsets
    else:
        cached = getattr(hub, "_sr_fluid_state", None)
        if cached is not None:
            fluid_state = cached
            flow_offsets = getattr(cached, "membrane_offsets", None)

    anchors: list[tuple[float, float, float]] = []
    sensors: list[Any] = []
    actuators: list[Any] = []
    for mid in member_ids:
        ent = id_to_ent.get(mid)
        if ent is None:
            continue
        et = id_to_type.get(mid, "")
        px, py = float(ent.position[0]), float(ent.position[1])
        pr = float(getattr(ent, "radius", 12.0))
        anchors.append((px, py, pr))
        if et == "sensor":
            sensors.append(ent)
        elif et == "actuator":
            actuators.append(ent)

    spring_members = False
    for sp in spring_links or []:
        sid = str(getattr(sp, "start_id", ""))
        eid = str(getattr(sp, "end_id", ""))
        if sid in member_ids or eid in member_ids:
            spring_members = True
            break

    membrane = _organic_membrane_path(
        cx,
        cy,
        anchors,
        segments=q.membrane_segments,
        membrane_phase=cell.membrane_phase,
        scene_time=scene_time,
        vitality=cell.vitality,
        energy=cell.energy,
        stress=cell.stress,
        seed=seed,
        wobble_scale_mul=0.38 if spring_members else 1.0,
        flow_offsets=flow_offsets,
    )
    _paint_cell_outer_glow(painter, membrane, cx, cy, vitality=cell.vitality, pulse=pulse)
    _paint_cytoplasm(
        painter,
        membrane,
        cx,
        cy,
        energy=cell.energy,
        stress=cell.stress,
        pulse=pulse,
        vitality=cell.vitality,
    )
    if fluid_state is not None:
        _paint_intracellular_flow_particles(
            painter,
            hub,
            cx,
            cy,
            membrane,
            energy=cell.energy,
            signal_flow=cell.signal_flow,
            endo_vx=fluid_state.endo_vx,
            endo_vy=fluid_state.endo_vy,
        )

    for edge in signal_edges or []:
        if str(edge.get("channel", "chemo")) != "chemo":
            continue
        sid, aid = str(edge.get("start", "")), str(edge.get("end", ""))
        if sid not in member_ids or aid not in member_ids:
            continue
        se = id_to_ent.get(sid)
        ae = id_to_ent.get(aid)
        if se is None or ae is None:
            continue
        try:
            ew = float(edge.get("weight", 1.0))
        except (TypeError, ValueError):
            ew = 1.0
        sensor_st = cell.by_entity.get(sid, SrEntityVisualState())
        chemo_flow = max(sensor_st.chemo_out, cell.by_entity.get(aid, SrEntityVisualState()).chemo_in)
        _paint_intracellular_signal_path(
            painter,
            float(se.position[0]),
            float(se.position[1]),
            float(ae.position[0]),
            float(ae.position[1]),
            cx,
            cy,
            ew,
            chemo_flow=chemo_flow,
            signal_phase=cell.signal_phase,
            dots_max=q.signal_dots_max,
            scene_time=scene_time,
            pulse=pulse,
        )

    _paint_nucleus(painter, hub, cell=cell, pulse=pulse, scene_time=scene_time)
    _paint_plasma_membrane_bilayer(
        painter,
        membrane,
        vitality=cell.vitality,
        lipid_dots=q.lipid_dots,
        membrane_phase=cell.membrane_phase,
        scene_time=scene_time,
        stress=cell.stress,
        pulse=pulse,
    )
    if fluid_state is not None:
        exo_mag = math.hypot(fluid_state.exo_vx, fluid_state.exo_vy)
        _paint_extracellular_flow_particles(
            painter,
            hub,
            cx,
            cy,
            membrane,
            fluid_strength=min(1.0, exo_mag / 80.0 + abs(fluid_state.pressure_delta) * 0.02),
            scene_time=scene_time,
        )
        _paint_transmembrane_exchange(
            painter,
            cx,
            cy,
            fluid_state.exchange_sites,
            scene_time=scene_time,
        )
    for sensor in sensors:
        sid = str(getattr(sensor, "id", ""))
        est = cell.by_entity.get(sid, extract_entity_visual_state(sensor))
        _paint_transmembrane_receptor(
            painter,
            sensor,
            cx,
            cy,
            est=est,
            membrane_phase=cell.membrane_phase,
            scene_time=scene_time,
            pulse=pulse,
        )
    for actuator in actuators:
        aid = str(getattr(actuator, "id", ""))
        est = cell.by_entity.get(aid, extract_entity_visual_state(actuator))
        _paint_cilia_effector(
            painter,
            actuator,
            cx,
            cy,
            est=est,
            cilia_count=q.cilia_count,
            membrane_phase=cell.membrane_phase,
            scene_time=scene_time,
            pulse=pulse,
        )


def paint_composite_cells(
    painter: QPainter,
    entities: list[Any],
    structural_edges: Iterable[tuple[str, str]],
    signal_edges: Iterable[dict[str, Any]],
    scene_time: float = 0.0,
    spring_links: Optional[Iterable[Any]] = None,
    *,
    emissions_prev: Optional[Mapping[str, float]] = None,
    niche_pressure: float = 0.0,
) -> set[str]:
    """绘制所有 hub 细胞；返回已纳入整细胞绘制的实体 id。"""
    id_to_ent, id_to_type = _entity_maps(entities)
    painted: set[str] = set()
    q = sr_render_quality()
    for hub_id, member_ids in _build_cell_groups(entities, structural_edges):
        hub = id_to_ent.get(hub_id)
        if hub is None:
            continue
        paint_composite_cell(
            painter,
            hub,
            member_ids,
            id_to_ent,
            id_to_type,
            signal_edges,
            entities,
            quality=q,
            scene_time=scene_time,
            spring_links=spring_links,
            emissions_prev=emissions_prev,
            niche_pressure=niche_pressure,
        )
        painted |= member_ids
    return painted

def paint_sr_background(painter: QPainter, width: int, height: int, scene_time: float = 0.0) -> None:
    """深空渐变 + 微粒网格 + 暗角。"""
    grad = QLinearGradient(0, 0, float(width), float(height))
    grad.setColorAt(0.0, QColor(8, 12, 22))
    grad.setColorAt(0.45, QColor(14, 20, 32))
    grad.setColorAt(1.0, QColor(6, 10, 18))
    painter.fillRect(0, 0, width, height, QBrush(grad))

    step = 48
    dot_pen = QPen(QColor(70, 110, 150, 22))
    painter.setPen(dot_pen)
    drift = (scene_time * 6.0) % step
    for gx in range(-step, width + step, step):
        for gy in range(-step, height + step, step):
            px = gx + drift * 0.35
            py = gy + drift * 0.2
            painter.drawPoint(int(px), int(py))

    vignette = QRadialGradient(width * 0.5, height * 0.5, max(width, height) * 0.72)
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.75, QColor(0, 0, 0, 0))
    vignette.setColorAt(1.0, QColor(0, 0, 0, 120))
    painter.fillRect(0, 0, width, height, QBrush(vignette))


def _paint_spring_curve(
    painter: QPainter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    scene_time: float,
    segments: int = 7,
) -> None:
    """软连接弹簧：沿直线锯齿/正弦形变。"""
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 6.0:
        return
    nx, ny = dx / dist, dy / dist
    px, py = -ny, nx
    amp = min(10.0, dist * 0.12)
    path = QPainterPath()
    path.moveTo(x1, y1)
    for i in range(1, segments):
        t = i / segments
        bx = x1 + dx * t
        by = y1 + dy * t
        sign = 1.0 if i % 2 else -1.0
        wob = sign * amp * math.sin(scene_time * 3.5 + t * math.pi * 2.0)
        path.lineTo(bx + px * wob, by + py * wob)
    path.lineTo(x2, y2)
    glow = QPen(QColor(120, 210, 180, 55), 3, Qt.PenStyle.SolidLine)
    painter.setPen(glow)
    painter.drawPath(path)
    core = QPen(QColor(170, 240, 210, 120), 1, Qt.PenStyle.SolidLine)
    painter.setPen(core)
    painter.drawPath(path)


def paint_sr_link_physics(
    painter: QPainter,
    connection_edges: Iterable[dict[str, Any]],
    spring_links: Iterable[Any],
    id_to_ent: dict[str, Any],
    id_to_type: dict[str, str],
    *,
    scene_time: float = 0.0,
    skip_entity_ids: Optional[set[str]] = None,
) -> None:
    """硬连接骨架辐条 + 软弹簧；整细胞内部边在 composite 之后叠加。"""
    skip = skip_entity_ids or set()

    for edge in connection_edges or []:
        if not isinstance(edge, dict):
            continue
        a = str(edge.get("start", ""))
        b = str(edge.get("end", ""))
        if not a or not b:
            continue
        if a in skip and b in skip:
            continue
        ea, eb = id_to_ent.get(a), id_to_ent.get(b)
        if ea is None or eb is None:
            continue
        ta, tb = id_to_type.get(a, ""), id_to_type.get(b, "")
        x1, y1 = float(ea.position[0]), float(ea.position[1])
        x2, y2 = float(eb.position[0]), float(eb.position[1])
        kind = str(edge.get("link_kind", "hard")).lower()
        if kind == "hard" and _is_membrane_topology_edge(ta, tb):
            bone = QPen(QColor(90, 150, 220, 90), 2, Qt.PenStyle.SolidLine)
            painter.setPen(bone)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    for sp in spring_links or []:
        a = str(getattr(sp, "start_id", ""))
        b = str(getattr(sp, "end_id", ""))
        if a in skip and b in skip:
            continue
        ea, eb = id_to_ent.get(a), id_to_ent.get(b)
        if ea is None or eb is None:
            continue
        _paint_spring_curve(
            painter,
            float(ea.position[0]),
            float(ea.position[1]),
            float(eb.position[0]),
            float(eb.position[1]),
            scene_time=scene_time,
        )


def paint_structural_edges(
    painter: QPainter,
    edges: Iterable[tuple[str, str]],
    id_to_pos: dict[str, Any],
    *,
    id_to_type: Optional[dict[str, str]] = None,
    skip_entity_ids: Optional[set[str]] = None,
) -> None:
    """仅绘制非膜拓扑边（如多细胞群落）；organism↔sensor/actuator 不画线框。"""
    skip_entity_ids = skip_entity_ids or set()
    for a, b in edges:
        if a in skip_entity_ids and b in skip_entity_ids:
            continue
        if id_to_type is not None:
            ta, tb = id_to_type.get(a, ""), id_to_type.get(b, "")
            if _is_membrane_topology_edge(ta, tb):
                continue
        pa = id_to_pos.get(a)
        pb = id_to_pos.get(b)
        if pa is None or pb is None:
            continue
        x1, y1, x2, y2 = int(pa[0]), int(pa[1]), int(pb[0]), int(pb[1])
        glow = QPen(QColor(90, 140, 210, 35), 3, Qt.PenStyle.SolidLine)
        painter.setPen(glow)
        painter.drawLine(x1, y1, x2, y2)
        core = QPen(QColor(140, 185, 240, 70), 1, Qt.PenStyle.DotLine)
        painter.setPen(core)
        painter.drawLine(x1, y1, x2, y2)


def paint_chemo_signal_edges(
    painter: QPainter,
    signal_edges: Iterable[dict[str, Any]],
    id_to_pos: dict[str, Any],
    scene_time: float,
    *,
    skip_entity_ids: Optional[set[str]] = None,
) -> None:
    """胞外/跨细胞趋化边；胞内 sensor→actuator 由 paint_composite_cell 绘制。"""
    skip_entity_ids = skip_entity_ids or set()
    for edge in signal_edges:
        if str(edge.get("channel", "chemo")) != "chemo":
            continue
        sid, aid = str(edge.get("start", "")), str(edge.get("end", ""))
        if sid in skip_entity_ids and aid in skip_entity_ids:
            continue
        pa = id_to_pos.get(str(edge.get("start", "")))
        pb = id_to_pos.get(str(edge.get("end", "")))
        if pa is None or pb is None:
            continue
        try:
            ew = float(edge.get("weight", 1.0))
        except (TypeError, ValueError):
            ew = 1.0
        pulse = 0.75 + 0.25 * math.sin(scene_time * 4.0 + ew)
        alpha = _clamp_alpha((60 + ew * 50) * pulse)
        x1, y1, x2, y2 = int(pa[0]), int(pa[1]), int(pb[0]), int(pb[1])
        glow_pen = QPen(QColor(40, 200, 140, _clamp_alpha(alpha * 0.45)), max(2, int(ew * 3)), Qt.PenStyle.SolidLine)
        painter.setPen(glow_pen)
        painter.drawLine(x1, y1, x2, y2)
        core_pen = QPen(QColor(120, 255, 190, alpha), max(1, min(3, int(ew * 1.5 + 0.5))))
        painter.setPen(core_pen)
        painter.drawLine(x1, y1, x2, y2)


def paint_well_affinity_lines(
    painter: QPainter,
    entities: list[Any],
) -> None:
    wells = [e for e in entities if str(getattr(e, "entity_type", "")) == "environment_well"]
    orgs = [e for e in entities if str(getattr(e, "entity_type", "")) == "organism"]
    if not wells or not orgs:
        return
    aff_pen = QPen(QColor(100, 170, 255, 70), 1, Qt.PenStyle.DotLine)
    painter.setPen(aff_pen)
    for wel in wells:
        wx, wy = float(wel.position[0]), float(wel.position[1])
        rw = float(getattr(wel, "radius", 24.0))
        nearest = None
        best_d = 1e18
        for org in orgs:
            ox, oy = float(org.position[0]), float(org.position[1])
            d = math.hypot(wx - ox, wy - oy)
            if d < best_d:
                best_d = d
                nearest = org
        if nearest is None:
            continue
        ro = float(getattr(nearest, "radius", 20.0))
        if best_d <= rw + ro + 220.0:
            painter.drawLine(
                int(wx),
                int(wy),
                int(float(nearest.position[0])),
                int(float(nearest.position[1])),
            )


def paint_membrane_hulls(
    painter: QPainter,
    entities: list[Any],
    structural_edges: Iterable[tuple[str, str]],
    scene_time: float,
) -> None:
    id_to_ent = {e.id: e for e in entities}
    etype = {e.id: str(getattr(e, "entity_type", "")) for e in entities}
    org_adj: dict[str, set[str]] = {}
    for a, b in structural_edges or []:
        if etype.get(a) == "organism" and etype.get(b) == "organism":
            org_adj.setdefault(a, set()).add(b)
            org_adj.setdefault(b, set()).add(a)
    seen_org: set[str] = set()
    pulse = 0.7 + 0.3 * math.sin(scene_time * 2.2)
    for start in org_adj:
        if start in seen_org:
            continue
        stack = [start]
        comp: list[str] = []
        while stack:
            u = stack.pop()
            if u in seen_org:
                continue
            seen_org.add(u)
            comp.append(u)
            for v in org_adj.get(u, ()):
                if v not in seen_org:
                    stack.append(v)
        if len(comp) < 2:
            continue
        sx = sy = 0.0
        for uid in comp:
            p = id_to_ent[uid].position
            sx += float(p[0])
            sy += float(p[1])
        n = float(len(comp))
        cx, cy = sx / n, sy / n
        r = 0.0
        for uid in comp:
            e = id_to_ent[uid]
            px, py = float(e.position[0]), float(e.position[1])
            rad = float(getattr(e, "radius", 18.0))
            r = max(r, math.hypot(px - cx, py - cy) + rad)
        r += 38.0
        hull_grad = QRadialGradient(cx, cy, r)
        hull_grad.setColorAt(0.0, QColor(90, 160, 230, _clamp_alpha(18 * pulse)))
        hull_grad.setColorAt(0.65, QColor(60, 120, 200, _clamp_alpha(42 * pulse)))
        hull_grad.setColorAt(1.0, QColor(40, 90, 160, _clamp_alpha(8 * pulse)))
        painter.setPen(QPen(QColor(130, 200, 255, _clamp_alpha(130 * pulse)), 2))
        painter.setBrush(QBrush(hull_grad))
        d = int(r * 2)
        painter.drawEllipse(int(cx - r), int(cy - r), d, d)


def _draw_glow_disc(
    painter: QPainter,
    cx: float,
    cy: float,
    radius: float,
    inner: QColor,
    outer: QColor,
    ring: Optional[QColor] = None,
) -> None:
    grad = QRadialGradient(cx, cy, radius)
    grad.setColorAt(0.0, inner)
    grad.setColorAt(0.55, outer)
    grad.setColorAt(1.0, QColor(outer.red(), outer.green(), outer.blue(), 0))
    if ring is not None:
        painter.setPen(QPen(ring, 2))
    else:
        painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(grad))
    d = int(radius * 2)
    painter.drawEllipse(int(cx - radius), int(cy - radius), d, d)


def paint_game_entity(painter: QPainter, entity: Any, scene_time: float) -> None:
    """游戏模式回退：方块贴图风，不绘制 PVAEC 细胞核与场井同心圆。"""
    cx = float(entity.position[0])
    cy = float(entity.position[1])
    r = max(4.0, float(getattr(entity, "radius", 18.0)))
    eid = str(getattr(entity, "id", ""))
    et = str(getattr(entity, "entity_type", ""))
    if et == "game_prop" or eid.startswith("wall") or et == "environment_well":
        color = QColor(100, 110, 130, 200)
        if eid == "exit_gate" or et == "nutrient":
            color = QColor(255, 200, 60, 220)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        if eid == "exit_gate" or et == "nutrient":
            painter.drawRoundedRect(int(cx - r), int(cy - r * 0.6), int(r * 2), int(r * 1.2), 4, 4)
        else:
            painter.drawRect(int(cx - r), int(cy - r * 0.35), int(r * 2), int(r * 0.7))
        return
    if eid.startswith("enemy_"):
        painter.setPen(QPen(QColor(20, 90, 40), 2))
        painter.setBrush(QBrush(QColor(72, 200, 96, 230)))
    else:
        painter.setPen(QPen(QColor(30, 70, 120), 2))
        painter.setBrush(QBrush(QColor(70, 170, 255, 230)))
    painter.drawRoundedRect(int(cx - r * 0.85), int(cy - r), int(r * 1.7), int(r * 2), 4, 4)


def paint_scene_entity(painter: QPainter, entity: Any, scene_time: float) -> None:
    """按 entity_type 绘制分层发光实体。"""
    cx = float(entity.position[0])
    cy = float(entity.position[1])
    r = max(3.0, float(getattr(entity, "radius", 18.0)))
    et = str(getattr(entity, "entity_type", ""))
    phase = _hash_phase(str(getattr(entity, "id", "")))
    pulse = 0.82 + 0.18 * math.sin(scene_time * 3.5 + phase)
    emission = float(getattr(entity, "emission_strength", 0.0) or 0.0)
    energy = getattr(entity, "energy", None)
    if energy is not None:
        try:
            emission = max(emission, min(1.0, float(energy) / 180.0))
        except (TypeError, ValueError):
            pass

    if et == "nutrient":
        glow_r = r * (1.35 + emission * 0.2)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            glow_r * pulse,
            QColor(255, 240, 160, 200),
            QColor(180, 220, 80, 90),
            QColor(255, 250, 200, 180),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 220, 220)))
        painter.drawEllipse(int(cx - r * 0.35), int(cy - r * 0.35), int(r * 0.7), int(r * 0.7))
        return

    if et == "environment_well":
        for i in range(3):
            ring_r = r * (1.0 + i * 0.55 + 0.12 * math.sin(scene_time * 2.0 + i + phase))
            alpha = _clamp_alpha((90 - i * 22) * pulse)
            painter.setPen(QPen(QColor(120, 190, 255, alpha), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            d = int(ring_r * 2)
            painter.drawEllipse(int(cx - ring_r), int(cy - ring_r), d, d)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            r * 0.85,
            QColor(160, 210, 255, 120),
            QColor(80, 140, 220, 40),
            QColor(200, 230, 255, 160),
        )
        return

    if et == "central_brain":
        glow_r = r * (1.25 + emission * 0.35)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            glow_r * pulse,
            QColor(255, 120, 180, 220),
            QColor(180, 60, 120, 70),
            QColor(255, 170, 210, 220),
        )
        path = QPainterPath()
        for i in range(6):
            ang = phase + i * (math.tau / 6.0) + scene_time * 0.4
            px = cx + math.cos(ang) * r * 0.72
            py = cy + math.sin(ang) * r * 0.72
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        painter.setPen(QPen(QColor(255, 200, 230, 180), 1.5))
        painter.setBrush(QBrush(QColor(255, 140, 190, 90)))
        painter.drawPath(path)
        return

    if et == "sensor":
        glow_r = r * (1.2 + emission * 0.25)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            glow_r,
            QColor(140, 255, 190, 200),
            QColor(60, 180, 120, 60),
            QColor(180, 255, 210, 200),
        )
        scan_ang = scene_time * 2.5 + phase
        ax = cx + math.cos(scan_ang) * r * 0.9
        ay = cy + math.sin(scan_ang) * r * 0.9
        painter.setPen(QPen(QColor(200, 255, 220, 160), 2))
        painter.drawLine(int(cx), int(cy), int(ax), int(ay))
        painter.setBrush(QBrush(QColor(220, 255, 235, 230)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - r * 0.28), int(cy - r * 0.28), int(r * 0.56), int(r * 0.56))
        return

    if et == "actuator":
        glow_r = r * (1.15 + emission * 0.2)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            glow_r,
            QColor(255, 190, 110, 210),
            QColor(200, 120, 40, 55),
            QColor(255, 210, 140, 200),
        )
        for i in range(3):
            ang = phase + i * (math.tau / 3.0) + math.sin(scene_time * 5.0 + i) * 0.35
            ox = cx + math.cos(ang) * r * 0.95
            oy = cy + math.sin(ang) * r * 0.95
            painter.setPen(QPen(QColor(255, 220, 160, 180), 2))
            painter.drawLine(int(cx), int(cy), int(ox), int(oy))
            painter.setBrush(QBrush(QColor(255, 200, 120, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(ox - r * 0.22), int(oy - r * 0.22), int(r * 0.44), int(r * 0.44))
        return

    if et == "organism":
        glow_r = r * (1.18 + emission * 0.3)
        _draw_glow_disc(
            painter,
            cx,
            cy,
            glow_r * pulse,
            QColor(160, 230, 255, 210),
            QColor(70, 150, 220, 65),
            QColor(190, 240, 255, 200),
        )
        nucleus_r = r * 0.42
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(220, 250, 255, 180)))
        painter.drawEllipse(int(cx - nucleus_r), int(cy - nucleus_r), int(nucleus_r * 2), int(nucleus_r * 2))
        return

    base = getattr(entity, "color", None)
    if isinstance(base, QColor):
        c = base
    else:
        c = QColor(140, 170, 255)
    _draw_glow_disc(
        painter,
        cx,
        cy,
        r * pulse,
        QColor(c.red(), c.green(), c.blue(), 180),
        QColor(c.red(), c.green(), c.blue(), 50),
        QColor(c.red(), c.green(), c.blue(), 200),
    )


def paint_sr_demo_legend(
    painter: QPainter,
    width: int,
    height: int,
    demo: dict[str, Any],
    *,
    bottom_margin: int = 58,
) -> None:
    """左下角圆角图例卡片。"""
    lines: list[str] = []
    title = str(demo.get("title", "")).strip()
    if title:
        lines.append(title)
    raw = demo.get("lines")
    if isinstance(raw, list):
        for line in raw:
            s = str(line).strip()
            if s:
                lines.append(s)
    if not lines:
        return

    margin = 14
    pad_x = 14
    pad_y = 12
    line_h = 17
    box_w = min(width - margin * 2, 440)
    box_h = pad_y * 2 + line_h * len(lines) + (8 if title else 0)
    x0 = margin
    y0 = max(margin, height - box_h - bottom_margin)

    path = QPainterPath()
    path.addRoundedRect(QRectF(x0, y0, box_w, box_h), 10, 10)
    card_grad = QLinearGradient(x0, y0, x0, y0 + box_h)
    card_grad.setColorAt(0.0, QColor(18, 24, 36, 215))
    card_grad.setColorAt(1.0, QColor(12, 16, 26, 235))
    painter.setPen(QPen(QColor(90, 140, 200, 140), 1))
    painter.setBrush(QBrush(card_grad))
    painter.drawPath(path)

    accent = QColor(130, 200, 255)
    body = QColor(200, 220, 240, 230)
    font = QFont(painter.font())
    font.setPointSize(10)
    painter.setFont(font)
    y_text = y0 + pad_y + line_h - 4
    if title:
        title_font = QFont(font)
        title_font.setBold(True)
        title_font.setPointSize(11)
        painter.setFont(title_font)
        painter.setPen(accent)
        painter.drawText(x0 + pad_x, y_text, title)
        painter.setFont(font)
        y_text += line_h + 4

    bullet_colors = {
        "代谢": QColor(160, 230, 255),
        "控制": QColor(255, 140, 190),
        "膜": QColor(130, 240, 170),
        "纤毛": QColor(255, 190, 110),
        "营养": QColor(195, 225, 120),
        "挑战": QColor(255, 200, 120),
    }
    for line in lines[1:] if title else lines:
        bullet = QColor(140, 170, 210)
        for key, col in bullet_colors.items():
            if key in line:
                bullet = col
                break
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bullet))
        painter.drawEllipse(x0 + pad_x, y_text - 9, 7, 7)
        painter.setPen(body)
        painter.drawText(x0 + pad_x + 14, y_text, line)
        y_text += line_h


def paint_session_banner_overlay(
    painter: QPainter,
    width: int,
    height: int,
    *,
    kind: str,
    message: str,
    elapsed: float,
    scene_time: float,
    title: Optional[str] = None,
    hint: Optional[str] = None,
) -> None:
    """Victory / 灭绝全屏横幅（渐入 + 脉动边框 + 粒子）。"""
    if not kind or not message.strip():
        return
    elapsed = max(0.0, float(elapsed))
    fade = min(1.0, elapsed / 0.45)
    pulse = 0.5 + 0.5 * math.sin(scene_time * 3.2 + elapsed * 2.0)

    is_victory = kind == "victory"
    accent = QColor(255, 220, 120) if is_victory else QColor(255, 100, 120)
    accent2 = QColor(120, 220, 255) if is_victory else QColor(180, 80, 100)
    if title and title.strip():
        title_text = title.strip()
    elif not any(ord(c) > 127 for c in message[:8]):
        title_text = "Victory" if is_victory else "Extinction"
    else:
        title_text = "目标达成" if is_victory else "种群灭绝"
    hint_text = (hint or "").strip()
    if not hint_text:
        hint_text = "按顶部 ▶ 继续 或 ⏹ 停止" if is_victory else "按 ⏹ 停止 后调整场景再试"
        if not any(ord(c) > 127 for c in message[:8]):
            hint_text = "Press ▶ Resume or ⏹ Stop" if is_victory else "Press ⏹ Stop and adjust the scene"

    dim = QColor(0, 0, 0, int(140 * fade))
    painter.fillRect(0, 0, width, height, dim)

    _paint_confetti_burst(
        painter,
        width,
        height,
        scene_time=scene_time,
        elapsed=elapsed,
        fade=fade,
        victory=is_victory,
    )

    card_w = min(width - 48, 520)
    card_h = 118
    cx, cy = width * 0.5, height * 0.42
    x0 = cx - card_w * 0.5
    y0 = cy - card_h * 0.5
    scale = 0.92 + 0.08 * fade + 0.02 * pulse
    sw, sh = card_w * scale, card_h * scale
    x0 = cx - sw * 0.5
    y0 = cy - sh * 0.5

    path = QPainterPath()
    path.addRoundedRect(QRectF(x0, y0, sw, sh), 14, 14)
    card_grad = QLinearGradient(x0, y0, x0, y0 + sh)
    card_grad.setColorAt(0.0, QColor(22, 28, 42, int(240 * fade)))
    card_grad.setColorAt(1.0, QColor(14, 18, 30, int(250 * fade)))
    border_alpha = int((150 + 80 * pulse) * fade)
    painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), border_alpha), 2))
    painter.setBrush(QBrush(card_grad))
    painter.drawPath(path)

    for i in range(12 if is_victory else 8):
        ang = scene_time * 1.8 + i * (math.tau / 12.0)
        dist = (sw * 0.35 + 18 * pulse) * fade
        px = cx + math.cos(ang) * dist
        py = cy + math.sin(ang) * dist * 0.55
        r = 3 + (i % 3)
        alpha = int(90 * fade * pulse)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(accent2.red(), accent2.green(), accent2.blue(), alpha)))
        painter.drawEllipse(int(px - r), int(py - r), r * 2, r * 2)

    title_font = QFont(painter.font())
    title_font.setBold(True)
    title_font.setPointSize(16)
    painter.setFont(title_font)
    painter.setPen(QColor(accent.red(), accent.green(), accent.blue(), int(255 * fade)))
    painter.drawText(int(x0 + 20), int(y0 + 38), title_text)

    body_font = QFont(painter.font())
    body_font.setPointSize(10)
    painter.setFont(body_font)
    painter.setPen(QColor(220, 230, 245, int(230 * fade)))
    msg = message.strip().split("\n")[0][:80]
    painter.drawText(int(x0 + 20), int(y0 + 62), msg)
    painter.setPen(QColor(160, 180, 210, int(180 * fade)))
    painter.drawText(int(x0 + 20), int(y0 + 84), hint_text[:72])


def _paint_confetti_burst(
    painter: QPainter,
    width: int,
    height: int,
    *,
    scene_time: float,
    elapsed: float,
    fade: float,
    victory: bool,
) -> None:
    """Victory 全屏粒子爆发（灭绝时为少量下落余烬）。"""
    if elapsed > 3.0 or fade <= 0.05:
        return
    count = 48 if victory else 18
    cx, cy = width * 0.5, height * 0.38
    for i in range(count):
        phase = _hash_phase(f"confetti-{i}")
        if victory:
            ang = phase + scene_time * 1.2 + i * 0.41
            dist = (80 + (i % 7) * 22) * fade + elapsed * 90 * (0.3 + (i % 5) * 0.12)
            px = cx + math.cos(ang) * dist
            py = cy + math.sin(ang) * dist * 0.65 - elapsed * 35 * (0.5 + phase)
            colors = (
                QColor(255, 230, 140),
                QColor(140, 220, 255),
                QColor(180, 255, 200),
                QColor(255, 180, 220),
            )
            col = colors[i % len(colors)]
        else:
            px = cx + math.sin(phase + i) * (120 + i * 8)
            py = cy + 40 + elapsed * 55 + (i % 9) * 6
            col = QColor(255, 90, 90)
        alpha = int((160 if victory else 100) * fade * max(0.0, 1.0 - elapsed / 3.0))
        if alpha < 8:
            continue
        w = 4 + (i % 3)
        h = 2 + (i % 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), alpha)))
        painter.drawRoundedRect(int(px), int(py), w, h, 1, 1)


class SrVisualRenderer:
    """SR 场景一帧绘制编排。"""

    def __init__(self) -> None:
        self._bg_cache = SrBackgroundCache()

    def paint_frame(
        self,
        painter: QPainter,
        width: int,
        height: int,
        *,
        entities: list[Any],
        structural_edges: Iterable[tuple[str, str]],
        signal_edges: Iterable[dict[str, Any]],
        scene_time: float,
        demo_legend: Optional[dict[str, Any]] = None,
        show_legend: bool = False,
        session_banner: Optional[dict[str, Any]] = None,
        sprite_catalog: Optional[Any] = None,
        connection_edges: Optional[Iterable[dict[str, Any]]] = None,
        spring_links: Optional[Iterable[Any]] = None,
        game_mode: bool = False,
        game_fx: Optional[Any] = None,
        game_player_id: Optional[str] = None,
        emissions_prev: Optional[Mapping[str, float]] = None,
        niche_pressure: float = 0.0,
    ) -> None:
        q = sr_render_quality()
        if not q.antialiasing:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self._bg_cache.paint(
            painter,
            width,
            height,
            scene_time,
            paint_sr_background,
            enabled=q.cache_background,
        )
        composite_ids: set[str] = set()
        if entities:
            id_to_pos = {e.id: e.position for e in entities}
            id_to_ent, id_to_type = _entity_maps(entities)
            if not game_mode:
                paint_well_affinity_lines(painter, entities)
                composite_ids = paint_composite_cells(
                    painter,
                    entities,
                    structural_edges,
                    signal_edges,
                    scene_time,
                    spring_links,
                    emissions_prev=emissions_prev,
                    niche_pressure=niche_pressure,
                )
                paint_sr_link_physics(
                    painter,
                    connection_edges or (),
                    spring_links or (),
                    id_to_ent,
                    id_to_type,
                    scene_time=scene_time,
                )
                paint_structural_edges(
                    painter,
                    structural_edges,
                    id_to_pos,
                    id_to_type=id_to_type,
                    skip_entity_ids=composite_ids,
                )
                paint_chemo_signal_edges(
                    painter,
                    signal_edges,
                    id_to_pos,
                    scene_time,
                    skip_entity_ids=composite_ids,
                )
            else:
                composite_ids = set()
            draw_order = (
                "environment_well",
                "game_prop",
                "nutrient",
                "central_brain",
                "empty",
                "game_actor",
                "organism",
            )
            rank = {name: i for i, name in enumerate(draw_order)}

            def sort_key(ent: Any) -> tuple[int, float]:
                et = str(getattr(ent, "entity_type", ""))
                return (rank.get(et, 99), -float(getattr(ent, "radius", 0.0)))

            for entity in sorted(entities, key=sort_key):
                if str(getattr(entity, "id", "")) in composite_ids:
                    continue
                try:
                    painted = False
                    if sprite_catalog is not None and getattr(sprite_catalog, "can_paint", None):
                        if sprite_catalog.can_paint(entity):
                            sprite_catalog.paint_entity(painter, entity, scene_time)
                            painted = True
                    if not painted:
                        if game_mode:
                            paint_game_entity(painter, entity, scene_time)
                        else:
                            paint_scene_entity(painter, entity, scene_time)
                except Exception:
                    continue
        if game_mode and game_fx is not None:
            try:
                from core.Lotucosm.sr_game_effects import paint_game_fx

                aim_ent = None
                if game_player_id:
                    aim_ent = next(
                        (e for e in (entities or []) if str(getattr(e, "id", "")) == game_player_id),
                        None,
                    )
                paint_game_fx(painter, game_fx, aim_entity=aim_ent)
            except Exception:
                pass
        elif game_mode and game_player_id:
            try:
                from core.Lotucosm.sr_game_effects import paint_game_aim_line

                aim_ent = next(
                    (e for e in (entities or []) if str(getattr(e, "id", "")) == game_player_id),
                    None,
                )
                if aim_ent is not None:
                    paint_game_aim_line(painter, aim_ent)
            except Exception:
                pass
        if show_legend and isinstance(demo_legend, dict):
            paint_sr_demo_legend(painter, width, height, demo_legend)
        if isinstance(session_banner, dict):
            kind = str(session_banner.get("kind", ""))
            msg = str(session_banner.get("message", ""))
            elapsed = float(session_banner.get("elapsed", 0.0))
            if kind and msg:
                paint_session_banner_overlay(
                    painter,
                    width,
                    height,
                    kind=kind,
                    message=msg,
                    elapsed=elapsed,
                    scene_time=scene_time,
                    title=str(session_banner.get("title", "") or "") or None,
                    hint=str(session_banner.get("hint", "") or "") or None,
                )
