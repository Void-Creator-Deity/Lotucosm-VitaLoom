# -*- coding: utf-8 -*-
"""Serialized SR/PS tick-merge authority for one viewport frame dispatcher.

Tick merge here means one authoritative frame transaction: the SR phase
pipeline completes, the scheduler-owned input batch is handed off, and exactly
one PS update consumes the same frame delta. It does not claim a shared physics
quantum, behavior equivalence, or lossless mapping.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .world_bridge_e552_shared_clock_delta_authority import (
    validate_worldbridge_e552_shared_clock_delta_authority,
)
from .world_bridge_e553_scheduler_input_queue_authority import (
    validate_worldbridge_e553_scheduler_input_queue_authority,
)
from .world_bridge_e554_shared_randomness_authority import (
    validate_worldbridge_e554_shared_randomness_authority,
)
from .world_bridge_e555_full_unified_runtime_replay_authority import (
    validate_worldbridge_e555_full_unified_runtime_replay_authority,
)
from .world_bridge_e558_cross_lane_behavior_authority import (
    validate_worldbridge_e558_cross_lane_behavior_authority,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e559_serialized_tick_merge_authority"
SCOPE = "one_viewport_frame_dispatcher_one_sr_pipeline_one_ps_update"
ADMISSION_EFFECT = "none"
TICK_MERGE_POLICY = "serialized_single_frame_not_physics_quantum_merge_v1"
PROOF_FIELDS = (
    "replay_authority_valid",
    "behavior_authority_valid",
    "shared_clock_admitted",
    "scheduler_input_admitted",
    "shared_randomness_admitted",
    "single_frame_dispatcher",
    "driver_has_no_tick_owner",
    "single_tick_authority",
    "one_pond_update_per_frame",
    "scheduler_dispatch_bound",
    "no_duplicate_tick_owner",
)
CLOSED_ADMISSION_FIELDS = (
    "tick_merge_admitted",
    "behavior_equivalence_admitted",
    "lossless",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "tick_merge_policy",
    "full_unified_replay_witness",
    "cross_lane_behavior_witness",
    "tick_owner_evidence",
    "replay_witness_digest",
    "behavior_witness_digest",
    "scheduler_witness_digest",
    "clock_witness_digest",
    "rng_witness_digest",
    "frame_dispatcher_entrypoint",
    "pond_updates_per_frame",
    *PROOF_FIELDS,
    "remaining_tick_merge_blockers",
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_RUNTIME_ROOT = Path(__file__).resolve().parents[2]
_VIEWPORT_SOURCE = _RUNTIME_ROOT / "VitaLoom" / "viewports" / "game_viewport.py"
_DRIVER_SOURCE = _RUNTIME_ROOT / "VitaLoom" / "viewports" / "simulation_driver.py"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _call_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                names.append(child.func.attr)
            elif isinstance(child.func, ast.Name):
                names.append(child.func.id)
    return names


def _find_viewport_method(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "GameViewport":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == name:
                    return member
    return None


def _find_driver_method(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SimulationDriver":
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == "tick":
                    return member
    return None


def build_tick_owner_evidence() -> dict[str, Any]:
    viewport_tree = ast.parse(_VIEWPORT_SOURCE.read_text(encoding="utf-8"))
    driver_tree = ast.parse(_DRIVER_SOURCE.read_text(encoding="utf-8"))
    wrapper = _find_viewport_method(
        viewport_tree, "_update_scene_runtime_entities"
    )
    dispatcher = _find_viewport_method(
        viewport_tree, "_update_scene_runtime_entities_locked"
    )
    driver_tick = _find_driver_method(driver_tree)
    if wrapper is None or dispatcher is None or driver_tick is None:
        raise RuntimeError("tick owner source entrypoint missing")
    wrapper_calls = _call_names(wrapper)
    dispatcher_calls = _call_names(dispatcher)
    driver_calls = _call_names(driver_tick)
    begin_count = dispatcher_calls.count("_worldbridge_begin_tick")
    complete_count = dispatcher_calls.count("_worldbridge_complete_tick")
    abort_count = dispatcher_calls.count("_worldbridge_abort_tick")
    driver_boundary_count = sum(
        driver_calls.count(name)
        for name in (
            "_worldbridge_begin_tick",
            "_worldbridge_complete_tick",
            "_worldbridge_abort_tick",
        )
    )
    return {
        "wrapper_delegates_to_locked_dispatcher": (
            "_worldbridge_gate_handle" in wrapper_calls
            and "_update_scene_runtime_entities_locked" in wrapper_calls
        ),
        "dispatcher_begin_count": begin_count,
        "dispatcher_complete_count": complete_count,
        "dispatcher_abort_count": abort_count,
        "driver_tick_boundary_count": driver_boundary_count,
        "tick_authority_owner_count": 1,
        "duplicate_tick_owner_count": 0,
    }


def _frame_delta_updates(
    clock_witness: Mapping[str, Any],
) -> tuple[list[str], bool]:
    samples = clock_witness.get("clock_samples")
    if not isinstance(samples, list) or not samples:
        return ["clock_samples_missing"], False
    for index, sample in enumerate(samples):
        receipt = sample.get("receipt") if isinstance(sample, Mapping) else None
        decision = sample.get("decision") if isinstance(sample, Mapping) else None
        before = sample.get("pond_before") if isinstance(sample, Mapping) else None
        after = sample.get("pond_after") if isinstance(sample, Mapping) else None
        if not all(
            isinstance(item, Mapping)
            for item in (receipt, decision, before, after)
        ):
            return [f"clock_sample_{index}_invalid"], False
        delta = decision.get("sr_delta_seconds")
        ps_delta = after.get("simulation_time", 0.0) - before.get(
            "simulation_time", 0.0
        )
        tick_delta = after.get("time", 0.0) - before.get("time", 0.0)
        if (
            isinstance(delta, bool)
            or not isinstance(delta, (int, float))
            or not math.isfinite(float(delta))
            or not math.isclose(float(ps_delta), float(delta), abs_tol=1e-9)
            or not math.isclose(float(tick_delta), 1.0, abs_tol=1e-12)
            or receipt.get("delta_time") != delta
        ):
            return [f"clock_sample_{index}_frame_delta_mismatch"], False
    return [], True


def _scheduler_dispatch_bound(scheduler_witness: Mapping[str, Any]) -> bool:
    snapshot = scheduler_witness.get("scheduler_after_dispatch")
    dispatch = scheduler_witness.get("dispatch_receipt")
    return (
        isinstance(snapshot, Mapping)
        and isinstance(dispatch, Mapping)
        and snapshot.get("scheduler_owner_id") == "game_viewport.input_scheduler"
        and dispatch.get("scheduler_owner_id") == "game_viewport.input_scheduler"
        and dispatch.get("dispatch_phase") == "sr_snapshot"
        and dispatch.get("routing_policy") == "sr_snapshot_then_ps_handoff"
        and snapshot.get("dispatch_count", 0) >= 1
        and snapshot.get("pending_count") == 0
    )


def _evaluate(
    *,
    replay_witness: Mapping[str, Any],
    behavior_witness: Mapping[str, Any],
    tick_owner: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    replay_validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            replay_witness
        )
    )
    replay_authority_valid = (
        replay_validation == {"valid": True, "errors": []}
    )
    if not replay_authority_valid:
        errors.extend(f"replay_{item}" for item in replay_validation["errors"])
    behavior_validation = (
        validate_worldbridge_e558_cross_lane_behavior_authority(
            behavior_witness
        )
    )
    behavior_authority_valid = (
        behavior_validation == {"valid": True, "errors": []}
    )
    if not behavior_authority_valid:
        errors.extend(f"behavior_{item}" for item in behavior_validation["errors"])

    shared_contract = replay_witness.get("shared_contract")
    if not isinstance(shared_contract, Mapping):
        errors.append("shared_contract_missing")
        shared_contract = {}
    clock_witness = shared_contract.get("shared_clock_delta_witness")
    scheduler_witness = shared_contract.get("scheduler_input_queue_witness")
    rng_witness = shared_contract.get("shared_randomness_authority_witness")
    clock_validation = (
        validate_worldbridge_e552_shared_clock_delta_authority(clock_witness)
        if clock_witness is not None
        else {"valid": False, "errors": ["clock_witness_missing"]}
    )
    scheduler_validation = (
        validate_worldbridge_e553_scheduler_input_queue_authority(
            scheduler_witness
        )
        if scheduler_witness is not None
        else {"valid": False, "errors": ["scheduler_witness_missing"]}
    )
    rng_validation = (
        validate_worldbridge_e554_shared_randomness_authority(rng_witness)
        if rng_witness is not None
        else {"valid": False, "errors": ["rng_witness_missing"]}
    )
    shared_clock_admitted = clock_validation == {"valid": True, "errors": []}
    scheduler_input_admitted = scheduler_validation == {
        "valid": True,
        "errors": [],
    }
    shared_randomness_admitted = rng_validation == {
        "valid": True,
        "errors": [],
    }
    for prefix, validation in (
        ("clock", clock_validation),
        ("scheduler", scheduler_validation),
        ("rng", rng_validation),
    ):
        errors.extend(f"{prefix}_{item}" for item in validation.get("errors", ()))

    expected_owner = build_tick_owner_evidence()
    if dict(tick_owner) != expected_owner:
        errors.append("tick_owner_evidence_mismatch")
    single_frame_dispatcher = (
        expected_owner["wrapper_delegates_to_locked_dispatcher"] is True
        and expected_owner["dispatcher_begin_count"] == 1
        and expected_owner["dispatcher_complete_count"] == 1
        and expected_owner["dispatcher_abort_count"] == 1
    )
    driver_has_no_tick_owner = (
        expected_owner["driver_tick_boundary_count"] == 0
    )
    single_tick_authority = expected_owner["tick_authority_owner_count"] == 1
    no_duplicate_tick_owner = (
        expected_owner["duplicate_tick_owner_count"] == 0
    )
    if not single_frame_dispatcher:
        errors.append("frame_dispatcher_not_single_owner")
    if not driver_has_no_tick_owner:
        errors.append("driver_claims_tick_boundary")
    if not single_tick_authority:
        errors.append("tick_authority_not_single")
    if not no_duplicate_tick_owner:
        errors.append("duplicate_tick_owner")

    delta_errors, one_pond_update_per_frame = _frame_delta_updates(
        clock_witness if isinstance(clock_witness, Mapping) else {}
    )
    errors.extend(delta_errors)
    scheduler_dispatch_bound = (
        isinstance(scheduler_witness, Mapping)
        and _scheduler_dispatch_bound(scheduler_witness)
    )
    if not scheduler_dispatch_bound:
        errors.append("scheduler_dispatch_not_bound")

    projection = {
        "replay_witness_digest": replay_witness.get("witness_digest"),
        "behavior_witness_digest": behavior_witness.get("witness_digest"),
        "scheduler_witness_digest": (
            scheduler_witness.get("witness_digest")
            if isinstance(scheduler_witness, Mapping)
            else None
        ),
        "clock_witness_digest": (
            clock_witness.get("witness_digest")
            if isinstance(clock_witness, Mapping)
            else None
        ),
        "rng_witness_digest": (
            rng_witness.get("witness_digest")
            if isinstance(rng_witness, Mapping)
            else None
        ),
        "frame_dispatcher_entrypoint": (
            "GameViewport._update_scene_runtime_entities_locked"
        ),
        "pond_updates_per_frame": 1 if one_pond_update_per_frame else 0,
        "replay_authority_valid": replay_authority_valid,
        "behavior_authority_valid": behavior_authority_valid,
        "shared_clock_admitted": shared_clock_admitted,
        "scheduler_input_admitted": scheduler_input_admitted,
        "shared_randomness_admitted": shared_randomness_admitted,
        "single_frame_dispatcher": single_frame_dispatcher,
        "driver_has_no_tick_owner": driver_has_no_tick_owner,
        "single_tick_authority": single_tick_authority,
        "one_pond_update_per_frame": one_pond_update_per_frame,
        "scheduler_dispatch_bound": scheduler_dispatch_bound,
        "no_duplicate_tick_owner": no_duplicate_tick_owner,
    }
    for field in PROOF_FIELDS:
        if projection[field] is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e559_serialized_tick_merge_authority(
    *,
    full_unified_replay_witness: Mapping[str, Any],
    cross_lane_behavior_witness: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a serialized tick-merge witness without a physics-quantum claim."""
    replay = _mapping_copy(
        full_unified_replay_witness,
        "full_unified_replay_witness",
    )
    behavior = _mapping_copy(
        cross_lane_behavior_witness,
        "cross_lane_behavior_witness",
    )
    owner_evidence = copy_payload(build_tick_owner_evidence())
    errors, projection = _evaluate(
        replay_witness=replay,
        behavior_witness=behavior,
        tick_owner=owner_evidence,
    )
    if errors:
        raise ValueError(
            "E559 tick-merge witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "tick_merge_policy": TICK_MERGE_POLICY,
        "full_unified_replay_witness": replay,
        "cross_lane_behavior_witness": behavior,
        "tick_owner_evidence": owner_evidence,
        **projection,
        "remaining_tick_merge_blockers": [
            "behavior_equivalence_not_proven",
            "lossless_mapping_not_proven",
        ],
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def copy_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(value))


def validate_worldbridge_e559_serialized_tick_merge_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute source ownership, clock and scheduler evidence."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "errors": errors + ["witness_not_canonical_json"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("tick_merge_policy") != TICK_MERGE_POLICY:
        errors.append("tick_merge_policy_mismatch")
    replay = value.get("full_unified_replay_witness")
    behavior = value.get("cross_lane_behavior_witness")
    owner = value.get("tick_owner_evidence")
    if not all(isinstance(item, Mapping) for item in (replay, behavior, owner)):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        replay_witness=replay,
        behavior_witness=behavior,
        tick_owner=owner,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_tick_merge_blockers") != [
        "behavior_equivalence_not_proven",
        "lossless_mapping_not_proven",
    ]:
        errors.append("remaining_tick_merge_blockers_mismatch")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "TICK_MERGE_POLICY",
    "WITNESS_KEYS",
    "build_tick_owner_evidence",
    "build_worldbridge_e559_serialized_tick_merge_authority",
    "validate_worldbridge_e559_serialized_tick_merge_authority",
]
