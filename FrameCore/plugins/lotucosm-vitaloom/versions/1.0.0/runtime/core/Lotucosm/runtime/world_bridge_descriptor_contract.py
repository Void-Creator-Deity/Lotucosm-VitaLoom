# -*- coding: utf-8
"""JSON-safe descriptor contract for future WorldBridge graph mapping.

This module deliberately describes data; it does not mutate SR entities, PS
organisms, components, scripts, or connection objects.  It is the preservation
seam that must exist before a live mapping can be considered.
"""
from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

DESCRIPTOR_SCHEMA_VERSION = 1
DESCRIPTOR_STATUS = "worldbridge_graph_descriptor"


class DescriptorContractError(ValueError):
    """Raised when a graph descriptor cannot be represented losslessly as JSON."""


def _json_safe(value: Any, *, path: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DescriptorContractError(f"non-finite float at {path}")
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise DescriptorContractError(f"non-string object key at {path}")
            result[key] = _json_safe(item, path=f"{path}.{key}")
        return {key: result[key] for key in sorted(result)}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    raise DescriptorContractError(f"unsupported value at {path}: {type(value).__name__}")


def canonicalize_descriptor(value: Mapping[str, Any]) -> dict[str, Any]:
    """Copy and validate a descriptor while preserving unknown data fields."""
    if not isinstance(value, Mapping):
        raise DescriptorContractError("descriptor root must be a mapping")
    normalized = _json_safe(value, path="$ ")
    if not isinstance(normalized, dict):
        raise DescriptorContractError("descriptor root must normalize to an object")
    return normalized


def build_worldbridge_graph_descriptor(
    *,
    membrane_nodes: Iterable[Mapping[str, Any]] = (),
    component_nodes: Iterable[Mapping[str, Any]] = (),
    edges: Iterable[Mapping[str, Any]] = (),
    scripts: Iterable[Mapping[str, Any]] = (),
    extensions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a stable, data-only graph descriptor from mapping facts.

    Every item is copied recursively.  Dict keys are canonicalized, while list
    order is intentionally retained because scene/graph ordering can be
    semantically relevant.  Unknown fields are retained rather than dropped.
    """
    raw = {
        "schema_version": DESCRIPTOR_SCHEMA_VERSION,
        "status": DESCRIPTOR_STATUS,
        "descriptor_state": "data_only",
        "read_only": True,
        "maps_live_objects": False,
        "lossless_for_descriptor_input": True,
        "membrane_nodes": list(membrane_nodes),
        "component_nodes": list(component_nodes),
        "edges": list(edges),
        "scripts": list(scripts),
        "extensions": dict(extensions or {}),
        "preservation": {
            "unknown_fields": "preserved",
            "dict_keys": "sorted",
            "list_order": "preserved",
            "live_mutation": "forbidden",
        },
    }
    return canonicalize_descriptor(raw)


def descriptor_round_trip(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    """Serialize and decode a descriptor, proving the JSON contract."""
    canonical = canonicalize_descriptor(descriptor)
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    if decoded != canonical:
        raise DescriptorContractError("descriptor changed during JSON round-trip")
    return decoded
