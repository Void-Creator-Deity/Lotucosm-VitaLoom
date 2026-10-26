# -*- coding: utf-8 -*-
"""E235 evidence for SR-local randomness ownership and explicit non-admissions."""
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
import random
import sys
from pathlib import Path

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    DEFAULT_SR_RUNTIME_SEED,
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


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
MODULE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_sr_runtime_randomness.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def _class(tree: ast.AST, class_name: str) -> ast.ClassDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"missing class {class_name}")


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for member in _class(tree, class_name).body:
        if isinstance(member, ast.FunctionDef) and member.name == method_name:
            return member
    raise AssertionError(f"missing method {class_name}.{method_name}")


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _self_attribute(node: ast.AST, attribute: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == attribute
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _keyword_is_sr_owner(call: ast.Call) -> bool:
    return any(keyword.arg == "rng" and _self_attribute(keyword.value, "_sr_runtime_rng") for keyword in call.keywords)


def test_seed_resolution_prefers_additive_sr_seed_then_proc_seed_then_default() -> None:
    assert resolve_sr_runtime_randomness_config({"pond_config": {"sr_runtime_seed": "77", "proc_seed": 66}}) == SrRuntimeRandomnessConfig(77, "pond_config.sr_runtime_seed")
    assert resolve_sr_runtime_randomness_config({"pond_config": {"proc_seed": -5}}) == SrRuntimeRandomnessConfig(-5, "pond_config.proc_seed")
    assert resolve_sr_runtime_randomness_config({"pond_config": {"sr_runtime_seed": True, "proc_seed": False}}) == SrRuntimeRandomnessConfig(DEFAULT_SR_RUNTIME_SEED, "constant_12345")
    assert resolve_sr_runtime_randomness_config({"pond_config": {"sr_runtime_seed": "not-an-int", "proc_seed": None}}) == SrRuntimeRandomnessConfig(DEFAULT_SR_RUNTIME_SEED, "constant_12345")
    assert resolve_sr_runtime_randomness_config(None) == SrRuntimeRandomnessConfig(DEFAULT_SR_RUNTIME_SEED, "constant_12345")


def test_caller_owned_rng_is_reproducible_and_does_not_touch_global_rngs() -> None:
    config = SrRuntimeRandomnessConfig(235, "pond_config.sr_runtime_seed")
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    first = create_sr_runtime_randomness_rng(config)
    second = create_sr_runtime_randomness_rng(config)
    first_values = [first.uniform(-20.0, 20.0), first.random(), first.randrange(1000)]
    second_values = [second.uniform(-20.0, 20.0), second.random(), second.randrange(1000)]
    assert first_values == second_values
    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)
    with pytest.raises(TypeError, match="SrRuntimeRandomnessConfig"):
        create_sr_runtime_randomness_rng(object())  # type: ignore[arg-type]


def test_detached_entity_fallback_is_stable_and_global_rng_neutral() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    left = create_detached_sr_entity_randomness_rng("id-235", "organism", (1.25, -3.5), 22.0)
    right = create_detached_sr_entity_randomness_rng("id-235", "organism", (1.25, -3.5), 22.0)
    changed = create_detached_sr_entity_randomness_rng("id-236", "organism", (1.25, -3.5), 22.0)
    assert [left.uniform(-20, 20), left.uniform(-20, 20)] == [right.uniform(-20, 20), right.uniform(-20, 20)]
    assert left.getstate() != changed.getstate()
    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)


def test_contract_is_static_and_validator_rejects_cross_lane_overclaims() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    contract = build_worldbridge_sr_runtime_randomness_contract()
    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)
    assert contract["contract_valid"] is True
    assert contract["seed_resolution"] == list(SEED_SOURCES)
    assert validate_worldbridge_sr_runtime_randomness_contract(contract) == {"valid": True, "errors": []}
    for field in (
        "bridge_rng_context_transport",
        "bridge_seed_agreement",
        "bridge_rng_state_checkpoint",
        "cross_lane_consumption_order_captured",
        "atomic_checkpoint",
        "replay_admitted",
        "default_ready",
    ):
        tampered = copy.deepcopy(contract)
        tampered[field] = True
        result = validate_worldbridge_sr_runtime_randomness_contract(tampered)
        assert result["valid"] is False
        assert f"{field}_overclaim" in result["errors"]


def test_qt_free_contract_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    module_name = "_qt_free_worldbridge_sr_randomness_e235"
    spec = importlib.util.spec_from_file_location(module_name, MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        contract = module.build_worldbridge_sr_runtime_randomness_contract()
    finally:
        sys.modules.pop(module_name, None)
    assert contract["qt_free"] is True
    assert contract["contract_valid"] is True


def test_viewport_sources_configure_one_owner_before_entity_construction_and_use_it() -> None:
    source = VIEWPORT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert "random" not in imports
    assert "random.Random()" not in source
    assert "hash((lineage_id, death_count, now))" not in source

    load = _method(tree, "GameViewport", "_load_scene_runtime_entities")
    configure_lines = [
        node.lineno
        for node in ast.walk(load)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _self_attribute(node.func, "_configure_sr_runtime_randomness")
    ]
    entity_lines = [
        node.lineno
        for node in ast.walk(load)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _self_attribute(node.func, "_SceneRuntimeEntity")
    ]
    assert configure_lines and entity_lines and min(configure_lines) < min(entity_lines)

    constructions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _self_attribute(node.func, "_SceneRuntimeEntity")
    ]
    assert constructions
    assert all(_keyword_is_sr_owner(call) for call in constructions)

    entity_init = _method(tree, "_SceneRuntimeEntity", "__init__")
    assert "create_detached_sr_entity_randomness_rng" in ast.unparse(entity_init)
    assert "velocity_rng.uniform" in ast.unparse(entity_init)


def test_viewport_paths_route_mutation_respawn_and_nutrients_to_sr_owner() -> None:
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    spawn = _method(tree, "GameViewport", "_process_organism_with_membrane_spawn")
    mutation_calls = [
        node for node in ast.walk(spawn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "mutate_signal_edges"
    ]
    assert len(mutation_calls) == 1
    assert _self_attribute(mutation_calls[0].args[-1], "_sr_runtime_rng")

    respawn = _method(tree, "GameViewport", "_apply_sr_respawn_mind_mutation_if_admitted")
    respawn_source = ast.unparse(respawn)
    assert "_worldbridge_opt_in_respawn_streams" in respawn_source
    assert "self._sr_runtime_rng.random()" in respawn_source
    assert "self._sr_runtime_rng" in respawn_source

    nutrient = _method(tree, "GameViewport", "_maybe_respawn_sr_nutrients")
    uniform_calls = [
        node for node in ast.walk(nutrient)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "uniform"
    ]
    assert len(uniform_calls) >= 2
    assert all(_self_attribute(call.func.value, "_sr_runtime_rng") for call in uniform_calls)


def test_bridge_stays_unchanged_while_pond_exposes_opt_in_rng_owner() -> None:
    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    for name in ("unified_pond_step", "unified_pond_step_with_trace"):
        function = _function(bridge_tree, name)
        parameters = {argument.arg for argument in function.args.args + function.args.kwonlyargs}
        assert not {"seed", "rng", "randomness_context", "rng_context"} & parameters

    pond_tree = ast.parse(POND.read_text(encoding="utf-8"))
    update = _method(pond_tree, "Pond", "update")
    assert [argument.arg for argument in update.args.args] == ["self", "delta_time"]
    assert not update.args.kwonlyargs
    pond_init = _method(pond_tree, "Pond", "__init__")
    resources = _method(pond_tree, "Pond", "create_initial_resources")
    assert "randomness_rng" in ast.unparse(pond_init)
    assert "_random_array" in ast.unparse(resources)
    assert "_random_uniform" in ast.unparse(resources)

    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    ensure = _method(viewport_tree, "GameViewport", "_ensure_unified_pond")
    ensure_source = ast.unparse(ensure)
    assert "initial_organisms=0" in ensure_source
    assert "initial_components=0" in ensure_source
    assert "randomness_rng" in ensure_source


def test_runtime_status_nests_e235_contract_without_default_enablement() -> None:
    contract = build_worldbridge_sr_runtime_randomness_contract()
    status = build_runtime_worldbridge_status()
    assert status["sr_runtime_randomness_ownership_contract"] == contract
    assert "sr_runtime_randomness_ownership_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

