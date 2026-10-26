from __future__ import annotations

import copy
import random

import numpy as np
import pytest

from builtin.entity_types.organism import Organism
from builtin.systems.assembly_system import AssemblySystem
from builtin.systems.floating_system import FloatingSystem
from builtin.systems.physics_engine import PhysicsEngine
from builtin.systems.resource_manager import ResourceManager
from core.Lotucosm.pond import Pond


def _pond() -> Pond:
    pond = Pond(
        name="transaction-state",
        initial_organisms=0,
        initial_components=0,
        randomness_rng=np.random.default_rng(42),
    )
    pond.add_organism(Organism("ps:a", (10.0, 20.0), energy=70.0))
    pond.physics_engine = PhysicsEngine(world_size=pond.size)
    pond.floating_system = FloatingSystem(
        world_size=pond.size, randomness_rng=pond.randomness_rng
    )
    pond.assembly_system = AssemblySystem(randomness_rng=pond.randomness_rng)
    pond.resource_manager = ResourceManager(
        world_size=pond.size, randomness_rng=pond.randomness_rng
    )
    pond._refresh_physics_targets()
    return pond


def test_runtime_snapshot_restores_live_owners_in_place_and_rng_state() -> None:
    pond = _pond()
    organism = pond.organisms["ps:a"]
    organisms = pond.organisms
    root_entities = pond.root_entities
    position = organism.position
    physics_targets = pond.physics_engine._targets
    resources_before = {
        key: [
            (tuple(item["position"]), item.get("amount"), item.get("type"))
            for item in values
        ]
        for key, values in pond.resources.items()
    }
    expected_rng = np.random.default_rng()
    expected_rng.bit_generator.state = copy.deepcopy(
        pond.randomness_rng.bit_generator.state
    )
    expected_next_random = expected_rng.random()

    snapshot = pond.capture_worldbridge_live_transaction_state()
    assert snapshot.digest
    assert pond.randomness_rng.random() == expected_next_random
    pond.randomness_rng.random()
    pond.time = 18
    organism.position[0] = 900.0
    organism.energy = 1.0
    pond.organisms.clear()
    pond.root_entities.clear()
    pond.physics_engine._targets.clear()
    pond.resources["food"].append({"position": np.array([1.0, 2.0]), "amount": 3.0})
    pond._worldbridge_input_events_last_tick.append({"sequence": 99})
    pond.add_organism(Organism("ps:new", (1.0, 1.0), energy=1.0))

    restored_digest = pond.restore_worldbridge_live_transaction_state(snapshot)

    assert restored_digest == snapshot.digest
    assert pond.organisms is organisms
    assert pond.root_entities is root_entities
    assert pond.organisms["ps:a"] is organism
    assert organism.position is position
    assert organism.position.tolist() == [10.0, 20.0]
    assert organism.energy == 70.0
    assert pond.physics_engine._targets is physics_targets
    assert pond.physics_engine._targets == [organism]
    assert "ps:new" not in pond.organisms
    resources_after = {
        key: [
            (tuple(item["position"]), item.get("amount"), item.get("type"))
            for item in values
        ]
        for key, values in pond.resources.items()
    }
    assert resources_after == resources_before
    assert pond._worldbridge_input_events_last_tick == []
    assert pond.randomness_rng.random() == expected_next_random


def test_runtime_snapshot_restores_python_random_owner() -> None:
    pond = _pond()
    owner = random.Random(1234)
    pond.script_random_owner = owner
    expected_next = random.Random(1234).random()
    snapshot = pond.capture_worldbridge_live_transaction_state()

    assert owner.random() == expected_next
    owner.random()
    pond.restore_worldbridge_live_transaction_state(snapshot)

    assert pond.script_random_owner is owner
    assert owner.random() == expected_next


def test_runtime_snapshot_rejects_opaque_mutable_owner_before_mutation() -> None:
    pond = _pond()

    class OpaqueOwner:
        __slots__ = ("value",)

        def __init__(self) -> None:
            self.value = object()

    pond.unsupported_owner = OpaqueOwner()
    with pytest.raises(TypeError, match="unsupported opaque Pond runtime owner"):
        pond.capture_worldbridge_live_transaction_state()


def test_runtime_snapshot_restores_nested_shared_and_cyclic_container_identities() -> None:
    pond = _pond()
    organism = pond.organisms["ps:a"]
    shared = {"energy": 70.0}
    left = [shared]
    right = {"shared": shared, "left": left}
    shared["cycle"] = right
    array = np.array([1.0, 2.0])
    payload = bytearray(b"before")
    organism.state_graph = left
    organism.state_cycle = right
    organism.state_array = array
    organism.state_bytes = payload
    pond.state_graph = right

    snapshot = pond.capture_worldbridge_live_transaction_state()

    shared["energy"] = 1.0
    left.append("drifted")
    right["new"] = True
    array[0] = 99.0
    payload[:] = b"after!"
    pond.restore_worldbridge_live_transaction_state(snapshot)

    assert organism.state_graph is left
    assert organism.state_cycle is right
    assert right["left"] is left
    assert left[0] is shared
    assert right["shared"] is shared
    assert shared["cycle"] is right
    assert shared["energy"] == 70.0
    assert "new" not in right
    assert organism.state_array is array
    assert array.tolist() == [1.0, 2.0]
    assert organism.state_bytes is payload
    assert payload == bytearray(b"before")
    assert pond.state_graph is right


def test_runtime_snapshot_digest_detects_shared_container_identity_drift() -> None:
    pond = _pond()
    organism = pond.organisms["ps:a"]
    first = {"value": 1}
    second = {"value": 1}
    graph = [first, second]
    organism.shared_graph = graph

    snapshot = pond.capture_worldbridge_live_transaction_state()
    graph[1] = first
    pond.restore_worldbridge_live_transaction_state(snapshot)

    assert graph[1] is second
    assert graph[1] is not first

