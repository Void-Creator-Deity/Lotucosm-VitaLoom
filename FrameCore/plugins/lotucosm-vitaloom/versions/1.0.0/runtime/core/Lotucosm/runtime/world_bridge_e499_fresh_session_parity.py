"""E499 fresh-session parity evidence for the quarantined shared transport."""
from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    WorldBridgeDeterministicRandomnessContext,
    restore_worldbridge_deterministic_randomness_context,
)
from .world_bridge_e498_rng_input_witness import (
    build_worldbridge_e498_rng_input_witness,
)
from .world_bridge_shared_state_transport import WorldBridgeSharedStateReceiver

SCHEMA_VERSION = 1
STATUS = "worldbridge_e499_fresh_session_parity"


def build_worldbridge_e499_fresh_session_parity(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    source_context: WorldBridgeDeterministicRandomnessContext,
    fresh_context: WorldBridgeDeterministicRandomnessContext,
) -> dict[str, Any]:
    """Prove detached receiver and RNG restoration in an explicitly provisioned session."""
    base = build_worldbridge_e498_rng_input_witness(envelopes)
    copied = [copy.deepcopy(dict(item)) for item in envelopes]
    last_snapshot = copied[-1]["rng_context_snapshot"]
    if last_snapshot is None:
        raise ValueError("E499 requires a final RNG snapshot")
    if source_context.snapshot() != last_snapshot:
        raise ValueError("source context is not positioned at final envelope snapshot")
    if fresh_context.context_id != source_context.context_id:
        raise ValueError("fresh RNG context id mismatch")

    fresh_receiver = WorldBridgeSharedStateReceiver()
    fresh_receiver.restore_continuity(base["receiver"])
    restore_worldbridge_deterministic_randomness_context(fresh_context, last_snapshot)
    restored_snapshot = fresh_context.snapshot()
    restored_cursor_equal = fresh_receiver.continuity_snapshot() == base["receiver"]
    restored_rng_equal = restored_snapshot == last_snapshot

    source_next: list[dict[str, Any]] = []
    fresh_next: list[dict[str, Any]] = []
    for stream_name in source_context.stream_names:
        source_stream = source_context.get_stream(stream_name)
        fresh_stream = fresh_context.get_stream(stream_name)
        draw_source = getattr(source_stream, "random", None)
        draw_fresh = getattr(fresh_stream, "random", None)
        if not callable(draw_source) or not callable(draw_fresh):
            raise ValueError("E499 supports only random()-compatible registered streams")
        draw_source()
        draw_fresh()
        source_next.append(source_context.snapshot())
        fresh_next.append(fresh_context.snapshot())
    next_generation_equal = source_next == fresh_next
    witness = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "base_witness": base,
        "source_context_id": source_context.context_id,
        "fresh_context_id": fresh_context.context_id,
        "receiver_cursor_restored": restored_cursor_equal,
        "rng_snapshot_restored": restored_rng_equal,
        "next_generation_equal": next_generation_equal,
        "fresh_session_parity": bool(restored_cursor_equal and restored_rng_equal and next_generation_equal),
        "provenance_required": True,
        "replay_admitted": False,
        "default_ready": False,
    }
    return witness


def validate_worldbridge_e499_fresh_session_parity(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("identity_mismatch")
    if value.get("read_only") is not True or value.get("provenance_required") is not True:
        errors.append("provenance_or_read_only_mismatch")
    if value.get("source_context_id") != value.get("fresh_context_id"):
        errors.append("context_ids_mismatch")
    for field in ("receiver_cursor_restored", "rng_snapshot_restored", "next_generation_equal", "fresh_session_parity"):
        if value.get(field) is not True:
            errors.append(f"{field}_not_proven")
    if value.get("replay_admitted") is not False or value.get("default_ready") is not False:
        errors.append("admission_overclaim")
    base = value.get("base_witness")
    if not isinstance(base, Mapping) or base.get("fresh_session_parity") is not False:
        errors.append("base_witness_invalid")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_e499_fresh_session_parity",
    "validate_worldbridge_e499_fresh_session_parity",
]
