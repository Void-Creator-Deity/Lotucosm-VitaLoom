# -*- coding: utf-8 -*-
"""Read-only WorldBridge component/membrane mapping decision."""
from __future__ import annotations

from typing import Any


def build_worldbridge_component_decision() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "worldbridge_component_membrane_decision",
        "read_only": True,
        "decision": "read_only_projection_only",
        "maps_live_components": False,
        "default_ready": False,
        "safe_projection_fields": [
            "component_id",
            "component_type",
            "location",
            "acquired",
            "congenital",
            "attach_point",
            "inspectable_properties",
            "connection_count",
        ],
        "forbidden_behavior": [
            "update",
            "sense",
            "process_signal",
            "auto_ingest",
            "mutate",
            "add_connection",
            "live_connection_objects",
        ],
        "component_kinds": {
            "Membrane": {
                "mapping_state": "decision_only",
                "safe_projection_fields": [
                    "radius",
                    "ingest_threshold",
                    "efficiency",
                ],
                "forbidden_behavior": ["auto_ingest", "is_inside"],
            },
            "Sensor": {
                "mapping_state": "decision_only",
                "safe_projection_fields": ["signal_threshold", "sensing_range"],
                "forbidden_behavior": ["sense", "process_signal"],
            },
            "Actuator": {
                "mapping_state": "decision_only",
                "safe_projection_fields": ["energy_cost"],
                "forbidden_behavior": ["process_signal", "get_force_vector"],
            },
        },
        "do_not_claim": [
            "membrane_component_graph_mapping",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
        ],
    }
