from __future__ import annotations

from pathlib import Path

import pytest

from builtin.editor_extensions.package_domain.package_transactions import (
    PackageTransactionError,
    PackageTransactionStore,
)
from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations
from builtin.editor_extensions.package_services import PackageOperationService


class TransactionOperationService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.install_result: dict[str, object] = {
            "ok": True,
            "install_path": str(project_root / "packages" / "pkg.alpha" / "1.0.0"),
            "source": "official",
            "version": "1.0.0",
        }
        self.snapshot: dict[str, object] = {
            "ok": True,
            "package_id": "pkg.alpha",
            "path": str(project_root / "packages" / "pkg.alpha" / "1.0.0"),
            "recorded": True,
            "exists": True,
            "artifact_present": True,
        }
        self.remove_result: dict[str, object] = {
            "ok": True,
            "removed_path": self.snapshot["path"],
            "was_installed": True,
        }
        self.install_calls: list[tuple[object, ...]] = []
        self.remove_calls: list[dict[str, object]] = []

    def install_package(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.install_calls.append((args, kwargs))
        target = Path(str(self.install_result["install_path"]))
        if self.install_result.get("ok"):
            target.mkdir(parents=True, exist_ok=True)
        return dict(self.install_result)

    def capture_local_artifact(self, package_id: str) -> dict[str, object]:
        assert package_id == "pkg.alpha"
        return dict(self.snapshot)

    def inspect_local_artifact_path(self, package_id: str, artifact_path: str) -> dict[str, object]:
        assert package_id == "pkg.alpha"
        path = Path(artifact_path)
        return {"ok": True, "package_id": package_id, "path": str(path), "exists": path.is_dir()}

    def remove_local_artifact(self, snapshot: dict[str, object]) -> dict[str, object]:
        self.remove_calls.append(dict(snapshot))
        result = dict(self.remove_result)
        if result.get("ok"):
            path = Path(str(snapshot.get("path", "")))
            if path.exists():
                path.rmdir()
                parent = path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
        return result


def test_install_project_command_failure_creates_recoverable_receipt_and_retry_records_same_artifact(
    tmp_path: Path,
) -> None:
    service = TransactionOperationService(tmp_path)
    store = PackageTransactionStore(tmp_path)
    commands: list[tuple[str, str, object]] = []

    def rejected(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        commands.append((name, package_id, payload))
        return {"ok": False, "error": "project_write_rejected"}

    package = {"id": "pkg.alpha", "source": "official", "version": "1.0.0"}
    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=rejected,
        downloader=None,
        mode="warn",
        transaction_store=store,
    )

    assert not result["ok"]
    assert result["transaction_state"] == "failed_recoverable"
    assert result["recovery"]["action"] == "retry_project_install"
    receipt = store.read(result["transaction_id"])
    assert receipt["payload"]["path"] == str(tmp_path / "packages" / "pkg.alpha" / "1.0.0")
    assert store.list_recoverable()["records"][0]["transaction_id"] == result["transaction_id"]

    def accepted(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        commands.append((name, package_id, payload))
        return {"ok": True}

    recovered = PackageProjectOperations.recover_transaction(
        result["transaction_id"],
        transaction_store=store,
        operation_service=service,
        run_project_command=accepted,
    )

    assert recovered["ok"]
    assert recovered["transaction_state"] == "completed"
    assert commands[-1] == (
        "plugin.install",
        "pkg.alpha",
        {"source": "official", "path": str(tmp_path / "packages" / "pkg.alpha" / "1.0.0"), "version": "1.0.0"},
    )
    assert store.list_recoverable()["records"] == []


def test_uninstall_preserves_pre_command_snapshot_and_recovers_only_local_cleanup(tmp_path: Path) -> None:
    service = TransactionOperationService(tmp_path)
    artifact = Path(str(service.snapshot["path"]))
    artifact.mkdir(parents=True)
    store = PackageTransactionStore(tmp_path)
    command_calls: list[tuple[str, str, object]] = []
    service.remove_result = {"ok": False, "error": "permission_denied"}

    def accepted(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        command_calls.append((name, package_id, payload))
        return {"ok": True}

    result = PackageProjectOperations.uninstall_package(
        "pkg.alpha",
        operation_service=service,
        run_project_command=accepted,
        transaction_store=store,
    )

    assert not result["ok"]
    assert result["transaction_state"] == "failed_recoverable"
    assert result["recovery"]["action"] == "retry_local_uninstall"
    assert service.remove_calls == [service.snapshot]
    assert command_calls == [("plugin.uninstall", "pkg.alpha", None)]
    assert artifact.is_dir()

    service.remove_result = {"ok": True, "removed_path": str(artifact), "was_installed": True}
    recovered = PackageProjectOperations.recover_transaction(
        result["transaction_id"],
        transaction_store=store,
        operation_service=service,
        run_project_command=lambda *_args: pytest.fail("uninstall recovery must not re-run project command"),
    )

    assert recovered["ok"]
    assert recovered["transaction_state"] == "completed"
    assert not artifact.exists()
    assert command_calls == [("plugin.uninstall", "pkg.alpha", None)]


def test_receipt_store_rejects_path_escape_and_reports_malformed_receipt(tmp_path: Path) -> None:
    store = PackageTransactionStore(tmp_path)
    receipt = store.begin("install", "pkg.alpha")

    with pytest.raises(PackageTransactionError) as escaped:
        store.read("../outside")
    assert escaped.value.code == "package_transaction_invalid_id"

    receipt_path = store.receipt_directory / f"{receipt['transaction_id']}.json"
    receipt_path.write_text("{}", encoding="utf-8")
    with pytest.raises(PackageTransactionError) as malformed:
        store.inspect(receipt["transaction_id"])
    assert malformed.value.code == "package_transaction_malformed"
    report = store.list_recoverable()
    assert not report["ok"]
    assert report["malformed"] == [{"path": str(receipt_path), "error": "package_transaction_malformed"}]


class ProjectManagerStub:
    def __init__(self, project_root: Path, config: dict[str, object]) -> None:
        self.project_root = project_root
        self.config = config

    def get_current_project_path(self) -> str:
        return str(self.project_root)

    def get_current_project_config(self) -> dict[str, object]:
        return self.config

    def update_project_config_fields(self, fields: dict[str, object]) -> bool:
        self.config.update(fields)
        return True


def test_real_operation_service_removes_captured_artifact_after_project_state_is_already_gone(tmp_path: Path) -> None:
    artifact = tmp_path / "packages" / "pkg.alpha" / "1.0.0"
    artifact.mkdir(parents=True)
    manager = ProjectManagerStub(
        tmp_path,
        {
            "package_state": {
                "installed": {"pkg.alpha": {"path": str(artifact), "version": "1.0.0"}},
                "version_overrides": {},
            }
        },
    )
    service = PackageOperationService(manager)
    snapshot = service.capture_local_artifact("pkg.alpha")
    assert snapshot["ok"] and snapshot["recorded"] and snapshot["exists"]

    manager.config["package_state"] = {"installed": {}, "version_overrides": {}}
    removal = service.remove_local_artifact(snapshot)

    assert removal["ok"]
    assert removal["removed_path"] == str(artifact)
    assert not artifact.exists()


def test_real_operation_service_rejects_outside_artifact_snapshot(tmp_path: Path) -> None:
    outside = tmp_path.parent / "not-a-package"
    outside.mkdir(exist_ok=True)
    manager = ProjectManagerStub(tmp_path, {"package_state": {"installed": {}}})
    service = PackageOperationService(manager)

    result = service.remove_local_artifact(
        {"package_id": "pkg.alpha", "path": str(outside), "recorded": True}
    )

    assert not result["ok"]
    assert result["error"] == "unsafe_artifact_path"
    assert outside.exists()


def test_install_recovery_fails_closed_when_receipt_artifact_disappeared(tmp_path: Path) -> None:
    service = TransactionOperationService(tmp_path)
    store = PackageTransactionStore(tmp_path)
    package = {"id": "pkg.alpha", "source": "official", "version": "1.0.0"}
    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=lambda *_args: {"ok": False},
        downloader=None,
        mode="warn",
        transaction_store=store,
    )
    artifact = Path(str(service.install_result["install_path"]))
    artifact.rmdir()
    calls: list[object] = []

    recovered = PackageProjectOperations.recover_transaction(
        result["transaction_id"],
        transaction_store=store,
        operation_service=service,
        run_project_command=lambda *args: calls.append(args) or {"ok": True},
    )

    assert not recovered["ok"]
    assert recovered["error"] == "artifact_missing"
    assert recovered["recovery"]["action"] == "manual_review"
    assert calls == []


def test_completed_receipt_cannot_replay_project_or_local_effects(tmp_path: Path) -> None:
    service = TransactionOperationService(tmp_path)
    store = PackageTransactionStore(tmp_path)
    package = {"id": "pkg.alpha", "source": "official", "version": "1.0.0"}
    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=lambda *_args: {"ok": True},
        downloader=None,
        mode="warn",
        transaction_store=store,
    )
    calls: list[object] = []

    replay = PackageProjectOperations.recover_transaction(
        result["transaction_id"],
        transaction_store=store,
        operation_service=service,
        run_project_command=lambda *args: calls.append(args) or {"ok": True},
    )

    assert result["ok"]
    assert not replay["ok"]
    assert replay["error"] == "transaction_not_recoverable"
    assert calls == []


def test_manifest_artifact_alignment_uses_same_durable_install_receipt(tmp_path: Path) -> None:
    service = TransactionOperationService(tmp_path)
    store = PackageTransactionStore(tmp_path)
    package = {
        "id": "pkg.alpha",
        "status": "official",
        "source": "official",
        "version": "1.0.0",
        "artifact": {"type": "file", "path": "alpha.zip"},
    }
    calls: list[tuple[str, str, object]] = []

    result = PackageProjectOperations.align_manifest_packages(
        ["pkg.alpha"],
        [package],
        get_enabled_ids=set,
        operation_service=service,
        run_project_command=lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": False},
        downloader=None,
        mode="warn",
        transaction_store=store,
    )

    assert not result["ok"]
    assert result["unresolved"] == [{"package_id": "pkg.alpha", "reason": "project_install_failed"}]
    recovery = store.list_recoverable()["records"]
    assert recovery[0]["action"] == "install"
    assert recovery[0]["recovery"]["action"] == "retry_project_install"
    assert calls == [("plugin.install", "pkg.alpha", {"source": "official", "path": str(tmp_path / "packages" / "pkg.alpha" / "1.0.0"), "version": "1.0.0"})]


def test_prepared_receipt_is_listed_but_fails_closed_to_manual_review(tmp_path: Path) -> None:
    store = PackageTransactionStore(tmp_path)
    receipt = store.begin("install", "pkg.alpha")

    listed = store.list_recoverable()
    result = PackageProjectOperations.recover_transaction(
        receipt["transaction_id"],
        transaction_store=store,
        operation_service=TransactionOperationService(tmp_path),
        run_project_command=lambda *_args: pytest.fail("ambiguous prepared receipt must not invoke command"),
    )

    assert listed["records"] == [
        {
            "transaction_id": receipt["transaction_id"],
            "action": "install",
            "package_id": "pkg.alpha",
            "state": "prepared",
            "recovery": {},
        }
    ]
    assert not result["ok"]
    assert result["error"] == "transaction_state_ambiguous"
    assert result["recovery"]["action"] == "manual_review"


def test_domain_uninstall_with_real_service_uses_snapshot_before_command_clears_package_state(tmp_path: Path) -> None:
    artifact = tmp_path / "packages" / "pkg.alpha" / "1.0.0"
    artifact.mkdir(parents=True)
    manager = ProjectManagerStub(
        tmp_path,
        {
            "package_state": {
                "installed": {"pkg.alpha": {"path": str(artifact), "version": "1.0.0"}},
                "version_overrides": {},
            }
        },
    )
    service = PackageOperationService(manager)

    def project_uninstall(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        assert (name, package_id, payload) == ("plugin.uninstall", "pkg.alpha", None)
        manager.config["package_state"] = {"installed": {}, "version_overrides": {}}
        return {"ok": True}

    result = PackageProjectOperations.uninstall_package(
        "pkg.alpha", operation_service=service, run_project_command=project_uninstall
    )

    assert result["ok"]
    assert result["transaction_id"]
    assert result["transaction_state"] == "completed"
    assert result["operation"]["removed_path"] == str(artifact)
    assert not artifact.exists()
    assert PackageTransactionStore(tmp_path).list_recoverable()["records"] == []


def test_domain_auto_creates_project_receipt_when_operation_service_has_active_project(tmp_path: Path) -> None:
    service = TransactionOperationService(tmp_path)
    service.project_manager = ProjectManagerStub(tmp_path, {"package_state": {"installed": {}}})
    package = {"id": "pkg.alpha", "source": "official", "version": "1.0.0"}

    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=lambda *_args: {"ok": False},
        downloader=None,
        mode="warn",
    )

    assert not result["ok"]
    assert result["transaction_id"]
    assert PackageTransactionStore(tmp_path).read(result["transaction_id"])["state"] == "failed_recoverable"
