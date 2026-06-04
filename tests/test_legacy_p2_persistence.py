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
from core.Lotucosm.memory import MemoryGene
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
