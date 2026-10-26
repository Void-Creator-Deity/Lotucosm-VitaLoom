from types import SimpleNamespace

import numpy as np

from core.Lotucosm.runtime.world_bridge import sync_sr_entity_to_organism
from builtin.entity_types.organism import Organism


def test_sr_to_ps_motion_uses_atomic_motion_owner_api():
    entity = SimpleNamespace(
        position=np.array([8.0, 9.0]),
        velocity=np.array([1.0, 2.0]),
        acceleration=np.array([0.1, 0.2]),
        energy=40.0,
        health=70.0,
    )
    organism = Organism("ps-1", (0.0, 0.0), energy=10.0, health=20.0)
    sync_sr_entity_to_organism(entity, organism)
    assert organism.position.tolist() == [8.0, 9.0]
    assert organism.velocity.tolist() == [1.0, 2.0]
    assert organism.acceleration.tolist() == [0.1, 0.2]


def test_sr_to_ps_motion_failure_does_not_partially_update_owner_state():
    entity = SimpleNamespace(
        position=np.array([float("nan"), 9.0]),
        velocity=np.array([4.0, 5.0]),
        acceleration=np.array([0.3, 0.4]),
        energy=40.0,
        health=70.0,
    )
    organism = Organism("ps-2", (1.0, 2.0), energy=10.0, health=20.0)
    before = organism.position.copy(), organism.velocity.copy(), organism.acceleration.copy()
    sync_sr_entity_to_organism(entity, organism)
    assert np.array_equal(organism.position, before[0])
    assert np.array_equal(organism.velocity, before[1])
    assert np.array_equal(organism.acceleration, before[2])
