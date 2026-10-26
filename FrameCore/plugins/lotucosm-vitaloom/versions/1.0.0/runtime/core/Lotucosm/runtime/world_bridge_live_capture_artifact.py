# -*- coding: utf-8 -*-
"""Qt-free canonical artifact envelope for one sealed WorldBridge capture session."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_live_capture_session import (
    build_worldbridge_live_capture_session_contract,
    validate_worldbridge_live_capture_session,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_sealed_live_comparability_capture_artifact"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-live-capture+json"
ENCODING = "utf-8"
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_ARTIFACT_ID_LENGTH = 128
DO_NOT_CLAIM = (
    "artifact_replay_input",
    "scene_or_pond_checkpoint",
    "session_persistence_authority",
    "common_sr_ps_time_alignment",
    "cross_sample_causality",
    "atomic_sr_ps_checkpoint",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "artifact_scope": "offline_diagnostic_transport_only",
    "replay_input": False,
    "checkpoint_state": False,
    "persistence_authority": False,
    "clocks_compared": False,
    "time_aligned": False,
    "causality_inferred": False,
    "atomic_checkpoint": False,
    "lossless": False,
    "replay_admitted": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "artifact_id",
    "media_type",
    "encoding",
    "canonical_json",
    "payload_schema",
    "payload_schema_version",
    "payload_byte_length",
    "session_id",
    "session_digest",
    "payload_digest",
    "session",
    "artifact_scope",
    "replay_input",
    "checkpoint_state",
    "persistence_authority",
    "clocks_compared",
    "time_aligned",
    "causality_inferred",
    "atomic_checkpoint",
    "lossless",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "artifact_digest",
}


def build_worldbridge_live_capture_artifact(
    session: Mapping[str, Any],
    *,
    artifact_id: str,
) -> dict[str, Any]:
    """Wrap one validated sealed E219 session in a canonical diagnostic envelope."""
    normalized_id = _clean_artifact_id(artifact_id)
    session_copy = _validated_sealed_session_copy(session)
    payload = _canonical_json_bytes(session_copy)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "artifact_id": normalized_id,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "payload_schema": session_copy["status"],
        "payload_schema_version": session_copy["schema_version"],
        "payload_byte_length": len(payload),
        "session_id": session_copy["session_id"],
        "session_digest": session_copy["session_digest"],
        "payload_digest": hashlib.sha256(payload).hexdigest(),
        "session": session_copy,
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["artifact_digest"] = _artifact_digest(result)
    encoded = _canonical_json_bytes(result)
    if len(encoded) > MAX_ARTIFACT_BYTES:
        raise OverflowError(
            f"worldbridge capture artifact exceeds {MAX_ARTIFACT_BYTES} bytes"
        )
    return result


def encode_worldbridge_live_capture_artifact(
    artifact: Mapping[str, Any],
    *,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> bytes:
    """Validate and canonically encode an E220 artifact as strict UTF-8 JSON."""
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_live_capture_artifact(artifact)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge capture artifact: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(artifact))
    if len(encoded) > limit:
        raise OverflowError(f"worldbridge capture artifact exceeds {limit} bytes")
    return encoded


def decode_worldbridge_live_capture_artifact(
    encoded: bytes | bytearray | memoryview,
    *,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> dict[str, Any]:
    """Decode only canonical, bounded, fully validated E220 artifact bytes."""
    limit = _byte_limit(max_bytes)
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded artifact must be bytes-like")
    raw = bytes(encoded)
    if not raw:
        raise ValueError("encoded artifact must not be empty")
    if len(raw) > limit:
        raise OverflowError(f"worldbridge capture artifact exceeds {limit} bytes")
    try:
        text = raw.decode(ENCODING, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("encoded artifact is not strict UTF-8") from exc
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded artifact is not strict JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded artifact root must be an object")
    validation = validate_worldbridge_live_capture_artifact(parsed)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge capture artifact: " + ",".join(validation["errors"]))
    canonical = _canonical_json_bytes(parsed)
    if canonical != raw:
        raise ValueError("encoded artifact is not canonical JSON")
    return copy.deepcopy(parsed)


def validate_worldbridge_live_capture_artifact(
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Return structural and nested-integrity errors without trusting envelope claims."""
    errors: list[str] = []
    if not isinstance(artifact, Mapping):
        return {"valid": False, "errors": ["artifact_not_mapping"]}
    try:
        value = dict(artifact)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["artifact_mapping_copy_failed"]}

    try:
        keys = set(value)
    except TypeError:
        return {"valid": False, "errors": ["artifact_keys_invalid"]}
    if keys != _REQUIRED_KEYS:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    try:
        _clean_artifact_id(value.get("artifact_id"))
    except ValueError:
        errors.append("artifact_id_invalid")
    if value.get("media_type") != MEDIA_TYPE:
        errors.append("media_type_mismatch")
    if value.get("encoding") != ENCODING:
        errors.append("encoding_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")

    session = value.get("session")
    session_valid = False
    if not isinstance(session, Mapping):
        errors.append("session_not_mapping")
    else:
        try:
            nested = validate_worldbridge_live_capture_session(session)
        except (KeyError, IndexError, TypeError, ValueError):
            nested = {"valid": False}
        if nested.get("valid") is not True:
            errors.append("nested_session_invalid")
        else:
            session_valid = True
            if session.get("lifecycle") != "sealed":
                errors.append("session_not_sealed")
            if session.get("session_complete") is not True:
                errors.append("session_not_complete")
            if session.get("partial_evidence") is not False:
                errors.append("session_partial_evidence_mismatch")
            if session.get("aggregation") is None:
                errors.append("session_aggregation_missing")

    payload: bytes | None = None
    if isinstance(session, Mapping):
        try:
            payload = _canonical_json_bytes(dict(session))
        except (TypeError, ValueError):
            errors.append("session_payload_not_canonicalizable")
    payload_length = value.get("payload_byte_length")
    if isinstance(payload_length, bool) or not isinstance(payload_length, int) or payload_length < 1:
        errors.append("payload_byte_length_invalid")
    if payload is not None:
        if payload_length != len(payload):
            errors.append("payload_byte_length_mismatch")
        if value.get("payload_digest") != hashlib.sha256(payload).hexdigest():
            errors.append("payload_digest_mismatch")
    elif not _is_sha256(value.get("payload_digest")):
        errors.append("payload_digest_invalid")

    if session_valid:
        if value.get("payload_schema") != session.get("status"):
            errors.append("payload_schema_mismatch")
        if value.get("payload_schema_version") != session.get("schema_version"):
            errors.append("payload_schema_version_mismatch")
        if value.get("session_id") != session.get("session_id"):
            errors.append("session_id_mismatch")
        if value.get("session_digest") != session.get("session_digest"):
            errors.append("session_digest_mismatch")
    else:
        if not isinstance(value.get("payload_schema"), str):
            errors.append("payload_schema_invalid")
        if isinstance(value.get("payload_schema_version"), bool) or not isinstance(
            value.get("payload_schema_version"), int
        ):
            errors.append("payload_schema_version_invalid")
        if not isinstance(value.get("session_id"), str):
            errors.append("session_id_invalid")
        if not _is_sha256(value.get("session_digest")):
            errors.append("session_digest_invalid")

    if not _is_sha256(value.get("artifact_digest")):
        errors.append("artifact_digest_invalid")
    else:
        try:
            if value["artifact_digest"] != _artifact_digest(value):
                errors.append("artifact_digest_mismatch")
        except (TypeError, ValueError):
            errors.append("artifact_digest_uncomputable")
    try:
        if len(_canonical_json_bytes(value)) > MAX_ARTIFACT_BYTES:
            errors.append("artifact_size_exceeded")
    except (TypeError, ValueError):
        errors.append("artifact_not_canonicalizable")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_live_capture_artifact_contract() -> dict[str, Any]:
    """Build deterministic self-validating E220 runtime-status evidence."""
    session = build_worldbridge_live_capture_session_contract()["session"]
    artifact = build_worldbridge_live_capture_artifact(
        session,
        artifact_id="worldbridge-e220-contract",
    )
    encoded = encode_worldbridge_live_capture_artifact(artifact)
    decoded = decode_worldbridge_live_capture_artifact(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_live_capture_artifact_contract",
        "contract_valid": validate_worldbridge_live_capture_artifact(artifact)["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_artifact_bytes": MAX_ARTIFACT_BYTES,
        "accepted_session_lifecycle": "sealed",
        "integrity_scope": "sha256_integrity_not_authenticity_or_replay_admission",
        "encoded_byte_length": len(encoded),
        "round_trip_equal": decoded == artifact,
        "artifact": copy.deepcopy(artifact),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_sealed_session_copy(session: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_worldbridge_live_capture_session(session)
    if not validation["valid"]:
        raise ValueError("invalid capture session: " + ",".join(validation["errors"]))
    if session.get("lifecycle") != "sealed":
        raise ValueError("capture artifact requires a sealed session")
    if session.get("session_complete") is not True or session.get("partial_evidence") is not False:
        raise ValueError("capture artifact requires a complete non-partial session")
    if session.get("aggregation") is None:
        raise ValueError("capture artifact requires a sealed aggregation")
    return copy.deepcopy(dict(session))


def _clean_artifact_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > MAX_ARTIFACT_ID_LENGTH
    ):
        raise ValueError(
            f"artifact_id must be a clean non-empty string up to {MAX_ARTIFACT_ID_LENGTH} characters"
        )
    return value


def _byte_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ARTIFACT_BYTES:
        raise ValueError(f"max_bytes must be an integer from 1 to {MAX_ARTIFACT_BYTES}")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode(ENCODING)


def _artifact_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("artifact_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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
    "MAX_ARTIFACT_BYTES",
    "MEDIA_TYPE",
    "build_worldbridge_live_capture_artifact",
    "build_worldbridge_live_capture_artifact_contract",
    "decode_worldbridge_live_capture_artifact",
    "encode_worldbridge_live_capture_artifact",
    "validate_worldbridge_live_capture_artifact",
]
