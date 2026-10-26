# -*- coding: utf-8
"""PS verify 三分单元测试。"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from core.Lotucosm.pvaec_cycle import PVAECCycle
from core.Lotucosm.ps_verify import (
    motor_from_ps_action,
    ps_exafference_predictability,
    ps_use_verify_triple,
    validate_action_legacy,
    validate_action_triple,
)
from core.Lotucosm.sr_developmental_ladder import VERIFY_SUCCESS_THRESHOLD
from core.Lotucosm.sr_interoception import interoception_for_entity, pvaec_verify_triple


class _Org:
    def __init__(self, energy: float = 100.0, health: float = 90.0):
        self.energy = energy
        self.max_energy = 200.0
        self.health = health
        self.max_health = 100.0
        self.velocity = np.array([1.0, 0.0])
        self.use_ps_verify_triple = True
        self._ps_pre_act_velocity = (0.5, 0.0)


class PsVerifyTripleTests(unittest.TestCase):
    def test_motor_from_explore_action(self) -> None:
        ax, ay = motor_from_ps_action({"c1": {"command": "explore", "params": {}}})
        self.assertGreater(abs(ax) + abs(ay), 0.0)

    def test_ps_exafference_stable_when_unchanged(self) -> None:
        obs = {"intero_energy_norm": 0.5, "sensor_a": 0.2}
        score = ps_exafference_predictability(obs, dict(obs), 0.0, 0.0, 1.0)
        self.assertGreater(score, 0.6)

    def test_validate_triple_uses_components(self) -> None:
        org = _Org(energy=80.0)
        org.energy = 120.0
        before = {**interoception_for_entity(_Org(80.0)), "sensor_a": 0.1}
        after = {**interoception_for_entity(org), "sensor_a": 0.1}
        action = {"sensor_a": {"command": "explore", "params": {"ax": 1.0}}}
        score = validate_action_triple(org, before, after, action, delta_time=1.0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        comps = getattr(org, "_ps_verify_components", {})
        self.assertIn("homeo", comps)
        self.assertIn("reaff", comps)
        self.assertIn("exaff", comps)
        self.assertAlmostEqual(
            score,
            pvaec_verify_triple(comps["homeo"], comps["reaff"], comps["exaff"]),
        )

    def test_legacy_validate_energy_up(self) -> None:
        org = _Org(energy=80.0)
        org.use_ps_verify_triple = False
        score = validate_action_legacy(org)
        org.energy = 120.0
        score2 = validate_action_legacy(org)
        self.assertGreater(score2, score)

    def test_pvaec_cycle_routes_triple_when_enabled(self) -> None:
        org = _Org()
        org.components = {}
        org.memory_system = SimpleNamespace(store=lambda _e: None, retrieve=lambda _p: [])
        org.enable_pvaec_cycle_per_tick = True
        cycle = PVAECCycle()
        self.assertTrue(ps_use_verify_triple(org))
        score = cycle.validate_action(
            org,
            {"intero_energy_norm": 0.4, "intero_health_norm": 0.8},
            {"intero_energy_norm": 0.55, "intero_health_norm": 0.82},
            {"act": {"command": "explore"}},
            {},
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertTrue(hasattr(org, "_ps_verify_components"))

    def test_verify_threshold_matches_sr(self) -> None:
        self.assertAlmostEqual(VERIFY_SUCCESS_THRESHOLD, 0.55)


if __name__ == "__main__":
    unittest.main()
