# -*- coding: utf-8 -*-
"""Qt-free Inspector consumer for bounded WorldBridge operator presentation."""
from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    NEGATIVE_CAPABILITIES,
    validate_worldbridge_quarantine_operator_presentation,
)
from core.VitaLoom.inspector.schema import InspectorField, InspectorSection

WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID = (
    "runtime.worldbridge.quarantine_operator_presentation"
)
WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_SCOPE = (
    "same_adapter_worldbridge_quarantine_operator_presentation"
)


@dataclass(frozen=True)
class WorldBridgeQuarantineOperatorPresentationViewModel:
    """Immutable, non-editable Inspector state for E242 evidence."""

    available: bool
    section: InspectorSection
    error: dict[str, str] | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True
    scope: str = WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_SCOPE
    authority_command_id: str = WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID
    collapsed_by_default: bool = True

    def to_dict(self) -> dict[str, Any]:
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
                        "value": copy.deepcopy(item.value),
                        "editable": item.editable,
                        "source_path": list(item.source_path),
                        "validation": dict(item.validation),
                    }
                    for item in self.section.fields
                ],
            },
        }


def build_worldbridge_quarantine_operator_presentation_view_model(
    command_result: Mapping[str, Any] | Any,
) -> WorldBridgeQuarantineOperatorPresentationViewModel:
    if not isinstance(command_result, Mapping):
        return _unavailable("invalid_command_result", "Presentation command result must be a mapping")
    warnings = _safe_warnings(command_result.get("warnings"))
    if command_result.get("ok") is not True:
        if command_result.get("ok") is False:
            return _command_error_view(command_result.get("error"), warnings)
        return _unavailable(
            "invalid_command_result",
            "Presentation command result must contain boolean ok",
            warnings=warnings,
        )
    result = command_result.get("result")
    if not isinstance(result, Mapping):
        return _unavailable("invalid_payload", "Presentation result must be a mapping", warnings=warnings)
    if not _is_json_value(result):
        return _unavailable("non_json_payload", "Presentation result must contain JSON values only", warnings=warnings)
    validation = validate_worldbridge_quarantine_operator_presentation(result)
    if validation["valid"] is not True:
        return _unavailable(
            "guardrail_violation",
            ", ".join(validation["errors"]),
            warnings=warnings,
        )
    normalized = copy.deepcopy(dict(result))
    if normalized.get("read_only") is not True or normalized.get("scope") != WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_SCOPE:
        return _unavailable("guardrail_violation", "Presentation must remain read-only and same-adapter scoped", warnings=warnings)
    if any(normalized.get("negative_capabilities", {}).get(key) is not False for key in NEGATIVE_CAPABILITIES):
        return _unavailable("guardrail_violation", "Presentation negative capabilities must remain false", warnings=warnings)
    fields = (
        _field("scope", "Scope", normalized["scope"]),
        _field("availability", "Availability", normalized["availability"]),
        _field("operator_state", "Operator State", normalized["operator_state"]),
        _field("headline", "Headline", normalized["headline"]),
        _field("caveat", "Caveat", normalized["caveat"]),
        _field("current_runtime_quarantined", "Current Runtime Quarantined", normalized["current_runtime_quarantined"], "bool"),
        _field("same_adapter_only", "Same Adapter Only", normalized["same_adapter_only"], "bool"),
        _field("evidence_summary", "Evidence Summary", normalized["evidence_summary"], "json"),
        _field("artifact_import_diagnostic", "Artifact Import Diagnostic", normalized["artifact_import_diagnostic"], "json"),
        _field("negative_capabilities", "Negative Capabilities", normalized["negative_capabilities"], "json"),
        _field("do_not_claim", "Do Not Claim", normalized["do_not_claim"], "json"),
    )
    return WorldBridgeQuarantineOperatorPresentationViewModel(
        available=normalized["availability"] == "available",
        section=InspectorSection(
            id="worldbridge-quarantine-operator-presentation",
            title="WorldBridge Quarantine (Operator Evidence)",
            fields=fields,
        ),
        warnings=warnings,
    )


def load_worldbridge_quarantine_operator_presentation_view_model(
    *, registry: Any | None = None,
) -> WorldBridgeQuarantineOperatorPresentationViewModel:
    if registry is None:
        from core.VitaLoom.commands.registry import get_command_registry

        registry = get_command_registry()
    try:
        result = registry.run(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {})
    except Exception as exc:
        return _unavailable("command_runner_error", str(exc).strip() or exc.__class__.__name__)
    return build_worldbridge_quarantine_operator_presentation_view_model(result)


def _field(field_id: str, label: str, value: Any, field_type: str = "string") -> InspectorField:
    return InspectorField(id=field_id, label=label, type=field_type, value=copy.deepcopy(value), editable=False, source_path=())


def _unavailable(code: str, message: str, *, warnings: tuple[str, ...] = ()) -> WorldBridgeQuarantineOperatorPresentationViewModel:
    safe_code = code if isinstance(code, str) and code else "presentation_unavailable"
    safe_message = message if isinstance(message, str) and message else "Operator presentation unavailable"
    return WorldBridgeQuarantineOperatorPresentationViewModel(
        available=False,
        section=InspectorSection(
            id="worldbridge-quarantine-operator-presentation",
            title="WorldBridge Quarantine (Operator Evidence)",
            fields=(
                _field("scope", "Scope", WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_SCOPE),
                _field("availability", "Availability", "unavailable"),
                _field("error_code", "Error Code", safe_code),
                _field("error_message", "Error Message", safe_message),
            ),
        ),
        error={"code": safe_code, "message": safe_message},
        warnings=warnings,
    )


def _command_error_view(raw_error: Any, warnings: tuple[str, ...]) -> WorldBridgeQuarantineOperatorPresentationViewModel:
    if isinstance(raw_error, Mapping):
        code = raw_error.get("code")
        message = raw_error.get("message")
    else:
        code = None
        message = None
    return _unavailable(
        code if isinstance(code, str) and code else "presentation_unavailable",
        message if isinstance(message, str) and message else "Operator presentation unavailable",
        warnings=warnings,
    )


def _safe_warnings(value: Any) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str)) if isinstance(value, list) else ()


def _is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


__all__ = [
    "WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID",
    "WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_SCOPE",
    "WorldBridgeQuarantineOperatorPresentationViewModel",
    "build_worldbridge_quarantine_operator_presentation_view_model",
    "load_worldbridge_quarantine_operator_presentation_view_model",
]
