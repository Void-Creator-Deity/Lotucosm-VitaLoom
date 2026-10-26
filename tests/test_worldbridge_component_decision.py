# -*- coding: utf-8 -*-
"""WorldBridge component/membrane mapping decision for Phase 6E."""
from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)


def test_component_decision_names_safe_projection_and_forbidden_behavior() -> None:
    decision = build_worldbridge_component_decision()

    assert decision["schema_version"] == 1
    assert decision["read_only"] is True
    assert decision["maps_live_components"] is False
    assert decision["default_ready"] is False
    assert decision["decision"] == "read_only_projection_only"
    assert "component_type" in decision["safe_projection_fields"]
    assert "inspectable_properties" in decision["safe_projection_fields"]
    assert "auto_ingest" in decision["forbidden_behavior"]
    assert "process_signal" in decision["forbidden_behavior"]
    assert decision["component_kinds"]["Membrane"]["mapping_state"] == "decision_only"
