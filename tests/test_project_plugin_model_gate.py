# -*- coding: utf-8 -*-
"""Project plugin model guard."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectPluginModelGateTests(unittest.TestCase):
    def test_project_plugin_model_gate_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "check_project_plugin_model.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("project plugin model OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
