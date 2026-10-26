# -*- coding: utf-8 -*-
"""Qt-free field evaluator for validated E216 live WorldBridge traces.

Values come from different ordered observation points.  A mismatch is an
observed cross-boundary drift, not proof of replay divergence or engine error.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from numbers import Real
from typing import Any

from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    validate_worldbridge_live_dual_lane_trace,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
    declared_worldbridge_mapping_losses,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_live_dual_lane_field_comparability"
COMPARISON_SCOPE = "ordered_cross_boundary_observation_not_same_instant_parity"
FLOAT_NOISE_TOLERANCE = 1e-9
ALLOWED_FIELD_STATUSES = frozenset(
    ("comparable_pass", "comparable_mismatch", "not_observed", "declared_loss")
)
COMPARABLE_RULES: tuple[dict[str, Any], ...] = (
    {"field": "position", "ledger_field": "position", "kind": "vector2"},
    {"field": "energy", "ledger_field": "energy", "kind": "scalar"},
    {"field": "health", "ledger_field": "health", "kind": "scalar"},
    {"field": "size", "ledger_field": "size_radius", "kind": "scalar"},
    {"field": "radius", "ledger_field": "size_radius", "kind": "scalar"},
    {"field": "velocity", "ledger_field": "velocity_acceleration", "kind": "vector2"},
    {"field": "acceleration", "ledger_field": "velocity_acceleration", "kind": "vector2"},
)
NON_COMPARABLE_LEDGER_FIELDS = (
    "max_energy",
    "max_health",
    "developmental_profile",
    "social_enabled",
)
DO_NOT_CLAIM = (
    "same_instant_sr_ps_parity",
    "atomic_sr_ps_checkpoint",
    "shared_sr_ps_clock",
    "lossless_worldbridge_mapping",
    "full_unified_runtime_replay",
    "unified_pond_default_ready",
)


def evaluate_worldbridge_live_trace_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate mapped fields from a validated E216 producer payload."""
    producer_validation = validate_worldbridge_live_dual_lane_trace(payload)
    if not producer_validation["valid"]:
        raise ValueError(
            "invalid live trace producer payload: " + ",".join(producer_validation["errors"])
        )
    trace = payload["trace"]
    lanes = trace["lanes"]
    sr_checkpoint = lanes["sr"]["checkpoint"]
    ps_checkpoint = lanes["ps"]["checkpoint"]
    sr_rows = _rows_by_id(sr_checkpoint["bridged_entities"], "entity_id")
    ps_rows = _rows_by_id(ps_checkpoint["bridged_organisms"], "organism_id")
    audit = build_worldbridge_mapping_audit()
    ledger = audit["fields"]

    pair_results: list[dict[str, Any]] = []
    counts = {status: 0 for status in sorted(ALLOWED_FIELD_STATUSES)}
    for link in trace["entity_links"]:
        sr_id = link["sr_entity_id"]
        ps_id = link["ps_organism_id"]
        sr_row = sr_rows[sr_id]
        if ps_id not in ps_rows:
            retired = ps_checkpoint.get("retired_bridge_links", [])
            retired_match = any(
                isinstance(row, Mapping)
                and row.get("sr_entity_id") == sr_id
                and row.get("ps_organism_id") == ps_id
                for row in retired
            )
            if not retired_match:
                raise ValueError(f"missing PS row without retired link: {sr_id}->{ps_id}")
            fields = []
            for rule in COMPARABLE_RULES:
                fields.append(_not_observed(rule, sr_row.get(rule["field"]), None))
                counts["not_observed"] += 1
            for field in NON_COMPARABLE_LEDGER_FIELDS:
                ledger_item = ledger[field]
                fields.append({
                    "field": field,
                    "ledger_field": field,
                    "status": "not_observed",
                    "reason": f"ledger_{ledger_item['state']}_{ledger_item['direction']}_not_live_comparable",
                })
                counts["not_observed"] += 1
            for field in declared_worldbridge_mapping_losses(audit):
                fields.append({
                    "field": field,
                    "ledger_field": field,
                    "status": "declared_loss",
                    "reason": "worldbridge_mapping_ledger_not_mapped",
                })
                counts["declared_loss"] += 1
            pair_results.append({
                "sr_entity_id": sr_id,
                "ps_organism_id": ps_id,
                "relation": link["relation"],
                "pair_key_status": "exact_link_key_match",
                "comparable_status": "not_observed",
                "fields": sorted(fields, key=lambda item: item["field"]),
            })
            continue
        ps_row = ps_rows[ps_id]
        _validate_pair_linked_ids(sr_row, ps_row, sr_id, ps_id)
        fields: list[dict[str, Any]] = []
        for rule in COMPARABLE_RULES:
            ledger_item = ledger[rule["ledger_field"]]
            if ledger_item.get("state") != "covered":
                raise ValueError(f"ledger field is not covered: {rule['ledger_field']}")
            result = _compare_field(sr_row, ps_row, rule)
            fields.append(result)
            counts[result["status"]] += 1
        for field in NON_COMPARABLE_LEDGER_FIELDS:
            ledger_item = ledger[field]
            result = {
                "field": field,
                "ledger_field": field,
                "status": "not_observed",
                "reason": f"ledger_{ledger_item['state']}_{ledger_item['direction']}_not_live_comparable",
            }
            fields.append(result)
            counts["not_observed"] += 1
        for field in declared_worldbridge_mapping_losses(audit):
            fields.append(
                {
                    "field": field,
                    "ledger_field": field,
                    "status": "declared_loss",
                    "reason": "worldbridge_mapping_ledger_not_mapped",
                }
            )
            counts["declared_loss"] += 1
        pair_status = _aggregate_comparable_status(fields)
        pair_results.append(
            {
                "sr_entity_id": sr_id,
                "ps_organism_id": ps_id,
                "relation": link["relation"],
                "pair_key_status": "exact_link_key_match",
                "comparable_status": pair_status,
                "fields": sorted(fields, key=lambda item: item["field"]),
            }
        )

    aggregate_status = _aggregate_pair_status(pair_results)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "comparison_scope": COMPARISON_SCOPE,
        "source_producer_status": payload["status"],
        "source_producer_digest": payload["producer_digest"],
        "source_trace_digest": trace["trace_digest"],
        "field_tolerance_policy": {
            "name": "finite_float_representation_noise_only",
            "absolute_tolerance": FLOAT_NOISE_TOLERANCE,
            "relative_tolerance": 0.0,
            "semantic_drift_budget": None,
        },
        "pair_count": len(pair_results),
        "pair_results": pair_results,
        "field_status_counts": counts,
        "aggregate_comparable_status": aggregate_status,
        "clocks_compared": False,
        "same_instant_parity": False,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "declared_mapping_losses": declared_worldbridge_mapping_losses(audit),
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    result["evaluation_digest"] = _evaluation_digest(result)
    return result


def validate_worldbridge_live_trace_field_evaluation(value: object) -> dict[str, Any]:
    """Validate evaluator output and all non-admission invariants."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["evaluation_must_be_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("comparison_scope") != COMPARISON_SCOPE:
        errors.append("comparison_scope_overclaim")
    if value.get("clocks_compared") is not False:
        errors.append("clock_equality_not_admitted")
    if value.get("same_instant_parity") is not False:
        errors.append("same_instant_parity_not_admitted")
    if value.get("atomic_checkpoint") is not False:
        errors.append("atomic_checkpoint_not_admitted")
    for field, error in (
        ("lossless", "lossless_mapping_not_admitted"),
        ("replay_admitted", "unified_replay_not_admitted"),
        ("default_ready", "default_ready_not_admitted"),
    ):
        if value.get(field) is not False:
            errors.append(error)
    tolerance = value.get("field_tolerance_policy")
    if not isinstance(tolerance, Mapping) or tolerance.get("absolute_tolerance") != FLOAT_NOISE_TOLERANCE:
        errors.append("field_tolerance_policy_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    audit_losses = declared_worldbridge_mapping_losses()
    if value.get("declared_mapping_losses") != audit_losses:
        errors.append("declared_mapping_losses_mismatch")

    pair_results = value.get("pair_results")
    observed_counts = {status: 0 for status in sorted(ALLOWED_FIELD_STATUSES)}
    if not isinstance(pair_results, list):
        errors.append("pair_results_missing")
    else:
        if value.get("pair_count") != len(pair_results):
            errors.append("pair_count_mismatch")
        seen_sr: set[str] = set()
        seen_ps: set[str] = set()
        for pair in pair_results:
            if not isinstance(pair, Mapping):
                errors.append("pair_result_invalid")
                continue
            sr_id = pair.get("sr_entity_id")
            ps_id = pair.get("ps_organism_id")
            if not isinstance(sr_id, str) or sr_id in seen_sr:
                errors.append("duplicate_or_invalid_sr_pair")
            else:
                seen_sr.add(sr_id)
            if not isinstance(ps_id, str) or ps_id in seen_ps:
                errors.append("duplicate_or_invalid_ps_pair")
            else:
                seen_ps.add(ps_id)
            if pair.get("pair_key_status") != "exact_link_key_match":
                errors.append("pair_key_status_not_exact")
            if not isinstance(pair.get("relation"), str) or not pair.get("relation"):
                errors.append("pair_relation_invalid")
            fields = pair.get("fields")
            if not isinstance(fields, list):
                errors.append("pair_fields_missing")
                continue
            expected_fields = {
                *(rule["field"] for rule in COMPARABLE_RULES),
                *NON_COMPARABLE_LEDGER_FIELDS,
                *declared_worldbridge_mapping_losses(),
            }
            seen_fields: set[str] = set()
            comparable_statuses: list[str] = []
            for item in fields:
                if not isinstance(item, Mapping) or item.get("status") not in ALLOWED_FIELD_STATUSES:
                    errors.append("field_status_invalid")
                    continue
                field = item.get("field")
                if not isinstance(field, str) or field in seen_fields:
                    errors.append("field_name_duplicate_or_invalid")
                    continue
                seen_fields.add(field)
                if field not in expected_fields:
                    errors.append("field_name_unexpected")
                    continue
                expected_ledger_field = _expected_ledger_field(field)
                if item.get("ledger_field") != expected_ledger_field:
                    errors.append("field_ledger_mapping_mismatch")
                if field in {rule["field"] for rule in COMPARABLE_RULES}:
                    rule = next(rule for rule in COMPARABLE_RULES if rule["field"] == field)
                    _validate_comparable_field_result(item, rule, errors)
                elif field in NON_COMPARABLE_LEDGER_FIELDS:
                    if item.get("status") != "not_observed" or not isinstance(item.get("reason"), str):
                        errors.append("non_comparable_field_status_invalid")
                else:
                    if item.get("status") != "declared_loss" or item.get("reason") != "worldbridge_mapping_ledger_not_mapped":
                        errors.append("declared_loss_field_status_invalid")
                status = item["status"]
                observed_counts[status] += 1
                if status in ("comparable_pass", "comparable_mismatch"):
                    comparable_statuses.append(status)
            if seen_fields != expected_fields:
                errors.append("field_set_mismatch")
            expected_pair_status = (
                "comparable_mismatch"
                if "comparable_mismatch" in comparable_statuses
                else "comparable_pass"
                if "comparable_pass" in comparable_statuses
                else "not_observed"
            )
            if pair.get("comparable_status") != expected_pair_status:
                errors.append("pair_comparable_status_mismatch")
    if value.get("field_status_counts") != observed_counts:
        errors.append("field_status_counts_mismatch")
    expected_aggregate = _aggregate_pair_status(pair_results if isinstance(pair_results, list) else [])
    if value.get("aggregate_comparable_status") != expected_aggregate:
        errors.append("aggregate_comparable_status_mismatch")

    digest = value.get("evaluation_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("evaluation_digest_invalid")
    try:
        expected_digest = _evaluation_digest(value)
    except (TypeError, ValueError):
        errors.append("evaluation_not_json_safe")
    else:
        if digest != expected_digest:
            errors.append("evaluation_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_live_trace_comparability_contract() -> dict[str, Any]:
    """Build stable evaluator evidence from the E216 sample producer."""
    from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
        build_worldbridge_live_dual_lane_trace,
    )

    producer = build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 0.05,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {
                    "entity_id": "sr:sample",
                    "linked_id": "ps:sample",
                    "position": [1.0, 2.0],
                    "velocity": [0.0, 0.0],
                    "acceleration": [0.0, 0.0],
                    "energy": 10.0,
                    "health": 10.0,
                    "size": 4.0,
                    "radius": 2.0,
                }
            ],
        },
        {
            "tick": 1,
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "bridged_organisms": [
                {
                    "organism_id": "ps:sample",
                    "linked_id": "sr:sample",
                    "position": [1.0, 2.0],
                    "velocity": [0.0, 0.0],
                    "acceleration": [0.0, 0.0],
                    "energy": 9.0,
                    "health": 10.0,
                    "size": 4.0,
                    "radius": 2.0,
                }
            ],
        },
        entity_links=[{"sr_entity_id": "sr:sample", "ps_organism_id": "ps:sample"}],
        observed_sr_delta=0.05,
    )
    evaluation = evaluate_worldbridge_live_trace_fields(producer)
    validation = validate_worldbridge_live_trace_field_evaluation(evaluation)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_live_trace_comparability_contract",
        "read_only": True,
        "contract_valid": bool(validation["valid"]),
        "evaluation": evaluation,
        "validation": validation,
        "tick_merge_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _compare_field(
    sr_row: Mapping[str, Any],
    ps_row: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    field = str(rule["field"])
    kind = str(rule["kind"])
    sr_value = sr_row.get(field)
    ps_value = ps_row.get(field)
    if kind == "scalar":
        sr_number = _finite_number_or_none(sr_value)
        ps_number = _finite_number_or_none(ps_value)
        if sr_number is None or ps_number is None:
            return _not_observed(rule, sr_value, ps_value)
        delta = abs(ps_number - sr_number)
        return {
            "field": field,
            "ledger_field": rule["ledger_field"],
            "status": "comparable_pass" if delta <= FLOAT_NOISE_TOLERANCE else "comparable_mismatch",
            "kind": kind,
            "sr_value": sr_number,
            "ps_value": ps_number,
            "absolute_delta": delta,
            "absolute_tolerance": FLOAT_NOISE_TOLERANCE,
        }
    if kind == "vector2":
        sr_vector = _finite_vector2_or_none(sr_value)
        ps_vector = _finite_vector2_or_none(ps_value)
        if sr_vector is None or ps_vector is None:
            return _not_observed(rule, sr_value, ps_value)
        deltas = [abs(ps_vector[index] - sr_vector[index]) for index in range(2)]
        maximum = max(deltas)
        return {
            "field": field,
            "ledger_field": rule["ledger_field"],
            "status": "comparable_pass" if maximum <= FLOAT_NOISE_TOLERANCE else "comparable_mismatch",
            "kind": kind,
            "sr_value": sr_vector,
            "ps_value": ps_vector,
            "absolute_delta": deltas,
            "max_absolute_delta": maximum,
            "absolute_tolerance": FLOAT_NOISE_TOLERANCE,
        }
    raise ValueError(f"unsupported comparison kind: {kind}")


def _validate_pair_linked_ids(
    sr_row: Mapping[str, Any],
    ps_row: Mapping[str, Any],
    sr_id: str,
    ps_id: str,
) -> None:
    if sr_row.get("entity_id") != sr_id or sr_row.get("linked_id") != ps_id:
        raise ValueError(f"sr bridge pair identity mismatch: {sr_id}->{ps_id}")
    if ps_row.get("organism_id") != ps_id or ps_row.get("linked_id") != sr_id:
        raise ValueError(f"ps bridge pair identity mismatch: {sr_id}->{ps_id}")


def _expected_ledger_field(field: str) -> str:
    for rule in COMPARABLE_RULES:
        if rule["field"] == field:
            return str(rule["ledger_field"])
    if field in NON_COMPARABLE_LEDGER_FIELDS:
        return field
    return field


def _validate_comparable_field_result(
    item: Mapping[str, Any],
    rule: Mapping[str, Any],
    errors: list[str],
) -> None:
    kind = rule["kind"]
    if item.get("kind") != kind:
        errors.append("comparable_field_kind_mismatch")
        return
    if item.get("absolute_tolerance") != FLOAT_NOISE_TOLERANCE:
        errors.append("comparable_field_tolerance_mismatch")
    status = item.get("status")
    if status == "not_observed":
        if not isinstance(item.get("reason"), str):
            errors.append("comparable_not_observed_reason_invalid")
        if not isinstance(item.get("sr_observed"), bool) or not isinstance(item.get("ps_observed"), bool):
            errors.append("comparable_not_observed_flags_invalid")
        return
    if status not in ("comparable_pass", "comparable_mismatch"):
        errors.append("comparable_field_status_invalid")
        return
    if kind == "scalar":
        sr_value = _finite_number_or_none(item.get("sr_value"))
        ps_value = _finite_number_or_none(item.get("ps_value"))
        delta = _finite_number_or_none(item.get("absolute_delta"))
        if sr_value is None or ps_value is None or delta is None:
            errors.append("scalar_comparison_values_invalid")
            return
        expected_delta = abs(ps_value - sr_value)
        if delta != expected_delta:
            errors.append("scalar_comparison_delta_mismatch")
        expected_status = "comparable_pass" if expected_delta <= FLOAT_NOISE_TOLERANCE else "comparable_mismatch"
        if status != expected_status:
            errors.append("scalar_comparison_status_mismatch")
        return
    sr_vector = _finite_vector2_or_none(item.get("sr_value"))
    ps_vector = _finite_vector2_or_none(item.get("ps_value"))
    deltas = item.get("absolute_delta")
    maximum = _finite_number_or_none(item.get("max_absolute_delta"))
    if sr_vector is None or ps_vector is None or not isinstance(deltas, list) or len(deltas) != 2 or maximum is None:
        errors.append("vector_comparison_values_invalid")
        return
    expected_deltas = [abs(ps_vector[index] - sr_vector[index]) for index in range(2)]
    if deltas != expected_deltas or maximum != max(expected_deltas):
        errors.append("vector_comparison_delta_mismatch")
    expected_status = "comparable_pass" if max(expected_deltas) <= FLOAT_NOISE_TOLERANCE else "comparable_mismatch"
    if status != expected_status:
        errors.append("vector_comparison_status_mismatch")


def _not_observed(rule: Mapping[str, Any], sr_value: object, ps_value: object) -> dict[str, Any]:
    return {
        "field": rule["field"],
        "ledger_field": rule["ledger_field"],
        "kind": rule["kind"],
        "status": "not_observed",
        "reason": "finite_value_missing_on_one_or_both_lanes",
        "sr_observed": sr_value is not None,
        "ps_observed": ps_value is not None,
        "absolute_tolerance": FLOAT_NOISE_TOLERANCE,
    }


def _rows_by_id(rows: object, identity_field: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError(f"{identity_field} rows must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"{identity_field} row must be a mapping")
        identity = row.get(identity_field)
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError(f"{identity_field} must be a non-empty string")
        normalized = identity.strip()
        if normalized in result:
            raise ValueError(f"duplicate {identity_field}: {normalized}")
        result[normalized] = row
    return result


def _finite_number_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _finite_vector2_or_none(value: object) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    projected = [_finite_number_or_none(value[0]), _finite_number_or_none(value[1])]
    return [float(projected[0]), float(projected[1])] if all(item is not None for item in projected) else None


def _aggregate_comparable_status(fields: list[Mapping[str, Any]]) -> str:
    statuses = [item.get("status") for item in fields]
    if "comparable_mismatch" in statuses:
        return "comparable_mismatch"
    if "comparable_pass" in statuses:
        return "comparable_pass"
    return "not_observed"


def _aggregate_pair_status(pair_results: list[Mapping[str, Any]]) -> str:
    statuses = [item.get("comparable_status") for item in pair_results if isinstance(item, Mapping)]
    if "comparable_mismatch" in statuses:
        return "comparable_mismatch"
    if "comparable_pass" in statuses:
        return "comparable_pass"
    return "not_observed"


def _evaluation_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("evaluation_digest", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "build_worldbridge_live_trace_comparability_contract",
    "evaluate_worldbridge_live_trace_fields",
    "validate_worldbridge_live_trace_field_evaluation",
]

