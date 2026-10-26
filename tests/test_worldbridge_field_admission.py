from __future__ import annotations

from core.Lotucosm.runtime.world_bridge_field_admission import (
    build_worldbridge_field_admission_matrix,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


def test_matrix_covers_every_mapping_audit_field_and_denies_live_adapter() -> None:
    matrix = build_worldbridge_field_admission_matrix()
    expected = {
        "position", "energy", "health", "size_radius", "velocity_acceleration",
        "max_energy", "max_health", "developmental_profile", "social_enabled",
        "active_visible_state", "render_identity", "scripts",
        "membrane_component_graph", "hierarchy", "memory_genes",
    }
    assert set(matrix["fields"]) == expected
    assert matrix["live_adapter_admitted"] is False
    assert all(item["live_adapter_admitted"] is False for item in matrix["fields"].values())


def test_matrix_is_explicit_about_current_gaps_and_required_evidence() -> None:
    matrix = build_worldbridge_field_admission_matrix()
    assert matrix["fields"]["position"]["current_state"] == "covered"
    assert matrix["fields"]["scripts"]["current_state"] == "not_mapped"
    assert matrix["fields"]["scripts"]["authority"] == "unresolved"
    assert "script_lifecycle" in matrix["fields"]["scripts"]["required_evidence"]
    assert matrix["unified_undo_redo_runtime"] is False


def test_matrix_does_not_overclaim_worldbridge_readiness() -> None:
    matrix = build_worldbridge_field_admission_matrix()
    assert matrix["read_only"] is True
    assert matrix["default_ready"] is False
    assert "lossless_worldbridge_mapping" in matrix["do_not_claim"]

def test_admission_matrix_stays_aligned_with_mapping_audit() -> None:
    matrix = build_worldbridge_field_admission_matrix()
    audit = build_worldbridge_mapping_audit()
    assert set(matrix["fields"]) == set(audit["fields"])
    for name, field in audit["fields"].items():
        assert matrix["fields"][name]["current_state"] == field["state"]
        assert matrix["fields"][name]["direction"] == field["direction"]
from core.Lotucosm.runtime.world_bridge_field_admission import (
    build_worldbridge_field_admission_verification,
)


def test_blocker_verifier_keeps_every_field_out_of_live_adapter() -> None:
    result = build_worldbridge_field_admission_verification()
    assert result["read_only"] is True
    assert result["all_fields_blocked"] is True
    assert result["live_adapter_admitted"] is False
    assert result["admitted_fields"] == []
    assert set(result["blocked_fields"]) == set(result["fields"])


def test_blocker_verifier_does_not_promote_descriptor_evidence_to_live_evidence() -> None:
    result = build_worldbridge_field_admission_verification()
    assert result["evidence_catalog"]["connection_order"]["proven"] is False
    assert result["evidence_catalog"]["pond_round_trip"]["proven"] is True
    assert "replay_trace" in result["fields"]["velocity_acceleration"]["missing_evidence"]
    assert "script_lifecycle" in result["fields"]["scripts"]["missing_evidence"]
