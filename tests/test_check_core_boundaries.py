# -*- coding: utf-8
"""core 边界门禁脚本。"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CheckCoreBoundariesTests(unittest.TestCase):
    def test_core_boundaries_pass(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_core_boundaries.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
