"""PS Organism energy mutation authority regressions."""

import math
import unittest

from builtin.entity_types.intelligent_organism import IntelligentOrganism


class OrganismEnergyAuthorityTests(unittest.TestCase):
    def test_set_energy_normalizes_numeric_values_and_rejects_invalid_before_mutation(self):
        organism = IntelligentOrganism("energy-test", (0.0, 0.0), energy=20.0)
        organism.set_energy("12.5")
        self.assertEqual(organism.energy, 12.5)

        with self.assertRaises(ValueError):
            organism.set_energy(math.nan)
        self.assertEqual(organism.energy, 12.5)

        with self.assertRaises(ValueError):
            organism.set_energy("not-a-number")
        self.assertEqual(organism.energy, 12.5)

    def test_consume_and_gain_keep_existing_energy_semantics_through_owner(self):
        organism = IntelligentOrganism(
            "energy-lifecycle",
            (0.0, 0.0),
            energy=20.0,
            max_energy=25.0,
        )
        self.assertTrue(organism.consume_energy(7.5))
        self.assertEqual(organism.energy, 12.5)
        self.assertFalse(organism.consume_energy(20.0))
        self.assertEqual(organism.energy, 12.5)

        organism.gain_energy(100.0)
        self.assertEqual(organism.energy, 25.0)

    def test_death_zeroes_energy_through_owner(self):
        organism = IntelligentOrganism(
            "energy-death",
            (0.0, 0.0),
            energy=0.01,
            energy_consumption_rate=1.0,
        )
        organism.update(1.0)
        self.assertTrue(organism.dead)
        self.assertEqual(organism.energy, 0.0)


if __name__ == "__main__":
    unittest.main()
