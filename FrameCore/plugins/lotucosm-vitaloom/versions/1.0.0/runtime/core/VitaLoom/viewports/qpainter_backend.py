# -*- coding: utf-8 -*-
"""QPainter viewport backend wrapping the existing SR visual renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    DrawCommand,
    LineCommand,
    TextCommand,
    compile_viewport_draw_commands,
)
from core.VitaLoom.viewports.viewport_backend import ViewportBackendInfo
from core.VitaLoom.viewports.viewport_snapshot import ViewportFrameSnapshot


@dataclass
class QPainterViewportFrame:
    width: int
    height: int
    entities: list[Any] = field(default_factory=list)
    structural_edges: Iterable[tuple[str, str]] = field(default_factory=tuple)
    signal_edges: Iterable[dict[str, Any]] = field(default_factory=tuple)
    scene_time: float = 0.0
    demo_legend: Optional[dict[str, Any]] = None
    show_legend: bool = False
    session_banner: Optional[dict[str, Any]] = None
    sprite_catalog: Optional[Any] = None
    connection_edges: Optional[Iterable[dict[str, Any]]] = None
    spring_links: Optional[Iterable[Any]] = None
    game_mode: bool = False
    game_fx: Optional[Any] = None
    game_player_id: Optional[str] = None
    emissions_prev: Optional[Mapping[str, float]] = None
    niche_pressure: float = 0.0


class QPainterViewportBackend:
    info = ViewportBackendInfo(
        name="qpainter",
        supports_gpu=False,
        supports_batching=False,
    )

    def __init__(self, renderer: Any | None = None) -> None:
        if renderer is None:
            from core.VitaLoom.viewports.sr_visual_renderer import SrVisualRenderer

            renderer = SrVisualRenderer()
        self._renderer = renderer
        self._quality: dict[str, Any] = {}
        self._width = 0
        self._height = 0
        self._render_calls = 0
        self._command_render_calls = 0
        self._command_renderer = QPainterDrawCommandRenderer()

    def render(self, target: Any, frame: QPainterViewportFrame | ViewportFrameSnapshot) -> None:
        if isinstance(frame, ViewportFrameSnapshot):
            self._width = int(frame.width)
            self._height = int(frame.height)
            self._render_calls += 1
            self._command_render_calls += 1
            self._command_renderer.render_frame(target, frame)
            return
        self._width = int(frame.width)
        self._height = int(frame.height)
        self._render_calls += 1
        self._renderer.paint_frame(
            target,
            self._width,
            self._height,
            entities=list(frame.entities),
            structural_edges=frame.structural_edges,
            signal_edges=frame.signal_edges,
            scene_time=float(frame.scene_time),
            demo_legend=frame.demo_legend,
            show_legend=bool(frame.show_legend),
            session_banner=frame.session_banner,
            sprite_catalog=frame.sprite_catalog,
            connection_edges=frame.connection_edges,
            spring_links=frame.spring_links,
            game_mode=bool(frame.game_mode),
            game_fx=frame.game_fx,
            game_player_id=frame.game_player_id,
            emissions_prev=frame.emissions_prev,
            niche_pressure=float(frame.niche_pressure),
        )

    def resize(self, width: int, height: int) -> None:
        self._width = int(width)
        self._height = int(height)

    def set_quality(self, quality: dict[str, Any]) -> None:
        self._quality = dict(quality)

    def stats(self) -> dict[str, Any]:
        return {
            "backend": self.info.name,
            "supports_gpu": self.info.supports_gpu,
            "supports_batching": self.info.supports_batching,
            "width": self._width,
            "height": self._height,
            "render_calls": self._render_calls,
            "command_render_calls": self._command_render_calls,
            "opengl_parity_ready": False,
            "opengl_batching_ready": False,
            "default_switch_allowed": False,
            "quality": dict(self._quality),
        }


class QPainterDrawCommandRenderer:
    def __init__(self) -> None:
        self._pen_cache: dict[tuple[tuple[int, int, int, int], float], Any] = {}
        self._brush_cache: dict[tuple[int, int, int, int], Any] = {}

    def render_frame(self, painter: Any, frame: ViewportFrameSnapshot) -> None:
        self.render_commands(painter, compile_viewport_draw_commands(frame))

    def render_commands(self, painter: Any, commands: Iterable[DrawCommand]) -> None:
        for command in commands:
            if isinstance(command, LineCommand):
                self._render_line(painter, command)
            elif isinstance(command, CircleCommand):
                self._render_circle(painter, command)
            elif isinstance(command, TextCommand):
                self._render_text(painter, command)

    def _render_circle(self, painter: Any, command: CircleCommand) -> None:
        painter.setPen(self._cached_pen(command.stroke, command.stroke_width))
        painter.setBrush(self._cached_brush(command.fill))
        x = int(round(command.center[0] - command.radius))
        y = int(round(command.center[1] - command.radius))
        size = int(round(command.radius * 2.0))
        painter.drawEllipse(x, y, size, size)

    def _render_line(self, painter: Any, command: LineCommand) -> None:
        painter.setPen(self._cached_pen(command.color, command.width))
        painter.drawLine(
            int(round(command.start[0])),
            int(round(command.start[1])),
            int(round(command.end[0])),
            int(round(command.end[1])),
        )

    def _render_text(self, painter: Any, command: TextCommand) -> None:
        painter.setPen(self._cached_pen(command.color, 1.0))
        painter.drawText(int(round(command.position[0])), int(round(command.position[1])), command.text)

    def _cached_pen(self, color: tuple[int, int, int, int], width: float) -> Any:
        key = (tuple(int(part) for part in color), float(width))
        cached = self._pen_cache.get(key)
        if cached is None:
            cached = _pen(key[0], key[1])
            self._pen_cache[key] = cached
        return cached

    def _cached_brush(self, color: tuple[int, int, int, int]) -> Any:
        key = tuple(int(part) for part in color)
        cached = self._brush_cache.get(key)
        if cached is None:
            cached = _brush(key)
            self._brush_cache[key] = cached
        return cached


def _pen(color: tuple[int, int, int, int], width: float) -> Any:
    try:
        from PyQt6.QtGui import QColor, QPen

        return QPen(QColor(*color), float(width))
    except Exception:
        return {"color": color, "width": float(width)}


def _brush(color: tuple[int, int, int, int]) -> Any:
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor, QBrush

        if color[3] <= 0:
            return Qt.BrushStyle.NoBrush
        return QBrush(QColor(*color))
    except Exception:
        return {"color": color}


__all__ = [
    "QPainterDrawCommandRenderer",
    "QPainterViewportBackend",
    "QPainterViewportFrame",
]
