# -*- coding: utf-8 -*-
"""GameViewport selected identity Adapter and dedicated service Seam."""
from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.service_keys import SR_SELECTED_IDENTITY_HOST
from core.VitaLoom.tools.selection_tool import Node
from core.VitaLoom.viewports.game_viewport import GameViewport


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def viewport() -> GameViewport:
    instance = GameViewport()
    instance.register_as_sr_host()
    try:
        yield instance
    finally:
        instance.unregister_as_sr_host()


def _install(viewport: GameViewport, *, counterpart: bool = True) -> str:
    entity = viewport._SceneRuntimeEntity("entity_1", "organism", (10.0, 20.0), 18.0)
    viewport.scene_runtime_entities = [entity]
    viewport._sr_serialized_scene_entity_ids = {"entity_1"} if counterpart else set()
    viewport._sr_runtime_scene_path = "scenes/demo.pond"
    viewport._using_scene_runtime = True
    epoch = viewport._begin_sr_snapshot_lifetime()
    assert epoch
    return epoch


def test_viewport_registers_separate_selected_identity_service(viewport: GameViewport) -> None:
    assert viewport.editor_context.services.get(SR_SELECTED_IDENTITY_HOST) is viewport


def test_viewport_resolves_scene_viewport_node_without_epoch_input(viewport: GameViewport, monkeypatch) -> None:
    epoch = _install(viewport)
    node = Node("entity_1", 1.0, 2.0, "organism")
    monkeypatch.setattr(viewport.editor_context, "_selected_objects", [node])
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: type(
            "Scene",
            (),
            {"get_current_scene_path": lambda self: "scenes/demo.pond"},
        )(),
    )

    result = viewport.resolve_selected_sr_runtime_entity()

    assert result["status"] == "ok"
    assert result["identity"]["runtime_epoch"] == epoch
    assert result["identity"]["entity_id"] == "entity_1"


def test_viewport_hierarchy_selection_and_missing_runtime(viewport: GameViewport) -> None:
    viewport.editor_context._selected_objects = [
        {"type": "entity", "id": "entity_1", "data": {"id": "entity_1"}}
    ]

    result = viewport.resolve_selected_sr_runtime_entity(
        selection_scene_path="scenes/demo.pond"
    )

    assert result["status"] == "not_running"


def test_viewport_explicit_old_identity_returns_stale(viewport: GameViewport, monkeypatch) -> None:
    old_epoch = _install(viewport)
    node = Node("entity_1", 1.0, 2.0, "organism")
    viewport.editor_context._selected_objects = [node]
    _install(viewport)

    result = viewport.resolve_selected_sr_runtime_entity(
        selection_scene_path="scenes/demo.pond",
        explicit_identity={
            "track": "sr_play",
            "runtime_epoch": old_epoch,
            "scene_path": "scenes/demo.pond",
            "entity_id": "entity_1",
        },
    )

    assert result["status"] == "stale"


def test_registry_command_reaches_real_viewport_adapter(viewport: GameViewport, monkeypatch) -> None:
    epoch = _install(viewport)
    viewport.editor_context._selected_objects = [
        {"type": "entity", "id": "entity_1", "data": {"id": "entity_1"}}
    ]
    monkeypatch.setattr(
        "core.VitaLoom.scene.scene_manager.get_scene_manager",
        lambda: type(
            "Scene",
            (),
            {"get_current_scene_path": lambda self: "scenes/demo.pond"},
        )(),
    )

    result = get_command_registry().run(
        "runtime.sr.selected_entity_snapshot",
        {},
        context={"editor_context": viewport.editor_context},
    )

    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
    assert result["result"]["identity"]["runtime_epoch"] == epoch
    assert result["result"]["snapshot"]["entity_id"] == "entity_1"
