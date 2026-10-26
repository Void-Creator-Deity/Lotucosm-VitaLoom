# -*- coding: utf-8 -*-
"""Read-only WorldBridge component projection for Phase 6F."""
from __future__ import annotations

import json

from core.Lotucosm.runtime.world_bridge_component_projection import (
    build_worldbridge_component_projection_diagnostics,
    build_worldbridge_component_projection,
    project_worldbridge_component,
)


class _ForbiddenBehaviorComponent:
    id = "membrane_1"
    component_type = "membrane"
    location = "external"
    acquired = False
    congenital = True
    attach_point = "cell_wall"
    radius = 42.0
    ingest_threshold = 0.35
    efficiency = 1.25
    connections = [object(), object()]

    def get_inspectable_properties(self) -> dict:
        return {
            "radius": {"value": self.radius, "type": float, "attributes": {"min": 10.0}},
            "efficiency": {"value": self.efficiency, "type": float, "attributes": {}},
        }

    def update(self, *_args, **_kwargs) -> None:
        raise AssertionError("update must not be called by projection")

    def sense(self, *_args, **_kwargs) -> None:
        raise AssertionError("sense must not be called by projection")

    def process_signal(self, *_args, **_kwargs) -> None:
        raise AssertionError("process_signal must not be called by projection")

    def auto_ingest(self, *_args, **_kwargs) -> None:
        raise AssertionError("auto_ingest must not be called by projection")

    def mutate(self, *_args, **_kwargs) -> None:
        raise AssertionError("mutate must not be called by projection")

    def add_connection(self, *_args, **_kwargs) -> None:
        raise AssertionError("add_connection must not be called by projection")


def test_project_component_reads_safe_fields_without_live_behavior() -> None:
    projected = project_worldbridge_component(_ForbiddenBehaviorComponent())

    assert projected["projection_state"] == "read_only_projection"
    assert projected["maps_live_components"] is False
    assert projected["component_id"] == "membrane_1"
    assert projected["component_type"] == "membrane"
    assert projected["location"] == "external"
    assert projected["acquired"] is False
    assert projected["congenital"] is True
    assert projected["attach_point"] == "cell_wall"
    assert projected["connection_count"] == 2
    assert projected["component_fields"]["radius"] == 42.0
    assert projected["component_fields"]["ingest_threshold"] == 0.35
    assert projected["component_fields"]["efficiency"] == 1.25
    assert projected["inspectable_properties"]["radius"]["type"] == "float"
    assert "connections" not in projected
    json.dumps(projected, ensure_ascii=False)


def test_projection_accepts_status_dictionaries_and_stays_json_serializable() -> None:
    status = {
        "id": "sensor_1",
        "component_type": "sensor",
        "location": "external",
        "acquired": True,
        "congenital": False,
        "attach_point": "front",
        "connection_count": 3,
        "inspectable_properties": {
            "sensing_range": {"value": 75.0, "type": float, "attributes": {}},
        },
        "signal_threshold": 0.6,
        "sensing_range": 75.0,
        "connections": [object()],
    }

    projected = project_worldbridge_component(status)

    assert projected["component_id"] == "sensor_1"
    assert projected["component_type"] == "sensor"
    assert projected["connection_count"] == 3
    assert projected["component_fields"]["signal_threshold"] == 0.6
    assert projected["component_fields"]["sensing_range"] == 75.0
    assert "connections" not in projected
    json.dumps(projected, ensure_ascii=False)


def test_build_projection_summarizes_coverage_without_default_readiness() -> None:
    projection = build_worldbridge_component_projection(
        [_ForbiddenBehaviorComponent(), {"id": "act_1", "component_type": "actuator", "energy_cost": 4.0}]
    )

    assert projection["schema_version"] == 1
    assert projection["read_only"] is True
    assert projection["maps_live_components"] is False
    assert projection["default_ready"] is False
    assert projection["projection_state"] == "read_only_projection"
    assert projection["component_count"] == 2
    assert projection["coverage"]["membrane"] == 1
    assert projection["coverage"]["actuator"] == 1
    assert "live_component_graph_mapping" in projection["do_not_claim"]
    json.dumps(projection, ensure_ascii=False)


def test_projection_diagnostics_summarize_readonly_evidence_without_mutating_input() -> None:
    projection = build_worldbridge_component_projection(
        [_ForbiddenBehaviorComponent(), {"id": "act_1", "component_type": "actuator", "energy_cost": 4.0}]
    )
    before = json.dumps(projection, ensure_ascii=False, sort_keys=True)

    diagnostics = build_worldbridge_component_projection_diagnostics(projection)

    assert json.dumps(projection, ensure_ascii=False, sort_keys=True) == before
    assert diagnostics["schema_version"] == 1
    assert diagnostics["status"] == "worldbridge_component_projection_diagnostics"
    assert diagnostics["diagnostic_state"] == "read_only_projection_diagnostics"
    assert diagnostics["read_only"] is True
    assert diagnostics["maps_live_components"] is False
    assert diagnostics["default_ready"] is False
    assert diagnostics["component_count"] == 2
    assert diagnostics["coverage"] == {"actuator": 1, "membrane": 1}
    assert "component_type" in diagnostics["safe_projection_fields"]
    assert "auto_ingest" in diagnostics["forbidden_behavior"]
    assert "live_component_graph_mapping" in diagnostics["do_not_claim"]
    assert "components" not in diagnostics
    json.dumps(diagnostics, ensure_ascii=False)
