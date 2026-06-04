"""
迭代与演化闭环相关单测。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import random
import unittest
from unittest.mock import patch

from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.entity_types.organism import Organism
from builtin.entity_types.reproduction import try_simple_reproduction
from builtin.systems.inheritance import InheritanceSystem
from builtin.systems.pvaec_orchestrator import PVAECOrchestrator
from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.pond import Pond


class MemoryGeneCopyTests(unittest.TestCase):
    def test_copy_is_shallow_independent_action_pattern(self):
        g = MemoryGene("ctx", {"a": 0.5, "b": -0.2}, 0.7)
        g.strength = 0.8
        g.age = 3
        c = g.copy()
        self.assertIsNot(c, g)
        self.assertEqual(c.situation, g.situation)
        self.assertEqual(c.action_pattern, g.action_pattern)
        self.assertIsNot(c.action_pattern, g.action_pattern)
        c.action_pattern["a"] = 9.0
        self.assertNotEqual(g.action_pattern["a"], 9.0)


class InheritanceMemoryGeneTests(unittest.TestCase):
    def test_inherit_copies_memory_genes_when_rate_satisfied(self):
        parent = Organism("par1", (10.0, 20.0))
        mg = MemoryGene("s", {"t": 0.1}, 0.5)
        parent.memory_genes.append(mg)
        inh = InheritanceSystem()
        inh.set_memory_gene_inheritance_rate(1.0)
        inh.set_mutation_rate(0.0)
        with patch.object(random, "random", return_value=0.0):
            child = inh.inherit(parent, (11.0, 21.0))
        self.assertGreaterEqual(len(child.memory_genes), 1)
        self.assertIsNot(child.memory_genes[0], mg)
        self.assertEqual(child.memory_genes[0].situation, mg.situation)


class PVAECOrchestratorTests(unittest.TestCase):
    def test_run_cycle_maintains_population_size(self):
        pond = Pond(name="orch", size=(400.0, 300.0), initial_organisms=0, initial_components=0)
        orgs = [Organism(f"o{i}", (float(20 + i * 5), 50.0)) for i in range(4)]
        orch = PVAECOrchestrator(maintain_population_size=True)
        out = orch.run_cycle(orgs, pond)
        self.assertEqual(len(out), 4)


class PondEvolutionIterationTests(unittest.TestCase):
    class _FakeOrch:
        def run_cycle(self, organisms, environment):
            return [
                Organism(f"gen_{i}", (12.0 + i, 14.0), generation=1) for i in range(len(organisms))
            ]

    def test_iteration_increments_on_generation_interval(self):
        pond = Pond(
            name="evo_pond",
            size=(200.0, 200.0),
            initial_organisms=0,
            initial_components=0,
            evolution_generation_interval=5,
            pvaec_orchestrator=self._FakeOrch(),
        )
        pond.add_organism(Organism("seed", (30.0, 40.0)))
        self.assertEqual(pond.iteration, 0)
        for _ in range(4):
            pond.update()
        self.assertEqual(pond.iteration, 0)
        pond.update()
        self.assertEqual(pond.iteration, 1)


class ReproductionInheritanceTests(unittest.TestCase):
    def test_try_simple_reproduction_use_inheritance(self):
        pond = Pond(name="rep", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        parent = IntelligentOrganism("p1", (50.0, 50.0), energy=150.0, max_energy=200.0)
        pond.add_organism(parent)
        child = try_simple_reproduction(parent, pond, min_energy_ratio=0.5, use_inheritance=True)
        self.assertIsNotNone(child)
        self.assertIn(child.id, pond.organisms)
        self.assertIsInstance(child, Organism)


class PondIntervalGuardTests(unittest.TestCase):
    def test_non_positive_evolution_interval_becomes_none(self):
        pond = Pond(
            name="iv0",
            size=(100.0, 100.0),
            initial_organisms=0,
            initial_components=0,
            evolution_generation_interval=0,
            pvaec_orchestrator=object(),
        )
        self.assertIsNone(pond.evolution_generation_interval)
        pond2 = Pond(
            name="ivn",
            size=(100.0, 100.0),
            initial_organisms=0,
            initial_components=0,
            evolution_generation_interval=-3,
            pvaec_orchestrator=object(),
        )
        self.assertIsNone(pond2.evolution_generation_interval)


if __name__ == "__main__":
    unittest.main()
