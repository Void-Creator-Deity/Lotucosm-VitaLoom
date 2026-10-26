# -*- coding: utf-8 -*-
"""WorldBridge mapping-loss audit for Phase 6D."""
from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


def test_mapping_audit_names_current_coverage_and_losses() -> None:
    audit = build_worldbridge_mapping_audit()

    assert audit["schema_version"] == 1
    assert audit["read_only"] is True
    assert audit["lossless"] is False
    assert audit["default_ready"] is False
    assert audit["fields"]["position"]["state"] == "covered"
    assert audit["fields"]["energy"]["state"] == "covered"
    assert audit["fields"]["health"]["state"] == "covered"
    assert audit["fields"]["size_radius"]["state"] == "covered"
    assert audit["fields"]["membrane_component_graph"]["state"] == "not_mapped"
    assert "lossless_worldbridge_mapping" in audit["do_not_claim"]


def test_mapping_audit_includes_component_decision_summary() -> None:
    audit = build_worldbridge_mapping_audit()

    decision = audit["component_mapping_decision"]
    assert decision["status"] == "worldbridge_component_membrane_decision"
    assert decision["maps_live_components"] is False
    assert decision["decision"] == "read_only_projection_only"


def test_mapping_audit_includes_component_projection_summary() -> None:
    audit = build_worldbridge_mapping_audit()

    projection = audit["component_projection"]
    assert projection["status"] == "worldbridge_component_projection"
    assert projection["projection_state"] == "read_only_projection"
    assert projection["maps_live_components"] is False
    assert projection["default_ready"] is False
