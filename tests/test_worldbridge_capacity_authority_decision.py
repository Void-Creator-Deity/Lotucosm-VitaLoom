# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from builtin.entity_types.organism import Organism
from builtin.systems.organism_serializer import OrganismSerializer
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge import (
    sr_entity_to_organism,
    sync_organism_to_sr_display,
    sync_sr_entity_to_organism,
)
from core.Lotucosm.runtime.world_bridge_capacity_decision import (
    build_worldbridge_capacity_decision,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)


ROOT = Path(__file__).resolve().parents[1]
FIELD_MAPPER = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge_field_mapper.py"
)


class WorldBridgeCapacityAuthorityDecisionTests(unittest.TestCase):
    def test_creation_seeds_capacity_but_later_syncs_preserve_both_lane_values(self) -> None:
        entity = EntityBase("sr-capacity-owner", position=(4.0, 5.0))
        entity.energy = 250.0
        entity.max_energy = 300.0
        entity.health = 80.0
        entity.max_health = 90.0
        organism = sr_entity_to_organism(
            entity, Pond(initial_organisms=0, initial_components=0)
        )

        self.assertEqual((organism.max_energy, organism.max_health), (300.0, 90.0))

        entity.max_energy = 450.0
        entity.max_health = 120.0
        organism.max_energy = 280.0
        organism.max_health = 75.0
        sync_sr_entity_to_organism(entity, organism)
        self.assertEqual((organism.max_energy, organism.max_health), (280.0, 75.0))

        sync_organism_to_sr_display(organism, entity)
        self.assertEqual((entity.max_energy, entity.max_health), (450.0, 120.0))

    def test_ps_capacity_clamp_and_serializer_round_trip_remain_ps_owned(self) -> None:
        organism = Organism(
            "ps-capacity-owner",
            (1.0, 2.0),
            energy=150.0,
            max_energy=180.0,
            health=999.0,
            max_health=75.0,
        )
        self.assertEqual(organism.health, 75.0)
        organism.gain_energy(100.0)
        self.assertEqual(organism.energy, 180.0)

        serializer = OrganismSerializer()
        restored = serializer.deserialize_organism(serializer.serialize_organism(organism))
        self.assertIsNotNone(restored)
        assert restored is not None
        self.assertEqual((restored.max_energy, restored.max_health), (180.0, 75.0))
        self.assertEqual((restored.energy, restored.health), (180.0, 75.0))

    def test_ledger_and_decision_expose_creation_only_non_synchronization_contract(self) -> None:
        audit = build_worldbridge_mapping_audit()
        self.assertEqual(
            audit["fields"]["max_energy"],
            {"state": "creation_only", "direction": "sr_to_ps"},
        )
        self.assertEqual(
            audit["fields"]["max_health"],
            {"state": "creation_only", "direction": "sr_to_ps"},
        )

        decision = build_worldbridge_capacity_decision()
        self.assertEqual(decision["decision"], "creation_seed_only")
        for field in ("max_energy", "max_health"):
            self.assertEqual(decision["fields"][field]["mapping_state"], "creation_only")
            self.assertFalse(decision["fields"][field]["continuous_sync"])
        self.assertIn("continuous_capacity_synchronization", decision["do_not_claim"])
        self.assertEqual(audit["capacity_authority_decision"], decision)

    def test_sync_functions_have_no_capacity_reflection_or_assignment_route(self) -> None:
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
        self.assertEqual(
            set(sync_functions),
            {"sync_sr_to_ps", "sync_ps_to_sr"},
        )

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
            self.assertTrue({"max_energy", "max_health"}.isdisjoint(names))


if __name__ == "__main__":
    unittest.main()
