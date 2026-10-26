"""Provenance-bound, read-only SR/PS topology corpus artifact."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .world_bridge_descriptor_contract import canonicalize_descriptor, descriptor_round_trip


SCHEMA_VERSION = 1
STATUS = "worldbridge_topology_corpus_artifact"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_worldbridge_topology_corpus_artifact(
    *,
    source_scene_path: str,
    scene_descriptor: Mapping[str, Any],
    ps_graph_corpus: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind real source descriptors and PS fact corpus without merging owners."""
    if not isinstance(source_scene_path, str) or not source_scene_path.strip():
        raise ValueError("source_scene_path must be non-empty")
    scene = canonicalize_descriptor(scene_descriptor)
    ps = canonicalize_descriptor(ps_graph_corpus)
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "maps_live_objects": False,
        "source": {
            "scene_path": source_scene_path,
            "scene_descriptor_digest": _digest(scene),
            "ps_graph_corpus_digest": _digest(ps),
        },
        "scene_descriptor": scene,
        "ps_graph_corpus": ps,
        "cross_lane_identity_join": "not_performed",
        "provenance_bound": True,
        "canonical_round_trip": True,
        "cross_lane_topology_admitted": False,
        "replay_admitted": False,
        "lossless": False,
        "default_ready": False,
        "do_not_claim": [
            "sr_ps_shared_topology_authority",
            "live_component_graph_mapping",
            "cross_lane_deterministic_replay",
            "lossless_worldbridge_mapping",
        ],
        "artifact_digest": "",
    }
    artifact["artifact_digest"] = _digest(artifact)
    return copy.deepcopy(artifact)


def validate_worldbridge_topology_corpus_artifact(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["artifact_must_be_mapping"]}
    required = {
        "schema_version", "status", "read_only", "maps_live_objects", "source",
        "scene_descriptor", "ps_graph_corpus", "cross_lane_identity_join",
        "provenance_bound", "canonical_round_trip", "cross_lane_topology_admitted",
        "replay_admitted", "lossless", "default_ready", "do_not_claim", "artifact_digest",
    }
    if set(value) != required:
        errors.append("artifact_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("artifact_version_mismatch")
    for key in ("read_only", "maps_live_objects", "provenance_bound", "canonical_round_trip"):
        if value.get(key) is not (True if key in {"read_only", "provenance_bound", "canonical_round_trip"} else False):
            errors.append(f"{key}_mismatch")
    if value.get("cross_lane_identity_join") != "not_performed":
        errors.append("cross_lane_identity_join_overclaim")
    for key in ("cross_lane_topology_admitted", "replay_admitted", "lossless", "default_ready"):
        if value.get(key) is not False:
            errors.append(f"{key}_overclaim")
    if not isinstance(value.get("source"), Mapping):
        errors.append("source_invalid")
    try:
        scene = canonicalize_descriptor(value.get("scene_descriptor"))
        ps = canonicalize_descriptor(value.get("ps_graph_corpus"))
        if value.get("source", {}).get("scene_descriptor_digest") != _digest(scene):
            errors.append("scene_descriptor_digest_mismatch")
        if value.get("source", {}).get("ps_graph_corpus_digest") != _digest(ps):
            errors.append("ps_graph_corpus_digest_mismatch")
        if descriptor_round_trip(scene) != scene or descriptor_round_trip(ps) != ps:
            errors.append("canonical_round_trip_failed")
    except (TypeError, ValueError, OverflowError):
        errors.append("nested_descriptor_invalid")
    candidate = dict(value)
    candidate["artifact_digest"] = ""
    if value.get("artifact_digest") != _digest(candidate):
        errors.append("artifact_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_topology_corpus_artifact",
    "validate_worldbridge_topology_corpus_artifact",
]
