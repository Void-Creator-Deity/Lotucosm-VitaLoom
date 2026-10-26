"""Canonical receipt artifact for explicit component identity evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = 1
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
ENCODING = "utf-8"
_REQUIRED_PROVENANCE_KEYS = {
    "source_kind",
    "runtime_status",
    "receipt_corpus_digest",
    "artifact_schema_version",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode(ENCODING)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _receipt_corpus_digest(receipts: list[dict[str, Any]]) -> str:
    return _digest(receipts)


def _default_provenance(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_kind": "worldbridge_component_identity_receipt_corpus",
        "runtime_status": "captured_diagnostic_only",
        "receipt_corpus_digest": _receipt_corpus_digest(receipts),
        "artifact_schema_version": SCHEMA_VERSION,
    }


def build_worldbridge_component_identity_artifact(
    *,
    receipts: Sequence[Mapping[str, Any]],
    duplicate_rejected: bool,
    owner_drift_rejected: bool,
    rollback_succeeded: bool,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    records = [copy.deepcopy(dict(item)) for item in receipts]
    records.sort(key=lambda item: (str(item.get("generation", "")), str(item.get("hub_id", ""))))
    artifact: dict[str, Any] = {
        "schema_version": 1,
        "status": "worldbridge_component_identity_artifact",
        "receipt_count": len(records),
        "receipts": records,
        "receipt_digests": [_digest(item) for item in records],
        "provenance": copy.deepcopy(
            dict(provenance) if provenance is not None else _default_provenance(records)
        ),
        "duplicate_rejected": bool(duplicate_rejected),
        "owner_drift_rejected": bool(owner_drift_rejected),
        "rollback_succeeded": bool(rollback_succeeded),
        "admission": {"component_relation_admitted": False, "replay_admitted": False, "default_ready": False},
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _digest(artifact)
    return artifact


def validate_worldbridge_component_identity_artifact(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_must_be_mapping"]}
    required = {
        "schema_version", "status", "receipt_count", "receipts", "receipt_digests", "provenance",
        "duplicate_rejected", "owner_drift_rejected", "rollback_succeeded", "admission", "artifact_digest",
    }
    if set(value) != required:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != 1 or value.get("status") != "worldbridge_component_identity_artifact":
        errors.append("artifact_identity_mismatch")
    receipts = value.get("receipts")
    digests = value.get("receipt_digests")
    if not isinstance(receipts, list) or not isinstance(digests, list) or len(receipts) != len(digests):
        errors.append("receipt_corpus_invalid")
    else:
        if value.get("receipt_count") != len(receipts):
            errors.append("receipt_count_mismatch")
        if digests != [_digest(item) for item in receipts]:
            errors.append("receipt_digest_mismatch")
        if receipts != sorted(receipts, key=lambda item: (str(item.get("generation", "")), str(item.get("hub_id", "")))):
            errors.append("receipt_order_drift")
    provenance = value.get("provenance")
    if not isinstance(provenance, Mapping) or set(provenance) != _REQUIRED_PROVENANCE_KEYS:
        errors.append("provenance_keys_mismatch")
    else:
        if not isinstance(provenance.get("source_kind"), str) or not provenance["source_kind"].strip():
            errors.append("provenance_source_kind_invalid")
        if not isinstance(provenance.get("runtime_status"), str) or not provenance["runtime_status"].strip():
            errors.append("provenance_runtime_status_invalid")
        if provenance.get("receipt_corpus_digest") != _receipt_corpus_digest(receipts if isinstance(receipts, list) else []):
            errors.append("provenance_receipt_corpus_digest_mismatch")
        if provenance.get("artifact_schema_version") != SCHEMA_VERSION:
            errors.append("provenance_schema_version_mismatch")
    for field in ("duplicate_rejected", "owner_drift_rejected", "rollback_succeeded"):
        if value.get(field) is not True:
            errors.append(f"{field}_required")
    admission = value.get("admission")
    if not isinstance(admission, Mapping) or admission != {"component_relation_admitted": False, "replay_admitted": False, "default_ready": False}:
        errors.append("admission_quarantine_drift")
    expected = _digest({**dict(value), "artifact_digest": ""})
    if value.get("artifact_digest") != expected:
        errors.append("artifact_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_component_identity_artifact(
    value: Mapping[str, Any], *, max_bytes: int = MAX_ARTIFACT_BYTES
) -> bytes:
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_component_identity_artifact(value)
    if not validation["valid"]:
        raise ValueError("invalid component identity artifact: " + ",".join(validation["errors"]))
    encoded = _canonical(dict(value))
    if len(encoded) > limit:
        raise OverflowError(f"component identity artifact exceeds {limit} bytes")
    return encoded


def decode_worldbridge_component_identity_artifact(
    encoded: bytes | bytearray | memoryview, *, max_bytes: int = MAX_ARTIFACT_BYTES
) -> dict[str, Any]:
    limit = _byte_limit(max_bytes)
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded artifact must be bytes-like")
    raw = bytes(encoded)
    if not raw:
        raise ValueError("encoded artifact must not be empty")
    if len(raw) > limit:
        raise OverflowError(f"component identity artifact exceeds {limit} bytes")
    try:
        text = raw.decode(ENCODING, errors="strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded artifact is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded artifact root must be an object")
    validation = validate_worldbridge_component_identity_artifact(parsed)
    if not validation["valid"]:
        raise ValueError("invalid component identity artifact: " + ",".join(validation["errors"]))
    if _canonical(parsed) != raw:
        raise ValueError("encoded artifact is not canonical JSON")
    return copy.deepcopy(parsed)


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _byte_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ARTIFACT_BYTES:
        raise ValueError(f"max_bytes must be an integer from 1 to {MAX_ARTIFACT_BYTES}")
    return value


__all__ = [
    "MAX_ARTIFACT_BYTES",
    "build_worldbridge_component_identity_artifact",
    "decode_worldbridge_component_identity_artifact",
    "encode_worldbridge_component_identity_artifact",
    "validate_worldbridge_component_identity_artifact",
]
