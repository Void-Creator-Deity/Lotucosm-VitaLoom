"""Organism capacity initialization authority regressions."""
import math
import unittest
from builtin.entity_types.intelligent_organism import IntelligentOrganism

class OrganismCapacityAuthorityTests(unittest.TestCase):
    def test_constructor_normalizes_capacities_and_values(self):
        organism = IntelligentOrganism("capacity-test", (0.0, 0.0), energy="12.5", max_energy="30", health=90, max_health=60)
        self.assertEqual(organism.energy, 12.5)
        self.assertEqual(organism.max_energy, 30.0)
        self.assertEqual(organism.health, 60.0)
        self.assertEqual(organism.max_health, 60.0)

    def test_invalid_capacity_is_rejected_without_partial_capacity_change(self):
        organism = IntelligentOrganism("capacity-invalid", (0.0, 0.0), max_energy=30.0, max_health=60.0)
        with self.assertRaises(ValueError):
            organism.set_max_energy(math.inf)
        with self.assertRaises(ValueError):
            organism.set_max_health(0.0)
        self.assertEqual((organism.max_energy, organism.max_health), (30.0, 60.0))

if __name__ == "__main__":
    unittest.main()
