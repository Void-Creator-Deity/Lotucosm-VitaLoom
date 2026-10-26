# -*- coding: utf-8 -*-
"""GUI boundary guardrails."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CheckGuiBoundariesTests(unittest.TestCase):
    def test_gui_boundaries_pass_for_repository(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_gui_boundaries.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_checker_rejects_qt_in_qt_free_lotucosm_runtime(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "gui_boundary_qt_bad"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "check_gui_boundaries.py"),
                "--scan-root",
                str(fixture),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Qt import in Qt-free Lotucosm runtime", proc.stdout + proc.stderr)

    def test_checker_rejects_pygame_on_main_gui_path(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "check_gui_boundaries.py"),
                "--scan-root",
                str(ROOT / "tests" / "fixtures" / "gui_boundary_bad"),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("pygame import on main GUI path", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
