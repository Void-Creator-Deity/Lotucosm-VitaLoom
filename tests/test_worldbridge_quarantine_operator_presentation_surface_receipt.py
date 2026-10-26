# -*- coding: utf-8 -*-
"""Focused E247 regression coverage for canonical immutable surface-audit receipts."""
from __future__ import annotations

import copy
import json

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import DO_NOT_CLAIM, NEGATIVE_CAPABILITIES
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import export_worldbridge_quarantine_operator_presentation
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import audit_worldbridge_quarantine_operator_presentation_export
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import consume_worldbridge_quarantine_operator_evidence_pair
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import audit_worldbridge_quarantine_operator_presentation_surfaces
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import (
    MAX_RECEIPT_BYTES,
    build_worldbridge_quarantine_operator_presentation_surface_receipt_contract,
    decode_worldbridge_quarantine_operator_presentation_surface_receipt,
    encode_worldbridge_quarantine_operator_presentation_surface_receipt,
    export_worldbridge_quarantine_operator_presentation_surface_receipt,
    validate_worldbridge_quarantine_operator_presentation_surface_receipt,
    validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract,
)
from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import build_worldbridge_quarantine_operator_evidence_bundle_view_model
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _surface_audit() -> dict[str, object]:
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
    exported = export_worldbridge_quarantine_operator_presentation(presentation)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(exported, audit_worldbridge_quarantine_operator_presentation_export(exported))
    command = {"ok": True, "result": copy.deepcopy(bundle)}
    inspector = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command).to_dict()
    return audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), inspector)


def test_surface_receipt_canonical_round_trip_and_copy_isolation() -> None:
    source = _surface_audit()
    receipt = export_worldbridge_quarantine_operator_presentation_surface_receipt(source)
    assert validate_worldbridge_quarantine_operator_presentation_surface_receipt(receipt, surface_audit=source) == {"valid": True, "errors": []}
    encoded = encode_worldbridge_quarantine_operator_presentation_surface_receipt(receipt)
    assert len(encoded) <= MAX_RECEIPT_BYTES
    assert decode_worldbridge_quarantine_operator_presentation_surface_receipt(encoded) == receipt
    assert "epoch-secret" not in encoded.decode("utf-8")
    source["source_bundle_digest"] = "0" * 64
    assert receipt["source_bundle_digest"] != source["source_bundle_digest"]


def test_surface_receipt_rejects_tampered_source_noncanonical_and_duplicate_json() -> None:
    source = _surface_audit()
    receipt = export_worldbridge_quarantine_operator_presentation_surface_receipt(source)
    tampered = copy.deepcopy(receipt)
    tampered["runtime_action_authority"] = True
    assert validate_worldbridge_quarantine_operator_presentation_surface_receipt(tampered)["valid"] is False
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_surface_receipt(b'{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_surface_receipt(json.dumps(receipt, indent=2).encode("utf-8"))
    invalid_source = copy.deepcopy(source)
    invalid_source["ui_authority"] = True
    with pytest.raises(ValueError, match="invalid presentation surface audit"):
        export_worldbridge_quarantine_operator_presentation_surface_receipt(invalid_source)


def test_surface_receipt_contract_status_and_source_byte_path() -> None:
    source = _surface_audit()
    source_bytes = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt = export_worldbridge_quarantine_operator_presentation_surface_receipt(source_bytes)
    assert validate_worldbridge_quarantine_operator_presentation_surface_receipt(receipt, surface_audit=source_bytes) == {"valid": True, "errors": []}
    contract = build_worldbridge_quarantine_operator_presentation_surface_receipt_contract()
    assert validate_worldbridge_quarantine_operator_presentation_surface_receipt_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_surface_receipt_contract"] == contract
    assert "quarantine_operator_presentation_surface_receipt_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
