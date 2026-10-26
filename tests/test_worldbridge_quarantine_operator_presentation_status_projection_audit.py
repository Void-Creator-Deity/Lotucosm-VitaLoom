# -*- coding: utf-8 -*-
"""Focused E250 coverage for the read-only WorldBridge status projection audit."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    COMMAND_ID,
    COMMAND_MODULE,
    CONSUMER_CONTRACT_KEY,
    MCP_MODULE,
    NON_CONSUMPTION_CONTRACT_KEY,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection,
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
_SOURCE_PATHS = {
    COMMAND_MODULE: "core/VitaLoom/commands/runtime_commands.py",
    MCP_MODULE: "core/VitaLoom/commands/mcp_adapter.py",
    STATUS_MODULE: "core/VitaLoom/simulation/runtime_worldbridge_status.py",
}


def _production_units() -> dict[str, str]:
    return {
        name: (_RUNTIME / relative_path).read_text(encoding="utf-8-sig")
        for name, relative_path in _SOURCE_PATHS.items()
    }


def _production_envelopes() -> tuple[dict[str, object], dict[str, object]]:
    command = reset_command_registry().run(COMMAND_ID, {})
    mcp = mcp_adapter.get_runtime_worldbridge_status()
    assert command["ok"] is True
    assert mcp["ok"] is True
    return command, mcp


def test_status_projection_audit_uses_existing_command_mcp_mirror_and_registers_contract() -> None:
    command, mcp = _production_envelopes()
    audit = audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, _production_units())

    assert audit["command_mcp_parity_valid"] is True
    assert audit["status_contract_projection_valid"] is True
    assert audit["source_topology_valid"] is True
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_audit(audit) == {"valid": True, "errors": []}
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_audit(
        encode_worldbridge_quarantine_operator_presentation_status_projection_audit(audit)
    ) == audit

    contract = build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_status_projection_audit_contract"] == contract
    assert "quarantine_operator_presentation_status_projection_audit_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

    isolated = copy.deepcopy(audit)
    command["result"]["runtime_mode"] = "tampered"
    assert audit == isolated


def test_mcp_helper_directly_forwards_only_existing_status_command(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run_command(command_id: str, payload: dict[str, object]) -> dict[str, object]:
        calls.append((command_id, copy.deepcopy(payload)))
        return {"ok": True, "result": {}}

    monkeypatch.setattr(mcp_adapter, "run_command", fake_run_command)
    assert mcp_adapter.get_runtime_worldbridge_status() == {"ok": True, "result": {}}
    assert mcp_adapter.get_runtime_worldbridge_status("workspace/demo") == {"ok": True, "result": {}}
    assert calls == [
        (COMMAND_ID, {}),
        (COMMAND_ID, {"project_path": "workspace/demo"}),
    ]


def test_status_projection_audit_fails_closed_for_drift_leaks_and_noncanonical_json() -> None:
    command, mcp = _production_envelopes()
    units = _production_units()

    mismatched_mcp = copy.deepcopy(mcp)
    mismatched_mcp["result"]["default_ready"] = True
    with pytest.raises(ValueError, match="default boundary mismatch"):
        audit_worldbridge_quarantine_operator_presentation_status_projection(command, mismatched_mcp, units)

    leaked_command = copy.deepcopy(command)
    leaked_command["result"]["receipt"] = {"opaque": True}
    with pytest.raises(ValueError, match="raw receipt input"):
        audit_worldbridge_quarantine_operator_presentation_status_projection(leaked_command, mcp, units)

    tampered_command = copy.deepcopy(command)
    tampered_mcp = copy.deepcopy(mcp)
    for envelope in (tampered_command, tampered_mcp):
        envelope["result"][CONSUMER_CONTRACT_KEY]["replay_exclusion_facts"]["receipt_is_not_replay_input"] = False
    with pytest.raises(ValueError, match="invalid receipt consumer contract"):
        audit_worldbridge_quarantine_operator_presentation_status_projection(tampered_command, tampered_mcp, units)

    operation_source = dict(units)
    operation_source[COMMAND_MODULE] = operation_source[COMMAND_MODULE].replace(
        "return command_ok(build_runtime_worldbridge_status(project_path=project_path))",
        "consume_worldbridge_quarantine_operator_presentation_receipt(None)\n    return command_ok(build_runtime_worldbridge_status(project_path=project_path))",
        1,
    )
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, operation_source)

    wrong_route_source = dict(units)
    wrong_route_source[MCP_MODULE] = wrong_route_source[MCP_MODULE].replace(COMMAND_ID, "runtime.worldbridge.mutate", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, wrong_route_source)

    audit = audit_worldbridge_quarantine_operator_presentation_status_projection(command, mcp, units)
    with pytest.raises(ValueError, match="invalid canonical status projection audit"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_audit(b'{"status":1,"status":1}')
    with pytest.raises(ValueError, match="non-canonical"):
        decode_worldbridge_quarantine_operator_presentation_status_projection_audit(
            json.dumps(audit, ensure_ascii=False, indent=2).encode("utf-8")
        )
    tampered_audit = copy.deepcopy(audit)
    tampered_audit["quarantine_clear_admitted"] = True
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_audit(tampered_audit)["valid"] is False
