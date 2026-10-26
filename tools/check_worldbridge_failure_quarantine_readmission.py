# -*- coding: utf-8 -*-
"""Mechanical E239 guard for complete WorldBridge current-runtime quarantine."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
sys.path.insert(0, str(RUNTIME))

from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
    OPT_IN_BRIDGE_ENTRY_POINTS,
    build_worldbridge_failure_quarantine_readmission_contract,
    classify_worldbridge_opt_in_bridge_admission,
    validate_worldbridge_failure_quarantine_readmission_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

MODULE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_readmission_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing method: {class_name}.{method_name}")


def main() -> int:
    contract = build_worldbridge_failure_quarantine_readmission_contract()
    if validate_worldbridge_failure_quarantine_readmission_contract(contract).get("valid") is not True:
        raise SystemExit("E239 quarantine/readmission contract validation failed")
    if contract.get("guarded_entry_points") != sorted(OPT_IN_BRIDGE_ENTRY_POINTS):
        raise SystemExit("E239 lost a known opt-in bridge writer")
    for path, field in (
        ("quarantine", "same_runtime_re_admission"),
        ("quarantine", "automatic_re_admission"),
        ("fresh_instance_re_admission_boundary", "reuses_partially_mutated_pond"),
        ("fresh_instance_re_admission_boundary", "restores_failed_runtime_state"),
        ("fresh_instance_re_admission_boundary", "replays_failed_handoff"),
        ("admissions", "same_runtime_safe_retry"),
        ("admissions", "automatic_quarantine_clear"),
        ("admissions", "cross_lane_rollback"),
        ("admissions", "in_place_restore"),
        ("admissions", "atomic_recovery"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
    ):
        if contract.get(path, {}).get(field) is not False:
            raise SystemExit(f"E239 contract overclaimed {path}.{field}")
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        if validate_worldbridge_failure_quarantine_readmission_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E239 validator accepted {path}.{field} overclaim")

    for entry in OPT_IN_BRIDGE_ENTRY_POINTS:
        decision = classify_worldbridge_opt_in_bridge_admission(
            entry,
            unified_pond_mode=True,
            handoff_suspended=True,
            current_pond_present=True,
        )
        if decision.get("admitted") is not False or decision.get("may_construct_or_reuse_pond") is not False:
            raise SystemExit(f"E239 admitted quarantined {entry}")
        if decision.get("may_call_sr_ps_bridge_mutator") is not False:
            raise SystemExit(f"E239 permits bridge mutation for quarantined {entry}")

    module_source = MODULE.read_text(encoding="utf-8")
    forbidden = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    if any(token in module_source for token in forbidden):
        raise SystemExit("E239 authority crossed UI, live-runtime, I/O, or persistence boundary")

    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for method_name, entry, mutator in (
        ("_ensure_unified_bridge_for_scene", "scene_prebridge", "ensure_bridged_organisms"),
        ("_process_organism_with_membrane_spawn", "spawn_bridge", "bridge_spawned_organism"),
        ("_run_unified_pond_bridge_tick", "tick_handoff", "_ensure_unified_pond"),
    ):
        source = ast.unparse(_method(tree, "GameViewport", method_name))
        if entry not in source or source.index(entry) > source.index(mutator):
            raise SystemExit(f"E239 {method_name} admits bridge mutation before quarantine gate")
    for method_name in ("_discard_scene_runtime_state", "_stop_simulation"):
        source = ast.unparse(_method(tree, "GameViewport", method_name))
        if source.index("self._unified_pond = None") > source.index("self._worldbridge_handoff_suspended = False"):
            raise SystemExit(f"E239 {method_name} clears quarantine before dropping Pond")

    status = build_runtime_worldbridge_status()
    if status.get("failure_quarantine_opt_in_handoff_readmission_contract") != contract:
        raise SystemExit("E239 runtime status does not nest quarantine contract")
    if "failure_quarantine_opt_in_handoff_readmission_module" not in status.get("pilot_modules", []):
        raise SystemExit("E239 runtime status lost pilot module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E239 changed dual/default-ready boundary")

    print(json.dumps({
        "status": "ok",
        "guarded_entry_points": sorted(OPT_IN_BRIDGE_ENTRY_POINTS),
        "same_runtime_safe_retry": False,
        "automatic_quarantine_clear": False,
        "replay_admitted": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
