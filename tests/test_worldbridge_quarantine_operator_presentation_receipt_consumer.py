# -*- coding: utf-8 -*-
"""Focused E248 regression coverage for receipt-only replay exclusion."""
from __future__ import annotations

import copy
import json

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import DO_NOT_CLAIM, NEGATIVE_CAPABILITIES
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import export_worldbridge_quarantine_operator_presentation
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import audit_worldbridge_quarantine_operator_presentation_export
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import consume_worldbridge_quarantine_operator_evidence_pair
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import audit_worldbridge_quarantine_operator_presentation_surfaces
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_receipt import export_worldbridge_quarantine_operator_presentation_surface_receipt
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer import (
    MAX_CONSUMER_BYTES,
    build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
    consume_worldbridge_quarantine_operator_presentation_receipt,
    decode_worldbridge_quarantine_operator_presentation_receipt_consumer,
    encode_worldbridge_quarantine_operator_presentation_receipt_consumer,
    validate_worldbridge_quarantine_operator_presentation_receipt_consumer,
    validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _receipt() -> dict[str, object]:
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
    audited = audit_worldbridge_quarantine_operator_presentation_export(exported)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(exported, audited)
    command = {"ok": True, "result": copy.deepcopy(bundle)}
    inspector = {
        "available": True, "read_only": True,
        "scope": bundle["consumer_scope"],
        "authority_command_id": "runtime.worldbridge.quarantine_operator_evidence_bundle",
        "collapsed_by_default": True, "warnings": [], "error": None,
        "section": {"id": "worldbridge-quarantine-operator-evidence-bundle", "title": "x", "fields": []},
    }
    from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import build_worldbridge_quarantine_operator_evidence_bundle_view_model
    inspector = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command).to_dict()
    surface = audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), inspector)
    return export_worldbridge_quarantine_operator_presentation_surface_receipt(surface)


def test_consumer_canonical_round_trip_and_copy_isolation() -> None:
    receipt = _receipt()
    consumer = consume_worldbridge_quarantine_operator_presentation_receipt(receipt)
    assert validate_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer, receipt=receipt) == {"valid": True, "errors": []}
    encoded = encode_worldbridge_quarantine_operator_presentation_receipt_consumer(consumer)
    assert len(encoded) <= MAX_CONSUMER_BYTES
    assert decode_worldbridge_quarantine_operator_presentation_receipt_consumer(encoded) == consumer
    receipt["source_bundle_digest"] = "0" * 64
    assert consumer["source_bundle_digest"] != receipt["source_bundle_digest"]


def test_consumer_rejects_tampering_noncanonical_duplicate_nonfinite_and_raw_lifecycle() -> None:
    receipt = _receipt()
    consumer = consume_worldbridge_quarantine_operator_presentation_receipt(receipt)
    tampered = copy.deepcopy(consumer)
    tampered["replay_admitted"] = True
    assert validate_worldbridge_quarantine_operator_presentation_receipt_consumer(tampered)["valid"] is False
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_receipt_consumer(b'{"status":1,"status":1}')
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_receipt_consumer(json.dumps(consumer, indent=2).encode("utf-8"))
    raw = copy.deepcopy(consumer)
    raw["replay_exclusion_facts"] = {"sr_runtime_epoch": "opaque"}
    assert validate_worldbridge_quarantine_operator_presentation_receipt_consumer(raw)["valid"] is False
    with pytest.raises(ValueError):
        consume_worldbridge_quarantine_operator_presentation_receipt(b'{"schema_version":1,"status":"x","checkpoint_state":NaN}')


def test_consumer_contract_and_status_registration() -> None:
    contract = build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract()
    assert validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_receipt_consumer_contract"] == contract
    assert "quarantine_operator_presentation_receipt_consumer_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
