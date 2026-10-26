"""Qt-free read-only Inspector projection for the E512 receipt."""
from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.Lotucosm.runtime.world_bridge_e512_provenance_receipt import validate_worldbridge_e512_provenance_receipt
from core.VitaLoom.inspector.schema import InspectorField, InspectorSection

COMMAND_ID = "runtime.worldbridge.provenance_receipt"

@dataclass(frozen=True)
class WorldBridgeProvenanceReceiptViewModel:
    available: bool
    section: InspectorSection
    error: dict[str, str] | None = None

def build_worldbridge_provenance_receipt_view_model(command_result: Mapping[str, Any] | Any) -> WorldBridgeProvenanceReceiptViewModel:
    if not isinstance(command_result, Mapping) or command_result.get("ok") is not True:
        error = command_result.get("error") if isinstance(command_result, Mapping) else None
        return _unavailable(str(error.get("code", "receipt_unavailable")) if isinstance(error, Mapping) else "receipt_unavailable", str(error.get("message", "Provenance receipt unavailable")) if isinstance(error, Mapping) else "Provenance receipt unavailable")
    result = command_result.get("result")
    if not isinstance(result, Mapping):
        return _unavailable("invalid_payload", "Provenance receipt result must be a mapping")
    availability = result.get("availability")
    if availability != "available":
        return _unavailable(str(result.get("status", "receipt_unavailable")), str(result.get("reason", "Provenance receipt unavailable")))
    receipt = result.get("receipt")
    validation = validate_worldbridge_e512_provenance_receipt(receipt)
    if validation["valid"] is not True:
        return _unavailable("receipt_validation_failed", ", ".join(validation["errors"]))
    value = copy.deepcopy(dict(receipt))
    fields = tuple(_field(key, key.replace("_", " ").title(), value[key]) for key in (
        "receipt_digest", "checkpoint_digest", "corpus_digest", "envelope_digest",
        "presentation_digest", "export_digest", "audit_digest", "diagnostic_digest",
        "replay_admitted", "default_ready", "lossless",
    ))
    return WorldBridgeProvenanceReceiptViewModel(True, InspectorSection("worldbridge-provenance-receipt", "WorldBridge Provenance Receipt", fields))

def load_worldbridge_provenance_receipt_view_model(*, registry: Any | None = None) -> WorldBridgeProvenanceReceiptViewModel:
    if registry is None:
        from core.VitaLoom.commands.registry import get_command_registry
        registry = get_command_registry()
    try:
        result = registry.run(COMMAND_ID, {})
    except Exception as exc:
        return _unavailable("command_runner_error", str(exc) or exc.__class__.__name__)
    return build_worldbridge_provenance_receipt_view_model(result)

def _field(field_id: str, label: str, value: Any) -> InspectorField:
    return InspectorField(id=field_id, label=label, type="bool" if isinstance(value, bool) else "string", value=copy.deepcopy(value), editable=False, source_path=())

def _unavailable(code: str, message: str) -> WorldBridgeProvenanceReceiptViewModel:
    return WorldBridgeProvenanceReceiptViewModel(False, InspectorSection("worldbridge-provenance-receipt", "WorldBridge Provenance Receipt", (_field("availability", "Availability", "unavailable"), _field("error_code", "Error Code", code), _field("error_message", "Error Message", message))), {"code": code, "message": message})

__all__ = ["COMMAND_ID", "WorldBridgeProvenanceReceiptViewModel", "build_worldbridge_provenance_receipt_view_model", "load_worldbridge_provenance_receipt_view_model"]
