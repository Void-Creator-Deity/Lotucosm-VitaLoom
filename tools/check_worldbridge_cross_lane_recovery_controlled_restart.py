# -*- coding: utf-8 -*-
"""Mechanical E238 guard: quarantine/restart classification is not recovery."""
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

from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    build_worldbridge_recovery_compensation_controlled_restart_contract,
    classify_worldbridge_handoff_failure_containment,
    validate_worldbridge_recovery_compensation_controlled_restart_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

MODULE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_recovery_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing method: {class_name}.{method_name}")


def main() -> int:
    contract = build_worldbridge_recovery_compensation_controlled_restart_contract()
    if validate_worldbridge_recovery_compensation_controlled_restart_contract(contract).get("valid") is not True:
        raise SystemExit("E238 recovery authority validation failed")
    for path, field in (
        ("compensation", "cross_lane_rollback"),
        ("compensation", "inverse_mutation_compensation"),
        ("compensation", "in_place_sr_ps_restore"),
        ("compensation", "atomic_recovery"),
        ("admissions", "cross_lane_rollback"),
        ("admissions", "in_place_restore"),
        ("admissions", "atomic_recovery"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
    ):
        if contract.get(path, {}).get(field) is not False:
            raise SystemExit(f"E238 contract overclaimed {path}.{field}")
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        if validate_worldbridge_recovery_compensation_controlled_restart_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E238 validator accepted {path}.{field} overclaim")
    restart = contract.get("fresh_restart_boundary", {})
    if restart.get("discard_current_sr_runtime_instance") is not True or restart.get("discard_current_ps_pond_instance") is not True:
        raise SystemExit("E238 lost fresh lifecycle discard boundary")
    if any(restart.get(field) is not False for field in ("reuses_partially_mutated_pond", "restores_prior_state", "replays_failed_handoff")):
        raise SystemExit("E238 fresh restart became restoration/replay")

    decision = classify_worldbridge_handoff_failure_containment({
        "phase": "pond_update",
        "failure_isolated": True,
        "rollback_performed": False,
        "cross_lane_transaction": False,
        "atomic_checkpoint": False,
        "partial_mutation_possible": True,
    })
    if decision.get("host_action") != "suspend_future_opt_in_handoffs_for_current_runtime":
        raise SystemExit("E238 classifier lost current-runtime suspension action")
    if decision.get("compensation_performed") is not False or decision.get("controlled_fresh_restart", {}).get("restores_failed_runtime_state") is not False:
        raise SystemExit("E238 classifier overclaimed state repair")

    module_source = MODULE.read_text(encoding="utf-8")
    forbidden = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    if any(token in module_source for token in forbidden):
        raise SystemExit("E238 authority crossed UI, live-runtime, I/O, or persistence boundary")

    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    bridge_source = ast.unparse(_method(viewport_tree, "GameViewport", "_run_unified_pond_bridge_tick"))
    if "_worldbridge_handoff_suspended" not in bridge_source:
        raise SystemExit("E238 viewport lost handoff quarantine")
    if "classify_worldbridge_handoff_failure_containment" not in bridge_source:
        raise SystemExit("E238 viewport lost Qt-free receipt classification")
    if bridge_source.index("_worldbridge_handoff_suspended") > bridge_source.index("_ensure_unified_pond"):
        raise SystemExit("E238 quarantine executes too late, after Pond reuse")
    for method_name in ("_discard_scene_runtime_state", "_stop_simulation"):
        source = ast.unparse(_method(viewport_tree, "GameViewport", method_name))
        if "self._unified_pond = None" not in source or "self._worldbridge_handoff_suspended = False" not in source:
            raise SystemExit(f"E238 {method_name} lost explicit fresh-runtime discard/reset")

    status = build_runtime_worldbridge_status()
    if status.get("cross_lane_recovery_compensation_controlled_restart_contract") != contract:
        raise SystemExit("E238 runtime status does not nest recovery contract")
    if "cross_lane_recovery_compensation_controlled_restart_module" not in status.get("pilot_modules", []):
        raise SystemExit("E238 runtime status lost pilot module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E238 changed dual/default-ready boundary")

    print(json.dumps({
        "status": "ok",
        "future_opt_in_handoff_suspension": True,
        "controlled_fresh_restart": True,
        "cross_lane_rollback": False,
        "in_place_restore": False,
        "replay_admitted": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
