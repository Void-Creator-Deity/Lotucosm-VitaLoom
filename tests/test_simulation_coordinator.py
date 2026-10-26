# -*- coding: utf-8
"""SimulationCoordinator 单元测试。"""
from __future__ import annotations

import unittest

from core.VitaLoom.simulation.simulation_coordinator import (
    SimulationCoordinator,
    SimulationLane,
)


class SimulationCoordinatorTests(unittest.TestCase):
    def test_parallel_allowed_by_default(self):
        ctx = type("Ctx", (), {"current_project_config": {}})()
        coord = SimulationCoordinator(ctx)
        self.assertTrue(coord.register_lane_start(SimulationLane.SR_PLAY))
        self.assertTrue(coord.register_lane_start(SimulationLane.PS_BATCH))

    def test_disallow_parallel_sr_ps(self):
        ctx = type(
            "Ctx",
            (),
            {"current_project_config": {"disallow_parallel_sr_ps": True}},
        )()
        coord = SimulationCoordinator(ctx)
        self.assertTrue(coord.register_lane_start(SimulationLane.SR_PLAY))
        self.assertFalse(coord.register_lane_start(SimulationLane.PS_BATCH))
        coord.register_lane_stop(SimulationLane.SR_PLAY)
        self.assertTrue(coord.register_lane_start(SimulationLane.PS_BATCH))

    def test_ps_replay_lane_is_explicit_and_not_sr_ps_exclusive(self):
        ctx = type(
            "Ctx",
            (),
            {"current_project_config": {"disallow_parallel_sr_ps": True}},
        )()
        coord = SimulationCoordinator(ctx)

        self.assertTrue(coord.register_lane_start(SimulationLane.SR_PLAY))
        self.assertTrue(coord.register_lane_start(SimulationLane.PS_REPLAY))
        self.assertFalse(coord.register_lane_start(SimulationLane.PS_BATCH))

        snap = coord.snapshot()
        self.assertEqual(snap.disallow_parallel_sr_ps, True)
        self.assertIn("sr_play", snap.active_lanes)
        self.assertIn("ps_replay", snap.active_lanes)


if __name__ == "__main__":
    unittest.main()
