# -*- coding: utf-8 -*-
"""Qt-free Adapter for command-backed WorldBridge Inspector diagnostics.

The Command Registry result is the only authority accepted by this Module.  It
turns runtime-wide, summary-only evidence into deterministic read-only
Inspector data without importing projection Implementation or edit bindings.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from core.VitaLoom.inspector.schema import InspectorField, InspectorSection


WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID = (
    "runtime.worldbridge.component_projection_diagnostics"
)
WORLD_BRIDGE_DIAGNOSTICS_SCOPE = "runtime"


@dataclass(frozen=True)
class WorldBridgeDiagnosticsViewModel:
    """Read-only presentation state for runtime-wide projection evidence."""

    available: bool
    section: InspectorSection
    error: dict[str, str] | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True
    scope: str = WORLD_BRIDGE_DIAGNOSTICS_SCOPE
    authority_command_id: str = WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID
    collapsed_by_default: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-safe representation for tests/adapters."""
        return {
            "available": self.available,
            "read_only": self.read_only,
            "scope": self.scope,
            "authority_command_id": self.authority_command_id,
            "collapsed_by_default": self.collapsed_by_default,
            "warnings": list(self.warnings),
            "error": dict(self.error) if self.error is not None else None,
            "section": {
                "id": self.section.id,
                "title": self.section.title,
                "fields": [
                    {
                        "id": item.id,
                        "label": item.label,
                        "type": item.type,
                        "value": item.value,
                        "editable": item.editable,
                        "source_path": list(item.source_path),
                        "validation": dict(item.validation),
                    }
                    for item in self.section.fields
                ],
            },
        }


def build_worldbridge_diagnostics_view_model(
    command_result: Mapping[str, Any] | Any,
) -> WorldBridgeDiagnosticsViewModel:
    """Validate one Command Registry-shaped result and build Inspector data."""
    if not isinstance(command_result, Mapping):
        return _unavailable(
            "invalid_command_result",
            "Diagnostics command result must be a mapping",
        )

    warnings = _safe_warnings(command_result.get("warnings"))
    ok = command_result.get("ok")
    if ok is not True:
        if ok is False:
            return _command_error_view(command_result.get("error"), warnings)
        return _unavailable(
            "invalid_command_result",
            "Diagnostics command result must contain boolean ok",
            warnings=warnings,
        )

    result = command_result.get("result")
    if not isinstance(result, Mapping):
        return _unavailable(
            "invalid_payload",
            "Diagnostics result must be a mapping",
            warnings=warnings,
        )
    if "components" in result:
        return _unavailable(
            "unsafe_components_payload",
            "Diagnostics payload must not contain component objects",
            warnings=warnings,
        )
    if not _is_json_value(result):
        return _unavailable(
            "non_json_payload",
            "Diagnostics payload must contain JSON values only",
            warnings=warnings,
        )

    guardrail_error = _guardrail_error(result)
    if guardrail_error is not None:
        return _unavailable(
            "guardrail_violation",
            guardrail_error,
            warnings=warnings,
        )

    normalized, validation_error = _normalize_diagnostics(result)
    if validation_error is not None:
        return _unavailable(
            "invalid_payload",
            validation_error,
            warnings=warnings,
        )

    component_count = normalized["component_count"]
    count_meaning = (
        "No components in current runtime projection evidence."
        if component_count == 0
        else f"{component_count} components in current runtime projection evidence."
    )
    fields = (
        _field("scope", "Scope", WORLD_BRIDGE_DIAGNOSTICS_SCOPE),
        _field(
            "authority_command",
            "Authority Command",
            WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID,
        ),
        _field("status", "Status", normalized["status"]),
        _field("diagnostic_state", "Diagnostic State", normalized["diagnostic_state"]),
        _field("read_only", "Read Only", normalized["read_only"], "bool"),
        _field(
            "maps_live_components",
            "Maps Live Components",
            normalized["maps_live_components"],
            "bool",
        ),
        _field("default_ready", "Default Ready", normalized["default_ready"], "bool"),
        _field("component_count", "Component Count", component_count, "int"),
        _field("component_count_meaning", "Count Meaning", count_meaning),
        _field("coverage", "Coverage", normalized["coverage"], "json"),
        _field(
            "safe_projection_fields",
            "Safe Projection Fields",
            normalized["safe_projection_fields"],
            "json",
        ),
        _field(
            "forbidden_behavior",
            "Forbidden Behavior",
            normalized["forbidden_behavior"],
            "json",
        ),
        _field("do_not_claim", "Do Not Claim", normalized["do_not_claim"], "json"),
    )
    return WorldBridgeDiagnosticsViewModel(
        available=True,
        section=InspectorSection(
            id="worldbridge-runtime-diagnostics",
            title="WorldBridge Diagnostics (Runtime-wide)",
            fields=fields,
        ),
        warnings=warnings,
    )


def load_worldbridge_diagnostics_view_model(
    *,
    registry: Any | None = None,
) -> WorldBridgeDiagnosticsViewModel:
    """Run the authority command exactly once and isolate registry failures."""
    if registry is None:
        from core.VitaLoom.commands.registry import get_command_registry

        registry = get_command_registry()
    try:
        command_result = registry.run(WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID, {})
    except Exception as exc:
        return _unavailable(
            "command_runner_error",
            _exception_message(exc),
        )
    return build_worldbridge_diagnostics_view_model(command_result)


def _field(field_id: str, label: str, value: Any, field_type: str = "string") -> InspectorField:
    return InspectorField(
        id=field_id,
        label=label,
        type=field_type,
        value=value,
        editable=False,
        source_path=(),
    )


def _unavailable(
    code: str,
    message: str,
    *,
    warnings: tuple[str, ...] = (),
) -> WorldBridgeDiagnosticsViewModel:
    safe_code = code if isinstance(code, str) and code else "diagnostics_unavailable"
    safe_message = message if isinstance(message, str) and message else "Diagnostics unavailable"
    return WorldBridgeDiagnosticsViewModel(
        available=False,
        section=InspectorSection(
            id="worldbridge-runtime-diagnostics",
            title="WorldBridge Diagnostics (Runtime-wide)",
            fields=(
                _field("scope", "Scope", WORLD_BRIDGE_DIAGNOSTICS_SCOPE),
                _field(
                    "authority_command",
                    "Authority Command",
                    WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID,
                ),
                _field("availability", "Availability", "unavailable"),
                _field("error_code", "Error Code", safe_code),
                _field("error_message", "Error Message", safe_message),
            ),
        ),
        error={"code": safe_code, "message": safe_message},
        warnings=warnings,
    )


def _command_error_view(
    raw_error: Any,
    warnings: tuple[str, ...],
) -> WorldBridgeDiagnosticsViewModel:
    if isinstance(raw_error, Mapping):
        code = raw_error.get("code")
        message = raw_error.get("message")
    else:
        code = None
        message = None
    return _unavailable(
        code if isinstance(code, str) and code else "diagnostics_unavailable",
        message if isinstance(message, str) and message else "Diagnostics unavailable",
        warnings=warnings,
    )


def _guardrail_error(result: Mapping[str, Any]) -> str | None:
    expected = {
        "read_only": True,
        "maps_live_components": False,
        "default_ready": False,
    }
    for key, expected_value in expected.items():
        if result.get(key) is not expected_value:
            return f"{key} must be {expected_value!r} for Inspector diagnostics"
    return None


def _normalize_diagnostics(
    result: Mapping[str, Any],
) -> tuple[dict[str, Any], str | None]:
    status = result.get("status")
    diagnostic_state = result.get("diagnostic_state")
    component_count = result.get("component_count")
    coverage = result.get("coverage")

    if not isinstance(status, str) or not status:
        return {}, "status must be a non-empty string"
    if not isinstance(diagnostic_state, str) or not diagnostic_state:
        return {}, "diagnostic_state must be a non-empty string"
    if isinstance(component_count, bool) or not isinstance(component_count, int) or component_count < 0:
        return {}, "component_count must be a non-negative integer"
    if not isinstance(coverage, Mapping):
        return {}, "coverage must be a mapping"
    normalized_coverage: dict[str, int] = {}
    for key, value in coverage.items():
        if not isinstance(key, str):
            return {}, "coverage keys must be strings"
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return {}, "coverage values must be non-negative integers"
        normalized_coverage[key] = value

    list_fields: dict[str, list[str]] = {}
    for key in ("safe_projection_fields", "forbidden_behavior", "do_not_claim"):
        value = result.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return {}, f"{key} must be a list of strings"
        list_fields[key] = list(value)

    normalized = {
        "status": status,
        "diagnostic_state": diagnostic_state,
        "read_only": True,
        "maps_live_components": False,
        "default_ready": False,
        "component_count": component_count,
        "coverage": dict(normalized_coverage),
        **list_fields,
    }
    return normalized, None


def _safe_warnings(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(item for item in raw if isinstance(item, str))


def _is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _is_json_value(item)
            for key, item in value.items()
        )
    return False


def _exception_message(exc: Exception) -> str:
    text = str(exc).strip()
    return text or exc.__class__.__name__


__all__ = [
    "WORLD_BRIDGE_DIAGNOSTICS_COMMAND_ID",
    "WORLD_BRIDGE_DIAGNOSTICS_SCOPE",
    "WorldBridgeDiagnosticsViewModel",
    "build_worldbridge_diagnostics_view_model",
    "load_worldbridge_diagnostics_view_model",
]
