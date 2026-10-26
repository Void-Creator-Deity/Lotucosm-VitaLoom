# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import os

import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.core.service_keys import (
    SIMULATION_SR_HOST,
    SR_SELECTED_IDENTITY_HOST,
    WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST,
)
from core.VitaLoom.kernel.layout_manager import LayoutManager
from core.VitaLoom.viewports.game_viewport import GameViewport


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def viewport() -> GameViewport:
    instance = GameViewport()
    instance.register_as_sr_host()
    yield instance
    instance.dispose_runtime_capabilities()


def test_game_viewport_dispose_runtime_capabilities_is_idempotent(viewport) -> None:
    services = viewport.editor_context.services
    assert services.get(SR_SELECTED_IDENTITY_HOST) is viewport
    assert services.get(SIMULATION_SR_HOST) is viewport
    assert services.get(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST) is viewport

    first = viewport.dispose_runtime_capabilities()
    second = viewport.dispose_runtime_capabilities()

    assert first.removed_keys == (
        SIMULATION_SR_HOST,
        SR_SELECTED_IDENTITY_HOST,
        WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST,
    )
    assert second is None
    assert services.get(SR_SELECTED_IDENTITY_HOST) is None
    assert services.get(SIMULATION_SR_HOST) is None
    assert services.get(WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST) is None


def test_layout_manager_disposes_generic_viewport_adapters() -> None:
    calls: list[str] = []

    class Adapter:
        def dispose_runtime_capabilities(self):
            calls.append("disposed")
            return "ok"

    manager = LayoutManager.__new__(LayoutManager)
    manager.viewports = {"game": Adapter(), "plain": object()}

    report = manager.dispose_viewport_runtime_capabilities()

    assert report == {"disposed": ("game",), "failed": ()}
    assert calls == ["disposed"]


def test_layout_manager_remove_viewport_cleans_before_delete() -> None:
    calls: list[str] = []

    class Stack:
        def removeWidget(self, widget) -> None:
            calls.append("removed-from-stack")

    class Adapter:
        def dispose_runtime_capabilities(self):
            calls.append("disposed")

        def deleteLater(self) -> None:
            calls.append("deleted")

    manager = LayoutManager.__new__(LayoutManager)
    manager.viewports = {"game": Adapter()}
    manager.viewport_providers = {}
    manager.viewport_tabs = None
    manager.main_window = type("Window", (), {"central_stack": Stack()})()
    manager.current_viewport = None

    manager.remove_viewport("game")

    assert calls == ["disposed", "removed-from-stack", "deleted"]
    assert manager.viewports == {}


def test_layout_manager_reports_cleanup_failure_without_hiding_it() -> None:
    class Broken:
        def dispose_runtime_capabilities(self):
            raise RuntimeError("boom")

    manager = LayoutManager.__new__(LayoutManager)
    manager.viewports = {"broken": Broken()}

    report = manager.dispose_viewport_runtime_capabilities()

    assert report["disposed"] == ()
    assert report["failed"] == ("broken",)


def test_editor_close_path_uses_layout_manager_capability_cleanup_before_release() -> None:
    source = inspect.getsource(__import__(
        "core.VitaLoom.kernel.editor_kernel", fromlist=["EditorKernel"]
    ).EditorKernel.closeEvent)
    assert "dispose_viewport_runtime_capabilities" in source
    assert source.index("dispose_viewport_runtime_capabilities") < source.index(
        "_release_project_world_host_lease"
    )
