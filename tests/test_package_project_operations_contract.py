"""Qt-free contract for package project-command orchestration."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations


class FakeOperationService:
    def __init__(self) -> None:
        self.install_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.uninstall_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.install_result: dict[str, object] = {
            "ok": True,
            "source": "builtin",
            "install_path": "",
            "version": "1.0.0",
        }
        self.uninstall_result: dict[str, object] = {"ok": True}

    def install_package(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.install_calls.append((args, kwargs))
        return dict(self.install_result)

    def uninstall_package(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.uninstall_calls.append((args, kwargs))
        return dict(self.uninstall_result)


def test_enable_requires_every_project_command_to_succeed() -> None:
    def command(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        return {"ok": package_id != "pkg.blocked"}

    result = PackageProjectOperations.enable_packages(["pkg.alpha", "pkg.blocked"], command)

    assert not result["ok"]
    assert result["changed"]
    assert result["succeeded_ids"] == ["pkg.alpha"]
    assert result["failed_ids"] == ["pkg.blocked"]


def test_install_uses_operation_then_project_command_without_double_state_write() -> None:
    service = FakeOperationService()
    calls: list[tuple[str, str, object]] = []

    def command(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        calls.append((name, package_id, payload))
        return {"ok": True}

    package = {"id": "pkg.alpha", "source": "builtin", "version": "1.0.0"}
    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=command,
        downloader=None,
        mode="warn",
    )

    assert result["ok"]
    assert service.install_calls[0][1]["record_project_state"] is False
    assert calls == [("plugin.install", "pkg.alpha", {"source": "builtin", "path": "", "version": "1.0.0"})]


def test_uninstall_tolerates_absent_local_artifact_after_project_command() -> None:
    service = FakeOperationService()
    service.uninstall_result = {"ok": False, "error": "not_installed"}
    calls: list[tuple[str, str, object]] = []

    def command(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        calls.append((name, package_id, payload))
        return {"ok": True}

    result = PackageProjectOperations.uninstall_package(
        "pkg.alpha", operation_service=service, run_project_command=command
    )

    assert result["ok"]
    assert service.uninstall_calls[0][1]["record_project_state"] is False
    assert calls == [("plugin.uninstall", "pkg.alpha", None)]


def test_uninstall_does_not_remove_local_artifact_when_project_command_fails() -> None:
    service = FakeOperationService()

    result = PackageProjectOperations.uninstall_package(
        "pkg.alpha",
        operation_service=service,
        run_project_command=lambda *_args: {"ok": False, "error": "project_rejected"},
    )

    assert not result["ok"]
    assert result["operation_skipped"]
    assert service.uninstall_calls == []


def test_manifest_alignment_records_artifact_before_enabling_package() -> None:
    service = FakeOperationService()
    calls: list[tuple[str, str, object]] = []

    def command(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        calls.append((name, package_id, payload))
        return {"ok": True}

    package = {
        "id": "pkg.alpha",
        "status": "official",
        "artifact": {"type": "file", "path": "alpha.zip"},
    }
    result = PackageProjectOperations.align_manifest_packages(
        ["pkg.alpha"],
        [package],
        get_enabled_ids=set,
        operation_service=service,
        run_project_command=command,
        downloader=None,
        mode="warn",
    )

    assert result["ok"]
    assert result["resolved_ids"] == ["pkg.alpha"]
    assert service.install_calls[0][1]["record_project_state"] is False
    assert calls == [
        ("plugin.install", "pkg.alpha", {"source": "builtin", "path": "", "version": "1.0.0"}),
        ("plugin.enable", "pkg.alpha", None),
    ]


def test_manifest_alignment_does_not_enable_unknown_or_failed_artifact_packages() -> None:
    service = FakeOperationService()
    service.install_result = {"ok": False, "error": "download_failed"}
    calls: list[tuple[str, str, object]] = []
    package = {
        "id": "pkg.alpha",
        "status": "official",
        "artifact": {"type": "file", "path": "alpha.zip"},
    }

    result = PackageProjectOperations.align_manifest_packages(
        ["pkg.alpha", "pkg.unknown"],
        [package],
        get_enabled_ids=set,
        operation_service=service,
        run_project_command=lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": True},
        downloader=None,
        mode="warn",
    )

    assert not result["ok"]
    assert result["resolved_ids"] == []
    assert {item["reason"] for item in result["unresolved"]} == {"artifact_install_failed", "package_not_in_catalog"}
    assert calls == []


def test_manifest_alignment_rejects_partial_enable_success() -> None:
    service = FakeOperationService()

    def command(name: str, package_id: str, payload: object = None) -> dict[str, object]:
        return {"ok": package_id == "pkg.alpha"}

    result = PackageProjectOperations.align_manifest_packages(
        ["pkg.alpha", "pkg.beta"],
        [{"id": "pkg.alpha", "status": "builtin"}, {"id": "pkg.beta", "status": "builtin"}],
        get_enabled_ids=set,
        operation_service=service,
        run_project_command=command,
        downloader=None,
        mode="warn",
    )

    assert not result["ok"]
    assert result["resolved_ids"] == ["pkg.alpha"]
    assert result["unresolved"] == [{"package_id": "pkg.beta", "reason": "project_enable_failed"}]