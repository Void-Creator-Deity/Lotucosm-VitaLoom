# -*- coding: utf-8 -*-
"""Paired E244 evidence-only receipt for E243 quarantine export and audit."""
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
    build_worldbridge_quarantine_operator_presentation_export_contract,
    decode_worldbridge_quarantine_operator_presentation_export_record,
    validate_worldbridge_quarantine_operator_presentation_export_record,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    MEDIA_TYPE as AUDIT_MEDIA_TYPE,
    audit_worldbridge_quarantine_operator_presentation_export,
    decode_worldbridge_quarantine_operator_presentation_export_audit,
    validate_worldbridge_quarantine_operator_presentation_export_audit,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_evidence_bundle"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-evidence-bundle+json"
MAX_BUNDLE_BYTES = 4 * 1024
DO_NOT_CLAIM = (
    "quarantine_evidence_bundle_is_not_recovery",
    "quarantine_evidence_bundle_is_not_same_runtime_retry",
    "quarantine_evidence_bundle_is_not_quarantine_clear_authority",
    "quarantine_evidence_bundle_is_not_replay_or_restore",
    "quarantine_evidence_bundle_is_not_live_runtime_state",
    "quarantine_evidence_bundle_is_not_persistence_or_file_network_output",
    "quarantine_evidence_bundle_is_not_ui_authority",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "consumer_scope": "validated_quarantine_presentation_export_audit_pair_only",
    "read_only": True,
    "export_audit_parity_valid": True,
    "bundle_persisted": False,
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
    "schema_version", "status", "media_type", "encoding", "canonical_json",
    "source_export_media_type", "source_audit_media_type", "source_export_digest", "source_audit_digest",
    "source_presentation_digest", "availability", "operator_state", "headline", "caveat",
    "current_runtime_quarantined", "same_adapter_only", "evidence_summary", "negative_capabilities",
    "consumer_scope", "read_only", "export_audit_parity_valid", "bundle_persisted", "file_written",
    "network_transmitted", "replay_input", "checkpoint_state", "restore_performed", "mutation_executed",
    "live_runtime_state", "ui_authority", "operator_action_admitted", "quarantine_clear_admitted",
    "same_runtime_retry_admitted", "replay_admitted", "default_ready", "do_not_claim", "bundle_digest",
}


def consume_worldbridge_quarantine_operator_evidence_pair(
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview,
    audit: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Admit one exact E243 export/audit pair as a compact evidence receipt."""
    source_export = _validated_export(export_record)
    source_audit = _validated_audit(audit)
    parity = validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(source_export, source_audit)
    if parity["valid"] is not True:
        raise ValueError("export/audit pair rejected: " + ",".join(parity["errors"]))
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "media_type": MEDIA_TYPE, "encoding": ENCODING,
        "canonical_json": True, "source_export_media_type": EXPORT_MEDIA_TYPE, "source_audit_media_type": AUDIT_MEDIA_TYPE,
        "source_export_digest": source_export["export_digest"], "source_audit_digest": source_audit["audit_digest"],
        "source_presentation_digest": source_export["source_presentation_digest"], "availability": source_export["availability"],
        "operator_state": source_export["operator_state"], "headline": source_export["headline"], "caveat": source_export["caveat"],
        "current_runtime_quarantined": source_export["current_runtime_quarantined"], "same_adapter_only": True,
        "evidence_summary": copy.deepcopy(source_export["evidence_summary"]),
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    bundle["bundle_digest"] = _bundle_digest(bundle)
    validation = validate_worldbridge_quarantine_operator_evidence_bundle(bundle, export_record=source_export, audit=source_audit)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine evidence bundle: " + ",".join(validation["errors"]))
    return copy.deepcopy(bundle)


def validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(export_record: object, audit: object) -> dict[str, Any]:
    """Verify exact bounded E243 export/audit provenance without runtime access."""
    try:
        source_export = _validated_export(export_record)
        source_audit = _validated_audit(audit)
    except (TypeError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    parity = validate_worldbridge_quarantine_operator_presentation_export_audit(source_audit, export_record=source_export)
    if parity["valid"] is not True:
        return {"valid": False, "errors": [f"audit_{error}" for error in parity["errors"]]}
    expected = {
        "source_export_media_type": EXPORT_MEDIA_TYPE, "source_export_digest": source_export["export_digest"],
        "source_presentation_digest": source_export["source_presentation_digest"], "availability": source_export["availability"],
        "operator_state": source_export["operator_state"], "headline": source_export["headline"], "caveat": source_export["caveat"],
        "current_runtime_quarantined": source_export["current_runtime_quarantined"], "same_adapter_only": True,
        "evidence_summary": source_export["evidence_summary"], "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
    }
    errors = [f"pair_parity_{key}_mismatch" for key, expected_value in expected.items() if source_audit.get(key) != expected_value]
    return {"valid": not errors, "errors": errors}


def validate_worldbridge_quarantine_operator_evidence_bundle(
    bundle: object,
    *,
    export_record: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
    audit: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    if not isinstance(bundle, Mapping):
        return {"valid": False, "errors": ["bundle_not_mapping"]}
    try:
        value = copy.deepcopy(dict(bundle))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["bundle_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS: errors.append("bundle_keys_mismatch")
    for key, expected in (("schema_version", SCHEMA_VERSION), ("status", STATUS), ("media_type", MEDIA_TYPE), ("encoding", ENCODING)):
        if value.get(key) != expected: errors.append(f"{key}_mismatch")
    if value.get("canonical_json") is not True: errors.append("canonical_json_mismatch")
    if value.get("source_export_media_type") != EXPORT_MEDIA_TYPE or value.get("source_audit_media_type") != AUDIT_MEDIA_TYPE:
        errors.append("source_media_type_mismatch")
    for key in ("source_export_digest", "source_audit_digest", "source_presentation_digest"):
        if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
    _validate_facts(value, errors)
    for key, expected in _STATIC_POLICIES.items():
        if value.get(key) != expected or type(value.get(key)) is not type(expected): errors.append(f"{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
    if value.get("bundle_digest") != _bundle_digest(value): errors.append("bundle_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_BUNDLE_BYTES: errors.append("bundle_oversized")
    except (TypeError, ValueError): errors.append("bundle_not_canonical_json")
    if (export_record is None) != (audit is None):
        errors.append("source_pair_must_be_supplied_together")
    elif export_record is not None and audit is not None:
        try:
            source_export, source_audit = _validated_export(export_record), _validated_audit(audit)
        except (TypeError, ValueError) as exc:
            errors.extend(("source_pair_invalid", str(exc)))
        else:
            pair = validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(source_export, source_audit)
            errors.extend(pair["errors"])
            expected = {
                "source_export_digest": source_export["export_digest"], "source_audit_digest": source_audit["audit_digest"],
                "source_presentation_digest": source_export["source_presentation_digest"], "availability": source_export["availability"],
                "operator_state": source_export["operator_state"], "headline": source_export["headline"], "caveat": source_export["caveat"],
                "current_runtime_quarantined": source_export["current_runtime_quarantined"], "same_adapter_only": True,
                "evidence_summary": source_export["evidence_summary"], "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
            }
            errors.extend(f"bundle_parity_{key}_mismatch" for key, expected_value in expected.items() if value.get(key) != expected_value)
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_evidence_bundle(bundle: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_quarantine_operator_evidence_bundle(bundle)
    if validation["valid"] is not True: raise ValueError("invalid quarantine evidence bundle: " + ",".join(validation["errors"]))
    return _canonical_json_bytes(bundle)


def decode_worldbridge_quarantine_operator_evidence_bundle(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)): raise TypeError("encoded bundle must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_BUNDLE_BYTES: raise ValueError("encoded bundle exceeds maximum size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid encoded quarantine evidence bundle") from exc
    validation = validate_worldbridge_quarantine_operator_evidence_bundle(decoded)
    if validation["valid"] is not True or _canonical_json_bytes(decoded) != raw: raise ValueError("encoded bundle is not valid canonical JSON")
    return copy.deepcopy(decoded)


def build_worldbridge_quarantine_operator_evidence_bundle_contract() -> dict[str, Any]:
    export_record = build_worldbridge_quarantine_operator_presentation_export_contract()["export_record"]
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": "worldbridge_quarantine_operator_evidence_bundle_contract", "read_only": True,
        "authority_scope": _STATIC_POLICIES["consumer_scope"], "media_type": MEDIA_TYPE, "max_bundle_bytes": MAX_BUNDLE_BYTES,
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM), "bundle": bundle,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_evidence_bundle_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_evidence_bundle_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping): return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != "worldbridge_quarantine_operator_evidence_bundle_contract": errors.append("contract_identity_mismatch")
    if contract.get("read_only") is not True or contract.get("authority_scope") != _STATIC_POLICIES["consumer_scope"]: errors.append("contract_authority_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_bundle_bytes") != MAX_BUNDLE_BYTES: errors.append("contract_media_or_size_mismatch")
    if contract.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}: errors.append("contract_negative_capabilities_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("contract_policy_mismatch")
    if validate_worldbridge_quarantine_operator_evidence_bundle(contract.get("bundle")).get("valid") is not True: errors.append("contract_bundle_invalid")
    return {"valid": not errors, "errors": errors}


def _validated_export(value: object) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)): return decode_worldbridge_quarantine_operator_presentation_export_record(value)
    if not isinstance(value, Mapping): raise TypeError("export_record must be mapping or canonical bytes")
    copied = copy.deepcopy(dict(value)); validation = validate_worldbridge_quarantine_operator_presentation_export_record(copied)
    if validation["valid"] is not True: raise ValueError("invalid quarantine presentation export: " + ",".join(validation["errors"]))
    return copied


def _validated_audit(value: object) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)): return decode_worldbridge_quarantine_operator_presentation_export_audit(value)
    if not isinstance(value, Mapping): raise TypeError("audit must be mapping or canonical bytes")
    copied = copy.deepcopy(dict(value)); validation = validate_worldbridge_quarantine_operator_presentation_export_audit(copied)
    if validation["valid"] is not True: raise ValueError("invalid quarantine presentation export audit: " + ",".join(validation["errors"]))
    return copied


def _validate_facts(value: Mapping[str, Any], errors: list[str]) -> None:
    if value.get("availability") not in {"available", "unavailable"}: errors.append("availability_invalid")
    if not all(_clean_nonempty_string(value.get(key)) for key in ("operator_state", "headline", "caveat")): errors.append("bounded_text_invalid")
    quarantined = value.get("current_runtime_quarantined")
    if (value.get("availability") == "available" and type(quarantined) is not bool) or (value.get("availability") == "unavailable" and quarantined is not None): errors.append("current_runtime_quarantined_invalid")
    if value.get("same_adapter_only") is not True: errors.append("same_adapter_only_mismatch")
    summary = value.get("evidence_summary"); expected_summary = {"failure_lifecycle_values_redacted", "current_lifecycle_values_redacted", "disposal_recorded", "disposal_boundary", "fresh_instance_boundary_observed"}
    if not isinstance(summary, Mapping) or set(summary) != expected_summary: errors.append("evidence_summary_shape_invalid")
    elif summary.get("failure_lifecycle_values_redacted") is not True or summary.get("current_lifecycle_values_redacted") is not True: errors.append("opaque_lifecycle_values_not_redacted")
    if value.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}: errors.append("negative_capabilities_mismatch")


def _bundle_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value); canonical.pop("bundle_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _clean_nonempty_string(value: object) -> bool: return isinstance(value, str) and bool(value) and value == value.strip()
def _is_sha256(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result: raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result
def _reject_json_constant(value: str) -> None: raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "MAX_BUNDLE_BYTES", "MEDIA_TYPE", "build_worldbridge_quarantine_operator_evidence_bundle_contract",
    "consume_worldbridge_quarantine_operator_evidence_pair", "decode_worldbridge_quarantine_operator_evidence_bundle",
    "encode_worldbridge_quarantine_operator_evidence_bundle", "validate_worldbridge_quarantine_operator_evidence_bundle",
    "validate_worldbridge_quarantine_operator_evidence_bundle_contract", "validate_worldbridge_quarantine_operator_evidence_bundle_source_pair",
]
