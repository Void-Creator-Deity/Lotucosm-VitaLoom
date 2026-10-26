# -*- coding: utf-8 -*-
"""Legacy B P2：pond_serializer 与 component_factory 行为内化回归。

职责: memory_genes 往返、旧版小写 type、模板工厂、文件 save/load。
时机: pytest 全量或单文件。
排错: 见 docs/legacy_gap_b_triage.md persistence / components 节。
"""
from __future__ import annotations

import os
import tempfile
import unittest

from builtin.components.PVAECEngine import PVAECEngine
from builtin.components.component_factory import ComponentFactory, normalize_component_type
from builtin.components.sensors import Sensor
from builtin.entity_types.organism import Organism
from builtin.systems.pond_serializer import PondSerializer
from builtin.systems.organism_serializer import OrganismSerializer
from core.Lotucosm.memory import MemoryGene, MemorySystem
from core.Lotucosm.pond import Pond


class ComponentFactoryLegacyTests(unittest.TestCase):
    def test_normalize_legacy_lowercase_types(self):
        self.assertEqual(normalize_component_type("sensor"), "Sensor")
        self.assertEqual(normalize_component_type("pvaecengine"), "PVAECEngine")

    def test_create_from_template_legacy_shape(self):
        f = ComponentFactory()
        c = f.create_component_from_template(
            {"type": "sensor", "name": "S1"},
            "c1",
            organism_id="o1",
        )
        self.assertIsInstance(c, Sensor)
        self.assertEqual(c.id, "c1")
        self.assertEqual(c.organism_id, "o1")

    def test_get_available_component_types_includes_sensor(self):
        names = ComponentFactory().get_available_component_types()
        self.assertIn("Sensor", names)


class OrganismSerializerMemoryAdoptionTests(unittest.TestCase):
    def test_memory_roundtrip_preserves_fields_through_domain_adoption(self) -> None:
        organism = Organism("org_memory", (1.0, 2.0))
        organism.memory_system = MemorySystem()
        memory = MemoryGene("ctx", {"tool": 0.3}, 0.6)
        memory.strength = 0.7
        memory.age = 4
        organism.memory_system.memories.append(memory)

        serializer = OrganismSerializer()
        restored = serializer.deserialize_organism(serializer.serialize_organism(organism))

        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.memory_system.memories), 1)
        got = restored.memory_system.memories[0]
        self.assertEqual(got.situation, "ctx")
        self.assertEqual(got.action_pattern, {"tool": 0.3})
        self.assertAlmostEqual(got.success_rate, 0.6)
        self.assertAlmostEqual(got.strength, 0.7)
        self.assertEqual(got.age, 4)

    def test_motion_and_lifecycle_state_roundtrip_through_owner_hydration(self) -> None:
        organism = Organism("org_state", (1.0, 2.0))
        organism.restore_motion_state(
            position=(9.0, 8.0),
            velocity=(1.5, -2.5),
            acceleration=(-0.25, 0.75),
        )
        organism.set_size(14.0)
        organism.set_radius(9.0)
        organism.set_generation(6)
        organism.set_dead(True)

        restored = OrganismSerializer().deserialize_organism(
            OrganismSerializer().serialize_organism(organism)
        )

        self.assertIsNotNone(restored)
        self.assertEqual(restored.position.tolist(), [9.0, 8.0])
        self.assertEqual(restored.velocity.tolist(), [1.5, -2.5])
        self.assertEqual(restored.acceleration.tolist(), [-0.25, 0.75])
        self.assertEqual(restored.size, 14.0)
        self.assertEqual(restored.radius, 9.0)
        self.assertEqual(restored.generation, 6)
        self.assertTrue(restored.dead)

    def test_legacy_payload_without_new_motion_and_lifecycle_keys_still_loads(self) -> None:
        organism = Organism("org_legacy", (3.0, 4.0))
        payload = OrganismSerializer().serialize_organism(organism)
        for key in ("velocity", "acceleration", "size", "radius", "generation", "dead"):
            payload.pop(key, None)

        restored = OrganismSerializer().deserialize_organism(payload)

        self.assertIsNotNone(restored)
        self.assertEqual(restored.position.tolist(), [3.0, 4.0])
        self.assertEqual(restored.velocity.tolist(), [0.0, 0.0])
        self.assertEqual(restored.acceleration.tolist(), [0.0, 0.0])
        self.assertEqual(restored.generation, 1)
        self.assertFalse(restored.dead)

    def test_hydration_does_not_apply_runtime_capacity_eviction(self) -> None:
        organism = Organism("org_many_memory", (0.0, 0.0))
        organism.memory_system = MemorySystem()
        payload = OrganismSerializer().serialize_organism(organism)
        payload["memories"] = [
            {
                "situation": f"ctx-{index}",
                "action_pattern": {"value": index},
                "success_rate": 0.5,
                "strength": 1.0,
                "age": index,
            }
            for index in range(1001)
        ]

        restored = OrganismSerializer().deserialize_organism(payload)

        self.assertIsNotNone(restored)
        self.assertEqual(len(restored.memory_system.memories), 1001)
        self.assertEqual(restored.memory_system.memories[0].situation, "ctx-0")
        self.assertEqual(restored.memory_system.memories[-1].situation, "ctx-1000")


class PondSerializerMemoryAdoptionTests(unittest.TestCase):
    def _pond_with_runtime_memory(self) -> Pond:
        pond = Pond(name="runtime_memory_pond", size=(240, 160), initial_organisms=0)
        organism = Organism("runtime_memory_org", (3.0, 4.0))
        organism.memory_system = MemorySystem()
        for index, (situation, strength, age) in enumerate(
            (("first", 0.25, 2), ("second", 0.85, 7))
        ):
            memory = MemoryGene(situation, {f"action-{index}": 0.1 + index}, 0.4 + index * 0.1)
            memory.strength = strength
            memory.age = age
            organism.memory_system.adopt_memory(memory)
        pond.organisms[organism.id] = organism
        return pond

    def test_runtime_memory_roundtrip_preserves_fields_and_order(self) -> None:
        serializer = PondSerializer(save_format="json")
        pond = self._pond_with_runtime_memory()

        payload = serializer.serialize_pond(pond)
        memory_payloads = payload["organisms"][0]["memories"]
        self.assertEqual(
            list(memory_payloads[0]),
            ["situation", "action_pattern", "success_rate", "strength", "age"],
        )

        restored_pond = serializer.deserialize_pond(payload, Pond)

        self.assertIsNotNone(restored_pond)
        restored = restored_pond.organisms["runtime_memory_org"]
        self.assertEqual(
            [memory.situation for memory in restored.memory_system.memories],
            ["first", "second"],
        )
        first, second = restored.memory_system.memories
        self.assertEqual(first.action_pattern, {"action-0": 0.1})
        self.assertAlmostEqual(first.success_rate, 0.4)
        self.assertAlmostEqual(first.strength, 0.25)
        self.assertEqual(first.age, 2)
        self.assertEqual(second.action_pattern, {"action-1": 1.1})
        self.assertAlmostEqual(second.success_rate, 0.5)
        self.assertAlmostEqual(second.strength, 0.85)
        self.assertEqual(second.age, 7)

    def test_empty_or_missing_memories_keep_pond_payload_compatible(self) -> None:
        serializer = PondSerializer()
        pond = Pond(name="empty_memory_pond", size=(100, 100), initial_organisms=0)
        organism = Organism("empty_memory_org", (0.0, 0.0))
        pond.organisms[organism.id] = organism
        payload = serializer.serialize_pond(pond)
        organism_payload = payload["organisms"][0]
        self.assertNotIn("memories", organism_payload)

        missing = serializer.deserialize_pond(payload, Pond)
        self.assertIsNotNone(missing)
        self.assertIsNone(missing.organisms["empty_memory_org"].memory_system)

        organism_payload["memories"] = []
        empty = serializer.deserialize_pond(payload, Pond)
        self.assertIsNotNone(empty)
        self.assertIsNone(empty.organisms["empty_memory_org"].memory_system)

    def test_non_dict_memory_entries_are_skipped(self) -> None:
        serializer = PondSerializer()
        pond = self._pond_with_runtime_memory()
        payload = serializer.serialize_pond(pond)
        payload["organisms"][0]["memories"].insert(1, "legacy-invalid-entry")

        restored_pond = serializer.deserialize_pond(payload, Pond)

        self.assertIsNotNone(restored_pond)
        restored = restored_pond.organisms["runtime_memory_org"]
        self.assertEqual(
            [memory.situation for memory in restored.memory_system.memories],
            ["first", "second"],
        )

    def test_malformed_memory_entry_keeps_existing_error_degradation(self) -> None:
        serializer = PondSerializer()
        pond = self._pond_with_runtime_memory()
        payload = serializer.serialize_pond(pond)
        del payload["organisms"][0]["memories"][0]["success_rate"]

        with self.assertLogs("PondSerializer", level="WARNING") as logs:
            restored_pond = serializer.deserialize_pond(payload, Pond)

        self.assertIsNotNone(restored_pond)
        self.assertNotIn("runtime_memory_org", restored_pond.organisms)
        self.assertTrue(any("反序列化生物体失败" in entry for entry in logs.output))


class PondSerializerP2Tests(unittest.TestCase):
    def test_memory_genes_roundtrip(self):
        pond = Pond(name="mg_pond", size=(200, 200), initial_organisms=0)
        org = Organism("o1", (1.0, 2.0))
        mg = MemoryGene("ctx_a", {"tool": 0.3}, 0.6)
        mg.strength = 0.7
        mg.age = 2
        org.memory_genes.append(mg)
        pond.organisms[org.id] = org

        ser = PondSerializer(save_format="json")
        loaded = ser.deserialize_pond(ser.serialize_pond(pond), Pond)
        self.assertIsNotNone(loaded)
        restored = loaded.organisms["o1"]
        self.assertEqual(len(restored.memory_genes), 1)
        rmg = restored.memory_genes[0]
        self.assertEqual(rmg.situation, "ctx_a")
        self.assertAlmostEqual(rmg.success_rate, 0.6)
        self.assertAlmostEqual(rmg.strength, 0.7)
        self.assertEqual(rmg.age, 2)
        self.assertEqual(rmg.action_pattern, {"tool": 0.3})

    def test_deserialize_component_accepts_legacy_lowercase_type(self):
        ser = PondSerializer()
        payload = {
            "type": "sensor",
            "id": "s_low",
            "name": "low",
            "location": "internal",
            "congenital": True,
            "acquired": False,
            "attach_point": None,
            "energy_consumption": 0.1,
            "is_sensor": True,
            "sensor_sensitivity": 0.9,
            "sense_range": 12.0,
        }
        comp = ser.deserialize_component(payload)
        self.assertIsNotNone(comp)
        self.assertIsInstance(comp, Sensor)
        self.assertAlmostEqual(comp.sensor_sensitivity, 0.9)

    def test_organism_with_pvaec_engine_file_roundtrip(self):
        pond = Pond(name="pvaec_pond", size=(300, 300), initial_organisms=0)
        org = Organism("o_pvaec", (5.0, 6.0))
        engine = PVAECEngine(component_id="e1", organism_id=org.id)
        engine.associations = {"a": {"b": 0.5}}
        org.components[engine.id] = engine
        pond.organisms[org.id] = org

        ser = PondSerializer(save_format="json")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pond.json")
            self.assertTrue(ser.save_pond(pond, path))
            loaded = ser.load_pond(path, Pond)
        self.assertIsNotNone(loaded)
        got = loaded.organisms["o_pvaec"].components["e1"]
        self.assertIsInstance(got, PVAECEngine)
        self.assertEqual(got.associations.get("a", {}).get("b"), 0.5)


if __name__ == "__main__":
    unittest.main()
