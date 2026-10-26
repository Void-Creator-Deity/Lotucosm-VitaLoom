# -*- coding: utf-8 -*-
"""Qt-free aggregation for ordered E217 live comparability evaluations."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    COMPARABLE_RULES,
    NON_COMPARABLE_LEDGER_FIELDS,
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
    declared_worldbridge_mapping_losses,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    build_worldbridge_live_dual_lane_trace,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_live_dual_lane_comparability_time_series"
AGGREGATION_SCOPE = "ordered_samples_without_time_alignment_or_causality"
ALLOWED_CLASSIFICATIONS = frozenset(
    (
        "stable_pass",
        "repeated_mismatch_observed",
        "intermittent_observation",
        "insufficient_observation",
    )
)
DO_NOT_CLAIM = (
    "common_sr_ps_time_alignment",
    "cross_sample_causality",
    "replay_divergence",
    "atomic_sr_ps_checkpoint",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def aggregate_worldbridge_live_trace_evaluations(
    samples: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate explicitly ordered, validated E217 evaluations read-only."""
    normalized = _normalize_samples(samples)
    pair_keys = sorted(
        {
            (pair["sr_entity_id"], pair["ps_organism_id"])
            for sample in normalized
            for pair in sample["evaluation"]["pair_results"]
        }
    )
    expected_fields = [rule["field"] for rule in COMPARABLE_RULES]
    expected_fields.extend(NON_COMPARABLE_LEDGER_FIELDS)
    expected_fields.extend(declared_worldbridge_mapping_losses())
    field_counts = {status: 0 for status in _field_statuses()}
    pair_results: list[dict[str, Any]] = []
    classification_counts = {classification: 0 for classification in sorted(ALLOWED_CLASSIFICATIONS)}

    for sr_id, ps_id in pair_keys:
        field_results: list[dict[str, Any]] = []
        for field in sorted(expected_fields):
            observations: list[dict[str, Any]] = []
            for sample in normalized:
                observation = _build_observation(sample, sr_id, ps_id, field)
                status = observation["status"]
                field_counts[status] += 1
                observations.append(observation)
            classification = _classify_observations(observations)
            classification_counts[classification] += 1
            field_results.append(
                {
                    "field": field,
                    "classification": classification,
                    "observations": observations,
                }
            )
        pair_results.append(
            {
                "sr_entity_id": sr_id,
                "ps_organism_id": ps_id,
                "pair_key_status": "exact_link_key_match",
                "field_results": field_results,
            }
        )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "aggregation_scope": AGGREGATION_SCOPE,
        "sample_count": len(normalized),
        "samples": normalized,
        "source_trace_digests": [sample["evaluation"]["source_trace_digest"] for sample in normalized],
        "source_evaluation_digests": [sample["evaluation"]["evaluation_digest"] for sample in normalized],
        "pair_count": len(pair_results),
        "pair_results": pair_results,
        "field_status_counts": field_counts,
        "classification_counts": classification_counts,
        "clocks_compared": False,
        "time_aligned": False,
        "causality_inferred": False,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "declared_mapping_losses": declared_worldbridge_mapping_losses(),
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["aggregation_digest"] = _aggregation_digest(result)
    return result


def validate_worldbridge_live_trace_time_series(value: object) -> dict[str, Any]:
    """Validate aggregation structure, sample identity, and no-claim invariants."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["aggregation_must_be_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("aggregation_scope") != AGGREGATION_SCOPE:
        errors.append("aggregation_scope_overclaim")
    for field, error in (
        ("clocks_compared", "clock_equality_not_admitted"),
        ("time_aligned", "time_alignment_not_admitted"),
        ("causality_inferred", "causality_not_admitted"),
        ("atomic_checkpoint", "atomic_checkpoint_not_admitted"),
        ("lossless", "lossless_mapping_not_admitted"),
        ("replay_admitted", "unified_replay_not_admitted"),
        ("default_ready", "default_ready_not_admitted"),
    ):
        if value.get(field) is not False:
            errors.append(error)
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("declared_mapping_losses") != declared_worldbridge_mapping_losses():
        errors.append("declared_mapping_losses_mismatch")

    samples = value.get("samples")
    sample_ids: set[str] = set()
    sample_indices: set[int] = set()
    source_digests: set[str] = set()
    structurally_valid_samples: list[Mapping[str, Any]] = []
    if not isinstance(samples, list) or not samples:
        errors.append("samples_missing")
        samples = []
    for sample in samples:
        if not isinstance(sample, Mapping):
            errors.append("sample_invalid")
            continue
        sample_valid = True
        sample_id = sample.get("sample_id")
        sample_index = sample.get("sample_index")
        if (
            not isinstance(sample_id, str)
            or not sample_id.strip()
            or sample_id != sample_id.strip()
            or sample_id in sample_ids
        ):
            errors.append("sample_id_duplicate_or_invalid")
            sample_valid = False
        else:
            sample_ids.add(sample_id)
        if isinstance(sample_index, bool) or not isinstance(sample_index, int) or sample_index < 0 or sample_index in sample_indices:
            errors.append("sample_index_duplicate_or_invalid")
            sample_valid = False
        else:
            sample_indices.add(sample_index)
        evaluation = sample.get("evaluation")
        try:
            evaluation_validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
        except (KeyError, IndexError, TypeError, ValueError):
            evaluation_validation = {"valid": False, "errors": ["nested_evaluation_validation_failed"]}
        if not evaluation_validation["valid"]:
            errors.append("nested_evaluation_invalid")
            sample_valid = False
        if isinstance(evaluation, Mapping):
            source_digest = evaluation.get("source_trace_digest")
            if not isinstance(source_digest, str) or not source_digest or source_digest in source_digests:
                errors.append("source_trace_digest_duplicate_or_invalid")
                sample_valid = False
            else:
                source_digests.add(source_digest)
        else:
            sample_valid = False
        if sample_valid:
            structurally_valid_samples.append(sample)
    if value.get("sample_count") != len(samples):
        errors.append("sample_count_mismatch")
    if value.get("source_trace_digests") != [sample.get("evaluation", {}).get("source_trace_digest") for sample in samples if isinstance(sample, Mapping) and isinstance(sample.get("evaluation"), Mapping)]:
        errors.append("source_trace_digests_mismatch")
    if value.get("source_evaluation_digests") != [sample.get("evaluation", {}).get("evaluation_digest") for sample in samples if isinstance(sample, Mapping) and isinstance(sample.get("evaluation"), Mapping)]:
        errors.append("source_evaluation_digests_mismatch")

    ordered_sample_keys = [
        (sample["sample_index"], sample["sample_id"])
        for sample in structurally_valid_samples
    ]
    if len(structurally_valid_samples) == len(samples) and ordered_sample_keys != sorted(ordered_sample_keys):
        errors.append("sample_order_mismatch")

    pair_results = value.get("pair_results")
    if not isinstance(pair_results, list):
        errors.append("pair_results_missing")
        pair_results = []
    if value.get("pair_count") != len(pair_results):
        errors.append("pair_count_mismatch")
    seen_pairs: set[tuple[str, str]] = set()
    expected_fields = {
        *(rule["field"] for rule in COMPARABLE_RULES),
        *NON_COMPARABLE_LEDGER_FIELDS,
        *declared_worldbridge_mapping_losses(),
    }
    expected_pair_keys = {
        (pair.get("sr_entity_id"), pair.get("ps_organism_id"))
        for sample in structurally_valid_samples
        for pair in sample["evaluation"].get("pair_results", [])
        if isinstance(pair, Mapping)
    }
    for pair in pair_results:
        if not isinstance(pair, Mapping):
            errors.append("pair_result_invalid")
            continue
        key = (pair.get("sr_entity_id"), pair.get("ps_organism_id"))
        if not isinstance(key[0], str) or not isinstance(key[1], str) or key in seen_pairs:
            errors.append("pair_key_duplicate_or_invalid")
        else:
            seen_pairs.add(key)
        if pair.get("pair_key_status") != "exact_link_key_match":
            errors.append("pair_key_status_not_exact")
        field_results = pair.get("field_results")
        if not isinstance(field_results, list):
            errors.append("field_results_missing")
            continue
        seen_fields: set[str] = set()
        for field_result in field_results:
            if not isinstance(field_result, Mapping):
                errors.append("field_result_invalid")
                continue
            field = field_result.get("field")
            classification = field_result.get("classification")
            if not isinstance(field, str) or field in seen_fields or field not in expected_fields:
                errors.append("field_result_name_invalid")
            else:
                seen_fields.add(field)
            if not isinstance(classification, str) or classification not in ALLOWED_CLASSIFICATIONS:
                errors.append("classification_invalid")
            observations = field_result.get("observations")
            if not isinstance(observations, list) or len(observations) != len(samples):
                errors.append("observation_count_invalid")
                continue
            observations_valid = True
            can_rebuild = (
                len(structurally_valid_samples) == len(samples)
                and isinstance(pair.get("sr_entity_id"), str)
                and isinstance(pair.get("ps_organism_id"), str)
                and isinstance(field, str)
                and field in expected_fields
            )
            for sample, observation in zip(samples, observations):
                if not isinstance(observation, Mapping) or observation.get("status") not in _field_statuses():
                    errors.append("observation_status_invalid")
                    observations_valid = False
                    continue
                if not isinstance(sample, Mapping) or not can_rebuild:
                    observations_valid = False
                    continue
                expected_observation = _build_observation(
                    sample,
                    pair["sr_entity_id"],
                    pair["ps_organism_id"],
                    field,
                )
                if observation != expected_observation:
                    errors.append("observation_evidence_mismatch")
            if observations_valid and classification != _classify_observations(observations):
                errors.append("classification_observation_mismatch")
        if seen_fields != expected_fields:
            errors.append("field_result_set_mismatch")
    if seen_pairs != expected_pair_keys:
        errors.append("pair_result_set_mismatch")
    if value.get("field_status_counts") != _recount_field_statuses(pair_results):
        errors.append("field_status_counts_mismatch")
    if value.get("classification_counts") != _recount_classifications(pair_results):
        errors.append("classification_counts_mismatch")

    digest = value.get("aggregation_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("aggregation_digest_invalid")
    try:
        expected_digest = _aggregation_digest(value)
    except (TypeError, ValueError):
        errors.append("aggregation_not_json_safe")
    else:
        if digest != expected_digest:
            errors.append("aggregation_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_live_trace_time_series_contract() -> dict[str, Any]:
    """Build deterministic E218 evidence without importing the Qt host."""
    samples = [
        {"sample_id": "sample-0001", "sample_index": 0, "evaluation": _sample_evaluation(30.0)},
        {"sample_id": "sample-0002", "sample_index": 1, "evaluation": _sample_evaluation(29.5)},
    ]
    aggregation = aggregate_worldbridge_live_trace_evaluations(samples)
    validation = validate_worldbridge_live_trace_time_series(aggregation)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_live_trace_time_series_contract",
        "read_only": True,
        "contract_valid": bool(validation["valid"]),
        "aggregation": aggregation,
        "validation": validation,
        "time_aligned": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _normalize_samples(samples: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    sample_ids: set[str] = set()
    sample_indices: set[int] = set()
    source_digests: set[str] = set()
    for index, raw_sample in enumerate(samples):
        if not isinstance(raw_sample, Mapping):
            raise TypeError(f"samples[{index}] must be a mapping")
        sample_id = raw_sample.get("sample_id")
        sample_index = raw_sample.get("sample_index")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError(f"samples[{index}].sample_id must be a non-empty string")
        sample_id = sample_id.strip()
        if sample_id in sample_ids:
            raise ValueError(f"duplicate sample_id: {sample_id}")
        if isinstance(sample_index, bool) or not isinstance(sample_index, int) or sample_index < 0:
            raise ValueError(f"samples[{index}].sample_index must be a non-negative integer")
        if sample_index in sample_indices:
            raise ValueError(f"duplicate sample_index: {sample_index}")
        evaluation = raw_sample.get("evaluation")
        validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
        if not validation["valid"]:
            raise ValueError("invalid E217 evaluation: " + ",".join(validation["errors"]))
        source_digest = evaluation["source_trace_digest"]
        if source_digest in source_digests:
            raise ValueError(f"duplicate source_trace_digest: {source_digest}")
        sample_ids.add(sample_id)
        sample_indices.add(sample_index)
        source_digests.add(source_digest)
        normalized.append(
            {
                "sample_id": sample_id,
                "sample_index": sample_index,
                "evaluation": copy.deepcopy(dict(evaluation)),
            }
        )
    if not normalized:
        raise ValueError("at least one E217 evaluation is required")
    return sorted(normalized, key=lambda item: (item["sample_index"], item["sample_id"]))


def _sample_evaluation(energy: float) -> dict[str, Any]:
    shared = {
        "position": [1.0, 2.0],
        "velocity": [0.5, 0.25],
        "acceleration": [0.0, 0.0],
        "health": 20.0,
        "size": 8.0,
        "radius": 4.0,
    }
    payload = build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 1.25,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {"entity_id": "sr:sample", "linked_id": "ps:sample", "energy": 30.0, **shared}
            ],
        },
        {
            "tick": int(energy),
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [
                {"organism_id": "ps:sample", "linked_id": "sr:sample", "energy": energy, **shared}
            ],
        },
        entity_links=[{"sr_entity_id": "sr:sample", "ps_organism_id": "ps:sample"}],
        observed_sr_delta=0.05,
    )
    return evaluate_worldbridge_live_trace_fields(payload)


def _pair_from_evaluation(evaluation: Mapping[str, Any], sr_id: str, ps_id: str) -> Mapping[str, Any] | None:
    for pair in evaluation["pair_results"]:
        if pair["sr_entity_id"] == sr_id and pair["ps_organism_id"] == ps_id:
            return pair
    return None


def _field_from_pair(pair: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    for result in pair["fields"]:
        if result["field"] == field:
            return result
    raise ValueError(f"missing E217 field: {field}")


def _build_observation(
    sample: Mapping[str, Any],
    sr_id: str,
    ps_id: str,
    field: str,
) -> dict[str, Any]:
    pair = _pair_from_evaluation(sample["evaluation"], sr_id, ps_id)
    if pair is None:
        return {
            "sample_id": sample["sample_id"],
            "sample_index": sample["sample_index"],
            "sample_pair_present": False,
            "status": "not_observed",
            "reason": "pair_not_present_in_sample",
        }
    field_result = _field_from_pair(pair, field)
    return {
        "sample_id": sample["sample_id"],
        "sample_index": sample["sample_index"],
        "sample_pair_present": True,
        "status": field_result["status"],
        "absolute_delta": field_result.get("absolute_delta"),
        "max_absolute_delta": field_result.get("max_absolute_delta"),
    }


def _classify_observations(observations: list[Mapping[str, Any]]) -> str:
    if len(observations) < 2 or any(observation.get("sample_pair_present") is not True for observation in observations):
        return "insufficient_observation"
    statuses = [observation["status"] for observation in observations]
    if all(status == "comparable_pass" for status in statuses):
        return "stable_pass"
    if all(status == "comparable_mismatch" for status in statuses):
        return "repeated_mismatch_observed"
    if set(statuses).issubset({"comparable_pass", "comparable_mismatch"}):
        return "intermittent_observation"
    return "insufficient_observation"


def _field_statuses() -> tuple[str, ...]:
    return ("comparable_mismatch", "comparable_pass", "declared_loss", "not_observed")


def _recount_field_statuses(pair_results: object) -> dict[str, int]:
    counts = {status: 0 for status in _field_statuses()}
    if not isinstance(pair_results, list):
        return counts
    for pair in pair_results:
        if not isinstance(pair, Mapping) or not isinstance(pair.get("field_results"), list):
            continue
        for field_result in pair["field_results"]:
            if not isinstance(field_result, Mapping) or not isinstance(field_result.get("observations"), list):
                continue
            for observation in field_result["observations"]:
                if isinstance(observation, Mapping) and observation.get("status") in counts:
                    counts[observation["status"]] += 1
    return counts


def _recount_classifications(pair_results: object) -> dict[str, int]:
    counts = {classification: 0 for classification in sorted(ALLOWED_CLASSIFICATIONS)}
    if not isinstance(pair_results, list):
        return counts
    for pair in pair_results:
        if not isinstance(pair, Mapping) or not isinstance(pair.get("field_results"), list):
            continue
        for field_result in pair["field_results"]:
            if not isinstance(field_result, Mapping):
                continue
            classification = field_result.get("classification")
            if isinstance(classification, str) and classification in counts:
                counts[classification] += 1
    return counts


def _aggregation_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("aggregation_digest", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "aggregate_worldbridge_live_trace_evaluations",
    "build_worldbridge_live_trace_time_series_contract",
    "validate_worldbridge_live_trace_time_series",
]
