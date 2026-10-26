"""Fail-closed evidence gate joining replay and dynamic-topology provenance."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_dynamic_topology_fresh_provenance import (
    validate_worldbridge_dynamic_topology_fresh_provenance,
)
from .world_bridge_e508_fresh_replay_corpus import (
    validate_worldbridge_e508_fresh_replay_corpus,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e532_replay_topology_gate"
BLOCKERS = (
    "topology_events_not_bound_per_tick_to_input_and_rng",
    "e508_e531_host_capture_pair_not_bound",
    "checkpoint_or_scene_binding_not_proven_for_combined_capture",
    "unified_runtime_replay_not_proven",
)
_REQUIRED_KEYS = {
    "schema_version",
    "status",
    "read_only",
    "replay_corpus",
    "topology_provenance",
    "replay_corpus_digest",
    "topology_provenance_digest",
    "runtime_epochs",
    "tick_count",
    "topology_event_count",
    "host_capture_pair_binding_proven",
    "topology_tick_binding_proven",
    "checkpoint_scene_binding_proven",
    "blockers",
    "replay_admitted",
    "default_ready",
    "lossless",
    "gate_digest",
}


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


def _gate_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["gate_digest"] = ""
    return _digest(payload)


def build_worldbridge_e532_replay_topology_gate(
    *,
    replay_corpus: Mapping[str, Any],
    topology_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind E508/E531 evidence only when both describe the same host pair.

    This packages independent evidence, not runtime authority: E508 and E531
    currently do not share a run identity, and no tick-to-topology event,
    checkpoint/scene, or live replay permission is inferred by this gate.
    """
    replay_copy = copy.deepcopy(dict(replay_corpus))
    topology_copy = copy.deepcopy(dict(topology_provenance))
    replay_validation = validate_worldbridge_e508_fresh_replay_corpus(replay_copy)
    if replay_validation != {"valid": True, "errors": []}:
        raise ValueError("E508 replay corpus invalid: " + ",".join(replay_validation["errors"]))
    topology_validation = validate_worldbridge_dynamic_topology_fresh_provenance(topology_copy)
    if topology_validation != {"valid": True, "errors": []}:
        raise ValueError("E531 topology provenance invalid: " + ",".join(topology_validation["errors"]))
    gate: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "replay_corpus": replay_copy,
        "topology_provenance": topology_copy,
        "replay_corpus_digest": replay_copy["corpus_digest"],
        "topology_provenance_digest": topology_copy["artifact_digest"],
        "runtime_epochs": {
            "e508": {
                "source": replay_copy["source_epoch"],
                "fresh": replay_copy["fresh_epoch"],
            },
            "e531": {
                "source": topology_copy["source_runtime_epoch"],
                "fresh": topology_copy["fresh_runtime_epoch"],
            },
        },
        "tick_count": replay_copy["tick_count"],
        "topology_event_count": len(topology_copy["events"]),
        "host_capture_pair_binding_proven": False,
        "topology_tick_binding_proven": False,
        "checkpoint_scene_binding_proven": False,
        "blockers": list(BLOCKERS),
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
        "gate_digest": "",
    }
    gate["gate_digest"] = _gate_digest(gate)
    return copy.deepcopy(gate)


def validate_worldbridge_e532_replay_topology_gate(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["gate_not_mapping"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("gate_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("gate_identity_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")

    replay = value.get("replay_corpus")
    replay_validation = validate_worldbridge_e508_fresh_replay_corpus(replay)
    if replay_validation != {"valid": True, "errors": []}:
        errors.append("replay_corpus_invalid")
    elif (
        value.get("replay_corpus_digest") != replay.get("corpus_digest")
        or value.get("tick_count") != replay.get("tick_count")
    ):
        errors.append("replay_corpus_binding_mismatch")

    topology = value.get("topology_provenance")
    topology_validation = validate_worldbridge_dynamic_topology_fresh_provenance(topology)
    if topology_validation != {"valid": True, "errors": []}:
        errors.append("topology_provenance_invalid")
    elif (
        value.get("topology_provenance_digest") != topology.get("artifact_digest")
        or value.get("topology_event_count") != len(topology.get("events", []))
    ):
        errors.append("topology_provenance_binding_mismatch")

    epochs = value.get("runtime_epochs")
    if not isinstance(epochs, Mapping):
        errors.append("runtime_epochs_invalid")
    elif isinstance(replay, Mapping) and isinstance(topology, Mapping):
        expected_epochs = {
            "e508": {"source": replay.get("source_epoch"), "fresh": replay.get("fresh_epoch")},
            "e531": {
                "source": topology.get("source_runtime_epoch"),
                "fresh": topology.get("fresh_runtime_epoch"),
            },
        }
        if epochs != expected_epochs:
            errors.append("runtime_epoch_binding_mismatch")

    if value.get("host_capture_pair_binding_proven") is not False:
        errors.append("host_capture_pair_binding_overclaim")
    if value.get("topology_tick_binding_proven") is not False:
        errors.append("topology_tick_binding_overclaim")
    if value.get("checkpoint_scene_binding_proven") is not False:
        errors.append("checkpoint_scene_binding_overclaim")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    for field in ("replay_admitted", "default_ready", "lossless"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    try:
        expected_digest = _gate_digest(value)
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("gate_not_canonical")
    if value.get("gate_digest") != expected_digest:
        errors.append("gate_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "BLOCKERS",
    "build_worldbridge_e532_replay_topology_gate",
    "validate_worldbridge_e532_replay_topology_gate",
]
