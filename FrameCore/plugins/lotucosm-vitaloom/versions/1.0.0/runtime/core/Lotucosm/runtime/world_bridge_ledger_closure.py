# -*- coding: utf-8 -*-
"""Read-only WorldBridge mapping-ledger closure evidence."""
from __future__ import annotations

from typing import Any

from core.Lotucosm.runtime.world_bridge_mutation_authority import MAPPING_FIELDS
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)


def build_worldbridge_ledger_closure() -> dict[str, Any]:
    """Build deterministic evidence for the reviewed, non-default ledger."""
    audit = build_worldbridge_mapping_audit()
    fields = audit["fields"]
    owner_contract_valid = audit.get("mutation_owner_contract_valid") is True
    owner_contract = audit.get("mutation_owner_contract")
    owner_fields = (
        owner_contract.get("fields")
        if isinstance(owner_contract, dict)
        else None
    )
    expected_projection = (
        {
            name: {"state": item["state"], "direction": item["direction"]}
            for name, item in owner_fields.items()
            if isinstance(item, dict)
        }
        if isinstance(owner_fields, dict)
        else {}
    )
    expected_losses = sorted(
        name
        for name, item in expected_projection.items()
        if item["state"] == "not_mapped"
    )
    fields_consistent = (
        owner_contract_valid
        and set(owner_fields or {}) == set(MAPPING_FIELDS)
        and fields == expected_projection
    )
    decisions = {
        "capacity": audit.get("capacity_authority_decision"),
        "spawn_profile": audit.get("spawn_profile_authority_decision"),
        "components": audit.get("component_mapping_decision"),
    }
    decisions_present = all(isinstance(value, dict) and value.get("read_only") for value in decisions.values())
    no_admission_claim = (
        owner_contract_valid
        and audit.get("read_only") is True
        and audit.get("lossless") is False
        and audit.get("default_ready") is False
        and sorted(audit.get("known_losses", [])) == expected_losses
        and "lossless_worldbridge_mapping" in set(audit.get("do_not_claim", []))
        and "unified_pond_default_ready" in set(audit.get("do_not_claim", []))
        and "full_unified_runtime_replay" in set(audit.get("do_not_claim", []))
    )
    return {
        "schema_version": 1,
        "status": "worldbridge_mapping_ledger_closure",
        "read_only": True,
        "ledger_closed_for_review": (
            fields_consistent and decisions_present and owner_contract_valid
        ),
        "unified_runtime_admitted": False,
        "default_ready": False,
        "field_count": len(fields),
        "expected_field_count": len(MAPPING_FIELDS),
        "fields_consistent": fields_consistent,
        "mutation_owner_contract_valid": owner_contract_valid,
        "decision_payloads_present": decisions_present,
        "known_losses": expected_losses,
        "no_admission_claim": no_admission_claim,
        "remaining_admission_blockers": [
            "lossless_mapping_not_proven",
            "sr_ps_tick_merge_not_proven",
            "full_unified_runtime_replay_not_proven",
            "field_level_lifecycle_and_persistence_parity_incomplete",
        ],
        "do_not_claim": [
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "sr_ps_tick_merge",
            "full_unified_runtime_replay",
        ],
    }
