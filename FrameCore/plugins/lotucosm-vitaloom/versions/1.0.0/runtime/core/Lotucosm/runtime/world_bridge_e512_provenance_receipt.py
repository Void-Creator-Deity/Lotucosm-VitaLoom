"""Cross-surface provenance receipt for E509/E510/E511 evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_e509_replay_persistence import validate_worldbridge_e509_replay_persistence_envelope
from .world_bridge_quarantine_operator_presentation import validate_worldbridge_quarantine_operator_presentation
from .world_bridge_quarantine_operator_presentation_export import validate_worldbridge_quarantine_operator_presentation_export_record
from .world_bridge_quarantine_operator_presentation_export_audit import validate_worldbridge_quarantine_operator_presentation_export_audit

SCHEMA_VERSION = 1
STATUS = "worldbridge_e512_provenance_receipt"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _without(value: Mapping[str, Any], field: str) -> str:
    payload = dict(value)
    payload[field] = ""
    return _digest(payload)


def build_worldbridge_e512_provenance_receipt(
    *,
    persistence_envelope: Mapping[str, Any],
    presentation: Mapping[str, Any],
    export_record: Mapping[str, Any],
    audit_record: Mapping[str, Any],
) -> dict[str, Any]:
    _require_valid(persistence_envelope, validate_worldbridge_e509_replay_persistence_envelope, "persistence_envelope")
    _require_valid(presentation, validate_worldbridge_quarantine_operator_presentation, "presentation")
    _require_valid(export_record, validate_worldbridge_quarantine_operator_presentation_export_record, "export_record")
    _require_valid(audit_record, validate_worldbridge_quarantine_operator_presentation_export_audit, "audit_record")
    _validate_surface_links(persistence_envelope, presentation, export_record, audit_record)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "checkpoint_digest": persistence_envelope["checkpoint_digest"],
        "corpus_digest": persistence_envelope["corpus_digest"],
        "envelope_digest": persistence_envelope["envelope_digest"],
        "presentation_digest": _digest(presentation),
        "export_digest": export_record["export_digest"],
        "audit_digest": audit_record["audit_digest"],
        "diagnostic_digest": persistence_envelope["restore_diagnostic"]["diagnostic_digest"],
        "surface_chain_valid": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "receipt_digest": "",
    }
    receipt["receipt_digest"] = _without(receipt, "receipt_digest")
    return copy.deepcopy(receipt)


def validate_worldbridge_e512_provenance_receipt(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["receipt_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    for field in ("checkpoint_digest", "corpus_digest", "envelope_digest", "presentation_digest", "export_digest", "audit_digest", "diagnostic_digest", "receipt_digest"):
        if not _is_digest(value.get(field)):
            errors.append(f"{field}_invalid")
    if value.get("surface_chain_valid") is not True:
        errors.append("surface_chain_invalid")
    for field in ("replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("receipt_digest") != _without(value, "receipt_digest"):
        errors.append("receipt_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_e512_provenance_receipt(value: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_e512_provenance_receipt(value)
    if validation["valid"] is not True:
        raise ValueError("invalid E512 provenance receipt: " + ",".join(validation["errors"]))
    return _canonical(value)


def decode_worldbridge_e512_provenance_receipt(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode canonical receipt bytes and reject non-canonical or invalid data."""
    raw = bytes(data)
    try:
        decoded = json.loads(raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid E512 provenance receipt encoding") from exc
    if not isinstance(decoded, dict) or _canonical(decoded) != raw:
        raise ValueError("non-canonical E512 provenance receipt encoding")
    validation = validate_worldbridge_e512_provenance_receipt(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid E512 provenance receipt: " + ",".join(validation["errors"]))
    return copy.deepcopy(decoded)


def build_worldbridge_e512_provenance_receipt_contract() -> dict[str, Any]:
    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_e512_provenance_receipt_contract",
        "read_only": True,
        "source_layers": ["e509_persistence", "e511_presentation", "operator_export", "operator_audit"],
        "authority_scope": "cross_surface_provenance_observation_only",
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "runtime_restore_performed": False,
    }
    contract["contract_valid"] = validate_worldbridge_e512_provenance_receipt_contract(contract)["valid"]
    return contract


def build_worldbridge_e512_provenance_receipt_status(receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    contract = build_worldbridge_e512_provenance_receipt_contract()
    if receipt is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_e512_provenance_receipt_unavailable",
            "read_only": True,
            "availability": "unavailable",
            "reason": "complete_cross_surface_receipt_not_bound_to_current_runtime",
            "receipt": None,
            "contract": contract,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    validation = validate_worldbridge_e512_provenance_receipt(receipt)
    if validation["valid"] is not True:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "worldbridge_e512_provenance_receipt_rejected",
            "read_only": True,
            "availability": "rejected",
            "reason": "receipt_validation_failed",
            "errors": list(validation["errors"]),
            "receipt": None,
            "contract": contract,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "availability": "available",
        "receipt": copy.deepcopy(dict(receipt)),
        "contract": contract,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


def validate_worldbridge_e512_provenance_receipt_contract(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != "worldbridge_e512_provenance_receipt_contract":
        errors.append("identity_mismatch")
    if value.get("read_only") is not True or value.get("authority_scope") != "cross_surface_provenance_observation_only":
        errors.append("authority_scope_mismatch")
    if value.get("source_layers") != ["e509_persistence", "e511_presentation", "operator_export", "operator_audit"]:
        errors.append("source_layers_mismatch")
    for field in ("replay_admitted", "default_ready", "lossless", "runtime_restore_performed"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    return {"valid": not errors, "errors": errors}


def _validate_surface_links(envelope: Mapping[str, Any], presentation: Mapping[str, Any], export_record: Mapping[str, Any], audit_record: Mapping[str, Any]) -> None:
    diagnostic = envelope.get("restore_diagnostic")
    replay_diagnostic = presentation.get("replay_persistence_diagnostic")
    if not isinstance(diagnostic, Mapping) or not isinstance(replay_diagnostic, Mapping):
        raise ValueError("replay diagnostic provenance missing")
    bounded_payload = {
        "schema_version": replay_diagnostic.get("schema_version"),
        "code": replay_diagnostic.get("code"),
        "errors": replay_diagnostic.get("errors"),
    }
    if replay_diagnostic.get("diagnostic_digest") != _digest(bounded_payload):
        raise ValueError("diagnostic digest provenance mismatch")
    if export_record.get("source_presentation_digest") != _digest(presentation):
        raise ValueError("presentation export digest provenance mismatch")
    if audit_record.get("source_presentation_digest") != export_record.get("source_presentation_digest"):
        raise ValueError("audit presentation digest provenance mismatch")
    if audit_record.get("source_export_digest") != export_record.get("export_digest"):
        raise ValueError("audit export digest provenance mismatch")
    if export_record.get("replay_persistence_diagnostic") != presentation.get("replay_persistence_diagnostic"):
        raise ValueError("export replay diagnostic provenance mismatch")


def _require_valid(value: Mapping[str, Any], validator: Any, name: str) -> None:
    result = validator(value)
    if result.get("valid") is not True:
        raise ValueError(f"invalid {name}: " + ",".join(result.get("errors", [])))


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


__all__ = [
    "build_worldbridge_e512_provenance_receipt",
    "build_worldbridge_e512_provenance_receipt_contract",
    "build_worldbridge_e512_provenance_receipt_status",
    "decode_worldbridge_e512_provenance_receipt",
    "encode_worldbridge_e512_provenance_receipt",
    "validate_worldbridge_e512_provenance_receipt",
    "validate_worldbridge_e512_provenance_receipt_contract",
]
