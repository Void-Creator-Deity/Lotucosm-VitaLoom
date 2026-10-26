# -*- coding: utf-8 -*-
from __future__ import annotations

from core.VitaLoom.inspector.schema import InspectorField


def test_position_field_edit_builds_transform_command_payload() -> None:
    from core.VitaLoom.inspector.command_binding import bind_inspector_edit

    entity = {"id": "hero", "position": [1.0, 2.0]}
    field = InspectorField(
        id="position_x",
        label="X",
        type="float",
        value=1.0,
        source_path=("position", 0),
    )

    result = bind_inspector_edit(
        field,
        new_value=7.5,
        entity=entity,
        scene_path="workspace/projects/demo/scenes/main.pond",
        entity_id="hero",
    )

    assert result.ok is True
    assert result.command_id == "transform.set"
    assert result.payload == {
        "scene_path": "workspace/projects/demo/scenes/main.pond",
        "entity_id": "hero",
        "position": [7.5, 2.0],
    }


def test_script_field_edit_builds_script_property_command_payload() -> None:
    from core.VitaLoom.inspector.command_binding import bind_inspector_edit

    field = InspectorField(
        id="script_brain_mind.level",
        label="level",
        type="int",
        value=1,
        source_path=("scripts", "brain", "mind.level"),
    )

    result = bind_inspector_edit(
        field,
        new_value=3,
        entity={"id": "hero"},
        scene_path="workspace/projects/demo/scenes/main.pond",
        entity_id="hero",
    )

    assert result.ok is True
    assert result.command_id == "script.set_property"
    assert result.payload == {
        "scene_path": "workspace/projects/demo/scenes/main.pond",
        "entity_id": "hero",
        "script": "brain",
        "property_path": "mind.level",
        "value": 3,
    }


def test_generic_field_edit_builds_entity_property_command_payload() -> None:
    from core.VitaLoom.inspector.command_binding import bind_inspector_edit

    field = InspectorField(
        id="energy",
        label="Energy",
        type="float",
        value=10.0,
        source_path=("energy",),
    )

    result = bind_inspector_edit(
        field,
        new_value=12.0,
        entity={"id": "hero"},
        scene_path="workspace/projects/demo/scenes/main.pond",
        entity_id="hero",
    )

    assert result.ok is True
    assert result.command_id == "entity.set_property"
    assert result.payload["property_path"] == "energy"
    assert result.payload["value"] == 12.0


def test_binding_rejects_readonly_or_invalid_field_edits() -> None:
    from core.VitaLoom.inspector.command_binding import bind_inspector_edit

    readonly = InspectorField(
        id="id",
        label="ID",
        type="string",
        value="hero",
        editable=False,
        source_path=("id",),
    )
    bounded = InspectorField(
        id="stress",
        label="Stress",
        type="float",
        value=0.5,
        validation={"min": 0.0, "max": 1.0},
        source_path=("stress",),
    )

    readonly_result = bind_inspector_edit(
        readonly,
        new_value="other",
        entity={"id": "hero"},
        scene_path="workspace/projects/demo/scenes/main.pond",
        entity_id="hero",
    )
    bounded_result = bind_inspector_edit(
        bounded,
        new_value=2.0,
        entity={"id": "hero"},
        scene_path="workspace/projects/demo/scenes/main.pond",
        entity_id="hero",
    )

    assert readonly_result.ok is False
    assert readonly_result.error == {"code": "readonly_field", "message": "Field is read-only: id"}
    assert bounded_result.ok is False
    assert bounded_result.error == {
        "code": "validation_failed",
        "message": "stress must be <= 1.0",
    }

