# -*- coding: utf-8 -*-
"""Mechanical E236 guard: phase-labelled failure isolation is not atomicity."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"

from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    build_worldbridge_transaction_failure_isolation_contract,
    validate_worldbridge_transaction_failure_isolation_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_transaction_authority.py"


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"missing function: {name}")


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing method: {class_name}.{method_name}")


def main() -> int:
    contract = build_worldbridge_transaction_failure_isolation_contract()
    if validate_worldbridge_transaction_failure_isolation_contract(contract).get("valid") is not True:
        raise SystemExit("E236 contract validation failed")
    if contract.get("failure_semantics", {}).get("partial_mutation_possible_after_live_phase_starts") is not True:
        raise SystemExit("E236 lost explicit partial-mutation warning")
    for path, field in (("failure_semantics", "rollback_performed"), ("failure_semantics", "cross_lane_transaction"), ("failure_semantics", "atomic_checkpoint"), ("admissions", "replay_admitted"), ("admissions", "default_ready")):
        if contract.get(path, {}).get(field) is not False:
            raise SystemExit(f"E236 contract overclaimed {path}.{field}")
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        if validate_worldbridge_transaction_failure_isolation_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E236 validator accepted {path}.{field} overclaim")

    module_source = MODULE.read_text(encoding="utf-8")
    forbidden = ("PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio")
    if any(token in module_source for token in forbidden):
        raise SystemExit("E236 authority module crossed UI/runtime/I-O boundary")

    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry_impl = {
        "unified_pond_step": "_unified_pond_step_impl",
        "unified_pond_step_with_trace": "_unified_pond_step_with_trace_impl",
    }
    for name, impl_name in entry_impl.items():
        entry = ast.unparse(_function(bridge_tree, name))
        if impl_name not in entry:
            raise SystemExit(f"E236 bridge {name} no longer delegates to {impl_name}")
    for name in entry_impl.values():
        source = ast.unparse(_function(bridge_tree, name))
        for required in ("_prepare_unified_pond_handoff", "PHASE_SR_TO_PS_SYNC", "PHASE_POND_UPDATE", "PHASE_PS_TO_SR_REFLECTION"):
            if required not in source:
                raise SystemExit(f"E236 bridge {name} lost {required}")
    trace_source = ast.unparse(_function(bridge_tree, "_unified_pond_step_with_trace_impl"))
    if "collect_worldbridge_live_entity_links(entities, pond)" not in trace_source:
        raise SystemExit("E236 trace lost pre-mutation live-pair admission")

    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    viewport_source = ast.unparse(_method(viewport_tree, "GameViewport", "_run_unified_pond_bridge_tick"))
    if "WorldBridgeHandoffFailure" not in viewport_source or "_worldbridge_last_handoff_failure" not in viewport_source:
        raise SystemExit("E236 viewport lost structured failure containment")

    status = build_runtime_worldbridge_status()
    if status.get("cross_lane_transaction_failure_isolation_contract") != contract:
        raise SystemExit("E236 runtime status does not nest authority contract")
    if "cross_lane_transaction_failure_isolation_module" not in status.get("pilot_modules", []):
        raise SystemExit("E236 status lost pilot module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E236 changed dual/default-ready boundary")

    print(json.dumps({"status": "ok", "failure_isolation": True, "rollback_performed": False, "atomic_checkpoint": False, "replay_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
