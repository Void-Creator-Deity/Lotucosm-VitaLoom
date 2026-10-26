# -*- coding: utf-8 -*-
"""Headless contract for selected-SR component projection Inspector data."""
from __future__ import annotations

import ast
import inspect
import json
from typing import Any

import pytest

from core.VitaLoom.inspector.sr_selected_component_projection import (
    SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID,
    build_sr_selected_component_projection_view_model,
    load_sr_selected_component_projection_view_model,
)


def _component(component_id: str = "sensor_1") -> dict[str, Any]:
    return {
        "projection_state": "runtime_snapshot_read_only_projection",
        "maps_live_components": False,
        "source": "sr_attached_runtime_entity",
        "identity_relation": "attached_projection_not_ps_component_equivalence",
        "component_id": component_id,
        "component_type": "sensor",
        "location": "attached",
        "attach_point": [1.0, 2.0],
        "connection_count": 1,
        "inspectable_properties": {"sensing_range": 16.0},
        "component_fields": {},
    }


def _projection(**overrides: Any) -> dict[str, Any]:
    projection: dict[str, Any] = {
        "schema_version": 1,
        "status": "ok",
        "scope": "runtime_snapshot_component_projection",
        "authority": "runtime_snapshot_component_projection",
        "track": "sr_play",
        "read_only": True,
        "projection_state": "runtime_snapshot_read_only_projection",
        "maps_live_components": False,
        "maps_live_runtime_snapshot_facts": True,
        "identity_relation": "attached_projection_not_ps_component_equivalence",
        "identity": {
            "track": "sr_play",
            "runtime_epoch": "sr_epoch_1",
            "scene_path": "scenes/demo.pond",
            "entity_id": "org_1",
        },
        "revision": 7,
        "component_count": 1,
        "coverage": {"sensor": 1},
        "components": [_component()],
        "do_not_claim": ["ps_component_equivalence"],
    }
    projection.update(overrides)
    return projection


def _command_result(**overrides: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "result": _projection(**overrides),
        "events": [],
        "warnings": ["authority warning"],
        "error": None,
    }


def _field_values(view_model: Any) -> dict[str, Any]:
    return {field.id: field.value for field in view_model.section.fields}


def test_ok_projection_preserves_selected_scope_authority_identity_and_components() -> None:
    view_model = build_sr_selected_component_projection_view_model(_command_result())

    assert view_model.available is True
    assert view_model.read_only is True
    assert view_model.scope == "selected_sr_runtime_entity"
    assert view_model.authority_command_id == SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID
    assert view_model.collapsed_by_default is True
    assert view_model.section.title == "WorldBridge Components (Selected SR Runtime Entity)"
    assert all(field.editable is False for field in view_model.section.fields)

    values = _field_values(view_model)
    assert values["scope"] == "selected_sr_runtime_entity"
    assert values["projection_scope"] == "runtime_snapshot_component_projection"
    assert values["authority_command"] == SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID
    assert values["status"] == "ok"
    assert values["track"] == "sr_play"
    assert values["identity"]["entity_id"] == "org_1"
    assert values["revision"] == 7
    assert values["component_count"] == 1
    assert values["coverage"] == {"sensor": 1}
    assert values["component.sensor_1"]["source"] == "sr_attached_runtime_entity"
    assert "1 attached component" in values["component_count_meaning"]
    assert "SR attachment projection; not PS Component equivalence." in view_model.warnings
    assert "authority warning" in view_model.warnings
    json.dumps(view_model.to_dict(), ensure_ascii=False, sort_keys=True, allow_nan=False)


@pytest.mark.parametrize(
    "override",
    [
        {"scope": "runtime"},
        {"track": "ps_batch"},
        {"read_only": False},
        {"projection_state": "live_objects"},
        {"maps_live_components": True},
        {"identity_relation": "unified"},
        {"maps_live_runtime_snapshot_facts": False},
    ],
)
def test_guardrail_mismatches_are_rejected(override: dict[str, Any]) -> None:
    view_model = build_sr_selected_component_projection_view_model(
        _command_result(**override)
    )

    assert view_model.available is False
    assert view_model.error is not None
    assert view_model.error["code"] == "guardrail_violation"
    assert all(field.editable is False for field in view_model.section.fields)


def test_non_json_live_and_non_finite_payloads_are_rejected() -> None:
    live = build_sr_selected_component_projection_view_model(
        _command_result(components=[object()])
    )
    non_finite = build_sr_selected_component_projection_view_model(
        _command_result(components=[{**_component(), "attach_point": [float("nan"), 2]}])
    )
    non_string_key = build_sr_selected_component_projection_view_model(
        _command_result(coverage={1: 1})
    )

    assert live.error is not None and live.error["code"] == "non_json_payload"
    assert non_finite.error is not None and non_finite.error["code"] == "non_json_payload"
    assert non_string_key.error is not None
    assert non_string_key.error["code"] == "non_json_payload"


def test_not_proven_preserves_unknown_count_instead_of_zero() -> None:
    view_model = build_sr_selected_component_projection_view_model(
        _command_result(
            status="not_proven",
            reason="component_facts_unavailable",
            maps_live_runtime_snapshot_facts=False,
            component_count=None,
            coverage={},
            components=[],
        )
    )

    assert view_model.available is True
    values = _field_values(view_model)
    assert values["status"] == "not_proven"
    assert values["reason"] == "component_facts_unavailable"
    assert values["component_count"] is None
    assert "unknown" in values["component_count_meaning"].lower()
    assert "zero" not in values["component_count_meaning"].lower()


@pytest.mark.parametrize(
    "status",
    [
        "unavailable",
        "not_running",
        "stale",
        "missing",
        "invalid_identity",
        "unsupported_track",
        "error",
    ],
)
def test_non_ok_projection_statuses_remain_explicit_read_only_states(status: str) -> None:
    view_model = build_sr_selected_component_projection_view_model(
        _command_result(
            status=status,
            reason=f"{status}_reason",
            identity=None,
            revision=None,
            maps_live_runtime_snapshot_facts=False,
            component_count=None,
            coverage={},
            components=[],
        )
    )

    assert view_model.available is True
    values = _field_values(view_model)
    assert values["status"] == status
    assert values["reason"] == f"{status}_reason"
    assert values["component_count"] is None


def test_malformed_projection_shape_is_rejected() -> None:
    bad_count = build_sr_selected_component_projection_view_model(
        _command_result(component_count=2)
    )
    duplicate = build_sr_selected_component_projection_view_model(
        _command_result(
            component_count=2,
            coverage={"sensor": 2},
            components=[_component(), _component()],
        )
    )
    bad_status = build_sr_selected_component_projection_view_model(
        _command_result(status="invented")
    )

    assert bad_count.error is not None and bad_count.error["code"] == "invalid_payload"
    assert duplicate.error is not None and duplicate.error["code"] == "invalid_payload"
    assert bad_status.error is not None and bad_status.error["code"] == "invalid_payload"


def test_command_error_becomes_safe_unavailable_view() -> None:
    view_model = build_sr_selected_component_projection_view_model(
        {
            "ok": False,
            "result": {},
            "events": [],
            "warnings": ["registry warning"],
            "error": {
                "code": "selected_projection_unavailable",
                "message": "projection unavailable",
                "details": {"live": object()},
            },
        }
    )

    assert view_model.available is False
    assert view_model.error == {
        "code": "selected_projection_unavailable",
        "message": "projection unavailable",
    }
    assert view_model.warnings == ("registry warning",)
    assert _field_values(view_model)["availability"] == "unavailable"
    json.dumps(view_model.to_dict(), ensure_ascii=False, sort_keys=True)


class _RecordingRegistry:
    def __init__(self, result: dict[str, Any] | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def run(self, command_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((command_id, payload))
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def test_loader_runs_only_selected_projection_authority_once() -> None:
    registry = _RecordingRegistry(_command_result())

    view_model = load_sr_selected_component_projection_view_model(registry=registry)

    assert registry.calls == [(SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID, {})]
    assert view_model.available is True


def test_loader_isolates_registry_exception() -> None:
    registry = _RecordingRegistry(error=RuntimeError("registry unavailable"))

    view_model = load_sr_selected_component_projection_view_model(registry=registry)

    assert registry.calls == [(SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID, {})]
    assert view_model.available is False
    assert view_model.error == {
        "code": "command_runner_error",
        "message": "registry unavailable",
    }


def test_view_model_copy_isolates_command_payload() -> None:
    command_result = _command_result()
    view_model = build_sr_selected_component_projection_view_model(command_result)

    command_result["result"]["identity"]["entity_id"] = "mutated"
    command_result["result"]["components"][0]["component_id"] = "mutated"
    command_result["warnings"].append("mutated")

    values = _field_values(view_model)
    assert values["identity"]["entity_id"] == "org_1"
    assert values["component.sensor_1"]["component_id"] == "sensor_1"
    assert "mutated" not in view_model.warnings


def test_adapter_module_stays_qt_free_and_behind_command_seam() -> None:
    import core.VitaLoom.inspector.sr_selected_component_projection as module

    tree = ast.parse(inspect.getsource(module))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    forbidden_prefixes = (
        "PyQt6",
        "core.Lotucosm.runtime.runtime_snapshot_component_projection",
        "core.VitaLoom.simulation.sr_selected_identity_host",
        "core.VitaLoom.inspector.command_binding",
        "core.VitaLoom.docks.inspector",
    )
    assert not any(name.startswith(forbidden_prefixes) for name in imported_modules)


def test_default_loader_reaches_headless_selected_projection_authority() -> None:
    view_model = load_sr_selected_component_projection_view_model()

    assert view_model.available is True
    values = _field_values(view_model)
    assert values["scope"] == "selected_sr_runtime_entity"
    assert values["track"] == "sr_play"
    assert values["status"] == "unavailable"
    assert values["component_count"] is None
    assert values["maps_live_runtime_snapshot_facts"] is False
