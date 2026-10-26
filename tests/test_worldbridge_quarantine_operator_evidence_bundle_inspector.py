# -*- coding: utf-8 -*-
"""Focused E245 regression coverage for immutable E244 bundle Inspector projection."""
from __future__ import annotations

import copy
import json

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM as PRESENTATION_DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import export_worldbridge_quarantine_operator_presentation
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import audit_worldbridge_quarantine_operator_presentation_export
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import consume_worldbridge_quarantine_operator_evidence_pair
from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import (
    WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID,
    build_worldbridge_quarantine_operator_evidence_bundle_view_model,
    load_worldbridge_quarantine_operator_evidence_bundle_view_model,
)


def _bundle(*, available: bool = True) -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available" if available else "unavailable",
        "operator_state": "fresh_instance_boundary_observed" if available else "unavailable",
        "headline": "独立的新生命周期边界" if available else "WorldBridge 生命周期证据不可用",
        "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。" if available else "缺少证据，不可作为运行时控制依据。",
        "current_runtime_quarantined": False if available else None, "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
                             "disposal_recorded": available, "disposal_boundary": "simulation_stop" if available else None,
                             "fresh_instance_boundary_observed": available},
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }
    if not available: presentation["reason"] = "lifecycle_evidence_unavailable"
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    return consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)


def test_bundle_inspector_projects_only_valid_bounded_evidence_immutably() -> None:
    bundle = _bundle()
    model = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": bundle, "warnings": ["bounded evidence"]})
    assert model.available is True
    assert model.error is None
    assert model.warnings == ("bounded evidence",)
    assert model.authority_command_id == WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID
    assert all(field.editable is False for field in model.section.fields)
    serialized = json.dumps(model.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "epoch-secret" not in serialized and "pond-secret" not in serialized
    source_value = next(field.value for field in model.section.fields if field.id == "evidence_summary")
    bundle["evidence_summary"]["fresh_instance_boundary_observed"] = False
    assert source_value["fresh_instance_boundary_observed"] is True


def test_bundle_inspector_guardrails_non_json_and_negative_capability_overclaims() -> None:
    bundle = _bundle()
    unsafe = copy.deepcopy(bundle)
    unsafe["evidence_summary"]["live"] = object()
    model = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": unsafe})
    assert model.available is False and model.error is not None
    assert model.error["code"] == "non_json_payload"

    invalid = copy.deepcopy(bundle)
    invalid["negative_capabilities"]["operator_action_admitted"] = True
    model = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": invalid})
    assert model.available is False and model.error is not None
    assert model.error["code"] == "guardrail_violation"


def test_bundle_inspector_unavailable_and_command_only_loader() -> None:
    unavailable = _bundle(available=False)
    model = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": unavailable})
    assert model.available is False and model.error is None
    assert all(field.editable is False for field in model.section.fields)

    class RecordingRegistry:
        def __init__(self) -> None: self.calls: list[tuple[str, dict[str, object]]] = []
        def run(self, command_id: str, payload: dict[str, object]) -> dict[str, object]:
            self.calls.append((command_id, dict(payload)))
            return {"ok": True, "result": _bundle()}
    registry = RecordingRegistry()
    loaded = load_worldbridge_quarantine_operator_evidence_bundle_view_model(registry=registry)
    assert loaded.available is True
    assert registry.calls == [(WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID, {})]


def test_bundle_inspector_default_host_is_expected_unavailable_read_model() -> None:
    model = load_worldbridge_quarantine_operator_evidence_bundle_view_model()
    assert model.available is False
    assert model.error is None
    assert all(field.editable is False for field in model.section.fields)
