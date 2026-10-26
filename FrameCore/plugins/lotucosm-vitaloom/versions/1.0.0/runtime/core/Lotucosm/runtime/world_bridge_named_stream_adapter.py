# -*- coding: utf-8 -*-
"""Opt-in adapter from an E223 named Python stream to one SR mind mutation seam."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.sr_mind_gene import mind_dict_mutate
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    WorldBridgeDeterministicRandomnessContext,
)


ADAPTER_SCHEMA_VERSION = 1
ADAPTER_KIND = "worldbridge_named_stream_sr_mind_mutation_adapter"
SUPPORTED_STREAM_FAMILY = "python_random"


def _stream_family(context: WorldBridgeDeterministicRandomnessContext, stream_name: str) -> str:
    snapshot = context.snapshot()
    for row in snapshot.get("streams", []):
        if row.get("stream_name") == stream_name:
            return str(row.get("family"))
    raise KeyError(f"unregistered deterministic stream: {stream_name}")


def validate_worldbridge_named_stream_sr_mind_adapter(
    context: object,
    stream_name: str,
) -> dict[str, Any]:
    """Validate one caller-owned Python stream without changing its state."""
    if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
        raise TypeError("context must be a WorldBridgeDeterministicRandomnessContext")
    if not isinstance(stream_name, str) or not stream_name:
        raise ValueError("stream_name must be a non-empty string")
    family = _stream_family(context, stream_name)
    if family != SUPPORTED_STREAM_FAMILY:
        raise ValueError(
            f"SR mind mutation adapter requires {SUPPORTED_STREAM_FAMILY!r}, got {family!r}"
        )
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "adapter_kind": ADAPTER_KIND,
        "context_id": context.context_id,
        "stream_name": stream_name,
        "stream_family": family,
        "caller_owned": True,
        "default_tick_attached": False,
        "restore_performed": False,
        "replay_admitted": False,
        "default_ready": False,
    }


def mutate_sr_mind_with_worldbridge_named_stream(
    context: WorldBridgeDeterministicRandomnessContext,
    stream_name: str,
    parent_slice: Mapping[str, float],
    sigma: float,
    *,
    gene_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run the existing SR/PS-aligned mind mutation with one named local stream."""
    contract = validate_worldbridge_named_stream_sr_mind_adapter(context, stream_name)
    before = context.snapshot()
    stream = context.get_stream(stream_name)
    child, deltas = mind_dict_mutate(
        parent_slice,
        float(sigma),
        stream,
        gene_keys=gene_keys,
    )
    after = context.snapshot()
    return {
        **contract,
        "parent": {str(key): float(value) for key, value in parent_slice.items()},
        "child": child,
        "deltas": deltas,
        "before_snapshot_digest": before["snapshot_digest"],
        "after_snapshot_digest": after["snapshot_digest"],
        "stream_state_changed": before != after,
        "replay_input": False,
        "checkpoint_state": False,
        "lossless": False,
    }


def build_worldbridge_named_stream_adapter_contract() -> dict[str, Any]:
    """Return static contract facts without constructing a context or consuming RNG."""
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "adapter_kind": ADAPTER_KIND,
        "supported_consumer": "sr_mind_gene.mind_dict_mutate",
        "supported_stream_family": SUPPORTED_STREAM_FAMILY,
        "caller_owned": True,
        "default_tick_attached": False,
        "global_rng_reseeded": False,
        "restore_api_exposed": False,
        "replay_admitted": False,
        "default_ready": False,
    }


TWO_STREAM_HANDOFF_KIND = "worldbridge_named_stream_sr_respawn_two_stream_handoff"


def validate_worldbridge_named_stream_sr_respawn_handoff(
    context: object,
    decision_stream_name: str,
    mutation_stream_name: str,
) -> dict[str, Any]:
    """Validate distinct caller-owned Python streams for decision and mutation roles."""
    decision = validate_worldbridge_named_stream_sr_mind_adapter(
        context, decision_stream_name
    )
    mutation = validate_worldbridge_named_stream_sr_mind_adapter(
        context, mutation_stream_name
    )
    if decision_stream_name == mutation_stream_name:
        raise ValueError("decision and mutation stream names must be distinct")
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "handoff_kind": TWO_STREAM_HANDOFF_KIND,
        "context_id": decision["context_id"],
        "decision_stream_name": decision_stream_name,
        "mutation_stream_name": mutation_stream_name,
        "stream_family": SUPPORTED_STREAM_FAMILY,
        "ordered_roles": ["decision", "mutation_if_admitted"],
        "caller_owned": True,
        "default_tick_attached": False,
        "replay_admitted": False,
        "default_ready": False,
    }


def evaluate_sr_mind_mutation_decision_with_worldbridge_named_stream(
    context: WorldBridgeDeterministicRandomnessContext,
    stream_name: str,
    probability: float,
) -> dict[str, Any]:
    """Consume one local draw and classify one bounded mutation decision."""
    contract = validate_worldbridge_named_stream_sr_mind_adapter(context, stream_name)
    clean_probability = float(probability)
    if not 0.0 <= clean_probability <= 1.0:
        raise ValueError("probability must be between 0.0 and 1.0")
    before = context.snapshot()
    stream = context.get_stream(stream_name)
    sampled_value = float(stream.random())
    after = context.snapshot()
    return {
        **contract,
        "decision_kind": "probability_threshold",
        "probability": clean_probability,
        "sampled_value": sampled_value,
        "admitted": sampled_value < clean_probability,
        "before_snapshot_digest": before["snapshot_digest"],
        "after_snapshot_digest": after["snapshot_digest"],
        "stream_state_changed": before != after,
    }


def run_worldbridge_named_stream_sr_respawn_handoff(
    context: WorldBridgeDeterministicRandomnessContext,
    decision_stream_name: str,
    mutation_stream_name: str,
    parent_slice: Mapping[str, float],
    sigma: float,
    probability: float,
    *,
    gene_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run the local decision first and consume mutation state only when admitted."""
    contract = validate_worldbridge_named_stream_sr_respawn_handoff(
        context, decision_stream_name, mutation_stream_name
    )
    parent = {str(key): float(value) for key, value in parent_slice.items()}
    before = context.snapshot()
    decision = evaluate_sr_mind_mutation_decision_with_worldbridge_named_stream(
        context, decision_stream_name, probability
    )
    after_decision = context.snapshot()
    if decision["admitted"]:
        mutation = mutate_sr_mind_with_worldbridge_named_stream(
            context,
            mutation_stream_name,
            parent,
            sigma,
            gene_keys=gene_keys,
        )
        child = mutation["child"]
        deltas = mutation["deltas"]
    else:
        mutation = None
        child = dict(parent)
        deltas = {}
    after = context.snapshot()
    return {
        **contract,
        "probability": decision["probability"],
        "sampled_value": decision["sampled_value"],
        "admitted": decision["admitted"],
        "parent": parent,
        "child": child,
        "deltas": deltas,
        "before_snapshot_digest": before["snapshot_digest"],
        "after_decision_snapshot_digest": after_decision["snapshot_digest"],
        "after_snapshot_digest": after["snapshot_digest"],
        "before_snapshot": before,
        "after_decision_snapshot": after_decision,
        "after_snapshot": after,
        "decision_stream_state_changed": decision["stream_state_changed"],
        "mutation_stream_consumed": mutation is not None,
        "ordered_steps": ["decision"] + (["mutation"] if mutation is not None else []),
        "replay_input": False,
        "checkpoint_state": False,
        "lossless": False,
    }


def build_worldbridge_respawn_two_stream_handoff_contract() -> dict[str, Any]:
    """Return static E225 facts without constructing or consuming any stream."""
    return {
        "schema_version": ADAPTER_SCHEMA_VERSION,
        "handoff_kind": TWO_STREAM_HANDOFF_KIND,
        "supported_consumer": "sr_war_respawn_mind_decision_then_mutation",
        "required_stream_family": SUPPORTED_STREAM_FAMILY,
        "required_distinct_stream_count": 2,
        "ordered_roles": ["decision", "mutation_if_admitted"],
        "caller_owned": True,
        "default_tick_attached": False,
        "global_rng_reseeded": False,
        "restore_api_exposed": False,
        "replay_admitted": False,
        "default_ready": False,
    }




