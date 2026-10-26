# -*- coding: utf-8 -*-
"""Read-only PS replay overlay tests for Phase 6."""
from __future__ import annotations

import json
import time
from pathlib import Path

from core.Lotucosm.runtime.ecology_observation import EcologyLane
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import SIMULATION_SR_HOST
from core.VitaLoom.simulation.ecology_registry import collect_ecology_snapshots
from core.VitaLoom.simulation.ps_replay_overlay import (
    overlay_points_from_run_dir,
    push_overlay_to_game_viewport,
)

ROOT = Path(__file__).resolve().parents[1]


class _FakeSrHost:
    def __init__(self) -> None:
        self.points: list[tuple[float, float]] = []

    def set_ps_replay_overlay_points(self, points: list[tuple[float, float]]) -> None:
        self.points = list(points)

    def get_sr_ecology_snapshot(self) -> dict[str, object]:
        return {
            "sim_running": True,
            "active": False,
            "population": 2,
            "overlay_point_count": len(self.points),
        }

    def is_sr_playing(self) -> bool:
        return False

    def refresh_canvas(self) -> None:
        return None


def test_ps_replay_overlay_reads_summary_without_mutating_scene(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    scene = project / "scene.pond"
    scene.write_text("pond-before\n", encoding="utf-8")
    before_text = scene.read_text(encoding="utf-8")
    before_mtime = scene.stat().st_mtime_ns
    time.sleep(0.002)

    run_dir = tmp_path / "runs" / "run_a"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "final": {
                    "positions_norm": [[0.1, 0.2], [1.4, -0.5]],
                    "population": 2,
                }
            }
        ),
        encoding="utf-8",
    )

    host = _FakeSrHost()
    registry = InMemoryRuntimeCapabilityRegistry()
    registry.register(SIMULATION_SR_HOST, host)
    ctx = type(
        "Ctx",
        (),
        {
            "services": registry,
            "current_project_path": str(project),
        },
    )()

    points = overlay_points_from_run_dir(run_dir)
    count = push_overlay_to_game_viewport(ctx, run_dir)

    assert points == [(0.1, 0.2), (1.0, 0.0)]
    assert count == 2
    assert host.points == points
    assert scene.read_text(encoding="utf-8") == before_text
    assert scene.stat().st_mtime_ns == before_mtime

    lanes = [snap.lane for snap in collect_ecology_snapshots(ctx)]
    assert EcologyLane.PS_REPLAY in lanes


def test_ps_replay_overlay_module_does_not_call_ps_tick_or_runner() -> None:
    source = (
        ROOT
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
        / "core"
        / "VitaLoom"
        / "simulation"
        / "ps_replay_overlay.py"
    ).read_text(encoding="utf-8")

    assert "Pond.update" not in source
    assert "PsExperimentRunner" not in source
