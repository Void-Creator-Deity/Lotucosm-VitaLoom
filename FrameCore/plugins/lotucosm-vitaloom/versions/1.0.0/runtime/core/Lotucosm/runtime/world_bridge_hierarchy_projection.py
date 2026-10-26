# -*- coding: utf-8 -*-
"""Read-only hierarchy projection at the WorldBridge boundary.

Organism-to-organism links can be correlated through the existing bridge
identity map. Component nodes remain unresolved because SR structural IDs and
PS component IDs do not yet have an identity contract. This module never
mutates either lane and never admits live hierarchy authority.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .world_bridge_component_identity import normalize_worldbridge_component_identity_links


def build_worldbridge_hierarchy_projection(
    *,
    entity_links: Iterable[Mapping[str, Any]],
    sr_structural_edges: Iterable[Mapping[str, Any]] = (),
    ps_hierarchy_contracts: Iterable[Mapping[str, Any]] = (),
    component_identity_links: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Project only hierarchy relations with an explicit identity witness."""
    links = _normalize_links(entity_links)
    sr_to_ps = {item["sr_entity_id"]: item["ps_organism_id"] for item in links}
    component_links = normalize_worldbridge_component_identity_links(
        component_identity_links, entity_links=links
    )
    sr_components = {item["sr_component_id"]: item for item in component_links}
    ps_owner_ids = {
        str(contract.get("owner_id"))
        for contract in ps_hierarchy_contracts
        if isinstance(contract, Mapping) and isinstance(contract.get("owner_id"), str)
    }
    mapped: list[dict[str, Any]] = []
    mapped_components: list[dict[str, Any]] = []
    unresolved_sr: list[dict[str, Any]] = []
    for index, edge in enumerate(sr_structural_edges):
        if not isinstance(edge, Mapping):
            raise TypeError(f"sr_structural_edges[{index}] must be an object")
        start = edge.get("start", edge.get("start_id"))
        end = edge.get("end", edge.get("end_id"))
        if not isinstance(start, str) or not isinstance(end, str):
            raise ValueError(f"sr_structural_edges[{index}] requires start/end ids")
        if start in sr_components and end in sr_components:
            parent, child = sr_components[start], sr_components[end]
            mapped_components.append({
                "relation": "sr_component_structural_edge",
                "sr_parent_component_id": start,
                "sr_child_component_id": end,
                "ps_parent_component_id": parent["ps_component_id"],
                "ps_child_component_id": child["ps_component_id"],
                "ps_parent_organism_id": parent["ps_organism_id"],
                "ps_child_organism_id": child["ps_organism_id"],
                "identity_witness": "explicit_component_identity_contract",
            })
        elif start in sr_to_ps and end in sr_to_ps:
            mapped.append({
                "relation": "sr_organism_structural_edge",
                "sr_parent_entity_id": start,
                "sr_child_entity_id": end,
                "ps_parent_organism_id": sr_to_ps[start],
                "ps_child_organism_id": sr_to_ps[end],
                "ps_owner_ids_observed": sorted(ps_owner_ids),
                "identity_witness": "bridge_entity_links",
            })
        else:
            unresolved_sr.append({"start": start, "end": end})
    mapped.sort(key=lambda item: (
        item["sr_parent_entity_id"], item["sr_child_entity_id"],
    ))
    mapped_components.sort(key=lambda item: (
        item["sr_parent_component_id"], item["sr_child_component_id"],
    ))
    unresolved_sr.sort(key=lambda item: (item["start"], item["end"]))
    return {
        "schema_version": 1,
        "status": "worldbridge_hierarchy_projection",
        "read_only": True,
        "projection_state": "component_relations_when_explicit",
        "live_hierarchy_authority": False,
        "cross_lane_replay": False,
        "bridge_link_count": len(links),
        "mapped_organism_relations": mapped,
        "mapped_component_relations": mapped_components,
        "unresolved_sr_relations": unresolved_sr,
        "component_identity_link_count": len(component_links),
        "ps_hierarchy_contract_count": len(ps_owner_ids),
        "unresolved_reason": "component_identity_contract_missing_or_incomplete",
        "do_not_claim": [
            "sr_ps_shared_hierarchy",
            "worldbridge_live_hierarchy_mapping",
            "cross_lane_hierarchy_replay",
        ],
    }


def validate_worldbridge_hierarchy_projection(value: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["projection_must_be_mapping"]}
    for key, expected in (("schema_version", 1), ("status", "worldbridge_hierarchy_projection")):
        if value.get(key) != expected:
            errors.append(f"{key}_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("live_hierarchy_authority") is not False:
        errors.append("live_hierarchy_authority_overclaim")
    if value.get("cross_lane_replay") is not False:
        errors.append("cross_lane_replay_overclaim")
    for field in (
        "mapped_organism_relations", "mapped_component_relations",
        "unresolved_sr_relations", "do_not_claim",
    ):
        if not isinstance(value.get(field), list):
            errors.append(f"{field}_must_be_list")
    return {"valid": not errors, "errors": errors}


def _normalize_links(links: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen_sr: set[str] = set()
    seen_ps: set[str] = set()
    for index, raw in enumerate(links):
        if not isinstance(raw, Mapping):
            raise TypeError(f"entity_links[{index}] must be an object")
        sr_id, ps_id = raw.get("sr_entity_id"), raw.get("ps_organism_id")
        if not isinstance(sr_id, str) or not sr_id.strip() or not isinstance(ps_id, str) or not ps_id.strip():
            raise ValueError(f"entity_links[{index}] has invalid ids")
        sr_id, ps_id = sr_id.strip(), ps_id.strip()
        if sr_id in seen_sr or ps_id in seen_ps:
            raise ValueError("duplicate hierarchy bridge identity")
        seen_sr.add(sr_id)
        seen_ps.add(ps_id)
        result.append({"sr_entity_id": sr_id, "ps_organism_id": ps_id})
    return sorted(result, key=lambda item: (item["sr_entity_id"], item["ps_organism_id"]))


__all__ = [
    "build_worldbridge_hierarchy_projection",
    "validate_worldbridge_hierarchy_projection",
]
