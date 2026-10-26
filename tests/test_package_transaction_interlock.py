# -*- coding: utf-8 -*-
"""Qt-free package transaction interlock proof, including a real second process."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from builtin.editor_extensions.package_domain.package_transaction_interlock import (
    PackageTransactionInterlockError,
    acquire_package_transaction_interlock,
    inspect_package_transaction_interlock,
)
from builtin.editor_extensions.package_domain.package_transactions import PackageTransactionStore
from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations


PACKAGE = {"id": "pkg.interlock", "source": "local", "version": "1.0.0"}


class _ProjectManager:
    def __init__(self, project: Path) -> None:
        self._project = project

    def get_current_project_path(self) -> str:
        return str(self._project)


class _OperationService:
    def __init__(self, project: Path, *, fail_if_called: bool = False) -> None:
        self.project_manager = _ProjectManager(project)
        self.project = project
        self.fail_if_called = fail_if_called
        self.calls: list[str] = []

    def install_package(self, package_id: str, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.calls.append("install")
        if self.fail_if_called:
            raise AssertionError("local install must not run while package interlock is held")
        artifact = self.project / "packages" / package_id
        artifact.mkdir(parents=True, exist_ok=True)
        return {
            "ok": True,
            "install_path": str(artifact),
            "source": "local",
            "version": "1.0.0",
        }

    def capture_local_artifact(self, package_id: str) -> dict[str, Any]:
        self.calls.append("snapshot")
        if self.fail_if_called:
            raise AssertionError("local snapshot must not run while package interlock is held")
        return {"ok": True, "package_id": package_id, "path": "", "recorded": False, "exists": False}

    def remove_local_artifact(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.calls.append("remove")
        if self.fail_if_called:
            raise AssertionError("local removal must not run while package interlock is held")
        return {"ok": True, "removed_path": str(snapshot.get("path", "")), "already_absent": True}


class PackageTransactionInterlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="package_interlock_"))
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "project.json").write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def _tree_bytes(project: Path) -> dict[str, bytes]:
        return {
            str(path.relative_to(project)): path.read_bytes()
            for path in sorted(project.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_inspect_is_read_only_and_acquire_release_is_owned(self) -> None:
        self.assertFalse((self.project / ".vitaloom").exists())
        absent = inspect_package_transaction_interlock(self.project)
        self.assertEqual(absent["status"], "absent")
        self.assertFalse((self.project / ".vitaloom").exists())

        lease = acquire_package_transaction_interlock(self.project, authority_action="test.owner")
        self.assertEqual(lease.inspection["record"]["authority_action"], "test.owner")
        self.assertEqual(inspect_package_transaction_interlock(self.project)["status"], "valid")
        lease.release()
        self.assertEqual(inspect_package_transaction_interlock(self.project)["status"], "absent")

    def test_existing_and_replaced_lock_fail_closed(self) -> None:
        lease = acquire_package_transaction_interlock(self.project, authority_action="test.owner")
        try:
            with self.assertRaises(PackageTransactionInterlockError) as held:
                acquire_package_transaction_interlock(self.project, authority_action="test.second")
            self.assertEqual(held.exception.code, "package_transaction_interlock_held")

            lock_path = self.project / ".vitaloom" / "package_transaction_interlock.json"
            replacement = {
                "schema_version": 1,
                "project_path": str(self.project.resolve()),
                "owner_nonce": "0" * 64,
                "pid": 1,
                "created_at_utc": "2026-07-18T00:00:00Z",
                "authority_action": "foreign.owner",
            }
            lock_path.write_text(json.dumps(replacement, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(PackageTransactionInterlockError) as refused:
                lease.release()
            self.assertEqual(refused.exception.code, "package_transaction_interlock_release_refused")
            self.assertEqual(json.loads(lock_path.read_text(encoding="utf-8")), replacement)
        finally:
            # The replacement is deliberate test evidence; leave teardown to remove it.
            pass

    def test_malformed_existing_lock_is_retained_and_fails_closed(self) -> None:
        lock_path = self.project / ".vitaloom" / "package_transaction_interlock.json"
        lock_path.parent.mkdir()
        lock_path.write_text("{malformed", encoding="utf-8")
        before = lock_path.read_bytes()
        with self.assertRaises(PackageTransactionInterlockError) as held:
            acquire_package_transaction_interlock(self.project, authority_action="test.malformed")
        self.assertEqual(held.exception.code, "package_transaction_interlock_held")
        self.assertEqual(inspect_package_transaction_interlock(self.project)["status"], "malformed")
        self.assertEqual(lock_path.read_bytes(), before)

    def test_symlink_metadata_root_is_rejected_without_following_it(self) -> None:
        external = self.root / "external-metadata"
        external.mkdir()
        metadata = self.project / ".vitaloom"
        try:
            metadata.symlink_to(external, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {type(exc).__name__}")
        with self.assertRaises(PackageTransactionInterlockError) as unsafe:
            acquire_package_transaction_interlock(self.project, authority_action="test.symlink")
        self.assertEqual(unsafe.exception.code, "package_transaction_interlock_path_unsafe")
        self.assertEqual(list(external.iterdir()), [])

    def test_domain_mutations_are_refused_before_any_package_write(self) -> None:
        service = _OperationService(self.project, fail_if_called=True)
        store = PackageTransactionStore(self.project)
        receipt = store.begin("install", PACKAGE["id"])
        receipt = store.advance(receipt["transaction_id"], "local_applied")
        receipt = store.advance(
            receipt["transaction_id"],
            "failed_recoverable",
            recovery={"action": "retry_project_install"},
        )

        lease = acquire_package_transaction_interlock(self.project, authority_action="test.holder")
        try:
            before = self._tree_bytes(self.project)
            install = PackageProjectOperations.install_package(
                PACKAGE,
                [PACKAGE],
                set(),
                operation_service=service,
                run_project_command=lambda *_args: {"ok": True},
                downloader=None,
                mode="warn",
            )
            uninstall = PackageProjectOperations.uninstall_package(
                PACKAGE["id"],
                operation_service=service,
                run_project_command=lambda *_args: {"ok": True},
            )
            recovery = PackageProjectOperations.recover_transaction(
                receipt["transaction_id"],
                transaction_store=store,
                operation_service=service,
                run_project_command=lambda *_args: {"ok": True},
            )
            for result in (install, uninstall, recovery):
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"], "package_transaction_interlock_held")
            self.assertEqual(service.calls, [])
            self.assertEqual(before, self._tree_bytes(self.project))
        finally:
            lease.release()

    def test_successful_install_releases_the_package_interlock(self) -> None:
        service = _OperationService(self.project)
        result = PackageProjectOperations.install_package(
            PACKAGE,
            [PACKAGE],
            set(),
            operation_service=service,
            run_project_command=lambda *_args: {"ok": True},
            downloader=None,
            mode="warn",
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(inspect_package_transaction_interlock(self.project)["status"], "absent")
        self.assertEqual(service.calls, ["install"])

    def test_real_second_process_package_install_is_refused_with_zero_project_writes(self) -> None:
        lease = acquire_package_transaction_interlock(self.project, authority_action="test.parent_holder")
        try:
            before = self._tree_bytes(self.project)
            script = r'''
import json
import sys
from pathlib import Path
from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations

class Manager:
    def __init__(self, project): self.project = project
    def get_current_project_path(self): return str(self.project)

class Service:
    def __init__(self, project): self.project_manager = Manager(project)
    def install_package(self, *_args, **_kwargs):
        raise RuntimeError("must not reach local install")

project = Path(sys.argv[1])
result = PackageProjectOperations.install_package(
    {"id": "pkg.child", "source": "local", "version": "1.0.0"},
    [],
    set(),
    operation_service=Service(project),
    run_project_command=lambda *_args: {"ok": True},
    downloader=None,
    mode="warn",
)
print(json.dumps({"ok": result.get("ok"), "error": result.get("error")}, sort_keys=True))
raise SystemExit(0 if result.get("error") == "package_transaction_interlock_held" else 9)
'''
            environment = dict(os.environ)
            environment["PYTHONPATH"] = os.pathsep.join(item for item in sys.path if item)
            completed = subprocess.run(
                [sys.executable, "-c", script, str(self.project)],
                cwd=str(self.root),
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["error"], "package_transaction_interlock_held")
            self.assertEqual(before, self._tree_bytes(self.project))
        finally:
            lease.release()


if __name__ == "__main__":
    unittest.main()