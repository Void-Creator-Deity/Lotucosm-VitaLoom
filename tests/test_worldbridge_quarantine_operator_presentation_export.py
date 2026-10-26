# -*- coding: utf-8 -*-
"""Focused E243 regression coverage for quarantine presentation export and audit."""
from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM as PRESENTATION_DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    MAX_EXPORT_BYTES,
    _export_digest,
    build_worldbridge_quarantine_operator_presentation_export_contract,
    decode_worldbridge_quarantine_operator_presentation_export_record,
    encode_worldbridge_quarantine_operator_presentation_export_record,
    export_worldbridge_quarantine_operator_presentation,
    validate_worldbridge_quarantine_operator_presentation_export_contract,
    validate_worldbridge_quarantine_operator_presentation_export_record,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    _audit_digest,
    audit_worldbridge_quarantine_operator_presentation_export,
    build_worldbridge_quarantine_operator_presentation_export_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_export_audit,
    encode_worldbridge_quarantine_operator_presentation_export_audit,
    validate_worldbridge_quarantine_operator_presentation_export_audit,
    validate_worldbridge_quarantine_operator_presentation_export_audit_contract,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

EXPORT_COMMAND = "runtime.worldbridge.quarantine_operator_presentation_export"
AUDIT_COMMAND = "runtime.worldbridge.quarantine_operator_presentation_export_audit"


def _presentation(*, available: bool = True) -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1,
        "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation",
        "read_only": True,
        "availability": "available" if available else "unavailable",
        "operator_state": "fresh_instance_boundary_observed" if available else "unavailable",
        "headline": "独立的新生命周期边界" if available else "WorldBridge 生命周期证据不可用",
        "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。" if available else "缺少证据，不可作为运行时控制依据。",
        "current_runtime_quarantined": False if available else None,
        "same_adapter_only": True,
        "evidence_summary": {
            "failure_lifecycle_values_redacted": True,
            "current_lifecycle_values_redacted": True,
            "disposal_recorded": True if available else False,
            "disposal_boundary": "simulation_stop" if available else None,
            "fresh_instance_boundary_observed": True if available else False,
        },
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }
    if not available:
        presentation["reason"] = "lifecycle_evidence_unavailable"
    return presentation


def _projection() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "worldbridge_quarantine_lifecycle_correlation",
        "read_only": True,
        "availability": "available",
        "current_runtime_quarantined": False,
        "negative_capabilities": {**{key: False for key in NEGATIVE_CAPABILITIES[:10]}, "default_ready": False},
        "correlation": {
            "state": "fresh_instance_boundary_observed",
            "same_adapter_only": True,
            "fresh_instance_boundary_observed": True,
            "observed_disposal": {"recorded": True, "boundary": "simulation_stop"},
        },
    }


def test_export_and_audit_are_canonical_copy_isolated_and_redacted() -> None:
    presentation = _presentation()
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    encoded = encode_worldbridge_quarantine_operator_presentation_export_record(export_record)
    decoded = decode_worldbridge_quarantine_operator_presentation_export_record(encoded)
    audit = audit_worldbridge_quarantine_operator_presentation_export(decoded)
    audit_encoded = encode_worldbridge_quarantine_operator_presentation_export_audit(audit)

    assert len(encoded) <= MAX_EXPORT_BYTES
    assert decoded == export_record
    assert decode_worldbridge_quarantine_operator_presentation_export_audit(audit_encoded) == audit
    assert validate_worldbridge_quarantine_operator_presentation_export_record(export_record, presentation=presentation) == {"valid": True, "errors": []}
    assert validate_worldbridge_quarantine_operator_presentation_export_audit(audit, export_record=export_record) == {"valid": True, "errors": []}
    serialized = json.dumps({"export": export_record, "audit": audit}, ensure_ascii=False, sort_keys=True)
    assert "epoch-secret" not in serialized and "pond-secret" not in serialized
    assert export_record["evidence_summary"]["fresh_instance_boundary_observed"] is True
    assert export_record["restore_performed"] is False
    assert audit["same_runtime_retry_admitted"] is False

    presentation["headline"] = "mutated after export"
    export_record["headline"] = "mutated after audit"
    assert decoded["headline"] != "mutated after audit"
    assert audit["headline"] != "mutated after audit"


@pytest.mark.parametrize("available", [True, False])
def test_export_preserves_bounded_available_and_unavailable_presentations(available: bool) -> None:
    presentation = _presentation(available=available)
    record = export_worldbridge_quarantine_operator_presentation(presentation)
    audit = audit_worldbridge_quarantine_operator_presentation_export(record)
    assert record["availability"] == presentation["availability"]
    assert audit["operator_state"] == presentation["operator_state"]
    assert record["negative_capabilities"] == {key: False for key in NEGATIVE_CAPABILITIES}


def test_export_and_audit_fail_closed_on_tampering_and_noncanonical_input() -> None:
    record = export_worldbridge_quarantine_operator_presentation(_presentation())
    tampered = copy.deepcopy(record)
    tampered["evidence_summary"]["fresh_instance_boundary_observed"] = False
    tampered["export_digest"] = _export_digest(tampered)
    validation = validate_worldbridge_quarantine_operator_presentation_export_record(tampered, presentation=_presentation())
    assert validation["valid"] is False
    assert "presentation_parity_evidence_summary_mismatch" in validation["errors"]

    duplicate = b'{"schema_version":1,"schema_version":1}'
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_export_record(duplicate)
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_export_audit(b'{"schema_version":NaN}')
    with pytest.raises(ValueError):
        decode_worldbridge_quarantine_operator_presentation_export_record(b"x" * (MAX_EXPORT_BYTES + 1))

    audit = audit_worldbridge_quarantine_operator_presentation_export(record)
    tampered_audit = copy.deepcopy(audit)
    tampered_audit["operator_action_admitted"] = True
    tampered_audit["audit_digest"] = _audit_digest(tampered_audit)
    assert "operator_action_admitted_mismatch" in validate_worldbridge_quarantine_operator_presentation_export_audit(tampered_audit)["errors"]


def test_contracts_and_read_only_command_mcp_status_surfaces() -> None:
    export_contract = build_worldbridge_quarantine_operator_presentation_export_contract()
    audit_contract = build_worldbridge_quarantine_operator_presentation_export_audit_contract()
    assert validate_worldbridge_quarantine_operator_presentation_export_contract(export_contract) == {"valid": True, "errors": []}
    assert validate_worldbridge_quarantine_operator_presentation_export_audit_contract(audit_contract) == {"valid": True, "errors": []}

    class Host:
        def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, object]:
            return _projection()

    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, Host())
    context = {"editor_context": SimpleNamespace(services=services)}
    registry = get_command_registry()
    for command_id in (EXPORT_COMMAND, AUDIT_COMMAND):
        spec = registry.describe(command_id)
        assert spec["mutates"] is False and spec["requires_gui"] is False
        result = registry.run(command_id, {}, context=context)
        assert result["ok"] is True
        assert result["result"]["default_ready"] is False

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return {"ok": True}
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_worldbridge_quarantine_operator_presentation_export() == {"ok": True}
        assert mcp_adapter.get_runtime_worldbridge_quarantine_operator_presentation_export_audit() == {"ok": True}
    finally:
        mcp_adapter.run_command = original
    assert calls == [(EXPORT_COMMAND, {}), (AUDIT_COMMAND, {})]

    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_export_contract"] == export_contract
    assert status["failure_quarantine_operator_presentation_export_audit_contract"] == audit_contract
    assert "quarantine_operator_presentation_export_module" in status["pilot_modules"]
    assert "quarantine_operator_presentation_export_audit_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
