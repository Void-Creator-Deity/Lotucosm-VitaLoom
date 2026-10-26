"""Evidence classification for hierarchy and membrane topology mapping."""
from __future__ import annotations

from typing import Any


def build_worldbridge_topology_mapping_audit() -> dict[str, Any]:
    """Separate SR structure persistence from cross-lane topology authority."""
    fields = {
        "sr_structure_fingerprint": {
            "state": "checkpoint_closed",
            "evidence": [
                "structural_edges",
                "signal_edges",
                "membrane_attach",
                "membrane_template",
                "restore_digest_comparison",
            ],
        },
        "ps_local_hierarchy": {
            "state": "local_owner_closed",
            "evidence": ["organism_component_parent_contract", "membrane_owner_contract"],
        },
        "component_hierarchy_projection": {
            "state": "read_only_projection",
            "evidence": ["explicit_component_identity_contract", "projection_validation"],
        },
        "sr_topology_live_owner": {
            "state": "live_owner_closed",
            "evidence": [
                "independent_topology_owner_state",
                "capture_restore_compensation",
                "fresh_host_portable_parity",
            ],
        },
        "membrane_behavior_boundary": {
            "state": "lane_local_isolated",
            "evidence": [
                "membrane_producer_binding",
                "ps_lane_live_usage",
                "cross_lane_call_absence",
                "falsifiable_behavior_scanner",
                "lane_local_roundtrip_contract",
                "sr_topology_owner_consumer_parity",
            ],
        },
        "cross_lane_hierarchy_authority": {
            "state": "not_admitted",
            "evidence": ["shared_topology_owner", "live_mutation_transaction", "replay_trace"],
        },
        "membrane_behavior_mapping": {
            "state": "not_admitted",
            "evidence": ["membrane_component_mapping", "cross_lane_behavior_authority", "replay_trace"],
        },
    }
    closed = [
        name for name, item in fields.items()
        if item["state"] in {"checkpoint_closed", "local_owner_closed"}
    ]
    live_owner_closed = [
        name for name, item in fields.items()
        if item["state"] == "live_owner_closed"
    ]
    lane_local_isolated = [
        name for name, item in fields.items()
        if item["state"] == "lane_local_isolated"
    ]
    return {
        "schema_version": 1,
        "status": "worldbridge_topology_mapping_audit",
        "read_only": True,
        "fields": fields,
        "topology_provenance_closed": len(closed) == 2,
        "sr_topology_live_owner_closed": len(live_owner_closed) == 1,
        "membrane_behavior_lane_local_isolated": len(lane_local_isolated) == 1,
        "lane_local_roundtrip": {
            "mode": "lane_local_roundtrip",
            "read_only": True,
            "sr_owner": "GameViewport.capture_sr_topology_owner_state/restore_sr_topology_owner_state",
            "ps_owner": "builtin.components.membrane.Membrane",
            "probe": "tools/check_worldbridge_e538_lane_local_roundtrip.py",
            "cross_lane_behavior_admitted": False,
            "tick_merge_admitted": False,
            "full_unified_replay_admitted": False,
        },
        "provenance_fields_closed": closed,
        "live_owner_fields_closed": live_owner_closed,
        "lane_local_fields_isolated": lane_local_isolated,
        "cross_lane_topology_admitted": False,
        "cross_lane_behavior_admitted": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "blockers": [
            "cross_lane_shared_topology_authority",
            "live_mutation_transaction",
            "membrane_component_mapping",
            "cross_lane_behavior_authority",
            "replay_trace",
        ],
        "do_not_claim": [
            "worldbridge_live_hierarchy_mapping",
            "worldbridge_live_membrane_mapping",
            "lossless_worldbridge_mapping",
            "unified_runtime_replay",
        ],
    }


__all__ = ["build_worldbridge_topology_mapping_audit"]