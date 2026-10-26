# -*- coding: utf-8 -*-
"""Bounded SR/PS replay protocol evidence for E313.

This is an isolated, Qt-free protocol harness.  It proves that a versioned
input log, explicit tick order, caller-owned RNG snapshots, and a controlled
restart can reproduce the *same synthetic lane model*.  It intentionally does
not restore live SR entities or a production Pond and therefore cannot admit a
WorldBridge live adapter.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
    validate_worldbridge_deterministic_randomness_snapshot,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e313_bounded_cross_lane_replay_corpus"
PHASE_ORDER = (
    "input_ingest",
    "sr_tick",
    "sr_to_ps_sync",
    "ps_tick",
    "trace_capture",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Mapping[str, Any], field: str) -> str:
    payload = dict(value)
    payload[field] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _input_log() -> list[dict[str, Any]]:
    return [
        {"sequence": 0, "tick": 0, "action": "thrust", "value": 1.0},
        {"sequence": 1, "tick": 1, "action": "turn", "value": -0.25},
        {"sequence": 2, "tick": 2, "action": "thrust", "value": 0.5},
        {"sequence": 3, "tick": 3, "action": "turn", "value": 0.75},
        {"sequence": 4, "tick": 4, "action": "thrust", "value": -0.5},
        {"sequence": 5, "tick": 5, "action": "turn", "value": 0.125},
    ]


def _new_run() -> dict[str, Any]:
    context = create_worldbridge_deterministic_randomness_context("e313-harness", "e313-fixed-root")
    register_worldbridge_deterministic_random_stream(context, "sr.logic", "python_random")
    register_worldbridge_deterministic_random_stream(context, "ps.resource", "numpy_pcg64_generator")
    return {
        "context": context,
        "tick": 0,
        "input_cursor": 0,
        "sr_position": 0.0,
        "ps_energy": 10.0,
        "trace": [],
    }


def _apply_tick(run: dict[str, Any], event: Mapping[str, Any]) -> None:
    if event.get("tick") != run["tick"]:
        raise ValueError("input tick does not match replay cursor")
    if event.get("sequence") != run["input_cursor"]:
        raise ValueError("input sequence is not monotonic")
    action = event.get("action")
    value = float(event.get("value"))
    sr_rng = run["context"].get_stream("sr.logic")
    ps_rng = run["context"].get_stream("ps.resource")
    # The phase order is deliberately explicit and fixed for this harness.
    impulse = value if action == "thrust" else value * 0.5
    sr_delta = impulse + (sr_rng.random() - 0.5) * 0.01
    run["sr_position"] += sr_delta
    ps_delta = float(ps_rng.random()) * 0.1
    run["ps_energy"] += sr_delta * 0.2 + ps_delta
    run["trace"].append(
        {
            "tick": run["tick"],
            "input_sequence": event["sequence"],
            "sr_position": round(run["sr_position"], 12),
            "ps_energy": round(run["ps_energy"], 12),
        }
    )
    run["tick"] += 1
    run["input_cursor"] += 1


def _snapshot(run: Mapping[str, Any]) -> dict[str, Any]:
    context = run["context"]
    random_snapshot = context.snapshot()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "phase_order": list(PHASE_ORDER),
        "tick": int(run["tick"]),
        "input_cursor": int(run["input_cursor"]),
        "sr_position": float(run["sr_position"]),
        "ps_energy": float(run["ps_energy"]),
        "randomness_snapshot": random_snapshot,
    }
    payload["checkpoint_digest"] = _digest(payload, "checkpoint_digest")
    return payload


def _restore(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    if checkpoint.get("phase_order") != list(PHASE_ORDER):
        raise ValueError("checkpoint phase order mismatch")
    if validate_e313_checkpoint(checkpoint)["valid"] is not True:
        raise ValueError("invalid E313 checkpoint")
    run = _new_run()
    run["tick"] = int(checkpoint["tick"])
    run["input_cursor"] = int(checkpoint["input_cursor"])
    run["sr_position"] = float(checkpoint["sr_position"])
    run["ps_energy"] = float(checkpoint["ps_energy"])
    snapshot = checkpoint["randomness_snapshot"]
    for stream in snapshot["streams"]:
        target = run["context"].get_stream(stream["stream_name"])
        state = stream["state"]
        if stream["family"] == "python_random":
            target.setstate((state["version"], tuple(state["internal_state"]), state["gaussian_cache"]))  # type: ignore[union-attr]
        else:
            target.bit_generator.state = {  # type: ignore[union-attr]
                "bit_generator": "PCG64",
                "state": {"state": state["state"]["state"], "inc": state["state"]["inc"]},
                "has_uint32": state["has_uint32"],
                "uinteger": state["uinteger"],
            }
    return run


def _finish(run: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "tick": run["tick"],
        "input_cursor": run["input_cursor"],
        "sr_position": round(float(run["sr_position"]), 12),
        "ps_energy": round(float(run["ps_energy"]), 12),
        "trace": copy.deepcopy(run["trace"]),
    }


def run_e313_bounded_replay_protocol() -> dict[str, Any]:
    """Execute baseline/checkpoint/restart and compare the post-checkpoint suffix."""
    events = _input_log()
    baseline = _new_run()
    for event in events[:3]:
        _apply_tick(baseline, event)
    checkpoint = _snapshot(baseline)
    for event in events[3:]:
        _apply_tick(baseline, event)
    baseline_final = _finish(baseline)

    restarted = _restore(checkpoint)
    for event in events[3:]:
        _apply_tick(restarted, event)
    restarted_final = _finish(restarted)
    suffix_baseline = baseline_final["trace"][3:]
    suffix_restarted = restarted_final["trace"]
    scalar_state_equal = all(
        baseline_final[field] == restarted_final[field]
        for field in ("tick", "input_cursor", "sr_position", "ps_energy")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "harness_only": True,
        "input_log": events,
        "phase_order": list(PHASE_ORDER),
        "checkpoint": checkpoint,
        "controlled_restart": {
            "fresh_lane_instances": True,
            "restored_from_checkpoint": True,
            "post_checkpoint_trace_equal": suffix_baseline == suffix_restarted,
            "final_state_equal": scalar_state_equal and suffix_baseline == suffix_restarted,
        },
        "baseline_final": baseline_final,
        "restarted_final": restarted_final,
        "evidence": {
            "input_sequence_monotonic": [event["sequence"] for event in events] == list(range(len(events))),
            "input_cursor_restored": restarted["input_cursor"] == checkpoint["input_cursor"] + len(events[3:]),
            "random_state_captured": validate_worldbridge_deterministic_randomness_snapshot(checkpoint["randomness_snapshot"])["valid"],
            "tick_order_fixed": tuple(checkpoint["phase_order"]) == PHASE_ORDER,
            "controlled_restart_reproduced": scalar_state_equal and suffix_baseline == suffix_restarted,
        },
        "production_live_adapter_admitted": False,
        "full_unified_replay_admitted": False,
        "cross_lane_replay": False,
        "default_ready": False,
    }


def validate_e313_checkpoint(checkpoint: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(checkpoint, Mapping):
        return {"valid": False, "errors": ["checkpoint_must_be_mapping"]}
    if checkpoint.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if checkpoint.get("status") != STATUS:
        errors.append("status_mismatch")
    if checkpoint.get("phase_order") != list(PHASE_ORDER):
        errors.append("phase_order_mismatch")
    for field in ("tick", "input_cursor"):
        value = checkpoint.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"{field}_invalid")
    for field in ("sr_position", "ps_energy"):
        if isinstance(checkpoint.get(field), bool) or not isinstance(checkpoint.get(field), (int, float)):
            errors.append(f"{field}_invalid")
    random_snapshot = checkpoint.get("randomness_snapshot")
    if validate_worldbridge_deterministic_randomness_snapshot(random_snapshot)["valid"] is not True:
        errors.append("randomness_snapshot_invalid")
    digest = checkpoint.get("checkpoint_digest")
    if not isinstance(digest, str) or digest != _digest(checkpoint, "checkpoint_digest"):
        errors.append("checkpoint_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_e313_bounded_replay_corpus() -> dict[str, Any]:
    corpus = run_e313_bounded_replay_protocol()
    corpus["checkpoint_validation"] = validate_e313_checkpoint(corpus["checkpoint"])
    corpus["protocol_valid"] = bool(
        corpus["checkpoint_validation"]["valid"]
        and all(corpus["evidence"].values())
        and corpus["production_live_adapter_admitted"] is False
        and corpus["full_unified_replay_admitted"] is False
    )
    return corpus


__all__ = [
    "PHASE_ORDER",
    "STATUS",
    "build_worldbridge_e313_bounded_replay_corpus",
    "run_e313_bounded_replay_protocol",
    "validate_e313_checkpoint",
]




