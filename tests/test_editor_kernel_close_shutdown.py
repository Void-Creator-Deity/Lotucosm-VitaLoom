# -*- coding: utf-8 -*-
"""E25 red proofs for fail-closed legacy Editor shutdown adaptation."""
from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from core.VitaLoom.core.capability_publication import publish_capabilities
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _ShutdownOnlyLoader:
    def __init__(self, calls: list[str], report=None, error: Exception | None = None):
        self._calls = calls
        self._report = report
        self._error = error

    @property
    def loaded_plugins(self):
        raise AssertionError("Editor close must not enumerate the runtime registry")

    def unload_plugin(self, _plugin_id):
        raise AssertionError("Editor close must use the single shutdown authority")

    def shutdown_plugins(self):
        self._calls.append("shutdown")
        if self._error is not None:
            raise self._error
        return self._report


class _Layout:
    def __init__(self, calls: list[str]):
        self._calls = calls

    def save_layout(self):
        self._calls.append("layout")

    def dispose_viewport_runtime_capabilities(self):
        self._calls.append("viewport_cleanup")
        return {"failed": ()}


def _fake_editor(calls: list[str], loader: _ShutdownOnlyLoader):
    return SimpleNamespace(
        _t=lambda _key, default="": default,
        _flush_project_before_shutdown=lambda: calls.append("flush")
        or {"status": "flushed"},
        layout_manager=_Layout(calls),
        plugin_loader=loader,
    )


def _event(calls: list[str]):
    return SimpleNamespace(
        accept=lambda: calls.append("accept"),
        ignore=lambda: calls.append("ignore"),
    )


@pytest.mark.parametrize("status", ["settled", "noop"])
def test_editor_close_accepts_only_after_shutdown_and_host_lease_release(
    monkeypatch, status: str
) -> None:
    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    calls: list[str] = []
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    monkeypatch.setattr(
        EditorKernel,
        "_release_project_world_host_lease",
        lambda _self: calls.append("release") or True,
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, {"status": status, "source": "shutdown"}),
    )

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "release",
        "accept",
    ]


@pytest.mark.parametrize("status", ["failed", "blocked"])
def test_editor_close_rejects_unsettled_shutdown_without_releasing_host_lease(
    monkeypatch, status: str
) -> None:
    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    calls: list[str] = []
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    monkeypatch.setattr(
        EditorKernel,
        "_release_project_world_host_lease",
        lambda _self: calls.append("release") or True,
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, {"status": status, "source": "shutdown"}),
    )

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "critical",
        "ignore",
    ]


def test_editor_close_rejects_shutdown_exception_without_releasing_host_lease(
    monkeypatch,
) -> None:
    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    calls: list[str] = []
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    monkeypatch.setattr(
        EditorKernel,
        "_release_project_world_host_lease",
        lambda _self: calls.append("release") or True,
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, error=RuntimeError("shutdown failed")),
    )

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "critical",
        "ignore",
    ]


class _PluginHostCapability:
    """Protocol-complete public Host double for publication-lease proof."""

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


@pytest.fixture
def _published_plugin_host_lease():
    """Publish a real exact-object lease without creating a second Host authority."""

    services = InMemoryRuntimeCapabilityRegistry()
    services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)
    host = _PluginHostCapability()
    lease = publish_capabilities(
        services,
        owner="test.editor-close.plugin-host",
        capabilities={PLUGIN_HOST_CONTROL_OBSERVATION: host},
    )
    try:
        yield services, host, lease
    finally:
        if lease.active:
            lease.release()
        services.unregister(PLUGIN_HOST_CONTROL_OBSERVATION)


def test_editor_close_ignores_failed_plugin_host_unpublication_and_retries(
    monkeypatch,
    _published_plugin_host_lease,
) -> None:
    """A settled Host may close only after its exact public lease releases."""

    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    services, host, lease = _published_plugin_host_lease
    calls: list[str] = []
    attempts = 0
    original_release = lease.release

    def flaky_release():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("plugin Host unpublication failed")
        return original_release()

    monkeypatch.setattr(lease, "release", flaky_release)
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, {"status": "settled", "source": "shutdown"}),
    )
    fake.editor_context = SimpleNamespace(services=services)
    fake._plugin_host_capability_lease = lease
    fake.project_world_capabilities = {}
    fake._project_world_host_lease = None

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "critical",
        "ignore",
    ]
    assert fake._plugin_host_capability_lease is lease
    assert lease.active is True
    assert services.get(PLUGIN_HOST_CONTROL_OBSERVATION) is host

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls[-5:] == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "accept",
    ]
    assert calls.count("critical") == 1
    assert calls.count("ignore") == 1
    assert fake._plugin_host_capability_lease is None
    assert lease.active is False
    assert services.has(PLUGIN_HOST_CONTROL_OBSERVATION) is False
    assert attempts == 2


class _FlakyProjectWorldLease:
    """Lifecycle double that retains its lease until a successful retry."""

    def __init__(self, calls: list[str], *, failures: int = 1) -> None:
        self._calls = calls
        self._failures = failures
        self._attempts = 0
        self._released = False

    @property
    def released(self) -> bool:
        return self._released

    @property
    def attempts(self) -> int:
        return self._attempts

    def release(self) -> bool:
        self._attempts += 1
        self._calls.append("project_world_lease_release")
        if self._attempts <= self._failures:
            raise RuntimeError("Project World composition release failed")
        self._released = True
        return True


def test_editor_close_ignores_project_world_capability_unregistration_failure_and_retries(
    monkeypatch,
) -> None:
    """Capability removal failure retains its exact map and composition lease."""

    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel
    from core.VitaLoom.project import project_world_capabilities as capabilities_module

    calls: list[str] = []
    services = InMemoryRuntimeCapabilityRegistry()
    key = "test.editor-close.project-world.unregistration"
    capability = object()
    services.register(key, capability)
    lease = _FlakyProjectWorldLease(calls, failures=0)
    attempts = 0
    original_unregister = capabilities_module.unregister_project_world_host_capabilities

    def flaky_unregister(actual_services: object, actual_capabilities: dict[str, object]):
        nonlocal attempts
        attempts += 1
        calls.append("project_world_capability_unregister")
        if attempts == 1:
            raise RuntimeError("Project World capability unregistration failed")
        return original_unregister(actual_services, actual_capabilities)

    monkeypatch.setattr(
        capabilities_module,
        "unregister_project_world_host_capabilities",
        flaky_unregister,
    )
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, {"status": "settled", "source": "shutdown"}),
    )
    fake.editor_context = SimpleNamespace(services=services)
    fake._plugin_host_capability_lease = None
    fake.project_world_capabilities = {key: capability}
    fake._project_world_host_lease = lease

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "project_world_capability_unregister",
        "critical",
        "ignore",
    ]
    assert fake.project_world_capabilities == {key: capability}
    assert fake._project_world_host_lease is lease
    assert lease.released is False
    assert lease.attempts == 0
    assert services.get(key) is capability

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls[-7:] == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "project_world_capability_unregister",
        "project_world_lease_release",
        "accept",
    ]
    assert calls.count("critical") == 1
    assert calls.count("ignore") == 1
    assert fake.project_world_capabilities == {}
    assert fake._project_world_host_lease is None
    assert lease.released is True
    assert lease.attempts == 1
    assert services.has(key) is False


def test_editor_close_ignores_project_world_lease_failure_without_resurrecting_capabilities(
    monkeypatch,
) -> None:
    """Lease-release failure remains retryable after exact unpublication completes."""

    from PyQt6.QtWidgets import QMessageBox
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    calls: list[str] = []
    services = InMemoryRuntimeCapabilityRegistry()
    owned_key = "test.editor-close.project-world.owned"
    replaced_key = "test.editor-close.project-world.replaced"
    owned_capability = object()
    stale_capability = object()
    replacement = object()
    services.register(owned_key, owned_capability)
    services.register(replaced_key, stale_capability)
    services.register(replaced_key, replacement)
    lease = _FlakyProjectWorldLease(calls)
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: SimpleNamespace(is_scene_modified=lambda: False),
    )
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *_args, **_kwargs: calls.append("critical")
    )
    fake = _fake_editor(
        calls,
        _ShutdownOnlyLoader(calls, {"status": "settled", "source": "shutdown"}),
    )
    fake.editor_context = SimpleNamespace(services=services)
    fake._plugin_host_capability_lease = None
    fake.project_world_capabilities = {
        owned_key: owned_capability,
        replaced_key: stale_capability,
    }
    fake._project_world_host_lease = lease

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "project_world_lease_release",
        "critical",
        "ignore",
    ]
    assert fake.project_world_capabilities == {}
    assert fake._project_world_host_lease is lease
    assert lease.released is False
    assert services.has(owned_key) is False
    assert services.get(replaced_key) is replacement

    EditorKernel.closeEvent(fake, _event(calls))

    assert calls[-6:] == [
        "flush",
        "layout",
        "viewport_cleanup",
        "shutdown",
        "project_world_lease_release",
        "accept",
    ]
    assert calls.count("critical") == 1
    assert calls.count("ignore") == 1
    assert fake.project_world_capabilities == {}
    assert fake._project_world_host_lease is None
    assert lease.released is True
    assert lease.attempts == 2
    assert services.has(owned_key) is False
    assert services.get(replaced_key) is replacement
def test_editor_close_source_uses_only_the_shutdown_interface() -> None:
    from core.VitaLoom.kernel.editor_kernel import EditorKernel

    source = inspect.getsource(EditorKernel.closeEvent)

    assert "plugin_loader.shutdown_plugins()" in source
    assert "loaded_plugins" not in source
    assert "unload_plugin(" not in source
