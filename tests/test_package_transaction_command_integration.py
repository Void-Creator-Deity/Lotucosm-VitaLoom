# -*- coding: utf-8 -*-
"""Qt-free command-registry coverage for package receipt operator recovery."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from builtin.editor_extensions.package_domain.package_transaction_interlock import acquire_package_transaction_interlock
from builtin.editor_extensions.package_domain.package_transactions import (
    PackageTransactionStore,
    ProjectPackageArtifactPort,
)
from core.VitaLoom.commands.registry import reset_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"
PACKAGE_ID = "vitalloom.engine.sr2d"


class PackageTransactionCommandIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="package_transaction_cmd_", dir=str(WORKSPACE)))
        self.project = self.tmp / "project"
        self.project.mkdir()
        (self.project / "project.json").write_text(
            json.dumps(
                {
                    "name": "package-transaction-command",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                    "loom_editor_version": "1.0.0",
                    "required_capabilities": {},
                    "package_state": {"installed": {}, "version_overrides": {}},
                    "disabled_plugins": [],
                }
            ),
            encoding="utf-8",
        )
        self.registry = reset_command_registry()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _failed_install_receipt(self) -> tuple[PackageTransactionStore, dict[str, object], Path]:
        artifact = self.project / "packages" / "sr2d-local"
        artifact.mkdir(parents=True)
        store = PackageTransactionStore(self.project)
        receipt = store.begin(
            "install",
            PACKAGE_ID,
            payload={"source": "local", "path": str(artifact), "version": "1.0.0"},
            local_snapshot={"package_id": PACKAGE_ID, "path": str(artifact), "recorded": True},
        )
        receipt = store.advance(receipt["transaction_id"], "local_applied")
        receipt = store.advance(
            receipt["transaction_id"],
            "failed_recoverable",
            recovery={"action": "retry_project_install"},
        )
        return store, receipt, artifact

    @staticmethod
    def _confirmation(receipt: dict[str, object], action: str) -> str:
        return f"resolve_package_transaction:{receipt['transaction_id']}:{action}"

    def test_inspect_and_list_are_read_only_and_expose_recovery_receipt(self) -> None:
        store, receipt, _ = self._failed_install_receipt()
        inspected = self.registry.run(
            "package.transaction.inspect",
            {"project_path": str(self.project), "transaction_id": receipt["transaction_id"]},
        )
        self.assertTrue(inspected["ok"], inspected)
        self.assertEqual(inspected["result"]["state"], "failed_recoverable")

        listed = self.registry.run("package.transaction.recovery.list", {"project_path": str(self.project)})
        self.assertTrue(listed["ok"], listed)
        self.assertEqual([row["transaction_id"] for row in listed["result"]["records"]], [receipt["transaction_id"]])
        self.assertEqual(store.read(receipt["transaction_id"])["state"], "failed_recoverable")

    def test_retry_install_requires_bound_confirmation_and_matching_action(self) -> None:
        _, receipt, _ = self._failed_install_receipt()
        bad_confirmation = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": receipt["transaction_id"],
                "action": "retry_project_install",
                "operator_confirmation": "yes",
            },
        )
        self.assertFalse(bad_confirmation["ok"])
        self.assertEqual(bad_confirmation["error"]["code"], "package_transaction_confirmation_required")

        mismatch = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": receipt["transaction_id"],
                "action": "retry_local_uninstall",
                "operator_confirmation": self._confirmation(receipt, "retry_local_uninstall"),
            },
        )
        self.assertFalse(mismatch["ok"])
        self.assertEqual(mismatch["error"]["code"], "package_transaction_action_mismatch")

    def test_install_retry_uses_plugin_install_authority_and_completes_receipt(self) -> None:
        store, receipt, artifact = self._failed_install_receipt()
        result = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": receipt["transaction_id"],
                "action": "retry_project_install",
                "operator_confirmation": self._confirmation(receipt, "retry_project_install"),
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertTrue(artifact.is_dir())
        self.assertEqual(store.read(receipt["transaction_id"])["state"], "completed")
        project_data = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        installed = project_data["package_state"]["installed"]
        self.assertEqual(installed[PACKAGE_ID]["path"], str(artifact.resolve()))
        self.assertEqual(installed[PACKAGE_ID]["source"], "local")

    def test_uninstall_retry_only_removes_local_artifact(self) -> None:
        artifact = self.project / "packages" / "remove-me"
        artifact.mkdir(parents=True)
        store = PackageTransactionStore(self.project)
        receipt = store.begin(
            "uninstall",
            PACKAGE_ID,
            local_snapshot={"package_id": PACKAGE_ID, "path": str(artifact), "recorded": True},
        )
        receipt = store.advance(receipt["transaction_id"], "project_applied")
        result = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": receipt["transaction_id"],
                "action": "retry_local_uninstall",
                "operator_confirmation": self._confirmation(receipt, "retry_local_uninstall"),
            },
        )
        self.assertTrue(result["ok"], result)
        self.assertFalse(artifact.exists())
        self.assertEqual(store.read(receipt["transaction_id"])["state"], "completed")
        project_data = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        self.assertNotIn("package_history", project_data)

    def test_recovery_resolve_rejects_held_dedicated_package_interlock(self) -> None:
        store, receipt, artifact = self._failed_install_receipt()
        lease = acquire_package_transaction_interlock(self.project, authority_action="test.command_holder")
        try:
            result = self.registry.run(
                "package.transaction.recovery.resolve",
                {
                    "project_path": str(self.project),
                    "transaction_id": receipt["transaction_id"],
                    "action": "retry_project_install",
                    "operator_confirmation": self._confirmation(receipt, "retry_project_install"),
                },
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "package_transaction_interlock_held")
            self.assertTrue(artifact.is_dir())
            self.assertEqual(store.read(receipt["transaction_id"])["state"], "failed_recoverable")
        finally:
            lease.release()

    def test_prepared_and_terminal_receipts_fail_closed(self) -> None:
        store = PackageTransactionStore(self.project)
        prepared = store.begin("install", PACKAGE_ID)
        prepared_result = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": prepared["transaction_id"],
                "action": "retry_project_install",
                "operator_confirmation": self._confirmation(prepared, "retry_project_install"),
            },
        )
        self.assertFalse(prepared_result["ok"])
        self.assertEqual(prepared_result["error"]["code"], "transaction_state_ambiguous")

        terminal = store.begin("install", PACKAGE_ID)
        terminal = store.advance(terminal["transaction_id"], "local_applied")
        terminal = store.advance(terminal["transaction_id"], "project_applied")
        terminal = store.advance(terminal["transaction_id"], "completed")
        terminal_result = self.registry.run(
            "package.transaction.recovery.resolve",
            {
                "project_path": str(self.project),
                "transaction_id": terminal["transaction_id"],
                "action": "finalize",
                "operator_confirmation": self._confirmation(terminal, "finalize"),
            },
        )
        self.assertFalse(terminal_result["ok"])
        self.assertEqual(terminal_result["error"]["code"], "transaction_not_recoverable")

    def test_artifact_port_rejects_relative_external_and_file_paths(self) -> None:
        port = ProjectPackageArtifactPort(self.project)
        external = self.tmp / "outside-package"
        external.mkdir()
        package_file = self.project / "packages" / "not-a-directory"
        package_file.parent.mkdir()
        package_file.write_text("not a package artifact", encoding="utf-8")

        for unsafe_path in ("packages/relative", str(external.resolve()), str(package_file.resolve())):
            result = port.inspect_local_artifact_path(PACKAGE_ID, unsafe_path)
            self.assertFalse(result["ok"], result)
            self.assertEqual(result["error"], "unsafe_artifact_path")

    def test_inspect_rejects_malformed_receipt_and_workspace_escape(self) -> None:
        receipt_root = self.project / ".vitaloom" / "package_transactions"
        receipt_root.mkdir(parents=True)
        (receipt_root / "malformed.json").write_text("{not-json", encoding="utf-8")
        malformed = self.registry.run(
            "package.transaction.inspect",
            {"project_path": str(self.project), "transaction_id": "malformed"},
        )
        self.assertFalse(malformed["ok"])
        self.assertEqual(malformed["error"]["code"], "package_transaction_malformed")

        external_root = Path(tempfile.mkdtemp(prefix="package_transaction_external_"))
        self.addCleanup(lambda: shutil.rmtree(external_root, ignore_errors=True))
        (external_root / "project.json").write_text("{}", encoding="utf-8")
        escaped = self.registry.run(
            "package.transaction.recovery.list",
            {"project_path": str(external_root)},
        )
        self.assertFalse(escaped["ok"])
        self.assertEqual(escaped["error"]["code"], "path_outside_workspace")
    def test_read_only_list_does_not_create_receipt_metadata_for_clean_project(self) -> None:
        clean = self.tmp / "clean-project"
        clean.mkdir()
        (clean / "project.json").write_text("{}", encoding="utf-8")
        result = self.registry.run("package.transaction.recovery.list", {"project_path": str(clean)})
        self.assertTrue(result["ok"], result)
        self.assertFalse((clean / ".vitaloom").exists())


if __name__ == "__main__":
    unittest.main()