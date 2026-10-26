# -*- coding: utf-8 -*-
"""tools/update_project_lock.py smoke tests."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "update_project_lock.py"


class ProjectLockCliTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_help_smoke(self) -> None:
        proc = self._run("--help")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("project.lock.json", proc.stdout)

    def test_sample_project_lock_check_passes(self) -> None:
        project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        proc = self._run(str(project), "--check")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_write_then_check_temp_project_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "lock-cli",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {
                            "vitalloom.engine.sr2d": ">=1.0.0"
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            write_proc = self._run(str(project), "--write")
            self.assertEqual(write_proc.returncode, 0, write_proc.stdout + write_proc.stderr)
            self.assertTrue((project / "project.lock.json").is_file())
            check_proc = self._run(str(project), "--check")
            self.assertEqual(check_proc.returncode, 0, check_proc.stdout + check_proc.stderr)

            lock = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
            lock["resolved_capabilities"]["vitalloom.engine.sr2d"] = "0.9.0"
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False),
                encoding="utf-8",
            )
            stale_proc = self._run(str(project), "--check")
            self.assertEqual(stale_proc.returncode, 1)

    def test_script_trust_digest_is_recorded_in_project_lock(self) -> None:
        from FrameCore.project_lock import (
            build_project_lock,
            project_script_trust_lock_matches,
        )

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            project_data = {
                "name": "trusted",
                "loom_editor_version": "1.0.0",
                "script_trust": {
                    "sha256_allowlist": [{"path": "scripts/main.py", "sha256": "a" * 64}]
                },
            }
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=ROOT)
            self.assertEqual(lock["script_trust"]["grant_count"], 1)
            self.assertEqual(len(lock["script_trust"]["sha256_allowlist_digest"]), 64)
            self.assertTrue(
                project_script_trust_lock_matches(project, lock, repo_root=ROOT)
            )

            project_data["script_trust"]["sha256_allowlist"][0]["sha256"] = "b" * 64
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            self.assertFalse(
                project_script_trust_lock_matches(project, lock, repo_root=ROOT)
            )

    def test_runtime_rejects_invalid_or_unsupported_lock_without_fallback(self) -> None:
        from FrameCore.project_lock import build_project_lock, resolve_project_runtime

        project_data = {
            "name": "schema-compat",
            "loom_editor_version": "1.0.0",
            "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock_path = project / "project.lock.json"
            lock_path.write_text("{broken", encoding="utf-8")
            invalid = resolve_project_runtime(project, repo_root=ROOT)
            self.assertEqual(invalid.lock_error, "project.lock.json is invalid or unreadable")
            self.assertEqual(invalid.lock_admission_code, "invalid")
            self.assertTrue(invalid.has_blocking_issues)

            lock = build_project_lock(project_data, repo_root=ROOT)
            lock["schema_version"] = 2
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            unsupported = resolve_project_runtime(project, repo_root=ROOT)
            self.assertEqual(
                unsupported.lock_error,
                "unsupported project.lock.json schema_version: 2",
            )
            self.assertEqual(unsupported.lock_admission_code, "unsupported_schema")
            self.assertTrue(unsupported.has_blocking_issues)

    def test_project_backend_selection_is_locked_and_drift_is_blocking(self) -> None:
        from FrameCore.project_lock import build_project_lock, resolve_project_runtime

        project_data = {
            "name": "backend-selection",
            "loom_editor_version": "1.0.0",
            "sr2d_backend": "python",
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=ROOT)
            self.assertEqual(
                lock["runtime_backend_selection"],
                {"sr2d": {"requested": "python"}},
            )
            lock["runtime_backend_selection"]["sr2d"]["requested"] = "cpp"
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False), encoding="utf-8"
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertTrue(resolved.runtime_backend_selection_mismatch)
            self.assertTrue(resolved.has_blocking_issues)
            self.assertIn("runtime_backend_mismatch", resolved.blocking_issue_codes)

    def test_runtime_accepts_legacy_lock_without_schema_field(self) -> None:
        from FrameCore.project_lock import build_project_lock, resolve_project_runtime

        project_data = {
            "name": "legacy-lock",
            "loom_editor_version": "1.0.0",
            "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=ROOT)
            lock.pop("schema_version")
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False), encoding="utf-8"
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertEqual(resolved.lock_error, "")
            self.assertEqual(resolved.lock_admission_code, "legacy")
            self.assertFalse(resolved.has_blocking_issues)

    def test_malformed_script_trust_is_not_silently_ignored(self) -> None:
        from FrameCore.project_lock import build_project_lock

        with self.assertRaisesRegex(ValueError, "script_trust must be an object"):
            build_project_lock(
                {
                    "name": "malformed-trust",
                    "loom_editor_version": "1.0.0",
                    "script_trust": [],
                },
                repo_root=ROOT,
            )

    def test_runtime_does_not_fallback_from_locked_product_version(self) -> None:
        from FrameCore.project_lock import build_project_lock, resolve_project_runtime

        project_data = {"name": "version-switch", "loom_editor_version": "1.0.0"}
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            lock = build_project_lock(project_data, repo_root=ROOT)
            lock["resolved_product"]["version"] = "99.0.0"
            (project / "project.lock.json").write_text(
                json.dumps(lock, ensure_ascii=False), encoding="utf-8"
            )
            resolved = resolve_project_runtime(project, repo_root=ROOT)
            self.assertTrue(resolved.product_version_missing)
            self.assertEqual(resolved.product_version, "99.0.0")
            self.assertTrue(resolved.has_blocking_issues)
            self.assertEqual(resolved.lock_admission_code, "version_missing")

    def test_lock_cli_diagnostics_distinguish_states(self) -> None:
        from tools.update_project_lock import diagnose_lock
        from FrameCore.project_lock import build_project_lock

        project_data = {"name": "diagnostics", "loom_editor_version": "1.0.0"}
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(project_data, ensure_ascii=False), encoding="utf-8"
            )
            expected = build_project_lock(project_data, repo_root=ROOT)
            self.assertEqual(diagnose_lock(project, expected)["code"], "missing")

            lock_path = project / "project.lock.json"
            lock_path.write_text("{broken", encoding="utf-8")
            self.assertEqual(diagnose_lock(project, expected)["code"], "invalid")

            lock_path.write_text(json.dumps(expected), encoding="utf-8")
            self.assertEqual(diagnose_lock(project, expected)["code"], "ok")
            legacy = dict(expected)
            legacy.pop("schema_version")
            lock_path.write_text(json.dumps(legacy), encoding="utf-8")
            self.assertEqual(diagnose_lock(project, expected)["code"], "legacy")

            stale = dict(expected)
            stale["resolved_product"] = dict(expected["resolved_product"])
            stale["resolved_product"]["version"] = "99.0.0"
            lock_path.write_text(json.dumps(stale), encoding="utf-8")
            self.assertEqual(diagnose_lock(project, expected)["code"], "stale")

            unsupported = dict(expected)
            unsupported["schema_version"] = 2
            lock_path.write_text(json.dumps(unsupported), encoding="utf-8")
            self.assertEqual(diagnose_lock(project, expected)["code"], "unsupported_schema")


if __name__ == "__main__":
    unittest.main()
