"""Qt-free manifest-alignment orchestration contract."""
from __future__ import annotations

from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations


class RecordingOperationService:
    def __init__(self) -> None:
        self.install_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.uninstall_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def install_package(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.install_calls.append((args, kwargs))
        return {"ok": True, "source": "official", "install_path": "project/pkg", "version": "1.0.0"}

    def uninstall_package(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.uninstall_calls.append((args, kwargs))
        return {"ok": True}


def test_enable_packages_uses_project_command_authority() -> None:
    calls: list[tuple[str, str, object]] = []

    result = PackageProjectOperations.enable_packages(
        ["vitalloom.pvaec.simulation"],
        lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": True},
    )

    assert result["ok"]
    assert calls == [("plugin.enable", "vitalloom.pvaec.simulation", None)]


def test_align_manifest_installs_artifact_records_project_state_then_enables() -> None:
    service = RecordingOperationService()
    calls: list[tuple[str, str, object]] = []
    package = {
        "id": "vitalloom.pvaec.simulation",
        "status": "official",
        "artifact": {"type": "file", "path": "dummy.zip"},
    }

    result = PackageProjectOperations.align_manifest_packages(
        ["vitalloom.pvaec.simulation"],
        [package],
        get_enabled_ids=set,
        operation_service=service,
        run_project_command=lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": True},
        downloader=None,
        mode="warn",
    )

    assert result["ok"]
    assert service.install_calls[0][1]["record_project_state"] is False
    assert calls == [
        ("plugin.install", "vitalloom.pvaec.simulation", {"source": "official", "path": "project/pkg", "version": "1.0.0"}),
        ("plugin.enable", "vitalloom.pvaec.simulation", None),
    ]


def test_install_records_project_state_through_command() -> None:
    service = RecordingOperationService()
    calls: list[tuple[str, str, object]] = []
    package = {"id": "vitalloom.pvaec.simulation", "version": "1.0.0", "source": "builtin"}

    result = PackageProjectOperations.install_package(
        package,
        [package],
        set(),
        operation_service=service,
        run_project_command=lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": True},
        downloader=None,
        mode="warn",
    )

    assert result["ok"]
    assert service.install_calls[0][1]["record_project_state"] is False
    assert calls == [("plugin.install", "vitalloom.pvaec.simulation", {"source": "official", "path": "project/pkg", "version": "1.0.0"})]


def test_uninstall_records_project_state_before_local_cleanup() -> None:
    service = RecordingOperationService()
    calls: list[tuple[str, str, object]] = []

    result = PackageProjectOperations.uninstall_package(
        "vitalloom.pvaec.simulation",
        operation_service=service,
        run_project_command=lambda name, package_id, payload=None: calls.append((name, package_id, payload)) or {"ok": True},
    )

    assert result["ok"]
    assert calls == [("plugin.uninstall", "vitalloom.pvaec.simulation", None)]
    assert service.uninstall_calls[0][1]["record_project_state"] is False