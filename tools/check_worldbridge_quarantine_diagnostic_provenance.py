# -*- coding: utf-8 -*-
"""Mechanical E240 guard for WorldBridge quarantine diagnostic visibility."""
from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"

from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
    build_worldbridge_quarantine_diagnostic_provenance_contract,
    project_worldbridge_quarantine_diagnostic,
    validate_worldbridge_quarantine_diagnostic_provenance_contract,
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
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_diagnostic_provenance.py"
HOST = RUNTIME / "core" / "VitaLoom" / "simulation" / "worldbridge_quarantine_diagnostic_host.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing method: {class_name}.{method_name}")


def _receipt() -> dict[str, object]:
    return build_worldbridge_handoff_failure_receipt(
        "pond_update",
        trace_requested=False,
        preflight_completed=True,
        sr_to_ps_sync_started=True,
        pond_update_started=True,
        ps_to_sr_reflection_started=False,
        cause=RuntimeError("E240 guard fixture"),
    )


def main() -> int:
    contract = build_worldbridge_quarantine_diagnostic_provenance_contract()
    if validate_worldbridge_quarantine_diagnostic_provenance_contract(contract).get("valid") is not True:
        raise SystemExit("E240 diagnostic provenance contract validation failed")
    for field in (
        "same_runtime_safe_retry",
        "automatic_quarantine_clear",
        "cross_lane_rollback",
        "in_place_restore",
        "atomic_recovery",
        "replay_admitted",
        "default_ready",
    ):
        if contract.get("admissions", {}).get(field) is not False:
            raise SystemExit(f"E240 contract overclaimed admissions.{field}")
        tampered = copy.deepcopy(contract)
        tampered["admissions"][field] = True
        if validate_worldbridge_quarantine_diagnostic_provenance_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E240 validator accepted admissions.{field} overclaim")

    receipt = _receipt()
    decision = classify_worldbridge_handoff_failure_containment(receipt)
    admission = classify_worldbridge_opt_in_bridge_admission(
        "tick_handoff",
        unified_pond_mode=True,
        handoff_suspended=True,
        current_pond_present=True,
    )
    diagnostic = project_worldbridge_quarantine_diagnostic(
        handoff_suspended=True,
        failure_receipt=receipt,
        recovery_decision=decision,
        quarantine_admission=admission,
    )
    if diagnostic.get("current_runtime_quarantined") is not True:
        raise SystemExit("E240 lost current-runtime quarantine visibility")
    if diagnostic.get("failure", {}).get("partial_mutation_possible") is not True:
        raise SystemExit("E240 lost partial mutation warning")
    if diagnostic.get("last_opt_in_bridge_admission", {}).get("admitted") is not False:
        raise SystemExit("E240 admitted quarantined bridge writer")
    boundary = diagnostic.get("fresh_lifecycle_boundary", {})
    if boundary.get("required_before_opt_in_re_admission") is not True:
        raise SystemExit("E240 lost fresh lifecycle requirement")
    if any(boundary.get(key) is not False for key in ("restores_failed_runtime_state", "replays_failed_handoff")):
        raise SystemExit("E240 diagnostic overclaimed restore or replay")

    forbidden = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    for path in (AUTHORITY, HOST):
        source = path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden):
            raise SystemExit(f"E240 read-only boundary crossed in {path.name}")

    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    query_source = ast.unparse(
        _method(viewport_tree, "GameViewport", "query_worldbridge_quarantine_diagnostic")
    )
    required = (
        "project_worldbridge_quarantine_diagnostic",
        "_worldbridge_handoff_suspended",
        "_worldbridge_last_handoff_failure",
        "_worldbridge_last_recovery_decision",
        "_worldbridge_last_quarantine_admission",
    )
    if any(token not in query_source for token in required):
        raise SystemExit("E240 viewport query lost required read-only provenance inputs")
    forbidden_query = (
        "_worldbridge_handoff_suspended =",
        "_ensure_unified_pond",
        "Pond(",
        "ensure_bridged_organisms",
        "bridge_spawned_organism",
        "unified_pond_step",
        "_start_simulation",
        "_stop_simulation",
        "_discard_scene_runtime_state",
    )
    if any(token in query_source for token in forbidden_query):
        raise SystemExit("E240 viewport diagnostic query gained mutable runtime authority")

    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_diagnostic_provenance_contract") != contract:
        raise SystemExit("E240 runtime status does not nest diagnostic contract")
    if "quarantine_diagnostic_provenance_module" not in status.get("pilot_modules", []):
        raise SystemExit("E240 runtime status lost diagnostic authority module")
    if "quarantine_diagnostic_query_host_module" not in status.get("pilot_modules", []):
        raise SystemExit("E240 runtime status lost diagnostic query host module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E240 changed dual/default-ready boundary")

    command = get_command_registry().describe("runtime.worldbridge.quarantine_diagnostic")
    if command.get("mutates") is not False or command.get("requires_gui") is not False:
        raise SystemExit("E240 diagnostic command is not headless/read-only")

    print(json.dumps({
        "status": "ok",
        "current_runtime_quarantined": True,
        "partial_mutation_warning": True,
        "fresh_lifecycle_required": True,
        "same_runtime_safe_retry": False,
        "in_place_restore": False,
        "replay_admitted": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
