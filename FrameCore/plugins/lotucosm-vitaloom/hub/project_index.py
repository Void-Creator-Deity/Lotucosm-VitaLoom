# -*- coding: utf-8 -*-
"""Suite Hub project index stored outside product runtimes."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from hub.hub_paths import hub_project_index_path, projects_root


def _norm(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def _read_index() -> list[str]:
    path = hub_project_index_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    raw_projects = data.get("projects", []) if isinstance(data, dict) else []
    if not isinstance(raw_projects, list):
        return []
    return [str(item) for item in raw_projects if item]


def _write_index(paths: Iterable[str | Path]) -> None:
    unique: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        path = Path(raw).resolve()
        key = _norm(path)
        if key in seen or not (path / "project.json").is_file():
            continue
        seen.add(key)
        unique.append(str(path))
    index_path = hub_project_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"schema_version": 1, "projects": unique}, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def register_known_project(project_path: str | Path) -> None:
    path = Path(project_path).resolve()
    if not (path / "project.json").is_file():
        return
    paths = _read_index()
    key = _norm(path)
    if all(_norm(existing) != key for existing in paths):
        paths.append(str(path))
    _write_index(paths)


def indexed_project_paths() -> list[str]:
    return [
        str(Path(path).resolve())
        for path in _read_index()
        if (Path(path) / "project.json").is_file()
    ]


def workspace_project_paths() -> list[str]:
    root = projects_root()
    paths: list[str] = []
    for parent in (root / "samples", root / "user"):
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if child.is_dir() and (child / "project.json").is_file():
                paths.append(str(child.resolve()))
    return paths


def discover_project_paths(*, include_external_recent: bool = False) -> list[str]:
    paths = workspace_project_paths()
    if include_external_recent:
        paths.extend(indexed_project_paths())
    return paths
