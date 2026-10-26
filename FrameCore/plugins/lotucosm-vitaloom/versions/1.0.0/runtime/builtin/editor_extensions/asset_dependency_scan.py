# -*- coding: utf-8 -*-
"""Editor-facing compatibility Adapter over the project asset-index Authority."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DependencyEdge:
    scene_file: str
    json_pointer: str
    kind: str
    raw_ref: str
    resolved_path: str
    exists: bool


def _to_edge(project: Path, row: dict[str, Any]) -> DependencyEdge:
    target = str(row.get("target", "") or "")
    raw = str(row.get("raw_ref", "") or "")
    if row.get("status") == "outside_project":
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = project / candidate
    else:
        candidate = project / target
    scene = str(row.get("scene", "") or "")
    scene_file = str(project / scene) if scene != "project.json" else str(project / "project.json")
    return DependencyEdge(
        scene_file=scene_file,
        json_pointer=str(row.get("json_pointer", "") or ""),
        kind=str(row.get("kind", "") or ""),
        raw_ref=raw,
        resolved_path=os.path.normpath(str(candidate)),
        exists=bool(row.get("exists", False)) and row.get("status") == "ok",
    )


def _index(project_root: str) -> dict[str, Any]:
    from core.VitaLoom.project.asset_index import build_project_asset_index

    return build_project_asset_index(project_root)


def scan_scene_file(scene_path: str, project_root: str) -> list[DependencyEdge]:
    """Return dependency edges for one `.pond` from the shared index snapshot."""
    project = Path(os.path.abspath(project_root))
    scene = Path(os.path.abspath(scene_path))
    try:
        scene_label = os.path.relpath(str(scene), str(project)).replace("\\", "/")
    except ValueError:
        return []
    rows = _index(str(project))["dependencies"]["edges"]
    return [_to_edge(project, row) for row in rows if row.get("scene") == scene_label]


def scan_project_json_active_scene(project_root: str) -> list[DependencyEdge]:
    project = Path(os.path.abspath(project_root))
    rows = _index(str(project))["dependencies"]["edges"]
    return [_to_edge(project, row) for row in rows if row.get("scene") == "project.json"]


def scan_project_dependencies(project_root: str) -> list[DependencyEdge]:
    """Project dependency Adapter preserving the legacy dataclass Interface."""
    project = Path(os.path.abspath(project_root))
    return [_to_edge(project, row) for row in _index(str(project))["dependencies"]["edges"]]


def reverse_index(edges: list[DependencyEdge]) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        out.setdefault(edge.resolved_path, []).append((edge.scene_file, edge.json_pointer))
    return out


def dependency_summary(edges: list[DependencyEdge]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    missing_by_kind: dict[str, int] = {}
    for edge in edges:
        by_kind[edge.kind] = by_kind.get(edge.kind, 0) + 1
        if not edge.exists:
            missing_by_kind[edge.kind] = missing_by_kind.get(edge.kind, 0) + 1
    return {
        "total_edges": len(edges),
        "by_kind": dict(sorted(by_kind.items())),
        "missing_total": sum(missing_by_kind.values()),
        "missing_by_kind": dict(sorted(missing_by_kind.items())),
    }


def format_dependency_scan_report(project_root: str, edges: list[DependencyEdge], summ: dict[str, Any]) -> str:
    lines = [
        f"[场景依赖] 工程: {project_root}",
        f"边总数: {summ.get('total_edges', 0)} | 按类型: {summ.get('by_kind')} | 缺失数: {summ.get('missing_total', 0)}",
    ]
    missing = [edge for edge in edges if not edge.exists]
    if not missing:
        lines.append("无缺失引用。")
    else:
        lines.append(f"缺失 {len(missing)} 条:")
        for edge in missing:
            lines.append(f"  [{edge.kind}] {edge.raw_ref}")
            lines.append(f"    -> {edge.resolved_path}")
            lines.append(f"    @ {edge.scene_file} {edge.json_pointer}")
    return "\n".join(lines)


