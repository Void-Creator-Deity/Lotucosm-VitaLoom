# -*- coding: utf-8 -*-
"""Qt-free WorldBridge mutation-owner and owner-drift contract.

The bridge currently has two live lane owners and a coordinator.  The
coordinator may order an opt-in hand-off and checkpoint restore, but it must
not become a third state owner.  This module records that boundary and offers
the small process-local binding check used by the live checkpoint adapter.

The binding is intentionally not portable replay data: Python object
identities only prove that one in-process operation is still addressing the
same owner roots.  Field mapping remains separately gated and the contract
does not enable unified runtime, replay, or lossless mapping.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1
PROCESS_OWNER_BINDING_SCHEMA_VERSION = 2
STATUS = "worldbridge_mutation_owner_contract"
_FIELD_STATES = frozenset({"covered", "creation_only", "partial", "not_mapped"})
_PROCESS_INSTANCE_NONCE = uuid4().hex

OWNER_ROOTS = (
    "viewport_host",
    "sr_runtime_entities",
    "ps_pond",
    "sr_runtime_rng",
    "ps_pond_rng",
    "input_sequence",
    "sr_identity_source",
    "ps_identity_source",
    "sr_physics_world",
)

MAPPING_FIELDS = (
    "position",
    "energy",
    "health",
    "max_energy",
    "max_health",
    "developmental_profile",
    "social_enabled",
    "size_radius",
    "velocity_acceleration",
    "active_visible_state",
    "render_identity",
    "scripts",
    "membrane_component_graph",
    "hierarchy",
    "memory_genes",
)

WORLD_BRIDGE_LIVE_MAPPER_PATHS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "position": ("creation_seed", "sr_to_ps", "ps_to_sr"),
    "energy": ("creation_seed", "sr_to_ps", "ps_to_sr"),
    "health": ("creation_seed", "sr_to_ps", "ps_to_sr"),
    "max_energy": ("creation_seed",),
    "max_health": ("creation_seed",),
    "size_radius": ("creation_seed", "ps_to_sr"),
    "velocity_acceleration": ("creation_seed", "sr_to_ps", "ps_to_sr"),
    "developmental_profile": ("spawn_profile_seed",),
    "social_enabled": ("spawn_profile_seed",),
    "active_visible_state": (
        "creation_seed",
        "sr_to_ps",
        "ps_to_sr",
        "visible_sr_presentation_only",
    ),
    "render_identity": (),
    "scripts": (),
    "membrane_component_graph": (),
    "hierarchy": (),
    "memory_genes": ("creation_seed", "sr_to_ps", "ps_to_sr"),
})

# This is the single source for the field-admission matrix's family and
# evidence vocabulary. Owner-specific blockers below remain separate: they
# describe the lane owner contract, while this catalog describes admission
# evidence. Keeping both in the same immutable module prevents the mapping
# audit and admission report from silently acquiring different field sets.
FIELD_ADMISSION_METADATA: Mapping[str, tuple[str, tuple[str, ...]]] = MappingProxyType({
    "position": ("shared_state", ("owner_setter", "pond_round_trip", "tick_order")),
    "energy": ("shared_state", ("owner_setter", "clamp_parity", "tick_order")),
    "health": ("shared_state", ("owner_setter", "clamp_parity", "tick_order")),
    "size_radius": ("shared_state", ("owner_setter", "pond_round_trip", "tick_order")),
    "velocity_acceleration": ("shared_state", ("owner_setter", "tick_order", "replay_trace")),
    "max_energy": ("capacity", ("creation_authority", "inheritance_parity", "pond_round_trip")),
    "max_health": ("capacity", ("creation_authority", "inheritance_parity", "pond_round_trip")),
    "developmental_profile": ("profile", ("lifecycle_authority", "inheritance_parity", "replay_trace")),
    "social_enabled": ("profile", ("lifecycle_authority", "inheritance_parity", "replay_trace")),
    "active_visible_state": ("lifecycle_presentation", ("lifecycle_authority", "persistence", "replay_trace")),
    "render_identity": ("presentation", ("render_authority", "asset_identity", "persistence")),
    "scripts": ("behavior", ("script_lifecycle", "command_binding", "replay_trace")),
    "membrane_component_graph": ("topology", ("authority_contract", "connection_order", "persistence")),
    "hierarchy": ("topology", ("authority_contract", "connection_order", "persistence")),
    "memory_genes": ("inheritance", ("inheritance_parity", "persistence", "replay_trace")),
})


@dataclass(frozen=True)
class _FieldOwnerDefinition:
    state: str
    direction: str
    sr_owner: str | None
    ps_owner: str | None
    mutation_owner: str
    mutation_api: str
    checkpoint_scope: str
    required_evidence: tuple[str, ...]


_FIELD_OWNER_DEFINITIONS: Mapping[str, _FieldOwnerDefinition] = MappingProxyType({
    "position": _FieldOwnerDefinition(
        "covered", "sr_to_ps_and_ps_to_sr", "sr_runtime_entity", "ps_organism",
        "lane_owned_api_with_compatibility_fallback",
        "ps_restore_motion_state_or_position_setter;sr_position_setter",
        "sr_state_and_ps_state",
        ("complete_field_parity", "shared_tick_authority", "replay_trace"),
    ),
    "energy": _FieldOwnerDefinition(
        "covered", "sr_to_ps_and_ps_to_sr", "sr_runtime_entity", "ps_organism",
        "lane_owned_api_with_compatibility_fallback",
        "ps_energy_setter_or_compat_attribute;sr_energy_setter_or_compat_attribute",
        "sr_state_and_ps_state",
        ("clamp_parity", "shared_tick_authority", "replay_trace"),
    ),
    "health": _FieldOwnerDefinition(
        "covered", "sr_to_ps_and_ps_to_sr", "sr_runtime_entity", "ps_organism",
        "lane_owned_api_with_compatibility_fallback",
        "ps_health_setter_or_compat_attribute;sr_health_setter_or_compat_attribute",
        "sr_state_and_ps_state",
        ("clamp_parity", "shared_tick_authority", "replay_trace"),
    ),
    "max_energy": _FieldOwnerDefinition(
        "creation_only", "sr_to_ps", "sr_runtime_entity", "ps_organism_constructor",
        "ps_constructor", "ps_organism_constructor_seed", "creation_only",
        ("capacity_owner_policy", "persistence", "replay_trace"),
    ),
    "max_health": _FieldOwnerDefinition(
        "creation_only", "sr_to_ps", "sr_runtime_entity", "ps_organism_constructor",
        "ps_constructor", "ps_organism_constructor_seed", "creation_only",
        ("capacity_owner_policy", "persistence", "replay_trace"),
    ),
    "size_radius": _FieldOwnerDefinition(
        "covered", "sr_to_ps_and_ps_to_sr", "sr_runtime_entity", "ps_organism",
        "lane_owned_api_with_compatibility_fallback",
        "ps_radius_setter;sr_size_and_radius_setter_or_compat_attribute",
        "sr_state_and_ps_state",
        ("field_parity", "shared_tick_authority", "replay_trace"),
    ),
    "velocity_acceleration": _FieldOwnerDefinition(
        "covered", "sr_to_ps_and_ps_to_sr", "sr_runtime_entity", "ps_organism",
        "lane_owned_api_with_compatibility_fallback",
        "ps_restore_motion_state_or_vector_setters;sr_vector_setters_or_compat_attribute",
        "sr_state_and_ps_state",
        ("integrator_owner_policy", "shared_tick_authority", "replay_trace"),
    ),
    "developmental_profile": _FieldOwnerDefinition(
        "partial", "spawn_request_to_ps", "sr_spawn_descriptor", "ps_organism_constructor",
        "ps_profile_api", "ps_spawn_profile_application", "spawn_only",
        ("runtime_lifecycle_owner", "inheritance_parity", "persistence"),
    ),
    "social_enabled": _FieldOwnerDefinition(
        "partial", "spawn_request_to_ps", "sr_spawn_descriptor", "ps_organism_constructor",
        "ps_profile_api", "ps_spawn_profile_application", "spawn_only",
        ("runtime_lifecycle_owner", "inheritance_parity", "persistence"),
    ),
    "active_visible_state": _FieldOwnerDefinition(
        "partial", "sr_active_to_ps_and_ps_to_sr_active;sr_visible_only",
        "sr_runtime_entity", "ps_organism",
        "lane_lifecycle_attributes_and_sr_presentation",
        "ps_active_attribute;sr_active_attribute;sr_visible_presentation_only",
        "lifecycle_partial",
        ("complete_lifecycle_mapping", "persistence", "replay_trace"),
    ),
    "render_identity": _FieldOwnerDefinition(
        "not_mapped", "none", "sr_render_adapter", None, "none", "none",
        "not_captured", ("render_authority", "asset_identity", "persistence"),
    ),
    "scripts": _FieldOwnerDefinition(
        "not_mapped", "none", "sr_script_registry", None, "none", "none",
        "diagnostic_receipts_only",
        ("script_lifecycle", "command_binding", "replay_trace"),
    ),
    "membrane_component_graph": _FieldOwnerDefinition(
        "not_mapped", "none", "sr_topology_owner", "ps_component_owner", "none", "none",
        "lane_local_only",
        ("shared_topology_owner", "live_mutation_transaction", "replay_trace"),
    ),
    "hierarchy": _FieldOwnerDefinition(
        "not_mapped", "none", "sr_topology_owner", "ps_hierarchy_owner", "none", "none",
        "lane_local_only",
        ("shared_hierarchy_owner", "persistence", "replay_trace"),
    ),
    "memory_genes": _FieldOwnerDefinition(
        "partial", "sr_to_ps_and_ps_to_sr_value_copy", "sr_memory_gene_store",
        "ps_inheritance_memory_store", "lane_gene_replace_api_with_value_copy",
        "memory_gene_value_copy_and_replace_api", "lane_local_partial",
        ("gene_identity", "inheritance_mutation_owner", "replay_trace"),
    ),
})


def _field_contract_record(name: str) -> dict[str, Any]:
    definition = _FIELD_OWNER_DEFINITIONS[name]
    family, admission_evidence = FIELD_ADMISSION_METADATA[name]
    return {
        "state": definition.state,
        "direction": definition.direction,
        "sr_owner": definition.sr_owner,
        "ps_owner": definition.ps_owner,
        "mutation_owner": definition.mutation_owner,
        "mutation_api": definition.mutation_api,
        "checkpoint_scope": definition.checkpoint_scope,
        "required_evidence": list(definition.required_evidence),
        "live_adapter_admitted": False,
        "live_mapper_paths": list(WORLD_BRIDGE_LIVE_MAPPER_PATHS[name]),
        "admission_family": family,
        "admission_required_evidence": list(admission_evidence),
    }


def build_worldbridge_mutation_owner_contract() -> dict[str, Any]:
    """Return the current owner and field mapping decision.

    This is a read-only contract.  ``worldbridge_coordinator`` owns ordering
    and validation only; it never owns the SR or PS values it translates.
    """
    fields = {
        name: _field_contract_record(name)
        for name in MAPPING_FIELDS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "authority_scope": "field_scoped_owner_registry_ordering_and_restore_compensation_candidate",
        "owners": {
            "sr_runtime_lane": {
                "root": "sr_runtime_entities",
                "owns": ["sr_runtime_entity_state", "sr_topology_owner", "sr_spawn_descriptor"],
                "mutation_entry": "owner_setter_or_runtime_restore_envelope",
            },
            "ps_runtime_lane": {
                "root": "ps_pond",
                "owns": ["ps_organism_state", "ps_hierarchy_owner", "ps_component_owner"],
                "mutation_entry": "pond_owner_api_or_in_place_restore",
            },
            "bridge_coordinator": {
                "root": "worldbridge_coordinator",
                "owns": ["ordering", "identity_binding_validation", "failure_compensation_order"],
                "must_not_own": ["sr_values", "ps_values", "lane_local_topology", "lane_rng_state"],
            },
        },
        "owner_roots": list(OWNER_ROOTS),
        "fields": fields,
        "owner_drift_policy": {
            "process_binding_schema_version": PROCESS_OWNER_BINDING_SCHEMA_VERSION,
            "capture_and_restore_same_roots_required": True,
            "replacement_root_is_compensatable": False,
            "drift_action": "fail_closed_without_claiming_compensation",
            "portable_object_identity": False,
        },
        "admissions": {
            "owner_binding": True,
            "field_scoped_live_mapping": False,
            "cross_lane_transaction": False,
            "rollback": False,
            "replay_admitted": False,
            "lossless": False,
            "default_ready": False,
        },
        "do_not_claim": [
            "unified_sr_ps_mutation_owner",
            "lossless_worldbridge_mapping",
            "cross_lane_transaction",
            "full_unified_runtime_replay",
            "unified_pond_default_ready",
        ],
    }


def validate_worldbridge_mutation_owner_contract(value: object) -> dict[str, Any]:
    """Validate the static contract and reject accidental admissions."""
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("authority_scope") != "field_scoped_owner_registry_ordering_and_restore_compensation_candidate":
        errors.append("authority_scope_mismatch")
    if tuple(value.get("owner_roots", ())) != OWNER_ROOTS:
        errors.append("owner_roots_mismatch")
    fields = value.get("fields")
    if not isinstance(fields, Mapping):
        errors.append("mapping_fields_mismatch")
    elif set(fields) != set(MAPPING_FIELDS):
        errors.append("mapping_fields_mismatch")
    if (
        set(FIELD_ADMISSION_METADATA) != set(MAPPING_FIELDS)
        or set(_FIELD_OWNER_DEFINITIONS) != set(MAPPING_FIELDS)
        or set(WORLD_BRIDGE_LIVE_MAPPER_PATHS) != set(MAPPING_FIELDS)
    ):
        errors.append("field_definition_inventory_mismatch")
    elif isinstance(fields, Mapping) and set(fields) == set(MAPPING_FIELDS):
        for name in MAPPING_FIELDS:
            item = fields.get(name)
            if not isinstance(item, Mapping):
                errors.append(f"field_{name}_invalid")
                continue
            state = item.get("state")
            direction = item.get("direction")
            mutation_api = item.get("mutation_api")
            mutation_owner = item.get("mutation_owner")
            if state not in _FIELD_STATES:
                errors.append(f"field_{name}_state_invalid")
            if not isinstance(direction, str) or not direction:
                errors.append(f"field_{name}_direction_invalid")
            if not isinstance(mutation_api, str) or not mutation_api:
                errors.append(f"field_{name}_mutation_api_invalid")
            if not isinstance(item.get("checkpoint_scope"), str) or not item.get("checkpoint_scope"):
                errors.append(f"field_{name}_checkpoint_scope_invalid")
            evidence = item.get("required_evidence")
            if not isinstance(evidence, list) or any(
                not isinstance(value, str) or not value for value in evidence
            ):
                errors.append(f"field_{name}_required_evidence_invalid")
            if item.get("sr_owner") is not None and not isinstance(item.get("sr_owner"), str):
                errors.append(f"field_{name}_sr_owner_invalid")
            if item.get("ps_owner") is not None and not isinstance(item.get("ps_owner"), str):
                errors.append(f"field_{name}_ps_owner_invalid")
            if mutation_owner not in {
                "none",
                "ps_constructor",
                "ps_profile_api",
                "lane_lifecycle_attributes_and_sr_presentation",
                "lane_gene_replace_api_with_value_copy",
                "lane_owned_api_with_compatibility_fallback",
            }:
                errors.append(f"field_{name}_mutation_owner_mismatch")
            if item.get("live_adapter_admitted") is not False:
                errors.append(f"field_{name}_admission_overclaim")
            if item.get("live_mapper_paths") != list(WORLD_BRIDGE_LIVE_MAPPER_PATHS[name]):
                errors.append(f"field_{name}_live_mapper_paths_mismatch")
            family, evidence = FIELD_ADMISSION_METADATA[name]
            if item.get("admission_family") != family:
                errors.append(f"field_{name}_admission_family_mismatch")
            if item.get("admission_required_evidence") != list(evidence):
                errors.append(f"field_{name}_admission_evidence_mismatch")
            if state == "not_mapped" and direction != "none":
                errors.append(f"field_{name}_unmapped_direction_mismatch")
            if direction == "none" and state != "not_mapped":
                errors.append(f"field_{name}_direction_without_mapping")
            expected = _field_contract_record(name)
            if set(item) != set(expected):
                errors.append(f"field_{name}_keys_mismatch")
            for key, expected_value in expected.items():
                if item.get(key) != expected_value:
                    errors.append(f"field_{name}_{key}_mismatch")
    policy = value.get("owner_drift_policy")
    if not isinstance(policy, Mapping):
        errors.append("owner_drift_policy_missing")
    else:
        if policy.get("process_binding_schema_version") != PROCESS_OWNER_BINDING_SCHEMA_VERSION:
            errors.append("owner_drift_process_binding_schema_version_mismatch")
        for name in ("capture_and_restore_same_roots_required", "replacement_root_is_compensatable", "portable_object_identity"):
            expected = True if name == "capture_and_restore_same_roots_required" else False
            if policy.get(name) is not expected:
                errors.append(f"owner_drift_{name}_mismatch")
        if policy.get("drift_action") != "fail_closed_without_claiming_compensation":
            errors.append("owner_drift_action_mismatch")
    owners = value.get("owners")
    if not isinstance(owners, Mapping) or set(owners) != {
        "sr_runtime_lane", "ps_runtime_lane", "bridge_coordinator"
    }:
        errors.append("owner_registry_invalid")
    else:
        expected_roots = {
            "sr_runtime_lane": "sr_runtime_entities",
            "ps_runtime_lane": "ps_pond",
            "bridge_coordinator": "worldbridge_coordinator",
        }
        for name, root in expected_roots.items():
            owner = owners.get(name)
            if not isinstance(owner, Mapping) or owner.get("root") != root:
                errors.append(f"owner_{name}_root_mismatch")
        coordinator = owners.get("bridge_coordinator")
        if isinstance(coordinator, Mapping):
            if set(coordinator.get("owns", ())) & {
                "sr_values", "ps_values", "lane_local_topology", "lane_rng_state"
            }:
                errors.append("coordinator_claims_lane_state_ownership")
            if set(coordinator.get("must_not_own", ())) != {
                "sr_values", "ps_values", "lane_local_topology", "lane_rng_state"
            }:
                errors.append("coordinator_owner_boundary_mismatch")
    admissions = value.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("admissions_missing")
    else:
        for name, expected in {
            "owner_binding": True,
            "field_scoped_live_mapping": False,
            "cross_lane_transaction": False,
            "rollback": False,
            "replay_admitted": False,
            "lossless": False,
            "default_ready": False,
        }.items():
            if admissions.get(name) is not expected:
                errors.append(f"admission_{name}_mismatch")
    return {"valid": not errors, "errors": errors}


def capture_process_owner_binding(
    *,
    runtime_epoch: object,
    roots: Mapping[str, object],
    sr_entities: Sequence[object] = (),
) -> dict[str, Any]:
    """Capture process-local object identities for one live operation."""
    if not isinstance(runtime_epoch, str) or not runtime_epoch.strip():
        raise ValueError("runtime_epoch must be a non-empty string")
    if set(roots) != set(OWNER_ROOTS):
        raise ValueError("owner binding roots mismatch")
    entity_bindings: list[dict[str, Any]] = []
    for entity in sr_entities:
        entity_id = getattr(entity, "id", None)
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise ValueError("SR owner binding entity id is invalid")
        entity_bindings.append({"entity_id": entity_id, "object_id": id(entity)})
    entity_bindings.sort(key=lambda item: item["entity_id"])
    return {
        "schema_version": PROCESS_OWNER_BINDING_SCHEMA_VERSION,
        "status": "worldbridge_process_owner_binding",
        "runtime_epoch": runtime_epoch,
        "process_instance_id": f"{os.getpid()}:{_PROCESS_INSTANCE_NONCE}",
        "portable": False,
        "roots": {
            name: (None if roots[name] is None else id(roots[name]))
            for name in OWNER_ROOTS
        },
        "sr_entity_bindings": entity_bindings,
    }


def validate_process_owner_binding(
    baseline: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    """Return explicit drift errors without attempting to repair the roots."""
    errors: list[str] = []
    for candidate, label in ((baseline, "baseline"), (current, "current")):
        if not isinstance(candidate, Mapping):
            errors.append(f"{label}_binding_invalid")
            continue
        if candidate.get("schema_version") != PROCESS_OWNER_BINDING_SCHEMA_VERSION:
            errors.append(f"{label}_schema_version_mismatch")
        if candidate.get("status") != "worldbridge_process_owner_binding":
            errors.append(f"{label}_status_mismatch")
        if not isinstance(candidate.get("process_instance_id"), str) or not candidate.get("process_instance_id"):
            errors.append(f"{label}_process_instance_id_missing")
        if candidate.get("portable") is not False:
            errors.append(f"{label}_portable_overclaim")
    if errors:
        return {"valid": False, "errors": errors}
    if baseline.get("runtime_epoch") != current.get("runtime_epoch"):
        errors.append("runtime_epoch_changed")
    if baseline.get("process_instance_id") != current.get("process_instance_id"):
        errors.append("process_instance_changed")
    baseline_roots = baseline.get("roots")
    current_roots = current.get("roots")
    if not isinstance(baseline_roots, Mapping) or not isinstance(current_roots, Mapping):
        errors.append("owner_roots_missing")
    elif set(baseline_roots) != set(OWNER_ROOTS) or set(current_roots) != set(OWNER_ROOTS):
        errors.append("owner_roots_keys_mismatch")
    else:
        for name in OWNER_ROOTS:
            if baseline_roots.get(name) != current_roots.get(name):
                errors.append(f"owner_root_changed:{name}")
    baseline_entities = baseline.get("sr_entity_bindings")
    current_entities = current.get("sr_entity_bindings")
    if not isinstance(baseline_entities, list) or not isinstance(current_entities, list):
        errors.append("sr_entity_owner_changed")
    elif len(baseline_entities) != len(current_entities):
        errors.append("sr_entity_owner_changed")
    else:
        if baseline_entities != current_entities:
            errors.append("sr_entity_owner_changed")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "FIELD_ADMISSION_METADATA",
    "MAPPING_FIELDS",
    "OWNER_ROOTS",
    "SCHEMA_VERSION",
    "STATUS",
    "WORLD_BRIDGE_LIVE_MAPPER_PATHS",
    "build_worldbridge_mutation_owner_contract",
    "capture_process_owner_binding",
    "validate_process_owner_binding",
    "validate_worldbridge_mutation_owner_contract",
]
