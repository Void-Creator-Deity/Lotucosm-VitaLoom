# -*- coding: utf-8 -*-
"""Backend-neutral viewport draw commands compiled from immutable snapshots."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Literal, TypeAlias

from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


Color: TypeAlias = tuple[int, int, int, int]
Vec2: TypeAlias = tuple[float, float]


@dataclass(frozen=True)
class CircleCommand:
    kind: Literal["circle"]
    entity_id: str
    center: Vec2
    radius: float
    fill: Color
    stroke: Color
    stroke_width: float = 1.0


@dataclass(frozen=True)
class LineCommand:
    kind: Literal["line"]
    edge_id: str
    start: Vec2
    end: Vec2
    color: Color
    width: float = 1.0


@dataclass(frozen=True)
class TextCommand:
    kind: Literal["text"]
    text_id: str
    position: Vec2
    text: str
    color: Color
    size: float = 12.0


DrawCommand: TypeAlias = CircleCommand | LineCommand | TextCommand


_ENTITY_COLORS: dict[str, tuple[Color, Color]] = {
    "organism": ((120, 210, 245, 220), (205, 245, 255, 230)),
    "sensor": ((120, 245, 180, 220), (215, 255, 230, 230)),
    "actuator": ((255, 185, 95, 220), (255, 225, 160, 230)),
    "central_brain": ((255, 135, 190, 220), (255, 210, 235, 230)),
    "nutrient": ((245, 235, 135, 220), (255, 255, 220, 230)),
    "environment_well": ((120, 190, 255, 180), (195, 230, 255, 220)),
}
_DEFAULT_FILL: Color = (145, 170, 240, 220)
_DEFAULT_STROKE: Color = (210, 225, 255, 220)
_SELECTED_STROKE: Color = (255, 230, 110, 255)
_HARD_EDGE: Color = (120, 155, 205, 180)
_SIGNAL_EDGE: Color = (115, 235, 195, 170)


def compile_viewport_draw_commands(frame: ViewportFrameSnapshot) -> tuple[DrawCommand, ...]:
    camera = frame.camera
    zoom = float(camera.zoom)
    if not math.isfinite(zoom) or zoom <= 0.0:
        raise ValueError(f"camera.zoom must be a finite positive value, got {camera.zoom!r}")

    visible_entities = {
        entity.id: entity
        for entity in sorted(frame.entities, key=lambda item: item.id)
        if entity.visible
    }
    commands: list[DrawCommand] = []

    for edge in sorted(frame.edges, key=lambda item: (item.source_id, item.target_id, item.kind)):
        source = visible_entities.get(edge.source_id)
        target = visible_entities.get(edge.target_id)
        if source is None or target is None:
            continue
        commands.append(
            LineCommand(
                kind="line",
                edge_id=f"{edge.source_id}:{edge.target_id}",
                start=_project_world_position(source.position, frame),
                end=_project_world_position(target.position, frame),
                color=_edge_color(edge.kind),
                width=max(1.0, float(edge.weight)) * zoom,
            )
        )

    for entity in visible_entities.values():
        fill, stroke = _entity_colors(entity)
        commands.append(
            CircleCommand(
                kind="circle",
                entity_id=entity.id,
                center=_project_world_position(entity.position, frame),
                radius=max(0.0, float(entity.radius)) * zoom,
                fill=fill,
                stroke=stroke,
                stroke_width=zoom,
            )
        )
        if entity.selected:
            commands.append(
                CircleCommand(
                    kind="circle",
                    entity_id=f"{entity.id}:selected",
                    center=_project_world_position(entity.position, frame),
                    radius=(max(0.0, float(entity.radius)) + 3.0) * zoom,
                    fill=(0, 0, 0, 0),
                    stroke=_SELECTED_STROKE,
                    stroke_width=2.0 * zoom,
                )
            )

    return tuple(commands)


def _project_world_position(position: Vec2, frame: ViewportFrameSnapshot) -> Vec2:
    """Project one world-space point through the Qt-free camera Interface.

    Camera rotation is expressed in radians. Scaling and rotation happen around
    the world origin before the screen-space camera position is applied. The
    default camera therefore preserves the legacy command stream exactly.
    """

    zoom = float(frame.camera.zoom)
    scaled_x = float(position[0]) * zoom
    scaled_y = float(position[1]) * zoom
    rotation = float(frame.camera.rotation)
    if rotation:
        cosine = math.cos(rotation)
        sine = math.sin(rotation)
        scaled_x, scaled_y = (
            scaled_x * cosine - scaled_y * sine,
            scaled_x * sine + scaled_y * cosine,
        )
    return (
        scaled_x + float(frame.camera.position[0]),
        scaled_y + float(frame.camera.position[1]),
    )


def _entity_colors(entity: ViewportEntitySnapshot) -> tuple[Color, Color]:
    default_fill, default_stroke = _ENTITY_COLORS.get(
        entity.entity_type,
        (_DEFAULT_FILL, _DEFAULT_STROKE),
    )
    return (
        _color(entity.visual_state.get("fill"), default_fill),
        _color(entity.visual_state.get("stroke"), default_stroke),
    )


def _edge_color(kind: str) -> Color:
    if kind in {"signal", "soft"}:
        return _SIGNAL_EDGE
    return _HARD_EDGE


def _color(value: object, default: Color) -> Color:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 4:
        return default
    try:
        return tuple(max(0, min(255, int(part))) for part in value)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return default


__all__ = [
    "CircleCommand",
    "Color",
    "DrawCommand",
    "LineCommand",
    "TextCommand",
    "Vec2",
    "compile_viewport_draw_commands",
]
