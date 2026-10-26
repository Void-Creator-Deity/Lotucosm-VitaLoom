# -*- coding: utf-8 -*-
"""Static/E244 smoke guard for quarantine evidence bundle consumer."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
BUNDLE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_operator_evidence_bundle.py"
COMMANDS = RUNTIME / "core" / "VitaLoom" / "commands" / "runtime_commands.py"

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
    _bundle_digest,
    build_worldbridge_quarantine_operator_evidence_bundle_contract,
    consume_worldbridge_quarantine_operator_evidence_pair,
    validate_worldbridge_quarantine_operator_evidence_bundle,
    validate_worldbridge_quarantine_operator_evidence_bundle_contract,
    validate_worldbridge_quarantine_operator_evidence_bundle_source_pair,
)
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def _presentation() -> dict[str, object]:
    return {
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


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name: return node
    raise SystemExit(f"missing function {name}")


def main() -> int:
    export_record = export_worldbridge_quarantine_operator_presentation(_presentation())
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    bundle = consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit)
    if validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(export_record, audit) != {"valid": True, "errors": []}:
        raise SystemExit("E244 export/audit pair invalid")
    if validate_worldbridge_quarantine_operator_evidence_bundle(bundle, export_record=export_record, audit=audit) != {"valid": True, "errors": []}:
        raise SystemExit("E244 bundle parity invalid")
    serial = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    if any(value in serial for value in ("epoch-secret", "pond-secret", "sr_runtime_epoch", "pond_lifetime_token")):
        raise SystemExit("E244 exposed opaque lifecycle values")
    for key in ("bundle_persisted", "file_written", "network_transmitted", "restore_performed", "mutation_executed", "ui_authority", "operator_action_admitted", "quarantine_clear_admitted", "same_runtime_retry_admitted", "default_ready"):
        if bundle.get(key) is not False: raise SystemExit(f"E244 policy overclaim: {key}")
    tampered_export = copy.deepcopy(export_record); tampered_export["headline"] = "wrong"; tampered_export["export_digest"] = _export_digest(tampered_export)
    if validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(tampered_export, audit).get("valid") is not False:
        raise SystemExit("E244 admitted a recomputed mismatched export")
    tampered_audit = copy.deepcopy(audit); tampered_audit["headline"] = "wrong"; tampered_audit["audit_digest"] = _audit_digest(tampered_audit)
    if validate_worldbridge_quarantine_operator_evidence_bundle_source_pair(export_record, tampered_audit).get("valid") is not False:
        raise SystemExit("E244 admitted a recomputed mismatched audit")
    tampered_bundle = copy.deepcopy(bundle); tampered_bundle["replay_admitted"] = True; tampered_bundle["bundle_digest"] = _bundle_digest(tampered_bundle)
    if validate_worldbridge_quarantine_operator_evidence_bundle(tampered_bundle).get("valid") is not False:
        raise SystemExit("E244 admitted replay authority overclaim")

    forbidden = ("PyQt6", "QWidget", "QPainter", "Pond(", "GameViewport", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "pickle", "deserialize_pond(")
    source = BUNDLE.read_text(encoding="utf-8-sig")
    if any(token in source for token in forbidden): raise SystemExit("E244 crossed Qt/runtime/I/O boundary")
    tree = ast.parse(COMMANDS.read_text(encoding="utf-8-sig"))
    handler = ast.unparse(_function(tree, "_runtime_worldbridge_quarantine_operator_evidence_bundle"))
    for expected in ("get_worldbridge_quarantine_lifecycle_host", "present_worldbridge_quarantine_lifecycle", "export_worldbridge_quarantine_operator_presentation", "audit_worldbridge_quarantine_operator_presentation_export", "consume_worldbridge_quarantine_operator_evidence_pair"):
        if expected not in handler: raise SystemExit(f"E244 command path absent: {expected}")
    if any(token in handler for token in ("_start_simulation", "_stop_simulation", "Pond(", "GameViewport", "open(")):
        raise SystemExit("E244 command gained runtime control")
    spec = get_command_registry().describe("runtime.worldbridge.quarantine_operator_evidence_bundle")
    if spec.get("mutates") is not False or spec.get("requires_gui") is not False: raise SystemExit("E244 command not read-only/headless")
    contract = build_worldbridge_quarantine_operator_evidence_bundle_contract()
    if validate_worldbridge_quarantine_operator_evidence_bundle_contract(contract) != {"valid": True, "errors": []}: raise SystemExit("E244 contract invalid")
    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_operator_evidence_bundle_contract") != contract: raise SystemExit("E244 status lost bundle contract")
    if "quarantine_operator_evidence_bundle_module" not in status.get("pilot_modules", []): raise SystemExit("E244 status lost module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False: raise SystemExit("E244 changed default boundary")
    print(json.dumps({"status": "ok", "pair_parity_valid": True, "writes_files": False, "transmits_network": False, "recovery_authority": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
