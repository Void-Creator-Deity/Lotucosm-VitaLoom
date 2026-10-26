# -*- coding: utf-8 -*-
"""Focused E240 regression coverage."""
from __future__ import annotations

import copy
import builtins
import importlib.util
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    build_worldbridge_quarantine_diagnostic_provenance_contract,
    project_worldbridge_quarantine_diagnostic,
    validate_worldbridge_quarantine_diagnostic_provenance_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import classify_worldbridge_opt_in_bridge_admission
from core.Lotucosm.runtime.world_bridge_recovery_authority import classify_worldbridge_handoff_failure_containment
from core.Lotucosm.runtime.world_bridge_transaction_authority import build_worldbridge_handoff_failure_receipt
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import get_worldbridge_quarantine_diagnostic_host


def _projection() -> dict[str, object]:
    receipt = build_worldbridge_handoff_failure_receipt(
        "pond_update", trace_requested=False, preflight_completed=True,
        sr_to_ps_sync_started=True, pond_update_started=True,
        ps_to_sr_reflection_started=False, cause=RuntimeError("fixture"),
    )
    return project_worldbridge_quarantine_diagnostic(
        handoff_suspended=True,
        failure_receipt=receipt,
        recovery_decision=classify_worldbridge_handoff_failure_containment(receipt),
        quarantine_admission=classify_worldbridge_opt_in_bridge_admission(
            "tick_handoff", unified_pond_mode=True,
            handoff_suspended=True, current_pond_present=True,
        ),
    )


def test_projection_reports_quarantine_and_copy_isolates() -> None:
    result = _projection()
    assert result["current_runtime_quarantined"] is True
    assert result["failure"]["phase"] == "pond_update"
    assert result["failure"]["partial_mutation_possible"] is True
    assert result["last_opt_in_bridge_admission"]["admitted"] is False
    assert result["fresh_lifecycle_boundary"]["required_before_opt_in_re_admission"] is True
    assert result["fresh_lifecycle_boundary"]["restores_failed_runtime_state"] is False
    result["failure"]["phase"] = "tampered"
    assert _projection()["failure"]["phase"] == "pond_update"


def test_projection_preserves_restore_diagnostic_without_recovery_authority() -> None:
    diagnostic = {
        "schema_version": 1,
        "code": "project_runtime_binding_rejected",
        "errors": ["runtime_binding_project_lock_digest_mismatch"],
    }
    diagnostic["diagnostic_digest"] = hashlib.sha256(
        json.dumps(diagnostic, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    result = project_worldbridge_quarantine_diagnostic(
        handoff_suspended=False,
        failure_receipt=None,
        recovery_decision=None,
        quarantine_admission=None,
        restore_diagnostic=diagnostic,
    )
    assert result["restore_diagnostic"] == {"recorded": True, **diagnostic}
    assert result["negative_capabilities"]["replay_admitted"] is False
    result["restore_diagnostic"]["errors"].append("mutated")
    assert diagnostic["errors"] == ["runtime_binding_project_lock_digest_mismatch"]


def test_contract_rejects_recovery_overclaims_and_incomplete_provenance() -> None:
    contract = build_worldbridge_quarantine_diagnostic_provenance_contract()
    for key in ("same_runtime_safe_retry", "automatic_quarantine_clear", "in_place_restore", "replay_admitted", "default_ready"):
        changed = copy.deepcopy(contract)
        changed["admissions"][key] = True
        assert validate_worldbridge_quarantine_diagnostic_provenance_contract(changed)["valid"] is False
    with pytest.raises(ValueError):
        project_worldbridge_quarantine_diagnostic(
            handoff_suspended=True, failure_receipt=None,
            recovery_decision={}, quarantine_admission=None,
        )


def test_host_command_mcp_and_static_status_stay_read_only() -> None:
    unavailable = get_worldbridge_quarantine_diagnostic_host(
        {"editor_context": SimpleNamespace(services=ServiceRegistry())}
    ).query_worldbridge_quarantine_diagnostic()
    assert unavailable["status"] == "unavailable"
    assert unavailable["negative_capabilities"]["may_clear_quarantine"] is False

    expected = _projection()
    class Host:
        def query_worldbridge_quarantine_diagnostic(self) -> dict[str, object]:
            return copy.deepcopy(expected)
    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, Host())
    spec = get_command_registry().describe("runtime.worldbridge.quarantine_diagnostic")
    assert spec["mutates"] is False and spec["requires_gui"] is False
    result = get_command_registry().run(
        "runtime.worldbridge.quarantine_diagnostic", {},
        context={"editor_context": SimpleNamespace(services=services)},
    )
    assert result["result"] == expected

    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_diagnostic_provenance_contract"] == build_worldbridge_quarantine_diagnostic_provenance_contract()
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return {"ok": True}
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_worldbridge_quarantine_diagnostic()["ok"] is True
    finally:
        mcp_adapter.run_command = original
    assert calls == [("runtime.worldbridge.quarantine_diagnostic", {})]

def test_authority_import_stays_qt_free(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    authority = Path(__file__).parents[1] / (
        "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
        "core/Lotucosm/runtime/world_bridge_quarantine_diagnostic_provenance.py"
    )
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError("E240 authority must remain Qt-free")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    spec = importlib.util.spec_from_file_location("e240_qt_free_authority", authority)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_quarantine_diagnostic_provenance_contract()["contract_valid"] is True


def test_viewport_query_and_capability_lifecycle_are_read_only() -> None:
    from PyQt6.QtWidgets import QApplication
    from core.VitaLoom.viewports.game_viewport import GameViewport

    receipt = build_worldbridge_handoff_failure_receipt(
        "pond_update", trace_requested=False, preflight_completed=True,
        sr_to_ps_sync_started=True, pond_update_started=True,
        ps_to_sr_reflection_started=False, cause=RuntimeError("viewport fixture"),
    )
    viewport = GameViewport.__new__(GameViewport)
    viewport._worldbridge_handoff_suspended = True
    viewport._worldbridge_last_handoff_failure = receipt
    viewport._worldbridge_last_recovery_decision = classify_worldbridge_handoff_failure_containment(receipt)
    viewport._worldbridge_last_quarantine_admission = classify_worldbridge_opt_in_bridge_admission(
        "tick_handoff", unified_pond_mode=True,
        handoff_suspended=True, current_pond_present=True,
    )
    result = viewport.query_worldbridge_quarantine_diagnostic()
    assert result["current_runtime_quarantined"] is True
    assert result["negative_capabilities"]["may_retry_same_runtime_handoff"] is False

    viewport._worldbridge_handoff_suspended = False
    historical = viewport.query_worldbridge_quarantine_diagnostic()
    assert historical["current_runtime_quarantined"] is False
    assert historical["evidence_lifetime_relation"] == (
        "historical_or_unverified_after_current_quarantine_cleared"
    )

    app = QApplication.instance() or QApplication([])
    real_viewport = GameViewport()
    real_viewport.register_as_sr_host()
    try:
        assert real_viewport.editor_context.services.get(
            WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST
        ) is real_viewport
        resolved = get_worldbridge_quarantine_diagnostic_host(
            {"editor_context": real_viewport.editor_context}
        )
        assert resolved.query_worldbridge_quarantine_diagnostic()["current_runtime_quarantined"] is False
    finally:
        real_viewport.unregister_as_sr_host()
        app.processEvents()
    unavailable = get_worldbridge_quarantine_diagnostic_host(
        {"editor_context": real_viewport.editor_context}
    ).query_worldbridge_quarantine_diagnostic()
    assert unavailable["status"] == "unavailable"

