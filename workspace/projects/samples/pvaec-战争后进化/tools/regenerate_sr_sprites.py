#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the PVAEC war-recovery sample assets from project-owned code."""
from __future__ import annotations

import runpy
import shutil
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for path in (start, *start.parents):
        if (path / "FrameCore").is_dir() and (path / "main.py").is_file():
            return path
    raise RuntimeError("could not find repository root")


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    repo = _find_repo_root(project)
    source_project = repo / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    source_tool = source_project / "tools" / "regenerate_sr_sprites.py"
    if not source_tool.is_file():
        raise FileNotFoundError(source_tool)
    runpy.run_path(str(source_tool), run_name="__main__")
    for rel in (
        "assets/sprites",
        "assets/branding/logo.png",
        "assets/未标题-1.png",
    ):
        src = source_project / rel
        dst = project / rel
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print("Regenerated war-recovery assets in", project / "assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
