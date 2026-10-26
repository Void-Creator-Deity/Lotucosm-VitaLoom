# -*- coding: utf-8 -*-
"""Focused E249 coverage for status-only receipt-consumer non-consumption."""
from __future__ import annotations

import copy
import json

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer import (
    STATUS as CONSUMER_STATUS,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit import (
    REGISTRATION_SYMBOL,
    STATUS,
    STATUS_MODULE,
    TARGET_MODULE,
    audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption,
    build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
    decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit,
    encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit,
    validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption,
    validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _units() -> dict[str, str]:
    return {
        TARGET_MODULE: "def consume_worldbridge_quarantine_operator_presentation_receipt(value): return value\n",
        STATUS_MODULE: f"from {TARGET_MODULE} import {REGISTRATION_SYMBOL}\ndef build_runtime_worldbridge_status(): return {{{REGISTRATION_SYMBOL!r}: {REGISTRATION_SYMBOL}()}}\n",
        "core.VitaLoom.viewports.game_viewport": "class GameViewport: pass\n",
        "core.VitaLoom.commands.runtime_commands": "def _runtime_worldbridge_status(payload, context): return None\n",
        "core.VitaLoom.commands.mcp_adapter": "def get_runtime_worldbridge_status(project_path=''): return None\n",
        "core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle": "def build_view_model(value): return value\n",
    }


def test_non_consumption_audit_canonical_round_trip_and_source_binding() -> None:
    units = _units()
    audit = audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(units)
    assert audit["non_consumption_valid"] is True
    assert audit["registration_edges"] == [{"module": STATUS_MODULE, "symbol": REGISTRATION_SYMBOL}]
    assert audit["forbidden_edges"] == []
    assert validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(audit, source_units=units) == {"valid": True, "errors": []}
    encoded = encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(audit)
    assert decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(encoded) == audit
    units[TARGET_MODULE] = "def consume_worldbridge_quarantine_operator_presentation_receipt(value): return {'changed': value}\n"
    assert audit["source_unit_digest"] != audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(units)["source_unit_digest"]


def test_non_consumption_audit_rejects_forbidden_import_and_call() -> None:
    units = _units()
    units["core.VitaLoom.viewports.game_viewport"] = (
        f"from {TARGET_MODULE} import consume_worldbridge_quarantine_operator_presentation_receipt\n"
        "class GameViewport:\n"
        "    def tick(self, value):\n"
        "        return consume_worldbridge_quarantine_operator_presentation_receipt(value)\n"
    )
    audit = audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(units)
    assert audit["non_consumption_valid"] is False
    assert any("game_viewport" in edge for edge in audit["forbidden_edges"])
    tampered = copy.deepcopy(audit)
    tampered["non_consumption_valid"] = True
    tampered["audit_digest"] = "0" * 64
    assert validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(tampered)["valid"] is False
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(b'{"status":1,"status":1}')
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(json.dumps(audit, indent=2).encode("utf-8"))


def test_non_consumption_contract_and_status_registration() -> None:
    contract = build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract()
    assert validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_consumer_non_consumption_audit_contract"] == contract
    assert "quarantine_operator_presentation_consumer_non_consumption_audit_module" in status["pilot_modules"]
    assert CONSUMER_STATUS == "worldbridge_quarantine_operator_presentation_receipt_consumer"
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
