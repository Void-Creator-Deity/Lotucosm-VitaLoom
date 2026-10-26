#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Group dirty worktree entries so cleanup can be staged deliberately."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


GROUP_RULES = (
    ("framecore_plugin_runtime", ("?? FrameCore/", " M FrameCore/", "M  FrameCore/", "A  FrameCore/")),
    ("native_backends", ("?? native/", " M native/", "M  native/", "A  native/")),
    ("docs_plans", ("?? docs/", " M docs/", "M  docs/", "A  docs/")),
    ("tests", ("?? tests/", " M tests/", "M  tests/", "A  tests/")),
    ("tools", ("?? tools/", " M tools/", "M  tools/", "A  tools/")),
    ("old_root_deletions", (" D core/", " D builtin/", " D plugins/", " D projects/", " D data/")),
    ("history_deletions", (" D .history/",)),
)


def _git_status_lines() -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _group_for(line: str) -> str:
    path = line[3:].strip().strip('"')
    if path.startswith(".history/"):
        return "history_deletions"
    if path.startswith(("core/", "builtin/", "plugins/", "projects/", "data/")) and line.startswith(" D "):
        return "old_root_deletions"
    for group, prefixes in GROUP_RULES:
        if line.startswith(prefixes):
            return group
    return "other"


def collect_audit() -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    for line in _git_status_lines():
        groups.setdefault(_group_for(line), []).append(line)
    return {
        "schema_version": 1,
        "root": str(ROOT),
        "total": sum(len(items) for items in groups.values()),
        "groups": {
            name: {
                "count": len(items),
                "sample": items[:20],
            }
            for name, items in sorted(groups.items())
        },
        "policy": "audit only; do not delete, revert, stage, or commit from this tool",
    }


def main() -> int:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    print(json.dumps(collect_audit(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
