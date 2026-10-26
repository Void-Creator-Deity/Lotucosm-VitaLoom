# -*- coding: utf-8 -*-
"""Headless contract for command-backed WorldBridge Inspector diagnostics."""
from __future__ import annotations

import json
from typing import Any

import pytest

from core.VitaLoom.inspector.worldbridge_diagnostics import (
    WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID,
    build_worldbridge_diagnostics_view_model,
    load_worldbridge_diagnostics_view_model,
)


def _command_result(**diagnostic_overrides: Any) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "schema_version": 1,
        "status": "worldbridge_component_projection_diagnostics",
        "diagnostic_state": "read_only_projection_diagnostics",
        "read_only": True,
        "maps_live_components": False,
        "default_ready": False,
        "component_count": 0,
        "coverage": {"membrane": 0},
        "safe_projection_fields": ["component_id", "component_type"],
        "forbidden_behavior": ["auto_ingest", "behavior_calls"],
        "do_not_claim": [
            "live_component_graph_mapping",
            "unified_pond_default_ready",
        ],
    }
    diagnostics.update(diagnostic_overrides)
    return {
        "ok": True,
        "result": diagnostics,
        "events": [],
        "warnings": ["runtime evidence only"],
        "error": None,
    }


def _field_values(view_model: Any) -> dict[str, Any]:
    return {field.id: field.value for field in view_model.section.fields}


def test_view_model_preserves_runtime_scope_authority_and_guardrails() -> None:
    view_model = build_worldbridge_diagnostics_view_model(_command_result())

    assert view_model.available is True
    assert view_model.read_only is True
    assert view_model.scope == "runtime"
    assert view_model.authority_command_id == WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID
    assert view_model.collapsed_by_default is True
    assert all(field.editable is False for field in view_model.section.fields)

    values = _field_values(view_model)
    assert values["scope"] == "runtime"
    assert values["authority_command"] == WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID
    assert values["read_only"] is True
    assert values["maps_live_components"] is False
    assert values["default_ready"] is False
    assert values["component_count"] == 0
    assert values["coverage"] == {"membrane": 0}
    assert values["safe_projection_fields"] == ["component_id", "component_type"]
    assert values["forbidden_behavior"] == ["auto_ingest", "behavior_calls"]
    assert values["do_not_claim"] == [
        "live_component_graph_mapping",
        "unified_pond_default_ready",
    ]
    assert "current runtime projection evidence" in values["component_count_meaning"].lower()
    assert "selected entity" not in values["component_count_meaning"].lower()
    assert view_model.warnings == ("runtime evidence only",)
    json.dumps(view_model.to_dict(), ensure_ascii=False, sort_keys=True)


@pytest.mark.parametrize(
    ("override", "expected_fragment"),
    [
        ({"read_only": False}, "read_only"),
        ({"maps_live_components": True}, "maps_live_components"),
        ({"default_ready": True}, "default_ready"),
    ],
)
def test_view_model_rejects_guardrail_mismatches(
    override: dict[str, Any],
    expected_fragment: str,
) -> None:
    view_model = build_worldbridge_diagnostics_view_model(_command_result(**override))

    assert view_model.available is False
    assert view_model.read_only is True
    assert view_model.error is not None
    assert view_model.error["code"] == "guardrail_violation"
    assert expected_fragment in view_model.error["message"]
    assert all(field.editable is False for field in view_model.section.fields)


def test_view_model_rejects_component_list_and_live_values() -> None:
    components_view = build_worldbridge_diagnostics_view_model(
        _command_result(components=[])
    )
    live_value_view = build_worldbridge_diagnostics_view_model(
        _command_result(coverage={"membrane": object()})
    )

    assert components_view.available is False
    assert components_view.error == {
        "code": "unsafe_components_payload",
        "message": "Diagnostics payload must not contain component objects",
    }
    assert live_value_view.available is False
    assert live_value_view.error is not None
    assert live_value_view.error["code"] == "non_json_payload"
    json.dumps(components_view.to_dict(), ensure_ascii=False, sort_keys=True)
    json.dumps(live_value_view.to_dict(), ensure_ascii=False, sort_keys=True)


def test_command_error_becomes_safe_read_only_unavailable_state() -> None:
    view_model = build_worldbridge_diagnostics_view_model(
        {
            "ok": False,
            "result": {},
            "events": [],
            "warnings": ["registry warning"],
            "error": {
                "code": "diagnostics_unavailable",
                "message": "projection evidence unavailable",
                "details": {"unsafe": object()},
            },
        }
    )

    assert view_model.available is False
    assert view_model.read_only is True
    assert view_model.scope == "runtime"
    assert view_model.error == {
        "code": "diagnostics_unavailable",
        "message": "projection evidence unavailable",
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


def test_runner_invokes_only_authority_command_once_with_empty_payload() -> None:
    registry = _RecordingRegistry(_command_result(component_count=2))

    view_model = load_worldbridge_diagnostics_view_model(registry=registry)

    assert registry.calls == [(WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID, {})]
    assert view_model.available is True
    assert _field_values(view_model)["component_count"] == 2


def test_runner_isolates_registry_exceptions() -> None:
    registry = _RecordingRegistry(error=RuntimeError("registry unavailable"))

    view_model = load_worldbridge_diagnostics_view_model(registry=registry)

    assert registry.calls == [(WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID, {})]
    assert view_model.available is False
    assert view_model.error == {
        "code": "command_runner_error",
        "message": "registry unavailable",
    }


def test_adapter_module_has_no_projection_or_edit_binding_imports() -> None:
    import ast
    import inspect
    import core.VitaLoom.inspector.worldbridge_diagnostics as diagnostics_module

    tree = ast.parse(inspect.getsource(diagnostics_module))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    assert not any(
        name.startswith("core.Lotucosm.runtime.world_bridge_component_projection")
        for name in imported_modules
    )
    assert "core.VitaLoom.inspector.command_binding" not in imported_modules


def test_default_runner_reaches_headless_command_registry_authority() -> None:
    view_model = load_worldbridge_diagnostics_view_model()

    assert view_model.available is True
    values = _field_values(view_model)
    assert values["scope"] == "runtime"
    assert values["read_only"] is True
    assert values["maps_live_components"] is False
    assert values["default_ready"] is False
