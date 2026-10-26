from __future__ import annotations

import ast
import random
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SIMULATION = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/systems/simulation.py"


def _numpy_state_equal(left, right) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def test_fallback_simulation_uses_caller_owned_rng_without_advancing_globals():
    from builtin.systems.simulation import Simulation

    python_before = random.getstate()
    numpy_before = np.random.get_state()
    first = Simulation(320, 240, enable_pygame=False, randomness_rng=random.Random(77))
    first.update()
    second = Simulation(320, 240, enable_pygame=False, randomness_rng=random.Random(77))
    second.update()

    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)
    assert [tuple(food.position) for food in first.environment.foods] == [
        tuple(food.position) for food in second.environment.foods
    ]
    assert first.randomness_rng is not second.randomness_rng


def test_fallback_simulation_source_has_no_runtime_module_global_random_draws():
    tree = ast.parse(SIMULATION.read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
            forbidden.append(node.func.attr)
    assert forbidden == ["Random"]
