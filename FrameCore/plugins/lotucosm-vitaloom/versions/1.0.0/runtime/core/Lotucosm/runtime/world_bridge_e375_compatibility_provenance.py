"""Auditable provenance receipt for the E374 compatibility corpus."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_e375_compatibility_provenance"
_REQUIRED_KEYS = {
    "schema_version", "status", "corpus_digest", "python_version",
    "artifact_digest", "integrity_digest", "runtime_artifact_verified",
    "migration_admitted", "replay_admitted", "default_ready", "lossless",
    "provenance_digest",
}


def build_worldbridge_e375_compatibility_provenance(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    python_version = result.get("python")
    if not isinstance(python_version, Sequence) or isinstance(python_version, (str, bytes)):
        raise ValueError("E374 result is missing python version")
    artifact_digest = result.get("artifact_digest")
    integrity_digest = result.get("integrity_digest")
    runtime_verified = isinstance(artifact_digest, str) and isinstance(integrity_digest, str)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "corpus_digest": result.get("corpus_digest"),
        "python_version": [int(value) for value in python_version],
        "artifact_digest": artifact_digest,
        "integrity_digest": integrity_digest,
        "runtime_artifact_verified": runtime_verified,
        "migration_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "provenance_digest": "",
    }
    receipt["provenance_digest"] = _provenance_digest(receipt)
    return copy.deepcopy(receipt)


def validate_worldbridge_e375_compatibility_provenance(
    value: object,
    *,
    expected_corpus_digest: str,
    expected_python: Sequence[int] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["provenance_must_be_mapping"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("provenance_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("provenance_schema_mismatch")
    if value.get("corpus_digest") != expected_corpus_digest:
        errors.append("corpus_digest_mismatch")
    python_version = value.get("python_version")
    if (
        not isinstance(python_version, list)
        or len(python_version) != 3
        or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in python_version)
    ):
        errors.append("python_version_invalid")
    elif expected_python is not None and list(python_version) != list(expected_python):
        errors.append("python_version_mismatch")
    runtime_verified = value.get("runtime_artifact_verified") is True
    if not runtime_verified or not isinstance(value.get("artifact_digest"), str) or not isinstance(value.get("integrity_digest"), str):
        errors.append("runtime_artifact_provenance_missing")
    for field in ("migration_admitted", "replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if value.get("provenance_digest") != _provenance_digest(value):
        errors.append("provenance_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_e375_compatibility_provenance(
    value: Mapping[str, Any],
    *,
    expected_corpus_digest: str,
    expected_python: Sequence[int] | None = None,
) -> bytes:
    validation = validate_worldbridge_e375_compatibility_provenance(
        value,
        expected_corpus_digest=expected_corpus_digest,
        expected_python=expected_python,
    )
    if validation["valid"] is not True:
        raise ValueError("invalid E375 provenance: " + ",".join(validation["errors"]))
    return _canonical(dict(value))


def decode_worldbridge_e375_compatibility_provenance(
    encoded: bytes | bytearray | memoryview,
    *,
    expected_corpus_digest: str,
    expected_python: Sequence[int] | None = None,
) -> dict[str, Any]:
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded provenance must be bytes-like")
    raw = bytes(encoded)
    if not raw:
        raise ValueError("encoded provenance is empty")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("encoded provenance is not strict JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise ValueError("encoded provenance is not canonical JSON")
    validation = validate_worldbridge_e375_compatibility_provenance(
        value,
        expected_corpus_digest=expected_corpus_digest,
        expected_python=expected_python,
    )
    if validation["valid"] is not True:
        raise ValueError("invalid E375 provenance: " + ",".join(validation["errors"]))
    return copy.deepcopy(value)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _provenance_digest(value: Mapping[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("provenance_digest", None)
    return hashlib.sha256(_canonical(unsigned)).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = item
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e375_compatibility_provenance",
    "validate_worldbridge_e375_compatibility_provenance",
    "encode_worldbridge_e375_compatibility_provenance",
    "decode_worldbridge_e375_compatibility_provenance",
]
