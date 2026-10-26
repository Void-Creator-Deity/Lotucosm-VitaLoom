# -*- coding: utf-8 -*-
"""Qt-free SR-local randomness ownership used by the WorldBridge dual runtime.

The helpers in this module own neither Python's module-global RNG nor NumPy's
legacy global RNG. They resolve one explicit seed for a loaded SR scene and
construct the caller-held ``random.Random`` instance used by that SR runtime
lifetime. This is deliberately not a cross-lane RNG protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_SR_RUNTIME_SEED = 12345
SEED_SOURCES = (
    "pond_config.sr_runtime_seed",
    "pond_config.proc_seed",
    "constant_12345",
)


@dataclass(frozen=True)
class SrRuntimeRandomnessConfig:
    """Resolved, immutable seed metadata for one loaded SR runtime."""

    seed: int
    seed_source: str


def resolve_sr_runtime_randomness_config(
    scene_data: Mapping[str, Any] | None,
) -> SrRuntimeRandomnessConfig:
    """Resolve an additive SR seed without touching process-global RNG state."""
    scene = scene_data if isinstance(scene_data, Mapping) else {}
    pond = scene.get("pond_config")
    pond_config = pond if isinstance(pond, Mapping) else {}
    for key, source in (
        ("sr_runtime_seed", "pond_config.sr_runtime_seed"),
        ("proc_seed", "pond_config.proc_seed"),
    ):
        parsed = _coerce_seed(pond_config.get(key))
        if parsed is not None:
            return SrRuntimeRandomnessConfig(seed=parsed, seed_source=source)
    return SrRuntimeRandomnessConfig(
        seed=DEFAULT_SR_RUNTIME_SEED,
        seed_source="constant_12345",
    )


class WorldBridgeCountingRandom(random.Random):
    """SR-local Random that exposes real draw count without changing values."""

    def __init__(self, seed: object) -> None:
        super().__init__(seed)
        self.worldbridge_draw_count = 0

    def random(self) -> float:
        self.worldbridge_draw_count += 1
        return super().random()


def create_sr_runtime_randomness_rng(
    config: SrRuntimeRandomnessConfig,
) -> random.Random:
    """Create a caller-held SR-local RNG without mutating process-global state."""
    if not isinstance(config, SrRuntimeRandomnessConfig):
        raise TypeError("config must be an SrRuntimeRandomnessConfig")
    return WorldBridgeCountingRandom(config.seed)


def create_detached_sr_entity_randomness_rng(
    entity_id: object,
    entity_type: object,
    position: tuple[float, float],
    radius: float,
) -> random.Random:
    """Return deterministic test/tool fallback randomness for a detached entity.

    Production SR construction receives the loaded-runtime owner. This fallback
    preserves direct nested-entity construction for tests and tooling without
    consuming a process-global or entropy-seeded RNG.
    """
    payload = json.dumps(
        {
            "entity_id": str(entity_id),
            "entity_type": str(entity_type),
            "position": [float(position[0]), float(position[1])],
            "radius": float(radius),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(seed)


def build_worldbridge_sr_runtime_randomness_contract() -> dict[str, Any]:
    """Return static E235 authority facts; this function consumes no RNG draws."""
    contract = {
        "schema_version": SCHEMA_VERSION,
        "contract": "worldbridge_sr_runtime_randomness_ownership",
        "read_only": True,
        "qt_free": True,
        "sr_runtime_owner": "one_caller_held_python_random_per_loaded_sr_scene_runtime",
        "seed_resolution": list(SEED_SOURCES),
        "sr_paths_using_owner": [
            "scene_runtime_entity_initial_velocity",
            "nutrient_spawn_position",
            "signal_edge_mutation",
            "legacy_respawn_admission",
            "legacy_respawn_mind_mutation",
        ],
        "legacy_unseeded_random_instance_remaining": False,
        "legacy_python_hash_derived_seed_remaining": False,
        "global_python_random_reseeded": False,
        "global_numpy_random_reseeded": False,
        "global_rng_state_captured": False,
        "sr_rng_state_checkpointed": False,
        "opt_in_respawn_two_stream_override": True,
        "ps_default_random_owner": "numpy_legacy_global_randomstate_plus_python_global_and_local_instances",
        "bridge_rng_context_transport": False,
        "bridge_seed_agreement": False,
        "bridge_rng_state_checkpoint": False,
        "cross_lane_consumption_order_captured": False,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
    }
    validation = validate_worldbridge_sr_runtime_randomness_contract(contract)
    contract["contract_valid"] = validation["valid"]
    return contract


def validate_worldbridge_sr_runtime_randomness_contract(contract: object) -> dict[str, Any]:
    """Reject claims beyond the SR-local authority genuinely implemented here."""
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("contract") != "worldbridge_sr_runtime_randomness_ownership":
        errors.append("contract_name_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("qt_free") is not True:
        errors.append("qt_free_required")
    if contract.get("sr_runtime_owner") != "one_caller_held_python_random_per_loaded_sr_scene_runtime":
        errors.append("sr_runtime_owner_mismatch")
    if contract.get("seed_resolution") != list(SEED_SOURCES):
        errors.append("seed_resolution_mismatch")
    paths = contract.get("sr_paths_using_owner")
    if not isinstance(paths, list) or set(paths) != {
        "scene_runtime_entity_initial_velocity",
        "nutrient_spawn_position",
        "signal_edge_mutation",
        "legacy_respawn_admission",
        "legacy_respawn_mind_mutation",
    }:
        errors.append("sr_paths_using_owner_mismatch")
    for field in (
        "legacy_unseeded_random_instance_remaining",
        "legacy_python_hash_derived_seed_remaining",
        "global_python_random_reseeded",
        "global_numpy_random_reseeded",
        "global_rng_state_captured",
        "sr_rng_state_checkpointed",
        "bridge_rng_context_transport",
        "bridge_seed_agreement",
        "bridge_rng_state_checkpoint",
        "cross_lane_consumption_order_captured",
        "atomic_checkpoint",
        "lossless",
        "replay_admitted",
        "default_ready",
    ):
        if contract.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if contract.get("opt_in_respawn_two_stream_override") is not True:
        errors.append("respawn_override_missing")
    if contract.get("ps_default_random_owner") != "numpy_legacy_global_randomstate_plus_python_global_and_local_instances":
        errors.append("ps_owner_mismatch")
    return {"valid": not errors, "errors": errors}


def _coerce_seed(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


__all__ = [
    "DEFAULT_SR_RUNTIME_SEED",
    "SCHEMA_VERSION",
    "SEED_SOURCES",
    "SrRuntimeRandomnessConfig",
    "build_worldbridge_sr_runtime_randomness_contract",
    "create_detached_sr_entity_randomness_rng",
    "create_sr_runtime_randomness_rng",
    "resolve_sr_runtime_randomness_config",
    "validate_worldbridge_sr_runtime_randomness_contract",
]
