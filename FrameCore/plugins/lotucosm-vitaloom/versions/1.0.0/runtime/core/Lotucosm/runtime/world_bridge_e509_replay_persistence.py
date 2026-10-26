"""Project-bound persistence envelope for the E508 replay corpus."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_bridge_e508_fresh_replay_corpus import (
    decode_worldbridge_e508_fresh_replay_corpus,
    encode_worldbridge_e508_fresh_replay_corpus,
    validate_worldbridge_e508_fresh_replay_corpus,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e509_replay_persistence_envelope"
MAX_ENVELOPE_BYTES = 64 * 1024 * 1024
_REQUIRED_KEYS = {
    "schema_version", "status", "project_path", "project_lock_digest", "scene_path",
    "checkpoint_digest", "corpus_digest", "corpus", "restore_diagnostic", "envelope_digest",
}


def build_worldbridge_e509_replay_persistence_envelope(
    *,
    project_path: str,
    project_lock: Mapping[str, Any],
    scene_path: str,
    corpus: Mapping[str, Any],
    restore_diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    _clean_context(project_path, "project_path")
    _clean_context(scene_path, "scene_path")
    lock_copy = _mapping_copy(project_lock, "project_lock")
    _validate_corpus(corpus)
    diagnostic = _copy_diagnostic(restore_diagnostic)
    corpus_copy = copy.deepcopy(dict(corpus))
    envelope: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "project_path": project_path,
        "project_lock_digest": _digest(lock_copy),
        "scene_path": scene_path,
        "checkpoint_digest": corpus_copy["checkpoint_digest"],
        "corpus_digest": corpus_copy["corpus_digest"],
        "corpus": corpus_copy,
        "restore_diagnostic": diagnostic,
        "envelope_digest": "",
    }
    envelope["envelope_digest"] = _envelope_digest(envelope)
    _ensure_size(envelope)
    return envelope


def validate_worldbridge_e509_replay_persistence_envelope(
    value: object,
    *,
    project_path: str | None = None,
    project_lock: Mapping[str, Any] | None = None,
    scene_path: str | None = None,
    checkpoint_digest: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["envelope_not_mapping"]}
    if set(value) != _REQUIRED_KEYS:
        errors.append("envelope_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    for field in ("project_path", "scene_path"):
        try:
            _clean_context(value.get(field), field)
        except ValueError:
            errors.append(f"{field}_invalid")
    corpus = value.get("corpus")
    corpus_validation = validate_worldbridge_e508_fresh_replay_corpus(corpus)
    if corpus_validation["valid"] is not True:
        errors.append("corpus_invalid")
    else:
        if value.get("checkpoint_digest") != corpus["checkpoint_digest"]:
            errors.append("checkpoint_digest_binding_mismatch")
        if value.get("corpus_digest") != corpus["corpus_digest"]:
            errors.append("corpus_digest_binding_mismatch")
    diagnostic = value.get("restore_diagnostic")
    try:
        _copy_diagnostic(diagnostic)
    except (TypeError, ValueError):
        errors.append("restore_diagnostic_invalid")
    if project_path is not None and value.get("project_path") != project_path:
        errors.append("project_path_binding_mismatch")
    if scene_path is not None and value.get("scene_path") != scene_path:
        errors.append("scene_path_binding_mismatch")
    if checkpoint_digest is not None and value.get("checkpoint_digest") != checkpoint_digest:
        errors.append("checkpoint_digest_context_mismatch")
    if project_lock is not None:
        try:
            expected = _digest(_mapping_copy(project_lock, "project_lock"))
        except (TypeError, ValueError):
            errors.append("project_lock_invalid")
        else:
            if value.get("project_lock_digest") != expected:
                errors.append("project_lock_binding_mismatch")
    for field in ("project_lock_digest", "checkpoint_digest", "corpus_digest", "envelope_digest"):
        if not _is_digest(value.get(field)):
            errors.append(f"{field}_invalid")
    try:
        if value.get("envelope_digest") != _envelope_digest(value):
            errors.append("envelope_digest_mismatch")
    except (TypeError, ValueError):
        errors.append("envelope_digest_uncomputable")
    try:
        _ensure_size(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("envelope_size_invalid")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_e509_replay_persistence_envelope(value: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_e509_replay_persistence_envelope(value)
    if validation["valid"] is not True:
        raise ValueError("invalid E509 persistence envelope: " + ",".join(validation["errors"]))
    return _canonical(value)


def decode_worldbridge_e509_replay_persistence_envelope(
    encoded: bytes | bytearray | memoryview,
    *,
    project_path: str | None = None,
    project_lock: Mapping[str, Any] | None = None,
    scene_path: str | None = None,
    checkpoint_digest: str | None = None,
) -> dict[str, Any]:
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded E509 envelope must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError("encoded E509 envelope is empty or exceeds its byte limit")
    try:
        parsed = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded E509 envelope is not strict UTF-8 JSON") from exc
    validation = validate_worldbridge_e509_replay_persistence_envelope(
        parsed, project_path=project_path, project_lock=project_lock,
        scene_path=scene_path, checkpoint_digest=checkpoint_digest,
    )
    if validation["valid"] is not True:
        raise ValueError("invalid E509 persistence envelope: " + ",".join(validation["errors"]))
    if _canonical(parsed) != raw:
        raise ValueError("encoded E509 envelope is not canonical JSON")
    return copy.deepcopy(parsed)


def write_worldbridge_e509_replay_persistence_envelope(path: str | Path, value: Mapping[str, Any]) -> Path:
    encoded = encode_worldbridge_e509_replay_persistence_envelope(value)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(encoded)
    temporary.replace(target)
    return target


def read_worldbridge_e509_replay_persistence_envelope(path: str | Path, **bindings: Any) -> dict[str, Any]:
    return decode_worldbridge_e509_replay_persistence_envelope(Path(path).read_bytes(), **bindings)


def _validate_corpus(value: Mapping[str, Any]) -> None:
    result = validate_worldbridge_e508_fresh_replay_corpus(value)
    if result["valid"] is not True:
        raise ValueError("invalid E508 corpus: " + ",".join(result["errors"]))


def _copy_diagnostic(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("restore diagnostic must be a mapping")
    required = {"schema_version", "code", "errors", "checkpoint_id", "checkpoint_digest", "diagnostic_digest"}
    if set(value) != required or value.get("schema_version") != 1:
        raise ValueError("restore diagnostic schema mismatch")
    if not isinstance(value.get("code"), str) or not value["code"].strip():
        raise ValueError("restore diagnostic code invalid")
    if not isinstance(value.get("errors"), list) or any(not isinstance(item, str) or not item.strip() for item in value["errors"]):
        raise ValueError("restore diagnostic errors invalid")
    if not isinstance(value.get("checkpoint_id"), str) or not _is_digest(value.get("checkpoint_digest")):
        raise ValueError("restore diagnostic checkpoint identity invalid")
    payload = {key: value[key] for key in required if key != "diagnostic_digest"}
    if value.get("diagnostic_digest") != _digest(payload):
        raise ValueError("restore diagnostic digest mismatch")
    return json.loads(_canonical(dict(value)).decode("utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _envelope_digest(value: Mapping[str, Any]) -> str:
    return _digest({**dict(value), "envelope_digest": ""})


def _mapping_copy(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    result = json.loads(_canonical(value).decode("utf-8"))
    if not isinstance(result, dict):
        raise TypeError(f"{field} must be a mapping")
    return result


def _clean_context(value: object, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 4096:
        raise ValueError(f"{field} invalid")


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _ensure_size(value: object) -> None:
    if len(_canonical(value)) > MAX_ENVELOPE_BYTES:
        raise OverflowError("E509 persistence envelope exceeds its byte limit")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "build_worldbridge_e509_replay_persistence_envelope",
    "decode_worldbridge_e509_replay_persistence_envelope",
    "encode_worldbridge_e509_replay_persistence_envelope",
    "read_worldbridge_e509_replay_persistence_envelope",
    "validate_worldbridge_e509_replay_persistence_envelope",
    "write_worldbridge_e509_replay_persistence_envelope",
]
