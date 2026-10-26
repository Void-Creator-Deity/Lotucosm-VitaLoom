# -*- coding: utf-8 -*-
"""Static/E245 smoke guard for immutable E244 evidence-bundle Inspector projection."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
INSPECTOR = RUNTIME / "core" / "VitaLoom" / "inspector" / "worldbridge_quarantine_operator_evidence_bundle.py"

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


def _bundle() -> dict[str, object]:
    presentation = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available", "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界", "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False, "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
                             "disposal_recorded": True, "disposal_boundary": "simulation_stop",
                             "fresh_instance_boundary_observed": True},
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    return consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit_worldbridge_quarantine_operator_presentation_export(export_record))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name: return node
    raise SystemExit(f"missing function {name}")


def main() -> int:
    bundle = _bundle()
    model = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": bundle})
    if model.available is not True or any(field.editable for field in model.section.fields):
        raise SystemExit("E245 Inspector did not produce immutable available evidence model")
    encoded = json.dumps(model.to_dict(), ensure_ascii=False, sort_keys=True)
    if any(token in encoded for token in ("epoch-secret", "pond-secret", "sr_runtime_epoch", "pond_lifetime_token")):
        raise SystemExit("E245 Inspector exposed opaque lifecycle values")
    unsafe = copy.deepcopy(bundle); unsafe["evidence_summary"]["bad"] = object()
    if build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": unsafe}).error != {"code": "non_json_payload", "message": "Evidence bundle result must contain JSON values only"}:
        raise SystemExit("E245 Inspector accepted non-JSON bundle")
    invalid = copy.deepcopy(bundle); invalid["negative_capabilities"]["replay_admitted"] = True
    result = build_worldbridge_quarantine_operator_evidence_bundle_view_model({"ok": True, "result": invalid})
    if result.error is None or result.error.get("code") != "guardrail_violation":
        raise SystemExit("E245 Inspector accepted negative capability overclaim")
    class Registry:
        def __init__(self) -> None: self.calls: list[tuple[str, dict[str, object]]] = []
        def run(self, command_id: str, payload: dict[str, object]) -> dict[str, object]:
            self.calls.append((command_id, dict(payload))); return {"ok": True, "result": bundle}
    registry = Registry()
    if load_worldbridge_quarantine_operator_evidence_bundle_view_model(registry=registry).available is not True:
        raise SystemExit("E245 loader did not project command response")
    if registry.calls != [(WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID, {})]:
        raise SystemExit("E245 loader called a non-authoritative surface")
    source = INSPECTOR.read_text(encoding="utf-8-sig")
    forbidden = ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "world_bridge_quarantine_lifecycle_correlation", "world_bridge_quarantine_operator_presentation_export", "world_bridge_quarantine_operator_presentation_export_audit")
    if any(token in source for token in forbidden): raise SystemExit("E245 Inspector crossed UI/runtime/upstream evidence boundary")
    tree = ast.parse(source)
    loader = ast.unparse(_function(tree, "load_worldbridge_quarantine_operator_evidence_bundle_view_model"))
    expected = "registry.run(WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID, {})"
    if expected not in loader: raise SystemExit("E245 loader no longer calls only E244 command")
    if any(token in loader for token in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport")):
        raise SystemExit("E245 loader gained runtime control")
    print(json.dumps({"status": "ok", "json_safe": True, "all_fields_immutable": True, "command_only": True, "ui_authority": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
