# -*- coding: utf-8 -*-
"""PsExperimentRunner 冒烟：短跑可完成且记忆/世代有变化。"""
from __future__ import annotations

import unittest

from builtin.systems.ps_experiment_runner import PsExperimentRunner
from core.Lotucosm.experiment_config import PsExperimentConfig


class PsExperimentRunnerTests(unittest.TestCase):
    def test_short_run_produces_snapshots_and_memory(self):
        cfg = PsExperimentConfig(
            name="unit_smoke",
            ticks=40,
            seed=1,
            initial_organisms=4,
            initial_components=0,
            evolution_generation_interval=20,
            snapshot_interval=10,
            enable_pvaec_cycle_per_tick=True,
            enable_generation_orchestrator=True,
        )
        runner = PsExperimentRunner(cfg)
        summary = runner.run()
        self.assertGreaterEqual(len(summary["snapshots"]), 2)
        final = summary["final"]
        self.assertGreaterEqual(final["population"], 1)
        self.assertGreaterEqual(final["iteration"], 1)

    def test_pvaec_only_no_generation(self):
        cfg = PsExperimentConfig(
            name="pvaec_only",
            ticks=25,
            seed=2,
            initial_organisms=3,
            evolution_generation_interval=0,
            enable_generation_orchestrator=False,
            enable_pvaec_cycle_per_tick=True,
            snapshot_interval=25,
        )
        summary = PsExperimentRunner(cfg).run()
        self.assertEqual(summary["final"]["iteration"], 0)
        self.assertGreater(summary["final"]["avg_memory_count"], 0.0)


if __name__ == "__main__":
    unittest.main()
