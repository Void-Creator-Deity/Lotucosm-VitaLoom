# -*- coding: utf-8 -*-
"""Read-only WorldBridge maximum-capacity authority decision."""
from __future__ import annotations

from typing import Any


def build_worldbridge_capacity_decision() -> dict[str, Any]:
    """Describe the reviewed maximum energy/health transfer boundary."""
    return {
        "schema_version": 1,
        "status": "worldbridge_capacity_authority_decision",
        "read_only": True,
        "decision": "creation_seed_only",
        "default_ready": False,
        "fields": {
            "max_energy": {
                "mapping_state": "creation_only",
                "direction": "sr_to_ps",
                "continuous_sync": False,
            },
            "max_health": {
                "mapping_state": "creation_only",
                "direction": "sr_to_ps",
                "continuous_sync": False,
            },
        },
        "sr_authority": [
            "scene_descriptor_and_inspector_properties",
            "interoception_normalization",
            "sr_repair_and_health_commands",
        ],
        "ps_authority": [
            "organism_construction_and_health_clamp",
            "metabolism_and_energy_recovery_clamp",
            "reproduction_and_inheritance",
            "pond_serializer_round_trip",
        ],
        "forbidden_behavior": [
            "per_tick_sr_to_ps_capacity_copy",
            "per_tick_ps_to_sr_capacity_copy",
            "capacity_driven_current_value_repair",
            "capacity_driven_scene_descriptor_rewrite",
        ],
        "unblock_requirements": [
            "field_level_sr_and_ps_authority_contract",
            "inspector_and_command_binding_policy",
            "pond_and_scene_persistence_round_trip",
            "repair_and_clamp_parity",
            "deterministic_replay_and_tick_order_evidence",
        ],
        "do_not_claim": [
            "continuous_capacity_synchronization",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "full_unified_runtime_replay",
        ],
    }
