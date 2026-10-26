# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect


class _Component:
    inspector_fields = [
        {
            "id": "stress",
            "label": "Stress",
            "type": "float",
            "value": 0.35,
            "editable": False,
            "source_path": ("components", "brain", "stress"),
            "validation": {"min": 0.0, "max": 1.0},
        }
    ]


class _EntityWithComponents:
    id = "organism_1"
    entity_type = "organism"
    position = (10.0, 20.0)
    components = {"brain": _Component()}


def test_inspector_schema_uses_component_metadata_fields() -> None:
    from core.VitaLoom.inspector.schema import build_inspector_sections

    sections = build_inspector_sections(_EntityWithComponents())

    component_section = next(section for section in sections if section.id == "component:brain")
    field = component_section.fields[0]

    assert field.id == "stress"
    assert field.label == "Stress"
    assert field.type == "float"
    assert field.value == 0.35
    assert field.editable is False
    assert field.source_path == ("components", "brain", "stress")
    assert field.validation == {"min": 0.0, "max": 1.0}


def test_inspector_schema_falls_back_to_safe_primitive_entity_fields() -> None:
    from core.VitaLoom.inspector.schema import build_inspector_sections

    entity = {
        "id": "hero",
        "type": "organism",
        "position": [1.5, 2.5],
        "energy": 42.0,
        "scripts": [{"name": "brain"}],
    }

    sections = build_inspector_sections(entity)

    general = next(section for section in sections if section.id == "general")
    transform = next(section for section in sections if section.id == "transform")
    fields = {field.id: field for section in sections for field in section.fields}

    assert [field.id for field in general.fields] == ["id", "type"]
    assert general.fields[0].editable is False
    assert fields["id"].value == "hero"
    assert fields["type"].value == "organism"
    assert fields["position_x"].value == 1.5
    assert fields["position_x"].source_path == ("position", 0)
    assert fields["position_y"].value == 2.5
    assert fields["energy"].value == 42.0
    assert all(field.id != "scripts" for field in general.fields)
    assert transform.title == "Transform"


def test_inspector_schema_module_has_no_qt_widget_dependency() -> None:
    from core.VitaLoom.inspector import schema

    source = inspect.getsource(schema)

    assert "PyQt6" not in source
    assert "QWidget" not in source
    assert "QLineEdit" not in source

