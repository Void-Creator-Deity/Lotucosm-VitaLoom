# -*- coding: utf-8 -*-
"""
旧版 Lotucosm-VitaLoom 有用行为内化到新架构的回归测试。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import random
import unittest
from unittest.mock import patch

from builtin.entity_types.organism import Organism
from builtin.systems.inheritance import InheritanceSystem
from builtin.systems.mutation import MutationSystem
from core.Lotucosm.memory import MemoryGene, MemorySystem


class InheritParentScalarsTests(unittest.TestCase):
    def test_child_inherits_rates_and_health_from_parent(self):
        parent = Organism(
            "p1",
            (1.0, 2.0),
            max_energy=300.0,
            max_health=80.0,
            health=72.0,
            mutation_rate=0.02,
            inheritance_rate=0.85,
            energy_consumption_rate=0.07,
        )
        inh = InheritanceSystem()
        inh.set_mutation_rate(0.0)
        with patch.object(random, "random", return_value=0.99):
            child = inh.inherit(parent, (3.0, 4.0))
        self.assertAlmostEqual(child.max_energy, 300.0)
        self.assertAlmostEqual(child.max_health, 80.0)
        self.assertAlmostEqual(child.mutation_rate, 0.02)
        self.assertAlmostEqual(child.inheritance_rate, 0.85)
        self.assertAlmostEqual(child.energy_consumption_rate, 0.07)
        self.assertAlmostEqual(child.health, 72.0 * 0.9)


class InheritMemoryGeneStrengthTests(unittest.TestCase):
    def test_weak_memory_gene_less_likely_than_strong(self) -> None:
        parent = Organism("p_strength", (0.0, 0.0))
        child = Organism("c_strength", (1.0, 1.0))
        weak = MemoryGene("weak_ctx", {"a": 0.0}, 0.5)
        weak.strength = 0.05
        strong = MemoryGene("strong_ctx", {"b": 0.0}, 0.5)
        strong.strength = 1.0
        parent.memory_genes = [weak, strong]
        inh = InheritanceSystem()
        inh.set_memory_gene_inheritance_rate(1.0)
        inh.set_mutation_rate(0.0)
        with patch(
            "builtin.systems.inheritance.random.random",
            side_effect=[0.5, 0.0, 1.0],
        ):
            inh._inherit_memory_genes(parent, child)
        self.assertEqual(len(child.memory_genes), 1)
        self.assertEqual(child.memory_genes[0].situation, "strong_ctx")

    def test_memory_gene_mutates_after_inherit_when_rate_high(self) -> None:
        parent = Organism("p_mut", (0.0, 0.0))
        child = Organism("c_mut", (0.0, 0.0))
        mg = MemoryGene("ctx", {"t": 0.1}, 0.5)
        mg.strength = 1.0
        parent.memory_genes = [mg]
        inh = InheritanceSystem()
        inh.set_memory_gene_inheritance_rate(1.0)
        inh.set_mutation_rate(1.0)
        with patch("builtin.systems.inheritance.random.random", side_effect=[0.0, 0.0]):
            with patch.object(MemoryGene, "mutate") as mocked_mutate:
                inh._inherit_memory_genes(parent, child)
        self.assertEqual(len(child.memory_genes), 1)
        mocked_mutate.assert_called_once()


class InheritRuntimeMemoryTests(unittest.TestCase):
    def test_runtime_memories_copied_to_child_memory_system(self):
        parent = Organism("p2", (0.0, 0.0))
        parent.memory_system = MemorySystem()
        mg = MemoryGene("sit", {"a": 0.1}, 0.5)
        mg.strength = 1.0
        parent.memory_system.memories.append(mg)
        inh = InheritanceSystem()
        inh.set_memory_gene_inheritance_rate(1.0)
        inh.set_mutation_rate(0.0)
        with patch.object(random, "random", return_value=0.0):
            child = inh.inherit(parent, (1.0, 1.0))
        self.assertIsNotNone(child.memory_system)
        self.assertGreaterEqual(len(child.memory_system.memories), 1)
        self.assertAlmostEqual(child.memory_system.memories[0].strength, 0.8)


class MutationOrganismScalarsTests(unittest.TestCase):
    def test_mutate_can_adjust_energy_consumption(self):
        org = Organism("m1", (0.0, 0.0), energy_consumption_rate=0.05)
        ms = MutationSystem()
        ms.set_mutation_rate(1.0)
        with patch.object(random, "random", return_value=0.0):
            ms.mutate(org)
        self.assertNotEqual(org.energy_consumption_rate, 0.05)

    def test_mutate_calls_memory_gene_mutate(self) -> None:
        org = Organism("m2", (0.0, 0.0))
        mg = MemoryGene("ctx", {"x": 0.0}, 0.5)
        org.memory_genes = [mg]
        ms = MutationSystem()
        ms.set_mutation_rate(1.0)
        with patch.object(MemoryGene, "mutate") as mocked_mutate:
            with patch("builtin.systems.mutation.random.random", return_value=0.0):
                ms.mutate(org)
        mocked_mutate.assert_called()


class PVAECEngineCompatTests(unittest.TestCase):
    def test_process_delegates_to_process_signal(self):
        from builtin.components.PVAECEngine import PVAECEngine

        e = PVAECEngine(component_id="e1", organism_id="o1")
        self.assertEqual(e.process(10.0), e.process_signal(10.0))
