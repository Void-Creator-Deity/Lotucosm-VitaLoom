# -*- coding: utf-8
"""生态观测接缝单元测试。

职责: 锁定 SR/PS 生态快照的统一显示契约。
排错: 失败时检查 ecology_observation 与 PsExperimentService 指标字段。
"""
from __future__ import annotations

import unittest

from core.Lotucosm.runtime.ecology_observation import (
    EcologyLane,
    snapshot_from_ps,
    snapshot_from_sr,
)
from core.VitaLoom.simulation.ps_experiment_service import compare_run_metrics


class EcologyObservationTests(unittest.TestCase):
    def test_snapshot_from_sr_idle(self):
        snap = snapshot_from_sr({})
        self.assertEqual(snap.lane, EcologyLane.SR_PLAY)
        self.assertFalse(snap.session_open)

    def test_snapshot_from_sr_playing(self):
        snap = snapshot_from_sr(
            {
                "sim_running": True,
                "active": True,
                "paused": False,
                "sim_time": 12.5,
                "population": 4,
                "population_peak": 6,
                "avg_generation": 1.2,
                "total_energy": 80.0,
                "play_goals_satisfied": True,
                "wander_amp_variance": 0.1,
                "avg_developmental_stage": 1.5,
                "pct_at_stage_s4": 0.25,
                "developmental_ladder_enabled": True,
                "avg_memory_gene_count": 2.0,
                "avg_social_memory_count": 0.5,
                "unified_bridge_enabled": True,
                "bridged_organism_count": 3,
            }
        )
        self.assertTrue(snap.session_open)
        self.assertEqual(snap.population, 4)
        lines = snap.to_display_lines()
        self.assertTrue(any("SR 段" in ln for ln in lines))
        self.assertTrue(any("WorldBridge" in ln for ln in lines))
        self.assertTrue(any("社会记忆" in ln for ln in lines))

    def test_snapshot_from_ps_running(self):
        snap = snapshot_from_ps(
            {
                "ps_active": True,
                "ps_tick": 10,
                "ps_total_ticks": 100,
                "ps_population": 8,
                "ps_iteration": 2,
                "ps_avg_fitness": 0.42,
                "ps_avg_memory_gene_count": 1.5,
                "ps_avg_social_memory_count": 0.2,
                "ps_avg_developmental_stage": 1.1,
                "ps_developmental_ladder_enabled": True,
            }
        )
        self.assertTrue(snap.active)
        self.assertEqual(snap.tick, 10)
        lines = snap.to_display_lines()
        self.assertTrue(any("社会记忆" in ln for ln in lines))

    def test_snapshot_from_ps_service_missing(self):
        snap = snapshot_from_ps({"ps_service_missing": True})
        lines = snap.to_display_lines()
        self.assertIn("服务未加载", "\n".join(lines))

    def test_compare_run_metrics_import(self):
        baseline = {"population": 1, "iteration": 0, "avg_fitness": 0.1, "avg_memory_count": 1.0}
        current = {"population": 3, "iteration": 1, "avg_fitness": 0.4, "avg_memory_count": 2.0}
        d = compare_run_metrics(baseline, current)
        self.assertAlmostEqual(d["delta_population"], 2.0)


if __name__ == "__main__":
    unittest.main()
