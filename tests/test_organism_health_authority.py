"""PS Organism health/dead mutation authority regressions."""
import math
import unittest
from builtin.entity_types.intelligent_organism import IntelligentOrganism

class OrganismHealthAuthorityTests(unittest.TestCase):
    def test_health_is_clamped_and_invalid_input_does_not_mutate(self):
        organism = IntelligentOrganism("health-test", (0.0, 0.0), health=40.0, max_health=100.0)
        organism.set_health(120.0)
        self.assertEqual(organism.health, 100.0)
        organism.set_health(-5.0)
        self.assertEqual(organism.health, 0.0)
        with self.assertRaises(ValueError):
            organism.set_health(math.nan)
        self.assertEqual(organism.health, 0.0)

    def test_dead_requires_bool_and_lifecycle_uses_owner(self):
        organism = IntelligentOrganism("dead-test", (0.0, 0.0))
        with self.assertRaises(TypeError):
            organism.set_dead(1)
        organism.set_dead(True)
        self.assertTrue(organism.dead)

if __name__ == "__main__":
    unittest.main()
