# -*- coding: utf-8 -*-
"""Read-only inventory of the current WorldBridge SR-input and lifecycle boundary.

This module describes source-backed dual-lane facts only.  It does not create a
shared queue, route input into Pond, schedule either lane, or mutate live state.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_input_pause_authority"
LIFECYCLE_ACTIONS = frozenset({"start", "pause", "resume", "stop", "discard_reload"})
DO_NOT_CLAIM = (
    "shared_queued_input_ordering",
    "cross_lane_input_ordering",
    "input_replay_admitted",
    "checkpoint_input_state",
    "shared_pause_reset_authority",
    "cross_lane_atomicity",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def _require_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")
    return value


def observe_worldbridge_sr_input_lifecycle(
    *,
    playing: bool,
    paused: bool,
    bridge_handoff_invoked: bool,
    lifecycle_action: str | None = None,
) -> dict[str, Any]:
    """Describe one caller-reported SR-local input opportunity without scheduling.

    ``lifecycle_action`` represents the host paths that discard the mutable SR
    buffer.  It is an observation vocabulary, not a new lifecycle coordinator.
    A bridge handoff may advance Pond only after a non-paused SR tick, but Pond
    receives no input argument or shared event record.
    """
    active = _require_bool(playing, "playing")
    is_paused = _require_bool(paused, "paused")
    requested_handoff = _require_bool(bridge_handoff_invoked, "bridge_handoff_invoked")
    if lifecycle_action is not None and lifecycle_action not in LIFECYCLE_ACTIONS:
        raise ValueError("lifecycle_action must be one of start, pause, resume, stop, discard_reload")

    lifecycle_discards_buffer = lifecycle_action is not None
    sr_snapshot_admitted = active and not is_paused and not lifecycle_discards_buffer
    bridge_handoff_admitted = sr_snapshot_admitted and requested_handoff
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "playing": active,
        "paused": is_paused,
        "lifecycle_action": lifecycle_action,
        "sr_snapshot_admitted": sr_snapshot_admitted,
        "sr_script_input_received": sr_snapshot_admitted,
        "sr_input_buffer_discarded": lifecycle_discards_buffer,
        "bridge_handoff_admitted": bridge_handoff_admitted,
        "ps_tick_may_advance": bridge_handoff_admitted,
        "ps_received_input": False,
        "shared_queue": False,
        "shared_event_log": False,
        "cross_lane_input_ordering": False,
        "input_replay_admitted": False,
        "checkpoint_input_state": False,
        "shared_pause_reset_authority": False,
        "atomicity_admitted": False,
        "default_ready": False,
    }


def build_worldbridge_input_pause_authority_contract() -> dict[str, Any]:
    """Return Qt-free static evidence for lane-local input and lifecycle behavior."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "static_source_inventory_and_bounded_sr_local_input_lifecycle_observation_only",
        "sr_input": {
            "owner": "viewport_private_sr_input_buffer",
            "ingestion": ["keyboard_press_release", "mouse_move_press_release"],
            "snapshot_boundary": "prepare_tick_before_sr_script_phase",
            "snapshot_semantics": {
                "keys_down": "immutable_frozenset_copy",
                "mouse_left_clicked": "one_tick_edge_cleared_after_snapshot",
                "paused_or_not_playing": "empty_snapshot",
            },
            "script_phase_precedes_opt_in_bridge_handoff": True,
        },
        "ps_input": {
            "pond_update_input_argument": False,
            "shared_queue": False,
            "shared_event_log": False,
            "ps_received_sr_input": False,
        },
        "lifecycle": {
            "start_clears_sr_input": True,
            "pause_clears_sr_input": True,
            "resume_clears_sr_input": True,
            "stop_clears_sr_input": True,
            "discard_reload_clears_sr_input": True,
            "bridge_exception_isolated": True,
            "shared_pause_reset_authority": False,
        },
        "scenario_observations": {
            "not_playing": observe_worldbridge_sr_input_lifecycle(
                playing=False, paused=False, bridge_handoff_invoked=True
            ),
            "paused": observe_worldbridge_sr_input_lifecycle(
                playing=True, paused=True, bridge_handoff_invoked=True
            ),
            "playing_sr_only": observe_worldbridge_sr_input_lifecycle(
                playing=True, paused=False, bridge_handoff_invoked=False
            ),
            "playing_opt_in_bridge": observe_worldbridge_sr_input_lifecycle(
                playing=True, paused=False, bridge_handoff_invoked=True
            ),
            "resume_discards_buffer": observe_worldbridge_sr_input_lifecycle(
                playing=True, paused=True, bridge_handoff_invoked=True, lifecycle_action="resume"
            ),
        },
        "admissions": {
            "shared_queued_input_ordering": False,
            "cross_lane_input_ordering": False,
            "input_replay_admitted": False,
            "checkpoint_input_state": False,
            "shared_pause_reset_authority": False,
            "atomicity_admitted": False,
            "lossless_mapping": False,
            "default_ready": False,
        },
        "remaining_unblock_requirements": [
            "scheduler_owner_and_canonical_input_event_schema",
            "monotonic_sequence_and_lane_phase_routing",
            "admission_backpressure_and_dropped_event_policy",
            "pause_resume_stop_reset_epoch_and_error_policy",
            "deterministic_serialized_input_log",
            "shared_rng_checkpoint_restore_and_replay_parity",
        ],
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    validation = validate_worldbridge_input_pause_authority_contract(contract)
    contract["contract_valid"] = validation["valid"]
    return contract


def validate_worldbridge_input_pause_authority_contract(contract: object) -> dict[str, Any]:
    """Reject input, replay, lifecycle, or readiness claims unsupported by source."""
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
    if contract.get("authority_scope") != "static_source_inventory_and_bounded_sr_local_input_lifecycle_observation_only":
        errors.append("authority_scope_overclaim")

    sr_input = contract.get("sr_input")
    if not isinstance(sr_input, Mapping):
        errors.append("sr_input_missing")
    else:
        snapshot = sr_input.get("snapshot_semantics")
        if not isinstance(snapshot, Mapping) or snapshot.get("keys_down") != "immutable_frozenset_copy":
            errors.append("sr_snapshot_semantics_mismatch")
        if not isinstance(snapshot, Mapping) or snapshot.get("mouse_left_clicked") != "one_tick_edge_cleared_after_snapshot":
            errors.append("sr_click_edge_semantics_mismatch")
        if sr_input.get("script_phase_precedes_opt_in_bridge_handoff") is not True:
            errors.append("sr_script_before_bridge_required")

    ps_input = contract.get("ps_input")
    if not isinstance(ps_input, Mapping):
        errors.append("ps_input_missing")
    else:
        for field, error in (
            ("pond_update_input_argument", "pond_update_input_argument_overclaim"),
            ("shared_queue", "shared_queue_overclaim"),
            ("shared_event_log", "shared_event_log_overclaim"),
            ("ps_received_sr_input", "ps_input_routing_overclaim"),
        ):
            if ps_input.get(field) is not False:
                errors.append(error)

    lifecycle = contract.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        errors.append("lifecycle_missing")
    else:
        for field in (
            "start_clears_sr_input",
            "pause_clears_sr_input",
            "resume_clears_sr_input",
            "stop_clears_sr_input",
            "discard_reload_clears_sr_input",
            "bridge_exception_isolated",
        ):
            if lifecycle.get(field) is not True:
                errors.append(f"{field}_required")
        if lifecycle.get("shared_pause_reset_authority") is not False:
            errors.append("shared_pause_reset_authority_overclaim")

    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for field, error in (
            ("shared_queued_input_ordering", "shared_queued_input_ordering_overclaim"),
            ("cross_lane_input_ordering", "cross_lane_input_ordering_overclaim"),
            ("input_replay_admitted", "input_replay_overclaim"),
            ("checkpoint_input_state", "checkpoint_input_state_overclaim"),
            ("shared_pause_reset_authority", "shared_pause_reset_overclaim"),
            ("atomicity_admitted", "atomicity_overclaim"),
            ("lossless_mapping", "lossless_mapping_overclaim"),
            ("default_ready", "default_ready_overclaim"),
        ):
            if admissions.get(field) is not False:
                errors.append(error)

    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}
