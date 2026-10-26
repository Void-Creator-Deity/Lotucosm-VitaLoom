# -*- coding: utf-8 -*-
"""E13 integration proof for exact runtime capability publication lifecycles."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtWidgets import QApplication, QWidget

import builtin.editor_extensions.console_plugin as console_plugin_module
import builtin.editor_extensions.downloader_plugin as downloader_plugin_module
import builtin.editor_extensions.package_manager_plugin as package_manager_plugin_module
import builtin.editor_extensions.ps_experiment_plugin as ps_plugin_module
import core.VitaLoom.ui.console as console_module
import core.VitaLoom.ui.logging_bridge as logging_bridge
from builtin.editor_extensions.console_plugin import ConsolePlugin
from builtin.editor_extensions.downloader_plugin import DownloaderPlugin
from builtin.editor_extensions.game_viewport_plugin import GameViewportPlugin
from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from builtin.editor_extensions.ps_experiment_plugin import PsExperimentPlugin
from core.VitaLoom.core.editor_context import ServiceRegistry, get_editor_context
from core.VitaLoom.core.service_keys import (
    DOWNLOADER,
    PACKAGE_CATALOG,
    PACKAGE_OPERATIONS,
    PS_EXPERIMENT,
    PS_RUNTIME_SNAPSHOT_HOST,
    SIMULATION_SR_HOST,
    SR_SELECTED_IDENTITY_HOST,
    UI_CONSOLE_PANEL,
)
from core.VitaLoom.inspector.sr_selected_component_projection import (
    load_sr_selected_component_projection_view_model,
)
from core.VitaLoom.player.player_shell import PlayerShell
from core.VitaLoom.viewports.game_viewport import GameViewport


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


class _EventBus:
    def __init__(self) -> None:
        self.subscriptions: list[tuple[str, object]] = []

    def subscribe(self, event: str, callback: object) -> None:
        self.subscriptions.append((event, callback))

    def unsubscribe(self, event: str, callback: object) -> None:
        try:
            self.subscriptions.remove((event, callback))
        except ValueError:
            pass


class _Context:
    def __init__(self, project_root: Path | None = None) -> None:
        self.services = ServiceRegistry()
        self.event_bus = _EventBus()
        self.kernel = None
        self.project_root = str(project_root) if project_root is not None else None

    @staticmethod
    def i18n_tr(_key: str, default: str = "") -> str:
        return default


def test_game_viewport_adapter_requires_explicit_host_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = get_editor_context()
    services = ServiceRegistry()
    monkeypatch.setattr(context, "services", services)
    monkeypatch.setattr(context, "event_bus", _EventBus(), raising=False)

    viewport = GameViewport()
    try:
        assert services.has(SIMULATION_SR_HOST) is False
        assert services.has(SR_SELECTED_IDENTITY_HOST) is False

        viewport.register_as_sr_host()
        assert services.get(SIMULATION_SR_HOST) is viewport
        assert services.get(SR_SELECTED_IDENTITY_HOST) is viewport

        sr_replacement = object()
        selection_replacement = object()
        services.register(SIMULATION_SR_HOST, sr_replacement)
        services.register(SR_SELECTED_IDENTITY_HOST, selection_replacement)
        viewport.unregister_as_sr_host()

        assert services.get(SIMULATION_SR_HOST) is sr_replacement
        assert services.get(SR_SELECTED_IDENTITY_HOST) is selection_replacement
    finally:
        viewport.unregister_as_sr_host()
        viewport.deleteLater()


def test_player_viewport_host_cleanup_is_safe_to_repeat() -> None:
    class FakeViewport:
        def __init__(self) -> None:
            self.unregister_calls = 0

        def unregister_as_sr_host(self) -> None:
            self.unregister_calls += 1

    viewport = FakeViewport()
    shell = type("FakePlayerShell", (), {"_viewport": viewport})()

    assert PlayerShell._release_viewport_host(shell)
    assert PlayerShell._release_viewport_host(shell)
    assert viewport.unregister_calls == 2

def test_game_viewport_plugin_unload_is_exact_and_idempotent() -> None:
    context = _Context()
    plugin = GameViewportPlugin()
    plugin.on_load(context)
    viewport = plugin.create_viewport_widget()

    assert context.services.get(SIMULATION_SR_HOST) is viewport
    assert context.services.get(SR_SELECTED_IDENTITY_HOST) is viewport

    sr_replacement = object()
    selection_replacement = object()
    context.services.register(SIMULATION_SR_HOST, sr_replacement)
    context.services.register(SR_SELECTED_IDENTITY_HOST, selection_replacement)

    plugin.on_unload()
    plugin.on_unload()

    assert plugin.viewport is None
    assert context.services.get(SIMULATION_SR_HOST) is sr_replacement
    assert context.services.get(SR_SELECTED_IDENTITY_HOST) is selection_replacement


def test_ps_plugin_unload_owns_its_service_not_registry_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePsService:
        def __init__(self, _root: Path) -> None:
            self.is_running = False
            self.bound_context: object | None = None
            self.unbind_count = 0

        def bind_editor_context(self, context: object) -> None:
            self.bound_context = context

        def unbind_editor_context(self) -> None:
            self.bound_context = None
            self.unbind_count += 1

        def discover_runtime_organisms(self) -> dict[str, Any]:
            return {}

        def query_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]:
            return {"identity": identity}

    monkeypatch.setattr(ps_plugin_module, "PsExperimentService", FakePsService)
    context = _Context(tmp_path)
    plugin = PsExperimentPlugin()
    plugin.on_load(context)
    owned_service = plugin._service

    service_replacement = object()
    host_replacement = object()
    context.services.register(PS_EXPERIMENT, service_replacement)
    context.services.register(PS_RUNTIME_SNAPSHOT_HOST, host_replacement)

    plugin.on_unload()
    plugin.on_unload()

    assert owned_service.unbind_count == 1
    assert context.services.get(PS_EXPERIMENT) is service_replacement
    assert context.services.get(PS_RUNTIME_SNAPSHOT_HOST) is host_replacement


def test_package_manager_unload_preserves_later_replacements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = object()
    operations = object()
    monkeypatch.setattr(package_manager_plugin_module, "PackageCatalogService", lambda _root: catalog)
    monkeypatch.setattr(
        package_manager_plugin_module,
        "PackageOperationService",
        lambda *_args: operations,
    )
    monkeypatch.setattr(
        package_manager_plugin_module,
        "get_project_world_read_model",
        lambda _context: object(),
    )
    monkeypatch.setattr(
        package_manager_plugin_module,
        "get_project_world_configuration_host",
        lambda _context: object(),
    )

    context = _Context(tmp_path)
    plugin = PackageManagerPlugin()
    monkeypatch.setattr(plugin, "_get_repo_root", lambda: str(tmp_path))
    monkeypatch.setattr(plugin, "_warm_package_cache", lambda: None)
    plugin.on_load(context)

    catalog_replacement = object()
    operations_replacement = object()
    context.services.register(PACKAGE_CATALOG, catalog_replacement)
    context.services.register(PACKAGE_OPERATIONS, operations_replacement)

    plugin.on_unload()

    assert context.services.get(PACKAGE_CATALOG) is catalog_replacement
    assert context.services.get(PACKAGE_OPERATIONS) is operations_replacement


def test_downloader_unload_preserves_later_replacement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = object()
    monkeypatch.setattr(
        downloader_plugin_module,
        "DownloaderService",
        lambda cache_dir: service,
    )
    context = _Context()
    plugin = DownloaderPlugin()
    plugin.on_load(context)

    replacement = object()
    context.services.register(DOWNLOADER, replacement)
    plugin.on_unload()

    assert context.services.get(DOWNLOADER) is replacement


def test_console_old_plugin_unload_preserves_new_panel_and_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeConsolePanel(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.lines: list[tuple[str, str]] = []

        def log(self, message: str, level: str = "info") -> None:
            self.lines.append((message, level))

    monkeypatch.setattr(console_module, "ConsolePanel", FakeConsolePanel)
    logging_bridge.detach_console_logging()
    context = _Context()
    old_plugin = ConsolePlugin()
    new_plugin = ConsolePlugin()
    old_plugin.on_load(context)
    new_plugin.on_load(context)

    old_plugin.create_dock_widget()
    old_panel = context.services.get(UI_CONSOLE_PANEL)
    old_handler = old_plugin._logging_handler
    new_plugin.create_dock_widget()
    new_panel = context.services.get(UI_CONSOLE_PANEL)
    new_handler = new_plugin._logging_handler

    assert old_panel is not new_panel
    assert old_handler is not new_handler
    assert logging_bridge._HANDLER is new_handler
    assert new_handler in logging.getLogger().handlers

    old_plugin.on_unload()

    assert context.services.get(UI_CONSOLE_PANEL) is new_panel
    assert logging_bridge._HANDLER is new_handler
    assert new_handler in logging.getLogger().handlers

    new_plugin.on_unload()
    assert context.services.has(UI_CONSOLE_PANEL) is False
    assert logging_bridge._HANDLER is None
    assert new_handler not in logging.getLogger().handlers


def test_real_game_viewport_plugin_unload_leaves_default_inspector_headless() -> None:
    context = get_editor_context()
    had_event_bus = hasattr(context, "event_bus")
    previous_event_bus = getattr(context, "event_bus", None)
    context.event_bus = _EventBus()
    plugin = GameViewportPlugin()
    try:
        plugin.on_load(context)
        viewport = plugin.create_viewport_widget()
        assert context.services.get(SR_SELECTED_IDENTITY_HOST) is viewport
    finally:
        plugin.on_unload()
        if had_event_bus:
            context.event_bus = previous_event_bus
        else:
            del context.event_bus

    view_model = load_sr_selected_component_projection_view_model()
    values = {field.id: field.value for field in view_model.section.fields}

    assert values["status"] == "unavailable"
    assert values["maps_live_runtime_snapshot_facts"] is False
