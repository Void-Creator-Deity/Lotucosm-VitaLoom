# -*- coding: utf-8 -*-
"""Focused E251 coverage for conceptual canonical-byte boundary drift audit."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    audit_worldbridge_quarantine_operator_presentation_status_projection,
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import (
    CONTRACT_KEY,
    E250_MODULE,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _e251_sources() -> dict[str, str]:
    return {
        E250_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: (_RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig"),
    }


def _e250_bytes() -> tuple[bytes, bytes]:
    sources = {
        "core.VitaLoom.commands.runtime_commands": (_RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
        "core.VitaLoom.commands.mcp_adapter": (_RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: (_RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig"),
    }
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}),
        mcp_adapter.get_runtime_worldbridge_status(),
        sources,
    )
    return encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250), _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract())


def test_boundary_audit_accepts_real_canonical_e250_evidence_and_registers_contract() -> None:
    e250_audit, e250_contract = _e250_bytes()
    audit = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, _e251_sources())
    assert audit["contract_drift_free"] is True
    assert audit["cross_process_read_only_boundary_valid"] is True
    assert audit["actual_process_started"] is False
    assert audit["ipc_transport_created"] is False
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit) == {"valid": True, "errors": []}
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit)) == audit

    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert "quarantine_operator_presentation_status_projection_boundary_audit_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

    isolated = copy.deepcopy(audit)
    e250_audit = b"{}"
    assert audit == isolated


def test_boundary_audit_fails_closed_for_contract_json_policy_and_source_drift() -> None:
    e250_audit, e250_contract = _e250_bytes()
    sources = _e251_sources()

    with pytest.raises(ValueError, match="non-canonical"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, json.dumps(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(), indent=2).encode(), sources)
    with pytest.raises(ValueError, match="invalid canonical E250 contract"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, b'{"x":1,"x":1}', sources)

    stale = json.loads(e250_contract)
    stale["static_policies"]["default_ready"] = True
    with pytest.raises(ValueError, match="invalid E250 contract"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, _canonical(stale), sources)

    bad_sources = dict(sources)
    bad_sources[E250_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="boundary source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, bad_sources)

    bad_status_sources = dict(sources)
    bad_status_sources[STATUS_MODULE] = bad_status_sources[STATUS_MODULE].replace(CONTRACT_KEY, "failure_wrong_contract", 1)
    with pytest.raises(ValueError, match="boundary source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, bad_status_sources)

    valid = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit, e250_contract, sources)
    tampered = copy.deepcopy(valid)
    tampered["ipc_transport_created"] = True
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(tampered)["valid"] is False
