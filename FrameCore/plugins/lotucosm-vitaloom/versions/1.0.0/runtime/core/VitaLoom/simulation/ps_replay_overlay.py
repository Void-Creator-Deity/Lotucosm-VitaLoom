# -*- coding: utf-8
"""PS 实验快照只读叠加点（C.2）：从 experiment_runs 生成归一化坐标。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple


def _points_from_positions_norm(raw: Any, cap: int) -> List[Tuple[float, float]]:
    if not isinstance(raw, list):
        return []
    out: List[Tuple[float, float]] = []
    for item in raw[:cap]:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((min(1.0, max(0.0, float(item[0]))), min(1.0, max(0.0, float(item[1])))))
    return out


def overlay_points_from_run_dir(run_dir: Path, max_points: int = 80) -> List[Tuple[float, float]]:
    """从 summary.json 读取 positions_norm；无则回退 tick×pop 网格。"""
    summary_path = run_dir / "summary.json"
    if not summary_path.is_file():
        return []
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        final = data.get("final") or {}
        pts = _points_from_positions_norm(final.get("positions_norm"), max_points)
        if pts:
            return pts
        snaps = data.get("snapshots") or []
        if not isinstance(snaps, list) or not snaps:
            final = data.get("final") or {}
            pop = max(1, int(final.get("population", 1)))
            return _grid_points(1, pop, max_points)
        points: List[Tuple[float, float]] = []
        for i, snap in enumerate(snaps[:max_points]):
            if not isinstance(snap, dict):
                continue
            tick = float(snap.get("tick", i))
            pop = float(snap.get("population", 1))
            total_ticks = float(data.get("config", {}).get("ticks", tick + 1) or tick + 1)
            nx = min(1.0, max(0.0, tick / max(1.0, total_ticks)))
            ny = min(1.0, max(0.05, pop / max(1.0, pop * 1.2)))
            points.append((nx, ny))
        return points or _grid_points(1, 8, max_points)
    except Exception:
        return []


def _grid_points(cols: int, count: int, cap: int) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    n = min(cap, max(1, count))
    for i in range(n):
        nx = (i % cols) / max(1, cols)
        ny = (i // cols) / max(1, (n // cols) + 1)
        out.append((min(0.95, nx), min(0.95, ny)))
    return out


def push_overlay_to_game_viewport(editor_context: object, run_dir: Path) -> int:
    """将叠加点推送到 simulation.sr_host；返回点数。"""
    from core.VitaLoom.simulation.sr_host import get_sr_host

    points = overlay_points_from_run_dir(run_dir)
    host = get_sr_host(editor_context)
    host.set_ps_replay_overlay_points(points)
    return len(points)
