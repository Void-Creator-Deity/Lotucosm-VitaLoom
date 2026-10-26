#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mechanical guard for E234 SR-local input/lifecycle non-admission."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_input_pause_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
INPUT_STATE = RUNTIME / "core" / "VitaLoom" / "viewports" / "sr_input_state.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
DRIVER = RUNTIME / "core" / "VitaLoom" / "viewports" / "simulation_driver.py"
GAME_TICK = RUNTIME / "core" / "Lotucosm" / "scene_runtime" / "game_tick.py"
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_input_pause_authority import (  # noqa: E402
    build_worldbridge_input_pause_authority_contract,
    validate_worldbridge_input_pause_authority_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (  # noqa: E402
    build_runtime_worldbridge_status,
)


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
        for call in sorted(ast.walk(node), key=lambda item: (getattr(item, "lineno", -1), getattr(item, "col_offset", -1)))
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    ]


def _self_call(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "self"
        and call.func.attr == name
        for call in ast.walk(node)
    )


def main() -> int:
    contract = build_worldbridge_input_pause_authority_contract()
    if validate_worldbridge_input_pause_authority_contract(contract) != {"valid": True, "errors": []}:
        raise SystemExit("E234 static input/lifecycle contract is invalid")
    if any(contract["ps_input"][field] is not False for field in ("pond_update_input_argument", "shared_queue", "shared_event_log", "ps_received_sr_input")):
        raise SystemExit("E234 admitted PS input routing, queue, or event log")
    if any(contract["admissions"][field] is not False for field in contract["admissions"]):
        raise SystemExit("E234 admitted input ordering, replay, checkpoint, atomicity, mapping, or readiness")
    if contract["lifecycle"]["shared_pause_reset_authority"] is not False:
        raise SystemExit("E234 admitted a shared pause/reset authority")

    authority_source = AUTHORITY.read_text(encoding="utf-8")
    forbidden = ("QWidget", "QPainter", "Pond(", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "queue.Queue", "deque(")
    if any(token in authority_source for token in forbidden):
        raise SystemExit("E234 authority inventory crossed into UI, runtime mutation, I/O, or queue ownership")

    input_tree = ast.parse(INPUT_STATE.read_text(encoding="utf-8"))
    input_snapshot = _method(input_tree, "SrInputState", "snapshot")
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "frozenset" for node in ast.walk(input_snapshot)):
        raise SystemExit("E234 source evidence lost immutable SR key snapshot")
    if not any(isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute) and target.attr == "_mouse_left_clicked" for target in node.targets) and isinstance(node.value, ast.Constant) and node.value.value is False for node in ast.walk(input_snapshot)):
        raise SystemExit("E234 source evidence lost click-edge consumption")

    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    snapshot_gate = _method(viewport, "GameViewport", "_sr_input_snapshot")
    if "is_playing" not in ast.unparse(snapshot_gate) or "is_paused" not in ast.unparse(snapshot_gate) or "empty_snapshot" not in ast.unparse(snapshot_gate):
        raise SystemExit("E234 source evidence lost inactive/paused empty input gate")
    for method_name in ("_start_simulation", "_pause_simulation", "_resume_simulation", "_stop_simulation", "_discard_scene_runtime_state"):
        if not _self_call(_method(viewport, "GameViewport", method_name), "_sr_input_clear"):
            raise SystemExit(f"E234 source evidence lost SR input clear for {method_name}")
    bridge_tick = _method(viewport, "GameViewport", "_run_unified_pond_bridge_tick")
    if not any(isinstance(node, ast.Try) for node in ast.walk(bridge_tick)):
        raise SystemExit("E234 source evidence lost bridge exception isolation")

    driver_calls = _calls(_method(ast.parse(DRIVER.read_text(encoding="utf-8")), "SimulationDriver", "tick"))
    if not (driver_calls.index("prepare_simulation_tick") < driver_calls.index("run_script_phase") < driver_calls.index("run_snapshot_phase")):
        raise SystemExit("E234 source evidence lost SR input-before-script-before-snapshot ordering")
    snapshot_calls = _calls(_method(viewport, "GameViewport", "run_snapshot_phase"))
    if not (snapshot_calls.index("_run_unified_pond_bridge_tick") < snapshot_calls.index("_publish_sr_runtime_snapshots")):
        raise SystemExit("E234 source evidence lost opt-in bridge placement")

    game_calls = _calls(_function(ast.parse(GAME_TICK.read_text(encoding="utf-8")), "step_game_runtime"))
    if not (game_calls.index("_sr_input_snapshot") < game_calls.index("_run_script_tick_batch")) or "_run_unified_pond_bridge_tick" in game_calls:
        raise SystemExit("E234 game mode input/bridge distinction changed")

    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry = _function(bridge_tree, "unified_pond_step")
    if "input" in {argument.arg for argument in entry.args.args + entry.args.kwonlyargs}:
        raise SystemExit("E234 source evidence found bridge input parameter")
    if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_unified_pond_step_impl" for node in ast.walk(entry)):
        raise SystemExit("E234 unified_pond_step no longer delegates to _unified_pond_step_impl")
    step = _function(bridge_tree, "_unified_pond_step_impl")
    update_calls = [
        node
        for node in ast.walk(step)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_invoke_clocked_pond_update"
    ]
    if len(update_calls) != 1 or len(update_calls[0].args) != 2 or not all(isinstance(argument, ast.Name) for argument in update_calls[0].args) or update_calls[0].keywords:
        raise SystemExit("E234 source evidence found Pond input routing")
        raise SystemExit("E234 source evidence found Pond input routing")

    status = build_runtime_worldbridge_status()
    if status.get("shared_queued_input_pause_reset_authority_contract") != contract:
        raise SystemExit("E234 runtime status does not nest static input/pause contract")
    if status.get("runtime_mode") != "dual" or status.get("default_ready") is not False:
        raise SystemExit("E234 changed default WorldBridge mode/readiness")

    print(json.dumps({"status": "ok", "contract_valid": True, "sr_local_input_only": True, "shared_queue": False, "input_replay_admitted": False, "shared_pause_reset_authority": False, "atomicity_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
