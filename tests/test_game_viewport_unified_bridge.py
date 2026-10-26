# -*- coding: utf-8
"""GameViewport unified_pond 桥接：模式切换、预桥接、tick 同步。"""
from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR
from core.Lotucosm.runtime.world_bridge_live_checkpoint import LiveCheckpointAdapters
from core.Lotucosm.runtime.world_bridge_transaction_authority import WorldBridgeHandoffFailure
from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    validate_worldbridge_live_dual_lane_trace,
)
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from core.Lotucosm.scripts import ScriptBase
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence


class GameViewportUnifiedBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_refresh_unified_pond_mode_dual_default(self) -> None:
        gv = GameViewport()
        gv._refresh_unified_pond_mode({})
        self.assertFalse(gv._unified_pond_mode)
        self.assertIsNone(gv._unified_pond)

    def test_refresh_unified_pond_mode_enabled(self) -> None:
        gv = GameViewport()
        gv._refresh_unified_pond_mode({"runtime_mode": "unified_pond"})
        self.assertTrue(gv._unified_pond_mode)

    def test_ensure_unified_bridge_for_scene_creates_organisms(self) -> None:
        gv = GameViewport()
        gv._unified_pond_mode = True
        o1 = gv._SceneRuntimeEntity("hub1", "organism", (50.0, 50.0), 20.0)
        o1.energy = 90.0
        gv.scene_runtime_entities = [o1]
        gv._ensure_unified_bridge_for_scene()
        self.assertIsNotNone(gv._unified_pond)
        oid = getattr(o1, BRIDGE_ORGANISM_ATTR, None)
        self.assertTrue(oid)
        self.assertIn(str(oid), gv._unified_pond.organisms)
        self.assertIs(o1.pond, gv._unified_pond)

    def test_dynamic_script_instantiation_stays_in_current_unified_pond(self) -> None:
        gv = GameViewport(identity_source=DeterministicIdentitySource("e425"))
        gv._unified_pond_mode = True
        entity = gv._SceneRuntimeEntity("hub-script", "organism", (5.0, 5.0), 12.0)
        gv.scene_runtime_entities = [entity]
        gv._ensure_unified_bridge_for_scene()

        script = ScriptBase()
        entity.add_script(script)
        created = script.instantiate("other")
        self.assertIsNotNone(created)
        self.assertIs(created.pond, gv._unified_pond)
        self.assertTrue(str(created.id).startswith("entity_"))
        self.assertIn(created, gv._unified_pond.root_entities)

    def test_runtime_script_failure_is_reported_to_host_sink(self) -> None:
        gv = GameViewport()
        entity = gv._SceneRuntimeEntity("runtime-failure", "organism", (5.0, 5.0), 12.0)

        class FailingScript(ScriptBase):
            def update(self, delta_time: float) -> None:
                raise RuntimeError("planned script failure")

        script = FailingScript()
        script._scene_script_path = "project/scripts/failing.py"
        entity.add_script(script)
        receipts: list[tuple[object, ...]] = []
        context = SimpleNamespace(
            delta_time=0.05,
            runtime_failure_sink=lambda *args: receipts.append(args),
        )

        with self.assertRaisesRegex(RuntimeError, "planned script failure"):
            entity.step_scripts(context)

        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0][0:3], ("project/scripts/failing.py", "runtime", "execution_failed"))

    def test_run_unified_pond_bridge_tick_syncs_hud(self) -> None:
        gv = GameViewport()
        gv._unified_pond_mode = True
        ent = gv._SceneRuntimeEntity("hub2", "organism", (10.0, 10.0), 15.0)
        ent.energy = 55.0
        ent.sr_debug_hud = {}
        gv.scene_runtime_entities = [ent]
        gv._ensure_unified_bridge_for_scene()
        pond = gv._unified_pond
        oid = getattr(ent, BRIDGE_ORGANISM_ATTR)
        org = pond.organisms[str(oid)]
        org.developmental_stage = 2
        gv._run_unified_pond_bridge_tick(0.05)
        self.assertAlmostEqual(float(ent.energy), float(org.energy), places=1)
        self.assertEqual(ent.sr_debug_hud.get("bridge_sync"), 1)
        self.assertEqual(ent.sr_debug_hud.get("developmental_stage"), 2)

    def test_bridge_delivers_canonical_input_batch_to_pond(self) -> None:
        gv = GameViewport()
        gv._unified_pond_mode = True
        ent = gv._SceneRuntimeEntity("hub-input", "organism", (10.0, 10.0), 15.0)
        gv.scene_runtime_entities = [ent]
        gv._ensure_unified_bridge_for_scene()
        sequence = WorldBridgeInputSequence()
        event = sequence.append("key_down", {"key": "W"})
        gv._worldbridge_input_events_last_tick = [event]

        self.assertIsNone(gv._run_unified_pond_bridge_tick(0.05))
        self.assertEqual(gv._unified_pond.worldbridge_input_events_last_tick, [event])

    def test_ps_death_retires_sr_hub_and_attached_child_without_rebridge(self) -> None:
        gv = GameViewport()
        gv._unified_pond_mode = True
        hub = gv._SceneRuntimeEntity("retired_hub", "organism", (10.0, 10.0), 15.0)
        hub.energy = 50.0
        child = gv._SceneRuntimeEntity("retired_child", "sensor", (12.0, 10.0), 4.0)
        gv.scene_runtime_entities = [hub, child]
        gv._sr_membrane_attach[child.id] = (hub.id, 2.0, 0.0)
        gv._ensure_unified_bridge_for_scene()
        pond = gv._unified_pond
        organism_id = getattr(hub, BRIDGE_ORGANISM_ATTR)
        pond.organisms[organism_id].set_dead(True)

        gv._run_unified_pond_bridge_tick(0.05)

        self.assertNotIn(organism_id, pond.organisms)
        self.assertEqual(gv.scene_runtime_entities, [])
        self.assertNotIn(child.id, gv._sr_membrane_attach)
        gv._run_unified_pond_bridge_tick(0.05)
        self.assertNotIn(organism_id, pond.organisms)

    def test_opt_in_live_trace_uses_real_viewport_and_pond_adapters(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._scene_runtime_time = 1.5
        gv._unified_pond_mode = True
        ent = gv._SceneRuntimeEntity("hub_trace", "organism", (4.0, 6.0), 12.0)
        ent.energy = 55.0
        gv.scene_runtime_entities = [ent]

        trace = gv._run_unified_pond_bridge_tick(0.05, capture_trace=True)

        self.assertIsInstance(trace, dict)
        self.assertTrue(validate_worldbridge_live_dual_lane_trace(trace)["valid"])
        self.assertFalse(trace["atomic_checkpoint"])
        self.assertEqual(trace["trace"]["lanes"]["sr"]["clock_value"], 1.5)
        self.assertEqual(trace["trace"]["lanes"]["ps"]["clock_value"], 1)
        self.assertEqual(len(trace["trace"]["entity_links"]), 1)

        evaluation = evaluate_worldbridge_live_trace_fields(trace)
        self.assertTrue(validate_worldbridge_live_trace_field_evaluation(evaluation)["valid"])
        self.assertIn(evaluation["aggregate_comparable_status"], {"comparable_pass", "comparable_mismatch"})
        self.assertFalse(evaluation["same_instant_parity"])
        self.assertFalse(evaluation["atomic_checkpoint"])
        self.assertFalse(evaluation["replay_admitted"])
        self.assertFalse(evaluation["default_ready"])

    def test_bridge_failure_is_contained_with_phase_receipt(self) -> None:
        class FailingPond:
            def __init__(self, organism: object) -> None:
                self.organisms = {"ps:failure": organism}
                self.update_calls = 0

            def update(self) -> None:
                self.update_calls += 1
                raise RuntimeError("planned Pond failure")

        gv = GameViewport()
        gv._unified_pond_mode = True
        ent = gv._SceneRuntimeEntity("hub_failure", "organism", (2.0, 3.0), 10.0)
        ent.energy = 40.0
        ent.sr_debug_hud = {}
        setattr(ent, BRIDGE_ORGANISM_ATTR, "ps:failure")
        organism = type("Organism", (), {})()
        organism.position = [0.0, 0.0]
        organism.velocity = [0.0, 0.0]
        organism.acceleration = [0.0, 0.0]
        organism.energy = 100.0
        organism.health = 100.0
        organism.developmental_stage = 0
        pond = FailingPond(organism)
        gv.scene_runtime_entities = [ent]
        gv._ensure_unified_pond = lambda: pond

        self.assertIsNone(gv._run_unified_pond_bridge_tick(0.05))
        self.assertEqual(pond.update_calls, 1)
        receipt = gv._worldbridge_last_handoff_failure
        self.assertEqual(receipt["phase"], "pond_update")
        self.assertTrue(receipt["partial_mutation_possible"])
        self.assertFalse(receipt["rollback_performed"])

    def test_bridge_failure_in_transactional_mode_is_rethrown_with_receipt(self) -> None:
        class FailingPond:
            def __init__(self) -> None:
                self.organisms = {}
                self.update_calls = 0

            def update(self) -> None:
                self.update_calls += 1
                raise RuntimeError("planned transactional Pond failure")

        gv = GameViewport()
        gv._unified_pond_mode = True
        gv._sr_runtime_epoch = "e540-game-viewport"
        gv._using_scene_runtime = True
        gv._unified_pond = SimpleNamespace(payload={}, organisms={}, time=0)
        ent = gv._SceneRuntimeEntity("hub_tx_failure", "organism", (2.0, 3.0), 10.0)
        ent.energy = 40.0
        setattr(ent, BRIDGE_ORGANISM_ATTR, "ps:tx-failure")
        organism = SimpleNamespace(
            position=[0.0, 0.0],
            velocity=[0.0, 0.0],
            acceleration=[0.0, 0.0],
            energy=100.0,
            health=100.0,
            developmental_stage=0,
        )
        pond = FailingPond()
        pond.organisms["ps:tx-failure"] = organism
        gv.scene_runtime_entities = [ent]
        gv._ensure_unified_pond = lambda: pond

        restored_live_ps: list[object] = []
        live_ps_state = SimpleNamespace(digest="live-ps-state")
        adapters = LiveCheckpointAdapters(
            capture_sr=lambda: {"entities": []},
            restore_sr=lambda _state: None,
            capture_ps=lambda: {"organisms": {}},
            restore_ps=lambda _state: None,
            capture_bridge=lambda: [],
            restore_bridge=lambda _links: None,
            capture_input=lambda: {},
            restore_input=lambda _state: None,
            capture_randomness=lambda: None,
            restore_randomness=lambda _state: None,
            capture_lifecycle=lambda: {},
            restore_lifecycle=lambda _state: None,
            capture_live_ps=lambda: live_ps_state,
            restore_live_ps=lambda state: restored_live_ps.append(state),
        )

        with patch(
            "core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter."
            "create_game_viewport_live_checkpoint_adapters",
            return_value=adapters,
        ):
            with self.assertRaisesRegex(
                WorldBridgeHandoffFailure, "planned transactional Pond failure"
            ):
                gv._run_unified_pond_bridge_tick(0.05, transactional=True)

        self.assertEqual(pond.update_calls, 1)
        receipt = gv._worldbridge_last_handoff_failure
        self.assertEqual(receipt["phase"], "pond_update")
        self.assertTrue(receipt["partial_mutation_possible"])
        self.assertTrue(receipt["rollback_performed"])
        self.assertTrue(receipt["transaction_rollback"]["rollback_attempted"])
        self.assertTrue(receipt["transaction_rollback"]["rollback_complete"])
        self.assertEqual(restored_live_ps, [live_ps_state])

    def test_run_snapshot_phase_enables_transactional_bridge(self) -> None:
        gv = GameViewport()
        calls: list[tuple[float, bool]] = []
        gv.scene_runtime_entities = []
        gv._sr_biosphere_load = 0.0
        gv._sr_biosphere_prev_load = 0.0
        gv._sr_load_max = 100.0
        gv._sr_game_mode = True
        gv._safe_war_profile = lambda: None
        gv._track_war_phase_transition = lambda _entities: None
        gv._sr_game_mode = True
        gv._snapshot_sr_channel_out_prev = lambda: None
        gv._refresh_sr_hud = lambda _entities: None
        gv._publish_sr_runtime_snapshots = lambda: None
        gv.capture_worldbridge_shared_state_envelope = lambda _dt: {}
        gv.consume_worldbridge_shared_state_envelope = lambda _envelope: None
        gv._maybe_log_scene_episode = lambda _dt: None
        gv._sr_biosphere_prev_load = 0.0
        gv._run_unified_pond_bridge_tick = (
            lambda dt, transactional=False: calls.append((dt, transactional))
        )

        with patch(
            "core.Lotucosm.scene_runtime.session_outcome."
            "resolve_session_outcomes",
            lambda _viewport: None,
        ):
            gv.run_snapshot_phase({"dt": 0.05, "load_before": 0.0})

        self.assertEqual(calls, [(0.05, True)])

    def test_snapshot_phase_does_not_swallow_transaction_failure(self) -> None:
        gv = GameViewport()
        gv.scene_runtime_entities = []
        gv._sr_biosphere_load = 0.0
        gv._sr_game_mode = True
        gv._sr_load_max = 100.0
        gv._safe_war_profile = lambda: None
        gv._snapshot_sr_channel_out_prev = lambda: None
        gv._refresh_sr_hud = lambda _entities: None
        gv._run_unified_pond_bridge_tick = lambda _dt, transactional=False: (
            _ for _ in ()
        ).throw(RuntimeError("snapshot transaction failed"))

        with self.assertRaisesRegex(RuntimeError, "snapshot transaction failed"):
            gv.run_snapshot_phase({"dt": 0.05, "load_before": 0.0})

    def test_worldbridge_complete_tick_clears_authority_on_failure(self) -> None:
        gv = GameViewport()
        cleared: list[bool] = []

        def fail_complete() -> dict[str, object]:
            raise RuntimeError("receipt sealing failed")

        gv._worldbridge_tick_authority = SimpleNamespace(
            current_tick=lambda: {"tick_sequence": 1},
            complete_tick=fail_complete,
            clear_active_tick=lambda: cleared.append(True),
        )

        with self.assertRaisesRegex(RuntimeError, "receipt sealing failed"):
            gv._worldbridge_complete_tick()

        self.assertEqual(cleared, [True])

    def test_ecology_snapshot_reports_bridge_fields(self) -> None:
        gv = GameViewport()
        gv._using_scene_runtime = True
        gv.is_playing = True
        gv.is_paused = False
        gv._unified_pond_mode = True
        ent = gv._SceneRuntimeEntity("hub3", "organism", (0.0, 0.0), 12.0)
        gv.scene_runtime_entities = [ent]
        gv._ensure_unified_bridge_for_scene()
        snap = gv.get_sr_ecology_snapshot()
        self.assertTrue(snap["unified_bridge_enabled"])
        self.assertEqual(snap["bridged_organism_count"], 1)


if __name__ == "__main__":
    unittest.main()
