# -*- coding: utf-8 -*-
"""PVAEC 内感受与 homeostatic_success 单元测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.sr_interoception import (
    exafference_predictability,
    homeostatic_success,
    interoception_for_entity,
    pvaec_verify_triple,
)


class _Ent:
    def __init__(self, energy: float = 100.0, health: float = 90.0):
        self.energy = energy
        self.max_energy = 200.0
        self.health = health
        self.max_health = 100.0
        self.sr_debug_hud = {"stress_norm": 0.3}


class PvaecInteroceptionTests(unittest.TestCase):
    def test_interoception_norms(self):
        snap = interoception_for_entity(_Ent(150.0, 80.0))
        self.assertAlmostEqual(snap["intero_energy_norm"], 0.75)
        self.assertAlmostEqual(snap["intero_health_norm"], 0.8)

    def test_homeostatic_success_energy_up(self):
        before = interoception_for_entity(_Ent(80.0))
        after = interoception_for_entity(_Ent(120.0))
        self.assertGreater(homeostatic_success(before, after), 0.5)

    def test_homeostatic_pvaec_step_runs_verify(self):
        class _Script(PvaecScript):
            homeostatic_pvaec_enabled = True

            def perceive(self, ctx):
                return {"x": 1}

            def think(self, obs, dt):
                return {}

            def act(self, dec, dt):
                if self.entity:
                    self.entity.energy += 5.0

        s = _Script()
        s.entity = _Ent(90.0)
        ctx = SceneRuntimeTickContext(
            owner_id="e1",
            owner_type="organism",
            owner_position=(0.0, 0.0),
            owner_radius=18.0,
            bounds=(800, 600),
            simulation_time=1.0,
            delta_time=0.05,
            peers=(),
        )
        s.pvaec_step(ctx, 0.05)
        self.assertGreaterEqual(getattr(s, "_pvaec_last_success", 0.0), 0.5)
        comps = getattr(s, "_pvaec_verify_components", {})
        self.assertIn("homeo", comps)
        self.assertIn("reaff", comps)
        self.assertIn("exaff", comps)

    def test_exafference_stable_when_obs_unchanged(self):
        obs = {
            "intrinsic_speed": 10.0,
            "sensor_pull": 0.2,
            "ambient_field": 100.0,
        }
        score = exafference_predictability(obs, dict(obs), 0.0, 0.0, 0.05)
        self.assertGreater(score, 0.6)

    def test_pvaec_verify_triple_weights(self):
        self.assertAlmostEqual(pvaec_verify_triple(1.0, 1.0, 1.0), 1.0)
        self.assertAlmostEqual(pvaec_verify_triple(0.0, 1.0, 0.0), 0.25)
        self.assertAlmostEqual(pvaec_verify_triple(1.0, 0.0, 0.0), 0.5)


if __name__ == "__main__":
    unittest.main()
