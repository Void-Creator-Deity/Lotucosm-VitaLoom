# -*- coding: utf-8 -*-
"""Read-only WorldBridge mapping-loss audit."""
from __future__ import annotations

from typing import Any

from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)
from core.Lotucosm.runtime.world_bridge_component_projection import (
    build_worldbridge_component_projection,
)
from core.Lotucosm.runtime.world_bridge_capacity_decision import (
    build_worldbridge_capacity_decision,
)
from core.Lotucosm.runtime.world_bridge_spawn_profile_decision import (
    build_worldbridge_spawn_profile_decision,
)
from core.Lotucosm.runtime.world_bridge_mutation_authority import (
    build_worldbridge_mutation_owner_contract,
    validate_worldbridge_mutation_owner_contract,
)


def build_worldbridge_mapping_audit(
    field_roundtrip_witness: dict[str, Any] | None = None,
    cross_lane_behavior_witness: dict[str, Any] | None = None,
    serialized_tick_merge_witness: dict[str, Any] | None = None,
    behavior_equivalence_witness: dict[str, Any] | None = None,
    lossless_mapping_witness: dict[str, Any] | None = None,
    script_checkpoint_witness: dict[str, Any] | None = None,
    cross_session_script_witness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner_contract = build_worldbridge_mutation_owner_contract()
    owner_contract_validation = validate_worldbridge_mutation_owner_contract(
        owner_contract
    )
    # The owner contract is the canonical field inventory. Keep the public
    # mapping-audit shape stable, but derive its state/direction projection so
    # admission, owner and mapping reports cannot silently fork their ledger.
    fields = {
        name: {"state": item["state"], "direction": item["direction"]}
        for name, item in owner_contract["fields"].items()
    }
    field_roundtrip_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "restored_cell_count": 0,
        "remaining_mapping_blockers": [],
        "errors": [],
    }
    if field_roundtrip_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e557_field_roundtrip_authority import (
            validate_worldbridge_e557_field_roundtrip_authority,
        )

        validation = validate_worldbridge_e557_field_roundtrip_authority(
            field_roundtrip_witness
        )
        field_roundtrip_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": field_roundtrip_witness.get("witness_digest"),
            "restored_cell_count": field_roundtrip_witness.get(
                "restored_cell_count", 0
            ),
            "remaining_mapping_blockers": list(
                field_roundtrip_witness.get(
                    "remaining_mapping_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    behavior_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "behavior_routing": None,
        "remaining_behavior_blockers": [],
        "errors": [],
    }
    if cross_lane_behavior_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e558_cross_lane_behavior_authority import (
            validate_worldbridge_e558_cross_lane_behavior_authority,
        )

        validation = validate_worldbridge_e558_cross_lane_behavior_authority(
            cross_lane_behavior_witness
        )
        behavior_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": cross_lane_behavior_witness.get(
                "witness_digest"
            ),
            "behavior_routing": dict(
                cross_lane_behavior_witness.get("behavior_routing", {})
            ),
            "remaining_behavior_blockers": list(
                cross_lane_behavior_witness.get(
                    "remaining_behavior_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    behavior_equivalence_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "routing_witness_digest": None,
        "scope": None,
        "equivalence_policy": None,
        "eligible_behavior_routes": [],
        "lane_local_behavior_routes": {},
        "remaining_behavior_blockers": [],
        "errors": [],
    }
    if behavior_equivalence_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e560_behavior_equivalence_authority import (
            validate_worldbridge_e560_behavior_equivalence_authority,
        )

        validation = (
            validate_worldbridge_e560_behavior_equivalence_authority(
                behavior_equivalence_witness
            )
        )
        behavior_equivalence_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": behavior_equivalence_witness.get(
                "witness_digest"
            ),
            "routing_witness_digest": behavior_equivalence_witness.get(
                "routing_witness_digest"
            ),
            "scope": behavior_equivalence_witness.get("scope"),
            "equivalence_policy": behavior_equivalence_witness.get(
                "equivalence_policy"
            ),
            "eligible_behavior_routes": list(
                behavior_equivalence_witness.get(
                    "eligible_behavior_routes", ()
                )
            ),
            "lane_local_behavior_routes": dict(
                behavior_equivalence_witness.get(
                    "lane_local_behavior_routes", {}
                )
            ),
            "remaining_behavior_blockers": list(
                behavior_equivalence_witness.get(
                    "remaining_behavior_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    lossless_mapping_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "lossless_policy": None,
        "scope": None,
        "portable_checkpoint_lossless": False,
        "silent_loss_cells": [],
        "nonportable_owner_boundaries": [],
        "remaining_lossless_blockers": [],
        "errors": [],
    }
    if lossless_mapping_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e561_lossless_mapping_authority import (
            validate_worldbridge_e561_lossless_mapping_authority,
        )

        validation = validate_worldbridge_e561_lossless_mapping_authority(
            lossless_mapping_witness
        )
        lossless_mapping_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": lossless_mapping_witness.get(
                "witness_digest"
            ),
            "lossless_policy": lossless_mapping_witness.get(
                "lossless_policy"
            ),
            "scope": lossless_mapping_witness.get("scope"),
            "portable_checkpoint_lossless": lossless_mapping_witness.get(
                "portable_checkpoint_lossless"
            )
            is True,
            "silent_loss_cells": list(
                lossless_mapping_witness.get("silent_loss_cells", ())
            ),
            "nonportable_owner_boundaries": list(
                lossless_mapping_witness.get(
                    "nonportable_owner_boundaries", ()
                )
            ),
            "remaining_lossless_blockers": list(
                lossless_mapping_witness.get(
                    "remaining_lossless_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    script_checkpoint_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "policy": None,
        "remaining_script_blockers": [],
        "errors": [],
    }
    if script_checkpoint_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e562_script_checkpoint_authority import (
            validate_worldbridge_e562_script_checkpoint_authority,
        )

        validation = validate_worldbridge_e562_script_checkpoint_authority(
            script_checkpoint_witness
        )
        script_checkpoint_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": script_checkpoint_witness.get(
                "witness_digest"
            ),
            "scope": script_checkpoint_witness.get("scope"),
            "policy": script_checkpoint_witness.get("policy"),
            "remaining_script_blockers": list(
                script_checkpoint_witness.get(
                    "remaining_script_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    cross_session_script_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "scope": None,
        "policy": None,
        "runtime_contract_version": None,
        "remaining_script_blockers": [],
        "errors": [],
    }
    if cross_session_script_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e563_cross_session_script_rehydration import (
            validate_worldbridge_e563_cross_session_script_rehydration_authority,
        )

        validation = (
            validate_worldbridge_e563_cross_session_script_rehydration_authority(
                cross_session_script_witness
            )
        )
        cross_session_script_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": cross_session_script_witness.get(
                "witness_digest"
            ),
            "scope": cross_session_script_witness.get("scope"),
            "policy": cross_session_script_witness.get("policy"),
            "runtime_contract_version": cross_session_script_witness.get(
                "runtime_contract_version"
            ),
            "remaining_script_blockers": list(
                cross_session_script_witness.get(
                    "remaining_script_blockers", ()
                )
            ),
            "errors": list(validation["errors"]),
        }
    tick_merge_evidence = {
        "evidence_available": False,
        "validated": False,
        "witness_digest": None,
        "errors": [],
    }
    if serialized_tick_merge_witness is not None:
        from core.Lotucosm.runtime.world_bridge_e559_serialized_tick_merge_authority import (
            validate_worldbridge_e559_serialized_tick_merge_authority,
        )

        validation = validate_worldbridge_e559_serialized_tick_merge_authority(
            serialized_tick_merge_witness
        )
        tick_merge_evidence = {
            "evidence_available": True,
            "validated": validation["valid"],
            "witness_digest": serialized_tick_merge_witness.get(
                "witness_digest"
            ),
            "errors": list(validation["errors"]),
        }
    tick_merge_admitted = tick_merge_evidence["validated"] is True
    behavior_equivalence_admitted = (
        behavior_equivalence_evidence["validated"] is True
        and behavior_equivalence_evidence["routing_witness_digest"]
        == behavior_evidence["witness_digest"]
        and behavior_evidence["validated"] is True
    )
    lossless_admitted = lossless_mapping_evidence["validated"] is True
    script_checkpoint_admitted = (
        script_checkpoint_evidence["validated"] is True
    )
    cross_session_script_admitted = (
        cross_session_script_evidence["validated"] is True
    )
    do_not_claim = [
        "lossless_worldbridge_mapping",
        "unified_pond_default_ready",
        "sr_ps_tick_merge",
        "full_unified_runtime_replay",
        "cross_lane_behavior_equivalence",
        "cross_lane_behavior_equivalence_outside_declared_scope",
        "portable_sr_executable_script_checkpoint",
        "cross_session_script_rehydration",
    ]
    if tick_merge_admitted:
        do_not_claim.remove("sr_ps_tick_merge")
    if behavior_equivalence_admitted:
        do_not_claim.remove("cross_lane_behavior_equivalence")
    if lossless_admitted:
        do_not_claim.remove("lossless_worldbridge_mapping")
    if cross_session_script_admitted:
        do_not_claim.remove("cross_session_script_rehydration")
    return {
        "schema_version": 1,
        "status": "worldbridge_mapping_loss_audit",
        "read_only": True,
        "lossless": lossless_admitted,
        "default_ready": False,
        "safe_extension_candidate": "size_radius",
        "fields": fields,
        "mutation_owner_contract": owner_contract,
        "mutation_owner_contract_valid": owner_contract_validation["valid"],
        "mutation_owner_contract_errors": owner_contract_validation["errors"],
        "known_losses": [
            name for name, item in fields.items() if item["state"] == "not_mapped"
        ],
        "field_roundtrip_evidence": field_roundtrip_evidence,
        "available_field_cells_closed": (
            field_roundtrip_evidence["validated"] is True
        ),
        "behavior_authority_evidence": behavior_evidence,
        "cross_lane_behavior_admitted": (
            behavior_evidence["validated"] is True
        ),
        "behavior_equivalence_evidence": behavior_equivalence_evidence,
        "behavior_equivalence_admitted": behavior_equivalence_admitted,
        "lossless_mapping_evidence": lossless_mapping_evidence,
        "script_checkpoint_admitted": script_checkpoint_admitted,
        "script_checkpoint_evidence": script_checkpoint_evidence,
        "cross_session_script_rehydration_admitted": (
            cross_session_script_admitted
        ),
        "cross_session_script_evidence": cross_session_script_evidence,
        "tick_merge_evidence": tick_merge_evidence,
        "tick_merge_admitted": tick_merge_admitted,
        "component_mapping_decision": build_worldbridge_component_decision(),
        "capacity_authority_decision": build_worldbridge_capacity_decision(),
        "spawn_profile_authority_decision": build_worldbridge_spawn_profile_decision(),
        "component_projection": build_worldbridge_component_projection(),
        "do_not_claim": do_not_claim,
    }


def declared_worldbridge_mapping_losses(
    audit: dict[str, Any] | None = None,
    *,
    excluded_partial_fields: tuple[str, ...] = (
        "active_visible_state",
        "developmental_profile",
        "social_enabled",
    ),
) -> list[str]:
    """Return fields still unavailable to the cross-lane trace.

    ``known_losses`` is intentionally strict and only includes ``not_mapped``
    fields. Trace comparability also retains partial fields whose value-copy
    exists but whose lifecycle/persistence/replay contract is incomplete.
    Profile fields already have dedicated non-comparable entries.
    """
    current = audit if audit is not None else build_worldbridge_mapping_audit()
    fields = current.get("fields", {})
    if not isinstance(fields, dict):
        return []
    losses = [
        str(name)
        for name, item in fields.items()
        if isinstance(item, dict)
        and (
            item.get("state") == "not_mapped"
            or (
                item.get("state") == "partial"
                and str(name) not in excluded_partial_fields
            )
        )
    ]
    return sorted(losses)

