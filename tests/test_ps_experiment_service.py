# -*- coding: utf-8
"""PsExperimentService 单元测试。"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class PsExperimentServiceTests(unittest.TestCase):
    def test_run_sync_short(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        cfg = PsExperimentConfig(
            name="svc_smoke",
            ticks=30,
            seed=7,
            initial_organisms=3,
            evolution_generation_interval=15,
            snapshot_interval=10,
        )
        with tempfile.TemporaryDirectory() as tmp:
            svc = PsExperimentService(Path(tmp))
            progress_ticks: list[int] = []

            def on_prog(m: dict) -> None:
                progress_ticks.append(int(m.get("tick", 0)))

            summary, out_dir = svc.run_sync(cfg, export=True, progress_callback=on_prog)
            self.assertGreaterEqual(len(summary["snapshots"]), 1)
            self.assertGreater(len(progress_ticks), 0)
            self.assertIsNotNone(out_dir)
            assert out_dir is not None
            self.assertTrue((out_dir / "summary.json").is_file())
            snap = svc.get_ecology_snapshot()
            self.assertFalse(snap.get("ps_active"))
            self.assertGreater(int(snap.get("ps_population", 0)), 0)

    def test_list_presets(self):
        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        svc = PsExperimentService(ROOT)
        presets = svc.list_presets()
        self.assertTrue(any(p[0] == "pvaec_homeostasis_loop" for p in presets))

    def test_load_preset_relative(self):
        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        svc = PsExperimentService(ROOT)
        cfg = svc.load_preset_relative("workspace/experiments/quick_evolution_only.json")
        self.assertEqual(cfg.name, "quick_evolution_only")

    def test_runtime_projection_resolves_repository_application_root(self):
        import builtin.editor_extensions.ps_experiment_plugin as plugin_module
        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        projection = SimpleNamespace(services=object(), event_bus=object())
        with patch.object(plugin_module, "application_root", return_value=ROOT):
            resolved = plugin_module._resolve_application_root(projection)

        self.assertEqual(resolved, ROOT)
        service = PsExperimentService(resolved)
        config = service.load_preset_relative(
            "workspace/experiments/pvaec_homeostasis_loop.json"
        )
        self.assertEqual(config.name, "pvaec_homeostasis")
        self.assertTrue(
            (resolved / "workspace" / "experiments" / "pvaec_homeostasis_loop.json").is_file()
        )

    def test_list_recent_runs(self):
        import json

        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_dir = root / "workspace" / "state" / "experiment_runs"
            run_a = runs_dir / "run_a"
            run_b = runs_dir / "run_b"
            run_a.mkdir(parents=True)
            run_b.mkdir(parents=True)
            (run_a / "summary.json").write_text(
                json.dumps(
                    {
                        "finished_at": "2026-01-01T10:00:00Z",
                        "config": {"name": "older"},
                        "final": {
                            "population": 5,
                            "iteration": 2,
                            "avg_fitness": 0.5,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (run_b / "summary.json").write_text(
                json.dumps(
                    {
                        "finished_at": "2026-06-01T12:00:00Z",
                        "config": {"name": "newer"},
                        "final": {
                            "population": 10,
                            "iteration": 4,
                            "avg_fitness": 0.9,
                        },
                    }
                ),
                encoding="utf-8",
            )
            svc = PsExperimentService(root)
            svc.config.output_dir = "workspace/state/experiment_runs"
            runs = svc.list_recent_runs(max_runs=5)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]["name"], "newer")
            self.assertEqual(runs[0]["population"], 10)
            self.assertEqual(runs[1]["name"], "older")

    def test_list_recent_runs_after_sync(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

        cfg = PsExperimentConfig(
            name="list_hist_smoke",
            ticks=20,
            seed=3,
            initial_organisms=2,
            evolution_generation_interval=10,
            snapshot_interval=10,
        )
        with tempfile.TemporaryDirectory() as tmp:
            svc = PsExperimentService(Path(tmp))
            svc.run_sync(cfg, export=True)
            runs = svc.list_recent_runs(max_runs=20)
            names = [r.get("name") for r in runs]
            self.assertIn("list_hist_smoke", names)

    def test_compare_run_metrics(self):
        from core.VitaLoom.simulation.ps_experiment_service import compare_run_metrics

        baseline = {
            "population": 10,
            "iteration": 2,
            "avg_fitness": 0.5,
            "avg_memory_count": 3.0,
        }
        current = {
            "population": 15,
            "iteration": 4,
            "avg_fitness": 0.8,
            "avg_memory_count": 4.5,
        }
        d = compare_run_metrics(baseline, current)
        self.assertAlmostEqual(d["delta_population"], 5.0)
        self.assertAlmostEqual(d["delta_iteration"], 2.0)
        self.assertAlmostEqual(d["delta_avg_fitness"], 0.3)
        self.assertAlmostEqual(d["delta_avg_memory_count"], 1.5)

    def test_emit_ps_experiment_state(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from core.Lotucosm.experiment_config import PsExperimentConfig
        from core.VitaLoom.simulation.ps_experiment_service import (
            EVENT_STATE,
            PsExperimentService,
        )

        class _Bus:
            def __init__(self):
                self.events: list[tuple[str, object]] = []

            def publish(self, name: str, data=None):
                self.events.append((name, data))

        bus = _Bus()
        ctx = type("Ctx", (), {"event_bus": bus})()
        svc = PsExperimentService(ROOT)
        svc.bind_editor_context(ctx)
        cfg = PsExperimentConfig(name="state_smoke", ticks=15, seed=1, initial_organisms=2)
        svc.run_sync(cfg, export=False)
        state_events = [d for n, d in bus.events if n == EVENT_STATE]
        self.assertGreater(len(state_events), 0)
        phases = [getattr(s, "phase", None) for s in state_events]
        self.assertIn("running", phases)
        self.assertTrue("finished" in phases or "cancelled" in phases)

    def test_load_project_bindings_preset_and_defaults(self):
        import json

        from core.VitaLoom.simulation.ps_experiment_service import (
            EVENT_CONFIG_CHANGED,
            PsExperimentService,
        )

        class _Bus:
            def __init__(self):
                self.events: list[tuple[str, object]] = []

            def publish(self, name: str, data=None):
                self.events.append((name, data))

        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / "project.json").write_text(
                json.dumps(
                    {
                        "ps_experiment_preset": "workspace/experiments/pvaec_homeostasis_loop.json",
                        "evolution_defaults": {"ticks": 777, "mutation_rate": 0.11},
                    }
                ),
                encoding="utf-8",
            )
            svc = PsExperimentService(ROOT)
            bus = _Bus()
            ctx = type("Ctx", (), {"event_bus": bus, "current_project_path": str(proj)})()
            svc.bind_editor_context(ctx)
            changed_events = [n for n, _ in bus.events if n == EVENT_CONFIG_CHANGED]
            self.assertGreaterEqual(len(changed_events), 1)
            self.assertEqual(svc.config.ticks, 777)
            self.assertAlmostEqual(svc.config.mutation_rate, 0.11)

    def test_project_bindings_are_idempotent_until_project_content_changes(self):
        import json

        from core.VitaLoom.simulation.ps_experiment_service import (
            EVENT_CONFIG_CHANGED,
            PsExperimentService,
        )

        class _Bus:
            def __init__(self):
                self.events: list[tuple[str, object]] = []

            def publish(self, name: str, data=None):
                self.events.append((name, data))

        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            project_json = proj / "project.json"
            project_json.write_text(
                json.dumps(
                    {
                        "ps_experiment_preset": "workspace/experiments/pvaec_homeostasis_loop.json",
                        "evolution_defaults": {"ticks": 321},
                    }
                ),
                encoding="utf-8",
            )
            svc = PsExperimentService(ROOT)
            bus = _Bus()
            ctx = type("Ctx", (), {"event_bus": bus, "current_project_path": str(proj)})()
            svc.bind_editor_context(ctx)
            self.assertEqual(svc.config.ticks, 321)
            changed_after_bind = sum(n == EVENT_CONFIG_CHANGED for n, _ in bus.events)

            self.assertFalse(svc.load_project_bindings(proj))
            self.assertEqual(
                sum(n == EVENT_CONFIG_CHANGED for n, _ in bus.events),
                changed_after_bind,
            )

            project_json.write_text(
                json.dumps(
                    {
                        "ps_experiment_preset": "workspace/experiments/pvaec_homeostasis_loop.json",
                        "evolution_defaults": {"ticks": 654},
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(svc.load_project_bindings(proj))
            self.assertEqual(svc.config.ticks, 654)


if __name__ == "__main__":
    unittest.main()
