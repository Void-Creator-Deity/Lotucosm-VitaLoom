# -*- coding: utf-8 -*-
"""Qt-free WorldBridge cross-lane randomness authority evidence.

This module inventories randomness reachable from the current SR/PS bridge call
path and offers explicit observation plus opt-in restoration of the two
process-global RNG states that expose stable state APIs today. Restoration is
never attached to a default tick and does not admit replay.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import re
from collections.abc import Mapping
from typing import Any

import numpy as np

from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_entropy_audit,
    build_native_entropy_boundary_receipt,
)


SCHEMA_VERSION = 1
CAPTURE_KIND = "worldbridge_global_random_state_observation"
RNG_CHECKPOINT_SCHEMA_VERSION = 1
RNG_CHECKPOINT_KIND = "worldbridge_rng_checkpoint"
_CAPTURE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

CAPTURED_AUTHORITY_IDS = (
    "python_process_global_random",
    "numpy_legacy_global_randomstate",
)

UNCAPTURED_AUTHORITY_IDS = (
    "explicit_caller_owned_rng_instances",
    "dynamic_script_plugin_entropy",
    "native_extension_or_third_party_rng",
)

AUTHORITY_IDS = CAPTURED_AUTHORITY_IDS + UNCAPTURED_AUTHORITY_IDS

_CAPTURE_KEYS = {
    "schema_version",
    "capture_kind",
    "capture_id",
    "read_only",
    "authorities",
    "captured_authority_ids",
    "uncaptured_authority_ids",
    "thread_atomic",
    "cross_authority_atomic",
    "global_states_advanced_by_capture",
    "global_states_reseeded",
    "restore_performed",
    "restore_api_exposed",
    "initial_seed_sufficient",
    "all_authorities_captured",
    "cross_lane_consumption_order_captured",
    "dynamic_entropy_boundary_closed",
    "native_entropy_boundary_closed",
    "replay_input",
    "checkpoint_state",
    "replay_admitted",
    "default_ready",
    "capture_digest",
}

_PYTHON_STATE_KEYS = {
    "format",
    "version",
    "internal_state",
    "gaussian_cache",
}

_NUMPY_STATE_KEYS = {
    "format",
    "bit_generator",
    "state_key",
    "position",
    "has_gauss",
    "cached_gaussian",
}

_FALSE_CLAIMS = (
    "thread_atomic",
    "cross_authority_atomic",
    "global_states_advanced_by_capture",
    "global_states_reseeded",
    "restore_performed",
    "restore_api_exposed",
    "initial_seed_sufficient",
    "all_authorities_captured",
    "cross_lane_consumption_order_captured",
    "dynamic_entropy_boundary_closed",
    "native_entropy_boundary_closed",
    "replay_input",
    "checkpoint_state",
    "replay_admitted",
    "default_ready",
)


def build_worldbridge_randomness_authority_inventory() -> list[dict[str, Any]]:
    """Return the deterministic E221 randomness/entropy authority inventory."""
    native_audit = build_native_entropy_audit()
    native_receipt = build_native_entropy_boundary_receipt()
    inventory = [
        {
            "authority_id": "python_process_global_random",
            "family": "python_random_module_global_mt19937",
            "owner_scope": "python_process_global",
            "reachability": "direct_and_conditional_across_sr_and_ps_bridge_work",
            "observed_sites": [
                "core/VitaLoom/viewports/game_viewport.py:random.uniform/random.random",
                "builtin/systems/assembly_system.py:random.random/random.randint",
                "builtin/systems/inheritance.py:random.random",
                "builtin/systems/mutation.py:random.random/random.gauss",
                "core/Lotucosm/memory.py:random.random/random.gauss",
            ],
            "initialization_path": "implicit module-global initialization or caller reseed",
            "consumption_boundary": "SR runtime phases and conditional Pond systems/organism updates",
            "capture_status": "captured_by_explicit_opt_in_observation",
            "state_api": "random.getstate",
            "restore_api": "random.setstate",
            "initial_seed_sufficient": False,
            "serializable": True,
            "restore_feasible": True,
            "ordering_sensitive": True,
            "project_configuration_coverage": "not declared by project or scene manifests",
            "notes": "State can be observed, but interleaved consumption order is not captured.",
        },
        {
            "authority_id": "numpy_legacy_global_randomstate",
            "family": "numpy_legacy_process_global_randomstate_mt19937",
            "owner_scope": "python_process_global_numpy_legacy_singleton",
            "reachability": "conditional_during_pond_update_and_ps_entity_system_work",
            "observed_sites": [
                "core/Lotucosm/pond.py:np.random.uniform",
                "core/Lotucosm/perception.py:np.random.normal",
                "core/Lotucosm/component.py:np.random.uniform",
                "builtin/entity_types/organism.py:np.random.uniform",
                "builtin/entity_types/reproduction.py:np.random",
                "builtin/systems/floating_system.py:np.random.randn/random/uniform",
                "builtin/systems/resource_manager.py:np.random",
            ],
            "initialization_path": "NumPy legacy singleton initialization or caller reseed",
            "consumption_boundary": "Pond systems, organisms, resource generation, and reproduction",
            "capture_status": "captured_by_explicit_opt_in_observation",
            "state_api": "numpy.random.get_state",
            "restore_api": "numpy.random.set_state",
            "initial_seed_sufficient": False,
            "serializable": True,
            "restore_feasible": True,
            "ordering_sensitive": True,
            "project_configuration_coverage": "not declared by project or scene manifests",
            "notes": "Only the legacy global RandomState is observed; Generator instances are separate.",
        },
        {
            "authority_id": "explicit_caller_owned_rng_instances",
            "family": "python_random_random_or_numpy_generator_instance",
            "owner_scope": "caller_owned_local_or_component",
            "reachability": "SR-local loaded-runtime owner plus procedural/mutation helpers;_generator_not_proven_in_bridge",
            "observed_sites": [
                "core/VitaLoom/viewports/game_viewport.py:_sr_runtime_rng seeded from pond_config",
                "core/Lotucosm/sr_game_procedural.py:random.Random(int(seed))",
                "core/Lotucosm/sr_mind_gene.py:caller-provided random.Random",
                "core/Lotucosm/sr_memory_gene_bridge.py:caller-provided random.Random",
                "core/Lotucosm/sr_membrane_topology.py:caller-provided random.Random",
            ],
            "initialization_path": "explicit caller seed or caller-created RNG object",
            "consumption_boundary": "procedural generation and SR mutation/topology helpers",
            "capture_status": "not_captured",
            "state_api": "instance-specific getstate or bit_generator.state",
            "restore_api": "instance-specific setstate or bit_generator.state assignment",
            "initial_seed_sufficient": False,
            "serializable": "owner_dependent",
            "restore_feasible": "owner_dependent",
            "ordering_sensitive": True,
            "project_configuration_coverage": "seed may be caller data but consumed state is not standardized",
            "notes": "E235 owns one SR runtime Random instance, but no common registry/checkpoint covers all live Random/Generator instances or PS globals.",
        },
        {
            "authority_id": "dynamic_script_plugin_entropy",
            "family": "dynamic_python_script_or_plugin_defined_entropy",
            "owner_scope": "script_or_plugin_defined",
            "reachability": "reachable_from_sr_script_phase_and_extension_hooks",
            "observed_sites": [
                "builtin/templates/official_cell_behavior.py:ScriptBase.random_uniform",
                "core/VitaLoom/viewports/game_viewport.py:dynamic SR script execution",
            ],
            "initialization_path": "dynamic script/plugin imports and owner-defined initialization",
            "consumption_boundary": "SR script phase or plugin hook",
            "capture_status": "not_captured",
            "state_api": "unknown_owner_defined",
            "restore_api": "unknown_owner_defined",
            "initial_seed_sufficient": False,
            "serializable": False,
            "restore_feasible": False,
            "ordering_sensitive": True,
            "project_configuration_coverage": "open dynamic boundary",
            "notes": "Static inventory cannot prove that scripts/plugins introduce no additional entropy.",
        },
        {
            "authority_id": "native_extension_or_third_party_rng",
            "family": "native_extension_or_third_party_defined_rng",
            "owner_scope": "native_or_dependency_defined",
            "reachability": "not_ruled_out_beneath_numpy_physics_scripts_or_future_plugins",
            "observed_sites": [
                "Pond.update dependency/native call boundary",
                "dynamic plugin and extension boundary",
            ],
            "initialization_path": "dependency or native implementation defined",
            "consumption_boundary": "opaque native/dependency calls reachable from lane work",
            "capture_status": "unknown_not_captured",
            "state_api": "not_proven",
            "restore_api": "not_proven",
            "initial_seed_sufficient": False,
            "serializable": False,
            "restore_feasible": False,
            "ordering_sensitive": True,
            "project_configuration_coverage": "no closed native RNG registry or audit evidence",
            "notes": "Absence of a known source is not evidence that every native source is absent.",
            "shipped_source_audit": native_audit,
            "boundary_receipt": native_receipt,
        },
    ]
    return copy.deepcopy(inventory)


def build_worldbridge_randomness_authority_contract() -> dict[str, Any]:
    """Build deterministic E221 status evidence without reading global RNG state."""
    python_example = random.Random(221).getstate()
    numpy_example = np.random.RandomState(221).get_state()
    example_capture = _build_capture_from_states(
        capture_id="e221-contract-example",
        python_state=python_example,
        numpy_state=numpy_example,
    )
    validation = validate_worldbridge_global_random_state_capture(example_capture)
    inventory = build_worldbridge_randomness_authority_inventory()
    native_audit = build_native_entropy_audit()
    native_receipt = build_native_entropy_boundary_receipt()
    return {
        "schema_version": SCHEMA_VERSION,
        "contract": "worldbridge_cross_lane_randomness_authority",
        "read_only": True,
        "qt_free": True,
        "actual_bridge_call_graph": [
            "GameViewport._update_scene_runtime_entities",
            "GameViewport._run_unified_pond_bridge_tick",
            "ensure_bridged_organisms",
            "unified_pond_step_or_unified_pond_step_with_trace",
            "sync_sr_entity_to_organism",
            "Pond.update",
            "Pond_systems_and_Organism.update",
            "Pond.generate_resources_and_optional_EvolutionRunner",
            "sync_organism_to_sr_display",
        ],
        "authority_ids": list(AUTHORITY_IDS),
        "authority_count": len(inventory),
        "inventory": inventory,
        "captured_authority_ids": list(CAPTURED_AUTHORITY_IDS),
        "uncaptured_authority_ids": list(UNCAPTURED_AUTHORITY_IDS),
        "capture_api": "capture_worldbridge_global_random_states",
        "validation_api": "validate_worldbridge_global_random_state_capture",
        "restore_api_exposed": True,
        "native_entropy_audit": native_audit,
        "native_entropy_boundary_receipt": native_receipt,
        "restore_api": "restore_worldbridge_global_random_states",
        "global_state_restore_is_opt_in": True,
        "global_state_restore_thread_atomic": False,
        "global_state_restore_cross_authority_atomic": False,
        "known_restore_apis": ["random.setstate", "numpy.random.set_state"],
        "status_construction_reads_global_rng_state": False,
        "status_construction_advances_global_rng_state": False,
        "initial_seed_sufficient": False,
        "all_authorities_captured": False,
        "cross_lane_consumption_order_captured": False,
        "common_clock_captured": False,
        "dynamic_entropy_boundary_closed": False,
        "native_entropy_boundary_closed": False,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "example_capture": example_capture,
        "example_capture_validation": validation,
        "contract_valid": validation == {"valid": True, "errors": []},
    }


def capture_worldbridge_global_random_states(*, capture_id: str) -> dict[str, Any]:
    """Explicitly observe supported process-global RNG states without mutation.

    Two reads are compared so the function refuses a capture if the observed
    states changed during collection.  This still is not thread-atomic or a
    cross-authority atomic checkpoint.
    """
    clean_id = _clean_capture_id(capture_id)
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    capture = _build_capture_from_states(
        capture_id=clean_id,
        python_state=python_before,
        numpy_state=numpy_before,
    )
    python_after = random.getstate()
    numpy_after = np.random.get_state()
    if python_before != python_after or not _numpy_raw_states_equal(numpy_before, numpy_after):
        raise RuntimeError("global RNG state changed during non-atomic capture")
    validation = validate_worldbridge_global_random_state_capture(capture)
    if validation != {"valid": True, "errors": []}:
        raise RuntimeError(f"invalid RNG capture produced: {validation['errors']}")
    return copy.deepcopy(capture)


def restore_worldbridge_global_random_states(capture: Mapping[str, Any]) -> None:
    """Restore the two captured process-global states with compensation.

    This is an explicit caller-owned operation. It validates the complete
    observation first, snapshots the current globals, applies Python then
    NumPy state, and restores the originals if either setter fails.
    """
    validation = validate_worldbridge_global_random_state_capture(capture)
    if validation != {"valid": True, "errors": []}:
        raise ValueError(f"invalid global RNG capture: {validation['errors']}")
    authorities = capture["authorities"]
    python_state = authorities["python_process_global_random"]
    numpy_state = authorities["numpy_legacy_global_randomstate"]
    target_python = (
        int(python_state["version"]),
        tuple(int(value) for value in python_state["internal_state"]),
        python_state["gaussian_cache"],
    )
    target_numpy = (
        str(numpy_state["bit_generator"]),
        np.asarray(numpy_state["state_key"], dtype=np.uint32),
        int(numpy_state["position"]),
        int(numpy_state["has_gauss"]),
        float(numpy_state["cached_gaussian"]),
    )
    original_python = random.getstate()
    original_numpy = np.random.get_state()
    try:
        random.setstate(target_python)
        np.random.set_state(target_numpy)
    except Exception as exc:
        try:
            random.setstate(original_python)
            np.random.set_state(original_numpy)
        except Exception as rollback_exc:
            raise RuntimeError("global RNG restore failed and rollback failed") from rollback_exc
        raise RuntimeError("global RNG restore failed and was rolled back") from exc


def validate_worldbridge_global_random_state_capture(capture: object) -> dict[str, Any]:
    """Validate a captured observation and return errors instead of raising."""
    errors: list[str] = []
    if not isinstance(capture, Mapping):
        return {"valid": False, "errors": ["capture_not_mapping"]}

    try:
        capture_keys = set(capture.keys())
    except Exception:
        return {"valid": False, "errors": ["capture_keys_invalid"]}
    if capture_keys != _CAPTURE_KEYS:
        errors.append("capture_keys_mismatch")

    if capture.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if capture.get("capture_kind") != CAPTURE_KIND:
        errors.append("capture_kind_mismatch")
    try:
        _clean_capture_id(capture.get("capture_id"))
    except ValueError:
        errors.append("capture_id_invalid")
    if capture.get("read_only") is not True:
        errors.append("read_only_mismatch")

    captured_ids = capture.get("captured_authority_ids")
    uncaptured_ids = capture.get("uncaptured_authority_ids")
    if captured_ids != list(CAPTURED_AUTHORITY_IDS):
        errors.append("captured_authority_ids_mismatch")
    if uncaptured_ids != list(UNCAPTURED_AUTHORITY_IDS):
        errors.append("uncaptured_authority_ids_mismatch")

    for field in _FALSE_CLAIMS:
        if capture.get(field) is not False:
            errors.append(f"{field}_mismatch")

    authorities = capture.get("authorities")
    if not isinstance(authorities, Mapping):
        errors.append("authorities_not_mapping")
    else:
        try:
            authority_keys = set(authorities.keys())
        except Exception:
            authority_keys = set()
            errors.append("authority_keys_invalid")
        if authority_keys != set(CAPTURED_AUTHORITY_IDS):
            errors.append("authority_keys_mismatch")
        _validate_python_state(authorities.get("python_process_global_random"), errors)
        _validate_numpy_state(authorities.get("numpy_legacy_global_randomstate"), errors)

    digest = capture.get("capture_digest")
    if not _is_sha256(digest):
        errors.append("capture_digest_invalid")
    try:
        expected_digest = _capture_digest(capture)
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("capture_not_canonical_json")
    if expected_digest is not None and digest != expected_digest:
        errors.append("capture_digest_mismatch")

    return {"valid": not errors, "errors": errors}


def _build_capture_from_states(
    *,
    capture_id: str,
    python_state: tuple[Any, ...],
    numpy_state: tuple[Any, ...],
) -> dict[str, Any]:
    capture: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "capture_kind": CAPTURE_KIND,
        "capture_id": _clean_capture_id(capture_id),
        "read_only": True,
        "authorities": {
            "python_process_global_random": _serialize_python_state(python_state),
            "numpy_legacy_global_randomstate": _serialize_numpy_state(numpy_state),
        },
        "captured_authority_ids": list(CAPTURED_AUTHORITY_IDS),
        "uncaptured_authority_ids": list(UNCAPTURED_AUTHORITY_IDS),
        "thread_atomic": False,
        "cross_authority_atomic": False,
        "global_states_advanced_by_capture": False,
        "global_states_reseeded": False,
        "restore_performed": False,
        "restore_api_exposed": False,
        "initial_seed_sufficient": False,
        "all_authorities_captured": False,
        "cross_lane_consumption_order_captured": False,
        "dynamic_entropy_boundary_closed": False,
        "native_entropy_boundary_closed": False,
        "replay_input": False,
        "checkpoint_state": False,
        "replay_admitted": False,
        "default_ready": False,
        "capture_digest": "",
    }
    capture["capture_digest"] = _capture_digest(capture)
    return capture


def _serialize_python_state(state: tuple[Any, ...]) -> dict[str, Any]:
    if not isinstance(state, tuple) or len(state) != 3:
        raise ValueError("unsupported Python random state")
    version, internal_state, gaussian_cache = state
    return {
        "format": "python_random_getstate_v1",
        "version": int(version),
        "internal_state": [int(value) for value in internal_state],
        "gaussian_cache": None if gaussian_cache is None else float(gaussian_cache),
    }


def _serialize_numpy_state(state: tuple[Any, ...]) -> dict[str, Any]:
    if not isinstance(state, tuple) or len(state) != 5:
        raise ValueError("unsupported NumPy legacy random state")
    bit_generator, state_key, position, has_gauss, cached_gaussian = state
    return {
        "format": "numpy_legacy_get_state_v1",
        "bit_generator": str(bit_generator),
        "state_key": [int(value) for value in np.asarray(state_key).tolist()],
        "position": int(position),
        "has_gauss": int(has_gauss),
        "cached_gaussian": float(cached_gaussian),
    }


def _validate_python_state(state: object, errors: list[str]) -> None:
    if not isinstance(state, Mapping):
        errors.append("python_state_not_mapping")
        return
    try:
        keys = set(state.keys())
    except Exception:
        errors.append("python_state_keys_invalid")
        return
    if keys != _PYTHON_STATE_KEYS:
        errors.append("python_state_keys_mismatch")
    if state.get("format") != "python_random_getstate_v1":
        errors.append("python_state_format_mismatch")
    version = state.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        errors.append("python_state_version_invalid")
    internal_state = state.get("internal_state")
    if (
        not isinstance(internal_state, list)
        or len(internal_state) < 2
        or any(isinstance(value, bool) or not isinstance(value, int) for value in internal_state)
    ):
        errors.append("python_internal_state_invalid")
    gaussian_cache = state.get("gaussian_cache")
    if gaussian_cache is not None and not _is_finite_number(gaussian_cache):
        errors.append("python_gaussian_cache_invalid")


def _validate_numpy_state(state: object, errors: list[str]) -> None:
    if not isinstance(state, Mapping):
        errors.append("numpy_state_not_mapping")
        return
    try:
        keys = set(state.keys())
    except Exception:
        errors.append("numpy_state_keys_invalid")
        return
    if keys != _NUMPY_STATE_KEYS:
        errors.append("numpy_state_keys_mismatch")
    if state.get("format") != "numpy_legacy_get_state_v1":
        errors.append("numpy_state_format_mismatch")
    if state.get("bit_generator") != "MT19937":
        errors.append("numpy_bit_generator_unsupported")
    state_key = state.get("state_key")
    if (
        not isinstance(state_key, list)
        or len(state_key) != 624
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 0xFFFFFFFF
            for value in state_key
        )
    ):
        errors.append("numpy_state_key_invalid")
    position = state.get("position")
    if isinstance(position, bool) or not isinstance(position, int) or not 0 <= position <= 624:
        errors.append("numpy_position_invalid")
    has_gauss = state.get("has_gauss")
    if isinstance(has_gauss, bool) or not isinstance(has_gauss, int) or has_gauss not in (0, 1):
        errors.append("numpy_has_gauss_invalid")
    if not _is_finite_number(state.get("cached_gaussian")):
        errors.append("numpy_cached_gaussian_invalid")


def _clean_capture_id(value: object) -> str:
    if not isinstance(value, str) or _CAPTURE_ID_RE.fullmatch(value) is None:
        raise ValueError("capture_id must be a clean 1-128 character identifier")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def build_caller_owned_stream_registry_digest(streams: Mapping[str, object]) -> str:
    """Hash stable owner names/families, excluding mutable stream state."""
    rows = []
    for name, stream in sorted(streams.items(), key=lambda item: str(item[0])):
        if isinstance(stream, random.Random):
            family = "python_random"
        elif isinstance(stream, np.random.Generator):
            family = "numpy_pcg64_generator"
        else:
            raise TypeError(f"unsupported caller-owned stream: {name}")
        rows.append({"name": str(name), "family": family})
    return hashlib.sha256(_canonical_json_bytes(rows)).hexdigest()


def build_randomness_owner_inventory(
    streams: Mapping[str, object],
    modes: Mapping[str, str] | None = None,
    *,
    lifecycle: str = "active",
) -> dict[str, Any]:
    """Build the single owner catalog used by live randomness checkpoints.

    Names are semantic owner identities, not object ids, so the catalog is
    stable across capture/restore while still binding family, mode, and
    lifecycle. Detached compatibility streams remain visible instead of being
    silently treated as runtime owners.
    """
    if not isinstance(streams, Mapping):
        raise TypeError("randomness owner streams must be a mapping")
    if modes is None:
        modes = {}
    if not isinstance(modes, Mapping) or set(modes) - set(streams):
        raise ValueError("randomness owner modes must match registered streams")
    if lifecycle not in {"active", "detached", "retired"}:
        raise ValueError("invalid randomness owner lifecycle")
    owners: list[dict[str, str]] = []
    for name, stream in sorted(streams.items(), key=lambda item: str(item[0])):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("randomness owner names must be non-empty strings")
        if isinstance(stream, random.Random):
            family = "python_random"
        elif isinstance(stream, np.random.Generator):
            family = "numpy_pcg64_generator"
        else:
            raise TypeError(f"unsupported randomness owner: {name}")
        mode = modes.get(name, "runtime")
        if mode not in {"runtime", "detached"}:
            raise ValueError(f"invalid randomness owner mode: {name}")
        owners.append({
            "identity": name,
            "family": family,
            "mode": mode,
            "lifecycle": lifecycle,
        })
    digest = hashlib.sha256(_canonical_json_bytes(owners)).hexdigest()
    return {"schema_version": 1, "owners": owners, "digest": digest}


def validate_randomness_owner_inventory(inventory: object) -> dict[str, Any]:
    """Validate an owner catalog without reading or mutating live streams."""
    if not isinstance(inventory, Mapping):
        return {"valid": False, "errors": ["owner_inventory_not_mapping"]}
    if set(inventory) != {"schema_version", "owners", "digest"}:
        return {"valid": False, "errors": ["owner_inventory_schema_invalid"]}
    if inventory.get("schema_version") != 1 or not isinstance(inventory.get("owners"), list):
        return {"valid": False, "errors": ["owner_inventory_schema_invalid"]}
    errors: list[str] = []
    previous = None
    for index, owner in enumerate(inventory["owners"]):
        if not isinstance(owner, Mapping) or set(owner) != {
            "identity", "family", "mode", "lifecycle"
        }:
            errors.append(f"owner_inventory_entry_{index}_invalid")
            continue
        identity = owner.get("identity")
        if not isinstance(identity, str) or not identity.strip() or identity <= (previous or ""):
            errors.append(f"owner_inventory_identity_{index}_invalid")
        previous = identity if isinstance(identity, str) else previous
        if owner.get("family") not in {"python_random", "numpy_pcg64_generator"}:
            errors.append(f"owner_inventory_family_{index}_invalid")
        if owner.get("mode") not in {"runtime", "detached"}:
            errors.append(f"owner_inventory_mode_{index}_invalid")
        if owner.get("lifecycle") not in {"active", "detached", "retired"}:
            errors.append(f"owner_inventory_lifecycle_{index}_invalid")
    try:
        expected = hashlib.sha256(_canonical_json_bytes(inventory["owners"])).hexdigest()
    except (TypeError, ValueError, OverflowError):
        errors.append("owner_inventory_not_canonical")
    else:
        if inventory.get("digest") != expected:
            errors.append("owner_inventory_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def validate_pond_randomness_owner_graph(
    pond: object, expected_owner: object
) -> dict[str, Any]:
    """Verify that every known PS owner slot points at the Pond owner.

    The inventory is intentionally explicit: an unknown stochastic child is a
    contract failure instead of being silently omitted from checkpoint scope.
    """
    errors: list[str] = []
    if pond is None or getattr(pond, "randomness_rng", None) is not expected_owner:
        errors.append("pond_owner_mismatch")

    def check(owner: object, path: str) -> None:
        if owner is None:
            errors.append(f"{path}_owner_missing")
        elif getattr(owner, "randomness_rng", None) is not expected_owner:
            errors.append(f"{path}_owner_mismatch")

    for name in (
        "floating_system",
        "assembly_system",
        "resource_manager",
        "pvaec_orchestrator",
    ):
        child = getattr(pond, name, None)
        if child is not None:
            check(child, name)
            if name == "pvaec_orchestrator":
                for phase in ("inheritance_system", "mutation_system", "selection_system"):
                    phase_owner = getattr(child, phase, None)
                    if phase_owner is not None:
                        check(phase_owner, f"{name}.{phase}")

    for collection_name in ("floating_components", "organisms", "root_entities"):
        collection = getattr(pond, collection_name, None)
        values = collection.values() if isinstance(collection, Mapping) else collection
        if values is None:
            continue
        for index, entity in enumerate(values):
            path = f"{collection_name}[{index}]"
            if hasattr(entity, "randomness_rng"):
                check(entity, path)
            for child_name in ("components", "scripts"):
                children = getattr(entity, child_name, None)
                if isinstance(children, Mapping):
                    children = children.values()
                if children is not None:
                    for child_index, child in enumerate(children):
                        if hasattr(child, "randomness_rng"):
                            check(child, f"{path}.{child_name}[{child_index}]")
            membrane = getattr(entity, "membrane", None)
            if membrane is not None and hasattr(membrane, "randomness_rng"):
                check(membrane, f"{path}.membrane")
    return {"valid": not errors, "errors": errors}


def validate_sr_script_randomness_owner_graph(
    entities: object, expected_owner: object
) -> dict[str, Any]:
    """Verify that every dynamically attached SR script uses the SR owner."""
    errors: list[str] = []
    if entities is None:
        return {"valid": True, "errors": []}
    for entity_index, entity in enumerate(entities):
        scripts = getattr(entity, "scripts", ())
        if scripts is None:
            continue
        for script_index, script in enumerate(scripts):
            path = f"scene_runtime_entities[{entity_index}].scripts[{script_index}]"
            if getattr(script, "randomness_rng", None) is not expected_owner:
                errors.append(f"{path}_owner_mismatch")
            if expected_owner is not None and hasattr(script, "randomness_owner_mode"):
                if getattr(script, "randomness_owner_mode") != "runtime":
                    errors.append(f"{path}_owner_mode_mismatch")
    return {"valid": not errors, "errors": errors}


def build_sr_script_owner_graph_digest(entities: object) -> str:
    """Digest loaded SR script structure and owner families, excluding state."""
    rows: list[dict[str, Any]] = []
    for entity_index, entity in enumerate(entities or ()):
        for script_index, script in enumerate(getattr(entity, "scripts", ()) or ()):
            owner = getattr(script, "randomness_rng", None)
            if isinstance(owner, random.Random):
                family = "python_random"
            elif isinstance(owner, np.random.Generator):
                family = "numpy_pcg64_generator"
            elif owner is None:
                family = "missing"
            else:
                family = type(owner).__name__
            rows.append({
                "entity_index": entity_index,
                "script_index": script_index,
                "execution_path": (
                    f"scene_runtime_entities[{entity_index}].scripts[{script_index}]"
                ),
                "script_type": f"{type(script).__module__}.{type(script).__qualname__}",
                "owner_family": family,
                "owner_stream_name": "sr.runtime" if owner is not None else None,
                "owner_mode": str(getattr(script, "randomness_owner_mode", "unknown")),
                "lifecycle": "active",
            })
    return hashlib.sha256(_canonical_json_bytes(rows)).hexdigest()


def build_sr_script_execution_receipts(entities: object) -> list[dict[str, Any]]:
    """Capture deterministic script tick/owner cursors for checkpoint restore."""
    receipts: list[dict[str, Any]] = []
    for entity_index, entity in enumerate(entities or ()):
        for script_index, script in enumerate(getattr(entity, "scripts", ()) or ()):
            owner = getattr(script, "randomness_rng", None)
            if isinstance(owner, random.Random):
                family = "python_random"
            elif isinstance(owner, np.random.Generator):
                family = "numpy_pcg64_generator"
            elif owner is None:
                family = "missing"
            else:
                family = type(owner).__name__
            receipts.append({
                "execution_path": f"scene_runtime_entities[{entity_index}].scripts[{script_index}]",
                "owner_stream_name": "sr.runtime" if owner is not None else None,
                "owner_family": family,
                "owner_mode": str(getattr(script, "randomness_owner_mode", "unknown")),
                "lifecycle": "active",
                "execution_ticks": int(getattr(script, "_randomness_execution_ticks", 0)),
                "consumption_count": int(getattr(script, "_randomness_consumption_count", 0)),
            })
    return receipts


def validate_sr_script_execution_receipts(receipts: object) -> dict[str, Any]:
    if not isinstance(receipts, list):
        return {"valid": False, "errors": ["script_execution_receipts_not_list"]}
    errors: list[str] = []
    paths: set[str] = set()
    for index, receipt in enumerate(receipts):
        required = {
            "execution_path", "owner_stream_name", "owner_family", "owner_mode",
            "lifecycle", "execution_ticks", "consumption_count",
        }
        if not isinstance(receipt, Mapping) or set(receipt) != required:
            errors.append(f"script_execution_receipt_{index}_schema_invalid")
            continue
        path = receipt.get("execution_path")
        if not isinstance(path, str) or not path or path in paths:
            errors.append(f"script_execution_receipt_{index}_path_invalid")
        paths.add(path if isinstance(path, str) else "")
        if receipt.get("owner_mode") not in {"runtime", "detached", "unknown"}:
            errors.append(f"script_execution_receipt_{index}_mode_invalid")
        if receipt.get("lifecycle") not in {"active", "detached", "retired"}:
            errors.append(f"script_execution_receipt_{index}_lifecycle_invalid")
        for field in ("execution_ticks", "consumption_count"):
            value = receipt.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"script_execution_receipt_{index}_{field}_invalid")
    return {"valid": not errors, "errors": sorted(set(errors))}


def build_script_evidence_digest(
    audits: object,
    receipts: object,
    trust_denials: object,
    failure_receipts: object,
    declared_paths: object = (),
    inventory: object = (),
    execution_receipts: object = (),
    boundary_receipt: object = None,
) -> str:
    """Bind script source, trust, entropy and failure evidence as one record."""
    return hashlib.sha256(
        _canonical_json_bytes({
            "audits": audits,
            "receipts": receipts,
            "trust_denials": trust_denials,
            "failure_receipts": failure_receipts,
            "declared_paths": declared_paths,
            "inventory": inventory,
            "execution_receipts": execution_receipts,
            "boundary_receipt": boundary_receipt,
        })
    ).hexdigest()


def _capture_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical["capture_digest"] = ""
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def build_worldbridge_rng_checkpoint_state(
    *,
    runtime_epoch: object,
    sr_runtime_rng: random.Random,
    deterministic_context: object | None = None,
    pond_runtime_rng: np.random.Generator | None = None,
    caller_owned_streams: Mapping[str, object] | None = None,
    caller_owned_stream_modes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Capture the supported RNG owners behind one detached checkpoint boundary.

    The result is intentionally incomplete when uncaptured entropy authorities
    remain in the inventory. It is a validated state bundle, not replay or
    default-runtime admission.
    """
    if not isinstance(runtime_epoch, str) or not runtime_epoch.strip():
        raise ValueError("runtime_epoch must be a non-empty string")
    if not isinstance(sr_runtime_rng, random.Random):
        raise TypeError("sr_runtime_rng must be random.Random")
    capture_id = "viewport-rng-" + hashlib.sha256(
        runtime_epoch.encode("utf-8")
    ).hexdigest()[:32]
    process_global = capture_worldbridge_global_random_states(capture_id=capture_id)
    context_snapshot = None
    if deterministic_context is not None:
        snapshot = getattr(deterministic_context, "snapshot", None)
        if not callable(snapshot):
            raise TypeError("deterministic_context must provide snapshot()")
        context_snapshot = copy.deepcopy(snapshot())
        from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
            validate_worldbridge_deterministic_randomness_snapshot,
        )

        validation = validate_worldbridge_deterministic_randomness_snapshot(
            context_snapshot
        )
        if validation != {"valid": True, "errors": []}:
            raise ValueError(
                "invalid deterministic context snapshot: "
                + ", ".join(validation["errors"])
            )
    version, internal_state, gaussian_cache = sr_runtime_rng.getstate()
    state: dict[str, Any] = {
        "schema_version": RNG_CHECKPOINT_SCHEMA_VERSION,
        "checkpoint_kind": RNG_CHECKPOINT_KIND,
        "runtime_epoch": runtime_epoch,
        "sr_runtime": {
            "kind": "sr_runtime_python_random",
            "version": int(version),
            "internal_state": [int(value) for value in internal_state],
            "gaussian_cache": (
                None if gaussian_cache is None else float(gaussian_cache)
            ),
        },
        "process_global": process_global,
        "deterministic_context": context_snapshot,
        "captured_authority_ids": [
            "sr_runtime_random",
            *CAPTURED_AUTHORITY_IDS,
            *( ["named_deterministic_streams"] if context_snapshot is not None else [] ),
        ],
        "uncaptured_authority_ids": list(UNCAPTURED_AUTHORITY_IDS),
        "complete": False,
        "replay_admitted": False,
        "default_ready": False,
        "checkpoint_digest": "",
        "native_boundary_receipt": build_native_entropy_boundary_receipt(),
    }
    if pond_runtime_rng is not None:
        state["pond_runtime"] = _serialize_numpy_generator_state(pond_runtime_rng)
    if caller_owned_streams is not None:
        state["caller_owned_streams"] = _serialize_caller_owned_streams(
            caller_owned_streams
        )
        state["caller_owned_stream_receipt"] = _build_caller_owned_stream_receipt(
            state["caller_owned_streams"], caller_owned_stream_modes
        )
        state["owner_inventory"] = build_randomness_owner_inventory(
            caller_owned_streams, caller_owned_stream_modes
        )
    state["checkpoint_digest"] = _rng_checkpoint_digest(state)
    validation = validate_worldbridge_rng_checkpoint_state(state)
    if validation != {"valid": True, "errors": []}:
        raise RuntimeError(
            "invalid RNG checkpoint state produced: " + ", ".join(validation["errors"])
        )
    return copy.deepcopy(state)


def validate_worldbridge_rng_checkpoint_state(state: object) -> dict[str, Any]:
    """Validate the detached RNG bundle without reading or mutating live RNGs."""
    errors: list[str] = []
    if not isinstance(state, Mapping):
        return {"valid": False, "errors": ["checkpoint_not_mapping"]}
    expected_keys = {
        "schema_version", "checkpoint_kind", "runtime_epoch", "sr_runtime",
        "process_global", "deterministic_context", "captured_authority_ids",
        "uncaptured_authority_ids", "complete", "replay_admitted", "default_ready",
        "checkpoint_digest",
    }
    optional_keys = {
        "pond_runtime",
        "caller_owned_streams",
        "caller_owned_stream_receipt",
        "owner_inventory",
        "native_boundary_receipt",
    }
    if not set(state) >= expected_keys or set(state) - expected_keys - optional_keys:
        errors.append("checkpoint_keys_mismatch")
    if state.get("schema_version") != RNG_CHECKPOINT_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if state.get("checkpoint_kind") != RNG_CHECKPOINT_KIND:
        errors.append("checkpoint_kind_mismatch")
    if not isinstance(state.get("runtime_epoch"), str) or not state.get("runtime_epoch", "").strip():
        errors.append("runtime_epoch_invalid")
    sr = state.get("sr_runtime")
    if not isinstance(sr, Mapping) or sr.get("kind") != "sr_runtime_python_random":
        errors.append("sr_runtime_invalid")
    else:
        try:
            _validate_python_state(
                {
                    "format": "python_random_getstate_v1",
                    "version": sr.get("version"),
                    "internal_state": sr.get("internal_state"),
                    "gaussian_cache": sr.get("gaussian_cache"),
                },
                errors,
            )
        except Exception:
            errors.append("sr_runtime_invalid")
    process_global = state.get("process_global")
    if validate_worldbridge_global_random_state_capture(process_global) != {
        "valid": True,
        "errors": [],
    }:
        errors.append("process_global_invalid")
    context = state.get("deterministic_context")
    if context is not None:
        from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
            validate_worldbridge_deterministic_randomness_snapshot,
        )

        if validate_worldbridge_deterministic_randomness_snapshot(context)["valid"] is not True:
            errors.append("deterministic_context_invalid")
    pond_runtime = state.get("pond_runtime")
    if pond_runtime is not None:
        _validate_numpy_generator_state(pond_runtime, errors)
    caller_owned_streams = state.get("caller_owned_streams")
    if caller_owned_streams is not None:
        _validate_caller_owned_streams(caller_owned_streams, errors)
        receipt = state.get("caller_owned_stream_receipt")
        if receipt is None:
            errors.append("caller_owned_stream_receipt_missing")
        else:
            _validate_caller_owned_stream_receipt(
                receipt, caller_owned_streams, errors
            )
        inventory = state.get("owner_inventory")
        if validate_randomness_owner_inventory(inventory) != {"valid": True, "errors": []}:
            errors.append("owner_inventory_invalid")
    elif "owner_inventory" in state:
        errors.append("owner_inventory_without_streams")
    elif "caller_owned_stream_receipt" in state:
        errors.append("caller_owned_stream_receipt_without_streams")
    native_receipt = state.get("native_boundary_receipt")
    from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
        validate_native_entropy_boundary_receipt,
    )
    if validate_native_entropy_boundary_receipt(native_receipt) != {
        "valid": True,
        "errors": [],
    }:
        errors.append("native_boundary_receipt_invalid")
    if not isinstance(state.get("captured_authority_ids"), list):
        errors.append("captured_authority_ids_invalid")
    if state.get("uncaptured_authority_ids") != list(UNCAPTURED_AUTHORITY_IDS):
        errors.append("uncaptured_authority_ids_mismatch")
    if state.get("complete") is not False:
        errors.append("complete_must_remain_false")
    for field in ("replay_admitted", "default_ready"):
        if state.get(field) is not False:
            errors.append(f"{field}_must_remain_false")
    try:
        expected = _rng_checkpoint_digest(state)
    except (TypeError, ValueError, OverflowError):
        expected = None
        errors.append("checkpoint_not_canonical_json")
    digest = state.get("checkpoint_digest")
    if not _is_sha256(digest):
        errors.append("checkpoint_digest_invalid")
    elif expected != digest:
        errors.append("checkpoint_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def _rng_checkpoint_digest(state: Mapping[str, Any]) -> str:
    payload = dict(state)
    payload["checkpoint_digest"] = ""
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _serialize_numpy_generator_state(stream: object) -> dict[str, Any]:
    if not isinstance(stream, np.random.Generator):
        raise TypeError("pond_runtime_rng must be numpy.random.Generator")
    raw = stream.bit_generator.state
    if raw.get("bit_generator") != "PCG64":
        raise ValueError("pond_runtime_rng must use NumPy PCG64")
    nested = raw.get("state")
    if not isinstance(nested, Mapping):
        raise ValueError("pond_runtime_rng state is invalid")
    return {
        "format": "numpy_generator_pcg64_state_v1",
        "bit_generator": "PCG64",
        "state": {"state": int(nested["state"]), "inc": int(nested["inc"])},
        "has_uint32": int(raw.get("has_uint32", 0)),
        "uinteger": int(raw.get("uinteger", 0)),
    }


def _validate_numpy_generator_state(state: object, errors: list[str]) -> None:
    if not isinstance(state, Mapping):
        errors.append("pond_runtime_invalid")
        return
    if state.get("format") != "numpy_generator_pcg64_state_v1" or state.get("bit_generator") != "PCG64":
        errors.append("pond_runtime_format_invalid")
        return
    nested = state.get("state")
    if not isinstance(nested, Mapping) or set(nested) != {"state", "inc"}:
        errors.append("pond_runtime_state_invalid")
    for field in ("has_uint32", "uinteger"):
        value = state.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"pond_runtime_{field}_invalid")


def _serialize_caller_owned_streams(streams: Mapping[str, object]) -> dict[str, Any]:
    if not isinstance(streams, Mapping):
        raise TypeError("caller_owned_streams must be a mapping")
    serialized: dict[str, Any] = {}
    for name, stream in streams.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("caller-owned stream names must be non-empty strings")
        if isinstance(stream, random.Random):
            version, internal, gaussian = stream.getstate()
            serialized[name] = {
                "family": "python_random",
                "state": {
                    "version": int(version),
                    "internal_state": [int(value) for value in internal],
                    "gaussian_cache": None if gaussian is None else float(gaussian),
                },
            }
        elif isinstance(stream, np.random.Generator):
            serialized[name] = {
                "family": "numpy_pcg64_generator",
                "state": _serialize_numpy_generator_state(stream),
            }
        else:
            raise TypeError(f"unsupported caller-owned stream: {name}")
    return serialized


def _build_caller_owned_stream_receipt(
    streams: Mapping[str, Any], modes: Mapping[str, str] | None
) -> dict[str, Any]:
    if modes is None:
        modes = {}
    if not isinstance(modes, Mapping) or set(modes) - set(streams):
        raise ValueError("caller-owned stream modes must match registered streams")
    entries = []
    for name, entry in streams.items():
        mode = modes.get(name, "runtime")
        if mode not in {"runtime", "detached"}:
            raise ValueError(f"invalid caller-owned stream mode: {name}")
        entries.append({
            "name": str(name),
            "family": str(entry["family"]),
            "mode": mode,
        })
    entries.sort(key=lambda item: item["name"])
    digest = hashlib.sha256(_canonical_json_bytes(entries)).hexdigest()
    return {
        "schema_version": 1,
        "streams": entries,
        "registry_digest": digest,
    }


def build_caller_owned_stream_receipt(
    streams: Mapping[str, object], modes: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Build a versioned mode/family receipt for live caller-owned streams."""
    return _build_caller_owned_stream_receipt(
        _serialize_caller_owned_streams(streams), modes
    )


def _validate_caller_owned_stream_receipt(
    receipt: object, streams: Mapping[str, Any], errors: list[str]
) -> None:
    if not isinstance(receipt, Mapping) or set(receipt) != {
        "schema_version", "streams", "registry_digest"
    } or receipt.get("schema_version") != 1:
        errors.append("caller_owned_stream_receipt_schema_invalid")
        return
    entries = receipt.get("streams")
    if not isinstance(entries, list) or {
        item.get("name") for item in entries if isinstance(item, Mapping)
    } != set(streams):
        errors.append("caller_owned_stream_receipt_streams_mismatch")
        return
    for item in entries:
        if not isinstance(item, Mapping) or set(item) != {"name", "family", "mode"}:
            errors.append("caller_owned_stream_receipt_entry_invalid")
            continue
        stream_entry = streams.get(item.get("name"))
        expected_family = (
            stream_entry.get("family") if isinstance(stream_entry, Mapping) else None
        )
        if item.get("family") != expected_family:
            errors.append("caller_owned_stream_receipt_family_mismatch")
        if item.get("mode") not in {"runtime", "detached"}:
            errors.append("caller_owned_stream_receipt_mode_invalid")
    try:
        expected = hashlib.sha256(_canonical_json_bytes(entries)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        errors.append("caller_owned_stream_receipt_not_canonical")
    else:
        if receipt.get("registry_digest") != expected:
            errors.append("caller_owned_stream_receipt_digest_mismatch")


def _validate_caller_owned_streams(streams: object, errors: list[str]) -> None:
    if not isinstance(streams, Mapping):
        errors.append("caller_owned_streams_invalid")
        return
    for name, entry in streams.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(entry, Mapping):
            errors.append("caller_owned_stream_entry_invalid")
            continue
        family = entry.get("family")
        state = entry.get("state")
        if family == "python_random":
            if not isinstance(state, Mapping):
                errors.append("caller_owned_python_state_invalid")
            else:
                _validate_python_state(
                    {
                        "format": "python_random_getstate_v1",
                        "version": state.get("version"),
                        "internal_state": state.get("internal_state"),
                        "gaussian_cache": state.get("gaussian_cache"),
                    },
                    errors,
                )
        elif family == "numpy_pcg64_generator":
            _validate_numpy_generator_state(state, errors)
        else:
            errors.append("caller_owned_stream_family_invalid")


def restore_worldbridge_caller_owned_streams(
    streams: Mapping[str, object], state: Mapping[str, Any]
) -> None:
    """Restore a named owner registry atomically, preserving stream identity."""
    errors: list[str] = []
    _validate_caller_owned_streams(state, errors)
    if errors:
        raise ValueError("invalid caller-owned stream registry: " + ", ".join(errors))
    if set(streams) != set(state):
        raise RuntimeError("caller-owned stream registration mismatch")
    originals: dict[str, object] = {}
    try:
        for name, stream in streams.items():
            entry = state[name]
            if entry["family"] == "python_random":
                if not isinstance(stream, random.Random):
                    raise TypeError(f"caller-owned stream family mismatch: {name}")
                originals[name] = stream.getstate()
                decoded = (
                    int(entry["state"]["version"]),
                    tuple(int(value) for value in entry["state"]["internal_state"]),
                    entry["state"].get("gaussian_cache"),
                )
                stream.setstate(decoded)
            else:
                if not isinstance(stream, np.random.Generator):
                    raise TypeError(f"caller-owned stream family mismatch: {name}")
                originals[name] = copy.deepcopy(stream.bit_generator.state)
                restore_worldbridge_numpy_generator_state(stream, entry["state"])
    except Exception:
        for name, original in originals.items():
            stream = streams[name]
            if isinstance(stream, random.Random):
                stream.setstate(original)
            else:
                stream.bit_generator.state = original
        raise


def restore_worldbridge_numpy_generator_state(
    stream: np.random.Generator, state: Mapping[str, Any]
) -> None:
    """Restore a caller-owned PCG64 Generator after structural validation."""
    errors: list[str] = []
    _validate_numpy_generator_state(state, errors)
    if errors:
        raise ValueError("invalid Pond randomness state: " + ", ".join(errors))
    target = {
        "bit_generator": "PCG64",
        "state": {
            "state": int(state["state"]["state"]),
            "inc": int(state["state"]["inc"]),
        },
        "has_uint32": int(state["has_uint32"]),
        "uinteger": int(state["uinteger"]),
    }
    original = copy.deepcopy(stream.bit_generator.state)
    try:
        stream.bit_generator.state = target
    except Exception:
        stream.bit_generator.state = original
        raise


def _numpy_raw_states_equal(left: tuple[Any, ...], right: tuple[Any, ...]) -> bool:
    return (
        len(left) == len(right) == 5
        and left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


__all__ = [
    "AUTHORITY_IDS",
    "CAPTURED_AUTHORITY_IDS",
    "CAPTURE_KIND",
    "SCHEMA_VERSION",
    "UNCAPTURED_AUTHORITY_IDS",
    "build_worldbridge_randomness_authority_contract",
    "build_worldbridge_randomness_authority_inventory",
    "build_worldbridge_rng_checkpoint_state",
    "build_caller_owned_stream_registry_digest",
    "build_caller_owned_stream_receipt",
    "build_randomness_owner_inventory",
    "validate_randomness_owner_inventory",
    "validate_pond_randomness_owner_graph",
    "validate_sr_script_randomness_owner_graph",
    "build_sr_script_owner_graph_digest",
    "build_sr_script_execution_receipts",
    "validate_sr_script_execution_receipts",
    "build_script_evidence_digest",
    "capture_worldbridge_global_random_states",
    "restore_worldbridge_global_random_states",
    "restore_worldbridge_numpy_generator_state",
    "restore_worldbridge_caller_owned_streams",
    "validate_worldbridge_rng_checkpoint_state",
    "validate_worldbridge_global_random_state_capture",
]
