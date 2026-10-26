# -*- coding: utf-8 -*-
"""Qt-free adapter for the reviewed live SR/PS shared-field slice.

The mapper owns field normalization, transfer ordering, and owner-API
selection. It does not own canonical SR or PS state, advance either runtime,
or admit replay/lossless behavior. Each lane remains responsible for applying
values through its own mutation API.
"""
from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from typing import Any, Callable

from .world_bridge_mutation_authority import WORLD_BRIDGE_LIVE_MAPPER_PATHS


def _read_xy(subject: Any) -> tuple[float, float] | None:
    position = getattr(subject, "position", None)
    if position is None:
        return None
    try:
        if hasattr(position, "x") and hasattr(position, "y"):
            return float(position.x), float(position.y)
        return float(position[0]), float(position[1])
    except (TypeError, ValueError, IndexError):
        return None


def _write_xy(subject: Any, x: float, y: float) -> bool:
    setter = getattr(subject, "set_position", None)
    if callable(setter):
        setter((float(x), float(y)))
        return True
    position = getattr(subject, "position", None)
    if position is None:
        return False
    try:
        if hasattr(position, "x") and hasattr(position, "y"):
            position.x = float(x)
            position.y = float(y)
            return True
        position[0] = float(x)
        position[1] = float(y)
        return True
    except (TypeError, ValueError, IndexError):
        return False


def _finite_vector2(subject: Any, attribute: str) -> tuple[float, float] | None:
    """Return a detached finite numeric 2-vector or ``None``."""
    raw = getattr(subject, attribute, None)
    if raw is None:
        return None
    try:
        values = (raw[0], raw[1])
    except (TypeError, IndexError, KeyError):
        return None
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
        return None
    vector = (float(values[0]), float(values[1]))
    return vector if all(math.isfinite(value) for value in vector) else None


def _has_writable_vector2(subject: Any, attribute: str) -> bool:
    """Check whether the destination exposes a usable owner write seam."""
    if callable(getattr(subject, "restore_motion_state", None)):
        return True
    if callable(getattr(subject, f"set_{attribute}", None)):
        return True
    raw = getattr(subject, attribute, None)
    if raw is None:
        return False
    if attribute == "position" and hasattr(raw, "x") and hasattr(raw, "y"):
        return True
    # Lists and ndarray-like values expose item assignment.  Immutable tuples
    # remain readable compatibility inputs but are not live mutation owners.
    return hasattr(raw, "__setitem__") and not isinstance(raw, (tuple, str, bytes))


def _write_vector2(subject: Any, attribute: str, vector: tuple[float, float]) -> bool:
    """Copy a validated 2-vector through its owner API with legacy fallback."""
    setter = getattr(subject, f"set_{attribute}", None)
    if callable(setter):
        setter(vector)
        return True
    target = getattr(subject, attribute, None)
    if target is None:
        return False
    try:
        target[0] = vector[0]
        target[1] = vector[1]
    except (TypeError, IndexError, KeyError, ValueError):
        return False
    return True


def _copy_memory_genes(source: Any, target: Any) -> bool:
    """Copy lane-owned memory-gene values without sharing mutable instances."""
    from core.Lotucosm.sr_memory_gene_bridge import (
        memory_genes_from_dicts,
        memory_genes_to_dicts,
    )

    source_is_sr = hasattr(source, "sr_memory_genes")
    source_attr = "sr_memory_genes" if source_is_sr else "memory_genes"
    target_attr = "memory_genes" if source_is_sr else "sr_memory_genes"
    raw = getattr(source, source_attr, None)
    if raw is None or not isinstance(raw, list):
        return False
    genes = memory_genes_from_dicts(memory_genes_to_dicts(raw))
    replace = getattr(target, "replace_memory_genes", None)
    if target_attr == "sr_memory_genes":
        from core.Lotucosm.sr_memory_gene_bridge import replace_entity_memory_genes

        replace_entity_memory_genes(target, genes)
    elif callable(replace):
        replace(genes)
    else:
        setattr(target, target_attr, genes)
    return True


def _read_size_radius(subject: Any) -> tuple[float, float]:
    raw_size = getattr(subject, "size", getattr(subject, "radius", 10.0))
    try:
        size = float(raw_size or 10.0)
    except (TypeError, ValueError):
        size = 10.0
    raw_radius = getattr(subject, "radius", size)
    try:
        radius = float(raw_radius or size)
    except (TypeError, ValueError):
        radius = size
    return size, radius


@dataclass(frozen=True)
class OrganismCreationSeed:
    """Detached lane-owned values used once when an SR entity is bridged."""

    position: tuple[float, float]
    energy: float
    max_energy: float
    health: float
    max_health: float
    size: float
    radius: float
    active: bool
    velocity: tuple[float, float] | None
    acceleration: tuple[float, float] | None

    def kinematic_kwargs(self) -> dict[str, tuple[float, float]]:
        return {
            name: value
            for name, value in (
                ("velocity", self.velocity),
                ("acceleration", self.acceleration),
            )
            if value is not None
        }


class InvalidOrganismCreationSeed(ValueError):
    """Raised when the minimum SR-owned data needed to create a PS owner is absent."""


class WorldBridgeFieldBatchError(RuntimeError):
    """A field batch failure with an explicit same-owner compensation result."""

    def __init__(
        self,
        direction: str,
        cause: BaseException,
        rollback_errors: tuple[str, ...],
        *,
        failed_field: str,
        phase: str,
        mutation_started: bool,
    ) -> None:
        self.direction = direction
        self.cause = cause
        self.rollback_errors = rollback_errors
        self.rollback_complete = not rollback_errors
        self.failed_field = failed_field
        self.phase = phase
        self.mutation_started = mutation_started
        self.rollback_attempted = mutation_started
        super().__init__(
            f"WorldBridge {direction} field batch {phase} failed at {failed_field}: {cause}; "
            f"rollback_attempted={self.rollback_attempted}; "
            f"rollback_complete={self.rollback_complete}; "
            f"rollback_errors={rollback_errors!r}"
        )


@dataclass(frozen=True)
class _FieldBatchOperation:
    name: str
    capture: Callable[[], Any]
    apply: Callable[[], None]
    restore: Callable[[Any], None]


@dataclass(frozen=True)
class _MemoryGeneStoreSnapshot:
    present: bool
    value: Any
    is_sequence: bool = False


@dataclass(frozen=True)
class _AttributeSnapshot:
    present: bool
    value: Any


@dataclass(frozen=True)
class _DebugHudSnapshot:
    present: bool
    original_value: Any
    was_mapping: bool
    key_values: tuple[tuple[str, bool, Any], ...]


def _run_field_batch(
    direction: str,
    operations: list[_FieldBatchOperation],
) -> None:
    """Capture one destination owner, apply fields, and compensate on failure."""
    captured: dict[str, Any] = {}
    for operation in operations:
        try:
            captured[operation.name] = operation.capture()
        except Exception as exc:
            raise WorldBridgeFieldBatchError(
                direction,
                exc,
                (),
                failed_field=operation.name,
                phase="capture",
                mutation_started=False,
            ) from exc

    attempted: list[_FieldBatchOperation] = []
    for operation in operations:
        attempted.append(operation)
        try:
            operation.apply()
        except Exception as exc:
            rollback_errors: list[str] = []
            for prior in reversed(attempted):
                try:
                    prior.restore(captured[prior.name])
                except Exception as rollback_exc:
                    rollback_errors.append(
                        f"{prior.name}: {type(rollback_exc).__name__}: {rollback_exc}"
                    )
            raise WorldBridgeFieldBatchError(
                direction,
                exc,
                tuple(rollback_errors),
                failed_field=operation.name,
                phase="apply",
                mutation_started=True,
            ) from exc


def _optional_owner_value(owner: Any, attribute: str) -> tuple[bool, Any]:
    try:
        return True, getattr(owner, attribute)
    except AttributeError:
        return False, None


def _capture_motion_state(owner: Any) -> dict[str, tuple[float, float] | None]:
    state: dict[str, tuple[float, float] | None] = {}
    for attribute in ("position", "velocity", "acceleration"):
        present, _ = _optional_owner_value(owner, attribute)
        if not present:
            state[attribute] = None
            continue
        if not _has_writable_vector2(owner, attribute):
            raise ValueError(f"destination {attribute} has no writable owner API")
        if attribute == "position":
            value = _read_xy(owner)
            if value is None or not all(math.isfinite(item) for item in value):
                raise ValueError("destination position cannot be captured for compensation")
        else:
            value = _finite_vector2(owner, attribute)
            if value is None:
                raise ValueError(f"destination {attribute} cannot be captured for compensation")
        state[attribute] = value
    return state


def _capture_vector_attribute(owner: Any, attribute: str) -> tuple[float, float] | None:
    present, _ = _optional_owner_value(owner, attribute)
    if not present:
        return None
    value = _read_xy(owner) if attribute == "position" else _finite_vector2(owner, attribute)
    if value is None or not all(math.isfinite(item) for item in value):
        raise ValueError(f"destination {attribute} cannot be captured for compensation")
    return value


def _restore_vector(owner: Any, attribute: str, value: tuple[float, float] | None) -> None:
    present, _ = _optional_owner_value(owner, attribute)
    if value is None:
        if present:
            delattr(owner, attribute)
        return

    setter = getattr(owner, f"set_{attribute}", None)
    if callable(setter):
        setter(value)
    elif attribute == "position":
        if not _write_xy(owner, value[0], value[1]):
            raise RuntimeError(f"owner API did not expose writable {attribute}")
    elif not _write_vector2(owner, attribute, value):
        raise RuntimeError(f"owner API did not expose writable {attribute}")

    current = _read_xy(owner) if attribute == "position" else _finite_vector2(owner, attribute)
    if current != value:
        raise RuntimeError(f"owner API did not restore {attribute}")


def _restore_vector_fields(owner: Any, state: Mapping[str, tuple[float, float] | None]) -> None:
    errors: list[str] = []
    for attribute in ("position", "velocity", "acceleration"):
        if attribute not in state:
            continue
        try:
            _restore_vector(owner, attribute, state[attribute])
        except Exception as exc:
            errors.append(f"{attribute}: {type(exc).__name__}: {exc}")
    if errors:
        raise RuntimeError("vector compensation failed: " + "; ".join(errors))


def _verify_vector_state(owner: Any, state: Mapping[str, tuple[float, float] | None]) -> None:
    for attribute, expected in state.items():
        present, _ = _optional_owner_value(owner, attribute)
        if expected is None:
            if present:
                raise RuntimeError(f"owner API did not restore absent {attribute}")
            continue
        actual = _read_xy(owner) if attribute == "position" else _finite_vector2(owner, attribute)
        if actual != expected:
            raise RuntimeError(f"owner API did not restore {attribute}")


def _restore_motion_state(owner: Any, state: Mapping[str, tuple[float, float] | None]) -> None:
    restore = getattr(owner, "restore_motion_state", None)
    if callable(restore) and all(state.get(name) is not None for name in ("position", "velocity", "acceleration")):
        try:
            restore(
                position=state["position"],
                velocity=state["velocity"],
                acceleration=state["acceleration"],
            )
            _verify_vector_state(owner, state)
            return
        except Exception:
            # A batch-style owner API may itself fail after partially writing.
            # Retry through its field setters before declaring compensation lost.
            pass

    _restore_vector_fields(owner, state)
    _verify_vector_state(owner, state)


def _capture_gene_store(owner: Any, attribute: str) -> _MemoryGeneStoreSnapshot:
    present, value = _optional_owner_value(owner, attribute)
    if not present:
        return _MemoryGeneStoreSnapshot(False, None)
    if isinstance(value, list):
        # The gene objects are immutable to this mapper; retaining their
        # identities lets owner replacement restore the exact pre-batch items.
        return _MemoryGeneStoreSnapshot(True, tuple(value), is_sequence=True)
    return _MemoryGeneStoreSnapshot(True, value)


def _restore_gene_store(
    owner: Any,
    attribute: str,
    snapshot: _MemoryGeneStoreSnapshot,
) -> None:
    if not snapshot.present:
        if attribute == "sr_memory_genes":
            from core.Lotucosm.sr_memory_gene_bridge import clear_entity_memory_genes

            clear_entity_memory_genes(owner)
        else:
            present, _ = _optional_owner_value(owner, attribute)
            if present:
                delattr(owner, attribute)
        if hasattr(owner, attribute):
            raise RuntimeError(f"owner API did not restore absent {attribute}")
        return

    if snapshot.is_sequence:
        values = list(snapshot.value)
        if attribute == "sr_memory_genes":
            from core.Lotucosm.sr_memory_gene_bridge import replace_entity_memory_genes

            replace_entity_memory_genes(owner, values)
        else:
            replace = getattr(owner, "replace_memory_genes", None)
            if callable(replace):
                replace(values)
            else:
                setattr(owner, attribute, values)
        restored = getattr(owner, attribute, None)
        if not isinstance(restored, list) or len(restored) != len(values):
            raise RuntimeError(f"owner API did not restore {attribute}")
        if any(actual is not expected for actual, expected in zip(restored, values)):
            raise RuntimeError(f"owner API changed values while restoring {attribute}")
        return

    setattr(owner, attribute, snapshot.value)
    if getattr(owner, attribute, None) is not snapshot.value:
        raise RuntimeError(f"owner API did not restore {attribute}")


def _capture_finite_scalar(owner: Any, attribute: str) -> float | None:
    present, raw = _optional_owner_value(owner, attribute)
    if not present:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"destination {attribute} cannot be captured for compensation") from exc
    if not math.isfinite(value):
        raise ValueError(f"destination {attribute} must be finite for compensation")
    return value


def _restore_scalar(
    owner: Any,
    attribute: str,
    setter_name: str,
    value: float | _AttributeSnapshot | None,
) -> None:
    if isinstance(value, _AttributeSnapshot):
        if not value.present:
            present, _ = _optional_owner_value(owner, attribute)
            if present:
                delattr(owner, attribute)
            if hasattr(owner, attribute):
                raise RuntimeError(f"owner API did not restore absent {attribute}")
            return
        if value.value is None:
            setattr(owner, attribute, None)
            if getattr(owner, attribute, None) is not None:
                raise RuntimeError(f"owner API did not restore {attribute}")
            return
        value = value.value
    if value is None:
        present, _ = _optional_owner_value(owner, attribute)
        if present:
            delattr(owner, attribute)
        return
    try:
        normalized_value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeError(f"cannot compensate {attribute} with a non-numeric value") from exc
    setter = getattr(owner, setter_name, None)
    setter(normalized_value) if callable(setter) else setattr(owner, attribute, normalized_value)
    try:
        restored = float(getattr(owner, attribute))
    except (TypeError, ValueError, AttributeError) as exc:
        raise RuntimeError(f"owner API did not restore {attribute}") from exc
    if not math.isfinite(restored) or restored != normalized_value:
        raise RuntimeError(f"owner API did not restore {attribute}")


def _capture_attribute(owner: Any, attribute: str) -> _AttributeSnapshot:
    present, value = _optional_owner_value(owner, attribute)
    return _AttributeSnapshot(present, copy.deepcopy(value) if present else None)


def _restore_attribute(owner: Any, attribute: str, snapshot: _AttributeSnapshot) -> None:
    present, _ = _optional_owner_value(owner, attribute)
    if snapshot.present:
        setattr(owner, attribute, copy.deepcopy(snapshot.value))
    elif present:
        delattr(owner, attribute)
    restored_present, restored = _optional_owner_value(owner, attribute)
    if restored_present != snapshot.present:
        raise RuntimeError(f"owner API did not restore {attribute} presence")
    if snapshot.present and restored != snapshot.value:
        raise RuntimeError(f"owner API did not restore {attribute}")


def _capture_size_radius_fields(
    owner: Any,
    attributes: tuple[str, ...],
) -> dict[str, _AttributeSnapshot]:
    return {
        attribute: _capture_attribute(owner, attribute)
        for attribute in attributes
    }


def _restore_size_radius(
    owner: Any,
    state: Mapping[str, _AttributeSnapshot],
) -> None:
    errors: list[str] = []
    if "size" in state:
        try:
            _restore_scalar(owner, "size", "set_size", state["size"])
        except Exception as exc:
            errors.append(f"size: {type(exc).__name__}: {exc}")
    # set_size may also update radius, so restore radius after size.
    if "radius" in state:
        try:
            _restore_scalar(owner, "radius", "set_radius", state["radius"])
        except Exception as exc:
            errors.append(f"radius: {type(exc).__name__}: {exc}")
    if errors:
        raise RuntimeError("size/radius compensation failed: " + "; ".join(errors))


def _capture_debug_hud(owner: Any) -> _DebugHudSnapshot:
    present, value = _optional_owner_value(owner, "sr_debug_hud")
    if not isinstance(value, dict):
        return _DebugHudSnapshot(present, value, False, ())
    keys = ("bridge_sync", "developmental_stage")
    return _DebugHudSnapshot(
        True,
        copy.deepcopy(value),
        True,
        tuple((key, key in value, value.get(key)) for key in keys),
    )


def _restore_debug_hud(owner: Any, snapshot: _DebugHudSnapshot) -> None:
    if not snapshot.was_mapping:
        present, _ = _optional_owner_value(owner, "sr_debug_hud")
        if snapshot.present:
            setattr(owner, "sr_debug_hud", snapshot.original_value)
        elif present:
            delattr(owner, "sr_debug_hud")
        restored_present, restored = _optional_owner_value(owner, "sr_debug_hud")
        if restored_present != snapshot.present or (
            snapshot.present and restored is not snapshot.original_value
        ):
            raise RuntimeError("owner API did not restore sr_debug_hud")
        return
    restored_value = copy.deepcopy(snapshot.original_value)
    setattr(owner, "sr_debug_hud", restored_value)
    for key, present, value in snapshot.key_values:
        if present:
            restored_value[key] = value
        else:
            restored_value.pop(key, None)
    for key, was_present, expected in snapshot.key_values:
        if (key in restored_value) != was_present:
            raise RuntimeError(f"owner API did not restore sr_debug_hud.{key}")
        if was_present and restored_value[key] != expected:
            raise RuntimeError(f"owner API did not restore sr_debug_hud.{key}")


def _finite_source_scalar(source: Any, attribute: str) -> float | None:
    if not hasattr(source, attribute):
        return None
    try:
        value = float(getattr(source, attribute))
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def _gene_copy_operation(source: Any, target: Any) -> _FieldBatchOperation | None:
    source_is_sr = hasattr(source, "sr_memory_genes")
    source_attribute = "sr_memory_genes" if source_is_sr else "memory_genes"
    destination_attribute = "memory_genes" if source_is_sr else "sr_memory_genes"
    raw = getattr(source, source_attribute, None)
    if not isinstance(raw, list):
        return None
    return _FieldBatchOperation(
        "memory_genes",
        lambda: _capture_gene_store(target, destination_attribute),
        lambda: _copy_memory_genes(source, target),
        lambda snapshot: _restore_gene_store(target, destination_attribute, snapshot),
    )


def _source_motion_values(source: Any, fallback: Any) -> dict[str, tuple[float, float]] | None:
    position = _read_xy(source)
    if position is None or not all(math.isfinite(value) for value in position):
        return None
    vectors: dict[str, tuple[float, float]] = {}
    for attribute in ("velocity", "acceleration"):
        candidate = _finite_vector2(source, attribute)
        if candidate is None:
            candidate = _finite_vector2(fallback, attribute) or (0.0, 0.0)
        vectors[attribute] = candidate
    return {
        "position": position,
        "velocity": vectors["velocity"],
        "acceleration": vectors["acceleration"],
    }


def _apply_motion_values(target: Any, values: Mapping[str, tuple[float, float]]) -> None:
    restore = getattr(target, "restore_motion_state", None)
    if callable(restore):
        restore(
            position=values["position"],
            velocity=values["velocity"],
            acceleration=values["acceleration"],
        )
        return
    _write_xy(target, *values["position"])
    for attribute in ("velocity", "acceleration"):
        _write_vector2(target, attribute, values[attribute])


def _vector_transfer_operation(
    source: Any,
    target: Any,
    attribute: str,
) -> _FieldBatchOperation | None:
    value = _read_xy(source) if attribute == "position" else _finite_vector2(source, attribute)
    if (
        value is None
        or not all(math.isfinite(item) for item in value)
        or not _has_writable_vector2(target, attribute)
    ):
        return None
    setter = getattr(target, f"set_{attribute}", None)
    current = getattr(target, attribute, None)
    if not callable(setter) and current is None:
        return None

    def apply() -> None:
        if attribute == "position":
            if not _write_xy(target, *value):
                raise RuntimeError("owner API did not expose writable position")
        elif not _write_vector2(target, attribute, value):
            raise RuntimeError(f"owner API did not expose writable {attribute}")

    return _FieldBatchOperation(
        attribute,
        lambda: _capture_vector_attribute(target, attribute),
        apply,
        lambda snapshot: _restore_vector(target, attribute, snapshot),
    )


def _apply_vector_values(target: Any, values: Mapping[str, tuple[float, float]]) -> None:
    for attribute, value in values.items():
        if not _write_vector2(target, attribute, value):
            raise RuntimeError(f"owner API did not expose writable {attribute}")


def _scalar_transfer_operation(
    source: Any,
    target: Any,
    attribute: str,
    setter_name: str,
) -> _FieldBatchOperation | None:
    value = _finite_source_scalar(source, attribute)
    if value is None or not hasattr(target, attribute):
        return None

    def apply() -> None:
        setter = getattr(target, setter_name, None)
        setter(value) if callable(setter) else setattr(target, attribute, value)

    return _FieldBatchOperation(
        attribute,
        lambda: _capture_attribute(target, attribute),
        apply,
        lambda snapshot: _restore_scalar(target, attribute, setter_name, snapshot),
    )


def build_organism_creation_seed(entity: Any) -> OrganismCreationSeed:
    """Read the explicit creation-only SR fields without mutating either lane."""
    position = _read_xy(entity)
    if position is None:
        raise InvalidOrganismCreationSeed("entity position is unavailable")
    size, radius = _read_size_radius(entity)
    energy = float(getattr(entity, "energy", 100.0) or 100.0)
    return OrganismCreationSeed(
        position=position,
        energy=energy,
        max_energy=float(getattr(entity, "max_energy", 200.0) or 200.0),
        health=float(getattr(entity, "health", energy) or energy),
        max_health=float(getattr(entity, "max_health", 100.0) or 100.0),
        size=size,
        radius=radius,
        active=bool(getattr(entity, "active", True)),
        velocity=_finite_vector2(entity, "velocity"),
        acceleration=_finite_vector2(entity, "acceleration"),
    )


def developmental_profile_from_spawn_request(req: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the explicit one-time developmental/social spawn profile."""
    out: dict[str, Any] = {}
    scripts = req.get("scripts")
    if not isinstance(scripts, list):
        return out
    for script_data in scripts:
        if not isinstance(script_data, dict):
            continue
        props = script_data.get("properties")
        if not isinstance(props, dict):
            continue
        if isinstance(props.get("developmental"), dict):
            out["developmental"] = dict(props["developmental"])
        if isinstance(props.get("social"), dict):
            out["social"] = dict(props["social"])
        if out:
            break
    return out


class WorldBridgeFieldMapper:
    """Apply reviewed field transfers through the destination lane owner."""

    __slots__ = ()

    def sync_sr_to_ps(self, entity: Any, organism: Any) -> None:
        """Apply the pre-Pond SR-to-PS transfer without copying capacities."""
        operations: list[_FieldBatchOperation] = []
        motion = _source_motion_values(entity, organism)
        if motion is not None:
            operations.append(_FieldBatchOperation(
                "motion_state",
                lambda: _capture_motion_state(organism),
                lambda: _apply_motion_values(organism, motion),
                lambda snapshot: _restore_motion_state(organism, snapshot),
            ))

        gene_operation = _gene_copy_operation(entity, organism)
        if gene_operation is not None:
            operations.append(gene_operation)

        if hasattr(entity, "active") and hasattr(organism, "active"):
            active = bool(getattr(entity, "active"))
            operations.append(_FieldBatchOperation(
                "active",
                lambda: _capture_attribute(organism, "active"),
                lambda: setattr(organism, "active", active),
                lambda snapshot: _restore_attribute(organism, "active", snapshot),
            ))
        for attribute, setter_name in (("energy", "set_energy"), ("health", "set_health")):
            if not hasattr(organism, attribute) or not hasattr(entity, attribute):
                continue
            value = _finite_source_scalar(entity, attribute)
            if value is None:
                continue

            def apply_scalar(
                target: Any = organism,
                field: str = attribute,
                setter_name: str = setter_name,
                field_value: float = value,
            ) -> None:
                setter = getattr(target, setter_name, None)
                setter(field_value) if callable(setter) else setattr(target, field, field_value)

            operations.append(_FieldBatchOperation(
                attribute,
                lambda target=organism, field=attribute: _capture_finite_scalar(target, field),
                apply_scalar,
                lambda snapshot, target=organism, field=attribute, setter=setter_name:
                    _restore_scalar(target, field, setter, snapshot),
            ))

        _run_field_batch("sr_to_ps", operations)

    def sync_ps_to_sr(self, organism: Any, entity: Any) -> None:
        """Reflect post-Pond state through SR setters; visibility stays local."""
        operations: list[_FieldBatchOperation] = []
        gene_operation = _gene_copy_operation(organism, entity)
        if gene_operation is not None:
            operations.append(gene_operation)

        position_operation = _vector_transfer_operation(organism, entity, "position")
        if position_operation is not None:
            operations.append(position_operation)

        if hasattr(entity, "active") and hasattr(organism, "active"):
            active = bool(getattr(organism, "active"))
            operations.append(_FieldBatchOperation(
                "active",
                lambda: _capture_attribute(entity, "active"),
                lambda: setattr(entity, "active", active),
                lambda snapshot: _restore_attribute(entity, "active", snapshot),
            ))

        for attribute, setter_name in (("energy", "set_energy"), ("health", "set_health")):
            operation = _scalar_transfer_operation(organism, entity, attribute, setter_name)
            if operation is not None:
                operations.append(operation)

        source_size = _finite_source_scalar(organism, "size")
        source_radius = _finite_source_scalar(organism, "radius")
        set_size = callable(getattr(entity, "set_size", None))
        set_radius = callable(getattr(entity, "set_radius", None))
        has_size = hasattr(entity, "size")
        has_radius = hasattr(entity, "radius")
        should_copy_size = source_size is not None and (set_size or has_size)
        should_copy_radius = source_radius is not None and has_radius and hasattr(organism, "radius")
        if should_copy_size or should_copy_radius:
            size_radius_fields = tuple(
                attribute
                for attribute, should_copy in (
                    ("size", should_copy_size),
                    ("radius", should_copy_radius or (should_copy_size and set_size)),
                )
                if should_copy
            )

            def apply_size_radius() -> None:
                if should_copy_size:
                    setter = getattr(entity, "set_size", None)
                    setter(source_size) if callable(setter) else setattr(entity, "size", source_size)
                if should_copy_radius:
                    setter = getattr(entity, "set_radius", None)
                    setter(source_radius) if callable(setter) else setattr(entity, "radius", source_radius)

            operations.append(_FieldBatchOperation(
                "size_radius",
                lambda: _capture_size_radius_fields(entity, size_radius_fields),
                apply_size_radius,
                lambda snapshot: _restore_size_radius(entity, snapshot),
            ))

        vector_values = {
            attribute: value
            for attribute in ("velocity", "acceleration")
            if (value := _finite_vector2(organism, attribute)) is not None
            and _has_writable_vector2(entity, attribute)
        }
        if vector_values:
            operations.append(_FieldBatchOperation(
                "velocity_acceleration",
                lambda: {
                    attribute: _capture_vector_attribute(entity, attribute)
                    for attribute in vector_values
                },
                lambda: _apply_vector_values(entity, vector_values),
                lambda snapshot: _restore_motion_state(
                    entity,
                    snapshot,
                ),
            ))

        operations.append(_FieldBatchOperation(
            "debug_hud",
            lambda: _capture_debug_hud(entity),
            lambda: self._update_debug_hud(organism, entity),
            lambda snapshot: _restore_debug_hud(entity, snapshot),
        ))

        _run_field_batch("ps_to_sr", operations)

    @staticmethod
    def copy_creation_memory_genes(entity: Any, organism: Any) -> bool:
        """Apply the optional SR-owned gene seed using detached value copies."""
        return _copy_memory_genes(entity, organism)

    @staticmethod
    def apply_spawn_profile(profile: Mapping[str, Any], organism: Any) -> None:
        """Apply one-time profile fields at PS organism creation only."""
        developmental = profile.get("developmental")
        if isinstance(developmental, dict):
            from core.Lotucosm.ps_developmental import apply_developmental_profile_to_organism

            apply_developmental_profile_to_organism(organism, developmental)
        social = profile.get("social")
        if isinstance(social, dict) and "enabled" in social:
            organism.social_learning_enabled = bool(social.get("enabled"))

    @staticmethod
    def _update_debug_hud(organism: Any, entity: Any) -> None:
        hud = getattr(entity, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
        hud["bridge_sync"] = 1
        if hasattr(organism, "developmental_stage"):
            hud["developmental_stage"] = int(getattr(organism, "developmental_stage", 0))
        entity.sr_debug_hud = hud


DEFAULT_WORLD_BRIDGE_FIELD_MAPPER = WorldBridgeFieldMapper()


def sync_sr_entity_to_organism(entity: Any, organism: Any) -> None:
    """Compatibility entry point for the SR-owned pre-update transfer."""
    DEFAULT_WORLD_BRIDGE_FIELD_MAPPER.sync_sr_to_ps(entity, organism)


def sync_organism_to_sr_display(organism: Any, entity: Any) -> None:
    """Compatibility entry point for the PS-owned post-update reflection."""
    DEFAULT_WORLD_BRIDGE_FIELD_MAPPER.sync_ps_to_sr(organism, entity)


__all__ = [
    "DEFAULT_WORLD_BRIDGE_FIELD_MAPPER",
    "InvalidOrganismCreationSeed",
    "OrganismCreationSeed",
    "WORLD_BRIDGE_LIVE_MAPPER_PATHS",
    "WorldBridgeFieldBatchError",
    "WorldBridgeFieldMapper",
    "developmental_profile_from_spawn_request",
    "build_organism_creation_seed",
    "sync_organism_to_sr_display",
    "sync_sr_entity_to_organism",
]
