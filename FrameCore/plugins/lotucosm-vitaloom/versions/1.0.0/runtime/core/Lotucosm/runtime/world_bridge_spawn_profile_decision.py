# -*- coding: utf-8 -*-
"""Read-only WorldBridge spawned developmental/social profile decision."""
from __future__ import annotations

from typing import Any


def build_worldbridge_spawn_profile_decision() -> dict[str, Any]:
    """Describe the reviewed spawn-request-only profile boundary."""
    return {
        "schema_version": 1,
        "status": "worldbridge_spawn_profile_authority_decision",
        "read_only": True,
        "decision": "spawn_request_seed_only",
        "default_ready": False,
        "fields": {
            "developmental_profile": {
                "mapping_state": "partial",
                "direction": "spawn_request_to_ps",
                "continuous_sync": False,
            },
            "social_enabled": {
                "mapping_state": "partial",
                "direction": "spawn_request_to_ps",
                "continuous_sync": False,
            },
        },
        "sr_authority": [
            "spawn_request_script_properties",
            "scene_descriptor_and_inspector_command_binding",
            "pond_scene_persistence",
        ],
        "ps_authority": [
            "organism_developmental_stage_and_counters",
            "social_learning_runtime_gate_and_memory_genes",
            "inheritance_reset_and_social_memory_transfer",
            "pond_runtime_persistence",
        ],
        "allowed_bridge_behavior": [
            "extract_spawn_request_profile",
            "initialize_new_ps_organism_profile",
            "write_developmental_stage_to_sr_debug_hud",
        ],
        "forbidden_behavior": [
            "per_tick_developmental_profile_copy",
            "per_tick_social_enabled_copy",
            "sr_descriptor_rewrite_from_ps_runtime_state",
            "bridge_control_of_ps_inheritance_or_social_memory",
        ],
        "unblock_requirements": [
            "field_level_sr_and_ps_lifecycle_contract",
            "inspector_and_registry_command_binding_policy",
            "pond_and_scene_persistence_round_trip",
            "inheritance_mutation_and_social_memory_parity",
            "deterministic_replay_and_tick_order_evidence",
        ],
        "do_not_claim": [
            "continuous_developmental_profile_synchronization",
            "continuous_social_enabled_synchronization",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "full_unified_runtime_replay",
        ],
    }
