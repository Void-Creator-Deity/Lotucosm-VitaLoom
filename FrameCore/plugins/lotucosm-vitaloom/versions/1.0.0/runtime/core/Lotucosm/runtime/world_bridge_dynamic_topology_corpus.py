"""Portable, digest-bound evidence for dynamic topology event sequences."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_dynamic_topology_corpus"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _is_digest(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def build_worldbridge_dynamic_topology_corpus(
    *,
    runtime_epoch: str,
    scene_path: str,
    events: Sequence[Mapping[str, Any]],
    duplicate_rejected: bool,
    missing_node_rejected: bool,
    epoch_drift_rejected: bool,
    replay_admitted: bool = False,
) -> dict[str, Any]:
    if not isinstance(runtime_epoch, str) or not runtime_epoch.strip():
        raise ValueError("runtime_epoch must be non-empty")
    if not isinstance(scene_path, str) or not scene_path.strip():
        raise ValueError("scene_path must be non-empty")
    if replay_admitted:
        raise ValueError("dynamic topology corpus cannot admit replay")
    records = [copy.deepcopy(dict(event)) for event in events]
    corpus = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "runtime_epoch": runtime_epoch,
        "scene_path": scene_path,
        "events": records,
        "duplicate_rejected": bool(duplicate_rejected),
        "missing_node_rejected": bool(missing_node_rejected),
        "epoch_drift_rejected": bool(epoch_drift_rejected),
        "replay_admitted": False,
        "corpus_digest": "",
    }
    corpus["corpus_digest"] = _digest(corpus)
    return copy.deepcopy(corpus)


def validate_worldbridge_dynamic_topology_corpus(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["corpus_must_be_mapping"]}
    required = {
        "schema_version", "status", "runtime_epoch", "scene_path", "events",
        "duplicate_rejected", "missing_node_rejected", "epoch_drift_rejected",
        "replay_admitted", "corpus_digest",
    }
    if set(value) != required:
        errors.append("corpus_keys_mismatch")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS:
        errors.append("corpus_identity_mismatch")
    for field in ("runtime_epoch", "scene_path"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"{field}_invalid")
    events = value.get("events")
    if not isinstance(events, list) or not events:
        errors.append("events_required")
    else:
        for index, event in enumerate(events):
            if not isinstance(event, Mapping):
                errors.append(f"event_{index}_invalid")
                continue
            if event.get("event_index") != index:
                errors.append(f"event_{index}_order_invalid")
            if event.get("runtime_epoch") != value.get("runtime_epoch"):
                errors.append(f"event_{index}_epoch_mismatch")
            if event.get("kind") not in {"spawn", "despawn", "rejection"}:
                errors.append(f"event_{index}_kind_invalid")
            if not _is_digest(event.get("structure_fingerprint")):
                errors.append(f"event_{index}_structure_digest_invalid")
            if not _is_digest(event.get("receipt_digest")):
                errors.append(f"event_{index}_receipt_digest_invalid")
            node_ids = event.get("node_ids")
            if not isinstance(node_ids, list) or any(not isinstance(node, str) or not node.strip() for node in node_ids):
                errors.append(f"event_{index}_node_ids_invalid")
    for field in ("duplicate_rejected", "missing_node_rejected", "epoch_drift_rejected"):
        if value.get(field) is not True:
            errors.append(f"{field}_required")
    if value.get("replay_admitted") is not False:
        errors.append("replay_admission_overclaim")
    candidate = dict(value)
    candidate["corpus_digest"] = ""
    try:
        expected = _digest(candidate)
    except (TypeError, ValueError, OverflowError):
        expected = None
        errors.append("corpus_not_canonical")
    if value.get("corpus_digest") != expected:
        errors.append("corpus_digest_mismatch")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "build_worldbridge_dynamic_topology_corpus",
    "validate_worldbridge_dynamic_topology_corpus",
]
