#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the PVAEC war-recovery sample audio from project-owned code."""
from __future__ import annotations

import runpy
import shutil
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
    source_tool = source_project / "tools" / "generate_sr_audio.py"
    if not source_tool.is_file():
        raise FileNotFoundError(source_tool)
    runpy.run_path(str(source_tool), run_name="__main__")
    src = source_project / "assets" / "audio"
    dst = project / "assets" / "audio"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print("Regenerated war-recovery audio in", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
