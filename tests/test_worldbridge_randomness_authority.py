# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
import random
from pathlib import Path

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    AUTHORITY_IDS,
    CAPTURED_AUTHORITY_IDS,
    UNCAPTURED_AUTHORITY_IDS,
    _capture_digest,
    build_worldbridge_randomness_authority_contract,
    build_worldbridge_randomness_authority_inventory,
    build_worldbridge_rng_checkpoint_state,
    build_randomness_owner_inventory,
    capture_worldbridge_global_random_states,
    restore_worldbridge_global_random_states,
    validate_worldbridge_global_random_state_capture,
    validate_worldbridge_rng_checkpoint_state,
    validate_randomness_owner_inventory,
)


def test_explicit_global_random_restore_reproduces_next_values() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    try:
        capture = capture_worldbridge_global_random_states(capture_id="restore-proof")
        expected_python = random.random()
        expected_numpy = float(np.random.random())

        random.random()
        np.random.random()
        restore_worldbridge_global_random_states(capture)

        assert random.random() == expected_python
        assert float(np.random.random()) == expected_numpy
    finally:
        random.setstate(python_before)
        np.random.set_state(numpy_before)


def test_global_random_restore_rejects_tampering_without_mutation() -> None:
    capture = capture_worldbridge_global_random_states(capture_id="restore-tamper")
    before_python = random.getstate()
    before_numpy = np.random.get_state()
    capture["capture_digest"] = "0" * 64
    with pytest.raises(ValueError):
        restore_worldbridge_global_random_states(capture)
    assert random.getstate() == before_python
    assert _numpy_state_equal(np.random.get_state(), before_numpy)


def test_global_random_restore_rolls_back_python_if_numpy_apply_fails(monkeypatch) -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    capture = capture_worldbridge_global_random_states(capture_id="restore-rollback")
    try:
        random.random()
        np.random.random()
        target_python = random.getstate()
        target_numpy = np.random.get_state()
        original_set_state = np.random.set_state
        calls = 0

        def fail_once(state):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("injected NumPy state apply failure")
            return original_set_state(state)

        monkeypatch.setattr(np.random, "set_state", fail_once)
        with pytest.raises(RuntimeError, match="rolled back"):
            restore_worldbridge_global_random_states(capture)
        assert random.getstate() == target_python
        assert _numpy_state_equal(np.random.get_state(), target_numpy)
    finally:
        random.setstate(python_before)
        np.random.set_state(numpy_before)


def test_randomness_authority_advertises_only_opt_in_global_restore() -> None:
    contract = build_worldbridge_randomness_authority_contract()
    assert contract["restore_api_exposed"] is True
    assert contract["restore_api"] == "restore_worldbridge_global_random_states"
    assert contract["global_state_restore_is_opt_in"] is True
    assert contract["global_state_restore_thread_atomic"] is False
    assert contract["global_state_restore_cross_authority_atomic"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_randomness_authority.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"
POND = RUNTIME / "core/Lotucosm/pond.py"
ASSEMBLY = RUNTIME / "builtin/systems/assembly_system.py"
INHERITANCE = RUNTIME / "builtin/systems/inheritance.py"
FLOATING = RUNTIME / "builtin/systems/floating_system.py"
TEMPLATE = RUNTIME / "builtin/templates/official_cell_behavior.py"
ENTITY = RUNTIME / "core/Lotucosm/entity.py"
PROCEDURAL = RUNTIME / "core/Lotucosm/sr_game_procedural.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _method(tree: ast.Module, class_name: str, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == name:
                    return member
    raise AssertionError(f"missing method {class_name}.{name}")


def test_inventory_is_complete_conservative_and_ordered() -> None:
    inventory = build_worldbridge_randomness_authority_inventory()
    assert [row["authority_id"] for row in inventory] == list(AUTHORITY_IDS)
    assert len(inventory) == 5
    assert set(CAPTURED_AUTHORITY_IDS) == {
        "python_process_global_random",
        "numpy_legacy_global_randomstate",
    }
    assert set(UNCAPTURED_AUTHORITY_IDS) == {
        "explicit_caller_owned_rng_instances",
        "dynamic_script_plugin_entropy",
        "native_extension_or_third_party_rng",
    }
    rows = {row["authority_id"]: row for row in inventory}
    assert rows["python_process_global_random"]["state_api"] == "random.getstate"
    assert rows["numpy_legacy_global_randomstate"]["state_api"] == "numpy.random.get_state"
    for row in inventory:
        assert row["initial_seed_sufficient"] is False
        assert row["observed_sites"]
        assert row["consumption_boundary"]
        assert row["project_configuration_coverage"]
    for authority_id in UNCAPTURED_AUTHORITY_IDS:
        assert rows[authority_id]["capture_status"] in {
            "not_captured",
            "unknown_not_captured",
        }


def test_contract_is_deterministic_and_does_not_observe_or_advance_global_rngs() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    first = build_worldbridge_randomness_authority_contract()
    second = build_worldbridge_randomness_authority_contract()
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    assert first == second
    assert python_before == python_after
    assert _numpy_state_equal(numpy_before, numpy_after)
    assert first["contract_valid"] is True
    assert first["example_capture_validation"] == {"valid": True, "errors": []}
    assert first["status_construction_reads_global_rng_state"] is False
    assert first["status_construction_advances_global_rng_state"] is False
    assert first["restore_api_exposed"] is True
    assert first["global_state_restore_is_opt_in"] is True
    for field in (
        "initial_seed_sufficient",
        "all_authorities_captured",
        "cross_lane_consumption_order_captured",
        "common_clock_captured",
        "atomic_checkpoint",
        "lossless",
        "replay_admitted",
        "default_ready",
    ):
        assert first[field] is False


def test_explicit_capture_is_side_effect_free_and_only_observes_two_global_states() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    capture = capture_worldbridge_global_random_states(capture_id="e221-side-effect-proof")
    python_after = random.getstate()
    numpy_after = np.random.get_state()

    assert python_before == python_after
    assert _numpy_state_equal(numpy_before, numpy_after)
    assert validate_worldbridge_global_random_state_capture(capture) == {
        "valid": True,
        "errors": [],
    }
    assert capture["captured_authority_ids"] == list(CAPTURED_AUTHORITY_IDS)
    assert capture["uncaptured_authority_ids"] == list(UNCAPTURED_AUTHORITY_IDS)
    assert set(capture["authorities"]) == set(CAPTURED_AUTHORITY_IDS)
    for field in (
        "thread_atomic",
        "cross_authority_atomic",
        "global_states_advanced_by_capture",
        "global_states_reseeded",
        "restore_performed",
        "restore_api_exposed",
        "initial_seed_sufficient",
        "all_authorities_captured",
        "cross_lane_consumption_order_captured",
        "dynamic_entropy_boundary_closed",
        "native_entropy_boundary_closed",
        "replay_input",
        "checkpoint_state",
        "replay_admitted",
        "default_ready",
    ):
        assert capture[field] is False


def test_capture_is_copy_isolated_and_rejects_bad_ids() -> None:
    first = capture_worldbridge_global_random_states(capture_id="copy-isolation")
    original = copy.deepcopy(first)
    first["authorities"]["python_process_global_random"]["internal_state"][0] ^= 1
    second = capture_worldbridge_global_random_states(capture_id="copy-isolation-2")
    assert first != original
    assert second["capture_id"] == "copy-isolation-2"
    assert validate_worldbridge_global_random_state_capture(original)["valid"] is True
    for bad_id in ("", "has space", "../escape", "x" * 129):
        with pytest.raises(ValueError):
            capture_worldbridge_global_random_states(capture_id=bad_id)


def test_initial_seed_is_not_equivalent_to_consumed_state() -> None:
    left = random.Random(221)
    right = random.Random(221)
    assert left.getstate() == right.getstate()
    right.random()
    assert left.getstate() != right.getstate()

    numpy_left = np.random.RandomState(221)
    numpy_right = np.random.RandomState(221)
    assert _numpy_state_equal(numpy_left.get_state(), numpy_right.get_state())
    numpy_right.random_sample()
    assert not _numpy_state_equal(numpy_left.get_state(), numpy_right.get_state())
    assert build_worldbridge_randomness_authority_contract()["initial_seed_sufficient"] is False


def test_validator_rejects_digest_nested_state_and_semantic_tampering() -> None:
    capture = capture_worldbridge_global_random_states(capture_id="tamper-proof")

    digest_tampered = copy.deepcopy(capture)
    digest_tampered["capture_digest"] = "0" * 64
    assert "capture_digest_mismatch" in validate_worldbridge_global_random_state_capture(
        digest_tampered
    )["errors"]

    nested_tampered = copy.deepcopy(capture)
    nested_tampered["authorities"]["numpy_legacy_global_randomstate"]["position"] = 999
    nested_tampered["capture_digest"] = _capture_digest(nested_tampered)
    assert "numpy_position_invalid" in validate_worldbridge_global_random_state_capture(
        nested_tampered
    )["errors"]

    overclaim = copy.deepcopy(capture)
    overclaim["replay_admitted"] = True
    overclaim["capture_digest"] = _capture_digest(overclaim)
    assert "replay_admitted_mismatch" in validate_worldbridge_global_random_state_capture(
        overclaim
    )["errors"]


def test_validator_handles_malformed_values_without_raising() -> None:
    assert validate_worldbridge_global_random_state_capture(None) == {
        "valid": False,
        "errors": ["capture_not_mapping"],
    }
    malformed = capture_worldbridge_global_random_states(capture_id="malformed")
    malformed["authorities"]["python_process_global_random"]["gaussian_cache"] = float("nan")
    validation = validate_worldbridge_global_random_state_capture(malformed)
    assert validation["valid"] is False
    assert "python_gaussian_cache_invalid" in validation["errors"]
    assert "capture_not_canonical_json" in validation["errors"]

    unhashable_value = copy.deepcopy(malformed)
    unhashable_value["authorities"]["numpy_legacy_global_randomstate"]["state_key"] = {1, 2}
    validation = validate_worldbridge_global_random_state_capture(unhashable_value)
    assert validation["valid"] is False
    assert "numpy_state_key_invalid" in validation["errors"]
    assert "capture_not_canonical_json" in validation["errors"]


def test_actual_bridge_functions_call_pond_update_between_sync_directions() -> None:
    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    clocked_update = _function(bridge_tree, "_invoke_clocked_pond_update")
    clocked_calls = [
        node.func.id
        for node in ast.walk(clocked_update)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "update" in clocked_calls
    entry_names = {
        "unified_pond_step": "_unified_pond_step_impl",
        "unified_pond_step_with_trace": "_unified_pond_step_with_trace_impl",
    }
    for entry_name, impl_name in entry_names.items():
        entry = _function(bridge_tree, entry_name)
        assert any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == impl_name
            for node in ast.walk(entry)
        ), f"{entry_name} must delegate to {impl_name}"
    for function_name in entry_names.values():
        function = _function(bridge_tree, function_name)
        calls = [
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "sync_sr_entity_to_organism" in calls
        assert "_invoke_clocked_pond_update" in calls
        assert "sync_organism_to_sr_display" in calls

    viewport_tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    bridge_tick = _method(
        viewport_tree,
        "GameViewport",
        "_run_unified_pond_bridge_tick_locked",
    )
    called_names = {
        node.func.id
        for node in ast.walk(bridge_tick)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert {
        "ensure_bridged_organisms",
        "unified_pond_step",
        "unified_pond_step_with_trace",
    } <= called_names


def test_rng_checkpoint_authority_binds_local_global_and_named_stream_state() -> None:
    from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
        create_worldbridge_deterministic_randomness_context,
        register_worldbridge_deterministic_random_stream,
    )

    context = create_worldbridge_deterministic_randomness_context("rng-cp", "seed")
    register_worldbridge_deterministic_random_stream(
        context, "ps.resource", "numpy_pcg64_generator"
    )
    local = random.Random(71)
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    checkpoint = build_worldbridge_rng_checkpoint_state(
        runtime_epoch="epoch-rng-cp",
        sr_runtime_rng=local,
        deterministic_context=context,
    )
    assert validate_worldbridge_rng_checkpoint_state(checkpoint) == {
        "valid": True,
        "errors": [],
    }
    assert checkpoint["complete"] is False
    assert checkpoint["replay_admitted"] is False
    assert "sr_runtime_random" in checkpoint["captured_authority_ids"]
    assert "named_deterministic_streams" in checkpoint["captured_authority_ids"]
    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)


def test_rng_checkpoint_authority_rejects_tampering_without_live_rng_access() -> None:
    checkpoint = build_worldbridge_rng_checkpoint_state(
        runtime_epoch="epoch-rng-tamper",
        sr_runtime_rng=random.Random(73),
    )
    tampered = copy.deepcopy(checkpoint)
    tampered["sr_runtime"]["internal_state"][0] ^= 1
    assert validate_worldbridge_rng_checkpoint_state(tampered) == {
        "valid": False,
        "errors": ["checkpoint_digest_mismatch"],
    }


def test_randomness_owner_inventory_binds_identity_mode_and_lifecycle() -> None:
    inventory = build_randomness_owner_inventory(
        {"sr.runtime": random.Random(73), "ps.pond": np.random.default_rng(74)},
        {"sr.runtime": "runtime", "ps.pond": "detached"},
    )
    assert inventory["owners"] == [
        {
            "identity": "ps.pond",
            "family": "numpy_pcg64_generator",
            "mode": "detached",
            "lifecycle": "active",
        },
        {
            "identity": "sr.runtime",
            "family": "python_random",
            "mode": "runtime",
            "lifecycle": "active",
        },
    ]
    assert validate_randomness_owner_inventory(inventory) == {
        "valid": True,
        "errors": [],
    }


def test_randomness_owner_inventory_rejects_digest_or_mode_tampering() -> None:
    inventory = build_randomness_owner_inventory({"sr.runtime": random.Random(75)})
    tampered = copy.deepcopy(inventory)
    tampered["owners"][0]["mode"] = "detached"
    assert validate_randomness_owner_inventory(tampered) == {
        "valid": False,
        "errors": ["owner_inventory_digest_mismatch"],
    }


def test_pond_update_retains_randomness_reachable_system_boundaries() -> None:
    update = _method(ast.parse(POND.read_text(encoding="utf-8")), "Pond", "update")
    call_names = {
        node.func.attr
        for node in ast.walk(update)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "generate_resources" in call_names
    assert "update" in call_names
    source = ast.unparse(update)
    assert "organism.update(environment=self)" in source
    assert "EvolutionRunner.apply_generation" in source


def test_inventory_is_anchored_to_remaining_identity_and_owner_sites() -> None:
    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    assert "_sr_runtime_rng" in viewport_source
    assert "random.Random()" not in viewport_source
    assert "hash((lineage_id, death_count, now))" not in viewport_source
    assert "random.Random(int(seed))" in PROCEDURAL.read_text(encoding="utf-8")
    assembly_source = ASSEMBLY.read_text(encoding="utf-8")
    assert "random_unit(self.randomness_rng)" in assembly_source
    assert "random_int(self.randomness_rng" in assembly_source
    assert "random.random" not in assembly_source
    inheritance_source = INHERITANCE.read_text(encoding="utf-8")
    assert "random_unit(self.randomness_rng)" in inheritance_source
    assert "random_int(self.randomness_rng" in inheritance_source
    assert "random.random" not in inheritance_source
    floating_source = FLOATING.read_text(encoding="utf-8")
    assert "FloatingSystem randomness owner is unavailable" in floating_source
    assert "np.random.randn" not in floating_source
    assert "np.random.random" not in floating_source
    assert "self._assembly_sequence += 1" in floating_source
    assert "uuid.uuid4" not in floating_source
    assert "uuid.uuid4" not in ENTITY.read_text(encoding="utf-8")
    template_source = TEMPLATE.read_text(encoding="utf-8")
    assert "self.random_uniform(" in template_source
    assert "import random" not in template_source


def test_script_base_binds_caller_owned_rng_without_advancing_process_global() -> None:
    from core.Lotucosm.scripts import ScriptBase

    owner = np.random.default_rng(77)
    process_before = random.getstate()
    numpy_before = np.random.get_state()

    class Entity:
        randomness_rng = owner
        pond = None

    script = ScriptBase()
    script.on_attach(Entity())
    assert script.randomness_rng is owner
    value = script.random_uniform(-1.0, 1.0)
    assert -1.0 <= value <= 1.0
    assert random.getstate() == process_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)


def test_capture_module_keeps_capture_read_only_and_restore_explicit() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    capture_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "capture_worldbridge_global_random_states"
    )
    capture_setters = [
        node.func.attr
        for node in ast.walk(capture_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"seed", "setstate", "set_state"}
    ]
    assert capture_setters == []

    restore_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "restore_worldbridge_global_random_states"
    )
    restore_setters = [
        node.func.attr
        for node in ast.walk(restore_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"setstate", "set_state"}
    ]
    assert restore_setters == ["setstate", "set_state", "setstate", "set_state"]


def test_runtime_status_nests_static_contract_without_changing_default_mode() -> None:
    contract = build_worldbridge_randomness_authority_contract()
    status = build_runtime_worldbridge_status()
    assert status["cross_lane_randomness_authority_contract"] == contract
    assert "randomness_authority_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_randomness_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_randomness", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.build_worldbridge_randomness_authority_contract()
    assert contract["qt_free"] is True
    assert contract["contract_valid"] is True

