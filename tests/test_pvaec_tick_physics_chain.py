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

        simulation_driver = MagicMock()
        gv = SimpleNamespace(
            _sr_game_mode=True,
            _simulation_driver=simulation_driver,
            scene_runtime_entities=[object()],
            _worldbridge_begin_tick=MagicMock(),
            _worldbridge_complete_tick=MagicMock(),
            _worldbridge_abort_tick=MagicMock(),
            _worldbridge_record_rng_phase=MagicMock(),
            _worldbridge_record_clock_consumer=MagicMock(),
            _sr_input_snapshot=MagicMock(),
        )
        with patch("core.Lotucosm.scene_runtime.game_tick.step_game_runtime") as step, patch(
            "core.Lotucosm.scene_runtime.session_outcome.resolve_session_outcomes"
        ):
            GameViewport._update_scene_runtime_entities(gv, 0.05)
            step.assert_called_once_with(gv, 0.05)
        simulation_driver.tick.assert_not_called()

        gv._sr_game_mode = False
        with patch("core.Lotucosm.scene_runtime.session_outcome.resolve_session_outcomes"):
            GameViewport._update_scene_runtime_entities(gv, 0.05)
        simulation_driver.tick.assert_called_once_with(gv, 0.05)

if __name__ == "__main__":
    unittest.main()
