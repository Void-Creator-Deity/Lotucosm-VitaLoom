# -*- coding: utf-8 -*-
"""Qt-free deterministic trace packaging for separate SR and PS lanes.

The trace is comparison evidence only. It does not merge clocks, establish
cross-track identity, persist a shared checkpoint, or admit unified replay.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
    declared_worldbridge_mapping_losses,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_dual_lane_tick_trace"
IDENTITY_RELATION = "bridge_pair_not_identity_equivalence"
SR_CLOCK_DOMAIN = "sr_scaled_scene_seconds"
PS_CLOCK_DOMAIN = "ps_pond_unit_ticks"
DO_NOT_CLAIM = (
    "shared_sr_ps_clock",
    "cross_track_identity_equivalence",
    "lossless_worldbridge_mapping",
    "full_unified_runtime_replay",
    "unified_pond_default_ready",
)


def build_worldbridge_dual_lane_trace(
    sr_checkpoint: Mapping[str, Any],
    ps_checkpoint: Mapping[str, Any],
    *,
    entity_links: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Package copy-isolated lane checkpoints into one deterministic trace."""
    sr = _json_mapping_copy(sr_checkpoint, "sr_checkpoint")
    ps = _json_mapping_copy(ps_checkpoint, "ps_checkpoint")
    links = _normalize_links(entity_links)
    audit = build_worldbridge_mapping_audit()

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "determinism_scope": "snapshot_packaging_only",
        "lanes": {
            "sr": {
                "track": "sr_play",
                "clock_domain": SR_CLOCK_DOMAIN,
                "clock_value": _finite_number(sr.get("sim_time", 0.0), "sr_checkpoint.sim_time"),
                "tick_index": _optional_non_negative_int(sr.get("tick"), "sr_checkpoint.tick"),
                "checkpoint": sr,
            },
            "ps": {
                "track": "ps_batch",
                "clock_domain": PS_CLOCK_DOMAIN,
                "clock_value": _non_negative_int(ps.get("tick", 0), "ps_checkpoint.tick"),
                "checkpoint": ps,
            },
        },
        "bridge_boundary": {
            "phase": "after_sr_snapshot_work_before_sr_snapshot_publication",
            "operation_order": [
                "sync_sr_to_ps",
                "pond_update_fixed_step",
                "sync_ps_to_sr_display",
            ],
            "sr_delta_consumed_by_pond": False,
        },
        "entity_links": links,
        "identity_relation": IDENTITY_RELATION,
        "declared_mapping_losses": declared_worldbridge_mapping_losses(audit),
        "existing_runner_scope": "ps_batch_vs_ps_unified_bridge_adapter_not_live_sr_ps_trace",
        "shared_clock": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    payload["trace_digest"] = _trace_digest(payload)
    return payload


def validate_worldbridge_dual_lane_trace(trace: object) -> dict[str, Any]:
    """Return deterministic errors for a malformed or over-claiming trace."""
    errors: list[str] = []
    if not isinstance(trace, Mapping):
        return {"valid": False, "errors": ["trace_must_be_mapping"]}

    if trace.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if trace.get("status") != STATUS:
        errors.append("status_mismatch")
    if trace.get("read_only") is not True:
        errors.append("read_only_required")
    if trace.get("determinism_scope") != "snapshot_packaging_only":
        errors.append("determinism_scope_overclaim")
    if trace.get("shared_clock") is not False:
        errors.append("shared_clock_not_admitted")
    if trace.get("lossless") is not False:
        errors.append("lossless_mapping_not_admitted")
    if trace.get("replay_admitted") is not False:
        errors.append("unified_replay_not_admitted")
    if trace.get("default_ready") is not False:
        errors.append("default_ready_not_admitted")
    if trace.get("identity_relation") != IDENTITY_RELATION:
        errors.append("cross_track_identity_not_admitted")

    lanes = trace.get("lanes")
    if not isinstance(lanes, Mapping):
        errors.append("lanes_missing")
    else:
        sr = lanes.get("sr")
        ps = lanes.get("ps")
        if not isinstance(sr, Mapping) or sr.get("clock_domain") != SR_CLOCK_DOMAIN:
            errors.append("sr_clock_domain_mismatch")
        if not isinstance(ps, Mapping) or ps.get("clock_domain") != PS_CLOCK_DOMAIN:
            errors.append("ps_clock_domain_mismatch")
        if isinstance(sr, Mapping) and isinstance(ps, Mapping):
            if sr.get("clock_domain") == ps.get("clock_domain"):
                errors.append("clock_domains_must_remain_distinct")

    boundary = trace.get("bridge_boundary")
    if not isinstance(boundary, Mapping):
        errors.append("bridge_boundary_missing")
    elif boundary.get("sr_delta_consumed_by_pond") is not False:
        errors.append("pond_delta_overclaim")

    expected_losses = declared_worldbridge_mapping_losses()
    if trace.get("declared_mapping_losses") != expected_losses:
        errors.append("mapping_losses_mismatch")

    links = trace.get("entity_links")
    if not isinstance(links, list):
        errors.append("entity_links_must_be_list")
    else:
        expected_order = sorted(
            links,
            key=lambda item: (
                str(item.get("sr_entity_id", "")) if isinstance(item, Mapping) else "",
                str(item.get("ps_organism_id", "")) if isinstance(item, Mapping) else "",
            ),
        )
        if links != expected_order:
            errors.append("entity_links_not_sorted")
        for item in links:
            if not isinstance(item, Mapping):
                errors.append("entity_link_must_be_mapping")
                continue
            if item.get("relation") != IDENTITY_RELATION:
                errors.append("entity_link_relation_mismatch")

    digest = trace.get("trace_digest")
    try:
        expected_digest = _trace_digest(dict(trace))
    except (TypeError, ValueError):
        errors.append("trace_not_json_safe")
    else:
        if digest != expected_digest:
            errors.append("trace_digest_mismatch")

    return {"valid": not errors, "errors": errors}


def build_worldbridge_dual_lane_trace_contract() -> dict[str, Any]:
    """Build a stable sample plus validation state for status/guard surfaces."""
    trace = build_worldbridge_dual_lane_trace(
        {"sim_time": 0.1, "tick": 2, "population": 1},
        {"tick": 1, "population": 1},
        entity_links=[{"sr_entity_id": "sr:sample", "ps_organism_id": "ps:sample"}],
    )
    validation = validate_worldbridge_dual_lane_trace(trace)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_dual_lane_trace_contract",
        "read_only": True,
        "contract_valid": bool(validation["valid"]),
        "trace": trace,
        "validation": validation,
        "tick_merge_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _normalize_links(entity_links: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    sr_ids: set[str] = set()
    ps_ids: set[str] = set()
    for index, raw in enumerate(entity_links):
        if not isinstance(raw, Mapping):
            raise TypeError(f"entity_links[{index}] must be a mapping")
        sr_id = _required_string(raw.get("sr_entity_id"), f"entity_links[{index}].sr_entity_id")
        ps_id = _required_string(raw.get("ps_organism_id"), f"entity_links[{index}].ps_organism_id")
        if sr_id in sr_ids:
            raise ValueError(f"duplicate sr_entity_id: {sr_id}")
        if ps_id in ps_ids:
            raise ValueError(f"duplicate ps_organism_id: {ps_id}")
        sr_ids.add(sr_id)
        ps_ids.add(ps_id)
        normalized.append(
            {
                "sr_entity_id": sr_id,
                "ps_organism_id": ps_id,
                "relation": IDENTITY_RELATION,
            }
        )
    return sorted(normalized, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]))


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{field} must be finite and non-negative")
    return result


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _optional_non_negative_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _non_negative_int(value, field)


def _json_mapping_copy(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    try:
        encoded = json.dumps(dict(value), ensure_ascii=False, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field} must contain only finite JSON values") from exc
    copied = json.loads(encoded)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must encode to an object")
    return copied


def _trace_digest(trace: Mapping[str, Any]) -> str:
    canonical = dict(trace)
    canonical.pop("trace_digest", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "build_worldbridge_dual_lane_trace",
    "build_worldbridge_dual_lane_trace_contract",
    "validate_worldbridge_dual_lane_trace",
]
