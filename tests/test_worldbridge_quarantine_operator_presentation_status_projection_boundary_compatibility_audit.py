# -*- coding: utf-8 -*-
"""Focused E252 coverage for deterministic E251 evidence provenance compatibility."""
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
    E250_MODULE,
    STATUS_MODULE,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import (
    CONTRACT_KEY,
    E251_MODULE,
    MODULE_ID,
    REQUIRED_UNITS,
    audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

_RUNTIME = Path(__file__).resolve().parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _e252_sources() -> dict[str, str]:
    return {
        E251_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: (_RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py").read_text(encoding="utf-8-sig"),
    }


def _e251_bytes() -> tuple[bytes, bytes]:
    status_path = _RUNTIME / "core/VitaLoom/simulation/runtime_worldbridge_status.py"
    e250_sources = {
        "core.VitaLoom.commands.runtime_commands": (_RUNTIME / "core/VitaLoom/commands/runtime_commands.py").read_text(encoding="utf-8-sig"),
        "core.VitaLoom.commands.mcp_adapter": (_RUNTIME / "core/VitaLoom/commands/mcp_adapter.py").read_text(encoding="utf-8-sig"),
        STATUS_MODULE: status_path.read_text(encoding="utf-8-sig"),
    }
    e250 = audit_worldbridge_quarantine_operator_presentation_status_projection(
        reset_command_registry().run("runtime.worldbridge.status", {}),
        mcp_adapter.get_runtime_worldbridge_status(),
        e250_sources,
    )
    e251 = audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(
        encode_worldbridge_quarantine_operator_presentation_status_projection_audit(e250),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract()),
        {
            E250_MODULE: (_RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py").read_text(encoding="utf-8-sig"),
            STATUS_MODULE: e250_sources[STATUS_MODULE],
        },
    )
    return (
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251),
        _canonical(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract()),
    )


def _audit() -> dict[str, object]:
    e251_audit, e251_contract = _e251_bytes()
    return audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(
        e251_audit, e251_contract, _e252_sources(), REQUIRED_UNITS
    )


def test_compatibility_audit_is_deterministic_round_trippable_and_status_registered() -> None:
    first = _audit()
    second = _audit()
    assert first == second
    assert encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(first) == encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(second)
    assert first["deterministic_compatibility_valid"] is True
    assert first["source_order"] == list(REQUIRED_UNITS)
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(first) == {"valid": True, "errors": []}
    assert decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(first)) == first

    contract = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract(contract) == {"valid": True, "errors": []}
    status = build_runtime_worldbridge_status()
    assert status[CONTRACT_KEY] == contract
    assert MODULE_ID in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_compatibility_audit_fails_closed_for_e251_contract_json_and_source_order_drift() -> None:
    e251_audit, e251_contract = _e251_bytes()
    sources = _e252_sources()

    drift = json.loads(e251_contract)
    drift["static_policies"]["default_ready"] = True
    with pytest.raises(ValueError, match="invalid E251 contract|drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, _canonical(drift), sources, REQUIRED_UNITS)
    with pytest.raises(ValueError, match="non-canonical"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, json.dumps(json.loads(e251_contract), ensure_ascii=False, indent=2).encode("utf-8"), sources, REQUIRED_UNITS)
    duplicate = b'{"schema_version":1,"schema_version":1}'
    with pytest.raises(ValueError, match="invalid canonical E251 contract"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, duplicate, sources, REQUIRED_UNITS)
    with pytest.raises(ValueError, match="source order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, sources, tuple(reversed(REQUIRED_UNITS)))
    with pytest.raises(ValueError, match="source order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, sources, (REQUIRED_UNITS[0], REQUIRED_UNITS[0]))
    with pytest.raises(ValueError, match="source order drift"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, sources, (*REQUIRED_UNITS, "extra.unit"))


def test_compatibility_audit_fails_closed_for_forbidden_source_edges_and_invalid_result() -> None:
    e251_audit, e251_contract = _e251_bytes()
    sources = _e252_sources()
    forbidden_e251 = dict(sources)
    forbidden_e251[E251_MODULE] += "\nimport subprocess\n"
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, forbidden_e251, REQUIRED_UNITS)

    registration_drift = dict(sources)
    registration_drift[STATUS_MODULE] = registration_drift[STATUS_MODULE].replace(CONTRACT_KEY, "contract_key_drift", 1)
    with pytest.raises(ValueError, match="source topology invalid"):
        audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(e251_audit, e251_contract, registration_drift, REQUIRED_UNITS)

    tampered = copy.deepcopy(_audit())
    tampered["deterministic_compatibility_valid"] = False
    assert validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(tampered)["valid"] is False
    with pytest.raises(ValueError, match="invalid compatibility audit"):
        encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(tampered)
