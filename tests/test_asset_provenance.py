# -*- coding: utf-8 -*-
"""Release sample assets must have explicit self-owned/generated provenance."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AssetProvenanceTests(unittest.TestCase):
    def test_asset_provenance_gate(self) -> None:
        proc = subprocess.run(
            [sys.executable, "tools/check_asset_provenance.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("asset provenance OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
