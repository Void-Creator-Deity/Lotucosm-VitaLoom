# -*- coding: utf-8 -*-
"""Canonical read-only evidence for one opt-in E225 respawn two-stream hand-off."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    validate_worldbridge_deterministic_randomness_snapshot,
)
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
    ADAPTER_SCHEMA_VERSION,
    SUPPORTED_STREAM_FAMILY,
    TWO_STREAM_HANDOFF_KIND,
    run_worldbridge_named_stream_sr_respawn_handoff,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_opt_in_respawn_two_stream_handoff_artifact"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-respawn-two-stream-handoff+json"
ENCODING = "utf-8"
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_ID_LENGTH = 128
DO_NOT_CLAIM = (
    "artifact_replay_input",
    "scene_or_pond_checkpoint",
    "artifact_persistence_authority",
    "atomic_cross_lane_or_cross_thread_handoff",
    "common_sr_ps_time_alignment",
    "full_rng_authority_closure",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "artifact_scope": "offline_diagnostic_transport_only",
    "replay_input": False,
    "checkpoint_state": False,
    "persistence_authority": False,
    "atomic_handoff": False,
    "time_aligned": False,
    "entropy_closed": False,
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
    "handoff_schema_version",
    "handoff_kind",
    "context_id",
    "decision_stream_name",
    "mutation_stream_name",
    "stream_family",
    "before_snapshot_digest",
    "after_decision_snapshot_digest",
    "after_snapshot_digest",
    "probability",
    "sampled_value",
    "admitted",
    "ordered_steps",
    "mutation_stream_consumed",
    "parent",
    "child",
    "deltas",
    "before_snapshot",
    "after_decision_snapshot",
    "after_snapshot",
    "handoff_payload_digest",
    "artifact_scope",
    "replay_input",
    "checkpoint_state",
    "persistence_authority",
    "atomic_handoff",
    "time_aligned",
    "entropy_closed",
    "lossless",
    "replay_admitted",
    "default_ready",
    "do_not_claim",
    "artifact_digest",
}
_HANDOFF_REQUIRED_KEYS = {
    "schema_version",
    "handoff_kind",
    "context_id",
    "decision_stream_name",
    "mutation_stream_name",
    "stream_family",
    "ordered_roles",
    "caller_owned",
    "default_tick_attached",
    "replay_admitted",
    "default_ready",
    "probability",
    "sampled_value",
    "admitted",
    "parent",
    "child",
    "deltas",
    "before_snapshot_digest",
    "after_decision_snapshot_digest",
    "after_snapshot_digest",
    "before_snapshot",
    "after_decision_snapshot",
    "after_snapshot",
    "decision_stream_state_changed",
    "mutation_stream_consumed",
    "ordered_steps",
    "replay_input",
    "checkpoint_state",
    "lossless",
}


def build_worldbridge_respawn_two_stream_artifact(
    handoff: Mapping[str, Any],
    *,
    artifact_id: str,
) -> dict[str, Any]:
    """Seal one complete E225 result as canonical read-only diagnostic evidence."""
    clean_id = _clean_artifact_id(artifact_id)
    handoff_copy = _validated_handoff_copy(handoff)
    payload = _canonical_json_bytes(handoff_copy)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "artifact_id": clean_id,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "handoff_schema_version": handoff_copy["schema_version"],
        "handoff_kind": handoff_copy["handoff_kind"],
        "context_id": handoff_copy["context_id"],
        "decision_stream_name": handoff_copy["decision_stream_name"],
        "mutation_stream_name": handoff_copy["mutation_stream_name"],
        "stream_family": handoff_copy["stream_family"],
        "before_snapshot_digest": handoff_copy["before_snapshot_digest"],
        "after_decision_snapshot_digest": handoff_copy[
            "after_decision_snapshot_digest"
        ],
        "after_snapshot_digest": handoff_copy["after_snapshot_digest"],
        "probability": handoff_copy["probability"],
        "sampled_value": handoff_copy["sampled_value"],
        "admitted": handoff_copy["admitted"],
        "ordered_steps": copy.deepcopy(handoff_copy["ordered_steps"]),
        "mutation_stream_consumed": handoff_copy["mutation_stream_consumed"],
        "parent": copy.deepcopy(handoff_copy["parent"]),
        "child": copy.deepcopy(handoff_copy["child"]),
        "deltas": copy.deepcopy(handoff_copy["deltas"]),
        "before_snapshot": copy.deepcopy(handoff_copy["before_snapshot"]),
        "after_decision_snapshot": copy.deepcopy(handoff_copy["after_decision_snapshot"]),
        "after_snapshot": copy.deepcopy(handoff_copy["after_snapshot"]),
        "handoff_payload_digest": hashlib.sha256(payload).hexdigest(),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["artifact_digest"] = _artifact_digest(result)
    if len(_canonical_json_bytes(result)) > MAX_ARTIFACT_BYTES:
        raise OverflowError(f"worldbridge respawn artifact exceeds {MAX_ARTIFACT_BYTES} bytes")
    return result


def encode_worldbridge_respawn_two_stream_artifact(
    artifact: Mapping[str, Any],
    *,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> bytes:
    """Validate and encode a bounded E226 artifact as strict canonical UTF-8 JSON."""
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_respawn_two_stream_artifact(artifact)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge respawn artifact: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(artifact))
    if len(encoded) > limit:
        raise OverflowError(f"worldbridge respawn artifact exceeds {limit} bytes")
    return encoded


def decode_worldbridge_respawn_two_stream_artifact(
    encoded: bytes | bytearray | memoryview,
    *,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> dict[str, Any]:
    """Decode only bounded, strict, canonical, fully validated E226 artifacts."""
    limit = _byte_limit(max_bytes)
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded artifact must be bytes-like")
    raw = bytes(encoded)
    if not raw:
        raise ValueError("encoded artifact must not be empty")
    if len(raw) > limit:
        raise OverflowError(f"worldbridge respawn artifact exceeds {limit} bytes")
    try:
        parsed = json.loads(
            raw.decode(ENCODING, errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("encoded artifact is not strict UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded artifact root must be an object")
    validation = validate_worldbridge_respawn_two_stream_artifact(parsed)
    if not validation["valid"]:
        raise ValueError("invalid worldbridge respawn artifact: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(parsed) != raw:
        raise ValueError("encoded artifact is not canonical JSON")
    return copy.deepcopy(parsed)


def validate_worldbridge_respawn_two_stream_artifact(
    artifact: object,
) -> dict[str, Any]:
    """Validate exact envelope keys, nested snapshots, and local two-stream semantics."""
    errors: list[str] = []
    if not isinstance(artifact, Mapping):
        return {"valid": False, "errors": ["artifact_not_mapping"]}
    try:
        value = dict(artifact)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["artifact_mapping_copy_failed"]}
    if set(value) != _REQUIRED_KEYS:
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

    handoff = _handoff_from_artifact(value)
    handoff_validation = validate_worldbridge_respawn_two_stream_handoff_evidence(handoff)
    if not handoff_validation["valid"]:
        errors.extend(f"handoff_{error}" for error in handoff_validation["errors"])
    else:
        payload = _canonical_json_bytes(handoff)
        if value.get("handoff_payload_digest") != hashlib.sha256(payload).hexdigest():
            errors.append("handoff_payload_digest_mismatch")

    if not _is_sha256(value.get("artifact_digest")):
        errors.append("artifact_digest_invalid")
    else:
        try:
            if value["artifact_digest"] != _artifact_digest(value):
                errors.append("artifact_digest_mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("artifact_digest_uncomputable")
    try:
        if len(_canonical_json_bytes(value)) > MAX_ARTIFACT_BYTES:
            errors.append("artifact_size_exceeded")
    except (TypeError, ValueError, OverflowError):
        errors.append("artifact_not_canonicalizable")
    return {"valid": not errors, "errors": errors}


def validate_worldbridge_respawn_two_stream_handoff_evidence(
    handoff: object,
) -> dict[str, Any]:
    """Validate one complete E225 result without mutating or restoring any stream."""
    errors: list[str] = []
    if not isinstance(handoff, Mapping):
        return {"valid": False, "errors": ["handoff_not_mapping"]}
    try:
        value = dict(handoff)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["handoff_mapping_copy_failed"]}
    if set(value) != _HANDOFF_REQUIRED_KEYS:
        errors.append("handoff_keys_mismatch")
    if value.get("schema_version") != ADAPTER_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("handoff_kind") != TWO_STREAM_HANDOFF_KIND:
        errors.append("handoff_kind_mismatch")
    if not _clean_nonempty_string(value.get("context_id")):
        errors.append("context_id_invalid")
    decision_name = value.get("decision_stream_name")
    mutation_name = value.get("mutation_stream_name")
    if not _clean_nonempty_string(decision_name):
        errors.append("decision_stream_name_invalid")
    if not _clean_nonempty_string(mutation_name):
        errors.append("mutation_stream_name_invalid")
    if decision_name == mutation_name:
        errors.append("stream_names_not_distinct")
    if value.get("stream_family") != SUPPORTED_STREAM_FAMILY:
        errors.append("stream_family_mismatch")
    if value.get("ordered_roles") != ["decision", "mutation_if_admitted"]:
        errors.append("ordered_roles_mismatch")
    for field, expected in {
        "caller_owned": True,
        "default_tick_attached": False,
        "replay_admitted": False,
        "default_ready": False,
        "replay_input": False,
        "checkpoint_state": False,
        "lossless": False,
    }.items():
        if value.get(field) is not expected:
            errors.append(f"{field}_mismatch")

    probability = _finite_float(value.get("probability"))
    sampled_value = _finite_float(value.get("sampled_value"))
    if probability is None or not 0.0 <= probability <= 1.0:
        errors.append("probability_invalid")
    if sampled_value is None or not 0.0 <= sampled_value < 1.0:
        errors.append("sampled_value_invalid")
    admitted = value.get("admitted")
    if type(admitted) is not bool:
        errors.append("admitted_invalid")
    elif probability is not None and sampled_value is not None and admitted is not (sampled_value < probability):
        errors.append("admission_mismatch")

    parent = _number_mapping(value.get("parent"))
    child = _number_mapping(value.get("child"))
    deltas = _number_mapping(value.get("deltas"))
    if parent is None:
        errors.append("parent_invalid")
    if child is None:
        errors.append("child_invalid")
    if deltas is None:
        errors.append("deltas_invalid")

    expected_steps = ["decision", "mutation"] if admitted is True else ["decision"]
    if value.get("ordered_steps") != expected_steps:
        errors.append("ordered_steps_mismatch")
    mutation_consumed = value.get("mutation_stream_consumed")
    if type(mutation_consumed) is not bool or mutation_consumed is not (admitted is True):
        errors.append("mutation_stream_consumed_mismatch")
    if value.get("decision_stream_state_changed") is not True:
        errors.append("decision_stream_state_changed_mismatch")
    if admitted is False and parent is not None and child is not None and child != parent:
        errors.append("rejected_child_mismatch")
    if admitted is False and deltas is not None and deltas != {}:
        errors.append("rejected_deltas_mismatch")
    if admitted is True and parent is not None and child is not None and deltas is not None:
        _validate_deltas(parent, child, deltas, errors)

    snapshots = {
        "before": value.get("before_snapshot"),
        "after_decision": value.get("after_decision_snapshot"),
        "after": value.get("after_snapshot"),
    }
    for label, snapshot in snapshots.items():
        nested = validate_worldbridge_deterministic_randomness_snapshot(snapshot)
        if nested.get("valid") is not True:
            errors.append(f"{label}_snapshot_invalid")
    if all(validate_worldbridge_deterministic_randomness_snapshot(snapshot)["valid"] for snapshot in snapshots.values()):
        _validate_snapshot_boundaries(value, snapshots, errors)
    return {"valid": not errors, "errors": errors}


def build_worldbridge_respawn_two_stream_artifact_contract() -> dict[str, Any]:
    """Build deterministic status evidence without touching module-global RNG state."""
    context = create_worldbridge_deterministic_randomness_context(
        "e226-contract-example",
        "e226-fixed-root-seed",
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.decision", SUPPORTED_STREAM_FAMILY
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.war.respawn.mind", SUPPORTED_STREAM_FAMILY
    )
    handoff = run_worldbridge_named_stream_sr_respawn_handoff(
        context,
        "sr.war.respawn.decision",
        "sr.war.respawn.mind",
        {"wander_amp": 20.0, "gain_high_stress": 40.0, "mem_alpha": 0.3},
        0.25,
        1.0,
    )
    artifact = build_worldbridge_respawn_two_stream_artifact(
        handoff,
        artifact_id="worldbridge-e226-contract",
    )
    encoded = encode_worldbridge_respawn_two_stream_artifact(artifact)
    decoded = decode_worldbridge_respawn_two_stream_artifact(encoded)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_respawn_two_stream_artifact_contract",
        "contract_valid": validate_worldbridge_respawn_two_stream_artifact(artifact)["valid"],
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "max_artifact_bytes": MAX_ARTIFACT_BYTES,
        "accepted_handoff_kind": TWO_STREAM_HANDOFF_KIND,
        "integrity_scope": "sha256_integrity_not_authenticity_or_replay_admission",
        "encoded_byte_length": len(encoded),
        "round_trip_equal": decoded == artifact,
        "artifact": copy.deepcopy(artifact),
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_handoff_copy(handoff: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_worldbridge_respawn_two_stream_handoff_evidence(handoff)
    if not validation["valid"]:
        raise ValueError("invalid respawn two-stream handoff: " + ",".join(validation["errors"]))
    return copy.deepcopy(dict(handoff))


def _handoff_from_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": value.get("handoff_schema_version"),
        "handoff_kind": value.get("handoff_kind"),
        "context_id": value.get("context_id"),
        "decision_stream_name": value.get("decision_stream_name"),
        "mutation_stream_name": value.get("mutation_stream_name"),
        "stream_family": value.get("stream_family"),
        "ordered_roles": ["decision", "mutation_if_admitted"],
        "caller_owned": True,
        "default_tick_attached": False,
        "replay_admitted": value.get("replay_admitted"),
        "default_ready": value.get("default_ready"),
        "probability": value.get("probability"),
        "sampled_value": value.get("sampled_value"),
        "admitted": value.get("admitted"),
        "parent": value.get("parent"),
        "child": value.get("child"),
        "deltas": value.get("deltas"),
        "before_snapshot_digest": value.get("before_snapshot_digest"),
        "after_decision_snapshot_digest": value.get("after_decision_snapshot_digest"),
        "after_snapshot_digest": value.get("after_snapshot_digest"),
        "before_snapshot": value.get("before_snapshot"),
        "after_decision_snapshot": value.get("after_decision_snapshot"),
        "after_snapshot": value.get("after_snapshot"),
        "decision_stream_state_changed": True,
        "mutation_stream_consumed": value.get("mutation_stream_consumed"),
        "ordered_steps": value.get("ordered_steps"),
        "replay_input": value.get("replay_input"),
        "checkpoint_state": value.get("checkpoint_state"),
        "lossless": value.get("lossless"),
    }


def _validate_snapshot_boundaries(
    value: Mapping[str, Any],
    snapshots: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    before = snapshots["before"]
    after_decision = snapshots["after_decision"]
    after = snapshots["after"]
    context_id = value.get("context_id")
    for label, snapshot, digest_field in (
        ("before", before, "before_snapshot_digest"),
        ("after_decision", after_decision, "after_decision_snapshot_digest"),
        ("after", after, "after_snapshot_digest"),
    ):
        if snapshot.get("context_id") != context_id:
            errors.append(f"{label}_snapshot_context_mismatch")
        if value.get(digest_field) != snapshot.get("snapshot_digest"):
            errors.append(f"{label}_snapshot_digest_mismatch")
    if _stream_layout(before) != _stream_layout(after_decision) or _stream_layout(before) != _stream_layout(after):
        errors.append("snapshot_stream_layout_mismatch")
        return
    decision_name = value.get("decision_stream_name")
    mutation_name = value.get("mutation_stream_name")
    stream_names = {row[0] for row in _stream_layout(before)}
    if decision_name not in stream_names:
        errors.append("decision_stream_missing_from_snapshot")
    if mutation_name not in stream_names:
        errors.append("mutation_stream_missing_from_snapshot")
    if _stream_family_from_snapshot(before, decision_name) != SUPPORTED_STREAM_FAMILY:
        errors.append("decision_stream_family_mismatch")
    if _stream_family_from_snapshot(before, mutation_name) != SUPPORTED_STREAM_FAMILY:
        errors.append("mutation_stream_family_mismatch")
    changed_decision = _changed_stream_names(before, after_decision)
    if changed_decision != {decision_name}:
        errors.append("decision_boundary_changed_streams_mismatch")
    admitted = value.get("admitted")
    if admitted is False:
        if after_decision != after:
            errors.append("rejected_final_snapshot_mismatch")
    elif admitted is True:
        changed_mutation = _changed_stream_names(after_decision, after)
        if changed_mutation != {mutation_name}:
            errors.append("mutation_boundary_changed_streams_mismatch")
    else:
        errors.append("admitted_invalid")


def _stream_layout(snapshot: Mapping[str, Any]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            row.get("stream_name"),
            row.get("family"),
            row.get("registration_index"),
            row.get("derivation_version"),
            row.get("derivation_digest"),
        )
        for row in snapshot["streams"]
    )


def _stream_family_from_snapshot(snapshot: Mapping[str, Any], name: object) -> object:
    for row in snapshot["streams"]:
        if row.get("stream_name") == name:
            return row.get("family")
    return None


def _changed_stream_names(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> set[str]:
    before_states = {row["stream_name"]: row["state"] for row in before["streams"]}
    after_states = {row["stream_name"]: row["state"] for row in after["streams"]}
    return {
        name
        for name in before_states
        if before_states[name] != after_states.get(name)
    }


def _validate_deltas(
    parent: Mapping[str, float], child: Mapping[str, float], deltas: Mapping[str, float], errors: list[str]
) -> None:
    if set(child) != set(deltas):
        errors.append("child_delta_key_mismatch")
    for key, delta in deltas.items():
        if key not in parent or key not in child:
            errors.append("delta_parent_child_key_mismatch")
            continue
        if not math.isclose(child[key] - parent[key], delta, rel_tol=0.0, abs_tol=1e-12):
            errors.append("delta_value_mismatch")
            return


def _number_mapping(value: object) -> dict[str, float] | None:
    if not isinstance(value, Mapping):
        return None
    result: dict[str, float] = {}
    for key, raw in value.items():
        if not _clean_nonempty_string(key):
            return None
        number = _finite_float(raw)
        if number is None:
            return None
        result[key] = number
    return result


def _finite_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clean_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _clean_artifact_id(value: object) -> str:
    if not _clean_nonempty_string(value) or len(value) > MAX_ARTIFACT_ID_LENGTH:
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
    "build_worldbridge_respawn_two_stream_artifact",
    "build_worldbridge_respawn_two_stream_artifact_contract",
    "decode_worldbridge_respawn_two_stream_artifact",
    "encode_worldbridge_respawn_two_stream_artifact",
    "validate_worldbridge_respawn_two_stream_artifact",
    "validate_worldbridge_respawn_two_stream_handoff_evidence",
]
