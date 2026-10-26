# -*- coding: utf-8 -*-
"""E26 integration proofs for the recursive plugin Host capability lifecycle."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION
from core.VitaLoom.kernel.editor_kernel import (
    EditorKernel,
    EditorKernelInitializationRollbackError,
)


RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _clean_plugin_host_capability():
    services = get_editor_context().services
    services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)
    yield services
    services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)


def test_editor_kernel_publishes_exact_nested_host_and_unpublishes_it(
    _clean_plugin_host_capability,
) -> None:
    services = _clean_plugin_host_capability
    kernel = EditorKernel()
    try:
        assert services.get(PLUGIN_HOST_CONTROL_OBSERVATION) is (
            kernel.plugin_loader.nested_plugin_host
        )
        assert resolve_plugin_host(services) is kernel.plugin_loader.nested_plugin_host
        assert kernel._release_project_world_host_lease() is True
        assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False
        assert kernel._plugin_host_capability_lease is None
    finally:
        kernel._release_project_world_host_lease()
        kernel.deleteLater()


def test_editor_kernel_release_preserves_newer_plugin_host_replacement(
    _clean_plugin_host_capability,
) -> None:
    services = _clean_plugin_host_capability
    kernel = EditorKernel()
    replacement = object()
    try:
        services.register(PLUGIN_HOST_CONTROL_OBSERVATION, replacement)
        assert kernel._release_project_world_host_lease() is True
        assert services.get(PLUGIN_HOST_CONTROL_OBSERVATION) is replacement
        assert kernel._plugin_host_capability_lease is None
    finally:
        kernel._release_project_world_host_lease()
        kernel.deleteLater()


def test_editor_kernel_init_failure_unpublishes_plugin_host(
    monkeypatch: pytest.MonkeyPatch,
    _clean_plugin_host_capability,
) -> None:
    from core.VitaLoom.project import project_world_host_composition

    services = _clean_plugin_host_capability
    monkeypatch.setattr(
        project_world_host_composition,
        "acquire_project_world_host",
        lambda _owner: (_ for _ in ()).throw(RuntimeError("composition failed")),
    )

    with pytest.raises(RuntimeError, match="composition failed"):
        EditorKernel()

    assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False


def test_editor_kernel_init_rollback_logs_project_world_capability_failure_and_is_retryable(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    _clean_plugin_host_capability,
) -> None:
    """Startup failure remains primary while exact Project World ownership is retained."""

    from core.VitaLoom.project import project_world_capabilities
    from core.VitaLoom.simulation import simulation_coordinator

    services = _clean_plugin_host_capability
    captured: list[EditorKernel] = []
    original_release = EditorKernel._release_project_world_host_lease
    original_unregister = project_world_capabilities.unregister_project_world_host_capabilities
    attempts = 0

    def capture_release(kernel: EditorKernel) -> bool:
        captured.append(kernel)
        return original_release(kernel)

    def flaky_unregister(actual_services: object, capabilities: dict[str, object]):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Project World capability rollback failed")
        return original_unregister(actual_services, capabilities)

    monkeypatch.setattr(EditorKernel, "_release_project_world_host_lease", capture_release)
    monkeypatch.setattr(
        project_world_capabilities,
        "unregister_project_world_host_capabilities",
        flaky_unregister,
    )
    monkeypatch.setattr(
        simulation_coordinator,
        "init_simulation_coordinator",
        lambda _context: (_ for _ in ()).throw(RuntimeError("startup failed")),
    )
    caplog.set_level("ERROR", logger="EditorKernel")

    with pytest.raises(
        EditorKernelInitializationRollbackError,
        match="Project World rollback did not settle: startup failed",
    ) as raised:
        EditorKernel()

    assert isinstance(raised.value.__cause__, RuntimeError)
    assert str(raised.value.__cause__) == "startup failed"
    assert len(captured) == 1
    kernel = captured[0]
    capabilities = dict(kernel.project_world_capabilities)
    lease = kernel._project_world_host_lease
    assert capabilities
    assert lease is not None
    assert lease.released is False
    assert kernel._plugin_host_capability_lease is None
    assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False
    assert all(services.get(key) is capability for key, capability in capabilities.items())
    assert "Project World capability rollback failed" in caplog.text

    assert kernel._release_project_world_host_lease() is True
    assert kernel.project_world_capabilities == {}
    assert kernel._project_world_host_lease is None
    assert all(services.has(key) is False for key in capabilities)
    assert attempts == 2
    kernel.deleteLater()


def test_editor_kernel_init_rollback_logs_lease_failure_without_resurrecting_replacement(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    _clean_plugin_host_capability,
) -> None:
    """A release error leaves only the lease and preserves a later replacement."""

    from core.VitaLoom.project import project_world_capabilities
    from core.VitaLoom.project.project_world_host_ownership import ProjectWorldHostLease
    from core.VitaLoom.project.project_world_capabilities import PROJECT_WORLD_READ_MODEL
    from core.VitaLoom.simulation import simulation_coordinator

    services = _clean_plugin_host_capability
    captured: list[EditorKernel] = []
    replacement = object()
    original_release_boundary = EditorKernel._release_project_world_host_lease
    original_unregister = project_world_capabilities.unregister_project_world_host_capabilities
    original_lease_release = ProjectWorldHostLease.release
    attempts = 0

    def capture_release(kernel: EditorKernel) -> bool:
        captured.append(kernel)
        return original_release_boundary(kernel)

    def publish_replacement_after_exact_unpublication(
        actual_services: object, capabilities: dict[str, object]
    ):
        removed = original_unregister(actual_services, capabilities)
        actual_services.register(PROJECT_WORLD_READ_MODEL, replacement)
        return removed

    def flaky_lease_release(lease: ProjectWorldHostLease[object]) -> bool:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Project World composition rollback failed")
        return original_lease_release(lease)

    monkeypatch.setattr(EditorKernel, "_release_project_world_host_lease", capture_release)
    monkeypatch.setattr(
        project_world_capabilities,
        "unregister_project_world_host_capabilities",
        publish_replacement_after_exact_unpublication,
    )
    monkeypatch.setattr(ProjectWorldHostLease, "release", flaky_lease_release)
    monkeypatch.setattr(
        simulation_coordinator,
        "init_simulation_coordinator",
        lambda _context: (_ for _ in ()).throw(RuntimeError("startup failed")),
    )
    caplog.set_level("ERROR", logger="EditorKernel")

    try:
        with pytest.raises(
            EditorKernelInitializationRollbackError,
            match="Project World rollback did not settle: startup failed",
        ) as raised:
            EditorKernel()

        assert isinstance(raised.value.__cause__, RuntimeError)
        assert str(raised.value.__cause__) == "startup failed"
        assert len(captured) == 1
        kernel = captured[0]
        assert kernel.project_world_capabilities == {}
        assert kernel._project_world_host_lease is not None
        assert kernel._project_world_host_lease.released is False
        assert kernel._plugin_host_capability_lease is None
        assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False
        assert services.get(PROJECT_WORLD_READ_MODEL) is replacement
        assert "Project World composition rollback failed" in caplog.text

        assert kernel._release_project_world_host_lease() is True
        assert kernel._project_world_host_lease is None
        assert services.get(PROJECT_WORLD_READ_MODEL) is replacement
        assert attempts == 2
        kernel.deleteLater()
    finally:
        services.unregister(PROJECT_WORLD_READ_MODEL)
def test_first_legacy_consumers_use_capability_seam_not_plugin_loader_state() -> None:
    relative_paths = (
        "builtin/editor_extensions/plugin_runtime_ops.py",
        "builtin/editor_extensions/plugin_manager_plugin.py",
        "builtin/editor_extensions/hot_reload_plugin.py",
        "main.py",
    )
    for relative_path in relative_paths:
        source = (RUNTIME_ROOT / relative_path).read_text(encoding="utf-8-sig")
        assert "kernel.plugin_loader" not in source, relative_path
        assert ".plugin_registry" not in source, relative_path
        assert ".loaded_plugins" not in source, relative_path
        assert ".failed_plugins" not in source, relative_path
        assert ".discovery_errors" not in source, relative_path
        assert (
            "resolve_plugin_host" in source
            or "PluginRuntimeOpsMixin" in source
        ), relative_path

def test_editor_kernel_init_failure_exact_unpublishes_without_restoring_predecessor(
    monkeypatch: pytest.MonkeyPatch,
    _clean_plugin_host_capability,
) -> None:
    """E13 exact-unpublication intentionally is not a predecessor stack."""
    from core.VitaLoom.project import project_world_host_composition

    services = _clean_plugin_host_capability
    predecessor = _CompletePluginHost()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, predecessor)
    monkeypatch.setattr(
        project_world_host_composition,
        "acquire_project_world_host",
        lambda _owner: (_ for _ in ()).throw(RuntimeError("composition failed")),
    )

    with pytest.raises(RuntimeError, match="composition failed"):
        EditorKernel()

    assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False


def test_editor_kernel_plugin_host_unpublication_failure_is_retryable(
    monkeypatch: pytest.MonkeyPatch,
    _clean_plugin_host_capability,
) -> None:
    services = _clean_plugin_host_capability
    kernel = EditorKernel()
    lease = kernel._plugin_host_capability_lease
    original_release = lease.release
    attempts = 0

    def flaky_release():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("unpublish failed")
        return original_release()

    monkeypatch.setattr(lease, "release", flaky_release)
    try:
        assert kernel._release_project_world_host_lease() is False
        assert kernel._plugin_host_capability_lease is lease
        assert services.get(PLUGIN_HOST_CONTROL_OBSERVATION) is (
            kernel.plugin_loader.nested_plugin_host
        )

        assert kernel._release_project_world_host_lease() is True
        assert kernel._plugin_host_capability_lease is None
        assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False
        assert attempts == 2
    finally:
        kernel._release_project_world_host_lease()
        kernel.deleteLater()


class _CompletePluginHost:
    """Minimal public Interface object used only as a prior registry value."""

    def observe_plugins(self) -> dict[str, object]:
        return {}

    def reload_plugin(self, plugin_id: str) -> dict[str, object]:
        return {}

    def unload_plugin(self, plugin_id: str) -> dict[str, object]:
        return {}

    def scan_project_addons(self, project_path: object) -> dict[str, object]:
        return {}

    def sync_plugins_for_project(
        self,
        project_data: dict[str, object],
        *,
        repo_root: object | None = None,
    ) -> dict[str, object]:
        return {}

