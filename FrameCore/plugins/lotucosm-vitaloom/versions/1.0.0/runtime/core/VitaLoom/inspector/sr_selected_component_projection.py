# -*- coding: utf-8 -*-
"""Qt-free Adapter for selected-SR runtime component projection Inspector data.

The Command Registry result is the only Authority Interface accepted by this
Module. It validates and copy-isolates strict JSON projection envelopes, then
builds deterministic read-only presentation data without importing PyQt, live
runtime objects, projection Implementation, selected identity Host, or edit
bindings.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from core.VitaLoom.inspector.schema import InspectorField, InspectorSection


SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID = (
    "runtime.sr.selected_entity_component_projection"
)
SR_SELECTED_COMPONENT_PROJECTION_SCOPE = "selected_sr_runtime_entity"
_RUNTIME_PROJECTION_SCOPE = "runtime_snapshot_component_projection"
_RUNTIME_PROJECTION_AUTHORITY = "runtime_snapshot_component_projection"
_SR_TRACK = "sr_play"
_PROJECTION_STATE = "runtime_snapshot_read_only_projection"
_IDENTITY_RELATION = "attached_projection_not_ps_component_equivalence"
_COMPONENT_SOURCE = "sr_attached_runtime_entity"
_EQUIVALENCE_WARNING = (
    "SR attachment projection; not PS Component equivalence."
)
_ALLOWED_STATUSES = {
    "ok",
    "not_proven",
    "unavailable",
    "not_running",
    "stale",
    "missing",
    "invalid_identity",
    "unsupported_track",
    "error",
}


@dataclass(frozen=True)
class SrSelectedComponentProjectionViewModel:
    """Read-only presentation state for one selected SR runtime entity."""

    available: bool
    section: InspectorSection
    error: dict[str, str] | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True
    scope: str = SR_SELECTED_COMPONENT_PROJECTION_SCOPE
    authority_command_id: str = SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID
    collapsed_by_default: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic copy-isolated JSON representation."""
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
                        "value": _json_copy(item.value),
                        "editable": item.editable,
                        "source_path": list(item.source_path),
                        "validation": _json_copy(dict(item.validation)),
                    }
                    for item in self.section.fields
                ],
            },
        }


def build_sr_selected_component_projection_view_model(
    command_result: Mapping[str, Any] | Any,
) -> SrSelectedComponentProjectionViewModel:
    """Validate one Command Registry-shaped result and build Inspector data."""
    if not isinstance(command_result, Mapping):
        return _unavailable(
            "invalid_command_result",
            "Selected SR projection command result must be a mapping",
        )

    warnings = _safe_warnings(command_result.get("warnings"))
    ok = command_result.get("ok")
    if ok is not True:
        if ok is False:
            return _command_error_view(command_result.get("error"), warnings)
        return _unavailable(
            "invalid_command_result",
            "Selected SR projection command result must contain boolean ok",
            warnings=warnings,
        )

    result = command_result.get("result")
    if not isinstance(result, Mapping):
        return _unavailable(
            "invalid_payload",
            "Selected SR projection result must be a mapping",
            warnings=warnings,
        )
    if not _is_json_value(result):
        return _unavailable(
            "non_json_payload",
            "Selected SR projection payload must contain JSON values only",
            warnings=warnings,
        )

    guardrail_error = _guardrail_error(result)
    if guardrail_error is not None:
        return _unavailable(
            "guardrail_violation",
            guardrail_error,
            warnings=warnings,
        )

    normalized, validation_error = _normalize_projection(result)
    if validation_error is not None:
        return _unavailable(
            "invalid_payload",
            validation_error,
            warnings=warnings,
        )

    status = normalized["status"]
    component_count = normalized["component_count"]
    fields: list[InspectorField] = [
        _field("scope", "Scope", SR_SELECTED_COMPONENT_PROJECTION_SCOPE),
        _field(
            "authority_command",
            "Authority Command",
            SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID,
        ),
        _field(
            "projection_scope",
            "Projection Scope",
            normalized["projection_scope"],
        ),
        _field("status", "Status", status),
    ]
    if normalized["reason"] is not None:
        fields.append(_field("reason", "Reason", normalized["reason"]))
    fields.extend(
        [
            _field("track", "Track", normalized["track"]),
            _field(
                "projection_state",
                "Projection State",
                normalized["projection_state"],
            ),
            _field(
                "identity_relation",
                "Identity Relation",
                normalized["identity_relation"],
            ),
            _field("identity", "Identity", normalized["identity"], "json"),
            _field("revision", "Revision", normalized["revision"], "int"),
            _field(
                "maps_live_components",
                "Maps Live Components",
                False,
                "bool",
            ),
            _field(
                "maps_live_runtime_snapshot_facts",
                "Maps Runtime Snapshot Facts",
                normalized["maps_live_runtime_snapshot_facts"],
                "bool",
            ),
            _field(
                "component_count",
                "Component Count",
                component_count,
                "int",
            ),
            _field(
                "component_count_meaning",
                "Count Meaning",
                _count_meaning(status, component_count),
            ),
            _field("coverage", "Coverage", normalized["coverage"], "json"),
        ]
    )
    for component in normalized["components"]:
        component_id = component["component_id"]
        fields.append(
            _field(
                f"component.{component_id}",
                f"Component: {component_id}",
                component,
                "json",
            )
        )
    fields.append(
        _field("do_not_claim", "Do Not Claim", normalized["do_not_claim"], "json")
    )

    presentation_warnings = _dedupe_warnings(
        (_EQUIVALENCE_WARNING, *warnings)
    )
    return SrSelectedComponentProjectionViewModel(
        available=True,
        section=InspectorSection(
            id="worldbridge-sr-selected-component-projection",
            title="WorldBridge Components (Selected SR Runtime Entity)",
            fields=tuple(fields),
        ),
        warnings=presentation_warnings,
    )


def load_sr_selected_component_projection_view_model(
    *,
    registry: Any | None = None,
) -> SrSelectedComponentProjectionViewModel:
    """Run the selected-SR Authority command exactly once."""
    if registry is None:
        from core.VitaLoom.commands.registry import get_command_registry

        registry = get_command_registry()
    try:
        command_result = registry.run(
            SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID,
            {},
        )
    except Exception as exc:
        return _unavailable(
            "command_runner_error",
            _exception_message(exc),
        )
    return build_sr_selected_component_projection_view_model(command_result)


def _guardrail_error(result: Mapping[str, Any]) -> str | None:
    expected = {
        "scope": _RUNTIME_PROJECTION_SCOPE,
        "authority": _RUNTIME_PROJECTION_AUTHORITY,
        "track": _SR_TRACK,
        "read_only": True,
        "projection_state": _PROJECTION_STATE,
        "maps_live_components": False,
        "identity_relation": _IDENTITY_RELATION,
    }
    for key, expected_value in expected.items():
        if result.get(key) != expected_value:
            return f"{key} must be {expected_value!r} for selected SR projection"

    status = result.get("status")
    if status not in _ALLOWED_STATUSES:
        return None
    maps_snapshot_facts = result.get("maps_live_runtime_snapshot_facts")
    expected_maps_snapshot_facts = status == "ok"
    if maps_snapshot_facts is not expected_maps_snapshot_facts:
        return (
            "maps_live_runtime_snapshot_facts must match whether status is 'ok'"
        )
    return None


def _normalize_projection(
    result: Mapping[str, Any],
) -> tuple[dict[str, Any], str | None]:
    status = result.get("status")
    if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
        return {}, "status must be a supported selected SR projection status"

    reason = result.get("reason")
    if reason is not None and (not isinstance(reason, str) or not reason):
        return {}, "reason must be a non-empty string or null"

    identity = result.get("identity")
    if identity is not None and not isinstance(identity, Mapping):
        return {}, "identity must be a mapping or null"
    normalized_identity = _json_copy(dict(identity)) if identity is not None else None

    revision = result.get("revision")
    if revision is not None and (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
    ):
        return {}, "revision must be a non-negative integer or null"

    component_count = result.get("component_count")
    coverage = result.get("coverage")
    components = result.get("components")
    if not isinstance(coverage, Mapping):
        return {}, "coverage must be a mapping"
    normalized_coverage: dict[str, int] = {}
    for key, value in coverage.items():
        if not isinstance(key, str):
            return {}, "coverage keys must be strings"
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return {}, "coverage values must be non-negative integers"
        normalized_coverage[key] = value
    if not isinstance(components, list):
        return {}, "components must be a list"

    normalized_components: list[dict[str, Any]] = []
    component_ids: set[str] = set()
    for raw_component in components:
        normalized_component, component_error = _normalize_component(raw_component)
        if component_error is not None:
            return {}, component_error
        component_id = normalized_component["component_id"]
        if component_id in component_ids:
            return {}, "component_id values must be unique"
        component_ids.add(component_id)
        normalized_components.append(normalized_component)
    normalized_components.sort(key=lambda item: item["component_id"])

    if status == "ok":
        if normalized_identity is None:
            return {}, "ok projection identity must be a mapping"
        if revision is None:
            return {}, "ok projection revision must be a non-negative integer"
        if (
            isinstance(component_count, bool)
            or not isinstance(component_count, int)
            or component_count < 0
        ):
            return {}, "ok component_count must be a non-negative integer"
        if component_count != len(normalized_components):
            return {}, "component_count must match components length"
        if sum(normalized_coverage.values()) != component_count:
            return {}, "coverage total must match component_count"
    else:
        if component_count is not None:
            return {}, "non-ok component_count must remain null"
        if normalized_components:
            return {}, "non-ok components must remain empty"
        if normalized_coverage:
            return {}, "non-ok coverage must remain empty"

    do_not_claim = result.get("do_not_claim")
    if not isinstance(do_not_claim, list) or not all(
        isinstance(item, str) for item in do_not_claim
    ):
        return {}, "do_not_claim must be a list of strings"

    return {
        "status": status,
        "reason": reason,
        "projection_scope": _RUNTIME_PROJECTION_SCOPE,
        "track": _SR_TRACK,
        "projection_state": _PROJECTION_STATE,
        "maps_live_runtime_snapshot_facts": status == "ok",
        "identity_relation": _IDENTITY_RELATION,
        "identity": normalized_identity,
        "revision": revision,
        "component_count": component_count,
        "coverage": dict(sorted(normalized_coverage.items())),
        "components": normalized_components,
        "do_not_claim": list(do_not_claim),
    }, None


def _normalize_component(
    raw_component: Any,
) -> tuple[dict[str, Any], str | None]:
    if not isinstance(raw_component, Mapping):
        return {}, "each component must be a mapping"
    expected = {
        "projection_state": _PROJECTION_STATE,
        "maps_live_components": False,
        "source": _COMPONENT_SOURCE,
        "identity_relation": _IDENTITY_RELATION,
    }
    for key, expected_value in expected.items():
        if raw_component.get(key) != expected_value:
            return {}, f"component {key} must be {expected_value!r}"

    for key in ("component_id", "component_type", "location"):
        value = raw_component.get(key)
        if not isinstance(value, str) or not value.strip():
            return {}, f"component {key} must be a non-empty string"

    attach_point = raw_component.get("attach_point")
    if (
        not isinstance(attach_point, list)
        or len(attach_point) != 2
        or any(not _is_finite_number(item) for item in attach_point)
    ):
        return {}, "component attach_point must contain two finite numbers"

    connection_count = raw_component.get("connection_count")
    if (
        isinstance(connection_count, bool)
        or not isinstance(connection_count, int)
        or connection_count < 0
    ):
        return {}, "component connection_count must be a non-negative integer"

    for key in ("inspectable_properties", "component_fields"):
        if not isinstance(raw_component.get(key), Mapping):
            return {}, f"component {key} must be a mapping"

    return _json_copy(dict(raw_component)), None


def _field(
    field_id: str,
    label: str,
    value: Any,
    field_type: str = "string",
) -> InspectorField:
    return InspectorField(
        id=field_id,
        label=label,
        type=field_type,
        value=_json_copy(value),
        editable=False,
        source_path=(),
    )


def _unavailable(
    code: str,
    message: str,
    *,
    warnings: tuple[str, ...] = (),
) -> SrSelectedComponentProjectionViewModel:
    safe_code = (
        code if isinstance(code, str) and code else "selected_projection_unavailable"
    )
    safe_message = (
        message
        if isinstance(message, str) and message
        else "Selected SR component projection unavailable"
    )
    return SrSelectedComponentProjectionViewModel(
        available=False,
        section=InspectorSection(
            id="worldbridge-sr-selected-component-projection",
            title="WorldBridge Components (Selected SR Runtime Entity)",
            fields=(
                _field("scope", "Scope", SR_SELECTED_COMPONENT_PROJECTION_SCOPE),
                _field(
                    "authority_command",
                    "Authority Command",
                    SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID,
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
) -> SrSelectedComponentProjectionViewModel:
    if isinstance(raw_error, Mapping):
        code = raw_error.get("code")
        message = raw_error.get("message")
    else:
        code = None
        message = None
    return _unavailable(
        code
        if isinstance(code, str) and code
        else "selected_projection_unavailable",
        message
        if isinstance(message, str) and message
        else "Selected SR component projection unavailable",
        warnings=warnings,
    )


def _count_meaning(status: str, component_count: int | None) -> str:
    if status == "ok":
        if component_count == 0:
            return (
                "Authority proved zero attached components for the selected SR "
                "runtime entity."
            )
        noun = "component" if component_count == 1 else "components"
        return (
            f"Authority proved {component_count} attached {noun} for the selected "
            "SR runtime entity."
        )
    if status == "not_proven":
        return (
            "Component count unknown; current SR snapshot did not prove component facts."
        )
    return f"Component count unavailable while selected SR projection status is {status}."


def _safe_warnings(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(item for item in raw if isinstance(item, str))


def _dedupe_warnings(warnings: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(warnings))


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


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _json_copy(value: Any) -> Any:
    return json.loads(
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    )


def _exception_message(exc: Exception) -> str:
    text = str(exc).strip()
    return text or exc.__class__.__name__


__all__ = [
    "SR_SELECTED_COMPONENT_PROJECTION_COMMAND_ID",
    "SR_SELECTED_COMPONENT_PROJECTION_SCOPE",
    "SrSelectedComponentProjectionViewModel",
    "build_sr_selected_component_projection_view_model",
    "load_sr_selected_component_projection_view_model",
]
