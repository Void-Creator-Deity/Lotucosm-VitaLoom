# -*- coding: utf-8 -*-
"""Focused E241 regression coverage for bounded lifecycle evidence."""
from __future__ import annotations

import builtins
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
    build_worldbridge_quarantine_disposal_observation,
    build_worldbridge_quarantine_lifecycle_correlation_contract,
    build_worldbridge_quarantine_lifecycle_evidence,
    project_worldbridge_quarantine_lifecycle_correlation,
    validate_worldbridge_quarantine_lifecycle_correlation_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    project_worldbridge_quarantine_diagnostic,
)
from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
    classify_worldbridge_opt_in_bridge_admission,
)
from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    classify_worldbridge_handoff_failure_containment,
)
from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    build_worldbridge_handoff_failure_receipt,
)
from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
    get_worldbridge_quarantine_diagnostic_host,
)
from core.VitaLoom.viewports.game_viewport import GameViewport


def _diagnostic(*, quarantined: bool) -> dict[str, object]:
    receipt = build_worldbridge_handoff_failure_receipt(
        "pond_update",
        trace_requested=False,
        preflight_completed=True,
        sr_to_ps_sync_started=True,
        pond_update_started=True,
        ps_to_sr_reflection_started=False,
        cause=RuntimeError("fixture"),
    )
    return project_worldbridge_quarantine_diagnostic(
        handoff_suspended=quarantined,
        failure_receipt=receipt,
        recovery_decision=classify_worldbridge_handoff_failure_containment(receipt),
        quarantine_admission=classify_worldbridge_opt_in_bridge_admission(
            "tick_handoff",
            unified_pond_mode=True,
            handoff_suspended=quarantined,
            current_pond_present=True,
        ),
    )


def _lifecycle(epoch: str, pond: str) -> dict[str, object]:
    result = build_worldbridge_quarantine_lifecycle_evidence(
        sr_runtime_epoch=epoch,
        pond_lifetime_token=pond,
    )
    assert result is not None
    return result


def test_projection_requires_both_new_opaque_tokens_for_fresh_boundary() -> None:
    failure = _lifecycle("epoch-1", "pond-1")
    disposal = build_worldbridge_quarantine_disposal_observation(
        failure_lifecycle=failure,
        active_lifecycle=failure,
        disposal_boundary="simulation_stop",
        handoff_suspended=True,
    )
    assert disposal is not None

    quarantined = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=True),
        failure_lifecycle=failure,
        disposal_observation=None,
        current_lifecycle=failure,
    )
    assert quarantined["correlation"]["state"] == "current_quarantined_failure_tuple_observed"

    for partial in (_lifecycle("epoch-2", "pond-1"), _lifecycle("epoch-1", "pond-2")):
        result = project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=failure,
            disposal_observation=disposal,
            current_lifecycle=partial,
        )
        assert result["correlation"]["state"] == "current_lifecycle_not_proven_fresh_from_failure"
        assert result["correlation"]["fresh_instance_boundary_observed"] is False

    fresh = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=False),
        failure_lifecycle=failure,
        disposal_observation=disposal,
        current_lifecycle=_lifecycle("epoch-2", "pond-2"),
    )
    assert fresh["correlation"]["state"] == "fresh_instance_boundary_observed"
    assert fresh["correlation"]["fresh_instance_boundary_observed"] is True
    assert fresh["negative_capabilities"]["fresh_boundary_is_state_recovery"] is False
    assert fresh["negative_capabilities"]["default_ready"] is False


def test_projection_preserves_incomplete_historical_and_quarantine_integrity() -> None:
    failure = _lifecycle("epoch-1", "pond-1")
    disposal = build_worldbridge_quarantine_disposal_observation(
        failure_lifecycle=failure,
        active_lifecycle=failure,
        disposal_boundary="scene_runtime_discard",
        handoff_suspended=True,
    )
    historical = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=False),
        failure_lifecycle=failure,
        disposal_observation=disposal,
        current_lifecycle=None,
    )
    assert historical["correlation"]["state"] == "historical_after_observed_disposal_no_current_sr_pond_pair"

    incomplete = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=True),
        failure_lifecycle=None,
        disposal_observation=None,
        current_lifecycle=None,
    )
    assert incomplete["correlation"]["state"] == "current_quarantined_lifecycle_evidence_incomplete"
    with pytest.raises(ValueError, match="differs"):
        project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=True),
            failure_lifecycle=failure,
            disposal_observation=None,
            current_lifecycle=_lifecycle("epoch-2", "pond-2"),
        )


def test_contract_copy_isolation_and_qt_free_import() -> None:
    contract = build_worldbridge_quarantine_lifecycle_correlation_contract()
    for key in (
        "same_runtime_safe_retry",
        "automatic_quarantine_clear",
        "fresh_boundary_is_state_recovery",
        "cross_lane_rollback",
        "in_place_restore",
        "replay_admitted",
        "cross_adapter_lifecycle_correlation",
        "default_ready",
    ):
        tampered = copy.deepcopy(contract)
        tampered["admissions"][key] = True
        assert validate_worldbridge_quarantine_lifecycle_correlation_contract(tampered)["valid"] is False

    result = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=False),
        failure_lifecycle=_lifecycle("epoch-1", "pond-1"),
        disposal_observation=None,
        current_lifecycle=None,
    )
    result["correlation"]["failure_lifecycle"]["sr_runtime_epoch"] = "tampered"
    assert project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=False),
        failure_lifecycle=_lifecycle("epoch-1", "pond-1"),
        disposal_observation=None,
        current_lifecycle=None,
    )["correlation"]["failure_lifecycle"]["sr_runtime_epoch"] == "epoch-1"

    source = Path(__file__).parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_lifecycle_correlation.py"
    spec = importlib.util.spec_from_file_location("e241_qt_free_probe", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("PyQt6"):
            raise AssertionError("E241 authority imported PyQt6")
        return original_import(name, *args, **kwargs)

    try:
        builtins.__import__ = guarded_import
        spec.loader.exec_module(module)
    finally:
        builtins.__import__ = original_import
    assert module.STATUS == "worldbridge_quarantine_lifecycle_correlation"


def test_game_viewport_proxy_observes_disposal_then_fresh_pair_without_mutation() -> None:
    viewport = GameViewport.__new__(GameViewport)
    viewport._sr_runtime_epoch = "epoch-1"
    viewport._worldbridge_active_pond_lifetime_token = "pond-1"
    viewport._worldbridge_handoff_suspended = True
    viewport._worldbridge_failure_lifecycle = viewport._worldbridge_current_lifecycle_evidence()
    viewport._worldbridge_disposal_observation = None
    viewport.query_worldbridge_quarantine_diagnostic = lambda: _diagnostic(quarantined=True)

    viewport._observe_worldbridge_quarantine_lifecycle_disposal("simulation_stop")
    assert viewport._worldbridge_disposal_observation is not None
    assert viewport.query_worldbridge_quarantine_lifecycle_correlation()["correlation"]["state"] == "current_quarantined_failure_tuple_observed"

    viewport._worldbridge_handoff_suspended = False
    viewport._sr_runtime_epoch = "epoch-2"
    viewport._worldbridge_active_pond_lifetime_token = "pond-2"
    viewport.query_worldbridge_quarantine_diagnostic = lambda: _diagnostic(quarantined=False)
    result = viewport.query_worldbridge_quarantine_lifecycle_correlation()
    assert result["correlation"]["state"] == "fresh_instance_boundary_observed"


def test_host_command_mcp_and_static_status_remain_read_only() -> None:
    unavailable = get_worldbridge_quarantine_diagnostic_host(
        {"editor_context": SimpleNamespace(services=ServiceRegistry())}
    ).query_worldbridge_quarantine_lifecycle_correlation()
    assert unavailable["status"] == "unavailable"
    assert unavailable["negative_capabilities"]["cross_adapter_lifecycle_correlation"] is False

    expected = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(quarantined=False),
        failure_lifecycle=None,
        disposal_observation=None,
        current_lifecycle=None,
    )

    class Host:
        def query_worldbridge_quarantine_diagnostic(self) -> dict[str, object]:
            return _diagnostic(quarantined=False)

        def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, object]:
            return copy.deepcopy(expected)

    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, Host())
    spec = get_command_registry().describe(
        "runtime.worldbridge.quarantine_lifecycle_correlation"
    )
    assert spec["mutates"] is False and spec["requires_gui"] is False
    result = get_command_registry().run(
        "runtime.worldbridge.quarantine_lifecycle_correlation",
        {},
        context={"editor_context": SimpleNamespace(services=services)},
    )
    assert result["result"] == expected

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return {"ok": True}
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_worldbridge_quarantine_lifecycle_correlation() == {"ok": True}
    finally:
        mcp_adapter.run_command = original
    assert calls == [("runtime.worldbridge.quarantine_lifecycle_correlation", {})]

    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_lifecycle_correlation_contract"] == contract_or_status_contract()
    assert "quarantine_lifecycle_correlation_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def contract_or_status_contract() -> dict[str, object]:
    return build_worldbridge_quarantine_lifecycle_correlation_contract()
