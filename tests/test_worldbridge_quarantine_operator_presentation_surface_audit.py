# -*- coding: utf-8 -*-
"""Focused E246 coverage for bounded command/MCP/Inspector operator presentation parity."""
from __future__ import annotations

import copy

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import (
    VISIBLE_FIELD_IDS,
    audit_worldbridge_quarantine_operator_presentation_surfaces,
    build_worldbridge_quarantine_operator_presentation_surface_audit_contract,
    validate_worldbridge_quarantine_operator_presentation_surface_audit,
    validate_worldbridge_quarantine_operator_presentation_surface_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import (
    build_worldbridge_quarantine_operator_evidence_bundle_view_model,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    export_worldbridge_quarantine_operator_presentation,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    audit_worldbridge_quarantine_operator_presentation_export,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import (
    consume_worldbridge_quarantine_operator_evidence_pair,
)


def _bundle() -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available", "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界", "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False, "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
                             "disposal_recorded": True, "disposal_boundary": "simulation_stop",
                             "fresh_instance_boundary_observed": True},
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "do_not_claim": list(DO_NOT_CLAIM),
    }
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    return consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)

def _surfaces() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    bundle = _bundle()
    command_result: dict[str, object] = {"ok": True, "result": copy.deepcopy(bundle), "warnings": ["bounded"]}
    mcp_result: dict[str, object] = {"ok": True, "result": copy.deepcopy(bundle), "warnings": ["bounded"]}
    inspector_view = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command_result).to_dict()
    return command_result, mcp_result, inspector_view


def test_surface_audit_enforces_exact_bounded_command_mcp_inspector_parity() -> None:
    command_result, mcp_result, inspector_view = _surfaces()
    audit = audit_worldbridge_quarantine_operator_presentation_surfaces(command_result, mcp_result, inspector_view)
    assert validate_worldbridge_quarantine_operator_presentation_surface_audit(audit) == {"valid": True, "errors": []}
    assert audit["visible_field_ids"] == list(VISIBLE_FIELD_IDS)
    assert audit["command_mcp_parity_valid"] is True
    assert audit["inspector_parity_valid"] is True
    assert audit["inspector_fields_editable"] is False
    for key in ("same_adapter_only", "opaque_lifecycle_values_exposed", "runtime_action_authority", "ui_authority", "default_ready"):
        assert audit[key] is (True if key == "same_adapter_only" else False)


def test_surface_audit_rejects_mismatch_editability_and_raw_lifecycle_leakage() -> None:
    command_result, mcp_result, inspector_view = _surfaces()
    mismatch = copy.deepcopy(mcp_result)
    mismatch["result"]["headline"] = "mismatch"
    with pytest.raises(ValueError, match="invalid evidence bundle|digest mismatch"):
        audit_worldbridge_quarantine_operator_presentation_surfaces(command_result, mismatch, inspector_view)

    editable = copy.deepcopy(inspector_view)
    editable["section"]["fields"][0]["editable"] = True
    with pytest.raises(ValueError, match="editability mismatch"):
        audit_worldbridge_quarantine_operator_presentation_surfaces(command_result, mcp_result, editable)

    leaked = copy.deepcopy(command_result)
    leaked["warnings"].append("normal")
    leaked["sr_runtime_epoch"] = "epoch-secret"
    with pytest.raises(ValueError, match="raw lifecycle key"):
        audit_worldbridge_quarantine_operator_presentation_surfaces(leaked, mcp_result, inspector_view)


def test_surface_contract_status_and_mcp_are_read_only_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = build_worldbridge_quarantine_operator_presentation_surface_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_surface_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_surface_audit_contract"] == contract
    assert "quarantine_operator_presentation_surface_audit_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

    captured: list[tuple[str, dict[str, object]]] = []
    def fake_run(command_id: str, payload: dict[str, object]) -> dict[str, object]:
        captured.append((command_id, payload))
        return {"ok": True, "result": {"bounded": True}}
    monkeypatch.setattr(mcp_adapter, "run_command", fake_run)
    assert mcp_adapter.get_runtime_worldbridge_quarantine_operator_evidence_bundle() == {"ok": True, "result": {"bounded": True}}
    assert captured == [("runtime.worldbridge.quarantine_operator_evidence_bundle", {})]


def test_surface_audit_validator_fails_closed_on_static_policy_overclaim() -> None:
    command_result, mcp_result, inspector_view = _surfaces()
    audit = audit_worldbridge_quarantine_operator_presentation_surfaces(command_result, mcp_result, inspector_view)
    invalid = copy.deepcopy(audit)
    invalid["runtime_action_authority"] = True
    assert validate_worldbridge_quarantine_operator_presentation_surface_audit(invalid)["valid"] is False


