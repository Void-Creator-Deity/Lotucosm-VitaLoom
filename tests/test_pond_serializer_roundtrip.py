"""
PondSerializer 往返：实体/组件不丢键。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from core.Lotucosm.entity import EntityBase

from builtin.systems.pond_serializer import PondSerializer
from builtin.systems.floating_system import FloatingSystem
from builtin.systems.physics_engine import PhysicsEngine
from builtin.systems.resource_manager import ResourceManager
from core.Lotucosm.pond import Pond
from builtin.entity_types.organism import Organism
from builtin.entity_types.simple_organism import SimpleOrganism


class PondSerializerRoundTripTests(unittest.TestCase):

    def test_base_organism_type_survives_round_trip(self):
        source = Organism("base_org", (1.0, 2.0), energy=40.0)

        restored = PondSerializer().deserialize_organism(
            PondSerializer().serialize_organism(source)
        )

        self.assertIsInstance(restored, Organism)
        self.assertNotIsInstance(restored, SimpleOrganism)


    def test_deserialize_and_in_place_restore_preserve_caller_owned_rng(self):
        owner = np.random.default_rng(321)
        source = Pond(
            name="rng_source",
            initial_organisms=0,
            initial_components=0,
            randomness_rng=owner,
        )
        source.add_organism(Organism("rng_org", (1.0, 2.0), energy=40.0))
        payload = PondSerializer().serialize_pond(source)

        loaded = PondSerializer().deserialize_pond(payload, Pond, randomness_rng=owner)
        self.assertIsNotNone(loaded)
        self.assertIs(loaded.randomness_rng, owner)
        self.assertIs(loaded.organisms["rng_org"].pond, loaded)
        self.assertIs(loaded.organisms["rng_org"].randomness_rng, owner)

        target = Pond(
            name="rng_target",
            initial_organisms=0,
            initial_components=0,
            randomness_rng=owner,
        )
        target.restore_serialized_state_in_place(payload)
        self.assertIs(target.randomness_rng, owner)
        self.assertIs(target.organisms["rng_org"].randomness_rng, owner)

    def test_floating_assembly_sequence_survives_restore(self):
        source = Pond(name="assembly_sequence", initial_organisms=0, initial_components=0)
        source.floating_system = FloatingSystem(world_size=source.size)
        source.floating_system._assembly_sequence = 7
        payload = PondSerializer().serialize_pond(source)
        self.assertEqual(payload["floating_assembly_sequence"], 7)

        target = Pond(name="target", initial_organisms=0, initial_components=0)
        target.floating_system = FloatingSystem(world_size=target.size)
        target.restore_serialized_state_in_place(payload)
        self.assertEqual(target.floating_system._assembly_sequence, 7)

    def test_in_place_restore_rebinds_physics_targets_to_restored_organisms(self):
        source = Pond(name="physics_source", initial_organisms=0, initial_components=0)
        source.add_organism(Organism("restored_org", (12.0, 18.0), energy=71.0))
        payload = PondSerializer().serialize_pond(source)

        target = Pond(name="physics_target", initial_organisms=0, initial_components=0)
        old = Organism("old_org", (1.0, 2.0), energy=10.0)
        target.add_organism(old)
        target.physics_engine = PhysicsEngine(world_size=target.size)
        target._refresh_physics_targets()
        self.assertIs(target.physics_engine._targets[0], old)

        target.restore_serialized_state_in_place(payload)

        restored = target.organisms["restored_org"]
        self.assertEqual(target.physics_engine._targets, [restored])
        self.assertIs(target.physics_engine._targets[0], restored)
        self.assertNotIn(old, target.physics_engine._targets)

    def test_restore_serialized_state_in_place_reconstructs_before_commit(self):
        source = Pond(name="in_place_source", size=(240, 180), initialize=False)
        organism = Organism("in_place_org", (12.0, 18.0), energy=71.0)
        source.add_organism(organism)
        source.time = 7
        source.iteration = 3
        payload = PondSerializer().serialize_pond(source)

        target = Pond(name="in_place_target", size=(100, 100), initialize=False)
        old = Organism("old_org", (1.0, 2.0), energy=10.0)
        target.add_organism(old)
        target.restore_serialized_state_in_place(payload)

        self.assertEqual(target.time, 7)
        self.assertEqual(target.iteration, 3)
        self.assertEqual(set(target.organisms), {"in_place_org"})
        self.assertIs(target.organisms["in_place_org"].pond, target)
        self.assertEqual([entity.id for entity in target.root_entities], ["in_place_org"])

        before_ids = set(target.organisms)
        malformed = dict(payload)
        malformed["organisms"] = [{"id": "broken"}]
        with self.assertRaises(ValueError):
            target.restore_serialized_state_in_place(malformed)
        self.assertEqual(set(target.organisms), before_ids)

    def test_restore_serialized_state_in_place_compensates_commit_failure(self):
        source = Pond(name="source", size=(240, 180), initialize=False)
        source.add_organism(Organism("new_org", (12.0, 18.0), energy=71.0))
        payload = PondSerializer().serialize_pond(source)

        target = Pond(name="target", size=(100, 100), initialize=False)
        old = Organism("old_org", (1.0, 2.0), energy=10.0)
        target.add_organism(old)
        previous_root_entities = target.root_entities
        class FailingFloatingSystem:
            def __init__(self):
                self.floating_components = ["old_entry"]
                self.world_size = (100.0, 100.0)

            def replace_floating_components(self, items):
                self.floating_components[:] = items
                raise RuntimeError("commit failure")

        target.floating_system = FailingFloatingSystem()
        previous_floating_components = target.floating_system.floating_components

        with self.assertRaisesRegex(RuntimeError, "commit failure"):
            target.restore_serialized_state_in_place(payload)

        self.assertIs(target.organisms["old_org"], old)
        self.assertIs(target.root_entities, previous_root_entities)
        self.assertIs(old.pond, target)
        self.assertIs(target.floating_system.floating_components, previous_floating_components)
        self.assertEqual(target.floating_system.floating_components, ["old_entry"])
        self.assertEqual(target.floating_system.world_size, (100.0, 100.0))
    def test_round_trip_preserves_basic_fields(self):
        pond = Pond(
            name="roundtrip_pond",
            size=(640, 360),
            initial_organisms=0,
            initial_components=7,
            component_variety="basic",
            evolution_generation_interval=11,
            max_population=42,
            environmental_factors={"light": 0.7},
            statistics={"steps": 3},
        )
        pond.time = 37
        pond.iteration = 12

        serializer = PondSerializer(save_format="json")
        payload = serializer.serialize_pond(pond)
        loaded = serializer.deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, pond.name)
        self.assertEqual(tuple(loaded.size), tuple(pond.size))
        self.assertEqual(loaded.time, 37)
        self.assertEqual(loaded.iteration, pond.iteration)
        self.assertEqual(loaded.max_population, pond.max_population)
        self.assertEqual(loaded.initial_components, pond.initial_components)
        self.assertEqual(loaded.component_variety, pond.component_variety)
        self.assertEqual(
            loaded.evolution_generation_interval,
            pond.evolution_generation_interval,
        )
        self.assertEqual(loaded.environmental_factors, pond.environmental_factors)

    def test_round_trip_preserves_motion_state_as_float_ndarrays(self):
        pond = Pond(name="motion_pond", size=(320, 200), initial_organisms=1)
        organism = next(iter(pond.organisms.values()))
        organism.set_position((11, 12))
        organism.set_velocity((1.5, -2.25))
        organism.set_acceleration((-0.5, 0.75))

        serializer = PondSerializer(save_format="json")
        loaded = serializer.deserialize_pond(serializer.serialize_pond(pond), Pond)
        restored = next(iter(loaded.organisms.values()))

        self.assertTrue(np.array_equal(restored.position, [11.0, 12.0]))
        self.assertTrue(np.array_equal(restored.velocity, [1.5, -2.25]))
        self.assertTrue(np.array_equal(restored.acceleration, [-0.5, 0.75]))
        self.assertEqual(restored.position.dtype, float)
        self.assertEqual(restored.velocity.dtype, float)
        self.assertEqual(restored.acceleration.dtype, float)

    def test_round_trip_rebuilds_root_entity_registration(self):
        pond = Pond(name="root_registration_pond", size=(320, 200), initial_organisms=1)

        loaded = PondSerializer().deserialize_pond(PondSerializer().serialize_pond(pond), Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(set(loaded.root_entities), set(loaded.organisms.values()))
        self.assertEqual(len(loaded.root_entities), len(loaded.organisms))
        self.assertTrue(all(organism.pond is loaded for organism in loaded.organisms.values()))

    def test_legacy_payload_without_time_defaults_to_zero(self):
        pond = Pond(name="legacy_time_pond", size=(160, 120), initial_organisms=0)
        payload = PondSerializer().serialize_pond(pond)
        payload.pop("time")

        loaded = PondSerializer().deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.time, 0)

    def test_legacy_payload_without_new_initialization_metadata_uses_defaults(self):
        pond = Pond(name="legacy_metadata_pond", size=(160, 120), initial_organisms=0)
        payload = PondSerializer().serialize_pond(pond)
        payload.pop("initial_components")
        payload.pop("component_variety")
        payload.pop("evolution_generation_interval")

        loaded = PondSerializer().deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.initial_components, 50)
        self.assertEqual(loaded.component_variety, "all")
        self.assertIsNone(loaded.evolution_generation_interval)

    def test_invalid_time_is_rejected_before_restore(self):
        pond = Pond(name="invalid_time_pond", size=(160, 120), initial_organisms=0)
        payload = PondSerializer().serialize_pond(pond)
        payload["time"] = -1

        with self.assertLogs("PondSerializer", level="WARNING"):
            loaded = PondSerializer().deserialize_pond(payload, Pond)

        self.assertIsNone(loaded)

    def test_restore_skips_default_initialization_and_preserves_metadata(self):
        pond = Pond(
            name="empty_restore_pond",
            size=(160, 120),
            initial_organisms=0,
            initial_components=0,
        )
        payload = PondSerializer().serialize_pond(pond)
        payload["initial_organisms"] = 3
        payload["basic_resources"] = []
        payload["simple_floating_components"] = []

        with patch.object(Pond, "initialize_pond", side_effect=AssertionError("restore initialized defaults")):
            loaded = PondSerializer().deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.initial_organisms, 3)
        self.assertEqual(loaded.resources, {"food": [], "energy": []})
        self.assertEqual(loaded.floating_components, [])
        self.assertEqual(loaded.organisms, {})

    def test_restore_does_not_consume_constructor_randomness(self):
        pond = Pond(
            name="random_state_restore_pond",
            size=(160, 120),
            initial_organisms=0,
            initial_components=0,
        )
        payload = PondSerializer().serialize_pond(pond)
        before = np.random.get_state()

        loaded = PondSerializer().deserialize_pond(payload, Pond)

        after = np.random.get_state()
        self.assertIsNotNone(loaded)
        self.assertEqual(before[0], after[0])
        self.assertTrue(np.array_equal(before[1], after[1]))
        self.assertEqual(before[2:], after[2:])

    def test_pond_load_merge_preserves_persisted_configuration(self):
        source = Pond(
            name="merge_source",
            size=(240, 180),
            initial_organisms=0,
            initial_components=9,
            component_variety="basic",
            evolution_generation_interval=13,
        )
        source.time = 8
        source.iteration = 2
        loaded = PondSerializer().deserialize_pond(
            PondSerializer().serialize_pond(source),
            Pond,
        )
        target = Pond(
            name="merge_target",
            size=(80, 60),
            initial_organisms=0,
            initial_components=1,
        )

        target._apply_loaded_pond_state(loaded)

        self.assertEqual(target.name, "merge_source")
        self.assertEqual(target.time, 8)
        self.assertEqual(target.iteration, 2)
        self.assertEqual(target.initial_organisms, 0)
        self.assertEqual(target.initial_components, 9)
        self.assertEqual(target.component_variety, "basic")
        self.assertEqual(target.evolution_generation_interval, 13)

    def test_subsystem_snapshot_projects_to_plain_pond_compatibility_state(self):
        source = Pond(name="subsystem_source", size=(240, 180), initial_organisms=0)
        source.floating_system = FloatingSystem(world_size=source.size)
        source.resource_manager = ResourceManager(world_size=source.size)

        component = source.floating_components[0]
        source.floating_components.clear()
        component.set_position((12.0, 14.0))
        component.set_velocity((1.5, -0.5))
        source.floating_system.replace_floating_components([{
            "component": component,
            "position": [12.0, 14.0],
            "velocity": [1.5, -0.5],
            "lifespan": 21,
            "decay_rate": 0.03,
        }])
        source.resource_manager.resources = {
            "food": [{"type": "food", "position": [3.0, 4.0], "amount": 2.5, "id": "food-1"}],
            "energy": [],
        }

        payload = PondSerializer().serialize_pond(source)
        loaded = PondSerializer().deserialize_pond(payload, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.floating_components), 1)
        self.assertTrue(np.array_equal(loaded.floating_components[0].position, [12.0, 14.0]))
        self.assertEqual(loaded.resources["food"][0]["id"], "food-1")
        self.assertEqual(loaded.resources["food"][0]["amount"], 2.5)

    def test_mixed_pond_and_subsystem_state_survives_two_round_trips(self):
        source = Pond(name="mixed_source", initial_organisms=0, initial_components=0)
        source.resources["food"] = [{"type": "food", "position": [1.0, 2.0], "amount": 1.0}]
        source.resource_manager = ResourceManager(world_size=source.size)
        source.resource_manager.resources["food"] = [
            {"type": "food", "position": [3.0, 4.0], "amount": 2.0, "id": "managed-food"}
        ]

        from builtin.components.component_factory import ComponentFactory

        factory = ComponentFactory()
        pond_component = factory.create_component("ComponentBase", "pond-float", organism_id="")
        managed_component = factory.create_component("ComponentBase", "managed-float", organism_id="")
        source.add_floating_component(pond_component)
        source.floating_system = FloatingSystem(world_size=source.size)
        source.floating_system.replace_floating_components([{
            "component": managed_component,
            "position": [5.0, 6.0],
            "velocity": [0.0, 0.0],
            "lifespan": 10,
            "decay_rate": 0.1,
        }])

        serializer = PondSerializer()
        first = serializer.deserialize_pond(serializer.serialize_pond(source), Pond)
        self.assertIsNotNone(first)
        self.assertEqual(len(first.resources["food"]), 2)
        self.assertEqual({comp.id for comp in first.floating_components}, {"pond-float", "managed-float"})

        second = serializer.deserialize_pond(serializer.serialize_pond(first), Pond)
        self.assertIsNotNone(second)
        self.assertEqual(len(second.resources["food"]), 2)
        self.assertEqual(
            [entry["id"] for entry in second.resources["food"] if "id" in entry],
            ["managed-food"],
        )
        self.assertEqual({comp.id for comp in second.floating_components}, {"pond-float", "managed-float"})

    def test_mixed_snapshot_replaces_existing_subsystems_without_double_projection(self):
        from builtin.components.component_factory import ComponentFactory

        source = Pond(name="source", initial_organisms=0, initial_components=0)
        source.resources = {
            "food": [{"type": "food", "position": [1, 2], "amount": 1}],
            "energy": [],
        }
        source.resource_manager = ResourceManager(world_size=source.size)
        source.resource_manager.resources["food"] = [
            {"type": "food", "position": [3, 4], "amount": 2, "id": "managed"}
        ]
        source.resource_manager.resources["mineral"] = [
            {"type": "mineral", "position": [7, 8], "amount": 3, "id": "ore"}
        ]
        factory = ComponentFactory()
        source.add_floating_component(factory.create_component("ComponentBase", "plain", organism_id=""))
        source.floating_system = FloatingSystem(world_size=source.size)
        source.floating_system.replace_floating_components([{
            "component": factory.create_component("ComponentBase", "system", organism_id=""),
            "position": [5, 6],
            "velocity": [0, 0],
            "lifespan": 17,
            "decay_rate": 0.2,
        }])

        target = Pond(name="target", initial_organisms=0, initial_components=0)
        target.resource_manager = ResourceManager(world_size=target.size)
        target.resource_manager.resources["food"] = [
            {"type": "food", "position": [9, 9], "amount": 9, "id": "stale"}
        ]
        target.floating_system = FloatingSystem(world_size=target.size)
        target.floating_system.replace_floating_components([{
            "component": factory.create_component("ComponentBase", "stale", organism_id=""),
            "position": [9, 9],
            "velocity": [0, 0],
            "lifespan": 1,
            "decay_rate": 0.1,
        }])

        serializer = PondSerializer()
        target._apply_loaded_pond_state(serializer.deserialize_pond(serializer.serialize_pond(source), Pond))

        self.assertEqual([item.get("id") for item in target.resources["food"]], [None])
        self.assertEqual([item["id"] for item in target.resource_manager.resources["food"]], ["managed"])
        self.assertEqual([item["id"] for item in target.resource_manager.resources["mineral"]], ["ore"])
        self.assertEqual([component.id for component in target.floating_components], ["plain"])
        managed = target.floating_system.floating_components
        self.assertEqual([entry["component"].id for entry in managed], ["system"])
        self.assertEqual(managed[0]["lifespan"], 17)
        self.assertEqual(managed[0]["decay_rate"], 0.2)
        saved = serializer.serialize_pond(target)
        self.assertEqual(len(saved["basic_resources"]), 1)
        self.assertEqual(len(saved["resources"]), 2)
        self.assertEqual(len(saved["simple_floating_components"]), 1)
        self.assertEqual(len(saved["floating_components"]), 1)

    def test_file_load_replaces_existing_subsystem_state(self):
        source = Pond(name="saved", initial_organisms=0, initial_components=0)
        source.resources = {"food": [], "energy": []}
        source.resource_manager = ResourceManager(world_size=source.size)
        source.resource_manager.resources["food"] = [
            {"type": "food", "position": [2, 3], "amount": 4, "id": "saved-food"}
        ]
        target = Pond(name="old", initial_organisms=0, initial_components=0)
        target.resource_manager = ResourceManager(world_size=target.size)
        target.resource_manager.resources["food"] = [
            {"type": "food", "position": [9, 9], "amount": 9, "id": "old-food"}
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "world.pond")
            self.assertTrue(source.save_pond(path))
            self.assertTrue(target.load_pond(path))

        self.assertEqual(target.name, "saved")
        self.assertEqual(target.resources["food"], [])
        self.assertEqual(target.resource_manager.resources["food"][0]["id"], "saved-food")

    def test_failed_save_preserves_existing_pond_file(self):
        pond = Pond(name="atomic", initial_organisms=0, initial_components=0)
        serializer = PondSerializer(save_format="json")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "world.pond")
            self.assertTrue(serializer.save_pond(pond, path))
            with open(path, "rb") as stream:
                before = stream.read()

            def fail_mid_write(_payload, stream, **_kwargs):
                stream.write("partial")
                raise OSError("simulated write failure")

            with patch("builtin.systems.pond_serializer.json.dump", side_effect=fail_mid_write):
                with self.assertLogs("PondSerializer", level="WARNING"):
                    self.assertFalse(serializer.save_pond(pond, path))

            with open(path, "rb") as stream:
                self.assertEqual(stream.read(), before)
            self.assertEqual(os.listdir(directory), ["world.pond"])

    def test_failed_replace_preserves_existing_pond_file(self):
        pond = Pond(name="replace", initial_organisms=0, initial_components=0)
        serializer = PondSerializer(save_format="json")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "world.pond")
            self.assertTrue(serializer.save_pond(pond, path))
            with open(path, "rb") as stream:
                before = stream.read()

            with patch("builtin.systems.pond_serializer.os.replace", side_effect=OSError("replace failed")):
                with self.assertLogs("PondSerializer", level="WARNING"):
                    self.assertFalse(serializer.save_pond(pond, path))

            with open(path, "rb") as stream:
                self.assertEqual(stream.read(), before)
            self.assertEqual(os.listdir(directory), ["world.pond"])

    def test_pickle_file_round_trip_after_atomic_save(self):
        source = Pond(name="pickle", initial_organisms=0, initial_components=0)
        serializer = PondSerializer(save_format="pickle")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "world.pond")
            self.assertTrue(serializer.save_pond(source, path))
            loaded = serializer.load_pond(path, Pond)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "pickle")

    def test_round_trip_preserves_size_radius_generation_and_dead_state(self):
        pond = Pond(name="lifecycle_pond", size=(320, 200), initial_organisms=1)
        organism = next(iter(pond.organisms.values()))
        organism.set_size(15.0)
        organism.set_radius(10.0)
        organism.set_generation(4)
        organism.set_dead(True)

        serializer = PondSerializer(save_format="json")
        loaded = serializer.deserialize_pond(serializer.serialize_pond(pond), Pond)
        restored = next(iter(loaded.organisms.values()))

        self.assertEqual(restored.size, 15.0)
        self.assertEqual(restored.radius, 10.0)
        self.assertEqual(restored.generation, 4)
        self.assertTrue(restored.dead)

    def test_restore_motion_state_validates_before_mutating(self):
        entity = EntityBase(position=(1, 2), velocity=(3, 4), acceleration=(5, 6))
        with self.assertRaises(ValueError):
            entity.restore_motion_state(
                position=(10, 11),
                velocity=(12, 13, 14),
                acceleration=(15, 16),
            )

        self.assertTrue(np.array_equal(entity.position, [1.0, 2.0]))
        self.assertTrue(np.array_equal(entity.velocity, [3.0, 4.0]))
        self.assertTrue(np.array_equal(entity.acceleration, [5.0, 6.0]))


if __name__ == "__main__":
    unittest.main()
