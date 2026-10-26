#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check or update a project's Suite/Product/Capability lock file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_expected_lock(project_path: Path, repo_root: Path) -> dict[str, Any]:
    from core.VitaLoom.suite.project_lock import build_project_lock_for_path

    return build_project_lock_for_path(project_path, repo_root=repo_root)


def lock_matches(project_path: Path, expected: dict[str, Any]) -> bool:
    current_path = project_path / "project.lock.json"
    if not current_path.is_file():
        return False
    try:
        current = json.loads(current_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return _canonical(current) == _canonical(expected)


def diagnose_lock(project_path: Path, expected: dict[str, Any]) -> dict[str, str]:
    """Return the stable lock admission code used by the CLI."""
    from FrameCore.project_lock import load_project_lock, project_lock_schema_error

    path = project_path / "project.lock.json"
    if not path.is_file():
        return {"code": "missing", "message": "project.lock.json is missing"}
    current = load_project_lock(project_path)
    if current is None:
        return {"code": "invalid", "message": "project.lock.json is invalid or unreadable"}
    schema_error = project_lock_schema_error(current)
    if schema_error:
        return {"code": "unsupported_schema", "message": schema_error}
    if "schema_version" not in current:
        expected_legacy = dict(expected)
        expected_legacy.pop("schema_version", None)
        legacy = _canonical(current) == _canonical(expected_legacy)
        return {
            "code": "legacy" if legacy else "stale",
            "message": "legacy lock is current" if legacy else "legacy lock is stale",
        }
    if _canonical(current) == _canonical(expected):
        return {"code": "ok", "message": "project.lock.json is current"}
    return {"code": "stale", "message": "project.lock.json is stale"}


def write_lock(project_path: Path, expected: dict[str, Any]) -> Path:
    from core.VitaLoom.suite.project_lock import write_project_lock

    return write_project_lock(project_path, expected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check or update project.lock.json from project.json and Suite registry."
    )
    parser.add_argument("project", help="Project directory containing project.json")
    parser.add_argument("--repo-root", default=str(ROOT), help="Suite repository/runtime root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if project.lock.json is missing or stale")
    mode.add_argument("--write", action="store_true", help="Write project.lock.json")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    project_path = Path(args.project).resolve()
    try:
        expected = build_expected_lock(project_path, repo_root)
    except Exception as exc:
        print(f"project lock build failed: {exc}", file=sys.stderr)
        return 2

    if args.check:
        diagnostic = diagnose_lock(project_path, expected)
        if diagnostic["code"] in {"ok", "legacy"}:
            print(f"project.lock.json {diagnostic['code']}: {project_path}")
            return 0
        print(
            f"project.lock.json {diagnostic['code']}: {diagnostic['message']}",
            file=sys.stderr,
        )
        return 1

    if args.write:
        out = write_lock(project_path, expected)
        print(f"wrote {out}")
        return 0

    print(_canonical(expected), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

