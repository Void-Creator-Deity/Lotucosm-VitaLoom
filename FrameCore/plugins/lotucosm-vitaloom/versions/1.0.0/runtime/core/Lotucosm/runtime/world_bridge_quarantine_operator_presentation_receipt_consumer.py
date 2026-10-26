# -*- coding: utf-8 -*-
"""Qt-free E248 consumer for an already validated E247 evidence receipt.

This module consumes evidence only.  It projects receipt/source digests and fixed
parity facts into a bounded in-memory record while explicitly excluding runtime
state reconstruction, replay, restore, persistence, and UI or action authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import (
    ENCODING as RECEIPT_ENCODING,
    MEDIA_TYPE as RECEIPT_MEDIA_TYPE,
    STATUS as RECEIPT_STATUS,
    VISIBLE_FIELD_IDS,
    MAX_RECEIPT_BYTES,
    decode_worldbridge_quarantine_operator_presentation_surface_receipt,
    validate_worldbridge_quarantine_operator_presentation_surface_receipt,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_receipt_consumer"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-receipt-consumer+json"
ENCODING = "utf-8"
MAX_CONSUMER_BYTES = 4 * 1024
SOURCE_SCOPE = "validated_e247_quarantine_presentation_surface_receipt_only"
SOURCE_RECEIPT_SCOPE = "validated_e246_quarantine_presentation_surface_audit_only"
DO_NOT_CLAIM = (
    "quarantine_operator_presentation_receipt_consumer_is_not_runtime_state",
    "quarantine_operator_presentation_receipt_consumer_is_not_checkpoint_state",
    "quarantine_operator_presentation_receipt_consumer_is_not_replay_input",
    "quarantine_operator_presentation_receipt_consumer_is_not_restore_source",
    "quarantine_operator_presentation_receipt_consumer_is_not_recovery",
    "quarantine_operator_presentation_receipt_consumer_is_not_same_runtime_retry",
    "quarantine_operator_presentation_receipt_consumer_is_not_quarantine_clear_authority",
    "quarantine_operator_presentation_receipt_consumer_is_not_persistence_or_file_network_output",
    "quarantine_operator_presentation_receipt_consumer_is_not_ui_or_runtime_action_authority",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "consumer_scope": SOURCE_SCOPE,
    "read_only": True,
    "receipt_integrity_valid": True,
    "source_receipt_consumed": True,
    "receipt_persisted": False,
    "file_written": False,
    "network_transmitted": False,
    "external_artifact_input": False,
    "raw_lifecycle_values_exposed": False,
    "checkpoint_state_consumed": False,
    "replay_cursor_consumed": False,
    "replay_input_admitted": False,
    "replay_admitted": False,
    "restore_admitted": False,
    "recovery_admitted": False,
    "same_runtime_retry_admitted": False,
    "quarantine_clear_admitted": False,
    "mutation_executed": False,
    "runtime_action_authority": False,
    "ui_authority": False,
    "default_ready": False,
}
_REPLAY_EXCLUSION_FACTS = {
    "receipt_is_not_checkpoint": True,
    "receipt_is_not_replay_input": True,
    "receipt_is_not_restore_source": True,
    "consumer_does_not_reconstruct_runtime": True,
    "consumer_does_not_schedule_runtime_action": True,
    "consumer_does_not_persist_or_transmit": True,
}
_RAW_LIFECYCLE_KEYS = frozenset({
    "sr_runtime_epoch",
    "pond_lifetime_token",
    "failure_sr_runtime_epoch",
    "failure_pond_lifetime_token",
    "current_sr_runtime_epoch",
    "current_pond_lifetime_token",
})
_REQUIRED_KEYS = {
    "schema_version", "status", "media_type", "encoding", "canonical_json",
    "source_receipt_status", "source_receipt_scope", "receipt_digest",
    "source_audit_digest", "source_bundle_digest", "visible_field_digest",
    "visible_field_ids", "command_mcp_parity_valid", "inspector_parity_valid",
    "inspector_fields_editable", "replay_exclusion_facts", "do_not_claim",
    "consumer_digest", *_STATIC_POLICIES,
}


def consume_worldbridge_quarantine_operator_presentation_receipt(
    receipt: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Consume one validated E247 receipt into a bounded evidence-only record."""
    source = _validated_receipt(receipt)
    _reject_raw_lifecycle_keys(source, "receipt")
    consumer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_receipt_status": RECEIPT_STATUS,
        "source_receipt_scope": source["receipt_scope"],
        "receipt_digest": source["receipt_digest"],
        "source_audit_digest": source["source_audit_digest"],
        "source_bundle_digest": source["source_bundle_digest"],
        "visible_field_digest": source["visible_field_digest"],
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "command_mcp_parity_valid": True,
        "inspector_parity_valid": True,
        "inspector_fields_editable": False,
        "replay_exclusion_facts": copy.deepcopy(_REPLAY_EXCLUSION_FACTS),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    consumer["consumer_digest"] = _consumer_digest(consumer)
    validation = validate_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer, receipt=source)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine presentation receipt consumer: " + ",".join(validation["errors"]))
    if len(_canonical_json_bytes(consumer)) > MAX_CONSUMER_BYTES:
        raise RuntimeError("quarantine presentation receipt consumer exceeds bounded size")
    return copy.deepcopy(consumer)


def encode_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer: Mapping[str, Any]) -> bytes:
    """Encode one validated consumer record as canonical UTF-8 JSON."""
    validation = validate_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation receipt consumer: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(consumer))
    if len(encoded) > MAX_CONSUMER_BYTES:
        raise ValueError("quarantine presentation receipt consumer exceeds bounded size")
    return bytes(encoded)


def decode_worldbridge_quarantine_operator_presentation_receipt_consumer(
    data: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Decode only canonical, duplicate-key-free consumer JSON."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("consumer data must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_CONSUMER_BYTES:
        raise ValueError("quarantine presentation receipt consumer exceeds bounded size")
    try:
        decoded = json.loads(
            raw.decode(ENCODING),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid canonical quarantine presentation receipt consumer JSON") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError("quarantine presentation receipt consumer must decode to mapping")
    validation = validate_worldbridge_quarantine_operator_presentation_receipt_consumer(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation receipt consumer: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(dict(decoded)) != raw:
        raise ValueError("non-canonical quarantine presentation receipt consumer JSON")
    return copy.deepcopy(dict(decoded))


def validate_worldbridge_quarantine_operator_presentation_receipt_consumer(
    consumer: object,
    *,
    receipt: Mapping[str, Any] | bytes | bytearray | memoryview | None = None,
) -> dict[str, Any]:
    """Fail closed unless the record remains a receipt-only replay exclusion."""
    if not isinstance(consumer, Mapping):
        return {"valid": False, "errors": ["consumer_not_mapping"]}
    try:
        value = copy.deepcopy(dict(consumer))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["consumer_not_copyable"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("consumer_shape_invalid")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("consumer_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("consumer_encoding_mismatch")
    if value.get("source_receipt_status") != RECEIPT_STATUS or value.get("source_receipt_scope") != SOURCE_RECEIPT_SCOPE:
        errors.append("source_receipt_identity_mismatch")
    if value.get("visible_field_ids") != list(VISIBLE_FIELD_IDS):
        errors.append("visible_field_ids_mismatch")
    if value.get("command_mcp_parity_valid") is not True or value.get("inspector_parity_valid") is not True:
        errors.append("surface_parity_missing")
    if value.get("inspector_fields_editable") is not False:
        errors.append("inspector_editability_overclaim")
    if value.get("replay_exclusion_facts") != _REPLAY_EXCLUSION_FACTS:
        errors.append("replay_exclusion_facts_mismatch")
    for key, expected in _STATIC_POLICIES.items():
        actual = value.get(key)
        matches = actual is expected if isinstance(expected, bool) else actual == expected
        if not matches:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    for key in ("receipt_digest", "source_audit_digest", "source_bundle_digest", "visible_field_digest"):
        if not _is_sha256(value.get(key)):
            errors.append(f"{key}_invalid")
    if value.get("consumer_digest") != _consumer_digest(value):
        errors.append("consumer_digest_mismatch")
    if not _is_json_value(value):
        errors.append("consumer_non_json_value")
    elif len(_canonical_json_bytes(value)) > MAX_CONSUMER_BYTES:
        errors.append("consumer_too_large")
    _reject_raw_lifecycle_keys(value, "consumer", errors)
    if receipt is not None:
        try:
            source = _validated_receipt(receipt)
        except (TypeError, ValueError):
            errors.append("source_receipt_invalid")
        else:
            for consumer_key, source_key in (
                ("receipt_digest", "receipt_digest"),
                ("source_audit_digest", "source_audit_digest"),
                ("source_bundle_digest", "source_bundle_digest"),
                ("visible_field_digest", "visible_field_digest"),
            ):
                if value.get(consumer_key) != source.get(source_key):
                    errors.append(f"source_{consumer_key}_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract() -> dict[str, Any]:
    """Return the static E248 receipt-only replay-exclusion contract."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "source_receipt_status": RECEIPT_STATUS,
        "source_scope": SOURCE_SCOPE,
        "source_receipt_scope": SOURCE_RECEIPT_SCOPE,
        "media_type": MEDIA_TYPE,
        "max_consumer_bytes": MAX_CONSUMER_BYTES,
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "replay_exclusion_facts": copy.deepcopy(_REPLAY_EXCLUSION_FACTS),
        "do_not_claim": list(DO_NOT_CLAIM),
        "accepts_only_validated_receipt": True,
        "raw_lifecycle_values_exposed": False,
        "runtime_state_reconstructed": False,
        "contract_valid": True,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != STATUS:
        errors.append("contract_identity_mismatch")
    if contract.get("source_receipt_status") != RECEIPT_STATUS or contract.get("source_scope") != SOURCE_SCOPE or contract.get("source_receipt_scope") != SOURCE_RECEIPT_SCOPE:
        errors.append("contract_source_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_consumer_bytes") != MAX_CONSUMER_BYTES:
        errors.append("contract_media_or_size_mismatch")
    if contract.get("visible_field_ids") != list(VISIBLE_FIELD_IDS):
        errors.append("contract_visible_fields_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES:
        errors.append("contract_policy_mismatch")
    if contract.get("replay_exclusion_facts") != _REPLAY_EXCLUSION_FACTS:
        errors.append("contract_replay_exclusion_mismatch")
    if contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_claim_mismatch")
    if contract.get("accepts_only_validated_receipt") is not True or contract.get("raw_lifecycle_values_exposed") is not False:
        errors.append("contract_input_or_lifecycle_mismatch")
    if contract.get("runtime_state_reconstructed") is not False or contract.get("contract_valid") is not True:
        errors.append("contract_authority_mismatch")
    return {"valid": not errors, "errors": errors}


def _validated_receipt(value: object) -> dict[str, Any]:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return decode_worldbridge_quarantine_operator_presentation_surface_receipt(value)
    if not isinstance(value, Mapping):
        raise TypeError("receipt must be mapping or canonical bytes")
    copied = copy.deepcopy(dict(value))
    validation = validate_worldbridge_quarantine_operator_presentation_surface_receipt(copied)
    if validation["valid"] is not True:
        raise ValueError("invalid quarantine presentation surface receipt: " + ",".join(validation["errors"]))
    return copied


def _consumer_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("consumer_digest", None)
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


def _reject_raw_lifecycle_keys(value: object, name: str, errors: list[str] | None = None) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _RAW_LIFECYCLE_KEYS:
                if errors is None:
                    raise ValueError(f"{name} exposes raw lifecycle key: {key}")
                errors.append(f"{name}_raw_lifecycle_key_{key}")
            _reject_raw_lifecycle_keys(item, name, errors)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_lifecycle_keys(item, name, errors)


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
    "DO_NOT_CLAIM", "ENCODING", "MAX_CONSUMER_BYTES", "MAX_RECEIPT_BYTES", "MEDIA_TYPE", "SOURCE_RECEIPT_SCOPE", "SOURCE_SCOPE", "STATUS",
    "build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract",
    "consume_worldbridge_quarantine_operator_presentation_receipt",
    "decode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "encode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "validate_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract",
]


