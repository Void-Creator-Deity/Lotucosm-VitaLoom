# -*- coding: utf-8 -*-
"""Bounded, in-memory E243 export for E242 quarantine operator presentations."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM as PRESENTATION_DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
    SCHEMA_VERSION as PRESENTATION_SCHEMA_VERSION,
    STATUS as PRESENTATION_STATUS,
    validate_worldbridge_quarantine_operator_presentation,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_export"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-export+json"
ENCODING = "utf-8"
MAX_EXPORT_BYTES = 4 * 1024
DO_NOT_CLAIM = (
    "quarantine_operator_presentation_export_is_not_recovery",
    "quarantine_operator_presentation_export_is_not_same_runtime_retry",
    "quarantine_operator_presentation_export_is_not_quarantine_clear_authority",
    "quarantine_operator_presentation_export_is_not_replay_or_restore",
    "quarantine_operator_presentation_export_is_not_live_runtime_state",
    "quarantine_operator_presentation_export_is_not_persistence_or_file_network_output",
    "quarantine_operator_presentation_export_is_not_ui_authority",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "export_scope": "validated_quarantine_operator_presentation_only",
    "read_only": True,
    "presentation_integrity_valid": True,
    "opaque_lifecycle_values_exposed": False,
    "export_persisted": False,
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
    "source_presentation_status", "source_presentation_digest", "source_scope",
    "availability", "operator_state", "headline", "caveat",
    "current_runtime_quarantined", "same_adapter_only", "evidence_summary",
    "artifact_import_diagnostic", "replay_persistence_diagnostic",
    "negative_capabilities", "source_do_not_claim", "export_scope", "read_only",
    "presentation_integrity_valid", "opaque_lifecycle_values_exposed", "export_persisted",
    "file_written", "network_transmitted", "replay_input", "checkpoint_state",
    "restore_performed", "mutation_executed", "live_runtime_state", "ui_authority",
    "operator_action_admitted", "quarantine_clear_admitted", "same_runtime_retry_admitted",
    "replay_admitted", "default_ready", "do_not_claim", "export_digest",
}


def export_worldbridge_quarantine_operator_presentation(
    presentation: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Export an already bounded E242 presentation as canonical in-memory evidence."""
    source = _validated_presentation(presentation)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_presentation_status": PRESENTATION_STATUS,
        "source_presentation_digest": _presentation_digest(source),
        "source_scope": source["scope"],
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
        "source_do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["export_digest"] = _export_digest(result)
    validation = validate_worldbridge_quarantine_operator_presentation_export_record(result, presentation=source)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine presentation export: " + ",".join(validation["errors"]))
    return copy.deepcopy(result)


def validate_worldbridge_quarantine_operator_presentation_export_record(
    export_record: object,
    *,
    presentation: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Validate fixed export schema, digest, redaction and optional source parity."""
    if not isinstance(export_record, Mapping):
        return {"valid": False, "errors": ["export_record_not_mapping"]}
    try:
        value = copy.deepcopy(dict(export_record))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["export_record_mapping_copy_failed"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("export_record_keys_mismatch")
    for key, expected in (("schema_version", SCHEMA_VERSION), ("status", STATUS), ("media_type", MEDIA_TYPE), ("encoding", ENCODING)):
        if value.get(key) != expected:
            errors.append(f"{key}_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    if value.get("source_presentation_status") != PRESENTATION_STATUS:
        errors.append("source_presentation_status_mismatch")
    if not _is_sha256(value.get("source_presentation_digest")):
        errors.append("source_presentation_digest_invalid")
    if not _clean_nonempty_string(value.get("source_scope")):
        errors.append("source_scope_invalid")
    _validate_facts(value, errors)
    for key, expected in _STATIC_POLICIES.items():
        if value.get(key) != expected or type(value.get(key)) is not type(expected):
            errors.append(f"{key}_mismatch")
    if value.get("source_do_not_claim") != list(PRESENTATION_DO_NOT_CLAIM):
        errors.append("source_do_not_claim_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("export_digest") != _export_digest(value):
        errors.append("export_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_EXPORT_BYTES:
            errors.append("export_record_oversized")
    except (TypeError, ValueError):
        errors.append("export_record_not_canonical_json")
    if presentation is not None:
        try:
            source = _validated_presentation(presentation)
        except (TypeError, ValueError) as exc:
            errors.extend(("source_presentation_invalid", str(exc)))
        else:
            errors.extend(_presentation_parity_errors(value, source))
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_export_record(export_record: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_quarantine_operator_presentation_export_record(export_record)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation export: " + ",".join(validation["errors"]))
    return _canonical_json_bytes(export_record)


def decode_worldbridge_quarantine_operator_presentation_export_record(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("encoded export must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_EXPORT_BYTES:
        raise ValueError("encoded export exceeds maximum size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid encoded quarantine presentation export") from exc
    validation = validate_worldbridge_quarantine_operator_presentation_export_record(decoded)
    if validation["valid"] is not True or _canonical_json_bytes(decoded) != raw:
        raise ValueError("encoded quarantine presentation export is not valid canonical JSON")
    return copy.deepcopy(decoded)


def build_worldbridge_quarantine_operator_presentation_export_contract() -> dict[str, Any]:
    unavailable = {
        "schema_version": PRESENTATION_SCHEMA_VERSION, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "unavailable", "operator_state": "unavailable", "headline": "WorldBridge lifecycle evidence unavailable",
        "caveat": "No runtime-control authority is granted.", "current_runtime_quarantined": None,
        "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True, "disposal_recorded": False, "disposal_boundary": None, "fresh_instance_boundary_observed": False},
        "artifact_import_diagnostic": None,
        "replay_persistence_diagnostic": None,
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM), "reason": "lifecycle_evidence_unavailable",
    }
    record = export_worldbridge_quarantine_operator_presentation(unavailable)
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": "worldbridge_quarantine_operator_presentation_export_contract",
        "read_only": True, "authority_scope": _STATIC_POLICIES["export_scope"], "media_type": MEDIA_TYPE,
        "max_export_bytes": MAX_EXPORT_BYTES, "opaque_lifecycle_values_exposed": False,
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "static_policies": copy.deepcopy(_STATIC_POLICIES), "do_not_claim": list(DO_NOT_CLAIM),
        "export_record": record,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_export_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_export_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != "worldbridge_quarantine_operator_presentation_export_contract":
        errors.append("contract_identity_mismatch")
    if contract.get("read_only") is not True or contract.get("authority_scope") != _STATIC_POLICIES["export_scope"]:
        errors.append("contract_authority_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_export_bytes") != MAX_EXPORT_BYTES:
        errors.append("contract_media_or_size_mismatch")
    if contract.get("opaque_lifecycle_values_exposed") is not False:
        errors.append("contract_opaque_values_overclaim")
    if contract.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}:
        errors.append("contract_negative_capabilities_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_policy_mismatch")
    if validate_worldbridge_quarantine_operator_presentation_export_record(contract.get("export_record")).get("valid") is not True:
        errors.append("contract_export_record_invalid")
    return {"valid": not errors, "errors": errors}


def _validated_presentation(value: Mapping[str, Any] | bytes | bytearray | memoryview) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError("export accepts an already bounded presentation mapping, not encoded source bytes")
    if not isinstance(value, Mapping):
        raise TypeError("presentation must be a mapping")
    copied = copy.deepcopy(dict(value))
    validation = validate_worldbridge_quarantine_operator_presentation(copied)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine operator presentation: " + ",".join(validation["errors"]))
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
    else:
        if summary.get("failure_lifecycle_values_redacted") is not True or summary.get("current_lifecycle_values_redacted") is not True:
            errors.append("opaque_lifecycle_values_not_redacted")
        if type(summary.get("disposal_recorded")) is not bool or type(summary.get("fresh_instance_boundary_observed")) is not bool:
            errors.append("evidence_summary_boolean_invalid")
        if summary.get("disposal_boundary") is not None and not isinstance(summary.get("disposal_boundary"), str):
            errors.append("evidence_summary_boundary_invalid")
    if value.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}:
        errors.append("negative_capabilities_mismatch")


def _presentation_parity_errors(record: Mapping[str, Any], presentation: Mapping[str, Any]) -> list[str]:
    expected = {
        "source_presentation_status": PRESENTATION_STATUS,
        "source_presentation_digest": _presentation_digest(presentation), "source_scope": presentation["scope"],
        "availability": presentation["availability"], "operator_state": presentation["operator_state"],
        "headline": presentation["headline"], "caveat": presentation["caveat"],
        "current_runtime_quarantined": presentation["current_runtime_quarantined"], "same_adapter_only": True,
        "evidence_summary": presentation["evidence_summary"],
        "artifact_import_diagnostic": presentation.get("artifact_import_diagnostic"),
        "replay_persistence_diagnostic": presentation.get("replay_persistence_diagnostic"),
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "source_do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }
    return [f"presentation_parity_{key}_mismatch" for key, expected_value in expected.items() if record.get(key) != expected_value]


def _presentation_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _export_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value); canonical.pop("export_digest", None)
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
    "MAX_EXPORT_BYTES", "MEDIA_TYPE", "build_worldbridge_quarantine_operator_presentation_export_contract",
    "decode_worldbridge_quarantine_operator_presentation_export_record",
    "encode_worldbridge_quarantine_operator_presentation_export_record",
    "export_worldbridge_quarantine_operator_presentation",
    "validate_worldbridge_quarantine_operator_presentation_export_contract",
    "validate_worldbridge_quarantine_operator_presentation_export_record",
]
