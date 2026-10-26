# -*- coding: utf-8 -*-
"""Qt-free evidence for WorldBridge checkpoint/restore feasibility.

The existing project has useful, lane-local persistence and observation APIs.
They do not compose into one live SR/PS checkpoint: SR snapshots are read-only
projections, PS Pond persistence reconstructs a fresh Pond, and bridge links,
input, RNG, lifecycle, plugin/native state, and rollback order have no common
versioned restore contract.  This module records that decision without
mutating runtime state or inventing replay authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_cross_lane_checkpoint_restore_feasibility"
DO_NOT_CLAIM = (
    "cross_lane_checkpoint_available",
    "cross_lane_restore_available",
    "atomic_sr_ps_checkpoint",
    "rollback_performed",
    "full_unified_runtime_replay",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def build_worldbridge_checkpoint_restore_feasibility_contract() -> dict[str, Any]:
    """Describe the strongest currently source-backed checkpoint decision."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "static_cross_lane_checkpoint_restore_feasibility_inventory_only",
        "decision": {
            "cross_lane_checkpoint_available": False,
            "cross_lane_restore_available": False,
            "replay_preconditions_satisfied": False,
            "reason": "no_versioned_complete_sr_ps_state_bundle_or_restore_order_exists",
        },
        "existing_lane_local_seams": {
            "sr_runtime_snapshot_authority": {
                "available": True,
                "kind": "epoch_scoped_copy_isolated_read_only_json_projection",
                "live_entity_restore": False,
                "scene_runtime_restore": False,
                "random_state_restore": False,
                "input_lifecycle_restore": False,
            },
            "worldbridge_live_trace_and_capture_artifact": {
                "available": True,
                "kind": "read_only_observation_and_evidence_artifact",
                "restore_input": False,
                "restore_live_sr_or_ps_objects": False,
                "atomic_checkpoint": False,
            },
            "ps_pond_serializer": {
                "available": True,
                "kind": "portable_ps_pond_reconstruction_to_new_instance",
                "serializes_pond_time": True,
                "restores_root_entity_registration": True,
                "restores_bridge_link_metadata": False,
                "in_place_live_pond_restore": False,
                "cross_lane_restore": False,
            },
        },
        "cross_lane_state_gaps": {
            "sr_runtime_entity_graph_and_script_state": False,
            "bridge_entity_to_organism_links": False,
            "pond_time_and_system_internal_state": False,
            "shared_input_queue_and_lifecycle_epoch": False,
            "sr_rng_state": False,
            "ps_rng_state": False,
            "cross_lane_rng_draw_order": False,
            "plugin_dynamic_script_native_extension_state": False,
            "restore_order_and_partial_failure_compensation": False,
            "same_instant_atomic_capture": False,
        },
        "replay_preconditions_missing": [
            "versioned_complete_sr_runtime_state",
            "versioned_complete_ps_pond_and_system_state",
            "bridge_link_and_identity_restoration",
            "shared_input_pause_reset_error_lifecycle_log",
            "sr_and_ps_rng_state_and_ordered_draw_protocol",
            "cross_lane_clock_delta_and_scheduler_contract",
            "restore_order_partial_failure_compensation_and_parity_evidence",
        ],
        "admissions": {
            "checkpoint_restore": False,
            "atomicity": False,
            "rollback": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_checkpoint_restore_feasibility_contract(contract)["valid"]
    return contract


def validate_worldbridge_checkpoint_restore_feasibility_contract(contract: object) -> dict[str, Any]:
    """Reject claims that confuse observation or PS persistence with restore."""
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    if contract.get("authority_scope") != "static_cross_lane_checkpoint_restore_feasibility_inventory_only":
        errors.append("authority_scope_overclaim")
    decision = contract.get("decision")
    if not isinstance(decision, Mapping):
        errors.append("decision_missing")
    else:
        for field in ("cross_lane_checkpoint_available", "cross_lane_restore_available", "replay_preconditions_satisfied"):
            if decision.get(field) is not False:
                errors.append(f"{field}_overclaim")
    seams = contract.get("existing_lane_local_seams")
    if not isinstance(seams, Mapping):
        errors.append("lane_local_seams_missing")
    else:
        sr = seams.get("sr_runtime_snapshot_authority")
        trace = seams.get("worldbridge_live_trace_and_capture_artifact")
        ps = seams.get("ps_pond_serializer")
        if not isinstance(sr, Mapping) or sr.get("available") is not True or sr.get("live_entity_restore") is not False:
            errors.append("sr_snapshot_boundary_mismatch")
        if not isinstance(trace, Mapping) or trace.get("available") is not True or trace.get("restore_live_sr_or_ps_objects") is not False:
            errors.append("trace_observation_boundary_mismatch")
        if not isinstance(ps, Mapping) or ps.get("available") is not True:
            errors.append("ps_persistence_missing")
        elif any(ps.get(field) is not False for field in ("restores_bridge_link_metadata", "in_place_live_pond_restore", "cross_lane_restore")):
            errors.append("ps_persistence_overclaim")
    gaps = contract.get("cross_lane_state_gaps")
    if not isinstance(gaps, Mapping) or not gaps or any(value is not False for value in gaps.values()):
        errors.append("cross_lane_state_gaps_mismatch")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for field in ("checkpoint_restore", "atomicity", "rollback", "replay_admitted", "lossless_mapping", "default_ready"):
            if admissions.get(field) is not False:
                errors.append(f"{field}_overclaim")
    if not isinstance(contract.get("replay_preconditions_missing"), list) or len(contract["replay_preconditions_missing"]) < 5:
        errors.append("replay_preconditions_incomplete")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "build_worldbridge_checkpoint_restore_feasibility_contract",
    "validate_worldbridge_checkpoint_restore_feasibility_contract",
]
