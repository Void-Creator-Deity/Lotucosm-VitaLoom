# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import unittest

from builtin.entity_types.organism import Organism
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge import (
    sr_entity_to_organism,
    sync_organism_to_sr_display,
    sync_sr_entity_to_organism,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)


class WorldBridgeKinematicMappingContractTests(unittest.TestCase):
    def _entity(self, entity_id: str = "sr-1") -> EntityBase:
        entity = EntityBase(
            entity_id,
            position=(10.0, 20.0),
            velocity=(1.25, -2.5),
            acceleration=(-3.75, 4.5),
        )
        entity.energy = 80.0
        entity.health = 70.0
        entity.sr_debug_hud = {}
        return entity

    def _pond(self) -> Pond:
        return Pond(
            name="kinematic-contract",
            size=(100.0, 100.0),
            initial_organisms=0,
            initial_components=0,
        )

    def test_creation_copies_finite_kinematics_without_aliasing(self) -> None:
        entity = self._entity()
        organism = sr_entity_to_organism(entity, self._pond())

        self.assertEqual(organism.velocity.tolist(), [1.25, -2.5])
        self.assertEqual(organism.acceleration.tolist(), [-3.75, 4.5])

        entity.velocity[0] = 99.0
        entity.acceleration[1] = 88.0
        self.assertEqual(organism.velocity.tolist(), [1.25, -2.5])
        self.assertEqual(organism.acceleration.tolist(), [-3.75, 4.5])

    def test_sync_is_bidirectional_for_velocity_and_acceleration(self) -> None:
        entity = self._entity()
        organism = Organism("ps-1", (0.0, 0.0))

        sync_sr_entity_to_organism(entity, organism)
        self.assertEqual(organism.velocity.tolist(), [1.25, -2.5])
        self.assertEqual(organism.acceleration.tolist(), [-3.75, 4.5])

        organism.velocity[0] = -8.0
        organism.velocity[1] = 6.5
        organism.acceleration[0] = 0.25
        organism.acceleration[1] = -0.5
        sync_organism_to_sr_display(organism, entity)

        self.assertEqual(entity.velocity.tolist(), [-8.0, 6.5])
        self.assertEqual(entity.acceleration.tolist(), [0.25, -0.5])

    def test_missing_or_malformed_kinematics_leave_targets_unchanged(self) -> None:
        entity = self._entity()
        organism = Organism("ps-2", (0.0, 0.0))
        organism.velocity[:] = (7.0, 8.0)
        organism.acceleration[:] = (9.0, 10.0)

        entity.velocity = [math.nan, 2.0]
        entity.acceleration = ["bad", 4.0]
        sync_sr_entity_to_organism(entity, organism)
        self.assertEqual(organism.velocity.tolist(), [7.0, 8.0])
        self.assertEqual(organism.acceleration.tolist(), [9.0, 10.0])

        entity.velocity = [11.0, 12.0]
        entity.acceleration = [13.0, 14.0]
        organism.velocity[:] = (math.inf, 1.0)
        organism.acceleration[:] = (2.0, math.nan)
        sync_organism_to_sr_display(organism, entity)
        self.assertEqual(entity.velocity, [11.0, 12.0])
        self.assertEqual(entity.acceleration, [13.0, 14.0])

    def test_ledger_marks_kinematics_covered_without_escalating_pilot_claims(self) -> None:
        audit = build_worldbridge_mapping_audit()

        self.assertEqual(audit["fields"]["velocity_acceleration"]["state"], "covered")
        self.assertEqual(
            audit["fields"]["velocity_acceleration"]["direction"],
            "sr_to_ps_and_ps_to_sr",
        )
        self.assertNotIn("velocity_acceleration", audit["known_losses"])
        self.assertFalse(audit["lossless"])
        self.assertFalse(audit["default_ready"])
        self.assertIn("sr_ps_tick_merge", audit["do_not_claim"])


if __name__ == "__main__":
    unittest.main()
