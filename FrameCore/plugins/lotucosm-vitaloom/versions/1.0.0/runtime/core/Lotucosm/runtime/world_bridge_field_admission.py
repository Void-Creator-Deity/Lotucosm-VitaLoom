from __future__ import annotations

"""Field-level admission matrix for future WorldBridge live mapping.

The matrix is policy evidence only.  It deliberately does not construct or
mutate SR/PS runtime objects.
"""

from typing import Any

from .world_bridge_mutation_authority import (
    FIELD_ADMISSION_METADATA,
    MAPPING_FIELDS,
    build_worldbridge_mutation_owner_contract,
    validate_worldbridge_mutation_owner_contract,
)

def build_worldbridge_field_admission_matrix() -> dict[str, Any]:
    """Return explicit, read-only admission evidence for every mapping field."""
    owner_contract = build_worldbridge_mutation_owner_contract()
    owner_validation = validate_worldbridge_mutation_owner_contract(owner_contract)
    if owner_validation != {"valid": True, "errors": []}:
        raise RuntimeError(
            "WorldBridge owner contract is invalid: "
            + ",".join(owner_validation["errors"])
        )
    owner_fields = owner_contract["fields"]
    if (
        set(owner_fields) != set(MAPPING_FIELDS)
        or set(FIELD_ADMISSION_METADATA) != set(MAPPING_FIELDS)
    ):
        raise RuntimeError("WorldBridge field catalog is inconsistent")
    fields: dict[str, Any] = {}
    for name in MAPPING_FIELDS:
        owner_field = owner_fields[name]
        current_state = owner_field["state"]
        direction = owner_field["direction"]
        family = owner_field["admission_family"]
        blockers = tuple(owner_field["admission_required_evidence"])
        fields[name] = {
            "family": family,
            "current_state": current_state,
            "direction": direction,
            "live_adapter_admitted": False,
            "required_evidence": list(blockers),
            "authority": "unresolved" if direction == "none" else (
                "shared_owner_contract" if direction == "sr_to_ps_and_ps_to_sr" else direction
            ),
        }
    return {
        "schema_version": 1,
        "status": "worldbridge_field_admission_matrix",
        "read_only": True,
        "live_adapter_admitted": False,
        "default_ready": False,
        "unified_undo_redo_runtime": False,
        "fields": fields,
        "admission_requirements": [
            "field_level_authority_contract",
            "pond_and_scene_persistence_round_trip",
            "script_lifecycle_and_command_binding_policy",
            "inheritance_mutation_parity",
            "deterministic_replay_and_tick_order_evidence",
        ],
        "do_not_claim": [
            "live_component_graph_mapping",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "sr_ps_tick_merge",
            "full_unified_runtime_replay",
        ],
    }


# These are deliberately conservative: descriptor/projection evidence is not
# promoted to live authority, lifecycle, or replay evidence.
_EVIDENCE_CATALOG: dict[str, dict[str, Any]] = {
    "owner_setter": {"proven": True, "scope": "state_owner_api"},
    "pond_round_trip": {"proven": True, "scope": "scene_persistence"},
    "tick_order": {"proven": True, "scope": "single_lane_or_handoff"},
    "clamp_parity": {"proven": True, "scope": "state_boundary"},
    "creation_authority": {"proven": True, "scope": "creation_only"},
    "lifecycle_authority": {"proven": False, "scope": "live_mapping"},
    "inheritance_parity": {"proven": False, "scope": "cross_lane_lifecycle"},
    "replay_trace": {"proven": False, "scope": "cross_lane_replay"},
    "render_authority": {"proven": False, "scope": "render_adapter"},
    "persistence": {"proven": True, "scope": "local_graph_round_trip_only"},
    "asset_identity": {"proven": False, "scope": "render_asset_contract"},
    "script_lifecycle": {"proven": False, "scope": "script_live_mapping"},
    "command_binding": {"proven": False, "scope": "semantic_command_contract"},
    "authority_contract": {"proven": False, "scope": "graph_live_authority"},
    # Local graph round-trip evidence does not prove cross-lane/live ordering.
    "connection_order": {"proven": False, "scope": "local_graph_round_trip_only"},
}


def build_worldbridge_field_admission_verification() -> dict[str, Any]:
    """Verify matrix blockers and return an executable no-overclaim gate."""
    matrix = build_worldbridge_field_admission_matrix()
    fields: dict[str, Any] = {}
    global_blockers = ["shared_runtime_replay_gate"]
    for name, policy in matrix["fields"].items():
        required = list(policy["required_evidence"])
        missing = [
            evidence for evidence in required
            if not _EVIDENCE_CATALOG.get(evidence, {"proven": False})["proven"]
        ]
        missing = global_blockers + missing
        fields[name] = {
            "current_state": policy["current_state"],
            "required_evidence": required,
            "missing_evidence": missing,
            "live_adapter_admitted": not missing,
            "blocked": bool(missing),
        }
    admitted = [name for name, item in fields.items() if item["live_adapter_admitted"]]
    return {
        "schema_version": 1,
        "status": "worldbridge_field_admission_verification",
        "read_only": True,
        "live_adapter_admitted": bool(admitted),
        "admitted_fields": admitted,
        "blocked_fields": [name for name, item in fields.items() if item["blocked"]],
        "all_fields_blocked": bool(fields) and not admitted,
        "global_blockers": global_blockers,
        "evidence_catalog": _EVIDENCE_CATALOG,
        "fields": fields,
        "matrix": matrix,
        "do_not_claim": list(matrix["do_not_claim"]),
    }


__all__ = [
    "build_worldbridge_field_admission_matrix",
    "build_worldbridge_field_admission_verification",
]

