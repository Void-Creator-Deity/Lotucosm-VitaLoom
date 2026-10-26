# -*- coding: utf-8 -*-
"""Schema-derived inspector field models with no UI dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


SourcePath = tuple[str | int, ...]


@dataclass(frozen=True)
class InspectorField:
    id: str
    label: str
    type: str
    value: Any
    editable: bool = True
    source_path: SourcePath = field(default_factory=tuple)
    validation: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InspectorSection:
    id: str
    title: str
    fields: tuple[InspectorField, ...] = field(default_factory=tuple)


def build_inspector_sections(entity: Any) -> tuple[InspectorSection, ...]:
    sections: list[InspectorSection] = []

    general_fields = _build_general_fields(entity)
    if general_fields:
        sections.append(InspectorSection("general", "General", tuple(general_fields)))

    transform_fields = _build_transform_fields(entity)
    if transform_fields:
        sections.append(InspectorSection("transform", "Transform", tuple(transform_fields)))

    primitive_fields = _build_safe_primitive_fields(entity)
    if primitive_fields:
        sections.append(InspectorSection("properties", "Properties", tuple(primitive_fields)))

    sections.extend(_build_component_sections(entity))
    return tuple(sections)


def _build_general_fields(entity: Any) -> list[InspectorField]:
    fields: list[InspectorField] = []
    entity_id = _read_value(entity, "id")
    entity_type = _read_value(entity, "type", default=_read_value(entity, "entity_type"))
    if entity_id is not None:
        fields.append(
            InspectorField(
                id="id",
                label="ID",
                type=_infer_field_type(entity_id),
                value=entity_id,
                editable=False,
                source_path=("id",),
            )
        )
    if entity_type is not None:
        fields.append(
            InspectorField(
                id="type",
                label="Type",
                type=_infer_field_type(entity_type),
                value=entity_type,
                editable=False,
                source_path=("type",),
            )
        )
    return fields


def _build_transform_fields(entity: Any) -> list[InspectorField]:
    position = _read_value(entity, "position")
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        return []
    return [
        InspectorField(
            id="position_x",
            label="X",
            type="float",
            value=position[0],
            source_path=("position", 0),
        ),
        InspectorField(
            id="position_y",
            label="Y",
            type="float",
            value=position[1],
            source_path=("position", 1),
        ),
    ]


def _build_safe_primitive_fields(entity: Any) -> list[InspectorField]:
    fields: list[InspectorField] = []
    for key, value in _iter_entity_items(entity):
        if key in {"id", "type", "entity_type", "position", "components", "scripts"}:
            continue
        if not _is_safe_primitive(value):
            continue
        fields.append(
            InspectorField(
                id=str(key),
                label=_label_from_id(str(key)),
                type=_infer_field_type(value),
                value=value,
                editable=True,
                source_path=(str(key),),
            )
        )
    return fields


def _build_component_sections(entity: Any) -> list[InspectorSection]:
    components = _read_value(entity, "components")
    if not isinstance(components, dict):
        return []
    sections: list[InspectorSection] = []
    for component_name, component in components.items():
        fields = tuple(_build_component_fields(str(component_name), component))
        if fields:
            sections.append(
                InspectorSection(
                    id=f"component:{component_name}",
                    title=f"Component: {component_name}",
                    fields=fields,
                )
            )
    return sections


def _build_component_fields(component_name: str, component: Any) -> Iterable[InspectorField]:
    raw_fields = _read_value(component, "inspector_fields")
    if not isinstance(raw_fields, (list, tuple)):
        return ()
    fields: list[InspectorField] = []
    for raw in raw_fields:
        if not isinstance(raw, dict):
            continue
        field_id = str(raw.get("id", "")).strip()
        if not field_id:
            continue
        source_path = raw.get("source_path", ("components", component_name, field_id))
        fields.append(
            InspectorField(
                id=field_id,
                label=str(raw.get("label") or _label_from_id(field_id)),
                type=str(raw.get("type") or _infer_field_type(raw.get("value"))),
                value=raw.get("value"),
                editable=bool(raw.get("editable", True)),
                source_path=tuple(source_path) if isinstance(source_path, (list, tuple)) else (str(source_path),),
                validation=dict(raw.get("validation") or {}),
            )
        )
    return fields


def _read_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _iter_entity_items(entity: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(entity, dict):
        return entity.items()
    return (
        (key, value)
        for key, value in vars(entity).items()
        if not key.startswith("_")
    )


def _is_safe_primitive(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _infer_field_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "none"
    return "string"


def _label_from_id(field_id: str) -> str:
    return field_id.replace("_", " ").strip().title() or field_id


__all__ = [
    "InspectorField",
    "InspectorSection",
    "SourcePath",
    "build_inspector_sections",
]

