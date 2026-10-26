# -*- coding: utf-8 -*-
"""Editor UI actions that delegate to the shared command registry."""
from __future__ import annotations

from typing import Any, Mapping

from core.VitaLoom.ui.semantic_history import mirror_scene_save_history_snapshot


def register_editor_command_actions(
    *,
    shortcut_manager: Any | None = None,
    layout_manager: Any | None = None,
    registry: Any | None = None,
    context: Any | None = None,
) -> Mapping[str, str]:
    """Register editor undo/redo actions through the command registry path."""
    if shortcut_manager is None:
        from core.VitaLoom.ui.shortcut_manager import get_shortcut_manager

        shortcut_manager = get_shortcut_manager()
    if registry is None:
        from core.VitaLoom.commands.registry import get_command_registry

        registry = get_command_registry()
    if layout_manager is None and context is not None:
        layout_manager = getattr(context, "layout_manager", None)

    def _run(command_id: str) -> None:
        result = registry.run(command_id, {})
        if command_id not in {"command.undo", "command.redo"} or not result.get("ok"):
            return
        result_data = result.get("result") or {}
        if mirror_scene_save_history_snapshot(result):
            return
        scene_path = str(result_data.get("scene_path") or "").strip()
        if scene_path and result_data.get("history_rehydrate_scene") is not False:
            registry.run("scene.open", {"scene_path": scene_path})

    shortcut_manager.register_shortcut(
        "edit.undo",
        lambda: _run("command.undo"),
        description="Undo",
        context=context,
    )
    shortcut_manager.register_shortcut(
        "edit.redo",
        lambda: _run("command.redo"),
        description="Redo",
        context=context,
    )
    if layout_manager is not None:
        layout_manager.add_menu_items(
            [
                {"path": "Edit/Undo", "action": lambda: _run("command.undo")},
                {"path": "Edit/Redo", "action": lambda: _run("command.redo")},
            ],
            plugin_name="core.command_actions",
        )
        layout_manager.add_toolbar_items(
            [
                {"text": "Undo", "action": lambda: _run("command.undo")},
                {"text": "Redo", "action": lambda: _run("command.redo")},
            ],
            plugin_name="core.command_actions",
        )
    return {"undo": "edit.undo", "redo": "edit.redo"}
