# -*- coding: utf-8 -*-
"""Immutable viewport render snapshots copied from live runtime objects."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


Vec2 = tuple[float, float]


@dataclass(frozen=True)
class ViewportEntitySnapshot:
    id: str
    entity_type: str
    position: Vec2
    velocity: Vec2 = (0.0, 0.0)
    radius: float = 18.0
    selected: bool = False
    visible: bool = True
    pinned: bool = False
    membrane_locked: bool = False
    visual_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ViewportEdgeSnapshot:
    source_id: str
    target_id: str
    kind: str = "hard"
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ViewportCameraSnapshot:
    position: Vec2 = (0.0, 0.0)
    zoom: float = 1.0
    rotation: float = 0.0


@dataclass(frozen=True)
class ViewportFrameSnapshot:
    width: int
    height: int
    scene_time: float = 0.0
    camera: ViewportCameraSnapshot = field(default_factory=ViewportCameraSnapshot)
    entities: tuple[ViewportEntitySnapshot, ...] = field(default_factory=tuple)
    edges: tuple[ViewportEdgeSnapshot, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


def build_viewport_entity_snapshot(entity: Any) -> ViewportEntitySnapshot:
    """Copy the render-facing fields from a live entity or entity-like mapping."""

    return ViewportEntitySnapshot(
        id=str(_read(entity, "id", "")),
        entity_type=str(_read(entity, "entity_type", _read(entity, "type", ""))),
        position=_vec2(_read(entity, "position", None)),
        velocity=_vec2(_read(entity, "velocity", None)),
        radius=_float(_read(entity, "radius", 18.0), 18.0),
        selected=_bool(_read(entity, "selected", False), False),
        visible=_bool(_read(entity, "visible", True), True),
        pinned=_bool(_read(entity, "pinned", False), False),
        membrane_locked=_bool(_read(entity, "membrane_locked", False), False),
        visual_state=_mapping_copy(_visual_state_source(entity)),
    )


def build_viewport_edge_snapshot(edge: Any) -> ViewportEdgeSnapshot:
    return ViewportEdgeSnapshot(
        source_id=str(_read(edge, "source_id", _read(edge, "source", _read(edge, "a", "")))),
        target_id=str(_read(edge, "target_id", _read(edge, "target", _read(edge, "b", "")))),
        kind=str(_read(edge, "kind", _read(edge, "link_kind", "hard"))),
        weight=_float(_read(edge, "weight", 1.0), 1.0),
        metadata=_mapping_copy(_read(edge, "metadata", {})),
    )


def build_viewport_camera_snapshot(camera: Any | None = None) -> ViewportCameraSnapshot:
    if camera is None:
        return ViewportCameraSnapshot()
    return ViewportCameraSnapshot(
        position=_vec2(_read(camera, "position", None)),
        zoom=_float(_read(camera, "zoom", 1.0), 1.0),
        rotation=_float(_read(camera, "rotation", 0.0), 0.0),
    )


def build_viewport_frame_snapshot(
    entities: Iterable[Any] | None = None,
    *,
    width: Any = 0,
    height: Any = 0,
    scene_time: Any = 0.0,
    camera: Any | None = None,
    edges: Iterable[Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ViewportFrameSnapshot:
    return ViewportFrameSnapshot(
        width=_int(width, 0),
        height=_int(height, 0),
        scene_time=_float(scene_time, 0.0),
        camera=build_viewport_camera_snapshot(camera),
        entities=tuple(build_viewport_entity_snapshot(entity) for entity in (entities or ())),
        edges=tuple(build_viewport_edge_snapshot(edge) for edge in (edges or ())),
        metadata=_mapping_copy(metadata or {}),
    )


def _read(source: Any, name: str, default: Any) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return bool(value)


def _vec2(value: Any) -> Vec2:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        try:
            return (_float(value[0], 0.0), _float(value[1], 0.0))
        except (IndexError, TypeError):
            return (0.0, 0.0)
    return (0.0, 0.0)


def _visual_state_source(entity: Any) -> Mapping[str, Any]:
    for name in ("sr_visual_state", "visual_state"):
        value = _read(entity, name, None)
        if isinstance(value, Mapping):
            return value
    return {}


def _mapping_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _freeze_value(item) for key, item in value.items()}


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _mapping_copy(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


__all__ = [
    "ViewportCameraSnapshot",
    "ViewportEdgeSnapshot",
    "ViewportEntitySnapshot",
    "ViewportFrameSnapshot",
    "build_viewport_camera_snapshot",
    "build_viewport_edge_snapshot",
    "build_viewport_entity_snapshot",
    "build_viewport_frame_snapshot",
]
