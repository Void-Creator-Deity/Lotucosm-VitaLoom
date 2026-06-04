# -*- coding: utf-8
"""游戏模式战斗反馈：飘字、挥砍弧（参考 rift-delve effects.js / melee.js）。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen


@dataclass
class SrGameFxState:
    floats: list[dict[str, Any]] = field(default_factory=list)
    swings: list[dict[str, Any]] = field(default_factory=list)


def create_fx_state() -> SrGameFxState:
    return SrGameFxState()


def ingest_fx_requests(state: SrGameFxState, requests: Sequence[Mapping[str, Any]]) -> None:
    for req in requests:
        kind = str(req.get("type", ""))
        if kind == "float":
            state.floats.append(
                {
                    "x": float(req.get("x", 0.0)),
                    "y": float(req.get("y", 0.0)),
                    "text": str(req.get("text", "")),
                    "life": float(req.get("life", 0.65)),
                    "color": str(req.get("color", "#ffeb99")),
                    "vy": float(req.get("vy", -48.0)),
                }
            )
        elif kind == "swing":
            state.swings.append(
                {
                    "x": float(req.get("x", 0.0)),
                    "y": float(req.get("y", 0.0)),
                    "angle": float(req.get("angle", 0.0)),
                    "range": float(req.get("range", 28.0)),
                    "arc_half": float(req.get("arc_half", 0.65)),
                    "life": float(req.get("life", 0.14)),
                    "color": str(req.get("color", "#c8e0ff")),
                }
            )


def update_game_fx(state: SrGameFxState, dt: float) -> None:
    next_floats: list[dict[str, Any]] = []
    for f in state.floats:
        f["life"] -= dt
        f["y"] += f["vy"] * dt
        if f["life"] > 0.0:
            next_floats.append(f)
    state.floats = next_floats

    next_swings: list[dict[str, Any]] = []
    for s in state.swings:
        s["life"] -= dt
        if s["life"] > 0.0:
            next_swings.append(s)
    state.swings = next_swings


def entity_hit_flash(entity: Any) -> float:
    hud = getattr(entity, "sr_debug_hud", None)
    if not isinstance(hud, dict):
        return 0.0
    try:
        return max(0.0, float(hud.get("hit_flash", 0.0)))
    except (TypeError, ValueError):
        return 0.0


def paint_hit_flash_overlay(painter: QPainter, cx: float, cy: float, radius: float, flash: float) -> None:
    if flash <= 0.0:
        return
    alpha = min(0.75, flash * 3.5)
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, int(255 * alpha)))
    d = int(radius * 2.2)
    painter.drawEllipse(int(cx - d * 0.5), int(cy - d * 0.5), d, d)
    painter.restore()


def paint_game_fx(
    painter: QPainter,
    state: SrGameFxState | None,
    *,
    aim_entity: Any | None = None,
) -> None:
    if aim_entity is not None:
        paint_game_aim_line(painter, aim_entity)
    if state is None:
        return
    for s in state.swings:
        life = float(s.get("life", 0.0))
        alpha = min(1.0, life / 0.14)
        rng = float(s.get("range", 28.0))
        arc = float(s.get("arc_half", 0.65))
        angle = float(s.get("angle", 0.0))
        cx = float(s.get("x", 0.0))
        cy = float(s.get("y", 0.0))
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(angle))
        color = QColor(str(s.get("color", "#c8e0ff")))
        color.setAlphaF(alpha * 0.85)
        painter.setPen(QPen(color, 3))
        fill = QColor(color.red(), color.green(), color.blue(), int(alpha * 60))
        painter.setBrush(fill)
        start_deg = 90.0 - math.degrees(arc)
        span_deg = math.degrees(arc * 2.0)
        painter.drawPie(
            int(-rng),
            int(-rng),
            int(rng * 2),
            int(rng * 2),
            int(start_deg * 16),
            int(span_deg * 16),
        )
        painter.restore()

    for f in state.floats:
        life = float(f.get("life", 0.0))
        painter.save()
        painter.setOpacity(min(1.0, life * 2.0))
        painter.setPen(QPen(QColor(str(f.get("color", "#ffeb99")))))
        painter.drawText(int(f["x"]), int(f["y"]), str(f.get("text", "")))
        painter.restore()


def paint_game_aim_line(painter: QPainter, entity: Any, *, length: float = 20.0) -> None:
    """鼠标瞄准辅助：从玩家中心沿 aim_angle 画短线（参考 Rift Delve）。"""
    hud = getattr(entity, "sr_debug_hud", None)
    if not isinstance(hud, dict):
        return
    try:
        angle = float(hud.get("aim_angle", 0.0))
    except (TypeError, ValueError):
        return
    cx = float(entity.position[0])
    cy = float(entity.position[1])
    ex = cx + math.cos(angle) * length
    ey = cy + math.sin(angle) * length
    painter.save()
    painter.setPen(QPen(QColor(200, 220, 255, 180), 2))
    painter.drawLine(int(cx), int(cy), int(ex), int(ey))
    painter.restore()
