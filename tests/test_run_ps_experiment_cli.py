# -*- coding: utf-8
"""run_ps_experiment.py CLI 报告与退出码。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RunPsExperimentCliTests(unittest.TestCase):
    def test_help_smoke(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "run_ps_experiment.py"), "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("--project", proc.stdout)

    def test_junit_and_report_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            junit = Path(tmp) / "out.xml"
            report = Path(tmp) / "out.json"
            cmd = [
                sys.executable,
                str(ROOT / "tools" / "run_ps_experiment.py"),
                "--ticks",
                "15",
                "--seed",
                "1",
                "--no-export",
                "--junit",
                str(junit),
                "--report-json",
                str(report),
            ]
            env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
            proc = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(junit.is_file())
            self.assertIn("testsuite", junit.read_text(encoding="utf-8"))
            self.assertTrue(report.is_file())
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertIn("summary", payload)


if __name__ == "__main__":
    unittest.main()
