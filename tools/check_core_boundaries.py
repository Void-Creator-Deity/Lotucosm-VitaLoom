#!/usr/bin/env python3
# -*- coding: utf-8
"""core/ 边界门禁：禁止示范工程路径与脚本名硬编码（见 ADR-0002）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = SUITE_ROOT / "versions" / "1.0.0"
RUNTIME_ROOT = VERSION_ROOT / "runtime"
CORE = RUNTIME_ROOT / "core"
FRAME_CORE = ROOT / "FrameCore"
SUITE_HUB = SUITE_ROOT / "hub"
EXECUTABLE_SCAN_ROOTS = (
    CORE,
    FRAME_CORE,
    RUNTIME_ROOT / "builtin",
    ROOT / "tools",
    ROOT / ".cursor" / "rules",
)
STANDALONE_SCAN_FILES = (
    ROOT / "main.py",
    ROOT / "player.py",
)
SCAN_SUFFIXES = {".py", ".json", ".toml", ".mdc"}

FORBIDDEN = (
    "pvaec-细胞演化",
    "织机教程",
    "sensor_patrol_pvaec",
    "player_rl",
)


def _legacy_flat_project_paths() -> tuple[str, ...]:
    pvaec = "pvaec-" + "细胞演化"
    tutorial = "织机教程-" + "迷你Roguelike"
    return (
        "projects/" + pvaec,
        "projects\\" + pvaec,
        "projects/" + tutorial,
        "projects\\" + tutorial,
    )


def _iter_executable_surface_files() -> list[Path]:
    files: list[Path] = []
    for root in EXECUTABLE_SCAN_ROOTS:
        if root.is_dir():
            files.extend(p for p in root.rglob("*") if p.is_file())
    files.extend(p for p in STANDALONE_SCAN_FILES if p.is_file())
    return [
        p
        for p in files
        if p.suffix in SCAN_SUFFIXES and "__pycache__" not in p.parts
    ]


def main() -> int:
    violations: list[str] = []
    for legacy in (
        ROOT / "core" / "Lotucosm",
        ROOT / "core" / "VitaLoom",
        ROOT / "core" / "api",
        ROOT / "builtin",
        ROOT / "products",
        ROOT / "suite_manifest.json",
    ):
        if legacy.exists():
            violations.append(f"legacy root runtime path exists: {legacy.relative_to(ROOT)}")
    for path in CORE.rglob("*"):
        if not path.is_file() or path.suffix not in (".py", ".md", ".json"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for token in FORBIDDEN:
            if token in text:
                for i, line in enumerate(text.splitlines(), 1):
                    if token in line:
                        violations.append(f"{path.relative_to(ROOT)}:{i}: {token}")
    for path in FRAME_CORE.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.is_relative_to(FRAME_CORE / "plugins"):
            continue
        if path.suffix == ".py":
            forbidden_imports = (
                "core.VitaLoom",
                "core.Lotucosm",
                "builtin",
                "projects",
            )
            for token in forbidden_imports:
                for i, line in enumerate(text.splitlines(), 1):
                    stripped = line.strip()
                    if not (
                        stripped.startswith("import ")
                        or stripped.startswith("from ")
                    ):
                        continue
                    if token in stripped:
                        violations.append(
                            f"{path.relative_to(ROOT)}:{i}: FrameCore import boundary {token}"
                        )
    if SUITE_HUB.is_dir():
        for path in SUITE_HUB.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not (
                    stripped.startswith("import ")
                    or stripped.startswith("from ")
                ):
                    continue
                for token in ("core.VitaLoom", "core.Lotucosm", "builtin"):
                    if token in stripped:
                        violations.append(
                            f"{path.relative_to(ROOT)}:{i}: Suite Hub import boundary {token}"
                        )
    for path in _iter_executable_surface_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for token in _legacy_flat_project_paths():
            if token not in text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if token in line:
                    violations.append(
                        f"{path.relative_to(ROOT)}:{i}: legacy flat project path {token}"
                    )
    if violations:
        print("core boundary violations:")
        for v in violations[:50]:
            print(v)
        if len(violations) > 50:
            print(f"... and {len(violations) - 50} more")
        return 1
    print("core boundaries OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
