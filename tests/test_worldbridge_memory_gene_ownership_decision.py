# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import random
import unittest
from unittest.mock import patch

from builtin.entity_types.organism import Organism
from builtin.systems.inheritance import InheritanceSystem
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge import sr_entity_to_organism
from core.Lotucosm.runtime.world_bridge import bridge_spawned_organism, sync_sr_entity_to_organism
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    capture_worldbridge_ps_checkpoint,
    capture_worldbridge_sr_checkpoint,
)
from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
    restore_sr_runtime_snapshot_slice,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit
from core.Lotucosm.sr_memory_gene_bridge import (
    inherit_sr_memory_genes,
    load_sr_memory_genes_from_props,
)


class WorldBridgeMemoryGeneOwnershipDecisionTests(unittest.TestCase):
    def test_sr_descriptor_memory_genes_are_copied_into_ps_without_sharing_objects(self) -> None:
        entity = EntityBase("sr-memory-owner", position=(4.0, 5.0))
        load_sr_memory_genes_from_props(
            entity,
            {
                "initial_memory_genes": [
                    {
                        "situation": "sensor_pull=1",
                        "action_pattern": {"turn": 0.25},
                        "success_rate": 0.75,
                        "strength": 0.8,
                        "age": 3,
                    }
                ]
            },
        )
        pond = Pond(initial_organisms=0, initial_components=0)

        organism = sr_entity_to_organism(entity, pond)

        self.assertEqual(len(entity.sr_memory_genes), 1)
        self.assertEqual(len(organism.memory_genes), 1)
        self.assertEqual(organism.memory_genes[0].situation, "sensor_pull=1")
        self.assertIsNot(organism.memory_genes[0], entity.sr_memory_genes[0])
        self.assertIsNot(
            organism.memory_genes[0].action_pattern,
            entity.sr_memory_genes[0].action_pattern,
        )
        self.assertNotEqual(id(entity.sr_memory_genes), id(organism.memory_genes))

    def test_ps_inheritance_clones_and_reweights_memory_gene_as_evolutionary_behavior(self) -> None:
        parent = Organism("ps-parent", (1.0, 2.0))
        gene = MemoryGene("ctx", {"move": 0.4}, 0.6)
        gene.strength = 0.8
        gene.age = 2
        parent.memory_genes.append(gene)
        inheritance = InheritanceSystem()
        inheritance.set_memory_gene_inheritance_rate(1.0)
        inheritance.set_mutation_rate(0.0)

        # The production contract intentionally weights inheritance by gene strength.
        # Pin the RNG so this test verifies cloning/reweighting instead of sampling luck.
        with patch("builtin.systems.inheritance.random.random", return_value=0.0):
            child = inheritance.inherit(parent, (2.0, 3.0))

        self.assertEqual(len(child.memory_genes), 1)
        inherited = child.memory_genes[0]
        self.assertIsNot(inherited, gene)
        self.assertIsNot(inherited.action_pattern, gene.action_pattern)
        self.assertAlmostEqual(inherited.strength, 0.68)
        self.assertEqual(inherited.age, 2)

    def test_sr_and_ps_non_social_inheritance_share_strength_contract(self) -> None:
        parent = Organism("parity-parent", (0.0, 0.0))
        gene = MemoryGene("parity", {"move": 0.4}, 0.6)
        gene.strength = 0.8
        parent.memory_genes.append(gene)

        ps_child = Organism("parity-ps-child", (1.0, 1.0))
        ps_inheritance = InheritanceSystem(randomness_rng=random.Random(7))
        ps_inheritance.set_memory_gene_inheritance_rate(1.0)
        ps_inheritance.set_mutation_rate(0.0)
        ps_inheritance._inherit_memory_genes(parent, ps_child)

        sr_child = inherit_sr_memory_genes(
            [gene], inheritance_rate=1.0, mutation_rate=0.0, rng=random.Random(7)
        )

        self.assertEqual(len(ps_child.memory_genes), len(sr_child))
        self.assertEqual(ps_child.memory_genes[0].situation, sr_child[0].situation)
        self.assertAlmostEqual(ps_child.memory_genes[0].strength, sr_child[0].strength)
        self.assertEqual(ps_child.memory_genes[0].action_pattern, sr_child[0].action_pattern)
        self.assertIsNot(ps_child.memory_genes[0], sr_child[0])

    def test_spawn_bridge_preserves_inherited_sr_gene_and_absent_sr_store_is_non_destructive(self) -> None:
        child_entity = EntityBase("sr-child", position=(2.0, 3.0))
        load_sr_memory_genes_from_props(
            child_entity,
            {"initial_memory_genes": [{"situation": "inherited", "action_pattern": {"ax": 4}}]},
        )
        pond = Pond(initial_organisms=0, initial_components=0)
        child = bridge_spawned_organism(
            child_entity,
            pond,
            {"scripts": [{"properties": {"developmental": {"enabled": True}}}]},
            equip_pvaec=False,
        )
        self.assertEqual(child.memory_genes[0].situation, "inherited")

        # A PS child may already have inherited state before SR has an
        # explicit gene store. A bridge sync must not erase that state.
        plain_entity = EntityBase("sr-plain", position=(0.0, 0.0))
        plain_child = Organism("ps-plain", (0.0, 0.0))
        plain_gene = MemoryGene("ps-inherited", {"ax": 6}, 0.7)
        plain_child.memory_genes.append(plain_gene)
        sync_sr_entity_to_organism(plain_entity, plain_child)
        self.assertEqual(plain_child.memory_genes[0].situation, "ps-inherited")

    def test_ledger_and_bridge_admit_only_value_copy_for_memory_genes(self) -> None:
        audit = build_worldbridge_mapping_audit()
        self.assertEqual(
            audit["fields"]["memory_genes"],
            {"state": "partial", "direction": "sr_to_ps_and_ps_to_sr_value_copy"},
        )
        self.assertNotIn("memory_genes", audit["known_losses"])

    def test_ps_to_sr_sync_round_trips_as_detached_values(self) -> None:
        entity = EntityBase("sr-memory-round-trip", position=(0.0, 0.0))
        load_sr_memory_genes_from_props(
            entity,
            {"initial_memory_genes": [{"situation": "initial", "action_pattern": {"x": 1}}]},
        )
        pond = Pond(initial_organisms=0, initial_components=0)
        organism = sr_entity_to_organism(entity, pond)
        organism.memory_genes[0].action_pattern["x"] = 2.0

        from core.Lotucosm.runtime.world_bridge import sync_organism_to_sr_display

        sync_organism_to_sr_display(organism, entity)

        self.assertEqual(entity.sr_memory_genes[0].action_pattern["x"], 2.0)
        self.assertIsNot(entity.sr_memory_genes[0], organism.memory_genes[0])

    def test_live_checkpoint_projects_memory_genes_as_copy_isolated_json_values(self) -> None:
        entity = EntityBase("sr-memory-checkpoint", position=(0.0, 0.0))
        load_sr_memory_genes_from_props(
            entity,
            {"initial_memory_genes": [{"situation": "checkpoint", "action_pattern": {"x": 1}}]},
        )
        pond = Pond(initial_organisms=0, initial_components=0)
        organism = sr_entity_to_organism(entity, pond)
        links = [{"sr_entity_id": entity.id, "ps_organism_id": organism.id}]

        sr = capture_worldbridge_sr_checkpoint({"sim_time": 0.0}, [entity], links)
        ps = capture_worldbridge_ps_checkpoint(pond, links)
        original = copy.deepcopy(sr["bridged_entities"][0]["memory_genes"])
        sr["bridged_entities"][0]["memory_genes"][0]["action_pattern"]["x"] = 9.0

        assert ps["bridged_organisms"][0]["memory_genes"][0]["action_pattern"]["x"] == 1.0
        assert original == ps["bridged_organisms"][0]["memory_genes"]

    def test_sr_snapshot_restore_round_trips_memory_genes_atomically(self) -> None:
        entity = EntityBase("sr-memory-restore", position=(0.0, 0.0))
        load_sr_memory_genes_from_props(
            entity,
            {"initial_memory_genes": [{"situation": "restore", "action_pattern": {"x": 3}}]},
        )
        snapshot = {
            "entity_id": entity.id,
            "memory_genes": [{
                "situation": "restored",
                "action_pattern": {"x": 8},
                "success_rate": 0.9,
                "strength": 0.7,
                "age": 4,
            }],
        }

        restore_sr_runtime_snapshot_slice(
            [entity], [snapshot], scene_time=1.0,
        )

        self.assertEqual(entity.sr_memory_genes[0].situation, "restored")
        self.assertEqual(entity.sr_memory_genes[0].action_pattern["x"], 8.0)
        self.assertEqual(entity.sr_memory_genes[0].age, 4)
        snapshot["memory_genes"][0]["action_pattern"]["x"] = 99
        self.assertEqual(entity.sr_memory_genes[0].action_pattern["x"], 8.0)


if __name__ == "__main__":
    unittest.main()

