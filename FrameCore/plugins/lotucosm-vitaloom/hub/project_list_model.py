# -*- coding: utf-8 -*-
"""Project discovery model for the Suite Hub."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from FrameCore.project_lock import resolve_project_runtime
from hub.hub_paths import is_frozen_bundle, is_under_application_root
from hub.project_index import discover_project_paths


@dataclass(frozen=True)
class HubProjectEntry:
    name: str
    path: str
    loom_editor_version: str
    modified_at: str
    description: str = ""
    product_id: str = "lotucosm-vitaloom"
    product_version: str = ""
    lock_status: str = ""
    lock_admission: str = ""


def _read_project_meta(project_path: Path, repo_root: Path) -> Optional[HubProjectEntry]:
    project_json = project_path / "project.json"
    if not project_json.is_file():
        return None
    try:
        data = json.loads(project_json.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    name = str(data.get("name") or project_path.name)
    product_id = str(data.get("product_id") or "lotucosm-vitaloom")
    product_version = str(data.get("loom_editor_version") or "")
    lock_status = ""
    lock_admission = ""
    try:
        resolved = resolve_project_runtime(project_path, repo_root=repo_root)
        product_id = resolved.product_id
        product_version = resolved.product_version or product_version
        lock_status = resolved.lock_status_text
        lock_admission = resolved.lock_admission_code
    except Exception:
        lock_status = "unresolved"
        lock_admission = "invalid"
    return HubProjectEntry(
        name=name,
        path=str(project_path.resolve()),
        loom_editor_version=str(data.get("loom_editor_version") or ""),
        modified_at=str(data.get("modified_at") or data.get("created_at") or ""),
        description=str(data.get("description") or ""),
        product_id=product_id,
        product_version=product_version,
        lock_status=lock_status,
        lock_admission=lock_admission,
    )


def _collect_project_paths_from_disk(_repo_root: Path) -> List[str]:
    return discover_project_paths(include_external_recent=False)


def discover_hub_projects(
    repo_root: str | Path,
    *,
    include_external_recent: bool = False,
) -> List[HubProjectEntry]:
    root = Path(repo_root)
    seen: set[str] = set()
    entries: List[HubProjectEntry] = []
    paths: List[str] = list(_collect_project_paths_from_disk(root))

    for raw in discover_project_paths(include_external_recent=include_external_recent):
        if is_frozen_bundle() and not include_external_recent:
            if not is_under_application_root(raw):
                continue
        paths.append(raw)

    for raw in paths:
        path = Path(raw).resolve()
        key = os.path.normcase(str(path))
        if key in seen or not (path / "project.json").is_file():
            continue
        entry = _read_project_meta(path, root)
        if entry is None:
            continue
        seen.add(key)
        entries.append(entry)

    def sort_key(entry: HubProjectEntry) -> tuple[float, str]:
        timestamp = 0.0
        if entry.modified_at:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    timestamp = datetime.strptime(entry.modified_at[:19], fmt).timestamp()
                    break
                except ValueError:
                    continue
        return (-timestamp, entry.name.lower())

    entries.sort(key=sort_key)
    return entries


def filter_entries(entries: List[HubProjectEntry], query: str) -> List[HubProjectEntry]:
    q = (query or "").strip().lower()
    if not q:
        return entries
    return [
        entry
        for entry in entries
        if q in entry.name.lower()
        or q in entry.path.lower()
        or q in entry.description.lower()
    ]
