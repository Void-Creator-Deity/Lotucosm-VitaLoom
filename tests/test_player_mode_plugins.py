# -*- coding: utf-8 -*-
"""Player 模式插件激活集。"""
from __future__ import annotations

import os
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PlayerModePluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev = os.environ.get("VITALOOM_PLAYER_MODE")
        os.environ["VITALOOM_PLAYER_MODE"] = "1"

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("VITALOOM_PLAYER_MODE", None)
        else:
            os.environ["VITALOOM_PLAYER_MODE"] = self._prev

    def test_is_player_mode(self) -> None:
        from core.VitaLoom.project.plugin_activation import is_player_mode

        self.assertTrue(is_player_mode())

    def test_collect_player_excludes_editor_docks(self) -> None:
        from core.VitaLoom.project.plugin_activation import collect_player_plugin_ids

        repo = Path(__file__).resolve().parents[1]
        project_data = {
            "required_packages": [
                "vitalloom.editor_essentials",
                "vitalloom.pvaec.simulation",
            ],
            "capabilities": ["sr2d", "pvaec"],
            "disabled_plugins": [],
        }
        active = collect_player_plugin_ids(project_data, repo_root=repo)
        self.assertIn("GameViewportPlugin", active)
        self.assertNotIn("HierarchyPlugin", active)
        self.assertNotIn("PackageManagerPlugin", active)
        self.assertNotIn("PsExperimentPlugin", active)

    def test_validate_player_runtime_accepts_locked_sample_project(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime

        repo = Path(__file__).resolve().parents[1]
        project = repo / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        resolved = validate_player_project_runtime(str(repo), str(project))
        self.assertEqual(resolved.product_id, "lotucosm-vitaloom")
        self.assertFalse(resolved.product_version_missing)
        self.assertFalse(resolved.missing_capabilities)

    def test_validate_player_runtime_rejects_stale_capability_lock(self) -> None:
        from core.VitaLoom.suite.project_lock import build_project_lock
        from core.VitaLoom.player.player_shell import validate_player_project_runtime

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            project_data = {
                "name": "stale-player",
                "loom_editor_version": "1.0.0",
                "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False),
                encoding="utf-8",
            )
            lock = build_project_lock(project_data, repo_root=repo)
            lock["resolved_capabilities"]["vitalloom.engine.sr2d"] = "0.9.0"
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "capability version mismatch"):
                validate_player_project_runtime(str(repo), str(project))

    def test_validate_player_runtime_rejects_unsatisfied_capability_constraint(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "future-player",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=9.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "capability constraint mismatch"):
                validate_player_project_runtime(str(repo), str(project))

    def test_exported_player_requires_project_lock(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "no-lock-export",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=1.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"VITALOOM_EXPORT_ROOT": str(tmp)}):
                with self.assertRaisesRegex(RuntimeError, "missing project.lock.json"):
                    validate_player_project_runtime(str(repo), str(project))

    def test_validate_player_runtime_rejects_stale_script_trust_lock(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "trusted-player",
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
            with self.assertRaisesRegex(RuntimeError, "script trust digest is stale"):
                validate_player_project_runtime(str(repo), str(project))

    def test_validate_player_runtime_accepts_current_script_trust_lock(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "trusted-player",
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
            resolved = validate_player_project_runtime(str(repo), str(project))
            self.assertEqual(resolved.product_id, "lotucosm-vitaloom")

    def test_validate_player_runtime_rejects_changed_trusted_source(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            script = project / "scripts" / "main.py"
            script.parent.mkdir()
            script.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            project_data = {
                "name": "changed-player",
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
                validate_player_project_runtime(str(repo), str(project))

    def test_validate_player_runtime_rejects_unsupported_lock_schema(self) -> None:
        from core.VitaLoom.player.player_shell import validate_player_project_runtime
        from core.VitaLoom.suite.project_lock import build_project_lock

        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            project_data = {
                "name": "unsupported-player-lock",
                "loom_editor_version": "1.0.0",
                "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=repo)
            lock["schema_version"] = 2
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "unsupported project.lock.json schema_version"):
                validate_player_project_runtime(str(repo), str(project))

    def test_player_cli_help_smoke(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, str(repo / "player.py"), "--help"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("--project", proc.stdout)

    def test_player_cli_rejects_invalid_project_before_qt(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(repo / "player.py"), "--project", tmp],
                cwd=str(repo),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("缺少 project.json", proc.stdout)


if __name__ == "__main__":
    unittest.main()
