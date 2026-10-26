from __future__ import annotations

import random

import numpy as np


def _numpy_state_equal(left, right) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


def test_default_ps_randomness_owners_do_not_touch_legacy_numpy_global_state():
    from builtin.systems.floating_system import FloatingSystem
    from builtin.systems.resource_manager import ResourceManager
    from core.Lotucosm.perception import PerceptionSystem
    from core.Lotucosm.pond import Pond

    python_before = random.getstate()
    numpy_before = np.random.get_state()
    pond = Pond(initialize=False, initial_organisms=0, initial_components=0)
    pond.create_initial_resources()
    ResourceManager(resource_spawn_rate=1.0).create_resource("food")
    FloatingSystem()._normal(2)
    PerceptionSystem(noise_level=0.1).add_noise(0.0)

    assert random.getstate() == python_before
    assert _numpy_state_equal(np.random.get_state(), numpy_before)
