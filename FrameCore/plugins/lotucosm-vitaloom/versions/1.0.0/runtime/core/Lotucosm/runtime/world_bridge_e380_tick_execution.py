"""Opt-in evidence for executing one existing dual-lane tick.

The module records and compares an invocation of the existing host-owned tick
boundary.  It does not schedule ticks, dispatch Qt events, or mutate either
lane.  Callers provide the captured before/after checkpoints and therefore
retain ownership of the UI-host adapter.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_e379_tick_envelope import digest_worldbridge_e379_state


SCHEMA_VERSION = 1
STATUS = "worldbridge_e380_tick_execution"
_IDENTITY_KEYS = frozenset(
    {
        "runtime_epoch",
        "capture_id",
        "checkpoint_id",
        "context_id",
        "digest",
        "capture_digest",
        "snapshot_digest",
        "envelope_digest",
        "checkpoint_digest",
        "evidence_digest",
        "receipt_digest",
        "process_owner_binding",
    }
)


def canonicalize_e380_checkpoint(value: object) -> object:
    """Project checkpoint state without lane-local identity or derived seals."""
    if isinstance(value, Mapping):
        return {
            str(key): canonicalize_e380_checkpoint(child)
            for key, child in value.items()
            if key not in _IDENTITY_KEYS
        }
    if isinstance(value, list):
        return [canonicalize_e380_checkpoint(child) for child in value]
    if isinstance(value, tuple):
        return [canonicalize_e380_checkpoint(child) for child in value]
    return copy.deepcopy(value)


def digest_e380_checkpoint(value: object) -> str:
    return digest_worldbridge_e379_state(canonicalize_e380_checkpoint(value))


def build_worldbridge_e380_tick_execution(
    *,
    sequence: int,
    sr_delta_seconds: float,
    ps_ticks: int,
    input_events: Sequence[Mapping[str, Any]],
    before_checkpoint: Mapping[str, Any],
    after_checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a non-negative integer")
    if isinstance(sr_delta_seconds, bool) or not isinstance(sr_delta_seconds, (int, float)):
        raise ValueError("sr_delta_seconds must be numeric")
    if float(sr_delta_seconds) < 0:
        raise ValueError("sr_delta_seconds must be non-negative")
    if isinstance(ps_ticks, bool) or not isinstance(ps_ticks, int) or ps_ticks < 0:
        raise ValueError("ps_ticks must be a non-negative integer")
    if not isinstance(before_checkpoint, Mapping) or not isinstance(after_checkpoint, Mapping):
        raise TypeError("checkpoints must be mappings")
    events = [dict(event) for event in input_events]
    for index, event in enumerate(events):
        if set(event) != {"sequence", "tick", "action", "payload"}:
            raise ValueError("input event shape is invalid")
        if event["sequence"] != index:
            raise ValueError("input event sequence must be contiguous")
        if event["tick"] != sequence:
            raise ValueError("input event tick must match execution sequence")
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "sequence": sequence,
        "sr_delta_seconds": float(sr_delta_seconds),
        "ps_ticks": ps_ticks,
        "input_events": events,
        "before_state_digest": digest_e380_checkpoint(before_checkpoint),
        "after_state_digest": digest_e380_checkpoint(after_checkpoint),
        "before_rng_digest": digest_e380_checkpoint(before_checkpoint.get("randomness_state")),
        "after_rng_digest": digest_e380_checkpoint(after_checkpoint.get("randomness_state")),
        "after_input_digest": digest_e380_checkpoint(after_checkpoint.get("input_state")),
        "component_state_digests": {
            field: {
                "before": digest_e380_checkpoint(before_checkpoint.get(field)),
                "after": digest_e380_checkpoint(after_checkpoint.get(field)),
            }
            for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")
        },
        "shared_tick_identity": f"e380:{sequence}",
        "execution_invoked": True,
        "input_consumption_observed": True,
        "rng_consumption_observed": True,
        "shared_clock_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    result["execution_digest"] = digest_worldbridge_e379_state(result)
    return result


def compare_worldbridge_e380_tick_executions(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> dict[str, Any]:
    required = {
        "schema_version", "status", "sequence", "sr_delta_seconds", "ps_ticks",
        "input_events", "before_state_digest", "after_state_digest",
        "before_rng_digest", "after_rng_digest", "after_input_digest",
        "component_state_digests",
        "shared_tick_identity", "execution_invoked", "input_consumption_observed",
        "rng_consumption_observed", "shared_clock_admitted", "replay_admitted",
        "default_ready", "lossless", "execution_digest",
    }
    if set(left) != required or set(right) != required:
        return {"equal": False, "reason": "schema_mismatch"}
    if left.get("execution_digest") != digest_worldbridge_e379_state(
        {key: value for key, value in left.items() if key != "execution_digest"}
    ) or right.get("execution_digest") != digest_worldbridge_e379_state(
        {key: value for key, value in right.items() if key != "execution_digest"}
    ):
        return {"equal": False, "reason": "execution_digest_mismatch"}
    equal = dict(left) == dict(right)
    return {"equal": equal, "reason": "canonical_match" if equal else "execution_state_mismatch"}


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e380_tick_execution",
    "canonicalize_e380_checkpoint",
    "compare_worldbridge_e380_tick_executions",
    "digest_e380_checkpoint",
]
