# -*- coding: utf-8 -*-
"""PsExperimentRunner 冒烟：短跑可完成且记忆/世代有变化。"""
from __future__ import annotations

import random
import unittest

import numpy as np

from builtin.systems.ps_experiment_runner import PsExperimentRunner
from core.Lotucosm.experiment_config import PsExperimentConfig


class PsExperimentRunnerTests(unittest.TestCase):
    @staticmethod
    def _numpy_state_equal(left, right):
        return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]

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

    def test_seeded_run_uses_local_owner_without_reseeding_process_globals(self):
        cfg = PsExperimentConfig(
            name="owner_isolation",
            ticks=5,
            seed=101,
            initial_organisms=2,
            initial_components=0,
            evolution_generation_interval=0,
            enable_generation_orchestrator=False,
            snapshot_interval=5,
        )
        python_before = random.getstate()
        numpy_before = np.random.get_state()

        PsExperimentRunner(cfg).run()

        self.assertEqual(random.getstate(), python_before)
        self.assertTrue(self._numpy_state_equal(np.random.get_state(), numpy_before))

    def test_seeded_runs_repeat_metrics(self):
        cfg = PsExperimentConfig(
            name="owner_repeat",
            ticks=10,
            seed=102,
            initial_organisms=3,
            initial_components=0,
            evolution_generation_interval=5,
            snapshot_interval=5,
        )
        first = PsExperimentRunner(cfg).run()
        second = PsExperimentRunner(cfg).run()

        self.assertEqual(first["snapshots"], second["snapshots"])
        self.assertEqual(first["final"], second["final"])

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


    def test_disaster_window_raises_pressure_in_war_ticks(self) -> None:
        from core.Lotucosm.experiment_config import PsDisasterWindow

        cfg = PsExperimentConfig(
            name="war_window",
            ticks=60,
            seed=3,
            initial_organisms=6,
            evolution_generation_interval=30,
            snapshot_interval=10,
            selection_pressure=0.5,
            disaster_window=PsDisasterWindow(
                start_tick=20,
                end_tick=40,
                selection_pressure_boost=0.3,
                max_population_cap=4,
            ),
        )
        runner = PsExperimentRunner(cfg)
        pond = runner.build_pond()
        runner._apply_disaster_window(25, pond)
        orch = pond.pvaec_orchestrator
        self.assertIsNotNone(orch)
        self.assertAlmostEqual(orch.selection_system.selection_pressure, 0.8, places=5)
        self.assertEqual(pond.max_population, 4)
        runner._apply_disaster_window(45, pond)
        self.assertAlmostEqual(orch.selection_system.selection_pressure, 0.5, places=5)

    def test_post_war_recovery_run_records_war_metrics(self) -> None:
        from core.Lotucosm.experiment_config import PsDisasterWindow

        cfg = PsExperimentConfig(
            name="post_war_short",
            ticks=90,
            seed=77,
            initial_organisms=10,
            max_population=20,
            evolution_generation_interval=40,
            snapshot_interval=20,
            enable_pvaec_cycle_per_tick=True,
            enable_generation_orchestrator=True,
            disaster_window=PsDisasterWindow(
                start_tick=50,
                end_tick=85,
                selection_pressure_boost=0.22,
                max_population_cap=10,
            ),
        )
        summary = PsExperimentRunner(cfg).run()
        final = summary["final"]
        self.assertIn(final.get("war_phase"), ("war", "recovery"))
        self.assertIsNotNone(final.get("population_at_war_end"))
        self.assertIsNotNone(final.get("war_population_min"))


if __name__ == "__main__":
    unittest.main()
