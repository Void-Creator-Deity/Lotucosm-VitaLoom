# -*- coding: utf-8
"""社会学习模块冒烟测试。"""
from __future__ import annotations

import unittest

from builtin.entity_types.organism import Organism
from builtin.systems.inheritance import InheritanceSystem
from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.social_memory import (
    SOCIAL_SITUATION_PREFIX,
    inherit_social_memory_genes,
    is_social_memory_gene,
    maybe_record_peer_from_environment,
    observe_peer_action,
    social_memories,
    social_stage_ready,
)


class SocialMemorySmokeTests(unittest.TestCase):
    def test_observe_requires_s3_when_ladder_on(self) -> None:
        org = Organism("o1", (0.0, 0.0))
        org.social_learning_enabled = True
        org.developmental_ladder_enabled = True
        org.developmental_stage = 2
        gene = observe_peer_action(org, "p2", {"act": {"command": "explore"}}, 0.8)
        self.assertIsNone(gene)
        org.developmental_stage = 3
        gene = observe_peer_action(org, "p2", {"act": {"command": "explore"}}, 0.8)
        self.assertIsNotNone(gene)
        self.assertTrue(is_social_memory_gene(gene))
        self.assertEqual(len(social_memories(org)), 1)

    def test_social_situation_prefix(self) -> None:
        g = MemoryGene(f"{SOCIAL_SITUATION_PREFIX}peer1", {}, 0.5)
        self.assertTrue(is_social_memory_gene(g))

    def test_inheritance_copies_social_genes(self) -> None:
        import random

        random.seed(0)
        parent = Organism("p1", (0.0, 0.0))
        parent.social_learning_enabled = True
        observe_peer_action(parent, "n1", {"a": 0.3}, 0.7)
        parent.memory_genes.append(
            MemoryGene("private_situation", {"x": 1.0}, 0.6)
        )
        child = InheritanceSystem().inherit(parent, (1.0, 1.0))
        social = social_memories(child)
        self.assertGreaterEqual(len(social), 1)
        self.assertTrue(all(is_social_memory_gene(g) for g in social))

    def test_maybe_record_from_pond(self) -> None:
        from core.Lotucosm.pond import Pond

        pond = Pond(name="t", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        a = Organism("a", (10.0, 10.0))
        b = Organism("b", (12.0, 10.0))
        a.social_learning_enabled = True
        a.developmental_ladder_enabled = True
        a.developmental_stage = 3
        pond.add_organism(a)
        pond.add_organism(b)
        gene = maybe_record_peer_from_environment(
            a,
            pond,
            {"act": {"command": "explore"}},
            0.9,
        )
        self.assertIsNotNone(gene)
        self.assertTrue(social_stage_ready(a))


if __name__ == "__main__":
    unittest.main()
