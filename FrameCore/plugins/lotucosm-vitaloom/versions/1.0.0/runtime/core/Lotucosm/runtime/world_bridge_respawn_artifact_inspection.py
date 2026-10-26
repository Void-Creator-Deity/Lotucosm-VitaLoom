# -*- coding: utf-8 -*-
"""Read-only consumer boundary for validated E226 respawn artifacts."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
    MAX_ARTIFACT_BYTES,
    MEDIA_TYPE as ARTIFACT_MEDIA_TYPE,
    decode_worldbridge_respawn_two_stream_artifact,
    validate_worldbridge_respawn_two_stream_artifact,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_respawn_two_stream_artifact_read_only_inspection"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-inspection+json"
ENCODING = "utf-8"
DO_NOT_CLAIM = (
    "inspection_replay_input",
    "inspection_checkpoint_state",
    "inspection_restore_authority",
    "inspection_mutation_execution",
    "inspection_live_runtime_state",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "inspection_scope": "validated_diagnostic_summary_only",
    "read_only": True,
    "replay_input": False,
    "checkpoint_state": False,
    "restore_performed": False,
    "mutation_executed": False,
    "live_runtime_state": False,
    "replay_admitted": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "media_type",
    "encoding",
    "canonical_json",
    "source_artifact_media_type",
    "source_artifact_id",
    "source_artifact_digest",
    "context_id",
    "decision_stream_name",
    "mutation_stream_name",
    "stream_family",
    "outcome",
    "admitted",
    "ordered_steps",
    "mutation_stream_consumed",
    "snapshot_digests",
    "parent_gene_count",
    "child_gene_count",
    "delta_gene_count",
    "inspection_scope",
    "read_only",
    "replay_input",
    "checkpoint_state",
    "restore_performed",
    "mutation_executed",
    "live_runtime_state",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "inspection_digest",
}


def inspect_worldbridge_respawn_two_stream_artifact(
    artifact: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Consume one validated artifact as a copy-isolated, non-executable summary."""
    validated = _validated_artifact(artifact)
    admitted = validated["admitted"]
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "source_artifact_media_type": ARTIFACT_MEDIA_TYPE,
        "source_artifact_id": validated["artifact_id"],
        "source_artifact_digest": validated["artifact_digest"],
        "context_id": validated["context_id"],
        "decision_stream_name": validated["decision_stream_name"],
        "mutation_stream_name": validated["mutation_stream_name"],
        "stream_family": validated["stream_family"],
        "outcome": "admitted_mutation" if admitted else "rejected_no_mutation",
        "admitted": admitted,
        "ordered_steps": copy.deepcopy(validated["ordered_steps"]),
        "mutation_stream_consumed": validated["mutation_stream_consumed"],
        "snapshot_digests": {
            "before": validated["before_snapshot_digest"],
            "after_decision": validated["after_decision_snapshot_digest"],
            "after": validated["after_snapshot_digest"],
        },
        "parent_gene_count": len(validated["parent"]),
        "child_gene_count": len(validated["child"]),
        "delta_gene_count": len(validated["deltas"]),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    summary["inspection_digest"] = _inspection_digest(summary)
    validation = validate_worldbridge_respawn_artifact_inspection(summary)
    if not validation["valid"]:
        raise RuntimeError("constructed invalid inspection summary: " + ",".join(validation["errors"]))
    return copy.deepcopy(summary)


def validate_worldbridge_respawn_artifact_inspection(
    summary: object,
) -> dict[str, Any]:
    """Validate exact summary structure and its self-integrity without executing anything."""
    errors: list[str] = []
    if not isinstance(summary, Mapping):
        return {"valid": False, "errors": ["summary_not_mapping"]}
    try:
        value = dict(summary)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["summary_mapping_copy_failed"]}
    if set(value) != _REQUIRED_KEYS:
        errors.append("summary_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("media_type") != MEDIA_TYPE:
        errors.append("media_type_mismatch")
    if value.get("encoding") != ENCODING:
        errors.append("encoding_mismatch")
    if value.get("canonical_json") is not True:
        errors.append("canonical_json_mismatch")
    if value.get("source_artifact_media_type") != ARTIFACT_MEDIA_TYPE:
        errors.append("source_artifact_media_type_mismatch")
    for field in (
        "source_artifact_id",
        "context_id",
        "decision_stream_name",
        "mutation_stream_name",
        "stream_family",
    ):
        if not _clean_nonempty_string(value.get(field)):
            errors.append(f"{field}_invalid")
    if not _is_sha256(value.get("source_artifact_digest")):
        errors.append("source_artifact_digest_invalid")
    if value.get("stream_family") != "python_random":
        errors.append("stream_family_mismatch")
    if value.get("outcome") not in {"admitted_mutation", "rejected_no_mutation"}:
        errors.append("outcome_invalid")
    admitted = value.get("admitted")
    if type(admitted) is not bool:
        errors.append("admitted_invalid")
    elif value.get("outcome") != ("admitted_mutation" if admitted else "rejected_no_mutation"):
        errors.append("outcome_mismatch")
    if value.get("ordered_steps") != (["decision", "mutation"] if admitted is True else ["decision"]):
        errors.append("ordered_steps_mismatch")
    if type(value.get("mutation_stream_consumed")) is not bool or value.get("mutation_stream_consumed") is not (admitted is True):
        errors.append("mutation_stream_consumed_mismatch")
    snapshot_digests = value.get("snapshot_digests")
    if not isinstance(snapshot_digests, Mapping) or set(snapshot_digests) != {"before", "after_decision", "after"}:
        errors.append("snapshot_digests_structure_invalid")
    else:
        for key, digest in snapshot_digests.items():
            if not _is_sha256(digest):
                errors.append(f"snapshot_digest_{key}_invalid")
    for field in ("parent_gene_count", "child_gene_count", "delta_gene_count"):
        if isinstance(value.get(field), bool) or not isinstance(value.get(field), int) or value.get(field) < 0:
            errors.append(f"{field}_invalid")
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected or type(value.get(field)) is not type(expected):
            errors.append(f"{field}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if not _is_sha256(value.get("inspection_digest")):
        errors.append("inspection_digest_invalid")
    else:
        try:
            if value["inspection_digest"] != _inspection_digest(value):
                errors.append("inspection_digest_mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("inspection_digest_uncomputable")
    try:
        _canonical_json_bytes(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("summary_not_canonicalizable")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_respawn_artifact_inspection(
    summary: Mapping[str, Any],
) -> bytes:
    """Encode a validated summary canonically; this is not an artifact persistence API."""
    validation = validate_worldbridge_respawn_artifact_inspection(summary)
    if not validation["valid"]:
        raise ValueError("invalid respawn inspection summary: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(summary))
    if len(encoded) > MAX_ARTIFACT_BYTES:
        raise OverflowError("respawn inspection summary exceeds artifact bound")
    return encoded


def decode_worldbridge_respawn_artifact_inspection(
    encoded: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    """Decode only canonical inspection-summary bytes; it never decodes executable state."""
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded inspection summary must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise ValueError("encoded inspection summary is empty or exceeds bound")
    try:
        parsed = json.loads(raw.decode(ENCODING, errors="strict"), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded inspection summary is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded inspection summary root must be an object")
    validation = validate_worldbridge_respawn_artifact_inspection(parsed)
    if not validation["valid"]:
        raise ValueError("invalid respawn inspection summary: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(parsed) != raw:
        raise ValueError("encoded inspection summary is not canonical JSON")
    return copy.deepcopy(parsed)


def build_worldbridge_respawn_artifact_inspection_contract() -> dict[str, Any]:
    """Build deterministic status evidence through the E226 artifact consumer seam."""
    from core.Lotucosm.runtime.world_bridge_respawn_two_stream_artifact import (
        build_worldbridge_respawn_two_stream_artifact_contract,
    )

    artifact = build_worldbridge_respawn_two_stream_artifact_contract()["artifact"]
    summary = inspect_worldbridge_respawn_two_stream_artifact(artifact)
    encoded = encode_worldbridge_respawn_artifact_inspection(summary)
    decoded = decode_worldbridge_respawn_artifact_inspection(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_artifact_inspection_contract",
        "contract_valid": validate_worldbridge_respawn_artifact_inspection(summary)["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "round_trip_equal": decoded == summary,
        "summary": copy.deepcopy(summary),
        "source_artifact_media_type": ARTIFACT_MEDIA_TYPE,
        "artifact_consumer_only": True,
        "restores_streams": False,
        "executes_mutation": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_artifact(
    artifact: Mapping[str, Any] | bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if isinstance(artifact, (bytes, bytearray, memoryview)):
        return decode_worldbridge_respawn_two_stream_artifact(artifact)
    validation = validate_worldbridge_respawn_two_stream_artifact(artifact)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge respawn artifact: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(artifact))


def _inspection_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("inspection_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _clean_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


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
    "MEDIA_TYPE",
    "build_worldbridge_respawn_artifact_inspection_contract",
    "decode_worldbridge_respawn_artifact_inspection",
    "encode_worldbridge_respawn_artifact_inspection",
    "inspect_worldbridge_respawn_two_stream_artifact",
    "validate_worldbridge_respawn_artifact_inspection",
]
