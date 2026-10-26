# -*- coding: utf-8 -*-
"""Mechanical E237 guard: evidence and serialization are not live cross-lane restore."""
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

from core.Lotucosm.runtime.world_bridge_checkpoint_restore_feasibility import (
    build_worldbridge_checkpoint_restore_feasibility_contract,
    validate_worldbridge_checkpoint_restore_feasibility_contract,
)
from core.Lotucosm.runtime.world_bridge_input_pause_authority import (
    build_worldbridge_input_pause_authority_contract,
)
from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    build_worldbridge_sr_runtime_randomness_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

MODULE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_checkpoint_restore_feasibility.py"
SR_SNAPSHOTS = RUNTIME / "core" / "VitaLoom" / "simulation" / "sr_runtime_snapshot_authority.py"
TRACE_PRODUCER = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_live_trace_producer.py"
POND_SERIALIZER = RUNTIME / "builtin" / "systems" / "pond_serializer.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"


def _class_method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise SystemExit(f"missing method: {class_name}.{method_name}")


def _has_function_named(tree: ast.AST, text: str) -> bool:
    return any(
        isinstance(node, ast.FunctionDef) and text in node.name.lower()
        for node in ast.walk(tree)
    )


def main() -> int:
    contract = build_worldbridge_checkpoint_restore_feasibility_contract()
    if validate_worldbridge_checkpoint_restore_feasibility_contract(contract).get("valid") is not True:
        raise SystemExit("E237 feasibility contract validation failed")
    for path, field in (
        ("decision", "cross_lane_checkpoint_available"),
        ("decision", "cross_lane_restore_available"),
        ("decision", "replay_preconditions_satisfied"),
        ("admissions", "checkpoint_restore"),
        ("admissions", "atomicity"),
        ("admissions", "rollback"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
        ("cross_lane_state_gaps", "sr_rng_state"),
    ):
        if contract.get(path, {}).get(field) is not False:
            raise SystemExit(f"E237 contract overclaimed {path}.{field}")
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        if validate_worldbridge_checkpoint_restore_feasibility_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E237 validator accepted {path}.{field} overclaim")

    module_source = MODULE.read_text(encoding="utf-8")
    forbidden = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib",
        "socket", "threading", "asyncio", "pickle", "deserialize_pond(",
    )
    if any(token in module_source for token in forbidden):
        raise SystemExit("E237 authority crossed UI, live-runtime, I/O, or persistence boundary")

    snapshot_tree = ast.parse(SR_SNAPSHOTS.read_text(encoding="utf-8-sig"))
    if _has_function_named(snapshot_tree, "restore"):
        raise SystemExit("E237 source unexpectedly added SR snapshot restore authority")

    trace_source = TRACE_PRODUCER.read_text(encoding="utf-8")
    if '"atomic_checkpoint": False' not in trace_source:
        raise SystemExit("E237 trace evidence lost explicit non-atomic checkpoint boundary")
    if _has_function_named(ast.parse(trace_source), "restore"):
        raise SystemExit("E237 source unexpectedly added trace restore authority")

    serializer_tree = ast.parse(POND_SERIALIZER.read_text(encoding="utf-8"))
    serialize_pond = _class_method(serializer_tree, "PondSerializer", "serialize_pond")
    if any(
        isinstance(node, ast.Attribute)
        and node.attr == "time"
        and isinstance(node.value, ast.Name)
        and node.value.id == "pond"
        for node in ast.walk(serialize_pond)
    ):
        raise SystemExit("E237 serializer now serializes pond.time; feasibility inventory needs review")
    deserialize_pond = _class_method(serializer_tree, "PondSerializer", "deserialize_pond")
    if not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "pond_class"
        for node in ast.walk(deserialize_pond)
    ):
        raise SystemExit("E237 source lost fresh Pond reconstruction evidence")

    pond_update = _class_method(ast.parse(POND.read_text(encoding="utf-8")), "Pond", "update")
    pond_update_source = ast.unparse(pond_update)
    for required in (
        "self.time += 1",
        "self.physics_engine.update()",
        "self.floating_system.update()",
        "self.assembly_system.update()",
        "self.resource_manager.update()",
    ):
        if required not in pond_update_source:
            raise SystemExit(f"E237 source lost Pond update stateful anchor: {required}")

    randomness = build_worldbridge_sr_runtime_randomness_contract()
    for field in (
        "sr_rng_state_checkpointed",
        "bridge_rng_state_checkpoint",
        "cross_lane_consumption_order_captured",
        "atomic_checkpoint",
        "replay_admitted",
    ):
        if randomness.get(field) is not False:
            raise SystemExit(f"E237 randomness precondition was overclaimed: {field}")
    input_authority = build_worldbridge_input_pause_authority_contract()
    for field in ("checkpoint_input_state", "input_replay_admitted"):
        if input_authority.get("admissions", {}).get(field) is not False:
            raise SystemExit(f"E237 input precondition was overclaimed: {field}")
    if input_authority.get("lifecycle", {}).get("shared_pause_reset_authority") is not False:
        raise SystemExit("E237 input authority unexpectedly admits shared lifecycle restoration")

    status = build_runtime_worldbridge_status()
    if status.get("cross_lane_checkpoint_restore_feasibility_contract") != contract:
        raise SystemExit("E237 runtime status does not nest feasibility contract")
    if "cross_lane_checkpoint_restore_feasibility_module" not in status.get("pilot_modules", []):
        raise SystemExit("E237 runtime status lost pilot module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E237 changed dual/default-ready boundary")

    print(json.dumps({
        "status": "ok",
        "cross_lane_checkpoint_available": False,
        "cross_lane_restore_available": False,
        "replay_preconditions_satisfied": False,
        "atomicity": False,
        "rollback": False,
        "default_ready": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
