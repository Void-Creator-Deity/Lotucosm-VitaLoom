"""Unified canonical transport for checkpoint, persistence, and admission evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_component_identity_persistence import (
    validate_worldbridge_component_identity_persistence_envelope,
)
from .world_bridge_live_checkpoint import validate_worldbridge_live_checkpoint
from .world_bridge_live_checkpoint_admission import (
    validate_worldbridge_live_checkpoint_admission_witness,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_checkpoint_artifact"
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "checkpoint",
    "persistence_envelope",
    "admission_witness",
    "checkpoint_digest",
    "persistence_digest",
    "witness_digest",
    "artifact_digest",
}


def build_worldbridge_checkpoint_artifact(
    *,
    checkpoint: Mapping[str, Any],
    persistence_envelope: Mapping[str, Any],
    admission_witness: Mapping[str, Any],
) -> dict[str, Any]:
    _require_valid(checkpoint, validate_worldbridge_live_checkpoint, "checkpoint")
    _require_valid(
        persistence_envelope,
        validate_worldbridge_component_identity_persistence_envelope,
        "persistence envelope",
    )
    _require_valid(
        admission_witness,
        validate_worldbridge_live_checkpoint_admission_witness,
        "admission witness",
    )
    checkpoint_copy = copy.deepcopy(dict(checkpoint))
    persistence_copy = copy.deepcopy(dict(persistence_envelope))
    witness_copy = copy.deepcopy(dict(admission_witness))
    _validate_cross_links(checkpoint_copy, persistence_copy, witness_copy)
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "checkpoint": checkpoint_copy,
        "persistence_envelope": persistence_copy,
        "admission_witness": witness_copy,
        "checkpoint_digest": _digest(checkpoint_copy),
        "persistence_digest": _digest(persistence_copy),
        "witness_digest": _digest(witness_copy),
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _artifact_digest(artifact)
    _ensure_size(artifact)
    return artifact


def validate_worldbridge_checkpoint_artifact(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_must_be_mapping"]}
    if set(value) != _REQUIRED_KEYS:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    for name, validator in (
        ("checkpoint", validate_worldbridge_live_checkpoint),
        ("persistence_envelope", validate_worldbridge_component_identity_persistence_envelope),
        ("admission_witness", validate_worldbridge_live_checkpoint_admission_witness),
    ):
        nested = value.get(name)
        try:
            result = validator(nested)
        except (TypeError, ValueError, KeyError):
            result = {"valid": False}
        if result.get("valid") is not True:
            errors.append(f"{name}_invalid")
    for field, nested_name in (
        ("checkpoint_digest", "checkpoint"),
        ("persistence_digest", "persistence_envelope"),
        ("witness_digest", "admission_witness"),
    ):
        if value.get(field) != _digest(value.get(nested_name)):
            errors.append(f"{field}_mismatch")
    try:
        _validate_cross_links(
            value.get("checkpoint"),
            value.get("persistence_envelope"),
            value.get("admission_witness"),
        )
    except (TypeError, ValueError):
        errors.append("cross_links_invalid")
    if value.get("artifact_digest") != _artifact_digest(value):
        errors.append("artifact_digest_mismatch")
    try:
        _ensure_size(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("artifact_size_invalid")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_checkpoint_artifact(
    value: Mapping[str, Any], *, max_bytes: int = MAX_ARTIFACT_BYTES
) -> bytes:
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_checkpoint_artifact(value)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge checkpoint artifact: " + ",".join(validation["errors"]))
    encoded = _canonical(value)
    if len(encoded) > limit:
        raise OverflowError(f"worldbridge checkpoint artifact exceeds {limit} bytes")
    return encoded


def decode_worldbridge_checkpoint_artifact(
    encoded: bytes | bytearray | memoryview, *, max_bytes: int = MAX_ARTIFACT_BYTES
) -> dict[str, Any]:
    limit = _byte_limit(max_bytes)
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded artifact must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > limit:
        raise ValueError("encoded checkpoint artifact is empty or exceeds its byte limit")
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded checkpoint artifact is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded checkpoint artifact root must be an object")
    validation = validate_worldbridge_checkpoint_artifact(parsed)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge checkpoint artifact: " + ",".join(validation["errors"]))
    if _canonical(parsed) != raw:
        raise ValueError("encoded checkpoint artifact is not canonical JSON")
    return copy.deepcopy(parsed)


def _validate_cross_links(
    checkpoint: Mapping[str, Any],
    persistence: Mapping[str, Any],
    witness: Mapping[str, Any],
) -> None:
    if not isinstance(checkpoint, Mapping):
        raise ValueError("checkpoint is not a mapping")
    if not isinstance(persistence, Mapping):
        raise ValueError("persistence envelope is not a mapping")
    if not isinstance(witness, Mapping):
        raise ValueError("admission witness is not a mapping")
    checkpoint_id = checkpoint.get("checkpoint_id")
    checkpoint_digest = _digest(checkpoint)
    identity = witness.get("checkpoint_identity")
    if not isinstance(identity, Mapping):
        raise ValueError("admission witness checkpoint identity is missing")
    if identity.get("checkpoint_id") != checkpoint_id or identity.get("digest") != checkpoint.get("digest"):
        raise ValueError("admission witness checkpoint identity drift")
    diagnostic = witness.get("restore_diagnostic")
    persisted_diagnostic = persistence.get("restore_diagnostic")
    if persisted_diagnostic is not None:
        if diagnostic != persisted_diagnostic:
            raise ValueError("persistence and witness diagnostic drift")
        if diagnostic.get("checkpoint_id") != checkpoint_id or diagnostic.get("checkpoint_digest") != checkpoint.get("digest"):
            raise ValueError("diagnostic checkpoint identity drift")
    if persistence.get("artifact_digest") != _digest(persistence.get("artifact")):
        raise ValueError("persistence nested artifact digest drift")
    if checkpoint_digest == "":
        raise ValueError("checkpoint digest is empty")


def _require_valid(value: Mapping[str, Any], validator: Any, name: str) -> None:
    result = validator(value)
    if result.get("valid") is not True:
        raise ValueError(f"invalid {name}: " + ",".join(result.get("errors", [])))


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _artifact_digest(value: Mapping[str, Any]) -> str:
    return _digest({**dict(value), "artifact_digest": ""})


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _byte_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ARTIFACT_BYTES:
        raise ValueError(f"max_bytes must be an integer from 1 to {MAX_ARTIFACT_BYTES}")
    return value


def _ensure_size(value: object) -> None:
    if len(_canonical(value)) > MAX_ARTIFACT_BYTES:
        raise OverflowError(f"worldbridge checkpoint artifact exceeds {MAX_ARTIFACT_BYTES} bytes")


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "MAX_ARTIFACT_BYTES",
    "build_worldbridge_checkpoint_artifact",
    "decode_worldbridge_checkpoint_artifact",
    "encode_worldbridge_checkpoint_artifact",
    "validate_worldbridge_checkpoint_artifact",
]
