# -*- coding: utf-8 -*-
"""Read-only, in-memory audit for E243 quarantine presentation exports."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import NEGATIVE_CAPABILITIES
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    ENCODING,
    MEDIA_TYPE as EXPORT_MEDIA_TYPE,
    SCHEMA_VERSION as EXPORT_SCHEMA_VERSION,
    build_worldbridge_quarantine_operator_presentation_export_contract,
    decode_worldbridge_quarantine_operator_presentation_export_record,
    validate_worldbridge_quarantine_operator_presentation_export_record,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_export_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-export-audit+json"
MAX_AUDIT_BYTES = 4 * 1024
DO_NOT_CLAIM = (
    "quarantine_operator_presentation_export_audit_is_not_recovery",
    "quarantine_operator_presentation_export_audit_is_not_same_runtime_retry",
    "quarantine_operator_presentation_export_audit_is_not_quarantine_clear_authority",
    "quarantine_operator_presentation_export_audit_is_not_replay_or_restore",
    "quarantine_operator_presentation_export_audit_is_not_live_runtime_state",
    "quarantine_operator_presentation_export_audit_is_not_persistence_or_file_network_output",
    "quarantine_operator_presentation_export_audit_is_not_ui_authority",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "audit_scope": "validated_quarantine_operator_presentation_export_only",
    "read_only": True,
    "export_integrity_valid": True,
    "audit_persisted": False,
    "file_written": False,
    "network_transmitted": False,
    "replay_input": False,
    "checkpoint_state": False,
    "restore_performed": False,
    "mutation_executed": False,
    "live_runtime_state": False,
    "ui_authority": False,
    "operator_action_admitted": False,
    "quarantine_clear_admitted": False,
    "same_runtime_retry_admitted": False,
    "replay_admitted": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version", "status", "media_type", "encoding", "canonical_json", "source_export_media_type",
    "source_export_digest", "source_presentation_digest", "availability", "operator_state", "headline", "caveat",
    "current_runtime_quarantined", "same_adapter_only", "evidence_summary", "artifact_import_diagnostic", "replay_persistence_diagnostic", "negative_capabilities",
    "audit_scope", "read_only", "export_integrity_valid", "audit_persisted", "file_written",
    "network_transmitted", "replay_input", "checkpoint_state", "restore_performed", "mutation_executed",
    "live_runtime_state", "ui_authority", "operator_action_admitted", "quarantine_clear_admitted",
    "same_runtime_retry_admitted", "replay_admitted", "default_ready", "do_not_claim", "audit_digest",
}


def audit_worldbridge_quarantine_operator_presentation_export(
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Audit a validated E243 export without accessing runtime/UI state."""
    source = _validated_export(export_record)
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_export_media_type": EXPORT_MEDIA_TYPE,
        "source_export_digest": source["export_digest"],
        "source_presentation_digest": source["source_presentation_digest"],
        "availability": source["availability"],
        "operator_state": source["operator_state"],
        "headline": source["headline"],
        "caveat": source["caveat"],
        "current_runtime_quarantined": source["current_runtime_quarantined"],
        "same_adapter_only": True,
        "evidence_summary": copy.deepcopy(source["evidence_summary"]),
        "artifact_import_diagnostic": copy.deepcopy(source.get("artifact_import_diagnostic")),
        "replay_persistence_diagnostic": copy.deepcopy(source.get("replay_persistence_diagnostic")),
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    audit["audit_digest"] = _audit_digest(audit)
    validation = validate_worldbridge_quarantine_operator_presentation_export_audit(audit, export_record=source)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine presentation export audit: " + ",".join(validation["errors"]))
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_export_audit(
    audit: object,
    *,
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    try:
        value = copy.deepcopy(dict(audit))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["audit_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("audit_keys_mismatch")
    for key, expected in (("schema_version", SCHEMA_VERSION), ("status", STATUS), ("media_type", MEDIA_TYPE), ("encoding", ENCODING)):
        if value.get(key) != expected:
            errors.append(f"{key}_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    if value.get("source_export_media_type") != EXPORT_MEDIA_TYPE:
        errors.append("source_export_media_type_mismatch")
    for key in ("source_export_digest", "source_presentation_digest"):
        if not _is_sha256(value.get(key)):
            errors.append(f"{key}_invalid")
    _validate_facts(value, errors)
    for key, expected in _STATIC_POLICIES.items():
        if value.get(key) != expected or type(value.get(key)) is not type(expected):
            errors.append(f"{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_AUDIT_BYTES:
            errors.append("audit_oversized")
    except (TypeError, ValueError):
        errors.append("audit_not_canonical_json")
    if export_record is not None:
        try:
            source = _validated_export(export_record)
        except (TypeError, ValueError) as exc:
            errors.extend(("source_export_invalid", str(exc)))
        else:
            errors.extend(_export_parity_errors(value, source))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_export_audit(audit: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_quarantine_operator_presentation_export_audit(audit)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation export audit: " + ",".join(validation["errors"]))
    return _canonical_json_bytes(audit)


def decode_worldbridge_quarantine_operator_presentation_export_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("encoded audit must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_AUDIT_BYTES:
        raise ValueError("encoded audit exceeds maximum size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid encoded quarantine presentation export audit") from exc
    validation = validate_worldbridge_quarantine_operator_presentation_export_audit(decoded)
    if validation["valid"] is not True or _canonical_json_bytes(decoded) != raw:
        raise ValueError("encoded quarantine presentation export audit is not valid canonical JSON")
    return copy.deepcopy(decoded)


def build_worldbridge_quarantine_operator_presentation_export_audit_contract() -> dict[str, Any]:
    export_record = build_worldbridge_quarantine_operator_presentation_export_contract()["export_record"]
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": "worldbridge_quarantine_operator_presentation_export_audit_contract",
        "read_only": True, "authority_scope": _STATIC_POLICIES["audit_scope"], "media_type": MEDIA_TYPE,
        "max_audit_bytes": MAX_AUDIT_BYTES, "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "static_policies": copy.deepcopy(_STATIC_POLICIES), "do_not_claim": list(DO_NOT_CLAIM), "audit": audit,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_export_audit_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_export_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != "worldbridge_quarantine_operator_presentation_export_audit_contract":
        errors.append("contract_identity_mismatch")
    if contract.get("read_only") is not True or contract.get("authority_scope") != _STATIC_POLICIES["audit_scope"]:
        errors.append("contract_authority_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_audit_bytes") != MAX_AUDIT_BYTES:
        errors.append("contract_media_or_size_mismatch")
    if contract.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}:
        errors.append("contract_negative_capabilities_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_policy_mismatch")
    if validate_worldbridge_quarantine_operator_presentation_export_audit(contract.get("audit")).get("valid") is not True:
        errors.append("contract_audit_invalid")
    return {"valid": not errors, "errors": errors}


def _validated_export(value: Mapping[str, Any] | bytes | bytearray | memoryview) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return decode_worldbridge_quarantine_operator_presentation_export_record(value)
    if not isinstance(value, Mapping):
        raise TypeError("export_record must be mapping or canonical bytes")
    copied = copy.deepcopy(dict(value))
    validation = validate_worldbridge_quarantine_operator_presentation_export_record(copied)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation export: " + ",".join(validation["errors"]))
    return copied


def _validate_facts(value: Mapping[str, Any], errors: list[str]) -> None:
    if value.get("availability") not in {"available", "unavailable"}:
        errors.append("availability_invalid")
    if not _clean_nonempty_string(value.get("operator_state")) or not _clean_nonempty_string(value.get("headline")) or not _clean_nonempty_string(value.get("caveat")):
        errors.append("bounded_text_invalid")
    availability = value.get("availability")
    quarantined = value.get("current_runtime_quarantined")
    if (availability == "available" and type(quarantined) is not bool) or (availability == "unavailable" and quarantined is not None):
        errors.append("current_runtime_quarantined_invalid")
    if value.get("same_adapter_only") is not True:
        errors.append("same_adapter_only_mismatch")
    summary = value.get("evidence_summary")
    expected_summary_keys = {"failure_lifecycle_values_redacted", "current_lifecycle_values_redacted", "disposal_recorded", "disposal_boundary", "fresh_instance_boundary_observed"}
    if not isinstance(summary, Mapping) or set(summary) != expected_summary_keys:
        errors.append("evidence_summary_shape_invalid")
    elif summary.get("failure_lifecycle_values_redacted") is not True or summary.get("current_lifecycle_values_redacted") is not True:
        errors.append("opaque_lifecycle_values_not_redacted")
    if value.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}:
        errors.append("negative_capabilities_mismatch")


def _export_parity_errors(audit: Mapping[str, Any], export_record: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_export_media_type": EXPORT_MEDIA_TYPE, "source_export_digest": export_record["export_digest"],
        "source_presentation_digest": export_record["source_presentation_digest"], "availability": export_record["availability"],
        "operator_state": export_record["operator_state"], "headline": export_record["headline"], "caveat": export_record["caveat"],
        "current_runtime_quarantined": export_record["current_runtime_quarantined"], "same_adapter_only": True,
        "evidence_summary": export_record["evidence_summary"], "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "artifact_import_diagnostic": export_record.get("artifact_import_diagnostic"),
        "replay_persistence_diagnostic": export_record.get("replay_persistence_diagnostic"),
    }
    return [f"export_parity_{key}_mismatch" for key, expected_value in expected.items() if audit.get(key) != expected_value]


def _audit_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value); canonical.pop("audit_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _clean_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


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
    "MAX_AUDIT_BYTES", "MEDIA_TYPE", "audit_worldbridge_quarantine_operator_presentation_export",
    "build_worldbridge_quarantine_operator_presentation_export_audit_contract",
    "decode_worldbridge_quarantine_operator_presentation_export_audit",
    "encode_worldbridge_quarantine_operator_presentation_export_audit",
    "validate_worldbridge_quarantine_operator_presentation_export_audit",
    "validate_worldbridge_quarantine_operator_presentation_export_audit_contract",
]
