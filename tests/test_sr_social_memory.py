# -*- coding: utf-8
"""SR 社会学习冒烟测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import RuntimePeerSnapshot, SceneRuntimeTickContext
from core.Lotucosm.social_memory import (
    inherit_social_sr_memory_genes,
    is_social_memory_gene,
    maybe_record_peer_from_sr_ctx,
    observe_peer_action_sr,
    sr_social_memories,
)
from core.Lotucosm.sr_memory_gene_bridge import ensure_entity_memory_genes, inherit_sr_memory_genes


class _Ent:
    def __init__(self, eid: str = "e1"):
        self.id = eid
        self.sr_debug_hud: dict = {}


class _SocialScript(PvaecScript):
    homeostatic_pvaec_enabled = False
    social_learning_enabled = True
    developmental_ladder_enabled = True
    developmental_stage = 3

    def perceive(self, ctx):
        return {}

    def think(self, obs, dt):
        return {"ax": 1.0, "ay": 0.2}

    def act(self, dec, dt):
        return


class SrSocialMemoryTests(unittest.TestCase):
    def test_observe_sr_writes_sr_memory_genes(self) -> None:
        ent = _Ent()
        gene = observe_peer_action_sr(ent, "p2", {"ax": 2.0, "ay": -0.5}, 0.8)
        self.assertIsNotNone(gene)
        self.assertTrue(is_social_memory_gene(gene))
        self.assertEqual(len(sr_social_memories(ent)), 1)
        self.assertAlmostEqual(gene.action_pattern["ax"], 2.0)

    def test_maybe_record_from_ctx(self) -> None:
        script = _SocialScript()
        ent = _Ent()
        script.entity = ent
        peer = RuntimePeerSnapshot(
            id="p9",
            entity_type="organism",
            position=(10.0, 10.0),
            radius=18.0,
            distance=12.0,
            surface_gap=5.0,
        )
        ctx = SceneRuntimeTickContext(
            owner_id="e1",
            owner_type="organism",
            owner_position=(0.0, 0.0),
            owner_radius=18.0,
            bounds=(800, 600),
            simulation_time=1.0,
            delta_time=0.05,
            peers=(peer,),
        )
        gene = maybe_record_peer_from_sr_ctx(script, ctx, {"ax": 0.5, "ay": 0.1}, 0.9)
        self.assertIsNotNone(gene)
        self.assertEqual(ent.sr_debug_hud.get("social_memory_count"), 1)

    def test_inherit_splits_social_and_private(self) -> None:
        parent = [
            MemoryGene("private", {"ax": 1.0}, 0.6),
            MemoryGene("social:peer1", {"ax": 0.2}, 0.7),
        ]
        parent[1].strength = 0.9
        private_child = inherit_sr_memory_genes(parent, inheritance_rate=1.0, mutation_rate=0.0)
        social_child = inherit_social_sr_memory_genes(parent, rate=1.0)
        self.assertEqual(len(private_child), 1)
        self.assertFalse(is_social_memory_gene(private_child[0]))
        self.assertEqual(len(social_child), 1)
        self.assertTrue(is_social_memory_gene(social_child[0]))


if __name__ == "__main__":
    unittest.main()
