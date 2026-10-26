# -*- coding: utf-8 -*-
"""Project strict track-specific runtime snapshot facts into WorldBridge evidence.

This Module accepts only Mapping/list/scalar JSON values owned by snapshot
Authorities. Live PS/SR objects and behavior remain behind their Adapters.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
SCOPE = "runtime_snapshot_component_projection"
AUTHORITY = "runtime_snapshot_component_projection"
PROJECTION_STATE = "runtime_snapshot_read_only_projection"
PS_TRACK = "ps_batch"
SR_TRACK = "sr_play"
PS_SOURCE = "ps_component_registry"
SR_SOURCE = "sr_attached_runtime_entity"
PS_IDENTITY_RELATION = "ps_component_registry_member"
SR_IDENTITY_RELATION = "attached_projection_not_ps_component_equivalence"
_ALLOWED_STATUS = {
    "unavailable",
    "not_running",
    "stale",
    "missing",
    "invalid_identity",
    "unsupported_track",
    "error",
}
_KIND_FIELDS: dict[str, tuple[str, ...]] = {
    "membrane": ("radius", "ingest_threshold", "efficiency"),
    "sensor": ("signal_threshold", "sensing_range"),
    "actuator": ("energy_cost",),
}
_DO_NOT_CLAIM = [
    "live_component_object_mapping",
    "lossless_worldbridge_mapping",
    "unified_pond_default_ready",
    "sr_ps_tick_merge",
    "ps_component_equivalence",
]


def project_ps_runtime_snapshot_components(snapshot_envelope: object) -> dict[str, Any]:
    """Project one PS organism snapshot through the PS component-fact schema."""
    return _project_snapshot(
        snapshot_envelope,
        expected_track=PS_TRACK,
        expected_source=PS_SOURCE,
        identity_relation=PS_IDENTITY_RELATION,
        include_ps_genetics=True,
    )


def project_sr_runtime_snapshot_components(snapshot_envelope: object) -> dict[str, Any]:
    """Project one selected SR organism snapshot through attachment facts only."""
    return _project_snapshot(
        snapshot_envelope,
        expected_track=SR_TRACK,
        expected_source=SR_SOURCE,
        identity_relation=SR_IDENTITY_RELATION,
        include_ps_genetics=False,
    )


def _project_snapshot(
    envelope: object,
    *,
    expected_track: str,
    expected_source: str,
    identity_relation: str,
    include_ps_genetics: bool,
) -> dict[str, Any]:
    if not isinstance(envelope, Mapping):
        return _base_result(
            status="error",
            track=expected_track,
            identity_relation=identity_relation,
            reason="invalid_snapshot_envelope",
        )

    raw_snapshot = envelope.get("snapshot")
    if (
        envelope.get("track") == expected_track
        and envelope.get("status") == "ok"
        and isinstance(raw_snapshot, Mapping)
        and "component_facts" in raw_snapshot
    ):
        try:
            _validate_json_value(raw_snapshot.get("component_facts"), "component_facts")
        except (TypeError, ValueError):
            return _base_result(
                status="error",
                track=expected_track,
                identity_relation=identity_relation,
                reason="invalid_component_facts",
            )

    try:
        _validate_json_value(envelope, "snapshot_envelope")
        source_envelope = _json_copy(dict(envelope))
    except (TypeError, ValueError):
        return _base_result(
            status="error",
            track=expected_track,
            identity_relation=identity_relation,
            reason="invalid_snapshot_envelope",
        )

    identity = source_envelope.get("identity")
    if not isinstance(identity, dict):
        identity = None
    revision = source_envelope.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        revision = None

    result = _base_result(
        status="error",
        track=expected_track,
        identity_relation=identity_relation,
        identity=identity,
        revision=revision,
    )
    track = source_envelope.get("track")
    if track != expected_track:
        result["status"] = "unsupported_track"
        result["reason"] = "unsupported_track"
        return result

    status = source_envelope.get("status")
    if status != "ok":
        if status not in _ALLOWED_STATUS:
            result["status"] = "error"
            result["reason"] = "unsupported_snapshot_status"
            return result
        result["status"] = status
        reason = source_envelope.get("reason")
        if isinstance(reason, str) and reason:
            result["reason"] = reason
        return result

    snapshot = source_envelope.get("snapshot")
    if not isinstance(snapshot, dict):
        result["status"] = "error"
        result["reason"] = "invalid_snapshot_envelope"
        return result
    if "component_facts" not in snapshot:
        result["status"] = "not_proven"
        result["reason"] = "component_facts_unavailable"
        return result

    facts = snapshot.get("component_facts")
    if not isinstance(facts, list):
        result["status"] = "error"
        result["reason"] = "invalid_component_facts"
        return result

    try:
        projected = [
            _project_fact(
                fact,
                expected_track=expected_track,
                expected_source=expected_source,
                identity_relation=identity_relation,
                include_ps_genetics=include_ps_genetics,
            )
            for fact in facts
        ]
        ids = [item["component_id"] for item in projected]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate component_id")
    except (TypeError, ValueError):
        result["status"] = "error"
        result["reason"] = "invalid_component_facts"
        return result

    projected.sort(key=lambda item: item["component_id"])
    coverage = Counter(item["component_type"].lower() for item in projected)
    result.update(
        {
            "status": "ok",
            "maps_live_runtime_snapshot_facts": True,
            "component_count": len(projected),
            "coverage": dict(sorted(coverage.items())),
            "components": _json_copy(projected),
        }
    )
    return result


def _project_fact(
    fact: object,
    *,
    expected_track: str,
    expected_source: str,
    identity_relation: str,
    include_ps_genetics: bool,
) -> dict[str, Any]:
    if not isinstance(fact, Mapping):
        raise TypeError("component fact must be an object")
    _validate_json_value(fact, "component_fact")
    source = _required_string(fact.get("source"), "source")
    relation = _required_string(fact.get("identity_relation"), "identity_relation")
    if source != expected_source or relation != identity_relation:
        raise ValueError("component fact source mismatch")

    component_id = _required_string(fact.get("component_id"), "component_id")
    component_type = _required_string(fact.get("component_type"), "component_type")
    location = _required_string(fact.get("location"), "location")
    connection_count = fact.get("connection_count")
    if (
        not isinstance(connection_count, int)
        or isinstance(connection_count, bool)
        or connection_count < 0
    ):
        raise ValueError("connection_count must be a non-negative integer")

    attach_point = fact.get("attach_point")
    if expected_track == PS_TRACK:
        if attach_point is not None and not isinstance(attach_point, str):
            raise ValueError("PS attach_point must be a string or null")
    else:
        if (
            not isinstance(attach_point, list)
            or len(attach_point) != 2
            or any(not _is_number(item) for item in attach_point)
        ):
            raise ValueError("SR attach_point must contain two finite numbers")

    kind = _normalize_kind(component_type)
    allowed_fields = set(_KIND_FIELDS.get(kind, ()))
    inspectable = _project_property_mapping(
        fact.get("inspectable_properties"), allowed_fields
    )
    component_fields = _project_property_mapping(
        fact.get("component_fields"), allowed_fields
    )
    projected: dict[str, Any] = {
        "projection_state": PROJECTION_STATE,
        "maps_live_components": False,
        "source": source,
        "identity_relation": relation,
        "component_id": component_id,
        "component_type": component_type,
        "location": location,
        "attach_point": _json_copy(attach_point),
        "connection_count": connection_count,
        "inspectable_properties": inspectable,
        "component_fields": component_fields,
    }
    if include_ps_genetics:
        acquired = fact.get("acquired")
        congenital = fact.get("congenital")
        if not isinstance(acquired, bool) or not isinstance(congenital, bool):
            raise ValueError("PS acquired/congenital must be booleans")
        projected["acquired"] = acquired
        projected["congenital"] = congenital
    return projected


def _project_property_mapping(value: object, allowed_fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("property projection must be an object")
    result: dict[str, Any] = {}
    for raw_name, raw_value in value.items():
        if not isinstance(raw_name, str):
            raise TypeError("property names must be strings")
        if raw_name not in allowed_fields:
            raise ValueError("unsupported component property")
        _validate_json_value(raw_value, raw_name)
        result[raw_name] = _json_copy(raw_value)
    return dict(sorted(result.items()))


def _base_result(
    *,
    status: str,
    track: str,
    identity_relation: str,
    identity: dict[str, Any] | None = None,
    revision: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scope": SCOPE,
        "authority": AUTHORITY,
        "track": track,
        "read_only": True,
        "projection_state": PROJECTION_STATE,
        "maps_live_components": False,
        "maps_live_runtime_snapshot_facts": False,
        "identity_relation": identity_relation,
        "identity": _json_copy(identity) if identity is not None else None,
        "revision": revision,
        "component_count": None,
        "coverage": {},
        "components": [],
        "do_not_claim": list(_DO_NOT_CLAIM),
    }
    if reason is not None:
        result["reason"] = reason
    return result


def _normalize_kind(component_type: str) -> str:
    lowered = component_type.lower()
    for kind in _KIND_FIELDS:
        if lowered == kind or kind in lowered:
            return kind
    return lowered


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_json_value(value: object, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise TypeError(f"{path} contains a non-JSON value")


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))

