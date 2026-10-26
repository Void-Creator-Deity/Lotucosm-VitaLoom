"""Organism component graph authority regressions."""
import unittest
from builtin.components.components_base import ComponentBase
from builtin.entity_types.intelligent_organism import IntelligentOrganism

class OrganismComponentAuthorityTests(unittest.TestCase):
    def test_replace_components_preserves_dict_seam_and_parent_links(self):
        organism = IntelligentOrganism("components-test", (0.0, 0.0))
        original = organism.components
        first = ComponentBase("first", component_type="sensor")
        second = ComponentBase("second", component_type="actuator")
        organism.replace_components([first, second])
        self.assertIs(organism.components, original)
        self.assertEqual(list(organism.components), ["first", "second"])
        self.assertIs(first.parent, organism)
        self.assertIs(second.parent, organism)

        organism.replace_components([second])
        self.assertEqual(list(organism.components), ["second"])
        self.assertIsNone(first.parent)

    def test_replace_components_rejects_invalid_or_duplicate_before_mutation(self):
        organism = IntelligentOrganism("components-invalid", (0.0, 0.0))
        first = ComponentBase("first", component_type="sensor")
        organism.add_component(first)
        with self.assertRaises(TypeError):
            organism.replace_components([ComponentBase("new", component_type="sensor"), object()])
        self.assertEqual(list(organism.components), ["first"])
        with self.assertRaises(ValueError):
            organism.replace_components([ComponentBase("x", component_type="sensor"), ComponentBase("x", component_type="actuator")])
        self.assertEqual(list(organism.components), ["first"])

    def test_set_membrane_validates_and_binds_owner(self):
        organism = IntelligentOrganism("membrane-test", (0.0, 0.0))
        membrane = ComponentBase("mem", component_type="membrane")
        organism.set_membrane(membrane)
        self.assertIs(organism.membrane, membrane)
        self.assertEqual(membrane.organism_id, organism.id)
        with self.assertRaises(TypeError):
            organism.set_membrane(object())
        self.assertIs(organism.membrane, membrane)

    def test_replace_components_compensates_attach_failure_without_touching_extra_children(self):
        organism = IntelligentOrganism("components-rollback", (0.0, 0.0))
        first = ComponentBase("first", component_type="sensor")
        second = ComponentBase("second", component_type="actuator")
        organism.replace_components([first, second])
        membrane = ComponentBase("mem", component_type="membrane")
        organism.set_membrane(membrane)
        extra = ComponentBase("extra-child", component_type="sensor")
        organism.add_child(extra)
        organism_id = organism.id
        rng = organism.randomness_rng
        first_owner = first.organism_id
        second_owner = second.organism_id
        replacement = ComponentBase("replacement", component_type="sensor")
        failing = ComponentBase("failing", component_type="actuator")

        def fail_attach(owner):
            raise RuntimeError("attach failed")

        failing.on_attach = fail_attach
        with self.assertRaises(RuntimeError):
            organism.replace_components([replacement, failing])

        self.assertEqual(list(organism.components), ["first", "second"])
        self.assertIs(organism.components["first"], first)
        self.assertIs(organism.components["second"], second)
        self.assertIs(first.parent, organism)
        self.assertIs(second.parent, organism)
        self.assertIs(organism.membrane, membrane)
        self.assertEqual(membrane.organism_id, organism_id)
        self.assertIs(organism.randomness_rng, rng)
        self.assertEqual(first.organism_id, first_owner)
        self.assertEqual(second.organism_id, second_owner)
        self.assertIs(extra.parent, organism)
        self.assertIn(extra, organism.children)
        self.assertNotIn(replacement, organism.children)
        self.assertNotIn(failing, organism.children)

    def test_replace_component_graph_restores_membrane_on_set_membrane_failure(self):
        organism = IntelligentOrganism("graph-rollback", (0.0, 0.0))
        first = ComponentBase("first", component_type="sensor")
        second = ComponentBase("second", component_type="actuator")
        organism.replace_components([first, second])
        previous_membrane = ComponentBase("mem-old", component_type="membrane")
        organism.set_membrane(previous_membrane)
        organism_id = organism.id
        rng = organism.randomness_rng
        membrane_owner = previous_membrane.organism_id
        replacement = ComponentBase("replacement", component_type="sensor")

        original_set_membrane = organism.set_membrane

        def fail_set_membrane(membrane):
            raise RuntimeError("set_membrane failed")

        organism.set_membrane = fail_set_membrane
        try:
            with self.assertRaises(RuntimeError):
                organism.replace_component_graph([replacement], previous_membrane)
        finally:
            organism.set_membrane = original_set_membrane

        self.assertEqual(list(organism.components), ["first", "second"])
        self.assertIs(organism.components["first"], first)
        self.assertIs(organism.components["second"], second)
        self.assertIs(organism.membrane, previous_membrane)
        self.assertEqual(previous_membrane.organism_id, membrane_owner)
        self.assertIs(organism.randomness_rng, rng)

if __name__ == "__main__":
    unittest.main()
