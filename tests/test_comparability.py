# -*- coding: utf-8
"""ADR 可比性阈值与 unified bridge 稳定性测试。"""
from __future__ import annotations

import unittest

from core.Lotucosm.runtime.comparability import (
    DEVELOPMENTAL_STAGE_REL_ERROR_MAX,
    POPULATION_REL_ERROR_MAX,
    ComparabilityReport,
    evaluate_adr_comparability,
    evaluate_snapshots_comparability,
    relative_error,
)
from core.Lotucosm.runtime.ecology_observation import EcologyLane, EcologySnapshot
from core.Lotucosm.runtime.world_bridge import (
    BRIDGE_ORGANISM_ATTR,
    ensure_bridged_organisms,
    unified_pond_step,
)
from core.Lotucosm.pond import Pond


class ComparabilityThresholdTests(unittest.TestCase):
    def test_relative_error_identical(self) -> None:
        self.assertAlmostEqual(relative_error(10.0, 10.0), 0.0)

    def test_population_within_threshold(self) -> None:
        report = evaluate_adr_comparability(
            {"population": 10, "avg_developmental_stage": 1.0},
            {"population": 11, "avg_developmental_stage": 1.0},
        )
        self.assertTrue(report.all_passed)
        pop_check = report.checks[0]
        self.assertEqual(pop_check.name, "population")
        self.assertLessEqual(relative_error(10, 11), POPULATION_REL_ERROR_MAX)

    def test_population_exceeds_threshold(self) -> None:
        report = evaluate_adr_comparability(
            {"population": 10, "avg_developmental_stage": 0},
            {"population": 20, "avg_developmental_stage": 0},
        )
        self.assertFalse(report.all_passed)

    def test_developmental_stage_threshold(self) -> None:
        report = evaluate_adr_comparability(
            {"population": 5, "avg_developmental_stage": 2.0},
            {"population": 5, "avg_developmental_stage": 2.4},
        )
        dev_checks = [c for c in report.checks if c.name == "avg_developmental_stage"]
        self.assertEqual(len(dev_checks), 1)
        self.assertTrue(dev_checks[0].passed)
        self.assertLessEqual(relative_error(2.0, 2.4), DEVELOPMENTAL_STAGE_REL_ERROR_MAX)

    def test_reproduction_abs_diff(self) -> None:
        report = evaluate_adr_comparability(
            {"population": 8},
            {"population": 8},
            reproduction_events_sr=3,
            reproduction_events_ps=4,
        )
        repro = [c for c in report.checks if c.name == "reproduction_events"]
        self.assertTrue(repro[0].passed)

    def test_evaluate_snapshots_comparability(self) -> None:
        sr = EcologySnapshot(
            lane=EcologyLane.SR_PLAY,
            active=True,
            session_open=True,
            label="SR",
            population=12,
            extras={"avg_developmental_stage": 1.5, "reproduction_events": 2},
        )
        ps = EcologySnapshot(
            lane=EcologyLane.PS_BATCH,
            active=True,
            session_open=True,
            label="PS",
            population=13,
            extras={"avg_developmental_stage": 1.6, "reproduction_events": 2},
        )
        report = evaluate_snapshots_comparability(sr, ps)
        self.assertIsInstance(report, ComparabilityReport)
        self.assertTrue(report.all_passed)
        repro = [c for c in report.checks if c.name == "reproduction_events"]
        self.assertEqual(len(repro), 1)
        self.assertTrue(repro[0].passed)

    def test_report_display_lines(self) -> None:
        report = evaluate_adr_comparability({"population": 10}, {"population": 10})
        lines = report.to_display_lines()
        self.assertTrue(any("可比性" in ln for ln in lines))
        self.assertTrue(any("population" in ln for ln in lines))


class UnifiedBridgeStabilityTests(unittest.TestCase):
    def test_fifty_tick_bridge_population_stable(self) -> None:
        class _Ent:
            def __init__(self, eid: str, x: float, y: float):
                self.id = eid
                self.entity_type = "organism"
                self.position = [x, y]
                self.energy = 100.0
                self.health = 90.0
                self.sr_debug_hud = {}

        pond = Pond(name="stab", size=(200.0, 200.0), initial_organisms=0, initial_components=0)
        ents = [_Ent(f"h{i}", float(i * 20), 50.0) for i in range(4)]
        ensure_bridged_organisms(ents, pond, equip_pvaec=False)
        self.assertEqual(len(pond.organisms), 4)
        for _ in range(50):
            unified_pond_step(pond, ents, delta_time=1.0)
        bridged = sum(1 for e in ents if getattr(e, BRIDGE_ORGANISM_ATTR, None))
        self.assertEqual(bridged, 4)
        self.assertGreater(len(pond.organisms), 0)
        for ent in ents:
            self.assertEqual(ent.sr_debug_hud.get("bridge_sync"), 1)


class EvolutionGenerationTests(unittest.TestCase):
    def test_ps_runner_tracks_reproduction_events(self) -> None:
        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig

        cfg = PsExperimentConfig(
            name="repro_test",
            ticks=30,
            seed=7,
            initial_organisms=4,
            max_population=8,
            evolution_generation_interval=10,
            enable_generation_orchestrator=True,
            snapshot_interval=10,
        )
        runner = PsExperimentRunner(cfg)
        summary = runner.run()
        repro = int((summary.get("final") or {}).get("reproduction_events", 0))
        self.assertGreater(repro, 0)


class DualComparabilityRunnerTests(unittest.TestCase):
    def test_run_dual_comparability_smoke(self) -> None:
        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.Lotucosm.runtime.dual_comparability_runner import run_dual_comparability

        cfg = PsExperimentConfig(
            name="dual_smoke",
            ticks=20,
            seed=99,
            initial_organisms=4,
            max_population=8,
            evolution_generation_interval=10,
            snapshot_interval=10,
        )
        runner = PsExperimentRunner(cfg)
        result = run_dual_comparability(runner, checkpoint_ticks=(10, 20))
        self.assertIn("final", result)
        self.assertIn("checkpoints", result)
        self.assertIsNotNone(result["final"].get("ps_metrics"))
        self.assertIsNotNone(result["final"].get("unified_bridge_metrics"))

    def test_arbitrary_checkpoint_tick_is_sampled_without_changing_interval(self) -> None:
        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.Lotucosm.runtime.dual_comparability_runner import run_dual_comparability

        cfg = PsExperimentConfig(
            name="dual_arbitrary_checkpoint",
            ticks=20,
            seed=99,
            initial_organisms=4,
            max_population=8,
            evolution_generation_interval=10,
            snapshot_interval=10,
        )
        runner = PsExperimentRunner(cfg)
        result = run_dual_comparability(runner, checkpoint_ticks=(15, 20))
        self.assertTrue(result["checkpoints"]["tick_15"]["passed"])
        self.assertEqual(result["checkpoints"]["tick_15"]["ps_metrics"]["tick"], 15)
        self.assertEqual(result["checkpoints"]["tick_15"]["unified_bridge_metrics"]["tick"], 15)
        self.assertEqual(runner.config.snapshot_interval, 10)


class EvolutionGenerationTests(unittest.TestCase):
    def test_second_generation_advances_iteration(self) -> None:
        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig

        cfg = PsExperimentConfig(
            name="gen2",
            ticks=55,
            seed=42,
            initial_organisms=8,
            max_population=16,
            evolution_generation_interval=25,
            enable_generation_orchestrator=True,
            snapshot_interval=25,
        )
        runner = PsExperimentRunner(cfg)
        summary = runner.run()
        iteration = int((summary.get("final") or {}).get("iteration", 0))
        repro = int((summary.get("final") or {}).get("reproduction_events", 0))
        self.assertGreaterEqual(iteration, 2, "second generation should advance iteration")
        self.assertGreater(repro, 0)


class ComparabilityDockTests(unittest.TestCase):
    def test_comparability_dock_lines_include_reproduction(self) -> None:
        from core.Lotucosm.runtime.comparability import (
            comparability_dock_lines,
            should_show_comparability_dock,
        )
        from core.Lotucosm.runtime.ecology_observation import EcologyLane, EcologySnapshot

        sr = EcologySnapshot(
            lane=EcologyLane.SR_PLAY,
            active=True,
            session_open=True,
            label="SR",
            population=8,
            extras={
                "reproduction_events": 3,
                "avg_developmental_stage": 1.0,
                "unified_bridge_enabled": True,
                "bridged_organism_count": 8,
            },
        )
        ps = EcologySnapshot(
            lane=EcologyLane.PS_BATCH,
            active=True,
            session_open=True,
            label="PS",
            population=8,
            extras={"reproduction_events": 2, "avg_developmental_stage": 1.1},
        )
        self.assertTrue(should_show_comparability_dock(sr, ps))
        lines = comparability_dock_lines(sr, ps)
        self.assertTrue(any("繁殖 SR=3" in ln for ln in lines))
        self.assertTrue(any("WorldBridge" in ln for ln in lines))
        self.assertTrue(any("reproduction_events" in ln for ln in lines))

    def test_should_show_with_reproduction_only(self) -> None:
        from core.Lotucosm.runtime.comparability import should_show_comparability_dock
        from core.Lotucosm.runtime.ecology_observation import EcologyLane, EcologySnapshot

        sr = EcologySnapshot(
            lane=EcologyLane.SR_PLAY,
            active=True,
            session_open=True,
            label="SR",
            population=0,
            extras={"reproduction_events": 1},
        )
        ps = EcologySnapshot(
            lane=EcologyLane.PS_BATCH,
            active=False,
            session_open=True,
            label="PS",
            population=0,
            extras={"reproduction_events": 1},
        )
        self.assertTrue(should_show_comparability_dock(sr, ps))


class ComparabilityMatrixTests(unittest.TestCase):
    def test_run_comparability_matrix_smoke(self) -> None:
        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.Lotucosm.runtime.dual_comparability_runner import run_comparability_matrix

        def factory(case: dict) -> PsExperimentRunner:
            cfg = PsExperimentConfig(
                name=str(case.get("name", "m")),
                ticks=15,
                seed=11,
                initial_organisms=4,
                max_population=8,
                evolution_generation_interval=10,
                snapshot_interval=5,
                developmental_ladder_enabled=bool(
                    (case.get("overrides") or {}).get("developmental_ladder_enabled", False)
                ),
            )
            return PsExperimentRunner(cfg)

        matrix = run_comparability_matrix(
            [
                {"name": "a", "overrides": {}},
                {"name": "b", "overrides": {"developmental_ladder_enabled": True}},
            ],
            base_runner_factory=factory,
            checkpoint_ticks=(10, 15),
        )
        self.assertEqual(len(matrix.get("cases") or []), 2)
        self.assertIn("all_passed", matrix)

    def test_post_war_recovery_matrix_unified_bridge(self) -> None:
        import json
        from pathlib import Path

        from builtin.systems.ps_experiment_runner import PsExperimentRunner
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.Lotucosm.runtime.dual_comparability_runner import run_dual_comparability

        root = Path(__file__).resolve().parents[1]
        cfg_path = root / "workspace" / "experiments" / "post_war_recovery.json"
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        raw["ticks"] = 80
        raw["name"] = "post_war_matrix_smoke"
        cfg = PsExperimentConfig.from_dict(raw)
        result = run_dual_comparability(
            PsExperimentRunner(cfg),
            checkpoint_ticks=(20, 40, 80),
        )
        self.assertIsNotNone(result["final"].get("unified_bridge_metrics"))
        self.assertTrue(result.get("all_passed"))


if __name__ == "__main__":
    unittest.main()
