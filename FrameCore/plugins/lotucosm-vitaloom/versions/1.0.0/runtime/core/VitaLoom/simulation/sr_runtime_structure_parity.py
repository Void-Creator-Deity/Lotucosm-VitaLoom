# -*- coding: utf-8
"""Deterministic fingerprinting of the SR runtime structure.

The fingerprint deliberately excludes mutable state: motion (position,
velocity, acceleration), body state (radius, size, energy, generation,
pinned, membrane_locked), script instance state, Qt objects and visual
caches.  It captures only entity identity/type, script identity and
topology/membrane wiring, so it proves that two loaded scene runtimes share
the same structural skeleton before a dynamic restore is attempted.  It
does not by itself prove replay or fresh-instance parity, and it must not
reject a restore merely because a mutable field drifted between capture and
restore: such fields are owned by the restore envelope, not by this gate.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SCHEMA_VERSION = 2
STATUS = "sr_runtime_structure_parity"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _json_copy(value: Any, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _entity_structure(entity: Any) -> dict[str, Any]:
    entity_id = str(getattr(entity, "id", "")).strip()
    entity_type = str(getattr(entity, "entity_type", "")).strip()
    if not entity_id or not entity_type:
        raise ValueError("SR structure entities require id and entity_type")
    raw_scripts = getattr(entity, "scripts", ()) or ()
    scripts: list[dict[str, str]] = []
    for script in raw_scripts:
        scripts.append(
            {
                "module": str(getattr(type(script), "__module__", "")),
                "qualname": str(getattr(type(script), "__qualname__", type(script).__name__)),
            }
        )
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "scripts": scripts,
    }


def _edge_structure(edges: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            raise TypeError(f"edge[{index}] must be a mapping")
        result.append(_json_copy(dict(edge), f"edge[{index}]"))
    return sorted(result, key=lambda value: _canonical(value))


def build_sr_runtime_structure_fingerprint(
    *,
    entities: Iterable[Any],
    scene_path: str | None,
    structural_edges: Iterable[Mapping[str, Any]],
    signal_edges: Iterable[Mapping[str, Any]],
    membrane_attach: Mapping[str, Sequence[Any]],
    membrane_template: Mapping[str, Any],
) -> dict[str, Any]:
    entity_rows = sorted((_entity_structure(entity) for entity in entities), key=lambda row: row["entity_id"])
    attachments: dict[str, list[Any]] = {}
    for child_id, value in sorted(membrane_attach.items()):
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValueError(f"invalid membrane attachment: {child_id}")
        attachments[str(child_id)] = _json_copy(list(value), f"membrane_attach[{child_id}]")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scene_path": scene_path,
        "entities": entity_rows,
        "structural_edges": _edge_structure(structural_edges),
        "signal_edges": _edge_structure(signal_edges),
        "membrane_attach": attachments,
        "membrane_template": _json_copy(dict(membrane_template), "membrane_template"),
    }
    payload["fingerprint"] = ""
    payload["fingerprint"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def validate_sr_runtime_structure_fingerprint(fingerprint: object) -> dict[str, Any]:
    if not isinstance(fingerprint, Mapping):
        return {"valid": False, "errors": ["fingerprint_must_be_mapping"]}
    required = {"schema_version", "status", "scene_path", "entities", "structural_edges", "signal_edges", "membrane_attach", "membrane_template", "fingerprint"}
    errors: list[str] = []
    if set(fingerprint) != required:
        errors.append("fingerprint_keys_mismatch")
    if fingerprint.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if fingerprint.get("status") != STATUS:
        errors.append("status_mismatch")
    for field in ("entities", "structural_edges", "signal_edges", "membrane_attach", "membrane_template"):
        if not isinstance(fingerprint.get(field), (list, dict)):
            errors.append(f"{field}_invalid")
    digest = fingerprint.get("fingerprint")
    candidate = dict(fingerprint)
    candidate["fingerprint"] = ""
    try:
        expected = hashlib.sha256(_canonical(candidate)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        expected = None
        errors.append("fingerprint_not_canonical_json")
    if not isinstance(digest, str) or digest != expected:
        errors.append("fingerprint_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def compare_sr_runtime_structure_fingerprints(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_validation = validate_sr_runtime_structure_fingerprint(left)
    right_validation = validate_sr_runtime_structure_fingerprint(right)
    if not left_validation["valid"] or not right_validation["valid"]:
        return {"equal": False, "reason": "invalid_fingerprint", "left": left_validation, "right": right_validation}
    return {
        "equal": left["fingerprint"] == right["fingerprint"],
        "reason": "exact_digest_match" if left["fingerprint"] == right["fingerprint"] else "structure_mismatch",
        "left_digest": left["fingerprint"],
        "right_digest": right["fingerprint"],
    }


__all__ = [
    "SCHEMA_VERSION",
    "STATUS",
    "build_sr_runtime_structure_fingerprint",
    "compare_sr_runtime_structure_fingerprints",
    "validate_sr_runtime_structure_fingerprint",
]
