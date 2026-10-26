# -*- coding: utf-8 -*-
"""Mechanical E235 guard for SR-local randomness ownership boundaries."""
from __future__ import annotations

import ast
import copy
import json
import random
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    SEED_SOURCES,
    SrRuntimeRandomnessConfig,
    build_worldbridge_sr_runtime_randomness_contract,
    create_detached_sr_entity_randomness_rng,
    create_sr_runtime_randomness_rng,
    resolve_sr_runtime_randomness_config,
    validate_worldbridge_sr_runtime_randomness_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
MODULE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_sr_runtime_randomness.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise SystemExit(f"E235 missing class {name}")


def _method(tree: ast.AST, class_name: str, name: str) -> ast.FunctionDef:
    for member in _class(tree, class_name).body:
        if isinstance(member, ast.FunctionDef) and member.name == name:
            return member
    raise SystemExit(f"E235 missing method {class_name}.{name}")


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"E235 missing function {name}")


def _self_attribute(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == name and isinstance(node.value, ast.Name) and node.value.id == "self"


def main() -> int:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    contract = build_worldbridge_sr_runtime_randomness_contract()
    config = resolve_sr_runtime_randomness_config({"pond_config": {"sr_runtime_seed": 235}})
    local_rng = create_sr_runtime_randomness_rng(config)
    detached_rng = create_detached_sr_entity_randomness_rng("e235", "organism", (1.0, 2.0), 20.0)
    local_sample = local_rng.random()
    detached_sample = detached_rng.random()
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    if config != SrRuntimeRandomnessConfig(235, "pond_config.sr_runtime_seed"):
        raise SystemExit("E235 additive SR seed resolution changed")
    if not isinstance(local_sample, float) or not isinstance(detached_sample, float):
        raise SystemExit("E235 caller-owned RNG construction failed")
    if python_before != python_after or not _numpy_state_equal(numpy_before, numpy_after):
        raise SystemExit("E235 SR-local helpers advanced a process-global RNG")
    if contract.get("contract_valid") is not True:
        raise SystemExit("E235 static SR randomness contract is invalid")
    if contract.get("seed_resolution") != list(SEED_SOURCES):
        raise SystemExit("E235 seed resolution order changed")
    for field in (
        "bridge_rng_context_transport",
        "bridge_seed_agreement",
        "bridge_rng_state_checkpoint",
        "cross_lane_consumption_order_captured",
        "atomic_checkpoint",
        "replay_admitted",
        "default_ready",
    ):
        if contract.get(field) is not False:
            raise SystemExit(f"E235 contract overclaimed {field}")
        tampered = copy.deepcopy(contract)
        tampered[field] = True
        if validate_worldbridge_sr_runtime_randomness_contract(tampered).get("valid") is not False:
            raise SystemExit(f"E235 validator accepted {field} overclaim")

    module_source = MODULE.read_text(encoding="utf-8")
    forbidden_module_tokens = (
        "PyQt6", "QWidget", "Pond(", "open(", "Path(", "requests", "urllib", "socket", "threading", "asyncio", "queue.Queue", "deque(",
    )
    if any(token in module_source for token in forbidden_module_tokens):
        raise SystemExit("E235 SR ownership module crossed into UI/runtime/I-O/queue authority")

    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    viewport_tree = ast.parse(viewport_source)
    imported = {alias.name for node in ast.walk(viewport_tree) if isinstance(node, ast.Import) for alias in node.names}
    if "random" in imported or "random.Random()" in viewport_source or "hash((lineage_id, death_count, now))" in viewport_source:
        raise SystemExit("E235 legacy GameViewport entropy/hash source returned")
    load = _method(viewport_tree, "GameViewport", "_load_scene_runtime_entities")
    configured = [node.lineno for node in ast.walk(load) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and _self_attribute(node.func, "_configure_sr_runtime_randomness")]
    constructed = [node.lineno for node in ast.walk(load) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and _self_attribute(node.func, "_SceneRuntimeEntity")]
    if not configured or not constructed or min(configured) >= min(constructed):
        raise SystemExit("E235 loader does not configure the SR owner before entity construction")
    all_constructions = [node for node in ast.walk(viewport_tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and _self_attribute(node.func, "_SceneRuntimeEntity")]
    if not all_constructions or any(not any(keyword.arg == "rng" and _self_attribute(keyword.value, "_sr_runtime_rng") for keyword in call.keywords) for call in all_constructions):
        raise SystemExit("E235 runtime entity construction bypassed the SR RNG owner")
    mutation = _method(viewport_tree, "GameViewport", "_process_organism_with_membrane_spawn")
    mutation_calls = [node for node in ast.walk(mutation) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "mutate_signal_edges"]
    if len(mutation_calls) != 1 or not mutation_calls[0].args or not _self_attribute(mutation_calls[0].args[-1], "_sr_runtime_rng"):
        raise SystemExit("E235 signal-edge mutation bypassed the SR RNG owner")
    respawn_source = ast.unparse(_method(viewport_tree, "GameViewport", "_apply_sr_respawn_mind_mutation_if_admitted"))
    if "_worldbridge_opt_in_respawn_streams" not in respawn_source or "self._sr_runtime_rng.random()" not in respawn_source:
        raise SystemExit("E235 respawn owner/opt-in stream precedence changed")

    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry_impl = {
        "unified_pond_step": "_unified_pond_step_impl",
        "unified_pond_step_with_trace": "_unified_pond_step_with_trace_impl",
    }
    for name, impl_name in entry_impl.items():
        entry = _function(bridge_tree, name)
        if not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == impl_name for node in ast.walk(entry)):
            raise SystemExit(f"E235 {name} no longer delegates to {impl_name}")
    for name in entry_impl.values():
        function = _function(bridge_tree, name)
        parameters = {argument.arg for argument in function.args.args + function.args.kwonlyargs}
        if {"seed", "rng", "randomness_context", "rng_context"} & parameters:
            raise SystemExit("E235 incorrectly admitted bridge RNG transport")
    pond_tree = ast.parse(POND.read_text(encoding="utf-8"))
    update = _method(pond_tree, "Pond", "update")
    update_parameters = {argument.arg for argument in update.args.args + update.args.kwonlyargs}
    if {"seed", "rng", "randomness_context", "rng_context"} & update_parameters:
        raise SystemExit("E235 incorrectly admitted Pond RNG context")
    if [argument.arg for argument in update.args.args][:1] != ["self"] or "delta_time" not in update_parameters:
        raise SystemExit("E235 Pond.update lost the explicit shared delta parameter")
        raise SystemExit("E235 incorrectly admitted Pond RNG context")
    pond_init_source = ast.unparse(_method(pond_tree, "Pond", "__init__"))
    resources_source = ast.unparse(_method(pond_tree, "Pond", "create_initial_resources"))
    if "randomness_rng" not in pond_init_source or "_random_array" not in resources_source:
        raise SystemExit("E235 lost explicit PS RNG owner seam")

    status = build_runtime_worldbridge_status()
    if status.get("sr_runtime_randomness_ownership_contract") != contract:
        raise SystemExit("E235 runtime status does not nest SR randomness contract")
    if "sr_runtime_randomness_ownership_module" not in status.get("pilot_modules", []):
        raise SystemExit("E235 runtime status lost SR randomness pilot module")
    if status.get("runtime_mode") != "dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False:
        raise SystemExit("E235 changed WorldBridge dual/default-ready boundary")

    print(json.dumps({"status": "ok", "contract_valid": True, "sr_local_owner": True, "bridge_rng_context_transport": False, "bridge_seed_agreement": False, "replay_admitted": False, "default_ready": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

