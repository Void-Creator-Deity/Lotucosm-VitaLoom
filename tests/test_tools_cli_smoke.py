# -*- coding: utf-8 -*-
"""常用 tools 入口的子进程 smoke。"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ToolsCliSmokeTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    def test_build_exe_help_smoke(self) -> None:
        proc = self._run("tools/build_exe.py", "--help")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("--console", proc.stdout)

    def test_benchmark_export_closure_smoke(self) -> None:
        proc = self._run("tools/benchmark_engine.py", "--case", "export_closure", "--repeats", "1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["cases"][0]["name"], "asset_export_closure")
        self.assertIn("file_count", data["cases"][0]["last_result"])

    def test_benchmark_asset_reference_transaction_scale_smoke(self) -> None:
        proc = self._run("tools/benchmark_engine.py", "--case", "asset_reference_transaction_scale", "--repeats", "1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        case = data["cases"][0]
        self.assertEqual(case["name"], "asset_reference_transaction_scale_1000")
        result = case["last_result"]
        self.assertEqual(result["rename_reference_edits"], 1)
        self.assertEqual(result["delete_reference_edits"], 0)
        self.assertTrue(result["export_ready_after_redo"])
        self.assertFalse(result["transaction_metadata_in_export"])

    def test_project_asset_generators_live_with_pvaec_project(self) -> None:
        root_tools = {path.name for path in (ROOT / "tools").glob("*.py")}
        self.assertNotIn("generate_sr_audio.py", root_tools)
        self.assertNotIn("regenerate_sr_sprites.py", root_tools)

        pvaec_projects = sorted((ROOT / "workspace" / "projects" / "samples").glob("pvaec-*"))
        self.assertGreaterEqual(len(pvaec_projects), 1)
        for project in pvaec_projects:
            project_tools = project / "tools"
            self.assertTrue((project_tools / "generate_sr_audio.py").is_file(), project.name)
            self.assertTrue((project_tools / "regenerate_sr_sprites.py").is_file(), project.name)

    def test_routine_maintenance_gates_smoke(self) -> None:
        proc = self._run(
            "tools/run_routine_maintenance.py",
            "--skip-tests",
            "--skip-audit",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("core boundaries", proc.stdout)
        self.assertIn("release consistency", proc.stdout)
        self.assertIn("compileall", proc.stdout)
        self.assertIn("main version", proc.stdout)
        self.assertIn("hub smoke", proc.stdout)
        self.assertIn("editor smoke", proc.stdout)
        self.assertIn("player help", proc.stdout)
        self.assertIn("player smoke", proc.stdout)

    def test_worktree_group_audit_smoke(self) -> None:
        proc = self._run("tools/audit_worktree_groups.py")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("groups", data)
        self.assertIn("policy", data)


if __name__ == "__main__":
    unittest.main()
