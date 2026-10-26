# -*- coding: utf-8 -*-
"""Static E246 guard: cross-surface evidence presentation stays Qt-free and non-authoritative."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_surface_audit import (
    VISIBLE_FIELD_IDS,
    audit_worldbridge_quarantine_operator_presentation_surfaces,
    build_worldbridge_quarantine_operator_presentation_surface_audit_contract,
    validate_worldbridge_quarantine_operator_presentation_surface_audit,
    validate_worldbridge_quarantine_operator_presentation_surface_audit_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import export_worldbridge_quarantine_operator_presentation
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import audit_worldbridge_quarantine_operator_presentation_export
from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import consume_worldbridge_quarantine_operator_evidence_pair
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.inspector.worldbridge_quarantine_operator_evidence_bundle import build_worldbridge_quarantine_operator_evidence_bundle_view_model
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_surface_audit.py"
INSPECTOR = RUNTIME / "core/VitaLoom/inspector/worldbridge_quarantine_operator_evidence_bundle.py"
MCP = RUNTIME / "core/VitaLoom/commands/mcp_adapter.py"


def _bundle() -> dict[str, object]:
    presentation: dict[str, object] = {
        "schema_version": 1, "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation", "read_only": True,
        "availability": "available", "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界", "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False, "same_adapter_only": True,
        "evidence_summary": {"failure_lifecycle_values_redacted": True, "current_lifecycle_values_redacted": True,
                             "disposal_recorded": True, "disposal_boundary": "simulation_stop",
                             "fresh_instance_boundary_observed": True},
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES}, "do_not_claim": list(DO_NOT_CLAIM),
    }
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    return consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit_worldbridge_quarantine_operator_presentation_export(export_record))


def main() -> int:
    bundle = _bundle()
    command = {"ok": True, "result": copy.deepcopy(bundle)}
    inspector = build_worldbridge_quarantine_operator_evidence_bundle_view_model(command).to_dict()
    audit = audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), inspector)
    if validate_worldbridge_quarantine_operator_presentation_surface_audit(audit) != {"valid": True, "errors": []}:
        raise SystemExit("E246 surface audit invalid")
    if audit["visible_field_ids"] != list(VISIBLE_FIELD_IDS) or audit["inspector_fields_editable"] is not False:
        raise SystemExit("E246 visible field contract mismatch")
    serial = json.dumps({"audit": audit, "inspector": inspector}, ensure_ascii=False, sort_keys=True)
    if any(value in serial for value in ("epoch-secret", "pond-secret", "sr_runtime_epoch", "pond_lifetime_token")):
        raise SystemExit("E246 exposed opaque lifecycle values")
    for key in ("runtime_action_authority", "ui_authority", "quarantine_clear_admitted", "same_runtime_retry_admitted", "recovery_admitted", "replay_or_restore_admitted", "persistence_admitted", "default_ready"):
        if audit.get(key) is not False:
            raise SystemExit(f"E246 policy overclaim: {key}")
    tampered = copy.deepcopy(inspector); tampered["section"]["fields"][0]["editable"] = True
    try:
        audit_worldbridge_quarantine_operator_presentation_surfaces(command, copy.deepcopy(command), tampered)
    except ValueError:
        pass
    else:
        raise SystemExit("E246 admitted editable Inspector field")

    forbidden = ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "deserialize_pond(")
    source = AUTHORITY.read_text(encoding="utf-8-sig")
    if any(token in source for token in forbidden):
        raise SystemExit("E246 crossed Qt/runtime/I/O boundary")
    tree = ast.parse(MCP.read_text(encoding="utf-8-sig"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_runtime_worldbridge_quarantine_operator_evidence_bundle")
    body = ast.unparse(function)
    if "runtime.worldbridge.quarantine_operator_evidence_bundle" not in body or any(token in body for token in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport", "open(")):
        raise SystemExit("E246 MCP surface gained control authority")
    inspector_source = INSPECTOR.read_text(encoding="utf-8-sig")
    if "registry.run(WORLD_BRIDGE_QUARANTINE_OPERATOR_EVIDENCE_BUNDLE_COMMAND_ID, {})" not in inspector_source:
        raise SystemExit("E246 Inspector lost command-only loading")
    spec = get_command_registry().describe("runtime.worldbridge.quarantine_operator_evidence_bundle")
    if spec.get("mutates") is not False or spec.get("requires_gui") is not False:
        raise SystemExit("E246 source command not read-only/headless")
    contract = build_worldbridge_quarantine_operator_presentation_surface_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_surface_audit_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E246 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_surface_audit_contract") != contract:
        raise SystemExit("E246 status lost surface contract")
    if "quarantine_operator_presentation_surface_audit_module" not in status.get("pilot_modules", []):
        raise SystemExit("E246 status lost module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E246 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "writes_files": False, "transmits_network": False, "runtime_action_authority": False, "ui_authority": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
