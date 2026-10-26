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

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    CONTEXT_KIND,
    DERIVATION_VERSION,
    MAX_STREAMS,
    _snapshot_digest,
    build_worldbridge_deterministic_randomness_context_contract,
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
    restore_worldbridge_deterministic_randomness_context,
    snapshot_worldbridge_deterministic_randomness_context,
    validate_worldbridge_deterministic_randomness_snapshot,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from core.Lotucosm.pond import Pond
from builtin.systems.resource_manager import ResourceManager
from builtin.systems.floating_system import FloatingSystem
from core.Lotucosm.perception import PerceptionSystem
from builtin.systems.pvaec_orchestrator import PVAECOrchestrator


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MODULE = RUNTIME / "core/Lotucosm/runtime/world_bridge_deterministic_randomness_context.py"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"


def _numpy_state_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def test_context_registers_supported_local_streams_and_validates_snapshot() -> None:
    context = create_worldbridge_deterministic_randomness_context(
        "context-001",
        "root-seed",
    )
    python_stream = register_worldbridge_deterministic_random_stream(
        context,
        "sr.script",
        "python_random",
    )
    numpy_stream = register_worldbridge_deterministic_random_stream(
        context,
        "ps.resource",
        "numpy_pcg64_generator",
    )
    assert isinstance(python_stream, random.Random)
    assert isinstance(numpy_stream, np.random.Generator)
    assert context.get_stream("sr.script") is python_stream
    assert context.get_stream("ps.resource") is numpy_stream
    snapshot = snapshot_worldbridge_deterministic_randomness_context(context)
    assert validate_worldbridge_deterministic_randomness_snapshot(snapshot) == {
        "valid": True,
        "errors": [],
    }
    assert snapshot["context_kind"] == CONTEXT_KIND
    assert snapshot["derivation_version"] == DERIVATION_VERSION
    assert snapshot["stream_count"] == 2
    assert [row["family"] for row in snapshot["streams"]] == [
        "python_random",
        "numpy_pcg64_generator",
    ]
    assert snapshot["root_seed_material_revealed"] is False


def test_named_stream_derivation_is_stable_and_registration_order_independent() -> None:
    first = create_worldbridge_deterministic_randomness_context("same", "same-seed")
    first_python = register_worldbridge_deterministic_random_stream(
        first, "one", "python_random"
    )
    first_numpy = register_worldbridge_deterministic_random_stream(
        first, "two", "numpy_pcg64_generator"
    )
    second = create_worldbridge_deterministic_randomness_context("same", "same-seed")
    second_numpy = register_worldbridge_deterministic_random_stream(
        second, "two", "numpy_pcg64_generator"
    )
    second_python = register_worldbridge_deterministic_random_stream(
        second, "one", "python_random"
    )
    assert first_python.getstate() == second_python.getstate()
    assert first_numpy.bit_generator.state == second_numpy.bit_generator.state
    first_rows = {row["stream_name"]: row for row in first.snapshot()["streams"]}
    second_rows = {row["stream_name"]: row for row in second.snapshot()["streams"]}
    for name in ("one", "two"):
        assert first_rows[name]["derivation_digest"] == second_rows[name]["derivation_digest"]
        assert first_rows[name]["state"] == second_rows[name]["state"]


def test_consumed_local_stream_state_changes_without_global_rng_change() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    context = create_worldbridge_deterministic_randomness_context("consumed", 1234)
    python_stream = register_worldbridge_deterministic_random_stream(
        context, "python", "python_random"
    )
    numpy_stream = register_worldbridge_deterministic_random_stream(
        context, "numpy", "numpy_pcg64_generator"
    )
    initial = context.snapshot()
    python_stream.random()
    numpy_stream.random()
    consumed = context.snapshot()
    python_after = random.getstate()
    numpy_after = np.random.get_state()
    assert python_before == python_after
    assert _numpy_state_equal(numpy_before, numpy_after)
    assert initial["streams"] != consumed["streams"]
    assert validate_worldbridge_deterministic_randomness_snapshot(consumed)["valid"] is True


def test_local_stream_restore_reproduces_python_and_numpy_draws_without_globals() -> None:
    context = create_worldbridge_deterministic_randomness_context("restore", "seed")
    python_stream = register_worldbridge_deterministic_random_stream(context, "python", "python_random")
    numpy_stream = register_worldbridge_deterministic_random_stream(context, "numpy", "numpy_pcg64_generator")
    python_stream.random()
    numpy_stream.random()
    checkpoint = context.snapshot()
    expected_python = [python_stream.random() for _ in range(3)]
    expected_numpy = [float(numpy_stream.random()) for _ in range(3)]
    global_python = random.getstate()
    global_numpy = np.random.get_state()

    restore_worldbridge_deterministic_randomness_context(context, checkpoint)
    assert [python_stream.random() for _ in range(3)] == expected_python
    assert [float(numpy_stream.random()) for _ in range(3)] == expected_numpy
    assert random.getstate() == global_python
    assert _numpy_state_equal(np.random.get_state(), global_numpy)


def test_local_stream_restore_rejects_registration_mismatch_without_mutation() -> None:
    source = create_worldbridge_deterministic_randomness_context("source", "seed")
    register_worldbridge_deterministic_random_stream(source, "python", "python_random")
    checkpoint = source.snapshot()
    target = create_worldbridge_deterministic_randomness_context("source", "seed")
    stream = register_worldbridge_deterministic_random_stream(target, "other", "python_random")
    before = stream.getstate()
    with pytest.raises(ValueError, match="registration mismatch"):
        restore_worldbridge_deterministic_randomness_context(target, checkpoint)
    assert stream.getstate() == before


def test_same_context_id_and_seed_produce_identical_full_snapshots() -> None:
    def make_snapshot() -> dict:
        context = create_worldbridge_deterministic_randomness_context("same", b"bytes")
        python_stream = register_worldbridge_deterministic_random_stream(
            context, "python", "python_random"
        )
        numpy_stream = register_worldbridge_deterministic_random_stream(
            context, "numpy", "numpy_pcg64_generator"
        )
        python_stream.random()
        numpy_stream.random()
        return context.snapshot()

    assert make_snapshot() == make_snapshot()


def test_registration_rejects_duplicate_invalid_and_capacity_overflow() -> None:
    context = create_worldbridge_deterministic_randomness_context("bounded", "seed")
    register_worldbridge_deterministic_random_stream(context, "one", "python_random")
    with pytest.raises(ValueError, match="already registered"):
        register_worldbridge_deterministic_random_stream(context, "one", "python_random")
    with pytest.raises(ValueError, match="unsupported"):
        register_worldbridge_deterministic_random_stream(context, "bad-family", "unknown")
    for bad_name in ("", "has space", "../escape", "x" * 97):
        with pytest.raises(ValueError):
            register_worldbridge_deterministic_random_stream(context, bad_name, "python_random")

    full = create_worldbridge_deterministic_randomness_context("full", "seed")
    for index in range(MAX_STREAMS):
        register_worldbridge_deterministic_random_stream(
            full,
            f"s{index}",
            "python_random" if index % 2 == 0 else "numpy_pcg64_generator",
        )
    with pytest.raises(ValueError, match="capacity"):
        register_worldbridge_deterministic_random_stream(full, "overflow", "python_random")


def test_registration_can_bind_existing_caller_owned_stream_without_consuming_it() -> None:
    context = create_worldbridge_deterministic_randomness_context("existing", "seed")
    stream = random.Random(123)
    before = stream.getstate()
    bound = register_worldbridge_deterministic_random_stream(
        context, "sr.runtime", "python_random", stream=stream
    )
    assert bound is stream
    assert stream.getstate() == before
    stream.random()
    checkpoint = context.snapshot()
    expected_next = stream.random()
    stream.random()
    restore_worldbridge_deterministic_randomness_context(context, checkpoint)
    assert stream.random() == expected_next

    with pytest.raises(TypeError, match="python_random"):
        register_worldbridge_deterministic_random_stream(
            context, "wrong", "python_random", stream=np.random.Generator(np.random.PCG64(1))
        )


def test_ps_pond_can_use_registered_numpy_owner_without_touching_global_rng() -> None:
    context = create_worldbridge_deterministic_randomness_context("pond-owner", "seed")
    stream = register_worldbridge_deterministic_random_stream(
        context, "ps.pond", "numpy_pcg64_generator"
    )
    global_before = np.random.get_state()
    pond = Pond(
        initialize=False,
        initial_organisms=0,
        initial_components=0,
        randomness_rng=stream,
    )
    pond.create_initial_resources()
    first = [
        (item["position"].tolist(), float(item["amount"]))
        for item in pond.resources["food"][:3]
    ]
    assert np.array_equal(np.random.get_state()[1], global_before[1])
    assert np.random.get_state()[0] == global_before[0]
    assert np.random.get_state()[2:] == global_before[2:]

    second_context = create_worldbridge_deterministic_randomness_context("pond-owner", "seed")
    second_stream = register_worldbridge_deterministic_random_stream(
        second_context, "ps.pond", "numpy_pcg64_generator"
    )
    second = Pond(initialize=False, initial_organisms=0, initial_components=0, randomness_rng=second_stream)
    second.create_initial_resources()
    assert first == [
        (item["position"].tolist(), float(item["amount"]))
        for item in second.resources["food"][:3]
    ]


def test_pond_binds_owner_to_runtime_added_organisms_and_components() -> None:
    from builtin.components.components_base import ComponentBase
    from builtin.entity_types.organism import Organism

    context = create_worldbridge_deterministic_randomness_context("pond-dynamic-owner", "seed")
    stream = register_worldbridge_deterministic_random_stream(
        context, "ps.pond", "numpy_pcg64_generator"
    )
    pond = Pond(initialize=False, initial_organisms=0, initial_components=0)
    pond.set_randomness_owner(stream)

    organism = Organism("runtime-added", (10.0, 20.0))
    assert pond.add_organism(organism)
    assert organism.randomness_rng is stream

    from core.Lotucosm.scripts import ScriptBase
    script = ScriptBase()
    organism.add_script(script)
    assert script.randomness_rng is stream

    component = ComponentBase("runtime-component", position=(1.0, 2.0))
    pond.add_floating_component(component)
    assert component.randomness_rng is stream

    attached = ComponentBase("attached-component", position=(5.0, 6.0))
    assert organism.add_component(attached)
    assert attached.randomness_rng is stream

    membrane = ComponentBase("runtime-membrane", position=(7.0, 8.0))
    organism.set_membrane(membrane)
    assert membrane.randomness_rng is stream

    replacement_context = create_worldbridge_deterministic_randomness_context(
        "pond-dynamic-owner-rebind", "seed"
    )
    replacement_stream = register_worldbridge_deterministic_random_stream(
        replacement_context, "ps.pond", "numpy_pcg64_generator"
    )
    pond.set_randomness_owner(replacement_stream)
    assert organism.randomness_rng is replacement_stream
    assert script.randomness_rng is replacement_stream
    assert attached.randomness_rng is replacement_stream
    assert membrane.randomness_rng is replacement_stream
    assert component.randomness_rng is replacement_stream

    replacement = ComponentBase("replacement-component", position=(3.0, 4.0))
    pond.replace_floating_components([replacement])
    assert replacement.randomness_rng is replacement_stream


def test_resource_manager_uses_the_same_explicit_numpy_owner() -> None:
    context = create_worldbridge_deterministic_randomness_context("resource-owner", "seed")
    stream = register_worldbridge_deterministic_random_stream(
        context, "ps.resource", "numpy_pcg64_generator"
    )
    global_before = np.random.get_state()
    manager = ResourceManager(
        randomness_rng=stream,
        resource_spawn_rate=1.0,
        max_food=100,
        max_energy=100,
    )
    manager.generate_resources()
    manager.create_resource("food")
    assert manager.resources["food"]
    assert np.array_equal(np.random.get_state()[1], global_before[1])
    assert np.random.get_state()[0] == global_before[0]
    assert np.random.get_state()[2:] == global_before[2:]


def test_floating_system_random_helpers_use_explicit_numpy_owner() -> None:
    context = create_worldbridge_deterministic_randomness_context("floating-owner", "seed")
    stream = register_worldbridge_deterministic_random_stream(
        context, "ps.floating", "numpy_pcg64_generator"
    )
    global_before = np.random.get_state()
    system = FloatingSystem(randomness_rng=stream)
    first = (system._random(), system._normal(2).tolist(), system._uniform(1, 3))
    assert len(first[1]) == 2
    assert np.array_equal(np.random.get_state()[1], global_before[1])
    assert np.random.get_state()[0] == global_before[0]
    assert np.random.get_state()[2:] == global_before[2:]


def test_perception_and_pvaec_use_explicit_numpy_owner() -> None:
    context = create_worldbridge_deterministic_randomness_context("pvaec-owner", "seed")
    stream = register_worldbridge_deterministic_random_stream(
        context, "ps.pvaec", "numpy_pcg64_generator"
    )
    global_before = np.random.get_state()
    perception = PerceptionSystem(noise_level=0.1, randomness_rng=stream)
    result = perception.add_noise({"x": 0.0, "y": np.asarray([0.0, 0.0])})
    assert "x" in result and result["y"].shape == (2,)
    orchestrator = PVAECOrchestrator(randomness_rng=stream)
    parent = type("Parent", (), {"position": (10.0, 20.0)})()
    child_position = orchestrator._child_position(parent, type("Env", (), {"size": (100.0, 100.0), "randomness_rng": stream})())
    assert len(child_position) == 2
    assert np.array_equal(np.random.get_state()[1], global_before[1])
    assert np.random.get_state()[0] == global_before[0]
    assert np.random.get_state()[2:] == global_before[2:]


def test_root_seed_policy_rejects_ambiguous_values() -> None:
    with pytest.raises(ValueError):
        create_worldbridge_deterministic_randomness_context("id", True)
    with pytest.raises(ValueError):
        create_worldbridge_deterministic_randomness_context("id", "")
    with pytest.raises(ValueError):
        create_worldbridge_deterministic_randomness_context("id", b"")
    with pytest.raises(TypeError):
        create_worldbridge_deterministic_randomness_context("id", 1.5)
    with pytest.raises(ValueError):
        create_worldbridge_deterministic_randomness_context("has space", "seed")


def test_snapshot_is_copy_isolated_and_digest_tampering_rejects() -> None:
    context = create_worldbridge_deterministic_randomness_context("copy", "seed")
    register_worldbridge_deterministic_random_stream(context, "python", "python_random")
    original = context.snapshot()
    mutated = copy.deepcopy(original)
    mutated["streams"][0]["state"]["internal_state"][0] ^= 1
    assert validate_worldbridge_deterministic_randomness_snapshot(original)["valid"] is True
    assert validate_worldbridge_deterministic_randomness_snapshot(mutated)["valid"] is False
    assert "snapshot_digest_mismatch" in validate_worldbridge_deterministic_randomness_snapshot(mutated)[
        "errors"
    ]

    resealed = copy.deepcopy(original)
    resealed["default_ready"] = True
    resealed["snapshot_digest"] = _snapshot_digest(resealed)
    assert "default_ready_mismatch" in validate_worldbridge_deterministic_randomness_snapshot(
        resealed
    )["errors"]


def test_snapshot_validator_rejects_extra_missing_and_malformed_structure() -> None:
    context = create_worldbridge_deterministic_randomness_context("shape", "seed")
    register_worldbridge_deterministic_random_stream(context, "python", "python_random")
    snapshot = context.snapshot()
    extra = copy.deepcopy(snapshot)
    extra["extra"] = True
    extra["snapshot_digest"] = _snapshot_digest(extra)
    assert "snapshot_keys_mismatch" in validate_worldbridge_deterministic_randomness_snapshot(extra)[
        "errors"
    ]
    missing = copy.deepcopy(snapshot)
    del missing["streams"]
    missing["snapshot_digest"] = _snapshot_digest(missing)
    assert "snapshot_keys_mismatch" in validate_worldbridge_deterministic_randomness_snapshot(
        missing
    )["errors"]
    malformed = copy.deepcopy(snapshot)
    malformed["streams"][0]["family"] = "native"
    malformed["snapshot_digest"] = _snapshot_digest(malformed)
    errors = validate_worldbridge_deterministic_randomness_snapshot(malformed)["errors"]
    assert "stream_family_invalid" in errors


def test_context_contract_is_deterministic_and_does_not_touch_global_rngs() -> None:
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    first = build_worldbridge_deterministic_randomness_context_contract()
    second = build_worldbridge_deterministic_randomness_context_contract()
    python_after = random.getstate()
    numpy_after = np.random.get_state()
    assert first == second
    assert python_before == python_after
    assert _numpy_state_equal(numpy_before, numpy_after)
    assert first["contract_valid"] is True
    assert first["snapshot_validation"] == {"valid": True, "errors": []}
    assert first["caller_owned"] is True
    assert first["default_tick_attached"] is False
    for field in (
        "uses_python_hash",
        "uses_wall_time",
        "uses_os_entropy",
        "global_python_random_touched",
        "global_numpy_random_touched",
        "replay_input",
        "checkpoint_state",
        "replay_admitted",
        "default_ready",
    ):
        assert first[field] is False
    assert first["restore_api_exposed"] is True


def test_source_has_no_hash_call_or_global_seed_restore_and_default_viewport_is_free() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "hash":
            forbidden.append("hash")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {
                "seed",
                "setstate",
                "set_state",
            }:
                owner = node.func.value
                if not isinstance(owner, ast.Name) or owner.id not in {"stream", "python_stream"}:
                    forbidden.append(node.func.attr)
    assert forbidden == []
    viewport_source = VIEWPORT.read_text(encoding="utf-8")
    assert "set_worldbridge_opt_in_deterministic_randomness_context" in viewport_source
    assert "_worldbridge_opt_in_deterministic_randomness_context" in viewport_source
    assert "_worldbridge_opt_in_deterministic_randomness_context = context" in viewport_source


def test_runtime_status_nests_static_context_contract_without_default_adoption() -> None:
    contract = build_worldbridge_deterministic_randomness_context_contract()
    status = build_runtime_worldbridge_status()
    assert status["opt_in_deterministic_randomness_context_contract"] == contract
    assert "deterministic_randomness_context_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_context_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_rng_context", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.build_worldbridge_deterministic_randomness_context_contract()
    assert contract["qt_free"] is True
    assert contract["contract_valid"] is True
