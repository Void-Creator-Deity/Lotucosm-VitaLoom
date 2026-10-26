# -*- coding: utf-8 -*-
"""Qt-free, in-place restore of the deliberately small SR runtime state slice.

This adapter restores only fields emitted by the SR snapshot producer.  It
does not recreate entities, scripts, topology, RNG, scheduler state, or a
cross-lane bridge.  Validation and rollback happen before the caller exposes
the mutation as a checkpoint operation.
"""
from __future__ import annotations

import copy
import json
import math
from collections.abc import Iterable, Mapping
from typing import Any


RESTORABLE_FIELDS = frozenset(
    {
        "position",
        "velocity",
        "acceleration",
        "radius",
        "energy",
        "health",
        "max_energy",
        "max_health",
        "generation",
        "developmental_stage",
        "social_learning_enabled",
        "pinned",
        "membrane_locked",
        "active",
        "visible",
        "memory_genes",
        "render_identity",
    }
)
SCHEMA_VERSION = 1


class SrRuntimeSnapshotRestoreError(ValueError):
    """Raised when a live SR restore cannot be admitted or completed."""


def restore_sr_runtime_snapshot_slice(
    entities: Iterable[Any],
    snapshots: Iterable[Mapping[str, Any]],
    *,
    scene_time: float,
    restore_scene_time: bool = True,
) -> float:
    """Apply a validated snapshot slice atomically and return the new time.

    All entity IDs, values, setter availability, and finite-number constraints
    are checked before the first live object is changed.  If a setter still
    fails unexpectedly, the original slice is restored best-effort and the
    original exception is wrapped with the entity ID.
    """
    entity_list = list(entities)
    entity_by_id: dict[str, Any] = {}
    for entity in entity_list:
        entity_id = _entity_id(entity)
        if entity_id in entity_by_id:
            raise SrRuntimeSnapshotRestoreError(f"duplicate live entity_id: {entity_id}")
        entity_by_id[entity_id] = entity

    snapshot_list = [_validate_snapshot(item) for item in snapshots]
    snapshot_ids = [item["entity_id"] for item in snapshot_list]
    if len(snapshot_ids) != len(set(snapshot_ids)):
        raise SrRuntimeSnapshotRestoreError("duplicate snapshot entity_id")
    unknown = [entity_id for entity_id in snapshot_ids if entity_id not in entity_by_id]
    if unknown:
        raise SrRuntimeSnapshotRestoreError(f"unknown snapshot entity_id: {unknown[0]}")
    next_time = _finite_number(scene_time, "scene_time")

    originals = {
        item["entity_id"]: _capture_entity_state(entity_by_id[item["entity_id"]])
        for item in snapshot_list
    }
    try:
        for item in snapshot_list:
            _apply_entity_state(entity_by_id[item["entity_id"]], item)
    except Exception as exc:
        rollback_errors: list[str] = []
        for entity_id, state in originals.items():
            try:
                _apply_entity_state(entity_by_id[entity_id], state)
            except Exception as rollback_exc:  # pragma: no cover - defensive path
                rollback_errors.append(f"{entity_id}: {rollback_exc}")
        detail = f"; rollback failed: {', '.join(rollback_errors)}" if rollback_errors else ""
        raise SrRuntimeSnapshotRestoreError(
            f"snapshot apply failed for {getattr(exc, 'entity_id', 'unknown')}: {exc}{detail}"
        ) from exc

    return next_time if restore_scene_time else _finite_number(scene_time, "scene_time")


def snapshot_restore_digest(payload: Mapping[str, Any]) -> str:
    """Return a stable digest for a validated, JSON-safe restore envelope."""
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    import hashlib

    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_snapshot(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise SrRuntimeSnapshotRestoreError("snapshot must be a mapping")
    entity_id = raw.get("entity_id")
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise SrRuntimeSnapshotRestoreError("snapshot entity_id must be non-empty")
    if "entity_type" in raw and not isinstance(raw["entity_type"], str):
        raise SrRuntimeSnapshotRestoreError("snapshot entity_type must be a string")
    result = {"entity_id": entity_id.strip()}
    for field in RESTORABLE_FIELDS:
        if field in raw:
            result[field] = copy.deepcopy(raw[field])
    position = result.get("position")
    velocity = result.get("velocity")
    acceleration = result.get("acceleration")
    for field, value in (
        ("position", position),
        ("velocity", velocity),
        ("acceleration", acceleration),
    ):
        if value is not None:
            _finite_vector(value, field)
    if "radius" in result:
        radius = _finite_number(result["radius"], "radius")
        if radius <= 0:
            raise SrRuntimeSnapshotRestoreError("radius must be positive")
        result["radius"] = radius
    if "energy" in result and result["energy"] is not None:
        result["energy"] = _finite_number(result["energy"], "energy")
    for field in ("health", "max_energy", "max_health"):
        if field in result and result[field] is not None:
            result[field] = _finite_number(result[field], field)
            if result[field] < 0.0:
                raise SrRuntimeSnapshotRestoreError(
                    f"{field} must be non-negative"
                )
    if "generation" in result:
        generation = result["generation"]
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise SrRuntimeSnapshotRestoreError("generation must be a non-negative integer")
    if "developmental_stage" in result:
        stage = result["developmental_stage"]
        if isinstance(stage, bool) or not isinstance(stage, int) or stage < 0:
            raise SrRuntimeSnapshotRestoreError(
                "developmental_stage must be a non-negative integer"
            )
    for field in (
        "pinned",
        "membrane_locked",
        "active",
        "visible",
        "social_learning_enabled",
    ):
        if field in result and not isinstance(result[field], bool):
            raise SrRuntimeSnapshotRestoreError(f"{field} must be boolean")
    if "memory_genes" in result:
        _validate_memory_genes(result["memory_genes"])
    if "render_identity" in result:
        _validate_render_identity(result["render_identity"])
    return result


def _capture_entity_state(entity: Any) -> dict[str, Any]:
    state: dict[str, Any] = {"entity_id": _entity_id(entity)}
    render_identity = _capture_render_identity(entity)
    if render_identity is not None:
        state["render_identity"] = render_identity
    for field in (
        "position", "velocity", "acceleration", "radius", "energy",
        "health", "max_energy", "max_health", "generation",
        "developmental_stage", "social_learning_enabled", "pinned",
        "membrane_locked", "active", "visible", "memory_genes",
    ):
        if hasattr(entity, field):
            value = getattr(entity, field)
            if field == "memory_genes":
                from core.Lotucosm.sr_memory_gene_bridge import memory_genes_to_dicts

                if not isinstance(value, list):
                    raise SrRuntimeSnapshotRestoreError("memory_genes must be a list")
                state[field] = memory_genes_to_dicts(value)
            else:
                state[field] = copy.deepcopy(value)
    return state


def _apply_entity_state(entity: Any, state: Mapping[str, Any]) -> None:
    entity_id = _entity_id(entity)
    if "position" in state:
        _call_setter(entity, "set_position", state["position"], entity_id)
    if "velocity" in state:
        _call_setter(entity, "set_velocity", state["velocity"], entity_id)
    if "acceleration" in state:
        _call_setter(entity, "set_acceleration", state["acceleration"], entity_id)
    if "radius" in state:
        setter = getattr(entity, "set_radius", None) or getattr(entity, "set_size", None)
        if not callable(setter):
            raise SrRuntimeSnapshotRestoreError(f"entity {entity_id} has no radius setter")
        setter(state["radius"])
    if "energy" in state and state["energy"] is not None:
        _call_setter(entity, "set_energy", state["energy"], entity_id)
    for field in ("health", "max_energy", "max_health"):
        if field in state and state[field] is not None:
            _call_setter(entity, f"set_{field}", state[field], entity_id)
    if "generation" in state:
        _call_setter(entity, "set_generation", state["generation"], entity_id)
    if "developmental_stage" in state:
        _call_setter(
            entity,
            "set_developmental_stage",
            state["developmental_stage"],
            entity_id,
        )
    if "social_learning_enabled" in state:
        _call_setter(
            entity,
            "set_social_learning_enabled",
            state["social_learning_enabled"],
            entity_id,
        )
    for field in ("pinned", "membrane_locked", "active", "visible"):
        if field in state:
            setattr(entity, field, state[field])
    if "render_identity" in state:
        _apply_render_identity(entity, state["render_identity"], entity_id)
    if "memory_genes" in state:
        from core.Lotucosm.sr_memory_gene_bridge import (
            memory_genes_from_dicts,
            replace_entity_memory_genes,
        )

        replace_entity_memory_genes(
            entity,
            memory_genes_from_dicts(state["memory_genes"]),
        )


def _render_identity_form(visual: Any) -> dict[str, Any] | None:
    """Project a live ``sr_visual`` into the shared render identity form.

    Mirrors the SR snapshot producer: the field is omitted when the entity
    has no visual owner or no finite alpha, so a missing visual is never
    silently materialized by a restore.
    """
    if visual is None:
        return None
    alpha = _finite_number(getattr(visual, "alpha", None), "render_identity.alpha")
    return {
        "flip_x": bool(getattr(visual, "flip_x", False)),
        "alpha": min(1.0, max(0.0, alpha)),
    }


def _capture_render_identity(entity: Any) -> dict[str, Any] | None:
    return _render_identity_form(getattr(entity, "sr_visual", None))


def _validate_render_identity(value: object) -> None:
    if not isinstance(value, Mapping):
        raise SrRuntimeSnapshotRestoreError("render_identity must be a mapping")
    if set(value) != {"flip_x", "alpha"}:
        raise SrRuntimeSnapshotRestoreError(
            "render_identity must contain exactly flip_x and alpha"
        )
    if not isinstance(value["flip_x"], bool):
        raise SrRuntimeSnapshotRestoreError("render_identity.flip_x must be boolean")
    alpha = _finite_number(value["alpha"], "render_identity.alpha")
    if alpha < 0.0 or alpha > 1.0:
        raise SrRuntimeSnapshotRestoreError(
            "render_identity.alpha must be within [0, 1]"
        )


def _apply_render_identity(entity: Any, value: Mapping[str, Any], entity_id: str) -> None:
    visual = getattr(entity, "sr_visual", None)
    if visual is None:
        raise SrRuntimeSnapshotRestoreError(
            f"entity {entity_id} has no sr_visual owner for render_identity"
        )
    visual.flip_x = bool(value["flip_x"])
    visual.alpha = float(value["alpha"])


def _validate_memory_genes(value: object) -> None:
    if not isinstance(value, list):
        raise SrRuntimeSnapshotRestoreError("memory_genes must be a list")
    from core.Lotucosm.sr_memory_gene_bridge import memory_genes_from_dicts

    if any(not isinstance(item, Mapping) for item in value):
        raise SrRuntimeSnapshotRestoreError("memory_genes must contain objects")
    try:
        memory_genes_from_dicts(value)
    except (TypeError, ValueError) as exc:
        raise SrRuntimeSnapshotRestoreError("memory_genes contains invalid values") from exc


def _call_setter(entity: Any, name: str, value: Any, entity_id: str) -> None:
    setter = getattr(entity, name, None)
    if not callable(setter):
        raise SrRuntimeSnapshotRestoreError(f"entity {entity_id} has no {name} setter")
    try:
        setter(value)
    except Exception as exc:
        setattr(exc, "entity_id", entity_id)
        raise


def _entity_id(entity: Any) -> str:
    value = getattr(entity, "id", None)
    if not isinstance(value, str) or not value.strip():
        raise SrRuntimeSnapshotRestoreError("live entity id must be non-empty")
    return value.strip()


def _finite_vector(value: Any, field: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise SrRuntimeSnapshotRestoreError(f"{field} must be a 2-vector")
    return (_finite_number(value[0], f"{field}[0]"), _finite_number(value[1], f"{field}[1]"))


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise SrRuntimeSnapshotRestoreError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SrRuntimeSnapshotRestoreError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise SrRuntimeSnapshotRestoreError(f"{field} must be finite")
    return number


__all__ = [
    "RESTORABLE_FIELDS",
    "SCHEMA_VERSION",
    "SrRuntimeSnapshotRestoreError",
    "snapshot_restore_digest",
    "restore_sr_runtime_snapshot_slice",
]
