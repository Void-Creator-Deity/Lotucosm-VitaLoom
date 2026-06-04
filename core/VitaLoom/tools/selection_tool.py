# -*- coding: utf-8 -*-
"""场景图节点 Node 与连线 ConnectionLine 数据模型（SceneViewport 绘制用）。

排错: 连线丢失 → start/end 节点 id 与 load_scene_data 实体 id 对齐。
"""

from __future__ import annotations

import math
import os
from typing import Any, Optional

from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient

from core.VitaLoom.core.logger import get_logger

logger = get_logger("SelectionTool")


class Node:
    """场景视口中的实体节点（位置、类型、脚本、序列化 to_dict）。"""

    def __init__(self, node_id: str, x: float, y: float, node_type: str = "sensor"):
        self.id = node_id
        self.x = x
        self.y = y
        self.name = node_id
        self.type = node_type
        self.radius = 25.0
        self.scripts: list[dict] = []
        self.sprite_path: str = ""
        self.sr_visual: Optional[dict[str, Any]] = None
        self.pinned: bool = False
        self._cached_pixmap = None
        self.connections: list["ConnectionLine"] = []

        if node_type == "organism":
            self.color = QColor(100, 150, 200)
            self.radius = 30.0
        elif node_type == "sensor":
            self.color = QColor(0, 255, 0)
        elif node_type == "actuator":
            self.color = QColor(255, 0, 0)
        elif node_type == "central_brain":
            self.color = QColor(255, 255, 0)
            self.radius = 25.0
        elif node_type in ("game_actor",):
            self.color = QColor(80, 180, 255)
            self.radius = 22.0
        elif node_type in ("game_prop",):
            self.color = QColor(140, 150, 170)
            self.radius = 20.0
        else:
            self.color = QColor(255, 255, 255)

    def set_sprite_path(self, path: str) -> None:
        self.sprite_path = path or ""
        self._cached_pixmap = None

    def _resolve_sprite_load_path(self) -> str:
        p = (self.sprite_path or "").strip()
        if not p:
            return ""
        if os.path.isabs(p) and os.path.isfile(p):
            return p
        try:
            from core.VitaLoom.core.editor_context import get_editor_context

            root = getattr(get_editor_context(), "current_project_path", None) or ""
            if root and not os.path.isabs(p):
                cand = os.path.normpath(os.path.join(root, p.replace("/", os.sep)))
                if os.path.isfile(cand):
                    return cand
        except Exception as e:
            logger.debug("解析资源相对路径失败: %s", e)
        return p

    def contains(self, point: QPoint) -> bool:
        return (point.x() - self.x) ** 2 + (point.y() - self.y) ** 2 <= self.radius ** 2

    def update_position(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)

    def draw(self, painter: QPainter) -> None:
        if self.sprite_path:
            try:
                from PyQt6.QtGui import QPixmap

                if self._cached_pixmap is None:
                    load_path = self._resolve_sprite_load_path()
                    self._cached_pixmap = QPixmap(load_path) if load_path else QPixmap()
                if self._cached_pixmap and not self._cached_pixmap.isNull():
                    img_size = int(self.radius * 2)
                    scaled = self._cached_pixmap.scaled(
                        img_size,
                        img_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    img_x = int(self.x - scaled.width() / 2)
                    img_y = int(self.y - scaled.height() / 2)
                    painter.drawPixmap(img_x, img_y, scaled)
                    painter.setPen(QPen(QColor(100, 150, 255, 150), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(img_x, img_y, scaled.width(), scaled.height())
                    return
            except Exception as e:
                logger.debug("绘制精灵失败: %s", e)

        gradient = QLinearGradient(self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius)
        gradient.setColorAt(0, self.color.lighter(120))
        gradient.setColorAt(1, self.color.darker(120))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.color.darker(150), 2))
        painter.drawEllipse(int(self.x - self.radius), int(self.y - self.radius), int(self.radius * 2), int(self.radius * 2))

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "position": [self.x, self.y],
            "radius": self.radius,
            "scripts": self.scripts,
        }
        if self.sprite_path:
            data["sprite_path"] = self.sprite_path
        if isinstance(self.sr_visual, dict) and self.sr_visual:
            data["sr_visual"] = dict(self.sr_visual)
        if self.pinned:
            data["pinned"] = True
        return data


class ConnectionLine:
    """两 Node 间的有向连线，供绘制与 Inspector 编辑。"""

    def __init__(self, start_node: Node, end_node: Node):
        self.start_node = start_node
        self.end_node = end_node
        self.weight = 1.0
        self.color = QColor(100, 100, 255)
        self.width = 2

    def draw(self, painter: QPainter) -> None:
        start_x = int(self.start_node.x)
        start_y = int(self.start_node.y)
        end_x = int(self.end_node.x)
        end_y = int(self.end_node.y)
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.hypot(dx, dy)
        if length < 5:
            return
        unit_dx = dx / length
        unit_dy = dy / length

        line_pen = QPen()
        line_gradient = QLinearGradient(start_x, start_y, end_x, end_y)
        line_gradient.setColorAt(0, self.color.lighter(150))
        line_gradient.setColorAt(0.5, self.color.darker(50))
        line_gradient.setColorAt(1, self.color.lighter(150))
        line_pen.setBrush(line_gradient)
        line_pen.setWidth(self.width)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(line_pen)
        painter.drawLine(start_x, start_y, end_x, end_y)

        arrow_size = 8
        arrow_width = 14
        arrow_base = QPoint(
            end_x - int(unit_dx * arrow_size),
            end_y - int(unit_dy * arrow_size),
        )
        arrow_p1 = QPoint(end_x, end_y)
        perp_x = -unit_dy
        perp_y = unit_dx
        arrow_p2 = QPoint(
            arrow_base.x() + int(perp_x * arrow_width / 2),
            arrow_base.y() + int(perp_y * arrow_width / 2),
        )
        arrow_p3 = QPoint(
            arrow_base.x() - int(perp_x * arrow_width / 2),
            arrow_base.y() - int(perp_y * arrow_width / 2),
        )
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow_p1, arrow_p2, arrow_p3)

    def contains(self, point: Any, tolerance: float = 8.0) -> bool:
        if isinstance(point, QPoint):
            p = QPointF(point.x(), point.y())
        elif isinstance(point, QPointF):
            p = point
        else:
            try:
                p = QPointF(float(point.x()), float(point.y()))
            except Exception:
                return False

        a = QPointF(float(self.start_node.x), float(self.start_node.y))
        b = QPointF(float(self.end_node.x), float(self.end_node.y))

        def distance_point_line(pf: QPointF, pa: QPointF, pb: QPointF) -> float:
            if pa == pb:
                return (pf - pa).manhattanLength()
            ap = pf - pa
            ab = pb - pa
            dot_ab_ab = QPointF.dotProduct(ab, ab)
            if dot_ab_ab == 0:
                return (pf - pa).manhattanLength()
            t = max(0.0, min(1.0, QPointF.dotProduct(ap, ab) / dot_ab_ab))
            projection = pa + t * ab
            return (pf - projection).manhattanLength()

        return distance_point_line(p, a, b) <= tolerance

    def to_dict(self) -> dict:
        return {
            "start": self.start_node.id,
            "end": self.end_node.id,
            "weight": self.weight,
        }
