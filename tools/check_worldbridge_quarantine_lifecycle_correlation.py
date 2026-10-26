# -*- coding: utf-8 -*-
"""Static E241 guard for bounded WorldBridge lifecycle correlation."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
import sys
sys.path.insert(0, str(RUNTIME))

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
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_quarantine_lifecycle_correlation.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
HOST = RUNTIME / "core/VitaLoom/simulation/worldbridge_quarantine_diagnostic_host.py"
COMMANDS = RUNTIME / "core/VitaLoom/commands/runtime_commands.py"


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise SystemExit(f"E241 missing {class_name}.{method_name}")


def _diagnostic(quarantined: bool) -> dict[str, object]:
    receipt = build_worldbridge_handoff_failure_receipt(
        "pond_update", trace_requested=False, preflight_completed=True,
        sr_to_ps_sync_started=True, pond_update_started=True,
        ps_to_sr_reflection_started=False, cause=RuntimeError("guard"),
    )
    return project_worldbridge_quarantine_diagnostic(
        handoff_suspended=quarantined,
        failure_receipt=receipt,
        recovery_decision=classify_worldbridge_handoff_failure_containment(receipt),
        quarantine_admission=classify_worldbridge_opt_in_bridge_admission(
            "tick_handoff", unified_pond_mode=True,
            handoff_suspended=quarantined, current_pond_present=True,
        ),
    )


def _lifecycle(epoch: str, pond: str) -> dict[str, object]:
    value = build_worldbridge_quarantine_lifecycle_evidence(
        sr_runtime_epoch=epoch, pond_lifetime_token=pond,
    )
    if value is None:
        raise SystemExit("E241 lifecycle evidence unexpectedly absent")
    return value


def main() -> int:
    contract = build_worldbridge_quarantine_lifecycle_correlation_contract()
    if validate_worldbridge_quarantine_lifecycle_correlation_contract(contract).get("valid") is not True:
        raise SystemExit("E241 baseline contract invalid")
    for field in (
        "same_runtime_safe_retry", "automatic_quarantine_clear",
        "fresh_boundary_is_state_recovery", "cross_lane_rollback",
        "in_place_restore", "replay_admitted",
        "cross_adapter_lifecycle_correlation", "default_ready",
    ):
        if contract.get("admissions", {}).get(field) is not False:
            raise SystemExit(f"E241 contract overclaimed admissions.{field}")
        tampered = copy.deepcopy(contract)
        tampered["admissions"][field] = True
        if validate_worldbridge_quarantine_lifecycle_correlation_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E241 validator accepted admissions.{field} overclaim")

    failure = _lifecycle("epoch-1", "pond-1")
    disposal = build_worldbridge_quarantine_disposal_observation(
        failure_lifecycle=failure, active_lifecycle=failure,
        disposal_boundary="simulation_stop", handoff_suspended=True,
    )
    if disposal is None:
        raise SystemExit("E241 failed to observe explicit quarantined disposal")
    fresh = project_worldbridge_quarantine_lifecycle_correlation(
        diagnostic=_diagnostic(False), failure_lifecycle=failure,
        disposal_observation=disposal, current_lifecycle=_lifecycle("epoch-2", "pond-2"),
    )
    if fresh.get("correlation", {}).get("fresh_instance_boundary_observed") is not True:
        raise SystemExit("E241 rejected a fully new same-adapter pair")
    for partial in (_lifecycle("epoch-2", "pond-1"), _lifecycle("epoch-1", "pond-2")):
        result = project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=_diagnostic(False), failure_lifecycle=failure,
            disposal_observation=disposal, current_lifecycle=partial,
        )
        if result.get("correlation", {}).get("fresh_instance_boundary_observed") is not False:
            raise SystemExit("E241 treated a partially changed tuple as fresh")

    forbidden = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    for path in (AUTHORITY, HOST):
        source = path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden):
            raise SystemExit(f"E241 read-only boundary crossed in {path.name}")

    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    query = ast.unparse(_method(tree, "GameViewport", "query_worldbridge_quarantine_lifecycle_correlation"))
    required = (
        "project_worldbridge_quarantine_lifecycle_correlation",
        "query_worldbridge_quarantine_diagnostic",
        "_worldbridge_failure_lifecycle",
        "_worldbridge_disposal_observation",
        "_worldbridge_current_lifecycle_evidence",
    )
    if any(token not in query for token in required):
        raise SystemExit("E241 query lost required read-only lifecycle inputs")
    forbidden_query = (
        "_worldbridge_handoff_suspended =", "_ensure_unified_pond", "Pond(",
        "_start_simulation", "_stop_simulation", "_discard_scene_runtime_state",
    )
    if any(token in query for token in forbidden_query):
        raise SystemExit("E241 lifecycle query gained mutable authority")

    source = VIEWPORT.read_text(encoding="utf-8")
    for method_name, boundary in (
        ("_discard_scene_runtime_state", "scene_runtime_discard"),
        ("_stop_simulation", "simulation_stop"),
    ):
        method = ast.unparse(_method(tree, "GameViewport", method_name))
        observe = method.find("_observe_worldbridge_quarantine_lifecycle_disposal")
        end_epoch = method.find("_end_sr_snapshot_lifetime")
        clear_pond = method.find("self._unified_pond = None")
        clear_suspend = method.find("self._worldbridge_handoff_suspended = False")
        if min(observe, end_epoch, clear_pond, clear_suspend) < 0 or not (observe < end_epoch < clear_pond < clear_suspend):
            raise SystemExit(f"E241 {method_name} lost ordered disposal boundary")
        if boundary not in method:
            raise SystemExit(f"E241 {method_name} lost disposal boundary label")

    ensure = ast.unparse(_method(tree, "GameViewport", "_ensure_unified_pond"))
    if ensure.find("Pond(") < 0 or ensure.find("_worldbridge_active_pond_lifetime_token") < ensure.find("Pond("):
        raise SystemExit("E241 Pond lifetime token was not assigned after construction")
    failure_handler = ast.unparse(_method(tree, "GameViewport", "_run_unified_pond_bridge_tick"))
    capture = failure_handler.find("self._worldbridge_failure_lifecycle")
    suspend = failure_handler.find("self._worldbridge_handoff_suspended = True")
    if capture < 0 or suspend < 0 or capture > suspend:
        raise SystemExit("E241 failure lifecycle was not captured before suspension")

    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_lifecycle_correlation_contract") != contract:
        raise SystemExit("E241 runtime status does not nest lifecycle contract")
    if "quarantine_lifecycle_correlation_module" not in status.get("pilot_modules", []):
        raise SystemExit("E241 runtime status lost lifecycle module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E241 changed dual/default-ready boundary")
    command = get_command_registry().describe("runtime.worldbridge.quarantine_lifecycle_correlation")
    if command.get("mutates") is not False or command.get("requires_gui") is not False:
        raise SystemExit("E241 command is not headless/read-only")

    print(json.dumps({
        "status": "ok", "fresh_boundary_observed": True,
        "partial_tuple_rejected": True, "same_runtime_safe_retry": False,
        "fresh_boundary_is_state_recovery": False,
        "cross_adapter_lifecycle_correlation": False, "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
