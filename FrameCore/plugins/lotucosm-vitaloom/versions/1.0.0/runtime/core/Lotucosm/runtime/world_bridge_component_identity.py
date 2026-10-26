# -*- coding: utf-8 -*-
"""Explicit, read-only SR/PS component identity evidence."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_FIELDS = ("sr_component_id", "ps_component_id", "sr_organism_id", "ps_organism_id")


def normalize_worldbridge_component_identity_links(
    links: Iterable[Mapping[str, Any]], *, entity_links: Iterable[Mapping[str, Any]] = ()
) -> list[dict[str, str]]:
    """Validate and return deterministic copies; never infer identity."""
    owners: dict[str, str] = {}
    for index, raw in enumerate(entity_links):
        if not isinstance(raw, Mapping):
            raise TypeError(f"entity_links[{index}] must be an object")
        sr_id, ps_id = raw.get("sr_entity_id"), raw.get("ps_organism_id")
        if not isinstance(sr_id, str) or not sr_id.strip() or not isinstance(ps_id, str) or not ps_id.strip():
            raise ValueError(f"entity_links[{index}] has invalid ids")
        sr_id, ps_id = sr_id.strip(), ps_id.strip()
        if sr_id in owners and owners[sr_id] != ps_id:
            raise ValueError("conflicting organism bridge identity")
        owners[sr_id] = ps_id
    result: list[dict[str, str]] = []
    seen_sr: set[str] = set()
    seen_ps: set[str] = set()
    for index, raw in enumerate(links):
        if not isinstance(raw, Mapping):
            raise TypeError(f"component_identity_links[{index}] must be an object")
        item: dict[str, str] = {}
        for field in _FIELDS:
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"component_identity_links[{index}].{field} is required")
            item[field] = value.strip()
        if item["sr_component_id"] in seen_sr or item["ps_component_id"] in seen_ps:
            raise ValueError("duplicate component identity")
        if item["sr_organism_id"] in owners and owners[item["sr_organism_id"]] != item["ps_organism_id"]:
            raise ValueError("component identity owner mismatch")
        seen_sr.add(item["sr_component_id"])
        seen_ps.add(item["ps_component_id"])
        result.append(item)
    return sorted(result, key=lambda item: (item["sr_component_id"], item["ps_component_id"]))


def validate_worldbridge_component_identity_links(value: object) -> dict[str, Any]:
    if not isinstance(value, list):
        return {"valid": False, "errors": ["component_identity_links_must_be_list"]}
    try:
        normalize_worldbridge_component_identity_links(value)
    except (TypeError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    return {"valid": True, "errors": []}


def capture_worldbridge_component_identity_links(
    entities: Iterable[Any], pond: Any
) -> list[dict[str, str]]:
    """Capture only an explicit host-provided component identity declaration."""
    links: list[dict[str, str]] = []
    organisms = getattr(pond, "organisms", None)
    if not hasattr(organisms, "get"):
        raise ValueError("pond.organisms registration map is unavailable")
    for entity in entities:
        declared = getattr(entity, "_world_bridge_component_identity_links", ())
        if declared:
            links.extend(declared)
    normalized = normalize_worldbridge_component_identity_links(links)
    for item in normalized:
        organism = organisms.get(item["ps_organism_id"])
        if organism is None:
            raise ValueError(f"unknown PS organism id: {item['ps_organism_id']}")
        component = getattr(organism, "components", {}).get(item["ps_component_id"])
        if component is None:
            raise ValueError(f"unknown PS component id: {item['ps_component_id']}")
        declared_sr_id = getattr(component, "sr_component_id", None)
        if declared_sr_id != item["sr_component_id"]:
            raise RuntimeError("live component identity receipt mismatch")
    return normalized


def bind_worldbridge_component_identity_links(entity: Any, organism: Any) -> list[dict[str, str]]:
    """Bind an entity's explicit component receipt to newly created PS components."""
    declared = getattr(entity, "_world_bridge_component_identity_links", ())
    if not declared:
        return []
    sr_entity_id = str(getattr(entity, "id", "")).strip()
    ps_organism_id = str(getattr(organism, "id", "")).strip()
    raw_links = list(declared)
    for raw in raw_links:
        if not isinstance(raw, Mapping):
            raise TypeError("component identity declaration must contain objects")
        if raw.get("sr_organism_id") != sr_entity_id or raw.get("ps_organism_id") != ps_organism_id:
            raise ValueError("component identity declaration owner mismatch")
    links = normalize_worldbridge_component_identity_links(raw_links)
    components = getattr(organism, "components", {})
    for item in links:
        component = components.get(item["ps_component_id"])
        if component is None:
            raise ValueError(f"unknown PS component id: {item['ps_component_id']}")
        existing = getattr(component, "sr_component_id", None)
        if existing not in (None, item["sr_component_id"]):
            raise ValueError("PS component SR identity already bound differently")
        component.sr_component_id = item["sr_component_id"]
    return links


def validate_worldbridge_component_identity_against_live(
    links: Iterable[Mapping[str, Any]], entities: Iterable[Any], pond: Any
) -> list[dict[str, str]]:
    """Validate a receipt against current explicit PS declarations."""
    expected = normalize_worldbridge_component_identity_links(links)
    current = capture_worldbridge_component_identity_links(entities, pond)
    if current != expected:
        raise RuntimeError("live component identity receipt mismatch")
    return current


__all__ = [
    "normalize_worldbridge_component_identity_links",
    "validate_worldbridge_component_identity_links",
    "capture_worldbridge_component_identity_links",
    "bind_worldbridge_component_identity_links",
    "validate_worldbridge_component_identity_against_live",
]
