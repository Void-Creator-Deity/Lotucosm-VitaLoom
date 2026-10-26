"""Organism lifecycle state authority regressions."""
import unittest
from builtin.entity_types.intelligent_organism import IntelligentOrganism

class OrganismLifecycleAuthorityTests(unittest.TestCase):
    def test_age_api_and_increment(self):
        organism = IntelligentOrganism("age-test", (0.0, 0.0), age=4)
        organism.advance_age(2)
        self.assertEqual(organism.age, 6)
        with self.assertRaises(ValueError):
            organism.set_age(-1)
        self.assertEqual(organism.age, 6)

    def test_generation_and_offspring_owner_apis(self):
        organism = IntelligentOrganism("generation-test", (0.0, 0.0), generation=3)
        organism.set_generation(4)
        organism.increment_offspring_count()
        self.assertEqual(organism.generation, 4)
        self.assertEqual(organism.offspring_count, 1)
        with self.assertRaises(TypeError):
            organism.set_generation(True)

if __name__ == "__main__":
    unittest.main()
