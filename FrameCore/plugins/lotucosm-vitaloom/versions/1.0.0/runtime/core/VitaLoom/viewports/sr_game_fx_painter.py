# -*- coding: utf-8 -*-
"""QPainter Host Adapter for SR game effects.

The state model stays in ``core.Lotucosm.sr_game_effects`` and remains Qt-free;
this module is the only owner of the concrete QPainter projection.
"""

from __future__ import annotations

import math
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from core.Lotucosm.sr_game_effects import SrGameFxState


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
    for item in state.swings:
        life = float(item.get("life", 0.0))
        alpha = min(1.0, life / 0.14)
        rng = float(item.get("range", 28.0))
        arc = float(item.get("arc_half", 0.65))
        angle = float(item.get("angle", 0.0))
        cx = float(item.get("x", 0.0))
        cy = float(item.get("y", 0.0))
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(angle))
        color = QColor(str(item.get("color", "#c8e0ff")))
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

    for item in state.floats:
        life = float(item.get("life", 0.0))
        painter.save()
        painter.setOpacity(min(1.0, life * 2.0))
        painter.setPen(QPen(QColor(str(item.get("color", "#ffeb99")))))
        painter.drawText(int(item["x"]), int(item["y"]), str(item.get("text", "")))
        painter.restore()


def paint_game_aim_line(painter: QPainter, entity: Any, *, length: float = 20.0) -> None:
    """鼠标瞄准辅助：从玩家中心沿 aim_angle 画短线。"""
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


__all__ = ["paint_game_aim_line", "paint_game_fx", "paint_hit_flash_overlay"]
