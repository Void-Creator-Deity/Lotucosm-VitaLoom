# -*- coding: utf-8
"""PVAEC tick 链：胞外漂移 + 边权学习 + game_mode 隔离。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.Lotucosm.sr_fluid_flow import (
    SrFluidCouplingConfig,
    apply_extracellular_drift,
    step_nutrient_field_exchange,
)
from core.Lotucosm.sr_membrane_topology import learn_chemo_edge_weights


def _org(x, y, *, vx=0.0, vy=0.0, r=22.0, eid="o1"):
    return SimpleNamespace(
        id=eid,
        entity_type="organism",
        position=[x, y],
        velocity=[vx, vy],
        radius=r,
        pinned=False,
        membrane_locked=False,
    )


def _nut(x, y, *, r=10.0, eid="n1"):
    return SimpleNamespace(
        id=eid,
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
        emission_strength=1.0,
    )


class PvaecTickPhysicsChainTests(unittest.TestCase):
    def test_drift_toward_nutrient(self) -> None:
        org = _org(100.0, 100.0)
        nut = _nut(220.0, 100.0)
        cfg = SrFluidCouplingConfig(enabled=True, drift_gain=0.8, max_drift_accel=120.0)
        apply_extracellular_drift([org, nut], {}, 0.05, cfg)
        self.assertGreater(float(org.velocity[0]), 0.0)

    def test_uptake_depletes_nutrient_emission(self) -> None:
        org = _org(100.0, 100.0, r=24.0)
        nut = _nut(115.0, 100.0, r=10.0)
        nut.emission_strength = 1.0
        cfg = SrFluidCouplingConfig(uptake_rate=4.0)
        step_nutrient_field_exchange([org, nut], 0.1, cfg)
        self.assertGreater(float(getattr(nut, "_sr_field_depletion", 0.0)), 0.0)
        self.assertLess(float(nut.emission_strength), 1.0)

    def test_learn_chemo_edges_reward(self) -> None:
        edges = [{"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.0}]
        up = learn_chemo_edge_weights(edges, reward=0.9, stress=0.0, learn_rate=0.2)
        down = learn_chemo_edge_weights(edges, reward=0.1, stress=0.8, learn_rate=0.2)
        self.assertGreater(up[0]["weight"], down[0]["weight"])

    def test_game_mode_skips_fluid_coupling_in_viewport(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        gv = GameViewport.__new__(GameViewport)
        gv._sr_game_mode = True
        with patch("core.Lotucosm.scene_runtime.game_tick.step_game_runtime") as step:
            GameViewport._update_scene_runtime_entities(gv, 0.05)
            step.assert_called_once()
        gv._sr_game_mode = False
        gv._scene_runtime_time = 0.0
        gv._scene_bounds = MagicMock(return_value=(400.0, 300.0))
        gv.scene_runtime_entities = []
        gv._sr_biosphere_load = 0.0
        gv._sr_biosphere_prev_load = 0.0
        gv._sr_load_max = 1.0
        gv._sr_signal_edges = []
        gv._scene_runtime_edges = []
        gv._sr_membrane_attach = {}
        gv._sr_fluid_coupling_cfg = SrFluidCouplingConfig()
        gv._sr_field_grid = None
        gv._scene_runtime_emissions_prev = {}
        gv._sr_caps_game = MagicMock(return_value={})
        gv._sr_input_snapshot = MagicMock(return_value=MagicMock())
        gv._run_script_tick_batch = MagicMock()
        gv._process_sr_damage_requests = MagicMock()
        gv._process_sr_removal_requests = MagicMock()
        gv._process_sr_spawn_requests = MagicMock()
        gv._sync_membrane_positions = MagicMock()
        gv._sr_inbound_for_entity = MagicMock(return_value={})
        gv._scene_runtime_neighbor_ids = {}
        gv._parent_organism_for_membrane_child = MagicMock(return_value=None)
        gv._apply_actuator_coupling = MagicMock()
        gv._apply_membrane_edge_learning = MagicMock()
        gv._sr_physics_world = MagicMock()
        gv._sr_nutrient_target_count = 0
        gv._advance_sr_visual_integrators = MagicMock()
        gv.editor_context = MagicMock(current_project_path=None)
        gv._refresh_sr_hud = MagicMock()
        gv._maybe_log_scene_episode = MagicMock()
        gv._snapshot_sr_channel_out_prev = MagicMock()
        with patch(
            "core.Lotucosm.scene_runtime.session_outcome.resolve_session_outcomes"
        ), patch(
            "core.Lotucosm.sr_fluid_flow.apply_extracellular_drift"
        ) as drift:
            GameViewport._update_scene_runtime_entities(gv, 0.05)
            drift.assert_called_once()


if __name__ == "__main__":
    unittest.main()
