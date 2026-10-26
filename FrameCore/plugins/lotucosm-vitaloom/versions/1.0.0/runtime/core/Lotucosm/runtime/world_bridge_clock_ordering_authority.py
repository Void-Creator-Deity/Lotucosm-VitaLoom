# -*- coding: utf-8 -*-
"""Read-only authority inventory for WorldBridge clocks and one serial handoff.

This module deliberately describes the current dual-lane topology.  It does
not turn SR scene seconds and PS Pond ticks into a common clock, and it does
not schedule either lane.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_clock_ordering_authority"
FRAME_CLOCK_DECISION_STATUS = "worldbridge_frame_clock_decision"
SR_CLOCK_DOMAIN = "sr_scaled_scene_seconds"
PS_CLOCK_DOMAIN = "ps_pond_unit_ticks"
SR_BASE_DELTA_SECONDS = 0.05
SR_MIN_SPEED = 0.2
SERIAL_HANDOFF_ORDER = (
    "complete_sr_tick_phases",
    "refresh_sr_hud",
    "sync_sr_to_ps",
    "pond_update_one_unit_tick",
    "sync_ps_to_sr_display",
    "publish_sr_runtime_snapshots",
)
DO_NOT_CLAIM = (
    "shared_sr_ps_clock",
    "sr_seconds_to_ps_ticks_conversion",
    "sr_ps_tick_merge",
    "cross_call_or_cross_thread_ordering",
    "atomic_sr_ps_checkpoint",
    "shared_queued_input_ordering",
    "full_unified_runtime_replay",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
)


def observe_worldbridge_clock_ordering(
    simulation_speed: float,
    *,
    paused: bool,
    bridge_handoff_invoked: bool,
) -> dict[str, Any]:
    """Describe one caller-reported SR tick opportunity without scheduling it.

    The result is a bounded observation, not a time conversion: when a
    handoff is invoked, PS advances one Pond unit regardless of the SR delta.
    A paused viewport admits neither an SR scene advance nor a bridge update.
    """
    if isinstance(simulation_speed, bool) or not isinstance(simulation_speed, (int, float)):
        raise TypeError("simulation_speed must be a finite number")
    speed = float(simulation_speed)
    if not math.isfinite(speed):
        raise ValueError("simulation_speed must be finite")
    if not isinstance(paused, bool):
        raise TypeError("paused must be bool")
    if not isinstance(bridge_handoff_invoked, bool):
        raise TypeError("bridge_handoff_invoked must be bool")

    sr_delta = 0.0 if paused else SR_BASE_DELTA_SECONDS * max(SR_MIN_SPEED, speed)
    ps_ticks = 1 if not paused and bridge_handoff_invoked else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "sr_clock_domain": SR_CLOCK_DOMAIN,
        "ps_clock_domain": PS_CLOCK_DOMAIN,
        "paused": paused,
        "sr_delta_seconds": sr_delta,
        "ps_ticks_advanced": ps_ticks,
        "ps_simulation_time_delta_seconds": sr_delta if ps_ticks else 0.0,
        "ps_update_policy": "one_update_per_sr_delta",
        "serial_handoff_observed": bool(ps_ticks),
        "serial_handoff_order": list(SERIAL_HANDOFF_ORDER) if ps_ticks else [],
        "shared_clock": False,
        "time_conversion_admitted": False,
        "atomicity_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
    }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decision_digest(decision: Mapping[str, Any]) -> str:
    payload = dict(decision)
    payload["decision_digest"] = ""
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _clean_decision_token(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    if len(value) > 160 or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-" for ch in value):
        raise ValueError(f"{field} must be a clean identifier")
    if not value[0].isalnum():
        raise ValueError(f"{field} must start with an alphanumeric character")
    return value


def issue_worldbridge_frame_clock_decision(
    simulation_speed: float,
    *,
    paused: bool,
    owner_token: str,
    runtime_epoch: str,
    decision_sequence: int,
    bridge_handoff_requested: bool,
) -> dict[str, Any]:
    if not isinstance(paused, bool):
        raise TypeError("paused must be bool")
    if not isinstance(bridge_handoff_requested, bool):
        raise TypeError("bridge_handoff_requested must be bool")
    if isinstance(decision_sequence, bool) or not isinstance(decision_sequence, int):
        raise TypeError("decision_sequence must be an integer")
    if decision_sequence < 1:
        raise ValueError("decision_sequence must be at least 1")
    if paused and bridge_handoff_requested:
        raise ValueError("paused frame cannot request a bridge handoff")
    delta = resolve_worldbridge_frame_delta(simulation_speed, paused=paused)
    decision = {
        "schema_version": SCHEMA_VERSION,
        "status": FRAME_CLOCK_DECISION_STATUS,
        "owner_token": _clean_decision_token(owner_token, "owner_token"),
        "runtime_epoch": _clean_decision_token(runtime_epoch, "runtime_epoch"),
        "decision_sequence": decision_sequence,
        "simulation_speed": float(simulation_speed),
        "paused": paused,
        "sr_delta_seconds": delta,
        "bridge_handoff_requested": bridge_handoff_requested,
        "time_conversion_admitted": False,
        "decision_digest": "",
    }
    decision["decision_digest"] = _decision_digest(decision)
    return copy.deepcopy(decision)


def validate_worldbridge_frame_clock_decision(decision: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(decision, Mapping):
        return {"valid": False, "errors": ["decision_not_mapping"]}
    expected_keys = {
        "schema_version", "status", "owner_token", "runtime_epoch",
        "decision_sequence", "simulation_speed", "paused",
        "sr_delta_seconds", "bridge_handoff_requested",
        "time_conversion_admitted", "decision_digest",
    }
    if set(decision) != expected_keys:
        errors.append("decision_keys_mismatch")
    if decision.get("schema_version") != SCHEMA_VERSION:
        errors.append("decision_version_mismatch")
    if decision.get("status") != FRAME_CLOCK_DECISION_STATUS:
        errors.append("decision_status_mismatch")
    try:
        _clean_decision_token(decision.get("owner_token"), "owner_token")
    except ValueError:
        errors.append("decision_owner_token_invalid")
    try:
        _clean_decision_token(decision.get("runtime_epoch"), "runtime_epoch")
    except ValueError:
        errors.append("decision_runtime_epoch_invalid")
    sequence = decision.get("decision_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        errors.append("decision_sequence_invalid")
    speed = decision.get("simulation_speed")
    if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not math.isfinite(float(speed)):
        errors.append("decision_simulation_speed_invalid")
    paused = decision.get("paused")
    if not isinstance(paused, bool):
        errors.append("decision_paused_invalid")
    requested = decision.get("bridge_handoff_requested")
    if not isinstance(requested, bool):
        errors.append("decision_bridge_handoff_requested_invalid")
    elif paused is True and requested:
        errors.append("decision_paused_handoff_inconsistent")
    delta = decision.get("sr_delta_seconds")
    if isinstance(delta, bool) or not isinstance(delta, (int, float)) or not math.isfinite(float(delta)) or float(delta) < 0.0:
        errors.append("decision_delta_invalid")
    if (
        isinstance(speed, (int, float)) and not isinstance(speed, bool)
        and isinstance(paused, bool)
        and isinstance(delta, (int, float)) and not isinstance(delta, bool)
    ):
        try:
            expected_delta = resolve_worldbridge_frame_delta(float(speed), paused=paused)
        except (TypeError, ValueError):
            pass
        else:
            if float(delta) != expected_delta:
                errors.append("decision_delta_mismatch")
    if decision.get("time_conversion_admitted") is not False:
        errors.append("decision_time_conversion_overclaim")
    digest = decision.get("decision_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("decision_digest_invalid")
    else:
        try:
            expected_digest = _decision_digest(decision)
        except (TypeError, ValueError, OverflowError):
            errors.append("decision_not_canonical_json")
        else:
            if digest != expected_digest:
                errors.append("decision_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def resolve_worldbridge_frame_delta(simulation_speed: float, *, paused: bool) -> float:
    """Resolve one frame delta without accumulating paused or dropped time."""
    if isinstance(paused, bool) is not True:
        raise TypeError("paused must be bool")
    if isinstance(simulation_speed, bool) or not isinstance(simulation_speed, (int, float)):
        raise TypeError("simulation_speed must be a finite number")
    speed = float(simulation_speed)
    if not math.isfinite(speed):
        raise ValueError("simulation_speed must be finite")
    if paused:
        return 0.0
    return SR_BASE_DELTA_SECONDS * max(SR_MIN_SPEED, speed)


def build_worldbridge_clock_ordering_authority_contract() -> dict[str, Any]:
    """Return static, Qt-free evidence for the actual dual-lane clock boundary."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "runtime_mode": "dual",
        "authority_scope": "static_source_inventory_and_single_opt_in_handoff_order_only",
        "sr_lane": {
            "clock_domain": SR_CLOCK_DOMAIN,
            "entrypoint": "GameViewport._update_simulation",
            "delta_expression": "0.05 * max(0.2, simulation_speed)",
            "scene_time_owner": "GameViewport._scene_runtime_time",
            "tick_driver": "SimulationDriver.tick",
            "pause_policy": "is_paused_returns_before_scene_tick_and_bridge_handoff",
            "phase_order": ["script", "spawn", "actuator", "fluid", "physics", "survival", "snapshot"],
        },
        "ps_lane": {
            "clock_domain": PS_CLOCK_DOMAIN,
            "entrypoint": "Pond.update",
            "clock_increment": 1,
            "root_entity_update_delta": "shared_delta_time",
            "bridge_delta_consumed": True,
            "pause_owner": "no_independent_bridge_pause_authority",
        },
        "serial_handoff": {
            "admitted": True,
            "scope": "one_opt_in_gameviewport_snapshot_phase_call_only",
            "order": list(SERIAL_HANDOFF_ORDER),
            "cross_call_ordering_admitted": False,
            "cross_thread_ordering_admitted": False,
            "atomicity_admitted": False,
        },
        "clock_relation": {
            "shared_clock": False,
            "time_conversion_admitted": False,
            "sr_seconds_per_ps_tick": None,
            "ps_ticks_per_sr_second": None,
            "reason": "baseline_inventory_requires_sealed_variable_delta_witness",
        },
        "scenario_observations": {
            "paused": observe_worldbridge_clock_ordering(1.0, paused=True, bridge_handoff_invoked=True),
            "slow_speed_handoff": observe_worldbridge_clock_ordering(0.01, paused=False, bridge_handoff_invoked=True),
            "fast_speed_handoff": observe_worldbridge_clock_ordering(3.0, paused=False, bridge_handoff_invoked=True),
            "missed_handoff": observe_worldbridge_clock_ordering(1.0, paused=False, bridge_handoff_invoked=False),
        },
        "replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "remaining_unblock_requirements": [
            "scheduler_owner_and_fixed_or_variable_step_policy",
            "pause_reset_error_and_accumulated_delta_policy",
            "explicit_sr_seconds_to_ps_ticks_rounding_policy",
            "dropped_frame_and_backpressure_policy",
            "shared_queued_input_ordering",
            "shared_random_seed_contract",
            "atomic_shared_checkpoint_and_replay_contract",
        ],
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    validation = validate_worldbridge_clock_ordering_authority_contract(contract)
    contract["contract_valid"] = validation["valid"]
    return contract


def validate_worldbridge_clock_ordering_authority_contract(contract: object) -> dict[str, Any]:
    """Reject claims beyond the narrow, existing source-backed authority."""
    errors: list[str] = []
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")
    if contract.get("authority_scope") != "static_source_inventory_and_single_opt_in_handoff_order_only":
        errors.append("authority_scope_overclaim")

    sr = contract.get("sr_lane")
    if not isinstance(sr, Mapping) or sr.get("clock_domain") != SR_CLOCK_DOMAIN:
        errors.append("sr_clock_domain_mismatch")
    elif sr.get("delta_expression") != "0.05 * max(0.2, simulation_speed)":
        errors.append("sr_delta_expression_mismatch")

    ps = contract.get("ps_lane")
    if not isinstance(ps, Mapping) or ps.get("clock_domain") != PS_CLOCK_DOMAIN:
        errors.append("ps_clock_domain_mismatch")
    elif (
        ps.get("clock_increment") != 1
        or ps.get("root_entity_update_delta") != "shared_delta_time"
    ):
        errors.append("ps_fixed_step_mismatch")
    elif ps.get("bridge_delta_consumed") is not True:
        errors.append("bridge_delta_consumption_missing")

    handoff = contract.get("serial_handoff")
    if not isinstance(handoff, Mapping) or handoff.get("admitted") is not True:
        errors.append("serial_handoff_missing")
    else:
        if handoff.get("order") != list(SERIAL_HANDOFF_ORDER):
            errors.append("serial_handoff_order_mismatch")
        for field, error in (
            ("cross_call_ordering_admitted", "cross_call_ordering_overclaim"),
            ("cross_thread_ordering_admitted", "cross_thread_ordering_overclaim"),
            ("atomicity_admitted", "atomicity_overclaim"),
        ):
            if handoff.get(field) is not False:
                errors.append(error)

    relation = contract.get("clock_relation")
    if not isinstance(relation, Mapping):
        errors.append("clock_relation_missing")
    else:
        if relation.get("shared_clock") is not False:
            errors.append("shared_clock_overclaim")
        if relation.get("time_conversion_admitted") is not False:
            errors.append("time_conversion_overclaim")
        if relation.get("sr_seconds_per_ps_tick") is not None or relation.get("ps_ticks_per_sr_second") is not None:
            errors.append("time_conversion_value_overclaim")

    scenarios = contract.get("scenario_observations")
    if not isinstance(scenarios, Mapping):
        errors.append("scenario_observations_missing")
    else:
        paused = scenarios.get("paused")
        slow = scenarios.get("slow_speed_handoff")
        fast = scenarios.get("fast_speed_handoff")
        missed = scenarios.get("missed_handoff")
        if not isinstance(paused, Mapping) or paused.get("sr_delta_seconds") != 0.0 or paused.get("ps_ticks_advanced") != 0:
            errors.append("paused_non_advance_mismatch")
        if not isinstance(slow, Mapping) or not math.isclose(float(slow.get("sr_delta_seconds", -1.0)), 0.01, rel_tol=0.0, abs_tol=1e-12) or slow.get("ps_ticks_advanced") != 1:
            errors.append("slow_speed_observation_mismatch")
        if not isinstance(fast, Mapping) or not math.isclose(float(fast.get("sr_delta_seconds", -1.0)), 0.15, rel_tol=0.0, abs_tol=1e-12) or fast.get("ps_ticks_advanced") != 1:
            errors.append("fast_speed_observation_mismatch")
        if not isinstance(missed, Mapping) or missed.get("sr_delta_seconds") != 0.05 or missed.get("ps_ticks_advanced") != 0:
            errors.append("missed_handoff_observation_mismatch")

    for field, error in (
        ("replay_admitted", "replay_overclaim"),
        ("lossless", "lossless_overclaim"),
        ("default_ready", "default_ready_overclaim"),
    ):
        if contract.get(field) is not False:
            errors.append(error)
    if contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "FRAME_CLOCK_DECISION_STATUS",
    "PS_CLOCK_DOMAIN",
    "SERIAL_HANDOFF_ORDER",
    "SR_CLOCK_DOMAIN",
    "build_worldbridge_clock_ordering_authority_contract",
    "issue_worldbridge_frame_clock_decision",
    "observe_worldbridge_clock_ordering",
    "resolve_worldbridge_frame_delta",
    "validate_worldbridge_clock_ordering_authority_contract",
    "validate_worldbridge_frame_clock_decision",
]


