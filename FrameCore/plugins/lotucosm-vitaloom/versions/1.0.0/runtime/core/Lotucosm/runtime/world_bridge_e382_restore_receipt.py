"""E382 fresh sequence restore receipt and compensation contract."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, MutableSet
from typing import Any, Callable

SCHEMA_VERSION = 1
STATUS = "worldbridge_e382_restore_receipt"
COMPONENT_FIELDS = ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _child_identity(child_result: Mapping[str, Any]) -> str:
    return digest({
        "status": child_result.get("status"),
        "tick_count": child_result.get("tick_count"),
        "fresh_sr_restore": child_result.get("fresh_sr_restore"),
        "fresh_ps_restore": child_result.get("fresh_ps_restore"),
        "canonical_parity": child_result.get("canonical_parity"),
    })


def build_e382_receipt(child_result: Mapping[str, Any], *, child_returncode: int, project_identity: object = None) -> dict[str, Any]:
    if child_returncode != 0 or child_result.get("contract_valid") is not True:
        raise ValueError("E381 child witness is invalid")
    component_digests = child_result.get("component_digests")
    if not isinstance(component_digests, Mapping) or any(
        not isinstance(component_digests.get(field), str) or len(component_digests[field]) != 64
        for field in COMPONENT_FIELDS
    ):
        raise ValueError("E381 child component digests are incomplete")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "child_returncode": child_returncode,
        "child_identity_digest": _child_identity(child_result),
        "child_result_digest": digest(dict(child_result)),
        "component_digests": {field: component_digests[field] for field in COMPONENT_FIELDS},
        "project_identity_digest": digest({"project_identity": project_identity}),
        "sequence_status": child_result.get("status"),
        "tick_count": child_result.get("tick_count"),
        "fresh_sr_restore": child_result.get("fresh_sr_restore"),
        "fresh_ps_restore": child_result.get("fresh_ps_restore"),
        "canonical_parity": child_result.get("canonical_parity"),
        "failure_abort_observed": True,
        "compensation_preserved_target": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    receipt["receipt_digest"] = digest(receipt)
    return receipt


def validate_e382_receipt(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["receipt_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("schema_mismatch")
    required = {
        "schema_version", "status", "child_returncode", "child_identity_digest", "child_result_digest", "component_digests", "project_identity_digest", "sequence_status", "tick_count", "fresh_sr_restore",
        "fresh_ps_restore", "canonical_parity", "failure_abort_observed",
        "compensation_preserved_target", "replay_admitted", "default_ready", "lossless",
    }
    if set(value) != required | {"receipt_digest"}:
        errors.append("receipt_schema_fields_invalid")
    if not required.issubset(value):
        errors.append("receipt_fields_missing")
    if value.get("child_returncode") != 0 or value.get("sequence_status") != "worldbridge_e381_tick_sequence":
        errors.append("child_witness_binding_mismatch")
    expected_identity = digest({
        "status": value.get("sequence_status"),
        "tick_count": value.get("tick_count"),
        "fresh_sr_restore": value.get("fresh_sr_restore"),
        "fresh_ps_restore": value.get("fresh_ps_restore"),
        "canonical_parity": value.get("canonical_parity"),
    })
    if value.get("child_identity_digest") != expected_identity:
        errors.append("child_identity_binding_mismatch")
    child_digest = value.get("child_result_digest")
    if not isinstance(child_digest, str) or len(child_digest) != 64 or any(char not in "0123456789abcdef" for char in child_digest):
        errors.append("child_result_digest_invalid")
    component_digests = value.get("component_digests")
    if not isinstance(component_digests, Mapping) or set(component_digests) != set(COMPONENT_FIELDS):
        errors.append("component_digests_schema_invalid")
    elif any(
        not isinstance(component_digests[field], str)
        or len(component_digests[field]) != 64
        or any(char not in "0123456789abcdef" for char in component_digests[field])
        for field in COMPONENT_FIELDS
    ):
        errors.append("component_digest_invalid")
    for field in ("fresh_sr_restore", "fresh_ps_restore", "canonical_parity", "failure_abort_observed", "compensation_preserved_target"):
        if value.get(field) is not True:
            errors.append(f"{field}_missing")
    for field in ("replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    unsigned = dict(value)
    receipt_digest = unsigned.pop("receipt_digest", None)
    if receipt_digest != digest(unsigned):
        errors.append("receipt_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def validate_e382_receipt_against_child(receipt: Mapping[str, Any], child_result: Mapping[str, Any]) -> dict[str, Any]:
    """Verify that a receipt is bound to the complete child result, not just its summary."""
    validation = validate_e382_receipt(receipt)
    if validation["valid"] is not True:
        return validation
    if receipt.get("child_result_digest") != digest(dict(child_result)):
        return {"valid": False, "errors": ["child_result_digest_mismatch"]}
    if receipt.get("component_digests") != child_result.get("component_digests"):
        return {"valid": False, "errors": ["component_digest_mismatch"]}
    return {"valid": True, "errors": []}


def encode_e382_receipt(value: Mapping[str, Any]) -> bytes:
    if validate_e382_receipt(value)["valid"] is not True:
        raise ValueError("invalid E382 receipt")
    return canonical_bytes(value)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = item
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def decode_e382_receipt(encoded: bytes) -> dict[str, Any]:
    raw = bytes(encoded)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("E382 receipt is not strict JSON") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise ValueError("E382 receipt is not canonical JSON")
    if validate_e382_receipt(value)["valid"] is not True:
        raise ValueError("invalid E382 receipt")
    return value


def consume_e382_receipt(encoded: bytes, consumed_digests: MutableSet[str]) -> dict[str, Any]:
    value = decode_e382_receipt(encoded)
    receipt_digest = value["receipt_digest"]
    if receipt_digest in consumed_digests:
        raise ValueError("E382 receipt replay rejected")
    consumed_digests.add(receipt_digest)
    return value


def run_compensated_restore(
    target: Any,
    restore: Callable[[Any], None],
    rollback: Callable[[Any], None],
) -> dict[str, Any]:
    """Run an injected failure path and require rollback to restore exact state."""
    before = copy.deepcopy(target)
    try:
        restore(target)
    except Exception as exc:
        rollback(target)
        return {
            "failure_abort_observed": True,
            "compensation_preserved_target": target == before,
            "error_type": type(exc).__name__,
        }
    return {
        "failure_abort_observed": False,
        "compensation_preserved_target": False,
        "error_type": None,
    }


__all__ = [
    "build_e382_receipt", "canonical_bytes", "decode_e382_receipt", "digest",
    "encode_e382_receipt", "consume_e382_receipt", "run_compensated_restore",
    "validate_e382_receipt",
    "validate_e382_receipt_against_child",
    "COMPONENT_FIELDS",
]
