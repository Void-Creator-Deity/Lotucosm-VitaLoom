# -*- coding: utf-8
"""plasticity_window 与社会偏置、WorldBridge 桩测试。"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.runtime.world_bridge import (
    BRIDGE_ORGANISM_ATTR,
    RUNTIME_MODE_DUAL,
    RUNTIME_MODE_UNIFIED,
    WorldBridgeNotReadyError,
    bridge_spawned_organism,
    capture_bridge_identity_links,
    developmental_profile_from_spawn_request,
    ensure_bridged_organisms,
    resolve_runtime_mode,
    restore_bridge_identity_links,
    sr_entity_to_organism,
    sync_organism_to_sr_display,
    sync_sr_entity_to_organism,
    unified_pond_enabled,
    unified_pond_step,
)
from core.Lotucosm.runtime.ecology_observation import snapshot_from_sr
from core.Lotucosm.social_memory import apply_ps_social_action_bias, observe_peer_action
from core.Lotucosm.pond import Pond
from builtin.entity_types.organism import Organism
from core.Lotucosm.sr_developmental_ladder import (
    can_advance_stage,
    plasticity_window_active,
    stage_min_ticks,
)


class PlasticityWindowTests(unittest.TestCase):

    def test_bridge_identity_links_round_trip_and_registration_validation(self) -> None:
        pond = Pond(name="identity_restore", size=(100, 100), initialize=False)
        organism = Organism("bridge_e1", (1.0, 2.0), energy=50.0)
        self.assertTrue(pond.add_organism(organism))
        entity = type("Entity", (), {"id": "e1"})()

        restore_bridge_identity_links(
            [entity], pond, [{"sr_entity_id": "e1", "ps_organism_id": "bridge_e1"}]
        )
        self.assertEqual(capture_bridge_identity_links([entity]), [
            {"sr_entity_id": "e1", "ps_organism_id": "bridge_e1"}
        ])

        before = getattr(entity, BRIDGE_ORGANISM_ATTR)
        with self.assertRaisesRegex(ValueError, "unknown PS"):
            restore_bridge_identity_links(
                [entity], pond, [{"sr_entity_id": "e1", "ps_organism_id": "missing"}]
            )
        self.assertEqual(getattr(entity, BRIDGE_ORGANISM_ATTR), before)

    def test_bridge_identity_restore_rolls_back_partial_binding(self) -> None:
        pond = Pond(name="identity_restore", size=(100, 100), initialize=False)
        pond.add_organism(Organism("bridge_a", (1.0, 2.0), energy=50.0))
        pond.add_organism(Organism("bridge_b", (3.0, 4.0), energy=50.0))
        first = type("Entity", (), {"id": "a"})()
        second = type("Entity", (), {"id": "b"})()

        with patch(
            "core.Lotucosm.runtime.world_bridge.capture_bridge_identity_links",
            return_value=[],
        ), self.assertRaisesRegex(ValueError, "identity links changed"):
            restore_bridge_identity_links(
                [first, second], pond,
                [
                    {"sr_entity_id": "a", "ps_organism_id": "bridge_a"},
                    {"sr_entity_id": "b", "ps_organism_id": "bridge_b"},
                ],
            )
        self.assertFalse(hasattr(first, BRIDGE_ORGANISM_ATTR))
        self.assertFalse(hasattr(second, BRIDGE_ORGANISM_ATTR))
    def test_plasticity_eases_s0_explore_requirement(self) -> None:
        min_t = stage_min_ticks(0) + 1
        self.assertFalse(
            can_advance_stage(0, min_t, explore_act_count=2, verify_success_count=0,
                              remember_event_count=0, reproduced=False, organism_peer_count=0)
        )
        self.assertTrue(
            can_advance_stage(
                0, min_t, explore_act_count=2, verify_success_count=0,
                remember_event_count=0, reproduced=False, organism_peer_count=0,
                plasticity_window=100,
            )
        )

    def test_plasticity_penalty_after_window_closed(self) -> None:
        min_t = stage_min_ticks(0) + 1
        late = min_t + 200
        self.assertTrue(
            can_advance_stage(
                0, late, explore_act_count=3, verify_success_count=0,
                remember_event_count=0, reproduced=False, organism_peer_count=0,
            )
        )
        self.assertFalse(
            can_advance_stage(
                0, late, explore_act_count=3, verify_success_count=0,
                remember_event_count=0, reproduced=False, organism_peer_count=0,
                plasticity_window=50,
                plasticity_penalty=True,
            )
        )

    def test_plasticity_window_active_flag(self) -> None:
        min_t = stage_min_ticks(0)
        self.assertFalse(plasticity_window_active(0, min_t, 50))
        self.assertTrue(plasticity_window_active(0, min_t + 1, 50))


class SocialBiasTests(unittest.TestCase):
    def test_retrieve_social_memory_bias(self) -> None:
        from core.Lotucosm.social_memory import retrieve_social_memory_bias

        genes = [
            MemoryGene("social:p1", {"ax": 10.0, "ay": -4.0}, 0.9),
        ]
        genes[0].strength = 0.8
        bx, by = retrieve_social_memory_bias(genes, blend=0.1)
        self.assertAlmostEqual(bx, 1.0)
        self.assertAlmostEqual(by, -0.4)

    def test_ps_social_action_bias(self) -> None:
        org = Organism("o1", (0.0, 0.0))
        org.social_learning_enabled = True
        org.developmental_ladder_enabled = True
        org.developmental_stage = 3
        observe_peer_action(org, "p2", {"act": {"signal": 0.8}}, 0.9)
        action = apply_ps_social_action_bias(
            org,
            {"sensor": {"command": "explore", "signal": 0.3, "params": {}}},
        )
        self.assertGreater(float(action["sensor"]["signal"]), 0.3)


class WorldBridgeStubTests(unittest.TestCase):
    def test_default_dual_mode(self) -> None:
        self.assertEqual(resolve_runtime_mode({}), RUNTIME_MODE_DUAL)
        self.assertFalse(unified_pond_enabled({}))

    def test_unified_mode_flag(self) -> None:
        self.assertTrue(
            unified_pond_enabled({"runtime_mode": RUNTIME_MODE_UNIFIED})
        )

    def test_sr_entity_bridge_and_sync(self) -> None:
        class _Ent:
            def __init__(self):
                self.id = "e1"
                self.position = [10.0, 20.0]
                self.energy = 80.0
                self.sr_debug_hud = {}

        ent = _Ent()
        pond = Pond(name="t", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        org = sr_entity_to_organism(ent, pond)
        org.position[0] = 55.0
        org.position[1] = 66.0
        org.energy = 42.0
        org.developmental_stage = 2
        sync_organism_to_sr_display(org, ent)
        self.assertAlmostEqual(ent.position[0], 55.0)
        self.assertAlmostEqual(ent.energy, 42.0)
        self.assertEqual(ent.sr_debug_hud.get("developmental_stage"), 2)

    def test_unified_pond_step_syncs(self) -> None:
        class _Ent:
            id = "e2"
            position = [0.0, 0.0]
            energy = 100.0
            sr_debug_hud = {}

        ent = _Ent()
        pond = Pond(name="t2", size=(100.0, 100.0), initial_organisms=0, initial_components=0)
        org = sr_entity_to_organism(ent, pond)
        org.energy = 77.0
        unified_pond_step(pond, [ent])
        self.assertAlmostEqual(ent.energy, float(org.energy), places=1)
        self.assertEqual(ent.sr_debug_hud.get("bridge_sync"), 1)

    def test_sync_sr_entity_to_organism(self) -> None:
        class _Ent:
            id = "e3"
            position = [5.0, 6.0]
            energy = 41.0
            health = 90.0

        ent = _Ent()
        org = Organism("o3", (0.0, 0.0))
        sync_sr_entity_to_organism(ent, org)
        self.assertAlmostEqual(org.position[0], 5.0)
        self.assertAlmostEqual(org.energy, 41.0)
        self.assertAlmostEqual(org.health, 90.0)

    def test_worldbridge_preserves_size_radius_on_creation_and_display_sync(self) -> None:
        class _Ent:
            id = "size1"
            position = [1.0, 2.0]
            energy = 80.0
            health = 70.0
            size = 18.0
            radius = 18.0
            sr_debug_hud = {}

        ent = _Ent()
        pond = Pond(name="size", size=(100.0, 100.0), initial_organisms=0, initial_components=0)
        org = sr_entity_to_organism(ent, pond)

        self.assertAlmostEqual(float(org.size), 18.0)
        self.assertAlmostEqual(float(org.radius), 18.0)

        org.set_size(24.0)
        sync_organism_to_sr_display(org, ent)

        self.assertAlmostEqual(float(ent.size), 24.0)
        self.assertAlmostEqual(float(ent.radius), 24.0)

    def test_bridge_spawned_organism_from_request(self) -> None:
        class _Ent:
            id = "spawn1"
            position = [0.0, 0.0]
            energy = 80.0
            entity_type = "organism"
            sr_debug_hud = {}

        ent = _Ent()
        pond = Pond(name="sp", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        req = {
            "scripts": [
                {
                    "properties": {
                        "developmental": {"enabled": True, "initial_stage": 1},
                        "social": {"enabled": True},
                    }
                }
            ]
        }
        org = bridge_spawned_organism(ent, pond, req)
        self.assertTrue(getattr(org, "developmental_ladder_enabled", False))
        self.assertTrue(getattr(org, "social_learning_enabled", False))
        self.assertEqual(getattr(ent, "_world_bridge_organism_id"), org.id)

    def test_bridge_spawned_organism_from_explicit_component_identity_receipt(self) -> None:
        class _Ent:
            id = "spawn_identity"
            position = [0.0, 0.0]
            energy = 80.0
            entity_type = "organism"
            sr_debug_hud = {}

        ent = _Ent()
        pond = Pond(name="sp_identity", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        request = {
            "component_identity_links": [
                {"sr_component_id": "sr-sensor", "ps_component_id": "bridge_spawn_identity_sensor",
                 "sr_organism_id": "spawn_identity", "ps_organism_id": "bridge_spawn_identity"},
                {"sr_component_id": "sr-actuator", "ps_component_id": "bridge_spawn_identity_actuator",
                 "sr_organism_id": "spawn_identity", "ps_organism_id": "bridge_spawn_identity"},
            ]
        }
        org = bridge_spawned_organism(ent, pond, request)
        self.assertEqual(org.components["bridge_spawn_identity_sensor"].sr_component_id, "sr-sensor")
        self.assertEqual(org.components["bridge_spawn_identity_actuator"].sr_component_id, "sr-actuator")

    def test_bridge_spawned_organism_rejects_component_identity_owner_drift(self) -> None:
        class _Ent:
            id = "spawn_bad_identity"
            position = [0.0, 0.0]
            energy = 80.0
            entity_type = "organism"

        ent = _Ent()
        pond = Pond(name="sp_bad_identity", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        request = {"component_identity_links": [{
            "sr_component_id": "sr-sensor", "ps_component_id": "bridge_spawn_bad_identity_sensor",
            "sr_organism_id": "other-sr", "ps_organism_id": "bridge_spawn_bad_identity",
        }]}
        with self.assertRaises(ValueError):
            bridge_spawned_organism(ent, pond, request)

    def test_developmental_profile_from_spawn_request(self) -> None:
        req = {
            "scripts": [
                {"properties": {"developmental": {"enabled": True}, "social": {"enabled": False}}}
            ]
        }
        profile = developmental_profile_from_spawn_request(req)
        self.assertTrue(profile.get("developmental", {}).get("enabled"))
        self.assertFalse(profile.get("social", {}).get("enabled"))

    def test_ensure_bridged_organisms_skips_existing(self) -> None:
        class _Ent:
            def __init__(self, eid: str):
                self.id = eid
                self.entity_type = "organism"
                self.position = [0.0, 0.0]
                self.energy = 100.0

        pond = Pond(name="eb", size=(100.0, 100.0), initial_organisms=0, initial_components=0)
        e1 = _Ent("a")
        e2 = _Ent("b")
        created = ensure_bridged_organisms([e1, e2], pond, equip_pvaec=False)
        self.assertEqual(created, 2)
        created2 = ensure_bridged_organisms([e1, e2], pond, equip_pvaec=False)
        self.assertEqual(created2, 0)

    def test_bridge_rejects_duplicate_organism_id_without_false_binding(self) -> None:
        class _Ent:
            id = "duplicate"
            position = [1.0, 2.0]
            energy = 50.0

        entity = _Ent()
        pond = Pond(name="collision", initial_organisms=0, initial_components=0)
        existing = Organism("bridge_duplicate", (7.0, 8.0))
        self.assertTrue(pond.add_organism(existing))

        with self.assertRaises(WorldBridgeNotReadyError):
            sr_entity_to_organism(entity, pond)

        self.assertIs(pond.organisms[existing.id], existing)
        self.assertEqual(pond.root_entities, [existing])
        self.assertFalse(hasattr(entity, BRIDGE_ORGANISM_ATTR))

    def test_bridge_rejects_pond_without_registration_api(self) -> None:
        class _Ent:
            id = "missing_api"
            position = [1.0, 2.0]
            energy = 50.0

        class _Pond:
            organisms = {}

        entity = _Ent()
        with self.assertRaises(WorldBridgeNotReadyError):
            sr_entity_to_organism(entity, _Pond())
        self.assertFalse(hasattr(entity, BRIDGE_ORGANISM_ATTR))

    def test_bridge_rejects_failed_registration_without_false_binding(self) -> None:
        class _Ent:
            id = "rejected"
            position = [1.0, 2.0]
            energy = 50.0

        class _Pond:
            def __init__(self):
                self.organisms = {}

            def add_organism(self, _organism):
                return False

        entity = _Ent()
        pond = _Pond()
        with self.assertRaises(WorldBridgeNotReadyError):
            sr_entity_to_organism(entity, pond)
        self.assertEqual(pond.organisms, {})
        self.assertFalse(hasattr(entity, BRIDGE_ORGANISM_ATTR))

    def test_snapshot_from_sr_includes_social_metric(self) -> None:
        snap = snapshot_from_sr(
            {
                "sim_running": True,
                "active": True,
                "population": 2,
                "avg_social_memory_count": 1.5,
            }
        )
        self.assertAlmostEqual(float(snap.extras.get("avg_social_memory_count", 0)), 1.5)


if __name__ == "__main__":
    unittest.main()
