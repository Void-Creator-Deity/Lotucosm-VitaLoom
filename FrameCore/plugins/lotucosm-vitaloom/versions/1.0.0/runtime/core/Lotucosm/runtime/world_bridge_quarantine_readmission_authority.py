# -*- coding: utf-8 -*-
"""Qt-free WorldBridge quarantine and fresh-instance re-admission authority.

A labelled WorldBridge handoff failure can follow partial live mutation.  The
current runtime therefore remains quarantined for every opt-in SR-to-PS bridge
writer, not merely the ordinary tick.  This module only classifies whether a
named bridge entry point may run.  It cannot construct a Pond, mutate either
lane, clear quarantine, restart a host, or restore/replay state.
"""
from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_failure_quarantine_opt_in_handoff_readmission_authority"
OPT_IN_BRIDGE_ENTRY_POINTS = frozenset(
    {
        "scene_prebridge",
        "spawn_bridge",
        "tick_handoff",
    }
)
DO_NOT_CLAIM = (
    "same_runtime_safe_retry",
    "automatic_quarantine_clear",
    "cross_lane_rollback",
    "inverse_mutation_compensation",
    "in_place_sr_ps_restore",
    "atomic_recovery",
    "full_unified_runtime_replay",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def classify_worldbridge_opt_in_bridge_admission(
    entry_point: str,
    *,
    unified_pond_mode: bool,
    handoff_suspended: bool,
    current_pond_present: bool,
) -> dict[str, Any]:
    """Return a copy-owned decision for one adapter-owned opt-in bridge writer.

    ``handoff_suspended`` is a containment state, not an invitation to retry.
    When true, the decision denies all bridge writers before Pond construction
    or bridge mutation.  A later fresh lifecycle can create new instances, but
    this classifier cannot perform or certify that lifecycle transition.
    """
    if entry_point not in OPT_IN_BRIDGE_ENTRY_POINTS:
        raise ValueError("entry_point is not a recognised opt-in WorldBridge writer")
    for name, value in (
        ("unified_pond_mode", unified_pond_mode),
        ("handoff_suspended", handoff_suspended),
        ("current_pond_present", current_pond_present),
    ):
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be bool")

    if not unified_pond_mode:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "read_only": True,
            "entry_point": entry_point,
            "admitted": False,
            "host_action": "skip_opt_in_bridge_disabled",
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "current_runtime_quarantined": handoff_suspended,
            "requires_fresh_runtime_lifecycle_before_re_admission": False,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        }
    if handoff_suspended:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS,
            "read_only": True,
            "entry_point": entry_point,
            "admitted": False,
            "host_action": "skip_quarantined_current_runtime_opt_in_bridge_writer",
            "may_construct_or_reuse_pond": False,
            "may_call_sr_ps_bridge_mutator": False,
            "current_runtime_quarantined": True,
            "current_pond_present": current_pond_present,
            "requires_fresh_runtime_lifecycle_before_re_admission": True,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "entry_point": entry_point,
        "admitted": True,
        "host_action": "admit_opt_in_bridge_writer_for_current_unquarantined_runtime",
        "may_construct_or_reuse_pond": True,
        "may_call_sr_ps_bridge_mutator": True,
        "current_runtime_quarantined": False,
        "current_pond_present": current_pond_present,
        "requires_fresh_runtime_lifecycle_before_re_admission": False,
        "restores_failed_runtime_state": False,
        "replays_failed_handoff": False,
    }


def build_worldbridge_failure_quarantine_readmission_contract() -> dict[str, Any]:
    """Describe the complete current-runtime bridge-writer quarantine boundary."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "classify_all_known_opt_in_bridge_writers_and_fresh_instance_re_admission_boundary_only",
        "guarded_entry_points": sorted(OPT_IN_BRIDGE_ENTRY_POINTS),
        "quarantine": {
            "requires_labelled_failure_containment": True,
            "blocks_scene_prebridge": True,
            "blocks_spawn_bridge": True,
            "blocks_tick_handoff": True,
            "blocks_pond_construction_or_reuse_for_guarded_writer": True,
            "blocks_sr_ps_bridge_mutation_for_guarded_writer": True,
            "same_runtime_re_admission": False,
            "automatic_re_admission": False,
        },
        "fresh_instance_re_admission_boundary": {
            "owner": "legacy_gameviewport_normal_stop_or_scene_discard_then_normal_start_or_reload",
            "requires_discard_current_sr_runtime_instance": True,
            "requires_discard_current_ps_pond_instance": True,
            "requires_clear_current_lifetime_quarantine_after_discard": True,
            "preserves_failure_receipt_as_historical_diagnostic_only": True,
            "reuses_partially_mutated_pond": False,
            "restores_failed_runtime_state": False,
            "replays_failed_handoff": False,
        },
        "admissions": {
            "quarantine_decision_classification": True,
            "all_known_opt_in_bridge_writers_guarded": True,
            "fresh_instance_lifecycle_re_admission_boundary": True,
            "same_runtime_safe_retry": False,
            "automatic_quarantine_clear": False,
            "cross_lane_rollback": False,
            "inverse_mutation_compensation": False,
            "in_place_restore": False,
            "atomic_recovery": False,
            "replay_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "required_future_evidence": [
            "complete_versioned_sr_ps_checkpoint_restore_protocol",
            "partial_mutation_compensation_and_identity_link_repair",
            "shared_clock_input_lifecycle_rng_native_plugin_restore_coverage",
            "cross_lane_replay_and_interaction_parity_evidence",
        ],
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_failure_quarantine_readmission_contract(contract)["valid"]
    return contract


def validate_worldbridge_failure_quarantine_readmission_contract(contract: object) -> dict[str, Any]:
    """Reject retry or state-recovery claims at the quarantine boundary."""
    if not isinstance(contract, dict):
        return {"valid": False, "errors": ["contract_must_be_dict"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    if contract.get("authority_scope") != "classify_all_known_opt_in_bridge_writers_and_fresh_instance_re_admission_boundary_only":
        errors.append("authority_scope_overclaim")
    if contract.get("guarded_entry_points") != sorted(OPT_IN_BRIDGE_ENTRY_POINTS):
        errors.append("guarded_entry_points_mismatch")
    quarantine = contract.get("quarantine")
    if not isinstance(quarantine, dict):
        errors.append("quarantine_missing")
    else:
        for field in (
            "requires_labelled_failure_containment",
            "blocks_scene_prebridge",
            "blocks_spawn_bridge",
            "blocks_tick_handoff",
            "blocks_pond_construction_or_reuse_for_guarded_writer",
            "blocks_sr_ps_bridge_mutation_for_guarded_writer",
        ):
            if quarantine.get(field) is not True:
                errors.append(f"{field}_required")
        for field in ("same_runtime_re_admission", "automatic_re_admission"):
            if quarantine.get(field) is not False:
                errors.append(f"{field}_overclaim")
    fresh = contract.get("fresh_instance_re_admission_boundary")
    if not isinstance(fresh, dict):
        errors.append("fresh_instance_re_admission_boundary_missing")
    else:
        for field in (
            "requires_discard_current_sr_runtime_instance",
            "requires_discard_current_ps_pond_instance",
            "requires_clear_current_lifetime_quarantine_after_discard",
            "preserves_failure_receipt_as_historical_diagnostic_only",
        ):
            if fresh.get(field) is not True:
                errors.append(f"{field}_required")
        for field in (
            "reuses_partially_mutated_pond",
            "restores_failed_runtime_state",
            "replays_failed_handoff",
        ):
            if fresh.get(field) is not False:
                errors.append(f"{field}_overclaim")
    admissions = contract.get("admissions")
    if not isinstance(admissions, dict):
        errors.append("admissions_missing")
    else:
        for field in (
            "quarantine_decision_classification",
            "all_known_opt_in_bridge_writers_guarded",
            "fresh_instance_lifecycle_re_admission_boundary",
        ):
            if admissions.get(field) is not True:
                errors.append(f"{field}_required")
        for field in (
            "same_runtime_safe_retry",
            "automatic_quarantine_clear",
            "cross_lane_rollback",
            "inverse_mutation_compensation",
            "in_place_restore",
            "atomic_recovery",
            "replay_admitted",
            "lossless_mapping",
            "default_ready",
        ):
            if admissions.get(field) is not False:
                errors.append(f"{field}_overclaim")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "OPT_IN_BRIDGE_ENTRY_POINTS",
    "classify_worldbridge_opt_in_bridge_admission",
    "build_worldbridge_failure_quarantine_readmission_contract",
    "validate_worldbridge_failure_quarantine_readmission_contract",
]
