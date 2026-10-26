# -*- coding: utf-8 -*-
"""Convert inspector field edits into shared command-layer payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from core.VitaLoom.inspector.schema import InspectorField


@dataclass(frozen=True)
class InspectorCommandBindingResult:
    ok: bool
    command_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    error: dict[str, str] | None = None


def bind_inspector_edit(
    field: InspectorField,
    *,
    new_value: Any,
    entity: Any,
    scene_path: str,
    entity_id: str,
) -> InspectorCommandBindingResult:
    if not field.editable:
        return _error("readonly_field", f"Field is read-only: {field.id}")

    validation_error = _validate_value(field, new_value)
    if validation_error is not None:
        return validation_error

    source_path = tuple(field.source_path or (field.id,))
    if _is_position_axis(source_path):
        position = _read_position(entity)
        if position is None:
            return _error("missing_position", "Entity has no editable position")
        position[int(source_path[1])] = new_value
        return _ok(
            "transform.set",
            {
                "scene_path": scene_path,
                "entity_id": entity_id,
                "position": position,
            },
        )

    if len(source_path) >= 3 and source_path[0] == "scripts":
        return _ok(
            "script.set_property",
            {
                "scene_path": scene_path,
                "entity_id": entity_id,
                "script": str(source_path[1]),
                "property_path": _property_path(source_path[2:]),
                "value": new_value,
            },
        )

    return _ok(
        "entity.set_property",
        {
            "scene_path": scene_path,
            "entity_id": entity_id,
            "property_path": _property_path(source_path),
            "value": new_value,
        },
    )


def _validate_value(
    field: InspectorField,
    value: Any,
) -> InspectorCommandBindingResult | None:
    validation = field.validation or {}
    if "min" in validation:
        try:
            if float(value) < float(validation["min"]):
                return _error(
                    "validation_failed",
                    f"{field.id} must be >= {validation['min']}",
                )
        except (TypeError, ValueError):
            return _error("validation_failed", f"{field.id} must be numeric")
    if "max" in validation:
        try:
            if float(value) > float(validation["max"]):
                return _error(
                    "validation_failed",
                    f"{field.id} must be <= {validation['max']}",
                )
        except (TypeError, ValueError):
            return _error("validation_failed", f"{field.id} must be numeric")
    return None


def _is_position_axis(source_path: tuple[str | int, ...]) -> bool:
    return (
        len(source_path) == 2
        and source_path[0] == "position"
        and source_path[1] in (0, 1)
    )


def _read_position(entity: Any) -> list[Any] | None:
    if isinstance(entity, Mapping):
        raw = entity.get("position")
    else:
        raw = getattr(entity, "position", None)
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None
    return [raw[0], raw[1]]


def _property_path(parts: tuple[str | int, ...]) -> str:
    return ".".join(str(part) for part in parts)


def _ok(command_id: str, payload: dict[str, Any]) -> InspectorCommandBindingResult:
    return InspectorCommandBindingResult(ok=True, command_id=command_id, payload=payload)


def _error(code: str, message: str) -> InspectorCommandBindingResult:
    return InspectorCommandBindingResult(ok=False, error={"code": code, "message": message})


__all__ = ["InspectorCommandBindingResult", "bind_inspector_edit"]

