# -*- coding: utf-8 -*-
"""Read-only SR/PS/PS_REPLAY runtime replay evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DO_NOT_CLAIM = (
    "unified_pond",
    "sr_ps_tick_merge",
    "full_unified_runtime_replay",
    "branching_history_conflict_resolution",
    "opengl_default_ready",
    "sr2d_native_acceleration",
)


class _ReplayStatusSrHost:
    def __init__(self, overlay_points: list[tuple[float, float]]) -> None:
        self._overlay_points = list(overlay_points)

    def set_ps_replay_overlay_points(self, points: list[tuple[float, float]]) -> None:
        self._overlay_points = list(points)

    def get_sr_ecology_snapshot(self) -> dict[str, Any]:
        return {
            "sim_running": False,
            "active": False,
            "population": 0,
            "overlay_point_count": len(self._overlay_points),
        }

    def is_sr_playing(self) -> bool:
        return False

    def refresh_canvas(self) -> None:
        return None


def _load_project_config(project_path: Path | None) -> dict[str, Any]:
    if project_path is None:
        return {}
    config_path = project_path / "project.json"
    if not config_path.is_file():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def build_runtime_replay_status(
    project_path: Path | None = None,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    from core.Lotucosm.runtime.ecology_observation import EcologyLane
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.core.service_keys import SIMULATION_SR_HOST
    from core.VitaLoom.simulation.ecology_registry import collect_ecology_snapshots
    from core.VitaLoom.simulation.ps_replay_overlay import overlay_points_from_run_dir
    from core.VitaLoom.simulation.simulation_coordinator import (
        SimulationCoordinator,
        SimulationLane,
    )

    project_config = _load_project_config(project_path)
    summary_path = run_dir / "summary.json" if run_dir is not None else None
    summary_available = bool(summary_path and summary_path.is_file())
    overlay_points = overlay_points_from_run_dir(run_dir) if run_dir is not None else []

    host = _ReplayStatusSrHost(overlay_points)
    registry = InMemoryRuntimeCapabilityRegistry()
    registry.register(SIMULATION_SR_HOST, host)
    ctx = type(
        "ReplayStatusContext",
        (),
        {
            "services": registry,
            "current_project_config": project_config,
            "current_project_path": str(project_path) if project_path else None,
        },
    )()
    coord = SimulationCoordinator(ctx)
    if overlay_points:
        coord.register_lane_start(SimulationLane.PS_REPLAY)
    lane_state = coord.snapshot()
    ecology_snapshots = collect_ecology_snapshots(ctx)

    return {
        "schema_version": 1,
        "status": "read_only_replay_evidence",
        "read_only": True,
        "project_path": str(project_path) if project_path else None,
        "lanes": {
            "active": sorted(lane_state.active_lanes),
            "defined": sorted(lane.value for lane in SimulationLane),
            "disallow_parallel_sr_ps": bool(lane_state.disallow_parallel_sr_ps),
        },
        "replay": {
            "run_dir": str(run_dir) if run_dir else None,
            "summary_path": str(summary_path) if summary_path else None,
            "summary_available": summary_available,
            "overlay_point_count": len(overlay_points),
        },
        "ecology": {
            "lanes_defined": sorted(lane.value for lane in EcologyLane),
            "lanes": [
                {
                    "lane": snap.lane.value,
                    "active": bool(snap.active),
                    "session_open": bool(snap.session_open),
                    "population": int(snap.population),
                    "generation": float(snap.generation),
                    "avg_fitness": float(snap.avg_fitness),
                    "extras": dict(snap.extras),
                }
                for snap in ecology_snapshots
            ],
        },
        "unified_pond_enabled": project_config.get("runtime_mode") == "unified_pond",
        "do_not_claim": list(DO_NOT_CLAIM),
    }
