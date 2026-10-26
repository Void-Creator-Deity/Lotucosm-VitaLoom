# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from builtin.entity_types.organism import Organism
from builtin.systems.inheritance import InheritanceSystem
from builtin.systems.organism_serializer import OrganismSerializer
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge import (
    bridge_spawned_organism,
    sync_organism_to_sr_display,
    sync_sr_entity_to_organism,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_spawn_profile_decision import (
    build_worldbridge_spawn_profile_decision,
)


ROOT = Path(__file__).resolve().parents[1]
FIELD_MAPPER = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge_field_mapper.py"
)


class WorldBridgeSpawnProfileAuthorityDecisionTests(unittest.TestCase):
    def test_spawn_request_seeds_profile_but_regular_syncs_preserve_ps_runtime_state(self) -> None:
        entity = EntityBase("sr-spawn-profile-owner", position=(4.0, 5.0))
        entity.energy = 120.0
        request = {
            "scripts": [
                {
                    "properties": {
                        "developmental": {
                            "enabled": True,
                            "initial_stage": 2,
                            "plasticity_window": 9,
                            "plasticity_penalty": True,
                        },
                        "social": {"enabled": True},
                    }
                }
            ]
        }
        organism = bridge_spawned_organism(
            entity,
            Pond(initial_organisms=0, initial_components=0),
            request,
            equip_pvaec=False,
        )

        self.assertTrue(organism.developmental_ladder_enabled)
        self.assertEqual(organism.developmental_stage, 2)
        self.assertEqual(organism.developmental_plasticity_window, 9)
        self.assertTrue(organism.developmental_plasticity_penalty)
        self.assertTrue(organism.social_learning_enabled)

        organism.developmental_ladder_enabled = False
        organism.developmental_stage = 3
        organism.developmental_plasticity_window = 1
        organism.social_learning_enabled = False
        sync_sr_entity_to_organism(entity, organism)
        sync_organism_to_sr_display(organism, entity)

        self.assertFalse(organism.developmental_ladder_enabled)
        self.assertEqual(organism.developmental_stage, 3)
        self.assertEqual(organism.developmental_plasticity_window, 1)
        self.assertFalse(organism.social_learning_enabled)
        self.assertEqual(entity.sr_debug_hud["developmental_stage"], 3)

    def test_ps_inheritance_and_serializer_have_independent_profile_lifecycles(self) -> None:
        parent = Organism("ps-profile-parent", (1.0, 2.0))
        parent.developmental_ladder_enabled = True
        parent.developmental_stage = 3
        parent.social_learning_enabled = True
        inheritance = InheritanceSystem()
        inheritance.set_mutation_rate(0.0)

        child = inheritance.inherit(parent, (2.0, 3.0))
        self.assertTrue(child.developmental_ladder_enabled)
        self.assertEqual(child.developmental_stage, 0)
        self.assertFalse(child.social_learning_enabled)

        serializer = OrganismSerializer()
        data = serializer.serialize_organism(parent)
        self.assertNotIn("developmental_ladder_enabled", data)
        self.assertNotIn("developmental_stage", data)
        self.assertNotIn("social_learning_enabled", data)
        restored = serializer.deserialize_organism(data)
        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertFalse(restored.developmental_ladder_enabled)
        self.assertEqual(restored.developmental_stage, 0)
        self.assertFalse(restored.social_learning_enabled)

    def test_ledger_and_decision_keep_both_fields_partial_and_spawn_only(self) -> None:
        audit = build_worldbridge_mapping_audit()
        expected_ledger = {"state": "partial", "direction": "spawn_request_to_ps"}
        self.assertEqual(audit["fields"]["developmental_profile"], expected_ledger)
        self.assertEqual(audit["fields"]["social_enabled"], expected_ledger)

        decision = build_worldbridge_spawn_profile_decision()
        self.assertEqual(decision["decision"], "spawn_request_seed_only")
        for field in ("developmental_profile", "social_enabled"):
            self.assertEqual(decision["fields"][field]["mapping_state"], "partial")
            self.assertFalse(decision["fields"][field]["continuous_sync"])
        self.assertEqual(audit["spawn_profile_authority_decision"], decision)

    def test_regular_sync_functions_have_no_profile_or_social_reflection_route(self) -> None:
        tree = ast.parse(FIELD_MAPPER.read_text(encoding="utf-8"))
        mapper = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "WorldBridgeFieldMapper"
        )
        sync_functions = {
            node.name: node
            for node in mapper.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"sync_sr_to_ps", "sync_ps_to_sr"}
        }
        self.assertEqual(set(sync_functions), {"sync_sr_to_ps", "sync_ps_to_sr"})
        forbidden = {
            "developmental_profile",
            "developmental_ladder_enabled",
            "developmental_plasticity_window",
            "developmental_plasticity_penalty",
            "social_enabled",
            "social_learning_enabled",
            "apply_developmental_profile_to_organism",
            "apply_bridge_profile_to_organism",
        }
        for function in sync_functions.values():
            names: set[str] = set()
            for node in ast.walk(function):
                if isinstance(node, ast.Attribute):
                    names.add(node.attr)
                elif isinstance(node, ast.Name):
                    names.add(node.id)
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"getattr", "hasattr", "setattr"}
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str)
                ):
                    names.add(node.args[1].value)
            self.assertTrue(forbidden.isdisjoint(names))


if __name__ == "__main__":
    unittest.main()
