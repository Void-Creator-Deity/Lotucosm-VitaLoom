#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical guard for E233 clock/order authority non-admission."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_clock_ordering_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"
DRIVER = RUNTIME / "core" / "VitaLoom" / "viewports" / "simulation_driver.py"
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (  # noqa: E402
    build_worldbridge_clock_ordering_authority_contract,
    validate_worldbridge_clock_ordering_authority_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status  # noqa: E402


def _method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing {class_name}.{method_name}")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"missing function {name}")


def _calls(node: ast.AST) -> list[str]:
    return [
        call.func.attr
        for call in sorted(
            ast.walk(node),
            key=lambda item: (getattr(item, "lineno", -1), getattr(item, "col_offset", -1)),
        )
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    ]


def main() -> int:
    contract = build_worldbridge_clock_ordering_authority_contract()
    if validate_worldbridge_clock_ordering_authority_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E233 static clock/order contract is invalid")
    if any((contract["clock_relation"][field] is not False for field in ("shared_clock", "time_conversion_admitted"))):
        raise SystemExit("E233 admitted a common clock or time conversion")
    if any((contract["serial_handoff"][field] is not False for field in ("cross_call_ordering_admitted", "cross_thread_ordering_admitted", "atomicity_admitted"))):
        raise SystemExit("E233 admitted ordering or atomicity beyond one handoff")
    if any(contract[field] is not False for field in ("replay_admitted", "lossless", "default_ready")):
        raise SystemExit("E233 admitted replay, lossless mapping, or default readiness")

    source = AUTHORITY.read_text(encoding="utf-8")
    forbidden = ("QWidget", "QPainter", "Pond(", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio")
    if any(token in source for token in forbidden):
        raise SystemExit("E233 authority inventory crossed into UI, runtime mutation, I/O, or scheduler authority")

    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    simulation_update = _method(viewport, "GameViewport", "_update_simulation")
    pause_if = next((node for node in ast.walk(simulation_update) if isinstance(node, ast.If) and isinstance(node.test, ast.Attribute) and node.test.attr == "is_paused"), None)
    if pause_if is None or not any(isinstance(node, ast.Return) for node in ast.walk(pause_if)):
        raise SystemExit("E233 source evidence lost paused viewport early return")
    snapshot_calls = _calls(_method(viewport, "GameViewport", "run_snapshot_phase"))
    if not (snapshot_calls.index("_refresh_sr_hud") < snapshot_calls.index("_run_unified_pond_bridge_tick") < snapshot_calls.index("_publish_sr_runtime_snapshots")):
        raise SystemExit("E233 source evidence lost viewport serial handoff placement")

    driver_calls = _calls(_method(ast.parse(DRIVER.read_text(encoding="utf-8")), "SimulationDriver", "tick"))
    expected = ["prepare_simulation_tick", "run_script_phase", "run_spawn_phase", "run_actuator_phase", "run_fluid_phase", "run_physics_phase", "run_survival_phase", "run_snapshot_phase"]
    if [name for name in driver_calls if name in expected] != expected:
        raise SystemExit("E233 source evidence lost SR phase order")

    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry = _function(bridge_tree, "unified_pond_step")
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_unified_pond_step_impl" for node in ast.walk(entry)):
        raise SystemExit("E233 unified_pond_step no longer delegates to _unified_pond_step_impl")
    step = _function(bridge_tree, "_unified_pond_step_impl")
    calls = [
        node for node in ast.walk(step)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_invoke_clocked_pond_update"
    ]
    if (
        len(calls) != 1
        or len(calls[0].args) != 2
        or not all(isinstance(arg, ast.Name) for arg in calls[0].args)
        or calls[0].keywords
    ):
        raise SystemExit("E233 source evidence lost explicit bridge delta handoff")
    pond_update = _method(ast.parse(POND.read_text(encoding="utf-8")), "Pond", "update")
    increments = any(isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute) and node.target.attr == "time" and isinstance(node.op, ast.Add) and isinstance(node.value, ast.Constant) and node.value.value == 1 for node in ast.walk(pond_update))
    if not increments:
        raise SystemExit("E233 source evidence lost one-unit Pond time increment")

    status = build_runtime_worldbridge_status()
    if status.get("common_clock_cross_lane_ordering_authority_contract") != contract:
        raise SystemExit("E233 runtime status does not nest the static clock/order contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E233 changed default WorldBridge mode/readiness")

    print(json.dumps({"status": "ok", "contract_valid": True, "shared_clock": False, "time_conversion_admitted": False, "serial_handoff_only": True, "atomicity_admitted": False, "replay_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


