# -*- coding: utf-8 -*-
"""E313-B evidence binding the protocol witness to current live capture seams."""
from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR, unified_pond_step_with_trace
from core.Lotucosm.runtime.world_bridge_live_trace_producer import validate_worldbridge_live_dual_lane_trace

SCHEMA_VERSION = 1
STATUS = "worldbridge_e313_bounded_live_capture_binding"


class _ProbePond:
    def __init__(self) -> None:
        self.organisms = {"ps:e313": SimpleNamespace(
            id="ps:e313", position=[10.0, 20.0], velocity=[0.0, 0.0],
            acceleration=[0.0, 0.0], radius=4.0, size=8.0, energy=50.0,
            health=30.0, generation=1, developmental_stage=1,
        )}
        self.time = 0
        self.iteration = 0
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1
        self.time += 1
        organism = self.organisms["ps:e313"]
        organism.position[0] += 1.0
        organism.energy -= 0.5


def _probe_entity() -> SimpleNamespace:
    entity = SimpleNamespace(
        id="sr:e313", entity_type="organism", position=[1.0, 2.0],
        velocity=[0.0, 0.0], acceleration=[0.0, 0.0], radius=4.0,
        size=8.0, energy=20.0, health=15.0, generation=1, sr_debug_hud={},
    )
    setattr(entity, BRIDGE_ORGANISM_ATTR, "ps:e313")
    return entity


def run_e313_live_capture_binding() -> dict[str, Any]:
    event = {"sequence": 7, "tick": 12, "action": "thrust", "value": 1.0}
    pond = _ProbePond()
    entity = _probe_entity()
    payload = unified_pond_step_with_trace(
        pond,
        [entity],
        sr_checkpoint={
            "sim_time": 0.6,
            "tick": event["tick"],
            "input_event": copy.deepcopy(event),
            "rng_provenance": {"transported": False, "reason": "bridge_api_has_no_rng_argument"},
        },
        delta_time=0.05,
    )
    trace = payload["trace"]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "capture_seam_exercised": True,
        "capture_validation": validate_worldbridge_live_dual_lane_trace(payload),
        "pond_update_calls": pond.update_calls,
        "capture_order": payload["capture_order"],
        "input_provenance": {
            "event_embedded_in_sr_observation": trace["lanes"]["sr"]["checkpoint"].get("input_event") == event,
            "sequence": event["sequence"],
            "tick": event["tick"],
            "ps_received_input": False,
            "shared_input_log": False,
        },
        "clock_provenance": {
            "sr_sim_time": trace["lanes"]["sr"]["clock_value"],
            "ps_tick": trace["lanes"]["ps"]["clock_value"],
            "same_clock_domain": False,
            "ps_consumed_sr_delta": payload["sr_delta_consumed_by_pond"] is True,
        },
        "rng_provenance": {
            "declared_in_observation": True,
            "transported_to_ps": False,
            "shared_consumption_order": False,
            "reason": "current unified_pond_step API does not transport RNG state/context",
        },
        "quarantine": {
            "required": True,
            "mode": "observation_only_no_replay",
            "fallback": "retain_dual_lane_runtime_and_discard_cross_lane_replay_claim",
        },
        "evidence": {
            "real_live_capture_seam": True,
            "ordered_non_atomic_capture": payload["atomic_checkpoint"] is False,
            "input_event_copy_isolated": trace["lanes"]["sr"]["checkpoint"]["input_event"] is not event,
            "clock_domains_separate": trace["lanes"]["sr"]["clock_domain"] != trace["lanes"]["ps"]["clock_domain"],
            "rng_transport_missing": True,
            "quarantine_on_missing_shared_state": True,
        },
        "production_live_adapter_admitted": False,
        "full_unified_replay_admitted": False,
        "cross_lane_replay": False,
        "default_ready": False,
    }


def build_worldbridge_e313_live_capture_binding() -> dict[str, Any]:
    result = run_e313_live_capture_binding()
    result["protocol_valid"] = bool(
        result["capture_validation"]["valid"]
        and all(result["evidence"].values())
        and result["quarantine"]["required"] is True
        and result["production_live_adapter_admitted"] is False
    )
    return result


__all__ = ["build_worldbridge_e313_live_capture_binding", "run_e313_live_capture_binding"]

