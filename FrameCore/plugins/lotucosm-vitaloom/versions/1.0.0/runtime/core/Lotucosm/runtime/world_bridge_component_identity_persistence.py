"""Project-bound persistence envelope for component identity diagnostic artifacts."""
from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_bridge_component_identity_artifact import (
    decode_worldbridge_component_identity_artifact,
    encode_worldbridge_component_identity_artifact,
    validate_worldbridge_component_identity_artifact,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_component_identity_persistence_envelope"
MAX_ENVELOPE_BYTES = 32 * 1024 * 1024
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "project_path",
    "project_lock_digest",
    "runtime_epoch",
    "scene_path",
    "artifact",
    "artifact_digest",
    "envelope_digest",
}
_RUNTIME_BINDING_KEYS = {
    "schema_version", "project_path", "project_lock_digest", "runtime_epoch", "scene_path"
}


def build_worldbridge_project_runtime_binding(
    *, project_path: str, project_lock: Mapping[str, Any], runtime_epoch: str, scene_path: str
) -> dict[str, Any]:
    _clean_context(project_path, "project_path")
    _clean_context(runtime_epoch, "runtime_epoch")
    _clean_context(scene_path, "scene_path")
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": project_path,
        "project_lock_digest": _digest(_json_mapping_copy(project_lock, "project_lock")),
        "runtime_epoch": runtime_epoch,
        "scene_path": scene_path,
    }


def validate_worldbridge_project_runtime_binding(
    value: object, *, project_path: str, project_lock: Mapping[str, Any],
    runtime_epoch: str, scene_path: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping) or set(value) != _RUNTIME_BINDING_KEYS:
        return {"valid": False, "errors": ["runtime_binding_keys_mismatch"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("runtime_binding_schema_version_mismatch")
    expected = build_worldbridge_project_runtime_binding(
        project_path=project_path, project_lock=project_lock,
        runtime_epoch=runtime_epoch, scene_path=scene_path,
    )
    for field in _RUNTIME_BINDING_KEYS:
        if value.get(field) != expected[field]:
            errors.append(f"runtime_binding_{field}_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_component_identity_persistence_envelope(
    *,
    project_path: str,
    project_lock: Mapping[str, Any],
    runtime_epoch: str,
    scene_path: str,
    artifact: Mapping[str, Any],
    restore_diagnostic: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _clean_context(project_path, "project_path")
    _clean_context(runtime_epoch, "runtime_epoch")
    _clean_context(scene_path, "scene_path")
    artifact_validation = validate_worldbridge_component_identity_artifact(artifact)
    if not artifact_validation["valid"]:
        raise ValueError("invalid component identity artifact: " + ",".join(artifact_validation["errors"]))
    lock_copy = _json_mapping_copy(project_lock, "project_lock")
    artifact_bytes = encode_worldbridge_component_identity_artifact(artifact)
    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "project_path": project_path,
        "project_lock_digest": _digest(lock_copy),
        "runtime_epoch": runtime_epoch,
        "scene_path": scene_path,
        "artifact": json.loads(artifact_bytes.decode("utf-8")),
        "artifact_digest": hashlib.sha256(artifact_bytes).hexdigest(),
        "envelope_digest": "",
    }
    if restore_diagnostic is not None:
        envelope["restore_diagnostic"] = _copy_restore_diagnostic(restore_diagnostic)
    envelope["envelope_digest"] = _envelope_digest(envelope)
    _ensure_size(envelope)
    return envelope


def validate_worldbridge_component_identity_persistence_envelope(
    value: object,
    *,
    project_path: str | None = None,
    project_lock: Mapping[str, Any] | None = None,
    runtime_epoch: str | None = None,
    scene_path: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["envelope_must_be_mapping"]}
    if not _REQUIRED_KEYS.issubset(set(value)) or set(value) - _REQUIRED_KEYS - {"restore_diagnostic"}:
        errors.append("envelope_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    for field in ("project_path", "runtime_epoch", "scene_path"):
        try:
            _clean_context(value.get(field), field)
        except ValueError:
            errors.append(f"{field}_invalid")
    artifact = value.get("artifact")
    artifact_validation = validate_worldbridge_component_identity_artifact(artifact)
    if not artifact_validation["valid"]:
        errors.append("nested_artifact_invalid")
    try:
        artifact_bytes = encode_worldbridge_component_identity_artifact(artifact)
    except (TypeError, ValueError, OverflowError):
        artifact_bytes = None
        errors.append("artifact_not_canonicalizable")
    if artifact_bytes is not None and value.get("artifact_digest") != hashlib.sha256(artifact_bytes).hexdigest():
        errors.append("artifact_digest_mismatch")
    if project_path is not None and value.get("project_path") != project_path:
        errors.append("project_path_binding_mismatch")
    if runtime_epoch is not None and value.get("runtime_epoch") != runtime_epoch:
        errors.append("runtime_epoch_binding_mismatch")
    if scene_path is not None and value.get("scene_path") != scene_path:
        errors.append("scene_path_binding_mismatch")
    if project_lock is not None:
        try:
            expected_lock_digest = _digest(_json_mapping_copy(project_lock, "project_lock"))
        except (TypeError, ValueError):
            errors.append("project_lock_invalid")
        else:
            if value.get("project_lock_digest") != expected_lock_digest:
                errors.append("project_lock_binding_mismatch")
    if not _is_sha256(value.get("project_lock_digest")):
        errors.append("project_lock_digest_invalid")
    if not _is_sha256(value.get("artifact_digest")):
        errors.append("artifact_digest_invalid")
    if not _is_sha256(value.get("envelope_digest")):
        errors.append("envelope_digest_invalid")
    else:
        try:
            if value["envelope_digest"] != _envelope_digest(value):
                errors.append("envelope_digest_mismatch")
        except (TypeError, ValueError):
            errors.append("envelope_digest_uncomputable")
    if "restore_diagnostic" in value:
        try:
            _copy_restore_diagnostic(value["restore_diagnostic"])
        except (TypeError, ValueError):
            errors.append("restore_diagnostic_invalid")
    try:
        _ensure_size(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("envelope_size_invalid")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_component_identity_persistence_envelope(
    value: Mapping[str, Any], *, max_bytes: int = MAX_ENVELOPE_BYTES
) -> bytes:
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_component_identity_persistence_envelope(value)
    if not validation["valid"]:
        raise ValueError("invalid component identity persistence envelope: " + ",".join(validation["errors"]))
    encoded = _canonical(value)
    if len(encoded) > limit:
        raise OverflowError(f"component identity persistence envelope exceeds {limit} bytes")
    return encoded


def decode_worldbridge_component_identity_persistence_envelope(
    encoded: bytes | bytearray | memoryview,
    *,
    project_path: str | None = None,
    project_lock: Mapping[str, Any] | None = None,
    runtime_epoch: str | None = None,
    scene_path: str | None = None,
    max_bytes: int = MAX_ENVELOPE_BYTES,
) -> dict[str, Any]:
    limit = _byte_limit(max_bytes)
    raw = bytes(encoded) if isinstance(encoded, (bytes, bytearray, memoryview)) else None
    if raw is None:
        raise TypeError("encoded envelope must be bytes-like")
    if not raw or len(raw) > limit:
        raise ValueError("encoded envelope is empty or exceeds its byte limit")
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded envelope is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded envelope root must be an object")
    validation = validate_worldbridge_component_identity_persistence_envelope(
        parsed,
        project_path=project_path,
        project_lock=project_lock,
        runtime_epoch=runtime_epoch,
        scene_path=scene_path,
    )
    if not validation["valid"]:
        raise ValueError("invalid component identity persistence envelope: " + ",".join(validation["errors"]))
    if _canonical(parsed) != raw:
        raise ValueError("encoded envelope is not canonical JSON")
    return parsed


def write_worldbridge_component_identity_persistence_envelope(
    path: str | Path, envelope: Mapping[str, Any]
) -> Path:
    encoded = encode_worldbridge_component_identity_persistence_envelope(envelope)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, target)
    return target


def read_worldbridge_component_identity_persistence_envelope(
    path: str | Path, **bindings: Any
) -> dict[str, Any]:
    return decode_worldbridge_component_identity_persistence_envelope(
        Path(path).read_bytes(), **bindings
    )


def _json_mapping_copy(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = json.loads(_canonical(value).decode("utf-8"))
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must be a mapping")
    return copied


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _envelope_digest(value: Mapping[str, Any]) -> str:
    return _digest({**dict(value), "envelope_digest": ""})


def _clean_context(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 4096:
        raise ValueError(f"{field} must be a clean non-empty string")
    return value


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _byte_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ENVELOPE_BYTES:
        raise ValueError(f"max_bytes must be an integer from 1 to {MAX_ENVELOPE_BYTES}")
    return value


def _ensure_size(value: object) -> None:
    if len(_canonical(value)) > MAX_ENVELOPE_BYTES:
        raise OverflowError(f"component identity persistence envelope exceeds {MAX_ENVELOPE_BYTES} bytes")


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _copy_restore_diagnostic(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("restore diagnostic must be a mapping")
    required = {"schema_version", "code", "errors", "checkpoint_id", "checkpoint_digest", "diagnostic_digest"}
    if set(value) != required or value.get("schema_version") != 1:
        raise ValueError("restore diagnostic schema mismatch")
    if not isinstance(value.get("code"), str) or not value["code"].strip():
        raise ValueError("restore diagnostic code invalid")
    if not isinstance(value.get("errors"), list) or any(
        not isinstance(item, str) or not item.strip() for item in value["errors"]
    ):
        raise ValueError("restore diagnostic errors invalid")
    if not isinstance(value.get("checkpoint_id"), str) or not isinstance(value.get("checkpoint_digest"), str):
        raise ValueError("restore diagnostic checkpoint identity invalid")
    payload = {key: value[key] for key in required if key != "diagnostic_digest"}
    expected = hashlib.sha256(_canonical(payload)).hexdigest()
    if value.get("diagnostic_digest") != expected:
        raise ValueError("restore diagnostic digest mismatch")
    return json.loads(_canonical(dict(value)).decode("utf-8"))


__all__ = [
    "MAX_ENVELOPE_BYTES",
    "build_worldbridge_component_identity_persistence_envelope",
    "build_worldbridge_project_runtime_binding",
    "decode_worldbridge_component_identity_persistence_envelope",
    "encode_worldbridge_component_identity_persistence_envelope",
    "read_worldbridge_component_identity_persistence_envelope",
    "validate_worldbridge_component_identity_persistence_envelope",
    "validate_worldbridge_project_runtime_binding",
    "write_worldbridge_component_identity_persistence_envelope",
]
