"""Qt-free comparison contract for a bounded sequence of E380 executions."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_e379_tick_envelope import digest_worldbridge_e379_state
from .world_bridge_e380_tick_execution import compare_worldbridge_e380_tick_executions


SCHEMA_VERSION = 1
STATUS = "worldbridge_e381_tick_sequence"


def build_worldbridge_e381_tick_sequence(
    records: Sequence[Mapping[str, Any]],
    *,
    dynamic_spawn_observed: bool,
    dynamic_despawn_observed: bool,
) -> dict[str, Any]:
    if not records:
        raise ValueError("tick sequence must not be empty")
    if not isinstance(dynamic_spawn_observed, bool) or not isinstance(dynamic_despawn_observed, bool):
        raise TypeError("lifecycle observations must be boolean")
    copied = [dict(record) for record in records]
    sequences = [record.get("sequence") for record in copied]
    if sequences != list(range(1, len(copied) + 1)):
        raise ValueError("tick sequence numbers must be contiguous from one")
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "tick_count": len(copied),
        "records": copied,
        "dynamic_spawn_observed": dynamic_spawn_observed,
        "dynamic_despawn_observed": dynamic_despawn_observed,
        "continuous_execution_observed": True,
        "shared_clock_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    result["component_digests"] = {
        field: digest_worldbridge_e379_state([
            record["component_state_digests"][field] for record in copied
        ])
        for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")
    }
    result["sequence_digest"] = digest_worldbridge_e379_state(result)
    return result


def compare_worldbridge_e381_tick_sequences(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> dict[str, Any]:
    required = {
        "schema_version", "status", "tick_count", "records",
        "dynamic_spawn_observed", "dynamic_despawn_observed",
        "continuous_execution_observed", "shared_clock_admitted",
        "replay_admitted", "default_ready", "lossless", "component_digests", "sequence_digest",
    }
    if set(left) != required or set(right) != required:
        return {"equal": False, "reason": "schema_mismatch"}
    for candidate in (left, right):
        unsigned = {key: value for key, value in candidate.items() if key != "sequence_digest"}
        if candidate.get("sequence_digest") != digest_worldbridge_e379_state(unsigned):
            return {"equal": False, "reason": "sequence_digest_mismatch"}
    if len(left["records"]) != len(right["records"]):
        return {"equal": False, "reason": "tick_count_mismatch"}
    for index, (left_record, right_record) in enumerate(zip(left["records"], right["records"], strict=True), 1):
        parity = compare_worldbridge_e380_tick_executions(left_record, right_record)
        if parity.get("equal") is not True:
            return {"equal": False, "reason": f"tick_{index}_{parity.get('reason', 'mismatch')}"}
    return {"equal": dict(left) == dict(right), "reason": "canonical_match" if dict(left) == dict(right) else "sequence_state_mismatch"}


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e381_tick_sequence",
    "compare_worldbridge_e381_tick_sequences",
]
