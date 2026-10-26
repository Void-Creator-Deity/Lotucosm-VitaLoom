# -*- coding: utf-8 -*-
"""Read-only WorldBridge component projection evidence."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)


_KIND_FIELDS: dict[str, tuple[str, ...]] = {
    "membrane": ("radius", "ingest_threshold", "efficiency"),
    "sensor": ("signal_threshold", "sensing_range"),
    "actuator": ("energy_cost",),
}


def project_worldbridge_component(component: Any) -> dict[str, Any]:
    component_type = str(_read(component, "component_type", "") or "").strip()
    kind = _normalize_kind(component_type)
    projected: dict[str, Any] = {
        "projection_state": "read_only_projection",
        "maps_live_components": False,
        "component_id": str(
            _read(component, "component_id", _read(component, "id", "unknown"))
            or "unknown"
        ),
        "component_type": component_type,
        "location": _read(component, "location", ""),
        "acquired": bool(_read(component, "acquired", False)),
        "congenital": bool(_read(component, "congenital", False)),
        "attach_point": _read(component, "attach_point", None),
        "inspectable_properties": _safe_json(_inspectable_properties(component)),
        "connection_count": _connection_count(component),
        "component_fields": _component_fields(component, kind),
    }
    return _safe_json(projected)


def build_worldbridge_component_projection(
    components: list[Any] | tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    projected = [project_worldbridge_component(item) for item in (components or [])]
    coverage = Counter(str(item.get("component_type", "")).lower() for item in projected)
    decision = build_worldbridge_component_decision()
    return {
        "schema_version": 1,
        "status": "worldbridge_component_projection",
        "projection_state": "read_only_projection",
        "read_only": True,
        "maps_live_components": False,
        "default_ready": False,
        "component_count": len(projected),
        "coverage": dict(sorted(coverage.items())),
        "safe_projection_fields": list(decision["safe_projection_fields"]),
        "forbidden_behavior": list(decision["forbidden_behavior"]),
        "components": projected,
        "do_not_claim": [
            "live_component_graph_mapping",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "sr_ps_tick_merge",
        ],
    }


def build_worldbridge_component_projection_diagnostics(
    projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(projection or build_worldbridge_component_projection())
    return {
        "schema_version": 1,
        "status": "worldbridge_component_projection_diagnostics",
        "diagnostic_state": "read_only_projection_diagnostics",
        "read_only": True,
        "maps_live_components": False,
        "default_ready": False,
        "component_count": int(source.get("component_count") or 0),
        "coverage": _safe_json(dict(source.get("coverage") or {})),
        "safe_projection_fields": list(source.get("safe_projection_fields") or []),
        "forbidden_behavior": list(source.get("forbidden_behavior") or []),
        "do_not_claim": list(source.get("do_not_claim") or []),
    }


def _read(subject: Any, key: str, default: Any = None) -> Any:
    if isinstance(subject, Mapping):
        return subject.get(key, default)
    return getattr(subject, key, default)


def _normalize_kind(component_type: str) -> str:
    lowered = component_type.lower()
    for kind in _KIND_FIELDS:
        if lowered == kind or kind in lowered:
            return kind
    return lowered


def _component_fields(component: Any, kind: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for name in _KIND_FIELDS.get(kind, ()):
        value = _read(component, name, None)
        if value is not None:
            fields[name] = value
    return _safe_json(fields)


def _connection_count(component: Any) -> int:
    explicit = _read(component, "connection_count", None)
    if explicit is not None:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            return 0
    connections = _read(component, "connections", None)
    try:
        return len(connections) if connections is not None else 0
    except TypeError:
        return 0


def _inspectable_properties(component: Any) -> Any:
    if isinstance(component, Mapping):
        return component.get("inspectable_properties", {})
    method = getattr(component, "get_inspectable_properties", None)
    if callable(method):
        try:
            return method()
        except Exception:
            return {}
    return getattr(component, "inspectable_properties", {})


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, type):
        return value.__name__
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_safe_json(item) for item in value]
    return repr(value)
