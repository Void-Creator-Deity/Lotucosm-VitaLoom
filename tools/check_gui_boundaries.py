#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI boundary guardrails.

The editor shell may use PyQt. The main GUI/SR path must not grow new pygame
imports; legacy pygame modules are quarantined outside this scan. The
Lotucosm runtime model is Qt-free; concrete Qt drawing belongs to VitaLoom
Host Adapter modules.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_RUNTIME = (
    ROOT
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


def _runtime_root(scan_root: Path) -> Path:
    bundled = (
        scan_root
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    if bundled.is_dir():
        return bundled
    return scan_root


def _main_gui_files(scan_root: Path) -> list[Path]:
    runtime = _runtime_root(scan_root)
    files: list[Path] = []

    vitalloom = runtime / "core" / "VitaLoom"
    if vitalloom.is_dir():
        files.extend(path for path in vitalloom.rglob("*.py") if path.is_file())

    lotucosm = runtime / "core" / "Lotucosm"
    if lotucosm.is_dir():
        files.extend(path for path in lotucosm.glob("sr_*.py") if path.is_file())
        sr_physics = lotucosm / "sr_physics2d"
        if sr_physics.is_dir():
            files.extend(path for path in sr_physics.rglob("*.py") if path.is_file())

    return sorted({path for path in files if "__pycache__" not in path.parts})


def _qt_import_lines(path: Path) -> list[int]:
    """Return source lines importing concrete Qt bindings."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return [
            i
            for i, line in enumerate(text.splitlines(), 1)
            if "PyQt" in line or "PySide" in line
        ]

    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("PyQt", "PySide")):
                    lines.append(int(getattr(node, "lineno", 0)))
                    break
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(("PyQt", "PySide")):
                lines.append(int(getattr(node, "lineno", 0)))
    return sorted(line for line in lines if line > 0)


def _pygame_import_lines(path: Path) -> list[int]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return [
            i
            for i, line in enumerate(text.splitlines(), 1)
            if line.strip().startswith(("import pygame", "from pygame"))
        ]

    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pygame" or alias.name.startswith("pygame."):
                    lines.append(int(getattr(node, "lineno", 0)))
                    break
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "pygame" or module.startswith("pygame."):
                lines.append(int(getattr(node, "lineno", 0)))
    return sorted(line for line in lines if line > 0)


def check(scan_root: Path) -> list[str]:
    violations: list[str] = []
    for path in _main_gui_files(scan_root):
        for line in _pygame_import_lines(path):
            try:
                rel = path.relative_to(scan_root)
            except ValueError:
                rel = path
            violations.append(f"{rel}:{line}: pygame import on main GUI path")

    # Lotucosm contains the Qt-free engine/runtime model. Do not scan VitaLoom
    # itself here because its docks and viewport backends are intentional Host
    # Adapter code.
    lotucosm = _runtime_root(scan_root) / "core" / "Lotucosm"
    if lotucosm.is_dir():
        for path in sorted(lotucosm.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for line in _qt_import_lines(path):
                try:
                    rel = path.relative_to(scan_root)
                except ValueError:
                    rel = path
                violations.append(f"{rel}:{line}: Qt import in Qt-free Lotucosm runtime")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=ROOT,
        help="repository or fixture root to scan",
    )
    args = parser.parse_args()
    scan_root = args.scan_root.resolve()
    violations = check(scan_root)
    if violations:
        print("GUI boundary violations:")
        for violation in violations[:50]:
            print(violation)
        if len(violations) > 50:
            print(f"... and {len(violations) - 50} more")
        return 1
    print("GUI boundaries OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
