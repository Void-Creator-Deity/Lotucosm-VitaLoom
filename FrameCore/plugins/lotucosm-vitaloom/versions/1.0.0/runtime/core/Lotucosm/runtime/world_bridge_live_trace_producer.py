# -*- coding: utf-8 -*-
"""Qt-free live producer for one ordered, non-atomic WorldBridge hand-off.

The producer projects existing SR observation data and the live PS Pond into
JSON checkpoints, then delegates trace sealing to the E215 contract.  It does
not create a shared world model, a common clock, or a replay checkpoint.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from numbers import Integral, Real
from typing import Any

from core.Lotucosm.runtime.world_bridge_dual_lane_trace import (
    build_worldbridge_dual_lane_trace,
    validate_worldbridge_dual_lane_trace,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_live_dual_lane_trace_producer"
BRIDGE_ORGANISM_ATTR = "_world_bridge_organism_id"
CAPTURE_ORDER = (
    "capture_sr_observation_before_bridge_handoff",
    "sync_sr_to_ps",
    "pond_update_fixed_step",
    "capture_ps_pond_after_update_before_display_reflection",
    "sync_ps_to_sr_display",
    "seal_e215_dual_lane_trace",
)
ATOMICITY = "ordered_non_atomic_dual_lane_capture"
DO_NOT_CLAIM = (
    "atomic_sr_ps_checkpoint",
    "shared_sr_ps_clock",
    "cross_track_identity_equivalence",
    "lossless_worldbridge_mapping",
    "full_unified_runtime_replay",
    "unified_pond_default_ready",
)
_AUTHORITY_OWNED_SR_FIELDS = frozenset(("capture_source", "bridged_entities"))
_AUTHORITY_OWNED_PS_FIELDS = frozenset(
    ("capture_source", "tick", "iteration", "population", "bridged_organisms", "retired_bridge_links")
)


def collect_worldbridge_live_entity_links(
    sr_entities: Iterable[Any],
    pond: Any,
) -> list[dict[str, str]]:
    """Resolve current bridge pairs and reject stale or ambiguous live links."""
    entities = list(sr_entities)
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise TypeError("pond.organisms must be a mapping")

    links: list[dict[str, str]] = []
    sr_ids: set[str] = set()
    ps_ids: set[str] = set()
    for index, entity in enumerate(entities):
        raw_ps_id = getattr(entity, BRIDGE_ORGANISM_ATTR, None)
        if raw_ps_id is None or not str(raw_ps_id).strip():
            continue
        sr_id = _required_string(getattr(entity, "id", None), f"sr_entities[{index}].id")
        ps_id = _required_string(raw_ps_id, f"sr_entities[{index}].{BRIDGE_ORGANISM_ATTR}")
        if sr_id in sr_ids:
            raise ValueError(f"duplicate sr_entity_id: {sr_id}")
        if ps_id in ps_ids:
            raise ValueError(f"duplicate ps_organism_id: {ps_id}")
        if organisms.get(ps_id) is None:
            raise ValueError(f"missing ps_organism_id: {ps_id}")
        sr_ids.add(sr_id)
        ps_ids.add(ps_id)
        links.append({"sr_entity_id": sr_id, "ps_organism_id": ps_id})
    return sorted(links, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]))


def capture_worldbridge_sr_checkpoint(
    sr_observation: Mapping[str, Any],
    sr_entities: Iterable[Any],
    entity_links: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Capture the SR observation before any SR-to-PS synchronization."""
    observation = _json_mapping_copy(sr_observation, "sr_observation")
    conflicts = sorted(_AUTHORITY_OWNED_SR_FIELDS.intersection(observation))
    if conflicts:
        raise ValueError(f"sr_observation contains producer-owned fields: {', '.join(conflicts)}")
    _finite_non_negative(observation.get("sim_time", 0.0), "sr_observation.sim_time")
    backend = observation.get("physics_backend")
    if backend is not None:
        if not isinstance(backend, Mapping):
            raise TypeError("sr_observation.physics_backend must be a mapping")
        if backend.get("schema_version") != 1 or not isinstance(
            backend.get("backend_id"), str
        ):
            raise ValueError("sr_observation.physics_backend capability is invalid")

    entities_by_id: dict[str, Any] = {}
    for index, entity in enumerate(sr_entities):
        entity_id = _required_string(getattr(entity, "id", None), f"sr_entities[{index}].id")
        if entity_id in entities_by_id:
            raise ValueError(f"duplicate sr_entity_id: {entity_id}")
        entities_by_id[entity_id] = entity

    projected: list[dict[str, Any]] = []
    retired: list[dict[str, str]] = []
    for index, raw_link in enumerate(entity_links):
        sr_id, ps_id = _link_ids(raw_link, index)
        entity = entities_by_id.get(sr_id)
        if entity is None:
            raise ValueError(f"missing sr_entity_id: {sr_id}")
        actual_ps_id = _required_string(
            getattr(entity, BRIDGE_ORGANISM_ATTR, None),
            f"sr_entity[{sr_id}].{BRIDGE_ORGANISM_ATTR}",
        )
        if actual_ps_id != ps_id:
            raise ValueError(f"stale bridge pair: {sr_id}->{ps_id}")
        projected.append(_project_live_subject(entity, sr_id, "entity_id", ps_id))

    return {
        **observation,
        "capture_source": "sr_observation_before_bridge_handoff",
        "bridged_entities": sorted(projected, key=lambda item: item["entity_id"]),
    }


def capture_worldbridge_ps_checkpoint(
    pond: Any,
    entity_links: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Capture linked PS organisms after Pond.update and before display reflection."""
    organisms = getattr(pond, "organisms", None)
    if not isinstance(organisms, Mapping):
        raise TypeError("pond.organisms must be a mapping")
    tick = _non_negative_int(getattr(pond, "time", None), "pond.time")
    iteration = _non_negative_int(getattr(pond, "iteration", 0), "pond.iteration")

    projected: list[dict[str, Any]] = []
    retired: list[dict[str, str]] = []
    links = list(entity_links)
    for index, raw_link in enumerate(links):
        sr_id, ps_id = _link_ids(raw_link, index)
        organism = organisms.get(ps_id)
        if organism is None:
            retired.append({
                "sr_entity_id": sr_id,
                "ps_organism_id": ps_id,
                "reason": "missing_after_pond_update",
            })
            continue
        projected.append(_project_live_subject(organism, ps_id, "organism_id", sr_id))

    checkpoint = {
        "capture_source": "ps_pond_after_update_before_display_reflection",
        "tick": tick,
        "iteration": iteration,
        "population": len(organisms),
        "bridged_organisms": sorted(projected, key=lambda item: item["organism_id"]),
        "retired_bridge_links": sorted(
            retired, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"])
        ),
    }
    conflicts = _AUTHORITY_OWNED_PS_FIELDS.difference(checkpoint)
    if conflicts:
        raise AssertionError(f"missing producer fields: {sorted(conflicts)}")
    return _json_mapping_copy(checkpoint, "ps_checkpoint")


def build_worldbridge_live_dual_lane_trace(
    sr_checkpoint: Mapping[str, Any],
    ps_checkpoint: Mapping[str, Any],
    *,
    entity_links: Iterable[Mapping[str, Any]],
    observed_sr_delta: Real,
) -> dict[str, Any]:
    """Seal one ordered live hand-off without claiming cross-lane atomicity."""
    delta = _finite_non_negative(observed_sr_delta, "observed_sr_delta")
    links = [_json_mapping_copy(link, f"entity_links[{index}]") for index, link in enumerate(entity_links)]
    trace = build_worldbridge_dual_lane_trace(
        sr_checkpoint,
        ps_checkpoint,
        entity_links=links,
    )
    validation = validate_worldbridge_dual_lane_trace(trace)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "live_capture": True,
        "capture_order": list(CAPTURE_ORDER),
        "atomic_checkpoint": False,
        "atomicity": ATOMICITY,
        "observed_sr_delta": delta,
        "sr_delta_consumed_by_pond": False,
        "determinism_scope": "single_call_order_and_json_projection_only",
        "trace": trace,
        "trace_validation": validation,
        "shared_clock": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    payload["producer_digest"] = _producer_digest(payload)
    return payload


def validate_worldbridge_live_dual_lane_trace(payload: object) -> dict[str, Any]:
    """Validate producer ordering, no-claim invariants, nested trace, and digest."""
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return {"valid": False, "errors": ["payload_must_be_mapping"]}
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    if payload.get("read_only") is not True:
        errors.append("read_only_required")
    if payload.get("live_capture") is not True:
        errors.append("live_capture_required")
    if payload.get("capture_order") != list(CAPTURE_ORDER):
        errors.append("capture_order_mismatch")
    if payload.get("atomic_checkpoint") is not False or payload.get("atomicity") != ATOMICITY:
        errors.append("atomic_checkpoint_not_admitted")
    if payload.get("sr_delta_consumed_by_pond") is not False:
        errors.append("sr_delta_consumption_overclaim")
    if payload.get("determinism_scope") != "single_call_order_and_json_projection_only":
        errors.append("determinism_scope_overclaim")
    for field, error in (
        ("shared_clock", "shared_clock_not_admitted"),
        ("lossless", "lossless_mapping_not_admitted"),
        ("replay_admitted", "unified_replay_not_admitted"),
        ("default_ready", "default_ready_not_admitted"),
    ):
        if payload.get(field) is not False:
            errors.append(error)
    try:
        _finite_non_negative(payload.get("observed_sr_delta"), "observed_sr_delta")
    except (TypeError, ValueError):
        errors.append("observed_sr_delta_invalid")

    trace = payload.get("trace")
    trace_validation = validate_worldbridge_dual_lane_trace(trace)
    if not trace_validation["valid"]:
        errors.append("nested_trace_invalid")
    if payload.get("trace_validation") != trace_validation:
        errors.append("trace_validation_mismatch")
    if isinstance(trace, Mapping):
        lanes = trace.get("lanes")
        sr_checkpoint = None
        ps_checkpoint = None
        if isinstance(lanes, Mapping):
            sr_lane = lanes.get("sr")
            ps_lane = lanes.get("ps")
            if isinstance(sr_lane, Mapping):
                sr_checkpoint = sr_lane.get("checkpoint")
            if isinstance(ps_lane, Mapping):
                ps_checkpoint = ps_lane.get("checkpoint")
        if not isinstance(sr_checkpoint, Mapping) or sr_checkpoint.get("capture_source") != "sr_observation_before_bridge_handoff":
            errors.append("sr_capture_source_mismatch")
        if not isinstance(ps_checkpoint, Mapping) or ps_checkpoint.get("capture_source") != "ps_pond_after_update_before_display_reflection":
            errors.append("ps_capture_source_mismatch")
        link_rows = trace.get("entity_links")
        if isinstance(link_rows, list):
            expected_sr = sorted(
                row.get("sr_entity_id")
                for row in link_rows
                if isinstance(row, Mapping) and isinstance(row.get("sr_entity_id"), str)
            )
            expected_ps = sorted(
                row.get("ps_organism_id")
                for row in link_rows
                if isinstance(row, Mapping) and isinstance(row.get("ps_organism_id"), str)
            )
            actual_sr = _checkpoint_identity_list(sr_checkpoint, "bridged_entities", "entity_id")
            actual_ps = _checkpoint_identity_list(ps_checkpoint, "bridged_organisms", "organism_id")
            retired = ps_checkpoint.get("retired_bridge_links", []) if isinstance(ps_checkpoint, Mapping) else []
            retired_ps = sorted(
                row.get("ps_organism_id") for row in retired
                if isinstance(row, Mapping) and isinstance(row.get("ps_organism_id"), str)
            )
            if actual_sr != expected_sr:
                errors.append("sr_checkpoint_link_set_mismatch")
            if sorted(actual_ps + retired_ps) != expected_ps:
                errors.append("ps_checkpoint_link_set_mismatch")
    if payload.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")

    digest = payload.get("producer_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        errors.append("producer_digest_invalid")
    try:
        expected = _producer_digest(payload)
    except (TypeError, ValueError):
        errors.append("payload_not_json_safe")
    else:
        if digest != expected:
            errors.append("producer_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_live_trace_producer_contract() -> dict[str, Any]:
    """Return deterministic status evidence without constructing live objects."""
    payload = build_worldbridge_live_dual_lane_trace(
        {
            "sim_time": 0.05,
            "population": 1,
            "capture_source": "sr_observation_before_bridge_handoff",
            "bridged_entities": [
                {"entity_id": "sr:sample", "linked_id": "ps:sample", "position": [1.0, 2.0]}
            ],
        },
        {
            "capture_source": "ps_pond_after_update_before_display_reflection",
            "tick": 1,
            "iteration": 0,
            "population": 1,
            "bridged_organisms": [
                {"organism_id": "ps:sample", "linked_id": "sr:sample", "position": [1.5, 2.5]}
            ],
        },
        entity_links=[{"sr_entity_id": "sr:sample", "ps_organism_id": "ps:sample"}],
        observed_sr_delta=0.05,
    )
    validation = validate_worldbridge_live_dual_lane_trace(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "worldbridge_live_trace_producer_contract",
        "read_only": True,
        "contract_valid": bool(validation["valid"]),
        "producer": payload,
        "validation": validation,
        "atomic_checkpoint": False,
        "tick_merge_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "do_not_claim": list(DO_NOT_CLAIM),
    }


def _checkpoint_identity_list(
    checkpoint: object,
    collection_field: str,
    identity_field: str,
) -> list[str] | None:
    if not isinstance(checkpoint, Mapping):
        return None
    rows = checkpoint.get(collection_field)
    if not isinstance(rows, list):
        return None
    identities: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            return None
        identity = row.get(identity_field)
        if not isinstance(identity, str) or not identity.strip():
            return None
        identities.append(identity.strip())
    return sorted(identities)


def _link_ids(raw_link: Mapping[str, Any], index: int) -> tuple[str, str]:
    if not isinstance(raw_link, Mapping):
        raise TypeError(f"entity_links[{index}] must be a mapping")
    return (
        _required_string(raw_link.get("sr_entity_id"), f"entity_links[{index}].sr_entity_id"),
        _required_string(raw_link.get("ps_organism_id"), f"entity_links[{index}].ps_organism_id"),
    )


def _project_live_subject(subject: Any, identity: str, identity_field: str, linked_id: str) -> dict[str, Any]:
    from core.Lotucosm.sr_memory_gene_bridge import memory_genes_to_dicts

    raw_memory_genes = getattr(subject, "sr_memory_genes", None)
    if raw_memory_genes is None:
        raw_memory_genes = getattr(subject, "memory_genes", [])
    if not isinstance(raw_memory_genes, list):
        raise TypeError(f"{identity_field} memory_genes must be a list")
    return {
        identity_field: identity,
        "linked_id": linked_id,
        "position": _vector2_or_none(getattr(subject, "position", None)),
        "velocity": _vector2_or_none(getattr(subject, "velocity", None)),
        "acceleration": _vector2_or_none(getattr(subject, "acceleration", None)),
        "radius": _finite_or_none(getattr(subject, "radius", None)),
        "size": _finite_or_none(getattr(subject, "size", None)),
        "energy": _finite_or_none(getattr(subject, "energy", None)),
        "health": _finite_or_none(getattr(subject, "health", None)),
        "max_energy": _finite_or_none(getattr(subject, "max_energy", None)),
        "max_health": _finite_or_none(getattr(subject, "max_health", None)),
        "generation": _optional_non_negative_int(getattr(subject, "generation", None)),
        "memory_genes": memory_genes_to_dicts(raw_memory_genes),
    }


def _vector2_or_none(value: object) -> list[float] | None:
    if value is None:
        return None
    try:
        raw = (value[0], value[1])  # type: ignore[index]
    except (TypeError, IndexError, KeyError):
        if hasattr(value, "x") and hasattr(value, "y"):
            raw = (getattr(value, "x"), getattr(value, "y"))
        else:
            return None
    projected = [_finite_or_none(raw[0]), _finite_or_none(raw[1])]
    return projected if all(item is not None for item in projected) else None


def _finite_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _optional_non_negative_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return _non_negative_int(value, "generation")
    except (TypeError, ValueError):
        return None


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{field} must be a non-negative integer")
    result = int(value)
    if result < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return result


def _finite_non_negative(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{field} must be finite and non-negative")
    return result


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _json_mapping_copy(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    try:
        encoded = json.dumps(dict(value), ensure_ascii=False, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field} must contain only finite JSON values") from exc
    copied = json.loads(encoded)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must encode to an object")
    return copied


def _producer_digest(payload: Mapping[str, Any]) -> str:
    canonical = dict(payload)
    canonical.pop("producer_digest", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "build_worldbridge_live_dual_lane_trace",
    "build_worldbridge_live_trace_producer_contract",
    "capture_worldbridge_ps_checkpoint",
    "capture_worldbridge_sr_checkpoint",
    "collect_worldbridge_live_entity_links",
    "validate_worldbridge_live_dual_lane_trace",
]
