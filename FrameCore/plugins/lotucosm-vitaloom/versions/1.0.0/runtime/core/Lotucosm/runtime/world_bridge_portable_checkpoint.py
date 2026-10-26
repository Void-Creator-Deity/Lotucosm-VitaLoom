# -*- coding: utf-8 -*-
"""Portable WorldBridge checkpoint representation.

A live checkpoint (``worldbridge_live_checkpoint``) intentionally carries
host-local capabilities: a process-scoped owner binding HMAC, captured
process-global random authorities, and a set of ``runtime_epoch`` strings
minted by the capturing host.  Those fields are required to restore *into the
same live process*, but they make the captured mapping unusable as a durable
artifact: a second process resolves no owner binding token, its process-global
RNG state is unrelated, and its runtime epoch is necessarily different.

This module owns the portable projection only.  It removes process-local
capabilities, records the host-local epoch binding declaratively, and seals the
result with a digest so the portable bytes are stable across processes.  It
does not restore, apply, replay, or admit anything: applying a portable
checkpoint to a fresh host is a separate, fail-closed operation owned by the
fresh host, because the mutation-owner contract declares
``portable_object_identity: False``.

Admission stays closed here by construction.  This is a representation
boundary, not a replay authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_live_checkpoint import (
    SCHEMA_VERSION as LIVE_SCHEMA_VERSION,
)
from .world_bridge_live_checkpoint import (
    STATUS as LIVE_STATUS,
)
from .world_bridge_live_checkpoint import (
    validate_worldbridge_live_checkpoint,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_portable_checkpoint"
MAX_PORTABLE_CHECKPOINT_BYTES = 64 * 1024 * 1024

_ADMISSION_KEYS = (
    "atomic_checkpoint",
    "lossless",
    "replay_admitted",
    "default_ready",
)

_STATE_KEYS = frozenset(
    {
        "topology_owner_state",
        "sr_state",
        "ps_state",
        "bridge_identity_links",
        "input_state",
        "randomness_state",
        "lifecycle",
    }
)

_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "checkpoint_id",
        "sequence",
        "runtime_mode",
        "state",
        "host_local_binding",
        "digest",
    }
)

# Host-local epoch locations inside a live checkpoint.  The list is exhaustive
# as of schema version 1; ``validate`` rejects unknown epoch locations by
# comparing against a recorder that walks the whole portable state.
_RUNTIME_EPOCH_PATHS = (
    ("sr_state", "runtime_restore_envelope", "runtime_epoch"),
    ("sr_state", "topology_receipt", "runtime_epoch"),
    ("input_state", "shared_transport", "runtime_epoch"),
    ("randomness_state", "runtime_epoch"),
    ("lifecycle", "project_runtime_binding", "runtime_epoch"),
    ("lifecycle", "runtime_epoch"),
    ("lifecycle", "script_evidence", "runtime_epoch"),
)

_HOST_LOCAL_BINDING_KEYS = frozenset(
    {
        "schema_version",
        "runtime_epochs",
        "owner_binding",
        "process_global_randomness",
        "object_identity_portable",
    }
)


def build_worldbridge_portable_checkpoint(
    live_checkpoint: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one validated live checkpoint onto its portable representation."""
    validation = validate_worldbridge_live_checkpoint(live_checkpoint)
    if validation["valid"] is not True:
        raise ValueError(
            "invalid live checkpoint: " + ",".join(validation["errors"])
        )
    source = copy.deepcopy(dict(live_checkpoint))
    portable_lifecycle = copy.deepcopy(dict(source["lifecycle"]))
    owner_binding = portable_lifecycle.pop("process_owner_binding", None)
    portable_randomness = copy.deepcopy(source["randomness_state"])
    process_global_randomness = None
    if isinstance(portable_randomness, dict):
        process_global_randomness = portable_randomness.pop("process_global", None)
    state: dict[str, Any] = {
        "topology_owner_state": copy.deepcopy(
            source.get("topology_owner_state", {})
        ),
        "sr_state": copy.deepcopy(source["sr_state"]),
        "ps_state": copy.deepcopy(source["ps_state"]),
        "bridge_identity_links": copy.deepcopy(source["bridge_identity_links"]),
        "input_state": copy.deepcopy(source["input_state"]),
        "randomness_state": portable_randomness,
        "lifecycle": portable_lifecycle,
    }
    checkpoint: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "checkpoint_id": source["checkpoint_id"],
        "sequence": source["sequence"],
        "runtime_mode": source["runtime_mode"],
        "state": state,
        "host_local_binding": {
            "schema_version": 1,
            "runtime_epochs": _collect_runtime_epochs(state),
            "owner_binding": {
                "present": owner_binding is not None,
                "removed": owner_binding is not None,
            },
            "process_global_randomness": {
                "present": process_global_randomness is not None,
                "removed": process_global_randomness is not None,
            },
            "object_identity_portable": False,
        },
        "digest": "",
    }
    _ensure_admissions_closed(checkpoint)
    checkpoint["digest"] = _digest(checkpoint)
    return copy.deepcopy(checkpoint)


def validate_worldbridge_portable_checkpoint(value: object) -> dict[str, Any]:
    """Validate portable structure, host-local disclosure, and digest seal."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["portable_checkpoint_must_be_mapping"]}
    if set(value) != set(_REQUIRED_KEYS):
        errors.append("portable_checkpoint_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    checkpoint_id = value.get("checkpoint_id")
    if not isinstance(checkpoint_id, str) or not checkpoint_id.strip():
        errors.append("checkpoint_id_invalid")
    sequence = value.get("sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        errors.append("sequence_invalid")
    if value.get("runtime_mode") != "dual":
        errors.append("runtime_mode_mismatch")

    state = value.get("state")
    if not isinstance(state, Mapping):
        errors.append("state_invalid")
    elif set(state) != _STATE_KEYS:
        errors.append("state_keys_mismatch")
    else:
        if not isinstance(state.get("sr_state"), Mapping):
            errors.append("sr_state_invalid")
        if not isinstance(state.get("topology_owner_state"), Mapping):
            errors.append("topology_owner_state_invalid")
        if not isinstance(state.get("ps_state"), Mapping):
            errors.append("ps_state_invalid")
        if not isinstance(state.get("bridge_identity_links"), list):
            errors.append("bridge_identity_links_invalid")
        if not isinstance(state.get("input_state"), Mapping):
            errors.append("input_state_invalid")
        randomness = state.get("randomness_state")
        if randomness is not None and not isinstance(randomness, Mapping):
            errors.append("randomness_state_invalid")
        elif isinstance(randomness, Mapping) and "process_global" in randomness:
            errors.append("process_global_randomness_not_portable")
        lifecycle = state.get("lifecycle")
        if not isinstance(lifecycle, Mapping):
            errors.append("lifecycle_invalid")
        elif "process_owner_binding" in lifecycle:
            errors.append("process_owner_binding_not_portable")

    binding = value.get("host_local_binding")
    if not isinstance(binding, Mapping) or set(binding) != set(_HOST_LOCAL_BINDING_KEYS):
        errors.append("host_local_binding_invalid")
    else:
        if binding.get("schema_version") != 1:
            errors.append("host_local_binding_schema_mismatch")
        epochs = binding.get("runtime_epochs")
        if not isinstance(epochs, Mapping) or any(
            not isinstance(key, str) or not isinstance(item, str) or not item
            for key, item in epochs.items()
        ):
            errors.append("host_local_runtime_epochs_invalid")
        owner = binding.get("owner_binding")
        if not isinstance(owner, Mapping) or set(owner) != {"present", "removed"}:
            errors.append("host_local_owner_binding_invalid")
        elif not isinstance(owner.get("present"), bool) or not isinstance(
            owner.get("removed"), bool
        ):
            errors.append("host_local_owner_binding_invalid")
        elif owner.get("present") is not owner.get("removed"):
            errors.append("host_local_owner_binding_inconsistent")
        process_global = binding.get("process_global_randomness")
        if not isinstance(process_global, Mapping) or set(process_global) != {
            "present",
            "removed",
        }:
            errors.append("host_local_process_global_randomness_invalid")
        elif not isinstance(process_global.get("present"), bool) or not isinstance(
            process_global.get("removed"), bool
        ):
            errors.append("host_local_process_global_randomness_invalid")
        elif process_global.get("present") is not process_global.get("removed"):
            errors.append("host_local_process_global_randomness_inconsistent")
        if binding.get("object_identity_portable") is not False:
            errors.append("object_identity_overclaim")

    if isinstance(state, Mapping):
        try:
            observed = _collect_runtime_epochs(state)
        except (TypeError, ValueError):
            errors.append("state_not_canonical_json")
        else:
            if isinstance(binding, Mapping) and binding.get("runtime_epochs") != observed:
                errors.append("host_local_runtime_epochs_drift")

    if value.get("digest") != _digest(value):
        errors.append("digest_mismatch")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("portable_checkpoint_not_canonical_json")
    try:
        _ensure_admissions_closed(value)
    except (TypeError, ValueError, OverflowError):
        errors.append("admission_overclaim")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_portable_checkpoint(
    value: Mapping[str, Any], *, max_bytes: int = MAX_PORTABLE_CHECKPOINT_BYTES
) -> bytes:
    limit = _byte_limit(max_bytes)
    validation = validate_worldbridge_portable_checkpoint(value)
    if validation["valid"] is not True:
        raise ValueError(
            "invalid worldbridge portable checkpoint: "
            + ",".join(validation["errors"])
        )
    encoded = _canonical(value)
    if len(encoded) > limit:
        raise OverflowError(
            f"worldbridge portable checkpoint exceeds {limit} bytes"
        )
    return encoded


def decode_worldbridge_portable_checkpoint(
    encoded: bytes | bytearray | memoryview,
    *,
    max_bytes: int = MAX_PORTABLE_CHECKPOINT_BYTES,
) -> dict[str, Any]:
    limit = _byte_limit(max_bytes)
    if not isinstance(encoded, (bytes, bytearray, memoryview)):
        raise TypeError("encoded portable checkpoint must be bytes-like")
    raw = bytes(encoded)
    if not raw or len(raw) > limit:
        raise ValueError(
            "encoded portable checkpoint is empty or exceeds its byte limit"
        )
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            "encoded portable checkpoint is not strict UTF-8 JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError("encoded portable checkpoint root must be an object")
    validation = validate_worldbridge_portable_checkpoint(parsed)
    if validation["valid"] is not True:
        raise ValueError(
            "invalid worldbridge portable checkpoint: "
            + ",".join(validation["errors"])
        )
    if _canonical(parsed) != raw:
        raise ValueError("encoded portable checkpoint is not canonical JSON")
    return copy.deepcopy(parsed)


def worldbridge_portable_checkpoint_state_digest(value: object) -> str:
    """Return the stable digest of the portable state payload only."""
    validation = validate_worldbridge_portable_checkpoint(value)
    if validation["valid"] is not True:
        raise ValueError(
            "invalid worldbridge portable checkpoint: "
            + ",".join(validation["errors"])
        )
    return _digest(value["state"])


def _collect_runtime_epochs(state: Mapping[str, Any]) -> dict[str, str]:
    epochs: dict[str, str] = {}
    for path in _RUNTIME_EPOCH_PATHS:
        node: Any = state
        for index, key in enumerate(path):
            if not isinstance(node, Mapping) or key not in node:
                node = None
                break
            node = node[key]
            if node is None and index < len(path) - 1:
                break
        if node is None:
            continue
        if not isinstance(node, str) or not node:
            raise ValueError("host-local runtime epoch is not a non-empty string")
        epochs[".".join(path)] = node
    return epochs


def _ensure_admissions_closed(value: Mapping[str, Any]) -> None:
    if value.get("runtime_mode") != "dual":
        raise ValueError("portable checkpoint runtime mode mismatch")
    # Admission keys may legitimately appear as explicit negative facts inside
    # captured state.  The portable boundary requires them to stay False; it
    # must not coerce a missing key into an open admission.
    for key in _ADMISSION_KEYS:
        for observed in _iter_key_values(value, key):
            if observed is not False:
                raise ValueError(
                    f"portable checkpoint must not claim admission {key}"
                )


def _iter_key_values(node: object, key: str) -> list[object]:
    found: list[object] = []
    if isinstance(node, Mapping):
        if key in node:
            found.append(node[key])
        for item in node.values():
            found.extend(_iter_key_values(item, key))
    elif isinstance(node, list):
        for item in node:
            found.extend(_iter_key_values(item, key))
    return found


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    payload = copy.deepcopy(value)
    if isinstance(payload, dict) and "digest" in payload:
        payload["digest"] = ""
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _byte_limit(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= MAX_PORTABLE_CHECKPOINT_BYTES
    ):
        raise ValueError(
            f"max_bytes must be an integer from 1 to {MAX_PORTABLE_CHECKPOINT_BYTES}"
        )
    return value


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = item
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "MAX_PORTABLE_CHECKPOINT_BYTES",
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_portable_checkpoint",
    "decode_worldbridge_portable_checkpoint",
    "encode_worldbridge_portable_checkpoint",
    "validate_worldbridge_portable_checkpoint",
    "worldbridge_portable_checkpoint_state_digest",
]