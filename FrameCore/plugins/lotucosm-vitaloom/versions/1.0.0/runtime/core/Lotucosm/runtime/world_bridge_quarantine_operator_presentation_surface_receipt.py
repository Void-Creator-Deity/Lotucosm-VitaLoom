# -*- coding: utf-8 -*-
"""Canonical, in-memory E247 receipt export for completed E246 surface audits.

The receipt is evidence only.  It accepts a fully validated presentation-surface
audit, preserves only bounded digests/policies, and has no runtime or UI authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import (
    SCOPE as SOURCE_SCOPE,
    STATUS as SOURCE_STATUS,
    VISIBLE_FIELD_IDS,
    validate_worldbridge_quarantine_operator_presentation_surface_audit,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_surface_receipt"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-surface-receipt+json"
ENCODING = "utf-8"
MAX_RECEIPT_BYTES = 4 * 1024
DO_NOT_CLAIM = (
    "quarantine_operator_presentation_surface_receipt_is_not_recovery",
    "quarantine_operator_presentation_surface_receipt_is_not_same_runtime_retry",
    "quarantine_operator_presentation_surface_receipt_is_not_quarantine_clear_authority",
    "quarantine_operator_presentation_surface_receipt_is_not_re_admission",
    "quarantine_operator_presentation_surface_receipt_is_not_replay_or_restore",
    "quarantine_operator_presentation_surface_receipt_is_not_live_runtime_state",
    "quarantine_operator_presentation_surface_receipt_is_not_persistence_or_file_network_output",
    "quarantine_operator_presentation_surface_receipt_is_not_ui_authority",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "receipt_scope": "validated_e246_quarantine_presentation_surface_audit_only",
    "read_only": True,
    "source_audit_integrity_valid": True,
    "same_adapter_only": True,
    "opaque_lifecycle_values_exposed": False,
    "receipt_persisted": False,
    "file_written": False,
    "network_transmitted": False,
    "external_artifact_input": False,
    "runtime_action_authority": False,
    "ui_authority": False,
    "quarantine_clear_admitted": False,
    "same_runtime_retry_admitted": False,
    "recovery_admitted": False,
    "replay_or_restore_admitted": False,
    "mutation_executed": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version", "status", "media_type", "encoding", "canonical_json",
    "source_audit_status", "source_audit_scope", "source_audit_digest", "source_bundle_digest",
    "visible_field_digest", "visible_field_ids", "command_mcp_parity_valid", "inspector_parity_valid",
    "inspector_fields_editable", "receipt_scope", "read_only", "source_audit_integrity_valid",
    "same_adapter_only", "opaque_lifecycle_values_exposed", "receipt_persisted", "file_written",
    "network_transmitted", "external_artifact_input", "runtime_action_authority", "ui_authority",
    "quarantine_clear_admitted", "same_runtime_retry_admitted", "recovery_admitted",
    "replay_or_restore_admitted", "mutation_executed", "default_ready", "do_not_claim", "receipt_digest",
}


def export_worldbridge_quarantine_operator_presentation_surface_receipt(
    surface_audit: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Export a bounded immutable receipt from one fully valid E246 audit."""
    source = _validated_source_audit(surface_audit)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_audit_status": SOURCE_STATUS,
        "source_audit_scope": SOURCE_SCOPE,
        "source_audit_digest": source["audit_digest"],
        "source_bundle_digest": source["source_bundle_digest"],
        "visible_field_digest": source["visible_field_digest"],
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "command_mcp_parity_valid": True,
        "inspector_parity_valid": True,
        "inspector_fields_editable": False,
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    receipt["receipt_digest"] = _receipt_digest(receipt)
    validation = validate_worldbridge_quarantine_operator_presentation_surface_receipt(receipt, surface_audit=source)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine presentation surface receipt: " + ",".join(validation["errors"]))
    if len(_canonical_json_bytes(receipt)) > MAX_RECEIPT_BYTES:
        raise RuntimeError("quarantine presentation surface receipt exceeds bounded size")
    return copy.deepcopy(receipt)


def encode_worldbridge_quarantine_operator_presentation_surface_receipt(receipt: Mapping[str, Any]) -> bytes:
    """Encode one validated receipt into canonical UTF-8 JSON without writing it."""
    validation = validate_worldbridge_quarantine_operator_presentation_surface_receipt(receipt)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation surface receipt: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(receipt))
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise ValueError("quarantine presentation surface receipt exceeds bounded size")
    return bytes(encoded)


def decode_worldbridge_quarantine_operator_presentation_surface_receipt(
    data: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Decode only canonical duplicate-key-free receipt JSON."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("receipt data must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("quarantine presentation surface receipt exceeds bounded size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid canonical quarantine presentation surface receipt JSON") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError("quarantine presentation surface receipt must decode to mapping")
    validation = validate_worldbridge_quarantine_operator_presentation_surface_receipt(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation surface receipt: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(dict(decoded)) != raw:
        raise ValueError("non-canonical quarantine presentation surface receipt JSON")
    return copy.deepcopy(dict(decoded))


def validate_worldbridge_quarantine_operator_presentation_surface_receipt(
    receipt: object,
    *,
    surface_audit: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Fail closed unless fixed receipt policy and optional source parity hold."""
    if not isinstance(receipt, Mapping):
        return {"valid": False, "errors": ["receipt_not_mapping"]}
    try:
        value = copy.deepcopy(dict(receipt))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["receipt_not_copyable"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("receipt_shape_invalid")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("receipt_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("receipt_encoding_mismatch")
    if value.get("source_audit_status") != SOURCE_STATUS or value.get("source_audit_scope") != SOURCE_SCOPE:
        errors.append("receipt_source_identity_mismatch")
    if value.get("visible_field_ids") != list(VISIBLE_FIELD_IDS):
        errors.append("visible_field_ids_mismatch")
    if value.get("command_mcp_parity_valid") is not True or value.get("inspector_parity_valid") is not True:
        errors.append("surface_parity_missing")
    if value.get("inspector_fields_editable") is not False:
        errors.append("inspector_editability_overclaim")
    for key, expected in _STATIC_POLICIES.items():
        actual = value.get(key)
        matches = actual is expected if isinstance(expected, bool) else actual == expected
        if not matches:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    for key in ("source_audit_digest", "source_bundle_digest", "visible_field_digest"):
        if not _is_sha256(value.get(key)):
            errors.append(f"{key}_invalid")
    if value.get("receipt_digest") != _receipt_digest(value):
        errors.append("receipt_digest_mismatch")
    if not _is_json_value(value):
        errors.append("receipt_non_json_value")
    elif len(_canonical_json_bytes(value)) > MAX_RECEIPT_BYTES:
        errors.append("receipt_too_large")
    if surface_audit is not None:
        try:
            source = _validated_source_audit(surface_audit)
        except (TypeError, ValueError) as exc:
            errors.append("source_audit_invalid")
        else:
            for receipt_key, source_key in (
                ("source_audit_digest", "audit_digest"),
                ("source_bundle_digest", "source_bundle_digest"),
                ("visible_field_digest", "visible_field_digest"),
            ):
                if value.get(receipt_key) != source.get(source_key):
                    errors.append(f"source_{receipt_key}_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_quarantine_operator_presentation_surface_receipt_contract() -> dict[str, Any]:
    """Return the static E247 non-authority receipt contract."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_audit_status": SOURCE_STATUS,
        "source_audit_scope": SOURCE_SCOPE,
        "media_type": MEDIA_TYPE,
        "max_receipt_bytes": MAX_RECEIPT_BYTES,
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM),
        "accepts_external_artifact_input": False,
        "raw_lifecycle_values_exposed": False,
        "contract_valid": True,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != STATUS:
        errors.append("contract_identity_mismatch")
    if contract.get("source_audit_status") != SOURCE_STATUS or contract.get("source_audit_scope") != SOURCE_SCOPE:
        errors.append("contract_source_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_receipt_bytes") != MAX_RECEIPT_BYTES:
        errors.append("contract_media_or_size_mismatch")
    if contract.get("visible_field_ids") != list(VISIBLE_FIELD_IDS) or contract.get("static_policies") != _STATIC_POLICIES:
        errors.append("contract_policy_mismatch")
    if contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_claim_mismatch")
    if contract.get("accepts_external_artifact_input") is not False or contract.get("raw_lifecycle_values_exposed") is not False:
        errors.append("contract_non_authority_mismatch")
    if contract.get("contract_valid") is not True:
        errors.append("contract_valid_missing")
    return {"valid": not errors, "errors": errors}


def _validated_source_audit(value: object) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        if len(raw) > MAX_RECEIPT_BYTES:
            raise ValueError("surface audit exceeds bounded size")
        try:
            decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("invalid canonical surface audit JSON") from exc
        if not isinstance(decoded, Mapping) or _canonical_json_bytes(dict(decoded)) != raw:
            raise ValueError("surface audit must be canonical mapping JSON")
        source = copy.deepcopy(dict(decoded))
    elif isinstance(value, Mapping):
        source = copy.deepcopy(dict(value))
    else:
        raise TypeError("surface_audit must be mapping or canonical bytes")
    validation = validate_worldbridge_quarantine_operator_presentation_surface_audit(source)
    if validation["valid"] is not True:
        raise ValueError("invalid presentation surface audit: " + ",".join(validation["errors"]))
    return source


def _receipt_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("receipt_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return False
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "DO_NOT_CLAIM", "ENCODING", "MAX_RECEIPT_BYTES", "MEDIA_TYPE", "STATUS",
    "build_worldbridge_quarantine_operator_presentation_surface_receipt_contract",
    "decode_worldbridge_quarantine_operator_presentation_surface_receipt",
    "encode_worldbridge_quarantine_operator_presentation_surface_receipt",
    "export_worldbridge_quarantine_operator_presentation_surface_receipt",
    "validate_worldbridge_quarantine_operator_presentation_surface_receipt",
    "validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract",
]
