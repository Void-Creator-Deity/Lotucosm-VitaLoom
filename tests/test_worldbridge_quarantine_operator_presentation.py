# -*- coding: utf-8 -*-
"""Focused E242 regression coverage for bounded quarantine operator presentation."""
from __future__ import annotations

import builtins
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    project_worldbridge_quarantine_diagnostic,
)
from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
    build_worldbridge_quarantine_disposal_observation,
    build_worldbridge_quarantine_lifecycle_evidence,
    project_worldbridge_quarantine_lifecycle_correlation,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM,
    KNOWN_STATES,
    NEGATIVE_CAPABILITIES,
    build_worldbridge_quarantine_operator_presentation_contract,
    present_worldbridge_quarantine_lifecycle,
    validate_worldbridge_quarantine_operator_presentation,
    validate_worldbridge_quarantine_operator_presentation_contract,
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
from core.VitaLoom.inspector.worldbridge_quarantine_operator_presentation import (
    WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID,
    build_worldbridge_quarantine_operator_presentation_view_model,
    load_worldbridge_quarantine_operator_presentation_view_model,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


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


def _disposal(failure: dict[str, object]) -> dict[str, object]:
    result = build_worldbridge_quarantine_disposal_observation(
        failure_lifecycle=failure,
        active_lifecycle=failure,
        disposal_boundary="simulation_stop",
        handoff_suspended=True,
    )
    assert result is not None
    return result


def _source(state: str) -> dict[str, object]:
    failure = _lifecycle("epoch-secret", "pond-secret")
    disposal = _disposal(failure)
    if state == "current_quarantined_lifecycle_evidence_incomplete":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=True),
            failure_lifecycle=None,
            disposal_observation=None,
            current_lifecycle=None,
        )
    if state == "current_quarantined_failure_tuple_observed":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=True),
            failure_lifecycle=failure,
            disposal_observation=None,
            current_lifecycle=failure,
        )
    if state == "no_captured_failure_lifecycle_evidence":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=None,
            disposal_observation=None,
            current_lifecycle=None,
        )
    if state == "historical_after_observed_disposal_no_current_sr_pond_pair":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=failure,
            disposal_observation=disposal,
            current_lifecycle=None,
        )
    if state == "historical_or_unverified_after_current_quarantine_cleared":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=failure,
            disposal_observation=None,
            current_lifecycle=None,
        )
    if state == "fresh_instance_boundary_observed":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=failure,
            disposal_observation=disposal,
            current_lifecycle=_lifecycle("epoch-new", "pond-new"),
        )
    if state == "current_lifecycle_not_proven_fresh_from_failure":
        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(quarantined=False),
            failure_lifecycle=failure,
            disposal_observation=disposal,
            current_lifecycle=_lifecycle("epoch-new", "pond-secret"),
        )
    raise AssertionError(f"unsupported fixture state: {state}")


@pytest.mark.parametrize("state", sorted(KNOWN_STATES))
def test_all_e241_states_map_to_bounded_redacted_operator_presentation(state: str) -> None:
    presentation = present_worldbridge_quarantine_lifecycle(_source(state))

    assert presentation["availability"] == "available"
    assert presentation["operator_state"] == state
    assert presentation["same_adapter_only"] is True
    assert presentation["negative_capabilities"] == {key: False for key in NEGATIVE_CAPABILITIES}
    assert set(presentation["do_not_claim"]) == set(DO_NOT_CLAIM)
    assert presentation["evidence_summary"]["failure_lifecycle_values_redacted"] is True
    assert presentation["evidence_summary"]["current_lifecycle_values_redacted"] is True
    serialized = json.dumps(presentation, ensure_ascii=False, sort_keys=True)
    assert "epoch-secret" not in serialized
    assert "pond-secret" not in serialized
    assert validate_worldbridge_quarantine_operator_presentation(presentation) == {"valid": True, "errors": []}


def test_fresh_boundary_is_explicitly_observation_only_not_recovery() -> None:
    presentation = present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))

    assert "\\u72ec\\u7acb\\u7684\\u65b0".encode("ascii").decode("unicode_escape") in presentation["headline"]
    assert "\\u4e0d\\u662f\\u6062\\u590d".encode("ascii").decode("unicode_escape") in presentation["caveat"]
    assert presentation["evidence_summary"]["fresh_instance_boundary_observed"] is True
    assert presentation["negative_capabilities"]["fresh_boundary_is_state_recovery"] is False
    assert presentation["negative_capabilities"]["operator_action_admitted"] is False
    assert presentation["negative_capabilities"]["ui_authority"] is False
    assert presentation["negative_capabilities"]["default_ready"] is False


def test_unavailable_source_remains_bounded_and_requires_negative_capabilities() -> None:
    unavailable = {
        "schema_version": 1,
        "status": "unavailable",
        "scope": "same_adapter_worldbridge_quarantine_lifecycle_evidence",
        "read_only": True,
        "availability": "unavailable",
        "current_runtime_quarantined": None,
        "reason": "host_unavailable",
        "negative_capabilities": {
            **{key: False for key in NEGATIVE_CAPABILITIES[:10]},
            "default_ready": False,
        },
    }
    presentation = present_worldbridge_quarantine_lifecycle(unavailable)

    assert presentation["availability"] == "unavailable"
    assert presentation["operator_state"] == "unavailable"
    assert presentation["current_runtime_quarantined"] is None
    assert presentation["reason"] == "host_unavailable"
    assert presentation["evidence_summary"]["fresh_instance_boundary_observed"] is False
    assert validate_worldbridge_quarantine_operator_presentation(presentation)["valid"] is True

    unavailable["negative_capabilities"]["default_ready"] = True
    with pytest.raises(ValueError, match="default_ready"):
        present_worldbridge_quarantine_lifecycle(unavailable)


def test_source_and_presentation_guardrails_fail_closed_and_copy_isolated() -> None:
    source = _source("fresh_instance_boundary_observed")
    source["negative_capabilities"].pop("fresh_boundary_is_state_recovery")
    with pytest.raises(ValueError, match="fresh_boundary_is_state_recovery"):
        present_worldbridge_quarantine_lifecycle(source)

    presentation = present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))
    presentation["negative_capabilities"]["ui_authority"] = True
    assert "negative_capabilities_ui_authority_overclaim" in validate_worldbridge_quarantine_operator_presentation(presentation)["errors"]
    presentation = present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))
    presentation["evidence_summary"]["failure_lifecycle_values_redacted"] = False
    assert "opaque_lifecycle_values_not_redacted" in validate_worldbridge_quarantine_operator_presentation(presentation)["errors"]

    isolated = present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))
    isolated["do_not_claim"].append("tampered")
    assert "tampered" not in present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))["do_not_claim"]


def test_artifact_import_rejection_is_presented_without_artifact_or_restore_authority() -> None:
    diagnostic = {
        "recorded": True,
        "schema_version": 1,
        "code": "worldbridge_checkpoint_artifact_rejected",
        "errors": ["artifact_digest_mismatch", "project_lock_binding_mismatch"],
        "diagnostic_digest": "a" * 64,
    }
    presentation = present_worldbridge_quarantine_lifecycle(
        _source("current_quarantined_failure_tuple_observed"),
        artifact_import_diagnostic=diagnostic,
    )

    assert validate_worldbridge_quarantine_operator_presentation(presentation) == {"valid": True, "errors": []}
    assert presentation["artifact_import_diagnostic"] == diagnostic
    serialized = json.dumps(presentation, ensure_ascii=False, sort_keys=True)
    assert "live_restore" not in serialized
    assert "ps_state" not in serialized
    assert "component_identity" not in serialized
    assert all(value is False for value in presentation["negative_capabilities"].values())

    tampered = copy.deepcopy(presentation)
    tampered["artifact_import_diagnostic"]["diagnostic_digest"] = "not-a-digest"
    assert validate_worldbridge_quarantine_operator_presentation(tampered)["valid"] is False


def test_contract_is_complete_copy_safe_and_qt_free() -> None:
    contract = build_worldbridge_quarantine_operator_presentation_contract()
    assert contract["contract_valid"] is True
    assert contract["opaque_lifecycle_values_exposed"] is False
    assert contract["ui_authority"] is False
    assert contract["operator_action_admitted"] is False
    assert contract["artifact_import_diagnostic_supported"] is True
    for key in NEGATIVE_CAPABILITIES:
        tampered = copy.deepcopy(contract)
        tampered["negative_capabilities"][key] = True
        assert validate_worldbridge_quarantine_operator_presentation_contract(tampered)["valid"] is False

    source = Path(__file__).parents[1] / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation.py"
    spec = importlib.util.spec_from_file_location("e242_qt_free_probe", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("PyQt6"):
            raise AssertionError("E242 authority imported PyQt6")
        return original_import(name, *args, **kwargs)

    try:
        builtins.__import__ = guarded_import
        spec.loader.exec_module(module)
    finally:
        builtins.__import__ = original_import
    assert module.STATUS == "worldbridge_quarantine_operator_presentation"


def test_command_mcp_status_and_e240_only_host_are_read_only_and_compatible() -> None:
    expected = _source("historical_after_observed_disposal_no_current_sr_pond_pair")

    class LifecycleHost:
        def query_worldbridge_quarantine_diagnostic(self) -> dict[str, object]:
            return _diagnostic(quarantined=False)

        def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, object]:
            return copy.deepcopy(expected)

    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, LifecycleHost())
    spec = get_command_registry().describe(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID)
    assert spec["mutates"] is False and spec["requires_gui"] is False
    result = get_command_registry().run(
        WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID,
        {},
        context={"editor_context": SimpleNamespace(services=services)},
    )
    assert result["ok"] is True
    assert result["result"]["operator_state"] == expected["correlation"]["state"]

    class E240OnlyHost:
        def query_worldbridge_quarantine_diagnostic(self) -> dict[str, object]:
            return _diagnostic(quarantined=False)

    e240_services = ServiceRegistry()
    e240_services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, E240OnlyHost())
    unavailable = get_command_registry().run(
        WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID,
        {},
        context={"editor_context": SimpleNamespace(services=e240_services)},
    )
    assert unavailable["ok"] is True
    assert unavailable["result"]["availability"] == "unavailable"
    assert get_command_registry().run(
        "runtime.worldbridge.quarantine_diagnostic",
        {},
        context={"editor_context": SimpleNamespace(services=e240_services)},
    )["ok"] is True

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return {"ok": True}
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_worldbridge_quarantine_operator_presentation() == {"ok": True}
    finally:
        mcp_adapter.run_command = original
    assert calls == [(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {})]

    status = build_runtime_worldbridge_status()
    assert status["failure_quarantine_operator_presentation_contract"] == build_worldbridge_quarantine_operator_presentation_contract()
    assert "quarantine_operator_presentation_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_inspector_consumer_only_accepts_bounded_json_immutable_presentation() -> None:
    presentation = present_worldbridge_quarantine_lifecycle(_source("fresh_instance_boundary_observed"))
    view_model = build_worldbridge_quarantine_operator_presentation_view_model(
        {"ok": True, "result": presentation, "warnings": ["bounded evidence"]}
    )
    assert view_model.available is True
    assert view_model.error is None
    assert view_model.warnings == ("bounded evidence",)
    assert all(field.editable is False for field in view_model.section.fields)
    serialized = json.dumps(view_model.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "epoch-secret" not in serialized
    assert "pond-secret" not in serialized

    unsafe = copy.deepcopy(presentation)
    unsafe["evidence_summary"]["live"] = object()
    unsafe_view = build_worldbridge_quarantine_operator_presentation_view_model({"ok": True, "result": unsafe})
    assert unsafe_view.available is False
    assert unsafe_view.error is not None and unsafe_view.error["code"] == "non_json_payload"

    invalid = copy.deepcopy(presentation)
    invalid["negative_capabilities"]["operator_action_admitted"] = True
    invalid_view = build_worldbridge_quarantine_operator_presentation_view_model({"ok": True, "result": invalid})
    assert invalid_view.available is False
    assert invalid_view.error is not None and invalid_view.error["code"] == "guardrail_violation"

    class RecordingRegistry:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, object]]] = []

        def run(self, command_id: str, payload: dict[str, object]) -> dict[str, object]:
            self.calls.append((command_id, dict(payload)))
            return {"ok": True, "result": presentation}

    registry = RecordingRegistry()
    loaded = load_worldbridge_quarantine_operator_presentation_view_model(registry=registry)
    assert loaded.available is True
    assert registry.calls == [(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {})]


def test_artifact_rejection_survives_command_export_mcp_and_inspector_consumers() -> None:
    diagnostic = _diagnostic(quarantined=True)
    diagnostic["restore_diagnostic"] = {
        "recorded": True,
        "schema_version": 1,
        "code": "worldbridge_checkpoint_artifact_rejected",
        "errors": ["project_lock_binding_mismatch", "artifact_digest_mismatch"],
        "diagnostic_digest": "c" * 64,
    }

    class ArtifactRejectionHost:
        def query_worldbridge_quarantine_diagnostic(self) -> dict[str, object]:
            return copy.deepcopy(diagnostic)

        def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, object]:
            return _source("current_quarantined_failure_tuple_observed")

    services = ServiceRegistry()
    services.register(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST, ArtifactRejectionHost())
    context = {"editor_context": SimpleNamespace(services=services)}

    command = get_command_registry().run(
        WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {}, context=context
    )
    assert command["ok"] is True
    presented = command["result"]
    assert presented["artifact_import_diagnostic"]["errors"] == [
        "project_lock_binding_mismatch", "artifact_digest_mismatch"
    ]

    exported = get_command_registry().run(
        "runtime.worldbridge.quarantine_operator_presentation_export", {}, context=context
    )
    assert exported["ok"] is True
    assert exported["result"]["artifact_import_diagnostic"] == presented["artifact_import_diagnostic"]

    view_model = build_worldbridge_quarantine_operator_presentation_view_model(command)
    assert view_model.available is True
    diagnostic_field = next(
        field for field in view_model.section.fields if field.id == "artifact_import_diagnostic"
    )
    assert diagnostic_field.editable is False
    assert diagnostic_field.value["code"] == "worldbridge_checkpoint_artifact_rejected"
    assert diagnostic_field.value["errors"] == presented["artifact_import_diagnostic"]["errors"]
    assert view_model.to_dict()["section"]["fields"]

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return command
        mcp_adapter.run_command = fake
        mcp_result = mcp_adapter.get_runtime_worldbridge_quarantine_operator_presentation()
    finally:
        mcp_adapter.run_command = original
    assert mcp_result == command
    assert calls == [(WORLD_BRIDGE_QUARANTINE_OPERATOR_PRESENTATION_COMMAND_ID, {})]
    assert all(value is False for value in presented["negative_capabilities"].values())

def test_inspector_default_null_host_is_an_expected_unavailable_model() -> None:
    view_model = load_worldbridge_quarantine_operator_presentation_view_model()
    assert view_model.available is False
    assert view_model.error is None
    assert all(field.editable is False for field in view_model.section.fields)
