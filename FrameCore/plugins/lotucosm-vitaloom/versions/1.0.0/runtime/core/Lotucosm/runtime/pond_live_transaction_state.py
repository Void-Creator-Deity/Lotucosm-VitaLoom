# -*- coding: utf-8
"""Process-local snapshots for compensating a live Pond mutation.

These snapshots preserve existing object identities and are intentionally not
portable save files. Every mutable Python owner reachable from the Pond graph
must be snapshotable; unknown opaque state fails before a caller mutates it.
RNG owners are captured by state while retaining their live identities.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import types
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any

import numpy as np


@dataclass(frozen=True)
class _ObjectState:
    owner: Any
    attributes: Mapping[str, Any]
    slot_names: tuple[str, ...]
    external_attributes: Mapping[str, Any]


@dataclass(frozen=True)
class _ContainerState:
    owner: Any
    kind: str
    content: Any


@dataclass(frozen=True)
class _RandomState:
    owner: Any
    kind: str
    state: Any


@dataclass(frozen=True)
class PondLiveTransactionState:
    """Identity-bound, in-process state captured before a Pond tick."""

    root: Any
    objects: tuple[_ObjectState, ...]
    containers: tuple[_ContainerState, ...]
    random_states: tuple[_RandomState, ...]
    digest: str


def capture_pond_live_transaction_state(pond: Any) -> PondLiveTransactionState:
    if pond is None:
        raise TypeError("Pond owner is required")

    objects: list[Any] = []
    containers: list[Any] = []
    random_owners: list[tuple[Any, str, Any]] = []
    seen: set[int] = set()

    def visit(value: Any) -> None:
        is_container = _is_snapshot_container(value)
        if not is_container and _is_atom(value):
            return
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)

        random_state = _capture_random_state(value)
        if random_state is not None:
            kind, state = random_state
            random_owners.append((value, kind, state))
            return

        if is_container:
            containers.append(value)

        if isinstance(value, Mapping):
            for key in sorted(value, key=_stable_sort_key):
                visit(key)
                visit(value[key])
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
            return
        if isinstance(value, (set, frozenset)):
            for item in sorted(value, key=_stable_sort_key):
                visit(item)
            return
        if isinstance(value, np.ndarray):
            if value.dtype == object:
                for item in value.flat:
                    visit(item)
            return
        if isinstance(value, bytearray):
            return

        attributes, slot_names = _read_object_attributes(value)
        if attributes is None:
            raise TypeError(
                "unsupported opaque Pond runtime owner: "
                f"{type(value).__module__}.{type(value).__qualname__}"
            )
        objects.append(value)
        for name in sorted(attributes):
            # These are authoritative external owner references. The live
            # checkpoint adapter captures them separately and must retain the
            # caller-owned object identity rather than clone its authority.
            if value is pond and name == "randomness_rng":
                continue
            visit(attributes[name])

    visit(pond)

    owner_memo = {id(owner): owner for owner in objects}
    owner_memo.update({id(owner): owner for owner in containers})
    owner_memo.update({id(owner): owner for owner, _, _ in random_owners})
    object_states: list[_ObjectState] = []
    for owner in objects:
        attributes, slot_names = _read_object_attributes(owner)
        assert attributes is not None
        external_attributes: dict[str, Any] = {}
        if owner is pond:
            external_attributes = {
                name: attributes[name]
                for name in ("randomness_rng",)
                if name in attributes
            }
            attributes = {
                name: value
                for name, value in attributes.items()
                if name != "randomness_rng"
            }
        try:
            detached = copy.deepcopy(attributes, owner_memo)
        except Exception as exc:
            raise TypeError(
                "Pond runtime owner state cannot be detached: "
                f"{type(owner).__module__}.{type(owner).__qualname__}"
            ) from exc
        object_states.append(
            _ObjectState(owner, detached, slot_names, external_attributes)
        )

    container_states: list[_ContainerState] = []
    for owner in containers:
        try:
            detached_content = _detach_container(owner, owner_memo)
        except Exception as exc:
            raise TypeError(
                "Pond runtime container state cannot be detached: "
                f"{type(owner).__module__}.{type(owner).__qualname__}"
            ) from exc
        container_states.append(
            _ContainerState(owner, _container_kind(owner), detached_content)
        )

    detached_random_states: list[_RandomState] = []
    for owner, kind, state in random_owners:
        detached_random_states.append(
            _RandomState(owner, kind, copy.deepcopy(state, owner_memo))
        )

    digest = _state_digest(
        tuple(object_states),
        tuple(container_states),
        tuple(detached_random_states),
    )
    return PondLiveTransactionState(
        pond,
        tuple(object_states),
        tuple(container_states),
        tuple(detached_random_states),
        digest,
    )


def restore_pond_live_transaction_state(
    pond: Any, snapshot: PondLiveTransactionState
) -> str:
    if not isinstance(snapshot, PondLiveTransactionState):
        raise TypeError("invalid Pond live transaction snapshot")
    if snapshot.root is not pond:
        raise RuntimeError("Pond live transaction owner root changed")
    if (
        _state_digest(snapshot.objects, snapshot.containers, snapshot.random_states)
        != snapshot.digest
    ):
        raise ValueError("Pond live transaction snapshot digest mismatch")

    owner_memo = _snapshot_owner_memo(snapshot)
    for state in snapshot.containers:
        _restore_container_state(state, owner_memo)
    for state in reversed(snapshot.objects):
        _restore_object_attributes(state, owner_memo)
    for state in snapshot.random_states:
        _restore_random_state(state)

    restored = capture_pond_live_transaction_state(pond)
    if restored.digest != snapshot.digest:
        raise RuntimeError("Pond live transaction restore digest mismatch")
    return restored.digest


def _read_object_attributes(value: Any) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    try:
        attributes = dict(vars(value))
    except TypeError:
        attributes = {}
        if not hasattr(type(value), "__slots__"):
            return None, ()

    slot_names: list[str] = []
    for cls in type(value).__mro__:
        declared = getattr(cls, "__slots__", ())
        if isinstance(declared, str):
            declared = (declared,)
        for name in declared:
            if name in {"__dict__", "__weakref__"}:
                continue
            slot_names.append(name)
            try:
                attributes[name] = getattr(value, name)
            except AttributeError:
                continue
    return attributes, tuple(dict.fromkeys(slot_names))


def _restore_object_attributes(
    state: _ObjectState, owner_memo: dict[int, Any]
) -> None:
    owner = state.owner
    snapshot_attributes = copy.deepcopy(dict(state.attributes), owner_memo)
    try:
        current = vars(owner)
    except TypeError:
        current = None
    if current is not None:
        for name in tuple(current):
            if (
                name not in snapshot_attributes
                and name not in state.slot_names
                and name not in state.external_attributes
            ):
                del current[name]
        for name, value in snapshot_attributes.items():
            if name not in state.slot_names:
                current[name] = _restore_value(current.get(name), value, owner_memo)
        for name, value in state.external_attributes.items():
            current[name] = value
    for name in state.slot_names:
        if name in snapshot_attributes:
            previous = getattr(owner, name, None)
            setattr(owner, name, _restore_value(previous, snapshot_attributes[name], owner_memo))
        else:
            try:
                delattr(owner, name)
            except AttributeError:
                pass


def _restore_value(current: Any, saved: Any, owner_memo: dict[int, Any]) -> Any:
    """Restore a value while preserving identities registered as owners."""
    owner = owner_memo.get(id(saved))
    if owner is not None:
        return owner
    if isinstance(saved, np.ndarray):
        if isinstance(current, np.ndarray) and current.shape == saved.shape and current.dtype == saved.dtype:
            current[...] = saved
            return current
        return copy.deepcopy(saved, owner_memo)
    if _is_snapshot_container(saved):
        raise RuntimeError(
            "Pond mutable container owner is missing from the transaction snapshot: "
            f"{_type_name(saved)}"
        )
    return copy.deepcopy(saved, owner_memo)


def _restore_container_state(
    state: _ContainerState, owner_memo: dict[int, Any]
) -> None:
    """Restore one registered mutable container in place.

    Container owners are restored before object attributes so shared and
    cyclic references inside an object graph resolve to the original live
    containers instead of newly allocated copies.
    """
    owner = state.owner
    if state.kind == "dict":
        if not isinstance(owner, dict):
            raise RuntimeError("Pond live transaction dict owner identity changed")
        owner.clear()
        for key, value in state.content.items():
            owner[_restore_value(None, key, owner_memo)] = _restore_value(
                None, value, owner_memo
            )
        return
    if state.kind == "list":
        if not isinstance(owner, list):
            raise RuntimeError("Pond live transaction list owner identity changed")
        owner[:] = [
            _restore_value(None, value, owner_memo) for value in state.content
        ]
        return
    if state.kind == "set":
        if not isinstance(owner, set):
            raise RuntimeError("Pond live transaction set owner identity changed")
        owner.clear()
        owner.update(
            _restore_value(None, value, owner_memo) for value in state.content
        )
        return
    if state.kind == "bytearray":
        if not isinstance(owner, bytearray):
            raise RuntimeError(
                "Pond live transaction bytearray owner identity changed"
            )
        owner[:] = state.content
        return
    if state.kind == "ndarray":
        if not isinstance(owner, np.ndarray):
            raise RuntimeError("Pond live transaction ndarray owner identity changed")
        _restore_ndarray_in_place(owner, state.content)
        return
    raise RuntimeError(f"unsupported Pond live transaction container: {state.kind}")


def _restore_ndarray_in_place(owner: np.ndarray, content: Any) -> None:
    if owner.shape != content.shape or owner.dtype != content.dtype:
        raise RuntimeError(
            "Pond live transaction ndarray owner shape or dtype changed"
        )
    owner[...] = content


def _snapshot_owner_memo(snapshot: PondLiveTransactionState) -> dict[int, Any]:
    owner_memo = {id(state.owner): state.owner for state in snapshot.objects}
    owner_memo.update({id(state.owner): state.owner for state in snapshot.containers})
    owner_memo.update(
        {id(state.owner): state.owner for state in snapshot.random_states}
    )
    return owner_memo


def _is_snapshot_container(value: Any) -> bool:
    return isinstance(value, (dict, list, set, bytearray, np.ndarray))


def _container_kind(value: Any) -> str:
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    if isinstance(value, set):
        return "set"
    if isinstance(value, bytearray):
        return "bytearray"
    if isinstance(value, np.ndarray):
        return "ndarray"
    raise TypeError(f"unsupported Pond runtime container: {_type_name(value)}")


def _detach_container(value: Any, owner_memo: dict[int, Any]) -> Any:
    kind = _container_kind(value)
    if kind == "dict":
        # Substitute registered owners while detaching everything else, so
        # nested and shared containers retain their transaction identity.
        return copy.deepcopy(dict(value), owner_memo)
    if kind == "list":
        return copy.deepcopy(list(value), owner_memo)
    if kind == "set":
        return copy.deepcopy(set(value), owner_memo)
    if kind == "bytearray":
        return bytes(value)
    if kind == "ndarray":
        if value.dtype == object:
            detached = np.empty(value.shape, dtype=object)
            for index, item in np.ndenumerate(value):
                detached[index] = copy.deepcopy(item, owner_memo)
            return detached
        return value.copy()
    raise TypeError(f"unsupported Pond runtime container: {_type_name(value)}")


def _capture_random_state(value: Any) -> tuple[str, Any] | None:
    if isinstance(value, np.random.Generator):
        return "numpy_generator", copy.deepcopy(value.bit_generator.state)
    if isinstance(value, np.random.RandomState):
        return "numpy_randomstate", copy.deepcopy(value.get_state())
    if isinstance(value, random.Random):
        return "python_random", copy.deepcopy(value.getstate())
    return None


def _restore_random_state(state: _RandomState) -> None:
    if state.kind == "numpy_generator":
        state.owner.bit_generator.state = copy.deepcopy(state.state)
    elif state.kind == "numpy_randomstate":
        state.owner.set_state(copy.deepcopy(state.state))
    elif state.kind == "python_random":
        state.owner.setstate(copy.deepcopy(state.state))
    else:
        raise ValueError("unsupported Pond RNG snapshot kind")


def _is_atom(value: Any) -> bool:
    if value is None or isinstance(value, (str, bytes, bool, int, Decimal, Enum, PurePath)):
        return True
    if isinstance(value, (float, complex, np.generic)):
        return True
    if isinstance(value, (type, types.ModuleType, types.FunctionType, types.BuiltinFunctionType)):
        return True
    if isinstance(value, (types.MethodType, types.BuiltinMethodType, types.CodeType, type(Ellipsis))):
        return True
    return False


def _stable_sort_key(value: Any) -> tuple[str, str, str]:
    kind = f"{type(value).__module__}.{type(value).__qualname__}"
    if isinstance(value, (str, int, float, bool, bytes, Enum)):
        return kind, str(value), ""
    return kind, repr(value), str(id(value))


def _state_digest(
    objects: tuple[_ObjectState, ...],
    containers: tuple[_ContainerState, ...],
    random_states: tuple[_RandomState, ...],
) -> str:
    owner_ids = {id(state.owner): index for index, state in enumerate(objects)}
    container_base = len(objects)
    owner_ids.update(
        {
            id(state.owner): container_base + index
            for index, state in enumerate(containers)
        }
    )
    random_base = container_base + len(containers)
    owner_ids.update(
        {
            id(state.owner): random_base + index
            for index, state in enumerate(random_states)
        }
    )
    next_external_id = random_base + len(random_states)
    for object_state in objects:
        for value in object_state.external_attributes.values():
            if id(value) not in owner_ids:
                owner_ids[id(value)] = next_external_id
                next_external_id += 1
    payload = {
        "objects": [
            {
                "index": index,
                "type": _type_name(state.owner),
                "attributes": _canonical_value(state.attributes, owner_ids),
                "external_attributes": _canonical_value(
                    state.external_attributes, owner_ids
                ),
            }
            for index, state in enumerate(objects)
        ],
        "containers": [
            {
                "index": container_base + index,
                "type": _type_name(state.owner),
                "kind": state.kind,
                "content": _canonical_value(state.content, owner_ids),
            }
            for index, state in enumerate(containers)
        ],
        "random_states": [
            {
                "index": random_base + index,
                "type": _type_name(state.owner),
                "kind": state.kind,
                "state": _canonical_value(state.state, owner_ids),
            }
            for index, state in enumerate(random_states)
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _canonical_value(value: Any, owner_ids: Mapping[int, int]) -> Any:
    owner_index = owner_ids.get(id(value))
    if owner_index is not None:
        return {"owner_ref": owner_index}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return {"float": "nan"}
        if math.isinf(value):
            return {"float": "inf" if value > 0 else "-inf"}
        return {"float": value.hex()}
    if isinstance(value, complex):
        return {"complex": [value.real.hex(), value.imag.hex()]}
    if isinstance(value, Decimal):
        return {"decimal": str(value)}
    if isinstance(value, Enum):
        return {"enum": _type_name(value), "value": _canonical_value(value.value, owner_ids)}
    if isinstance(value, PurePath):
        return {"path": value.as_posix()}
    if isinstance(value, bytes):
        return {"bytes": value.hex()}
    if isinstance(value, bytearray):
        return {"bytearray": bytes(value).hex()}
    if isinstance(value, np.ndarray):
        return {
            "ndarray": {
                "dtype": value.dtype.str,
                "shape": list(value.shape),
                "values": _canonical_value(value.tolist(), owner_ids),
            }
        }
    if isinstance(value, np.generic):
        return {"numpy_scalar": _type_name(value), "value": _canonical_value(value.item(), owner_ids)}
    if isinstance(value, Mapping):
        items = [
            (_canonical_value(key, owner_ids), _canonical_value(item, owner_ids))
            for key, item in value.items()
        ]
        items.sort(key=lambda pair: json.dumps(pair[0], sort_keys=True, ensure_ascii=False))
        return {"mapping": items}
    if isinstance(value, (list, tuple)):
        return {"tuple" if isinstance(value, tuple) else "list": [_canonical_value(item, owner_ids) for item in value]}
    if isinstance(value, (set, frozenset)):
        items = [_canonical_value(item, owner_ids) for item in value]
        items.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return {"frozenset" if isinstance(value, frozenset) else "set": items}
    if isinstance(
        value,
        (
            type,
            types.ModuleType,
            types.FunctionType,
            types.BuiltinFunctionType,
            types.MethodType,
            types.BuiltinMethodType,
            types.CodeType,
            type(Ellipsis),
        ),
    ):
        return {"callable": _type_name(value)}
    if hasattr(value, "__dict__"):
        raise TypeError("Pond owner graph contains an uncaptured mutable object")
    raise TypeError(f"unsupported Pond state value: {_type_name(value)}")


def _type_name(value: Any) -> str:
    cls = value if isinstance(value, type) else type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


__all__ = [
    "PondLiveTransactionState",
    "capture_pond_live_transaction_state",
    "restore_pond_live_transaction_state",
]
