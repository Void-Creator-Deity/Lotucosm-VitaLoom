# -*- coding: utf-8 -*-
"""Opt-in deterministic, caller-owned named RNG streams for future experiments."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
from collections.abc import Mapping
from typing import Any

import numpy as np


SCHEMA_VERSION = 1
CONTEXT_KIND = "worldbridge_deterministic_randomness_context"
DERIVATION_VERSION = "sha256_named_stream_v1"
MAX_STREAMS = 64
_CONTEXT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_STREAM_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
_SUPPORTED_FAMILIES = ("python_random", "numpy_pcg64_generator")

_SNAPSHOT_KEYS = {
    "schema_version",
    "context_kind",
    "context_id",
    "read_only",
    "derivation_version",
    "root_seed_encoding",
    "root_seed_digest",
    "root_seed_material_revealed",
    "max_streams",
    "stream_count",
    "streams",
    "global_python_random_touched",
    "global_numpy_random_touched",
    "restore_performed",
    "replay_input",
    "checkpoint_state",
    "replay_admitted",
    "default_ready",
    "snapshot_digest",
}

_STREAM_KEYS = {
    "stream_name",
    "family",
    "registration_index",
    "derivation_version",
    "derivation_digest",
    "state",
}

_PYTHON_STATE_KEYS = {"format", "version", "internal_state", "gaussian_cache"}
_NUMPY_STATE_KEYS = {
    "format",
    "bit_generator",
    "state",
    "has_uint32",
    "uinteger",
}


class WorldBridgeDeterministicRandomnessContext:
    """Caller-owned local stream registry; it never owns module-global RNGs."""

    __slots__ = (
        "context_id",
        "root_seed_encoding",
        "root_seed_digest",
        "_root_seed_bytes",
        "_streams",
    )

    def __init__(
        self,
        *,
        context_id: str,
        root_seed_encoding: str,
        root_seed_digest: str,
        root_seed_bytes: bytes,
    ) -> None:
        self.context_id = context_id
        self.root_seed_encoding = root_seed_encoding
        self.root_seed_digest = root_seed_digest
        self._root_seed_bytes = root_seed_bytes
        self._streams: dict[str, tuple[str, object, str]] = {}

    @property
    def stream_names(self) -> tuple[str, ...]:
        return tuple(self._streams)

    def get_stream(self, stream_name: str) -> object:
        clean_name = _clean_stream_name(stream_name)
        try:
            return self._streams[clean_name][1]
        except KeyError as exc:
            raise KeyError(f"unregistered deterministic stream: {clean_name}") from exc

    def snapshot(self) -> dict[str, Any]:
        return snapshot_worldbridge_deterministic_randomness_context(self)


def create_worldbridge_deterministic_randomness_context(
    context_id: str,
    root_seed: str | bytes | int,
) -> WorldBridgeDeterministicRandomnessContext:
    """Create an explicit context from caller-provided seed material only."""
    clean_id = _clean_context_id(context_id)
    seed_encoding, seed_bytes = _normalize_root_seed(root_seed)
    return WorldBridgeDeterministicRandomnessContext(
        context_id=clean_id,
        root_seed_encoding=seed_encoding,
        root_seed_digest=hashlib.sha256(seed_bytes).hexdigest(),
        root_seed_bytes=seed_bytes,
    )


def register_worldbridge_deterministic_random_stream(
    context: WorldBridgeDeterministicRandomnessContext,
    stream_name: str,
    family: str,
    *,
    stream: object | None = None,
) -> object:
    """Register one stable local stream or an existing caller-owned stream."""
    if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
        raise TypeError("context must be a WorldBridgeDeterministicRandomnessContext")
    clean_name = _clean_stream_name(stream_name)
    if family not in _SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported deterministic stream family: {family!r}")
    if clean_name in context._streams:
        raise ValueError(f"deterministic stream already registered: {clean_name}")
    if len(context._streams) >= MAX_STREAMS:
        raise ValueError(f"deterministic stream capacity exceeded: {MAX_STREAMS}")

    derivation_digest = _derive_stream_digest(
        context._root_seed_bytes,
        clean_name,
        family,
    )
    seed_int = int.from_bytes(bytes.fromhex(derivation_digest)[:16], "big")
    if stream is None:
        if family == "python_random":
            stream = random.Random(seed_int)
        else:
            stream = np.random.Generator(np.random.PCG64(seed_int))
    elif family == "python_random":
        if not isinstance(stream, random.Random):
            raise TypeError("python_random stream must be random.Random")
    elif family == "numpy_pcg64_generator":
        if not isinstance(stream, np.random.Generator):
            raise TypeError("numpy_pcg64_generator stream must be numpy.random.Generator")
        if stream.bit_generator.__class__.__name__ != "PCG64":
            raise ValueError("numpy stream must use PCG64")
    context._streams[clean_name] = (
        family,
        stream,
        derivation_digest,
    )
    return stream


def snapshot_worldbridge_deterministic_randomness_context(
    context: WorldBridgeDeterministicRandomnessContext,
) -> dict[str, Any]:
    """Capture all registered local stream states without touching global RNGs."""
    if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
        raise TypeError("context must be a WorldBridgeDeterministicRandomnessContext")
    streams: list[dict[str, Any]] = []
    for registration_index, (stream_name, (family, stream, derivation_digest)) in enumerate(
        context._streams.items()
    ):
        if family == "python_random":
            state = _serialize_python_state(stream.getstate())
        elif family == "numpy_pcg64_generator":
            state = _serialize_numpy_generator_state(stream)
        else:
            raise RuntimeError(f"unsupported registered stream family: {family!r}")
        streams.append(
            {
                "stream_name": stream_name,
                "family": family,
                "registration_index": registration_index,
                "derivation_version": DERIVATION_VERSION,
                "derivation_digest": derivation_digest,
                "state": state,
            }
        )

    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "context_kind": CONTEXT_KIND,
        "context_id": context.context_id,
        "read_only": True,
        "derivation_version": DERIVATION_VERSION,
        "root_seed_encoding": context.root_seed_encoding,
        "root_seed_digest": context.root_seed_digest,
        "root_seed_material_revealed": False,
        "max_streams": MAX_STREAMS,
        "stream_count": len(streams),
        "streams": streams,
        "global_python_random_touched": False,
        "global_numpy_random_touched": False,
        "restore_performed": False,
        "replay_input": False,
        "checkpoint_state": False,
        "replay_admitted": False,
        "default_ready": False,
        "snapshot_digest": "",
    }
    snapshot["snapshot_digest"] = _snapshot_digest(snapshot)
    validation = validate_worldbridge_deterministic_randomness_snapshot(snapshot)
    if validation != {"valid": True, "errors": []}:
        raise RuntimeError(f"invalid deterministic context snapshot: {validation['errors']}")
    return copy.deepcopy(snapshot)


def restore_worldbridge_deterministic_randomness_context(
    context: WorldBridgeDeterministicRandomnessContext,
    snapshot: Mapping[str, Any],
) -> None:
    """Restore registered local stream states atomically.

    The target context must have the same registrations in the same order;
    this prevents a snapshot from silently changing stream ownership. Global
    Python and NumPy RNGs are never touched.
    """
    if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
        raise TypeError("context must be a WorldBridgeDeterministicRandomnessContext")
    validation = validate_worldbridge_deterministic_randomness_snapshot(snapshot)
    if validation != {"valid": True, "errors": []}:
        raise ValueError(f"invalid deterministic context snapshot: {validation['errors']}")
    if snapshot.get("context_id") != context.context_id:
        raise ValueError("deterministic context id mismatch")
    streams = snapshot["streams"]
    if tuple(item["stream_name"] for item in streams) != context.stream_names:
        raise ValueError("deterministic stream registration mismatch")
    prepared: list[tuple[object, object]] = []
    for item in streams:
        family, stream, derivation_digest = context._streams[item["stream_name"]]
        if family != item["family"] or derivation_digest != item["derivation_digest"]:
            raise ValueError(f"deterministic stream metadata mismatch: {item['stream_name']}")
        prepared.append((stream, _decode_stream_state(item["state"], family)))

    originals = [_capture_stream_state(stream, family) for family, stream, _ in context._streams.values()]
    try:
        for (stream, state), item in zip(prepared, streams):
            family = item["family"]
            if family == "python_random":
                stream.setstate(state)
            else:
                stream.bit_generator.state = state
    except Exception as exc:
        for (family, stream, _), original in zip(context._streams.values(), originals):
            if family == "python_random":
                stream.setstate(original)
            else:
                stream.bit_generator.state = original
        raise RuntimeError("deterministic stream restore failed and was rolled back") from exc


def _decode_stream_state(state: Mapping[str, Any], family: str) -> object:
    if family == "python_random":
        return (
            int(state["version"]),
            tuple(int(value) for value in state["internal_state"]),
            state["gaussian_cache"],
        )
    if family == "numpy_pcg64_generator":
        return {
            "bit_generator": "PCG64",
            "state": {
                "state": int(state["state"]["state"]),
                "inc": int(state["state"]["inc"]),
            },
            "has_uint32": int(state["has_uint32"]),
            "uinteger": int(state["uinteger"]),
        }
    raise ValueError(f"unsupported deterministic stream family: {family}")


def _capture_stream_state(stream: object, family: str) -> object:
    if family == "python_random":
        return stream.getstate()
    return copy.deepcopy(stream.bit_generator.state)


def validate_worldbridge_deterministic_randomness_snapshot(snapshot: object) -> dict[str, Any]:
    """Validate a full local-stream snapshot without restoring or mutating it."""
    errors: list[str] = []
    if not isinstance(snapshot, Mapping):
        return {"valid": False, "errors": ["snapshot_not_mapping"]}
    try:
        keys = set(snapshot.keys())
    except Exception:
        return {"valid": False, "errors": ["snapshot_keys_invalid"]}
    if keys != _SNAPSHOT_KEYS:
        errors.append("snapshot_keys_mismatch")
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if snapshot.get("context_kind") != CONTEXT_KIND:
        errors.append("context_kind_mismatch")
    try:
        _clean_context_id(snapshot.get("context_id"))
    except ValueError:
        errors.append("context_id_invalid")
    if snapshot.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if snapshot.get("derivation_version") != DERIVATION_VERSION:
        errors.append("derivation_version_mismatch")
    if snapshot.get("root_seed_material_revealed") is not False:
        errors.append("root_seed_material_revealed_mismatch")
    if not _is_sha256(snapshot.get("root_seed_digest")):
        errors.append("root_seed_digest_invalid")
    if snapshot.get("max_streams") != MAX_STREAMS:
        errors.append("max_streams_mismatch")

    for field_name in (
        "global_python_random_touched",
        "global_numpy_random_touched",
        "restore_performed",
        "replay_input",
        "checkpoint_state",
        "replay_admitted",
        "default_ready",
    ):
        if snapshot.get(field_name) is not False:
            errors.append(f"{field_name}_mismatch")

    streams = snapshot.get("streams")
    if not isinstance(streams, list):
        errors.append("streams_not_list")
        streams = []
    stream_names: list[str] = []
    if len(streams) > MAX_STREAMS:
        errors.append("stream_capacity_exceeded")
    for index, stream in enumerate(streams):
        _validate_stream_snapshot(stream, index, stream_names, errors)
    if snapshot.get("stream_count") != len(streams):
        errors.append("stream_count_mismatch")
    if len(set(stream_names)) != len(stream_names):
        errors.append("duplicate_stream_name")

    digest = snapshot.get("snapshot_digest")
    if not _is_sha256(digest):
        errors.append("snapshot_digest_invalid")
    try:
        expected_digest = _snapshot_digest(snapshot)
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("snapshot_not_canonical_json")
    if expected_digest is not None and digest != expected_digest:
        errors.append("snapshot_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_deterministic_randomness_context_contract() -> dict[str, Any]:
    """Build deterministic E223 evidence using only local caller-owned streams."""
    context = create_worldbridge_deterministic_randomness_context(
        "e223-contract-example",
        "e223-fixed-root-seed",
    )
    python_stream = register_worldbridge_deterministic_random_stream(
        context,
        "sr.script",
        "python_random",
    )
    numpy_stream = register_worldbridge_deterministic_random_stream(
        context,
        "ps.resource",
        "numpy_pcg64_generator",
    )
    assert isinstance(python_stream, random.Random)
    assert isinstance(numpy_stream, np.random.Generator)
    python_stream.random()
    numpy_stream.random()
    snapshot = context.snapshot()
    validation = validate_worldbridge_deterministic_randomness_snapshot(snapshot)
    return {
        "schema_version": SCHEMA_VERSION,
        "contract": "worldbridge_opt_in_deterministic_randomness_context",
        "read_only": True,
        "qt_free": True,
        "caller_owned": True,
        "default_tick_attached": False,
        "supported_stream_families": list(_SUPPORTED_FAMILIES),
        "max_streams": MAX_STREAMS,
        "derivation_version": DERIVATION_VERSION,
        "uses_python_hash": False,
        "uses_wall_time": False,
        "uses_os_entropy": False,
        "global_python_random_touched": False,
        "global_numpy_random_touched": False,
        "restore_api_exposed": True,
        "replay_input": False,
        "checkpoint_state": False,
        "replay_admitted": False,
        "default_ready": False,
        "snapshot": snapshot,
        "snapshot_validation": validation,
        "contract_valid": validation == {"valid": True, "errors": []},
    }


def _normalize_root_seed(root_seed: str | bytes | int) -> tuple[str, bytes]:
    if isinstance(root_seed, bool):
        raise ValueError("root_seed must not be bool")
    if isinstance(root_seed, int):
        text = str(root_seed)
        return f"int:{text}", text.encode("ascii")
    if isinstance(root_seed, bytes):
        if not root_seed or len(root_seed) > 256:
            raise ValueError("root_seed bytes must contain 1-256 bytes")
        return f"bytes:{root_seed.hex()}", bytes(root_seed)
    if isinstance(root_seed, str):
        if not root_seed or len(root_seed) > 256:
            raise ValueError("root_seed text must contain 1-256 characters")
        return f"text:{root_seed}", root_seed.encode("utf-8")
    raise TypeError("root_seed must be str, bytes, or int")


def _derive_stream_digest(root_seed_bytes: bytes, stream_name: str, family: str) -> str:
    material = b"vitaloom/e223/" + root_seed_bytes + b"/" + stream_name.encode("utf-8") + b"/" + family.encode("ascii")
    return hashlib.sha256(material).hexdigest()


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


def _serialize_numpy_generator_state(stream: object) -> dict[str, Any]:
    if not isinstance(stream, np.random.Generator):
        raise TypeError("numpy stream must be a numpy.random.Generator")
    raw = stream.bit_generator.state
    if raw.get("bit_generator") != "PCG64":
        raise ValueError("only NumPy PCG64 Generator streams are supported")
    nested = raw.get("state")
    if not isinstance(nested, Mapping):
        raise ValueError("NumPy PCG64 state is not a mapping")
    return {
        "format": "numpy_generator_pcg64_state_v1",
        "bit_generator": "PCG64",
        "state": {
            "state": int(nested["state"]),
            "inc": int(nested["inc"]),
        },
        "has_uint32": int(raw.get("has_uint32", 0)),
        "uinteger": int(raw.get("uinteger", 0)),
    }


def _validate_stream_snapshot(
    stream: object,
    expected_index: int,
    stream_names: list[str],
    errors: list[str],
) -> None:
    if not isinstance(stream, Mapping):
        errors.append("stream_not_mapping")
        return
    try:
        keys = set(stream.keys())
    except Exception:
        errors.append("stream_keys_invalid")
        return
    if keys != _STREAM_KEYS:
        errors.append("stream_keys_mismatch")
    name = stream.get("stream_name")
    try:
        clean_name = _clean_stream_name(name)
        stream_names.append(clean_name)
    except ValueError:
        errors.append("stream_name_invalid")
    family = stream.get("family")
    if family not in _SUPPORTED_FAMILIES:
        errors.append("stream_family_invalid")
    if stream.get("registration_index") != expected_index:
        errors.append("registration_index_mismatch")
    if stream.get("derivation_version") != DERIVATION_VERSION:
        errors.append("stream_derivation_version_mismatch")
    if not _is_sha256(stream.get("derivation_digest")):
        errors.append("stream_derivation_digest_invalid")
    state = stream.get("state")
    if family == "python_random":
        _validate_python_state(state, errors)
    elif family == "numpy_pcg64_generator":
        _validate_numpy_state(state, errors)


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
    cache = state.get("gaussian_cache")
    if cache is not None and (
        isinstance(cache, bool) or not isinstance(cache, (int, float))
    ):
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
    if state.get("format") != "numpy_generator_pcg64_state_v1":
        errors.append("numpy_state_format_mismatch")
    if state.get("bit_generator") != "PCG64":
        errors.append("numpy_bit_generator_unsupported")
    nested = state.get("state")
    if not isinstance(nested, Mapping) or set(nested.keys()) != {"state", "inc"}:
        errors.append("numpy_nested_state_invalid")
    elif any(
        isinstance(nested.get(field), bool)
        or not isinstance(nested.get(field), int)
        or nested.get(field) < 0
        for field in ("state", "inc")
    ):
        errors.append("numpy_nested_state_value_invalid")
    for field in ("has_uint32", "uinteger"):
        value = state.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"numpy_{field}_invalid")


def _clean_context_id(value: object) -> str:
    if not isinstance(value, str) or _CONTEXT_ID_RE.fullmatch(value) is None:
        raise ValueError("context_id must be a clean 1-128 character identifier")
    return value


def _clean_stream_name(value: object) -> str:
    if not isinstance(value, str) or _STREAM_NAME_RE.fullmatch(value) is None:
        raise ValueError("stream_name must be a clean 1-96 character identifier")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _snapshot_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical["snapshot_digest"] = ""
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


__all__ = [
    "CONTEXT_KIND",
    "DERIVATION_VERSION",
    "MAX_STREAMS",
    "WorldBridgeDeterministicRandomnessContext",
    "build_worldbridge_deterministic_randomness_context_contract",
    "create_worldbridge_deterministic_randomness_context",
    "register_worldbridge_deterministic_random_stream",
    "snapshot_worldbridge_deterministic_randomness_context",
    "restore_worldbridge_deterministic_randomness_context",
    "validate_worldbridge_deterministic_randomness_snapshot",
]
