import random

import numpy as np
import pytest

from builtin.components.components_base import ComponentBase
from builtin.components.PVAECEngine import PVAECEngine
from builtin.systems.inheritance import InheritanceSystem
from builtin.systems.mutation import MutationSystem
from builtin.systems.pvaec_orchestrator import PVAECOrchestrator
from builtin.entity_types.organism import Organism
from core.Lotucosm.memory import MemoryGene


def test_mutation_primitives_require_an_explicit_owner() -> None:
    from builtin.components.components_base import ComponentBase

    component = ComponentBase("owner-required", position=(0.0, 0.0))
    gene = MemoryGene("owner-required", {"move": 0.1}, 0.5)

    with pytest.raises(RuntimeError, match="explicit randomness owner"):
        component.mutate()
    with pytest.raises(RuntimeError, match="explicit randomness owner"):
        gene.mutate()
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)


def test_inheritance_owner_does_not_advance_global_random():
    parent = Organism("parent", (0.0, 0.0))
    owner = random.Random(41)
    before = random.getstate()

    InheritanceSystem(randomness_rng=owner).inherit(parent, (1.0, 1.0))

    assert random.getstate() == before


def test_mutation_owner_does_not_advance_global_random():
    organism = Organism("organism", (0.0, 0.0))
    owner = random.Random(42)
    system = MutationSystem(randomness_rng=owner)
    system.set_mutation_rate(1.0)
    before = random.getstate()

    system.mutate(organism)

    assert random.getstate() == before


def test_owner_migrated_memory_and_component_mutation_does_not_touch_globals():
    parent = Organism("parent-with-state", (0.0, 0.0))
    parent.memory_genes.append(MemoryGene("ctx", {"move": 0.2}, 0.5))
    parent.add_component(ComponentBase("component", position=(0.0, 0.0)))
    owner = random.Random(43)
    inheritance = InheritanceSystem(randomness_rng=owner)
    inheritance.set_memory_gene_inheritance_rate(1.0)
    inheritance.set_mutation_rate(1.0)
    python_before = random.getstate()
    numpy_before = np.random.get_state()

    child = inheritance.inherit(parent, (1.0, 1.0))

    assert child.memory_genes
    assert child.components
    assert random.getstate() == python_before
    after = np.random.get_state()
    assert after[0] == numpy_before[0]
    assert np.array_equal(after[1], numpy_before[1])
    assert after[2:] == numpy_before[2:]


def test_numpy_owner_runs_complete_pvaec_cycle_without_global_rng_consumption():
    context = create_worldbridge_deterministic_randomness_context("pvaec-cycle-owner", "seed")
    owner = register_worldbridge_deterministic_random_stream(
        context, "ps.pvaec", "numpy_pcg64_generator"
    )
    pond = Pond(
        name="owner-cycle",
        size=(200.0, 160.0),
        initialize=False,
        initial_organisms=0,
        initial_components=0,
        max_population=4,
        randomness_rng=owner,
    )
    organisms = [Organism(f"org-{index}", (20.0 + index, 30.0), energy=100.0) for index in range(4)]
    orchestrator = PVAECOrchestrator(randomness_rng=owner)
    python_before = random.getstate()
    numpy_before = np.random.get_state()

    result = orchestrator.run_cycle(organisms, pond)

    assert len(result) == 4
    assert random.getstate() == python_before
    after = np.random.get_state()
    assert after[0] == numpy_before[0]
    assert np.array_equal(after[1], numpy_before[1])
    assert after[2:] == numpy_before[2:]


def test_pvaec_numpy_owner_repeats_same_cycle_trace():
    def run_once():
        context = create_worldbridge_deterministic_randomness_context("pvaec-repeat", "seed")
        owner = register_worldbridge_deterministic_random_stream(
            context, "ps.pvaec", "numpy_pcg64_generator"
        )
        pond = Pond(
            initialize=False,
            initial_organisms=0,
            initial_components=0,
            max_population=3,
            size=(200.0, 160.0),
            randomness_rng=owner,
        )
        organisms = [Organism(f"org-{index}", (20.0 + index, 30.0), energy=100.0) for index in range(3)]
        result = PVAECOrchestrator(randomness_rng=owner).run_cycle(organisms, pond)
        return [(item.id, tuple(float(value) for value in item.position)) for item in result]

    assert run_once() == run_once()


def test_pvaec_engine_owner_does_not_advance_global_random():
    engine = PVAECEngine(
        "engine-owner",
        associations={"sensor": {"actuator": 0.5}},
        exploration_rate=1.0,
        randomness_rng=random.Random(44),
    )
    python_before = random.getstate()

    result = engine.generate_control_signals({"sensor": 1.0})

    assert "actuator" in result
    assert random.getstate() == python_before
