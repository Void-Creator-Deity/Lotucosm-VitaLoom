# -*- coding: utf-8 -*-
"""Static/E243 smoke guard for bounded quarantine presentation export and audit."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_operator_presentation_export.py"
AUDIT = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_operator_presentation_export_audit.py"
COMMANDS = RUNTIME / "core" / "VitaLoom" / "commands" / "runtime_commands.py"

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    DO_NOT_CLAIM as PRESENTATION_DO_NOT_CLAIM,
    NEGATIVE_CAPABILITIES,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
    _export_digest,
    build_worldbridge_quarantine_operator_presentation_export_contract,
    export_worldbridge_quarantine_operator_presentation,
    validate_worldbridge_quarantine_operator_presentation_export_contract,
    validate_worldbridge_quarantine_operator_presentation_export_record,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
    _audit_digest,
    audit_worldbridge_quarantine_operator_presentation_export,
    build_worldbridge_quarantine_operator_presentation_export_audit_contract,
    validate_worldbridge_quarantine_operator_presentation_export_audit,
    validate_worldbridge_quarantine_operator_presentation_export_audit_contract,
)
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _presentation() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "worldbridge_quarantine_operator_presentation",
        "scope": "same_adapter_worldbridge_quarantine_operator_presentation",
        "read_only": True,
        "availability": "available",
        "operator_state": "fresh_instance_boundary_observed",
        "headline": "独立的新生命周期边界",
        "caveat": "这只是观测，不是恢复、重试、重准入、还原或重放。",
        "current_runtime_quarantined": False,
        "same_adapter_only": True,
        "evidence_summary": {
            "failure_lifecycle_values_redacted": True,
            "current_lifecycle_values_redacted": True,
            "disposal_recorded": True,
            "disposal_boundary": "simulation_stop",
            "fresh_instance_boundary_observed": True,
        },
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(PRESENTATION_DO_NOT_CLAIM),
    }


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"missing function {name}")


def main() -> int:
    presentation = _presentation()
    record = export_worldbridge_quarantine_operator_presentation(presentation)
    audit = audit_worldbridge_quarantine_operator_presentation_export(record)
    if validate_worldbridge_quarantine_operator_presentation_export_record(record, presentation=presentation) != {"valid": True, "errors": []}:
        raise SystemExit("E243 export parity invalid")
    if validate_worldbridge_quarantine_operator_presentation_export_audit(audit, export_record=record) != {"valid": True, "errors": []}:
        raise SystemExit("E243 audit parity invalid")
    serial = json.dumps({"record": record, "audit": audit}, ensure_ascii=False, sort_keys=True)
    if any(value in serial for value in ("epoch-secret", "pond-secret", "sr_runtime_epoch", "pond_lifetime_token")):
        raise SystemExit("E243 exposed opaque lifecycle values")
    if record["evidence_summary"]["fresh_instance_boundary_observed"] is not True:
        raise SystemExit("E243 lost fresh-boundary observation")
    for value in (record, audit):
        for key in ("restore_performed", "mutation_executed", "ui_authority", "default_ready", "replay_admitted"):
            if value.get(key) is not False:
                raise SystemExit(f"E243 policy overclaim: {key}")
    tampered = copy.deepcopy(record)
    tampered["negative_capabilities"]["fresh_boundary_is_state_recovery"] = True
    tampered["export_digest"] = _export_digest(tampered)
    if validate_worldbridge_quarantine_operator_presentation_export_record(tampered).get("valid") is not False:
        raise SystemExit("E243 accepted negative-capability overclaim")
    tampered_audit = copy.deepcopy(audit)
    tampered_audit["quarantine_clear_admitted"] = True
    tampered_audit["audit_digest"] = _audit_digest(tampered_audit)
    if validate_worldbridge_quarantine_operator_presentation_export_audit(tampered_audit).get("valid") is not False:
        raise SystemExit("E243 accepted audit authority overclaim")

    forbidden = ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "deserialize_pond(")
    for path in (AUTHORITY, AUDIT):
        source = path.read_text(encoding="utf-8-sig")
        if any(token in source for token in forbidden):
            raise SystemExit(f"E243 crossed runtime/UI/I/O boundary in {path.name}")
    tree = ast.parse(COMMANDS.read_text(encoding="utf-8-sig"))
    for name, expected in (
        ("_runtime_worldbridge_quarantine_operator_presentation_export", "export_worldbridge_quarantine_operator_presentation"),
        ("_runtime_worldbridge_quarantine_operator_presentation_export_audit", "audit_worldbridge_quarantine_operator_presentation_export"),
    ):
        handler = ast.unparse(_function(tree, name))
        if "get_worldbridge_quarantine_lifecycle_host" not in handler or expected not in handler:
            raise SystemExit(f"E243 command lost bounded path: {name}")
        if any(token in handler for token in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport", "open(")):
            raise SystemExit(f"E243 command gained runtime control: {name}")
    for command_id in ("runtime.worldbridge.quarantine_operator_presentation_export", "runtime.worldbridge.quarantine_operator_presentation_export_audit"):
        spec = get_command_registry().describe(command_id)
        if spec.get("mutates") is not False or spec.get("requires_gui") is not False:
            raise SystemExit(f"E243 command not read-only/headless: {command_id}")

    export_contract = build_worldbridge_quarantine_operator_presentation_export_contract()
    audit_contract = build_worldbridge_quarantine_operator_presentation_export_audit_contract()
    if validate_worldbridge_quarantine_operator_presentation_export_contract(export_contract) != {"valid": True, "errors": []}:
        raise SystemExit("E243 export contract invalid")
    if validate_worldbridge_quarantine_operator_presentation_export_audit_contract(audit_contract) != {"valid": True, "errors": []}:
        raise SystemExit("E243 audit contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_presentation_export_contract") != export_contract:
        raise SystemExit("E243 status lost export contract")
    if status.get("failure_quarantine_operator_presentation_export_audit_contract") != audit_contract:
        raise SystemExit("E243 status lost audit contract")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E243 changed default WorldBridge boundary")
    print(json.dumps({"status": "ok", "writes_files": False, "transmits_network": False, "recovery_authority": False, "operator_action_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
