# -*- coding: utf-8 -*-
"""Focused E244 regression coverage for quarantine evidence bundle consumption."""
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
    _export_digest,
    export_worldbridge_quarantine_operator_presentation,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    _audit_digest,
    audit_worldbridge_quarantine_operator_presentation_export,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import (
    MAX_BUNDLE_BYTES,
    _bundle_digest,
    build_worldbridge_quarantine_operator_evidence_bundle_contract,
    consume_worldbridge_quarantine_operator_evidence_pair,
    decode_worldbridge_quarantine_operator_evidence_bundle,
    encode_worldbridge_quarantine_operator_evidence_bundle,
    validate_worldbridge_quarantine_operator_evidence_bundle,
    validate_worldbridge_quarantine_operator_evidence_bundle_contract,
    validate_worldbridge_quarantine_operator_evidence_bundle_source_pair,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

COMMAND_ID = "runtime.worldbridge.quarantine_operator_evidence_bundle"


def _presentation(*, available: bool = True) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available" if available else "unavailable",
        "operator_state": "fresh_instance_boundary_observed" if available else "unavailable",
        "headline": "独立的新生命周期边界" if available else "WorldBridge 生命周期证据不可用",
        "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。" if available else "缺少证据，不可作为运行时控制依据。",
        "current_runtime_quarantined": False if available else None, "same_adapter_only": True,
        "evidence_summary": {
            "failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
            "disposal_recorded": available, "disposal_boundary": "simulation_stop" if available else None,
            "fresh_instance_boundary_observed": available,
        },
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }
    if not available: value["reason"] = "lifecycle_evidence_unavailable"
    return value


def _projection() -> dict[str, object]:
    return {
        "schema_version": 1, "status": "worldbridge_quarantine_lifecycle_correlation", "read_only": True,
        "availability": "available", "current_runtime_quarantined": False,
        "negative_capabilities": {**{key: False for key in NEGATIVE_CAPABILITIES[:10]}, "default_ready": False},
        "correlation": {"state": "fresh_instance_boundary_observed", "same_adapter_only": True,
                        "fresh_instance_boundary_observed": True,
                        "observed_disposal": {"recorded": True, "boundary": "simulation_stop"}},
    }


def _pair(*, available: bool = True) -> tuple[dict[str, object], dict[str, object]]:
    export_record = export_worldbridge_quarantine_operator_presentation(_presentation(available=available))
    return export_record, audit_worldbridge_quarantine_operator_presentation_export(export_record)


def test_bundle_is_canonical_copy_isolated_and_retains_only_bounded_evidence() -> None:
    export_record, audit = _pair()
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)
    encoded = encode_worldbridge_quarantine_operator_evidence_bundle(bundle)
    decoded = decode_worldbridge_quarantine_operator_evidence_bundle(encoded)
    assert len(encoded) <= MAX_BUNDLE_BYTES
    assert decoded == bundle
    assert validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(export_record, audit) == {"valid": True, "errors": []}
    assert validate_worldbridge_quarantine_operator_evidence_bundle(bundle, export_record=export_record, audit=audit) == {"valid": True, "errors": []}
    serialized = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    assert "epoch-secret" not in serialized and "pond-secret" not in serialized
    assert bundle["evidence_summary"]["fresh_instance_boundary_observed"] is True
    assert bundle["restore_performed"] is False
    assert bundle["quarantine_clear_admitted"] is False
    export_record["headline"] = "mutated"
    audit["headline"] = "mutated"
    assert bundle["headline"] != "mutated"


@pytest.mark.parametrize("available", [True, False])
def test_bundle_preserves_available_and_unavailable_bounded_states(available: bool) -> None:
    export_record, audit = _pair(available=available)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)
    assert bundle["availability"] == ("available" if available else "unavailable")
    assert bundle["current_runtime_quarantined"] is (False if available else None)
    assert bundle["negative_capabilities"] == {key: False for key in NEGATIVE_CAPABILITIES}


def test_bundle_rejects_recomputed_export_or_audit_tampering_and_bad_bytes() -> None:
    export_record, audit = _pair()
    tampered_export = copy.deepcopy(export_record)
    tampered_export["headline"] = "wrong bounded wording"
    tampered_export["export_digest"] = _export_digest(tampered_export)
    assert validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(tampered_export, audit)["valid"] is False
    with pytest.raises(ValueError):
        consume_worldbridge_quarantine_operator_evidence_pair(tampered_export, audit)

    tampered_audit = copy.deepcopy(audit)
    tampered_audit["operator_state"] = "wrong"
    tampered_audit["audit_digest"] = _audit_digest(tampered_audit)
    assert validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(export_record, tampered_audit)["valid"] is False
    with pytest.raises(ValueError):
        consume_worldbridge_quarantine_operator_evidence_pair(export_record, tampered_audit)

    bundle = consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)
    tampered_bundle = copy.deepcopy(bundle)
    tampered_bundle["operator_action_admitted"] = True
    tampered_bundle["bundle_digest"] = _bundle_digest(tampered_bundle)
    assert "operator_action_admitted_mismatch" in validate_worldbridge_quarantine_operator_evidence_bundle(tampered_bundle)["errors"]
    with pytest.raises(ValueError): decode_worldbridge_quarantine_operator_evidence_bundle(b'{"schema_version":NaN}')
    with pytest.raises(ValueError): decode_worldbridge_quarantine_operator_evidence_bundle(b"x" * (MAX_BUNDLE_BYTES + 1))


def test_contract_command_mcp_and_status_are_headless_read_only() -> None:
    contract = build_worldbridge_quarantine_operator_evidence_bundle_contract()
    assert validate_worldbridge_quarantine_operator_evidence_bundle_contract(contract) == {"valid": True, "errors": []}

    class Host:
        def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, object]: return _projection()
    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, Host())
    registry = get_command_registry()
    spec = registry.describe(COMMAND_ID)
    assert spec["mutates"] is False and spec["requires_gui"] is False
    result = registry.run(COMMAND_ID, {}, context={"editor_context": SimpleNamespace(services=services)})
    assert result["ok"] is True
    assert result["result"]["operator_state"] == "fresh_instance_boundary_observed"

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {}))); return {"ok": True}
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_worldbridge_quarantine_operator_evidence_bundle() == {"ok": True}
    finally:
        mcp_adapter.run_command = original
    assert calls == [(COMMAND_ID, {})]

    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_evidence_bundle_contract"] == contract
    assert "quarantine_operator_evidence_bundle_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
