from __future__ import annotations

"""Explicit local PS hierarchy/authority contract.

This contract describes ownership inside the PS organism lane only.  It is not
an SR hierarchy mapping and it deliberately does not authorize WorldBridge live
mutation or cross-lane replay.
"""

from typing import Any


def build_ps_hierarchy_authority_contract(organism: Any) -> dict[str, Any]:
    """Return portable hierarchy facts for one PS organism instance."""
    components = list(getattr(organism, "components", {}).values())
    membrane = getattr(organism, "membrane", None)
    parent_ids = {
        str(component.id): getattr(getattr(component, "parent", None), "id", None)
        for component in components
    }
    component_parent_ok = all(parent_id == organism.id for parent_id in parent_ids.values())
    membrane_owner_ok = membrane is None or getattr(membrane, "organism_id", None) == organism.id
    membrane_is_child = membrane is not None and membrane in getattr(organism, "children", ())
    contract = {
        "schema_version": 1,
        "read_only": True,
        "owner_id": str(organism.id),
        "component_parent_authority": "organism",
        "membrane_reference_authority": "organism",
        "membrane_relation": "special_owned_reference",
        "component_parent_ids": parent_ids,
        "membrane_id": getattr(membrane, "id", None),
        "membrane_is_entity_child": membrane_is_child,
        "evidence": {
            "component_parent_links_valid": component_parent_ok,
            "membrane_owner_binding_valid": membrane_owner_ok,
            "membrane_update_ownership": "organism_component_phase",
            "duplicate_entity_tree_update_avoided": not membrane_is_child,
            "cross_lane_hierarchy_authority": False,
            "worldbridge_live_authority": False,
        },
        "do_not_claim": [
            "sr_ps_shared_hierarchy",
            "worldbridge_live_hierarchy_mapping",
            "cross_lane_hierarchy_replay",
        ],
    }
    return contract


def validate_ps_hierarchy_authority_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Validate the portable contract without touching runtime objects."""
    errors: list[str] = []
    if contract.get("read_only") is not True:
        errors.append("read_only must be true")
    if contract.get("component_parent_authority") != "organism":
        errors.append("component parent authority must remain organism")
    if contract.get("membrane_reference_authority") != "organism":
        errors.append("membrane reference authority must remain organism")
    if contract.get("membrane_relation") != "special_owned_reference":
        errors.append("membrane relation must remain special_owned_reference")
    evidence = contract.get("evidence", {})
    for key in ("component_parent_links_valid", "membrane_owner_binding_valid", "duplicate_entity_tree_update_avoided"):
        if evidence.get(key) is not True:
            errors.append(f"missing hierarchy evidence: {key}")
    if evidence.get("cross_lane_hierarchy_authority") is not False:
        errors.append("cross-lane hierarchy authority must remain blocked")
    if evidence.get("worldbridge_live_authority") is not False:
        errors.append("WorldBridge live authority must remain blocked")
    return {"valid": not errors, "errors": errors}


__all__ = ["build_ps_hierarchy_authority_contract", "validate_ps_hierarchy_authority_contract"]
