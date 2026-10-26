# -*- coding: utf-8 -*-
"""Pure viewport draw-command batching for the opt-in OpenGL backend."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    DrawCommand,
    LineCommand,
    TextCommand,
)


Primitive: TypeAlias = Literal["circle", "line", "text"]
StyleKey: TypeAlias = tuple[Any, ...]
InstancePayload: TypeAlias = tuple[float | int | str, ...]


@dataclass(frozen=True)
class OpenGLBatch:
    primitive: Primitive
    style_key: StyleKey
    ids: tuple[str, ...]
    instances: tuple[InstancePayload, ...]

    @property
    def instance_count(self) -> int:
        return len(self.instances)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive": self.primitive,
            "style_key": self.style_key,
            "ids": self.ids,
            "instances": self.instances,
            "instance_count": self.instance_count,
        }


def compile_opengl_batches(commands: tuple[DrawCommand, ...] | list[DrawCommand]) -> tuple[OpenGLBatch, ...]:
    """Batch matching styles while preserving the viewport's semantic layers."""

    grouped: "OrderedDict[StyleKey, tuple[Primitive, list[str], list[InstancePayload]]]" = OrderedDict()
    for command in sorted(commands, key=_command_sort_key):
        primitive, style_key, item_id, payload = _batch_parts(command)
        if style_key not in grouped:
            grouped[style_key] = (primitive, [], [])
        _primitive, ids, instances = grouped[style_key]
        ids.append(item_id)
        instances.append(payload)
    return tuple(
        OpenGLBatch(
            primitive=primitive,
            style_key=style_key,
            ids=tuple(ids),
            instances=tuple(instances),
        )
        for style_key, (primitive, ids, instances) in grouped.items()
    )


def _command_sort_key(command: DrawCommand) -> tuple[int, StyleKey, str]:
    primitive, style_key, item_id, _payload = _batch_parts(command)
    if isinstance(command, LineCommand):
        layer = 0
    elif isinstance(command, CircleCommand) and command.entity_id.endswith(":selected"):
        layer = 2
    elif isinstance(command, CircleCommand):
        layer = 1
    else:
        layer = 3
    return (layer, style_key, item_id)


def _batch_parts(command: DrawCommand) -> tuple[Primitive, StyleKey, str, InstancePayload]:
    if isinstance(command, CircleCommand):
        return (
            "circle",
            ("circle", command.fill, command.stroke, float(command.stroke_width)),
            command.entity_id,
            (
                float(command.center[0]),
                float(command.center[1]),
                float(command.radius),
            ),
        )
    if isinstance(command, LineCommand):
        return (
            "line",
            ("line", command.color, float(command.width)),
            command.edge_id,
            (
                float(command.start[0]),
                float(command.start[1]),
                float(command.end[0]),
                float(command.end[1]),
            ),
        )
    if isinstance(command, TextCommand):
        return (
            "text",
            ("text", command.color, float(command.size), command.text),
            command.text_id,
            (
                float(command.position[0]),
                float(command.position[1]),
                command.text,
            ),
        )
    raise TypeError(f"Unsupported draw command: {type(command)!r}")


__all__ = [
    "InstancePayload",
    "OpenGLBatch",
    "Primitive",
    "StyleKey",
    "compile_opengl_batches",
]
