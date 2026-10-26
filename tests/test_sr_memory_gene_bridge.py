# -*- coding: utf-8
"""SR MemoryGene 桥接与 reafference verify 测试。"""
from __future__ import annotations

import random
import unittest

from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.sr_interoception import combined_verify_success, reafference_consistency
from core.Lotucosm.sr_memory_gene_bridge import (
    adopt_entity_memory_gene,
    inherit_sr_memory_genes,
    memory_gene_from_dict,
    memory_gene_to_dict,
    memory_genes_from_dicts,
    replace_entity_memory_genes,
    retrieve_sr_memory_bias,
    situation_from_observation,
    store_sr_memory_from_pvaec,
)


class _FakeEntity:
    pass


class SrMemoryGeneBridgeTests(unittest.TestCase):
    def test_roundtrip_dict(self) -> None:
        g = MemoryGene("ctx|a=1", {"ax": 0.5, "ay": -0.2}, 0.7)
        g.strength = 0.9
        restored = memory_gene_from_dict(memory_gene_to_dict(g))
        self.assertEqual(restored.situation, g.situation)
        self.assertAlmostEqual(restored.action_pattern["ax"], 0.5)
        self.assertAlmostEqual(restored.success_rate, 0.7)

    def test_inherit_respects_strength(self) -> None:
        parent = [
            MemoryGene("weak", {"ax": 0.0}, 0.4),
            MemoryGene("strong", {"ax": 1.0}, 0.9),
        ]
        parent[0].strength = 0.1
        parent[1].strength = 1.0
        rng = random.Random(42)
        child = inherit_sr_memory_genes(parent, inheritance_rate=1.0, mutation_rate=0.0, rng=rng)
        situations = {g.situation for g in child}
        self.assertIn("strong", situations)

    def test_adopt_enforces_capacity_and_rejects_invalid_before_mutation(self) -> None:
        ent = _FakeEntity()
        weak = MemoryGene("weak", {}, 0.2)
        weak.strength = 0.1
        strong = MemoryGene("strong", {}, 0.8)
        strong.strength = 0.9
        adopt_entity_memory_gene(ent, weak, max_genes=1)
        adopt_entity_memory_gene(ent, strong, max_genes=1)
        self.assertEqual([gene.situation for gene in ent.sr_memory_genes], ["strong"])
        with self.assertRaises(TypeError):
            adopt_entity_memory_gene(ent, object())  # type: ignore[arg-type]
        self.assertEqual([gene.situation for gene in ent.sr_memory_genes], ["strong"])

    def test_replace_is_atomic_and_preserves_existing_list_identity(self) -> None:
        ent = _FakeEntity()
        original = MemoryGene("original", {}, 0.5)
        adopt_entity_memory_gene(ent, original)
        list_identity = id(ent.sr_memory_genes)
        replacement = [MemoryGene("a", {}, 0.5), MemoryGene("b", {}, 0.5)]
        with self.assertRaises(TypeError):
            replace_entity_memory_genes(ent, [replacement[0], object()])  # type: ignore[list-item]
        self.assertEqual(ent.sr_memory_genes, [original])
        replace_entity_memory_genes(ent, replacement, max_genes=1)
        self.assertEqual(id(ent.sr_memory_genes), list_identity)
        self.assertEqual(len(ent.sr_memory_genes), 1)
        self.assertEqual(ent.sr_memory_genes[0].situation, "b")

    def test_store_respects_custom_capacity(self) -> None:
        ent = _FakeEntity()
        obs = {"sensor_pull": 0.1}
        store_sr_memory_from_pvaec(ent, obs, {"ax": 1.0, "ay": 0.0}, 0.8, max_genes=0)
        self.assertEqual(ent.sr_memory_genes, [])

    def test_store_and_retrieve_bias(self) -> None:
        ent = _FakeEntity()
        obs = {
            "sensor_pull": 0.5,
            "actuator_pull": 0.1,
            "niche_pressure": 0.2,
            "intrinsic_speed": 10.0,
            "ambient_field": 100.0,
        }
        store_sr_memory_from_pvaec(ent, obs, {"ax": 3.0, "ay": -2.0}, 0.8)
        bx, by = retrieve_sr_memory_bias(obs, ent.sr_memory_genes, blend=1.0)
        self.assertAlmostEqual(bx, 3.0)
        self.assertAlmostEqual(by, -2.0)

    def test_props_deserialize(self) -> None:
        data = [{"situation": "x", "action_pattern": {"ax": 1.0}, "success_rate": 0.6, "strength": 0.8}]
        genes = memory_genes_from_dicts(data)
        self.assertEqual(len(genes), 1)
        self.assertEqual(genes[0].situation, "x")

    def test_situation_stable(self) -> None:
        s = situation_from_observation({"sensor_pull": 0.1234, "actuator_pull": 0.0})
        self.assertIn("sensor_pull=0.123", s)


class ReafferenceVerifyTests(unittest.TestCase):
    def test_reafference_high_when_motion_matches(self) -> None:
        score = reafference_consistency((0.0, 0.0), (3.0, 4.0), 60.0, 80.0, 0.05)
        self.assertGreater(score, 0.4)

    def test_combined_verify_blend(self) -> None:
        c = combined_verify_success(1.0, 0.0, homeo_weight=0.65)
        self.assertAlmostEqual(c, 0.65)


if __name__ == "__main__":
    unittest.main()
