#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report AI command undo/redo and audit-history status."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

REPRESENTATIVE_COMMANDS = (
    "entity.create",
    "entity.delete",
    "prefab.place",
    "asset.apply_to_scene",
    "scene.save",
    "project.set_active_scene",
    "project.set_ps_experiment_preset",
    "project.set_evolution_defaults",
    "entity.set_property",
    "transform.set",
    "transform.batch_set",
    "connection.create",
    "connection.delete",
    "connection.set_weight",
    "script.set_property",
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def build_status() -> dict[str, Any]:
    from core.VitaLoom.commands.registry import reset_command_registry

    registry = reset_command_registry()
    registry_source = RUNTIME / "core" / "VitaLoom" / "commands" / "registry.py"
    runtime_commands_source = RUNTIME / "core" / "VitaLoom" / "commands" / "runtime_commands.py"
    command_stack_source = RUNTIME / "core" / "VitaLoom" / "commands" / "command.py"

    registry_text = registry_source.read_text(encoding="utf-8")
    runtime_text = runtime_commands_source.read_text(encoding="utf-8")
    ui_actions_source = RUNTIME / "core" / "VitaLoom" / "ui" / "command_actions.py"
    standard_ui_source = RUNTIME / "builtin" / "editor_extensions" / "standard_ui_plugin.py"
    editor_kernel_source = RUNTIME / "core" / "VitaLoom" / "kernel" / "editor_kernel.py"
    ui_actions_text = ui_actions_source.read_text(encoding="utf-8") if ui_actions_source.is_file() else ""
    standard_ui_text = standard_ui_source.read_text(encoding="utf-8") if standard_ui_source.is_file() else ""
    editor_kernel_text = editor_kernel_source.read_text(encoding="utf-8")
    command_stack_exists = command_stack_source.is_file() and "class CommandStack" in command_stack_source.read_text(
        encoding="utf-8"
    )
    registry_integrated = "CommandStack" in registry_text or "CommandStack" in runtime_text
    has_durable_scene_audit = "audit_id" in registry_text or "audit_id" in runtime_text
    has_registry_undo_bridge = "def undo_last" in registry_text and "def redo_last" in registry_text
    command_undo_path = "command.undo" in runtime_text and "command.redo" in runtime_text
    durable_project_undo = (
        "def undo_project" in registry_text
        and "command.undo_project" in runtime_text
        and "durable_undo" in registry_text
    )
    durable_project_redo = (
        "def redo_project" in registry_text
        and "command.redo_project" in runtime_text
        and "durable_redo" in registry_text
    )
    ui_undo_path = (
        "register_editor_command_actions" in ui_actions_text
        and "edit.undo" in ui_actions_text
        and "command.undo" in ui_actions_text
        and "_register_core_command_actions" in editor_kernel_text
    )
    ui_menu_toolbar_path = (
        "add_menu_items" in ui_actions_text
        and "add_toolbar_items" in ui_actions_text
        and "Edit/Undo" in ui_actions_text
        and "Edit/Redo" in ui_actions_text
        and "layout_manager=" in editor_kernel_text
    )
    standard_ui_semantic_history_dispatch = (
        "def _run_semantic_history_command" in standard_ui_text
        and '"command.undo"' in standard_ui_text
        and '"command.redo"' in standard_ui_text
        and 'registry.run("scene.open", {"scene_path": scene_path})' in standard_ui_text
        and "context.command_stack" not in standard_ui_text
    )
    memory_editor_source = RUNTIME / "core" / "VitaLoom" / "memory_editor.py"
    memory_editor_text = memory_editor_source.read_text(encoding="utf-8") if memory_editor_source.is_file() else ""
    memory_editor_registry_route = (
        'id="memory.edit"' in runtime_text
        and 'get_command_registry().run(' in memory_editor_text
        and '"memory.edit"' in memory_editor_text
        and "CommandStack" not in memory_editor_text
    )
    inspector_source = RUNTIME / "core" / "VitaLoom" / "docks" / "inspector.py"
    viewport_source = RUNTIME / "core" / "VitaLoom" / "viewports" / "scene_viewport.py"
    inspector_text = inspector_source.read_text(encoding="utf-8") if inspector_source.is_file() else ""
    viewport_text = viewport_source.read_text(encoding="utf-8") if viewport_source.is_file() else ""
    inspector_semantic_property_route = (
        "def _apply_scene_entity_property_command" in inspector_text
        and "self._apply_scene_entity_property_command(obj, prop_name, new_value)" in inspector_text
        and 'get_command_registry().run("scene.open", {"scene_path": scene_path})' in inspector_text
    )
    inspector_transient_property_route = (
        "def _apply_transient_property_command" in inspector_text
        and 'registry.run("inspector.set_property", payload)' in inspector_text
        and "bind_transient_target" in inspector_text
        and "CommandStack" not in inspector_text
        and "command_stack" not in inspector_text
    )
    ui_history_scene_refresh = (
        'command_id not in {"command.undo", "command.redo"}' in ui_actions_text
        and 'registry.run("scene.open", {"scene_path": scene_path})' in ui_actions_text
    )
    viewport_single_node_drag_semantic_route = (
        "def _commit_single_node_drag_via_command" in viewport_text
        and "def _run_scene_transform_command" in viewport_text
        and "self._commit_single_node_drag_via_command(" in viewport_text
        and '"transform.set"' in viewport_text
    )
    viewport_multi_node_drag_semantic_route = (
        "def _run_scene_batch_transform_command" in viewport_text
        and "def _commit_multi_node_drag_via_command" in viewport_text
        and '"transform.batch_set"' in viewport_text
        and "self._commit_multi_node_drag_via_command(" in viewport_text
        and "MoveNodeCommand" not in viewport_text
        and 'get_command_registry().run("scene.open", {"scene_path": scene_path})' in viewport_text
    )
    viewport_connection_semantic_route = (
        "def _run_scene_connection_command" in viewport_text
        and "def _commit_connection_via_command" in viewport_text
        and '"connection.create"' in viewport_text
        and '"connection.delete"' in viewport_text
        and 'get_command_registry().run("scene.open", {"scene_path": scene_path})' in viewport_text
    )
    viewport_event_node_semantic_route = (
        "def _run_scene_entity_create_command" in viewport_text
        and "def _run_scene_entity_delete_command" in viewport_text
        and "def _add_node" in viewport_text
        and "def _delete_node" in viewport_text
        and "def create_entity_node" in viewport_text
        and '"entity.create"' in viewport_text
        and '"entity.delete"' in viewport_text
        and "AddNodeCommand" not in viewport_text
        and "DeleteNodeCommand" not in viewport_text
        and 'get_command_registry().run("scene.open", {"scene_path": scene_path})' in viewport_text
    )
    viewport_keyboard_semantic_history = (
        "def _run_global_scene_history_command" in viewport_text
        and "def _run_viewport_keyboard_history_command" in viewport_text
        and "return self._run_global_scene_history_command(command_id)" in viewport_text
        and 'self._run_viewport_keyboard_history_command("command.undo")' in viewport_text
        and 'self._run_viewport_keyboard_history_command("command.redo")' in viewport_text
    )
    viewport_local_command_stack_retired = (
        "from core.VitaLoom.commands.command import CommandStack" not in viewport_text
        and "self.command_stack" not in viewport_text
        and "command_stack" not in viewport_text
    )

    commands: list[dict[str, Any]] = []
    for command_id in REPRESENTATIVE_COMMANDS:
        spec = registry.describe(command_id)
        undoable = bool(spec["undoable"])
        mutates = bool(spec["mutates"])
        commands.append(
            {
                "id": command_id,
                "mutates": mutates,
                "undoable_metadata": undoable,
                "events_envelope": True,
                "undo_redo": "command_path" if command_undo_path else (
                    "registry_bridge" if has_registry_undo_bridge else "metadata_only"
                ),
                "durable_project_undo": durable_project_undo,
                "durable_project_redo": durable_project_redo,
                "audit_history": "durable" if has_durable_scene_audit else "events_only",
            }
        )

    representative_undo = bool(has_registry_undo_bridge)
    command_facing_undo = bool(command_undo_path)
    unified_undo = False
    durable_audit = bool(has_durable_scene_audit)
    if representative_undo and durable_audit:
        status = "durable_audit_with_representative_undo"
    elif durable_audit:
        status = "durable_audit_without_unified_undo"
    else:
        status = "metadata_and_events_only"
    return {
        "schema_version": 4,
        "status": status,
        "commands": commands,
        "command_stack": {
            "exists": bool(command_stack_exists),
            "source": _rel(command_stack_source),
            "registry_integrated": bool(registry_integrated),
        },
        "command_registry_undo_bridge": bool(has_registry_undo_bridge),
        "command_undo_redo_path": command_facing_undo,
        "ui_undo_redo_action_binding": bool(ui_undo_path),
        "ui_menu_toolbar_undo_redo_binding": bool(ui_menu_toolbar_path),
        "standard_ui_semantic_history_dispatch": bool(standard_ui_semantic_history_dispatch),
        "inspector_semantic_property_route": bool(inspector_semantic_property_route),
        "inspector_transient_property_route": bool(inspector_transient_property_route),
        "memory_editor_registry_route": bool(memory_editor_registry_route),
        "inspector_local_command_stack_retired": "CommandStack" not in inspector_text and "command_stack" not in inspector_text,
        "viewport_single_node_drag_semantic_route": bool(viewport_single_node_drag_semantic_route),
        "viewport_multi_node_drag_semantic_route": bool(viewport_multi_node_drag_semantic_route),
        "viewport_connection_semantic_route": bool(viewport_connection_semantic_route),
        "viewport_event_node_semantic_route": bool(viewport_event_node_semantic_route),
        "viewport_keyboard_semantic_history": bool(viewport_keyboard_semantic_history),
        "viewport_local_command_stack_retired": bool(viewport_local_command_stack_retired),
        "ui_history_scene_refresh": bool(ui_history_scene_refresh),
        "representative_undo_redo_runtime": representative_undo,
        "representative_durable_project_undo": bool(durable_project_undo),
        "representative_durable_project_redo": bool(durable_project_redo),
        "unified_undo_redo_runtime": unified_undo,
        "durable_audit_history": durable_audit,
        "checked_sources": [
            _rel(registry_source),
            _rel(runtime_commands_source),
            _rel(command_stack_source),
            _rel(ui_actions_source),
            _rel(standard_ui_source),
            _rel(editor_kernel_source),
            _rel(inspector_source),
            _rel(memory_editor_source),
            _rel(viewport_source),
        ],
        "notes": [
            "Representative scene edit CommandSpecs declare undoable metadata.",
            "CommandRegistry.run returns event envelopes and writes durable audit JSONL for project-scoped mutating commands.",
            "CommandRegistry exposes representative in-memory undo_last/redo_last bridge for entity.create, entity.delete, prefab.place, asset.apply_to_scene, scene.save, project.set_active_scene, project.set_ps_experiment_preset, project.set_evolution_defaults, entity.set_property, transform.set, transform.batch_set, connection.create, connection.delete, connection.set_weight, and script.set_property.",
            "command.undo and command.redo expose that representative bridge to command-facing adapter paths.",
            "Editor UI undo/redo shortcuts are bound to command.undo and command.redo through the command action helper.",
            "Editor menu and toolbar undo/redo actions are bound to the same command.undo and command.redo path.",
            "Standard UI contribution handlers dispatch command.undo/command.redo through Registry and rehydrate successful scene history through scene.open without a context.command_stack fallback.",
            "Supported Inspector entity fields take the semantic registry route before the legacy CommandStack and refresh the loaded .pond through scene.open.",
            "Inspector transient object, dict, position-axis, and nested-script fallback edits use inspector.set_property with Registry-owned target tokens; transient history stores only JSON-safe values and guarded inverses.",
            "Inspector no longer owns or references a private CommandStack; legacy CommandStack remains only as compatibility code for other consumers.",
            "MemoryEditor edit_memory routes atomically through memory.edit with Registry-owned transient memory tokens; import/export/visualization remain non-editing compatibility surfaces.",
            "Single-node SceneViewport drag commits use transform.set instead of local CommandStack.execute and refresh from canonical .pond state.",
            "SceneViewport multi-node drag commits use one atomic transform.batch_set record, rehydrate from canonical .pond state, and do not write legacy CommandStack records.",
            "SceneViewport connection create/delete commits use semantic Registry commands, rehydrate from canonical .pond state, and preserve exact connection list slots for durable undo/redo.",
            "SceneViewport node add, event-driven entity create, and node delete commits use entity.create/entity.delete instead of local AddNodeCommand/DeleteNodeCommand, rehydrate from canonical .pond state, and only emit success side effects after Runtime command success.",
            "SceneViewport has no local CommandStack surface; focused Ctrl+Z/Ctrl+Y route directly to command.undo and command.redo through the semantic Registry history path.",
            "UI undo/redo actions refresh the current .pond after a successful registry history mutation so the viewport can rehydrate from semantic truth.",
            "command.undo_project can replay the latest representative project-scoped execute audit as durable_undo from a fresh registry.",
            "command.redo_project can replay the latest representative durable_undo audit as durable_redo from a fresh registry.",
            "Current CommandStack is a legacy UI Command object stack and is not called by CommandRegistry.run.",
            "Durable project undo/redo is representative-only; full unified undo/runtime replay is not implemented.",
        ],
    }


def main() -> int:
    status = build_status()
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    expected = status["status"] == "durable_audit_with_representative_undo"
    expected = expected and status["command_stack"]["exists"]
    expected = expected and not status["command_stack"]["registry_integrated"]
    expected = expected and status["command_registry_undo_bridge"]
    expected = expected and status["command_undo_redo_path"]
    expected = expected and status["ui_undo_redo_action_binding"]
    expected = expected and status["ui_menu_toolbar_undo_redo_binding"]
    expected = expected and status["standard_ui_semantic_history_dispatch"]
    expected = expected and status["inspector_semantic_property_route"]
    expected = expected and status["inspector_transient_property_route"]
    expected = expected and status["memory_editor_registry_route"]
    expected = expected and status["inspector_local_command_stack_retired"]
    expected = expected and status["viewport_single_node_drag_semantic_route"]
    expected = expected and status["viewport_multi_node_drag_semantic_route"]
    expected = expected and status["viewport_connection_semantic_route"]
    expected = expected and status["viewport_event_node_semantic_route"]
    expected = expected and status["viewport_keyboard_semantic_history"]
    expected = expected and status["ui_history_scene_refresh"]
    expected = expected and status["representative_undo_redo_runtime"]
    expected = expected and status["representative_durable_project_undo"]
    expected = expected and status["representative_durable_project_redo"]
    expected = expected and not status["unified_undo_redo_runtime"]
    expected = expected and status["durable_audit_history"]
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
