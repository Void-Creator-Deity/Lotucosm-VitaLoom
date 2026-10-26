# -*- coding: utf-8
"""export_player 工具冒烟。"""
from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ExportPlayerSmokeTests(unittest.TestCase):
    def test_export_creates_launch_scripts_and_runtime(self) -> None:
        from tools.export_player import export_project

        repo = Path(__file__).resolve().parents[1]
        src = repo / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        if not (src / "project.json").is_file():
            self.skipTest("示范工程不存在")

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "proj"
            shutil.copytree(src, work)
            out = export_project(work, repo_root=repo)
            self.assertTrue((out / "launch.bat").is_file())
            self.assertTrue((out / "player_main.py").is_file())
            self.assertTrue((out / "project" / "project.json").is_file())
            self.assertTrue((out / "project" / "project.lock.json").is_file())
            runtime = out / "runtime"
            self.assertTrue(runtime.is_dir())
            self.assertTrue((runtime / "main.py").is_file())
            self.assertTrue((runtime / "player.py").is_file())
            self.assertTrue((runtime / "builtin" / "package_index.json").is_file())
            self.assertTrue((runtime / "core" / "Lotucosm").exists() or (runtime / "core").exists())
            from core.VitaLoom.player.player_shell import validate_player_project_runtime

            resolved = validate_player_project_runtime(str(runtime), str(out / "project"))
            self.assertEqual(resolved.product_id, "lotucosm-vitaloom")
            self.assertFalse(resolved.product_version_missing)
            self.assertFalse(resolved.missing_capabilities)
            meta = json.loads((out / "export_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("runtime_packages", meta)
            self.assertTrue(len(meta.get("runtime_packages", [])) >= 1)
            self.assertEqual(meta["suite"]["id"], "lotucosm.vitaloom.suite")
            self.assertEqual(meta["product"]["id"], "lotucosm-vitaloom")
            self.assertEqual(meta["product"]["lock_status"], "已锁定")
            self.assertEqual(meta["lock"]["source_admission"], "current")
            self.assertEqual(meta["lock"]["runtime_status"], "已锁定")
            self.assertEqual(meta["lock"]["runtime_admission"], "current")
            self.assertIn("resolved_capabilities", meta)
            proc = subprocess.run(
                [sys.executable, str(out / "player_main.py"), "--help"],
                cwd=str(out),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("usage:", proc.stdout)
            smoke = subprocess.run(
                [sys.executable, str(out / "player_main.py"), "--smoke"],
                cwd=str(out),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertIn("Player smoke OK:", smoke.stdout)

    def test_export_rejects_unsatisfied_capability_constraint(self) -> None:
        from tools.export_player import export_project

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "bad_export"
            project.mkdir()
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "bad-export",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=9.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "not exportable"):
                export_project(project, repo_root=repo)

    def test_export_rejects_stale_script_trust_lock(self) -> None:
        from tools.export_player import export_project
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "trusted_export"
            project.mkdir()
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "trusted-export",
                "loom_editor_version": "1.0.0",
                "script_trust": {
                    "sha256_allowlist": [{"path": "scripts/main.py", "sha256": digest}]
                },
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=repo)
            lock["script_trust"]["sha256_allowlist_digest"] = "0" * 64
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False), encoding="utf-8"
            )
            previous_export = project / "dist" / "export" / "trusted-export"
            previous_export.mkdir(parents=True)
            marker = previous_export / "preserve.txt"
            marker.write_text("existing export", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "script trust digest is stale"):
                export_project(project, repo_root=repo)
            self.assertTrue(marker.is_file())

    def test_export_preserves_current_script_trust_lock(self) -> None:
        from tools.export_player import export_project
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "trusted_export"
            project.mkdir()
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "trusted-export",
                "loom_editor_version": "1.0.0",
                "script_trust": {
                    "sha256_allowlist": [{"path": "scripts/main.py", "sha256": digest}]
                },
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            (project / "project.lock.json").write_text(
                json.dumps(build_project_lock(project_data, repo_root=repo), ensure_ascii=False),
                encoding="utf-8",
            )
            out = export_project(project, repo_root=repo)
            exported_data = json.loads(
                (out / "project" / "project.json").read_text(encoding="utf-8")
            )
            exported_lock = json.loads(
                (out / "project" / "project.lock.json").read_text(encoding="utf-8")
            )
            self.assertEqual(exported_data["script_trust"], project_data["script_trust"])
            self.assertEqual(exported_lock["script_trust"], build_project_lock(project_data, repo_root=repo)["script_trust"])

    def test_export_rejects_changed_trusted_source(self) -> None:
        from tools.export_player import export_project
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "changed_export"
            project.mkdir()
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "changed-export",
                "loom_editor_version": "1.0.0",
                "script_trust": {
                    "sha256_allowlist": [{"path": "scripts/main.py", "sha256": digest}]
                },
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            (project / "project.lock.json").write_text(
                json.dumps(build_project_lock(project_data, repo_root=repo), ensure_ascii=False),
                encoding="utf-8",
            )
            script.write_text("VALUE = 2\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source validation failed"):
                export_project(project, repo_root=repo)

    def test_export_player_cli_smoke(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        src = repo / "workspace" / "projects" / "samples" / "织机教程-迷你Roguelike"
        if not (src / "project.json").is_file():
            self.skipTest("示范工程不存在")
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "tutorial"
            shutil.copytree(src, work)
            proc = subprocess.run(
                [sys.executable, str(repo / "tools" / "export_player.py"), str(work)],
                cwd=str(repo),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("导出完成:", proc.stdout)


if __name__ == "__main__":
    unittest.main()
