# -*- coding: utf-8 -*-
"""Qt-free bounded session producer for repeated WorldBridge live evidence."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
    validate_worldbridge_live_dual_lane_trace,
)
from core.Lotucosm.runtime.world_bridge_live_trace_time_series import (
    aggregate_worldbridge_live_trace_evaluations,
    validate_worldbridge_live_trace_time_series,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_bounded_live_comparability_capture_session"
MAX_SESSION_SAMPLES = 4096
EVIDENCE_KINDS = (
    "e216_live_producer",
    "e217_field_evaluation",
)
LIFECYCLES = ("open", "sealed", "aborted")
DO_NOT_CLAIM = (
    "session_scheduler_authority",
    "common_sr_ps_time_alignment",
    "cross_sample_causality",
    "atomic_sr_ps_checkpoint",
    "lossless_worldbridge_mapping",
    "full_unified_runtime_replay",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "bounded": True,
    "capture_source": "explicit_existing_bridge_handoff_append_only",
    "sample_index_policy": "zero_based_contiguous_append_order",
    "sampling_policy": "one_sample_per_explicit_append_no_timer_or_interpolation",
    "overflow_policy": "reject_without_mutation",
    "failure_policy": "reject_input_without_mutation_or_explicit_abort",
    "pair_churn_policy": "preserve_e218_pair_absence",
    "scheduler_owned": False,
    "clocks_compared": False,
    "time_aligned": False,
    "causality_inferred": False,
    "atomic_checkpoint": False,
    "lossless": False,
    "replay_admitted": False,
    "default_ready": False,
}


def start_worldbridge_live_capture_session(
    session_id: str,
    *,
    max_samples: int,
) -> dict[str, Any]:
    """Create an empty bounded diagnostic session without owning a clock."""
    normalized_id = _session_id(session_id)
    capacity = _sample_capacity(max_samples)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "session_id": normalized_id,
        "lifecycle": "open",
        "max_samples": capacity,
        "sample_count": 0,
        "evidence_kind": None,
        "samples": [],
        "source_trace_digests": [],
        "source_evaluation_digests": [],
        "aggregation": None,
        "abort_reason": None,
        "partial_evidence": True,
        "session_complete": False,
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["session_digest"] = _session_digest(result)
    return result


def append_worldbridge_live_capture_session_evidence(
    session: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Append one validated E216 or E217 item and return a new open session."""
    current = _validated_session_copy(session, required_lifecycle="open")
    if current["sample_count"] >= current["max_samples"]:
        raise OverflowError("worldbridge live capture session capacity reached")

    evaluation, evidence_kind = _normalize_evidence(evidence)
    established_kind = current["evidence_kind"]
    if established_kind is not None and established_kind != evidence_kind:
        raise ValueError(
            f"mixed session evidence kind: expected {established_kind}, got {evidence_kind}"
        )
    source_trace_digest = evaluation["source_trace_digest"]
    if source_trace_digest in current["source_trace_digests"]:
        raise ValueError(f"duplicate source_trace_digest: {source_trace_digest}")

    sample_index = current["sample_count"]
    sample = {
        "sample_id": _sample_id(current["session_id"], sample_index),
        "sample_index": sample_index,
        "source_evidence_kind": evidence_kind,
        "evaluation": copy.deepcopy(evaluation),
    }
    result = copy.deepcopy(current)
    result["evidence_kind"] = evidence_kind
    result["samples"].append(sample)
    result["sample_count"] = len(result["samples"])
    result["source_trace_digests"].append(source_trace_digest)
    result["source_evaluation_digests"].append(evaluation["evaluation_digest"])
    result["session_digest"] = _session_digest(result)
    return result


def seal_worldbridge_live_capture_session(
    session: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal a non-empty session and attach its validated E218 aggregation."""
    current = _validated_session_copy(session, required_lifecycle="open")
    if current["sample_count"] < 1:
        raise ValueError("cannot seal an empty worldbridge live capture session")
    aggregation = aggregate_worldbridge_live_trace_evaluations(current["samples"])
    aggregation_validation = validate_worldbridge_live_trace_time_series(aggregation)
    if not aggregation_validation["valid"]:
        raise ValueError(
            "invalid E218 aggregation: " + ",".join(aggregation_validation["errors"])
        )
    result = copy.deepcopy(current)
    result["lifecycle"] = "sealed"
    result["aggregation"] = aggregation
    result["partial_evidence"] = False
    result["session_complete"] = True
    result["session_digest"] = _session_digest(result)
    return result


def abort_worldbridge_live_capture_session(
    session: Mapping[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    """Abort an open session while retaining explicitly labeled partial evidence."""
    current = _validated_session_copy(session, required_lifecycle="open")
    normalized_reason = _required_clean_string(reason, "reason", maximum=256)
    result = copy.deepcopy(current)
    result["lifecycle"] = "aborted"
    result["abort_reason"] = normalized_reason
    result["aggregation"] = None
    result["partial_evidence"] = True
    result["session_complete"] = False
    result["session_digest"] = _session_digest(result)
    return result


def validate_worldbridge_live_capture_session(value: object) -> dict[str, Any]:
    """Validate session lifecycle, nested evidence, reconstruction, and no-claims."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["session_must_be_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    for field, expected in _STATIC_POLICIES.items():
        if value.get(field) != expected:
            errors.append(f"{field}_policy_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")

    session_id = value.get("session_id")
    session_id_valid = (
        isinstance(session_id, str)
        and bool(session_id)
        and session_id == session_id.strip()
        and len(session_id) <= 128
    )
    if not session_id_valid:
        errors.append("session_id_invalid")

    max_samples = value.get("max_samples")
    max_samples_valid = (
        not isinstance(max_samples, bool)
        and isinstance(max_samples, int)
        and 1 <= max_samples <= MAX_SESSION_SAMPLES
    )
    if not max_samples_valid:
        errors.append("max_samples_invalid")

    lifecycle = value.get("lifecycle")
    lifecycle_valid = isinstance(lifecycle, str) and lifecycle in LIFECYCLES
    if not lifecycle_valid:
        errors.append("lifecycle_invalid")

    samples = value.get("samples")
    if not isinstance(samples, list):
        errors.append("samples_missing")
        samples = []
    if value.get("sample_count") != len(samples):
        errors.append("sample_count_mismatch")
    if max_samples_valid and len(samples) > max_samples:
        errors.append("sample_capacity_exceeded")

    evidence_kind = value.get("evidence_kind")
    evidence_kind_valid = evidence_kind is None or (
        isinstance(evidence_kind, str) and evidence_kind in EVIDENCE_KINDS
    )
    if not evidence_kind_valid:
        errors.append("evidence_kind_invalid")
    if not samples and evidence_kind is not None:
        errors.append("empty_session_evidence_kind_mismatch")
    if samples and evidence_kind is None:
        errors.append("nonempty_session_evidence_kind_missing")

    source_trace_digests: list[str] = []
    source_evaluation_digests: list[str] = []
    structurally_valid_samples: list[Mapping[str, Any]] = []
    seen_source_digests: set[str] = set()
    for expected_index, sample in enumerate(samples):
        sample_valid = True
        if not isinstance(sample, Mapping):
            errors.append("sample_invalid")
            continue
        if sample.get("sample_index") != expected_index:
            errors.append("sample_index_not_contiguous")
            sample_valid = False
        expected_sample_id = _sample_id(session_id, expected_index) if session_id_valid else None
        if sample.get("sample_id") != expected_sample_id:
            errors.append("sample_id_mismatch")
            sample_valid = False
        sample_kind = sample.get("source_evidence_kind")
        if not isinstance(sample_kind, str) or sample_kind not in EVIDENCE_KINDS:
            errors.append("sample_evidence_kind_invalid")
            sample_valid = False
        elif evidence_kind_valid and sample_kind != evidence_kind:
            errors.append("sample_evidence_kind_mismatch")
            sample_valid = False

        evaluation = sample.get("evaluation")
        try:
            evaluation_validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
        except (KeyError, IndexError, TypeError, ValueError):
            evaluation_validation = {"valid": False, "errors": ["nested_validation_failed"]}
        if not evaluation_validation["valid"]:
            errors.append("nested_evaluation_invalid")
            sample_valid = False
        if isinstance(evaluation, Mapping):
            trace_digest = evaluation.get("source_trace_digest")
            evaluation_digest = evaluation.get("evaluation_digest")
            if not _is_sha256(trace_digest) or trace_digest in seen_source_digests:
                errors.append("source_trace_digest_duplicate_or_invalid")
                sample_valid = False
            else:
                seen_source_digests.add(trace_digest)
                source_trace_digests.append(trace_digest)
            if not _is_sha256(evaluation_digest):
                errors.append("source_evaluation_digest_invalid")
                sample_valid = False
            else:
                source_evaluation_digests.append(evaluation_digest)
        else:
            sample_valid = False
        if sample_valid:
            structurally_valid_samples.append(sample)

    if value.get("source_trace_digests") != source_trace_digests:
        errors.append("source_trace_digests_mismatch")
    if value.get("source_evaluation_digests") != source_evaluation_digests:
        errors.append("source_evaluation_digests_mismatch")

    aggregation = value.get("aggregation")
    abort_reason = value.get("abort_reason")
    can_rebuild = len(structurally_valid_samples) == len(samples) and bool(samples)
    if lifecycle == "open":
        if aggregation is not None:
            errors.append("open_session_aggregation_forbidden")
        if abort_reason is not None:
            errors.append("open_session_abort_reason_forbidden")
        if value.get("partial_evidence") is not True:
            errors.append("open_session_must_be_partial")
        if value.get("session_complete") is not False:
            errors.append("open_session_not_complete")
    elif lifecycle == "aborted":
        if aggregation is not None:
            errors.append("aborted_session_aggregation_forbidden")
        if not isinstance(abort_reason, str) or not abort_reason or abort_reason != abort_reason.strip():
            errors.append("aborted_session_reason_invalid")
        if value.get("partial_evidence") is not True:
            errors.append("aborted_session_must_be_partial")
        if value.get("session_complete") is not False:
            errors.append("aborted_session_not_complete")
    elif lifecycle == "sealed":
        if not samples:
            errors.append("sealed_session_empty")
        if abort_reason is not None:
            errors.append("sealed_session_abort_reason_forbidden")
        if value.get("partial_evidence") is not False:
            errors.append("sealed_session_partial_flag_invalid")
        if value.get("session_complete") is not True:
            errors.append("sealed_session_not_complete")
        try:
            aggregation_validation = validate_worldbridge_live_trace_time_series(aggregation)
        except (KeyError, IndexError, TypeError, ValueError):
            aggregation_validation = {"valid": False, "errors": ["nested_aggregation_validation_failed"]}
        if not aggregation_validation["valid"]:
            errors.append("nested_aggregation_invalid")
        if can_rebuild:
            try:
                expected_aggregation = aggregate_worldbridge_live_trace_evaluations(samples)
            except (KeyError, IndexError, TypeError, ValueError):
                errors.append("aggregation_rebuild_failed")
            else:
                if aggregation != expected_aggregation:
                    errors.append("aggregation_evidence_mismatch")

    digest = value.get("session_digest")
    if not _is_sha256(digest):
        errors.append("session_digest_invalid")
    try:
        expected_digest = _session_digest(value)
    except (TypeError, ValueError):
        errors.append("session_not_json_safe")
    else:
        if digest != expected_digest:
            errors.append("session_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_live_capture_session_contract() -> dict[str, Any]:
    """Build deterministic E219 evidence without importing the Qt host."""
    session = start_worldbridge_live_capture_session("contract-session", max_samples=2)
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _sample_producer(sample_number=1, ps_energy=30.0),
    )
    session = append_worldbridge_live_capture_session_evidence(
        session,
        _sample_producer(sample_number=2, ps_energy=29.5),
    )
    session = seal_worldbridge_live_capture_session(session)
    validation = validate_worldbridge_live_capture_session(session)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_live_capture_session_contract",
        "read_only": True,
        "contract_valid": bool(validation["valid"]),
        "session": session,
        "validation": validation,
        "scheduler_owned": False,
        "time_aligned": False,
        "causality_inferred": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _validated_session_copy(
    session: Mapping[str, Any],
    *,
    required_lifecycle: str,
) -> dict[str, Any]:
    validation = validate_worldbridge_live_capture_session(session)
    if not validation["valid"]:
        raise ValueError("invalid capture session: " + ",".join(validation["errors"]))
    if session.get("lifecycle") != required_lifecycle:
        raise RuntimeError(
            f"capture session must be {required_lifecycle}, got {session.get('lifecycle')}"
        )
    return copy.deepcopy(dict(session))


def _normalize_evidence(evidence: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    if not isinstance(evidence, Mapping):
        raise TypeError("capture evidence must be a mapping")
    try:
        producer_validation = validate_worldbridge_live_dual_lane_trace(evidence)
    except (KeyError, IndexError, TypeError, ValueError):
        producer_validation = {"valid": False, "errors": ["producer_validation_failed"]}
    if producer_validation["valid"]:
        evaluation = evaluate_worldbridge_live_trace_fields(evidence)
        evaluation_validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
        if not evaluation_validation["valid"]:
            raise ValueError("generated E217 evaluation invalid")
        return copy.deepcopy(evaluation), "e216_live_producer"

    try:
        evaluation_validation = validate_worldbridge_live_trace_field_evaluation(evidence)
    except (KeyError, IndexError, TypeError, ValueError):
        evaluation_validation = {"valid": False, "errors": ["evaluation_validation_failed"]}
    if evaluation_validation["valid"]:
        return copy.deepcopy(dict(evidence)), "e217_field_evaluation"
    raise ValueError(
        "capture evidence must be a validated E216 producer or E217 evaluation"
    )


def _session_id(value: object) -> str:
    return _required_clean_string(value, "session_id", maximum=128)


def _required_clean_string(value: object, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise ValueError(f"{field} must be a clean non-empty string up to {maximum} characters")
    return value


def _sample_capacity(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_SESSION_SAMPLES:
        raise ValueError(f"max_samples must be an integer from 1 to {MAX_SESSION_SAMPLES}")
    return value


def _sample_id(session_id: object, sample_index: int) -> str:
    return f"{session_id}:sample-{sample_index:04d}"


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _session_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("session_digest", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sample_producer(*, sample_number: int, ps_energy: float) -> dict[str, Any]:
    shared = {
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
    }
    return build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 1.0 + sample_number / 10.0,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {
                    "entity_id": "sr:session",
                    "linked_id": "ps:session",
                    "energy": 30.0,
                    **shared,
                }
            ],
        },
        {
            "tick": sample_number,
            "iteration": sample_number,
            "population": 1,
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [
                {
                    "organism_id": "ps:session",
                    "linked_id": "sr:session",
                    "energy": ps_energy,
                    **shared,
                }
            ],
        },
        entity_links=[
            {"sr_entity_id": "sr:session", "ps_organism_id": "ps:session"}
        ],
        observed_sr_delta=0.05,
    )


__all__ = [
    "abort_worldbridge_live_capture_session",
    "append_worldbridge_live_capture_session_evidence",
    "build_worldbridge_live_capture_session_contract",
    "seal_worldbridge_live_capture_session",
    "start_worldbridge_live_capture_session",
    "validate_worldbridge_live_capture_session",
]
