# -*- coding: utf-8 -*-
"""AI-native command registry shared by UI, CLI, and MCP adapters."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from core.VitaLoom.project.command_audit import (
    canonical_command_audit_path,
    project_command_audit_exists,
    read_project_command_audit_entries,
)


CommandPayload = Mapping[str, Any]
CommandContext = Mapping[str, Any]
CommandHandler = Callable[[CommandPayload, CommandContext], Dict[str, Any]]


def command_ok(
    result: Optional[Mapping[str, Any]] = None,
    *,
    events: Optional[list[str]] = None,
    warnings: Optional[list[str]] = None,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "result": dict(result or {}),
        "events": list(events or []),
        "warnings": list(warnings or []),
        "error": None,
    }


def command_error(
    code: str,
    message: str,
    *,
    details: Optional[Mapping[str, Any]] = None,
    warnings: Optional[list[str]] = None,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "result": {},
        "events": [],
        "warnings": list(warnings or []),
        "error": {
            "code": str(code),
            "message": str(message),
            "details": dict(details or {}),
        },
    }


@dataclass(frozen=True)
class CommandSpec:
    id: str
    title: str
    handler: CommandHandler
    input_schema: Mapping[str, Any] = field(default_factory=lambda: {"type": "object"})
    output_schema: Mapping[str, Any] = field(default_factory=lambda: {"type": "object"})
    mutates: bool = False
    undoable: bool = False
    requires_gui: bool = False
    capability: str = "vitalloom.core.platform"
    owner: str = "core"
    description: str = ""

    def describe(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "mutates": self.mutates,
            "undoable": self.undoable,
            "requires_gui": self.requires_gui,
            "capability": self.capability,
            "owner": self.owner,
        }


class CommandRegistry:
    """Registry for commands that are safe to expose to UI/CLI/MCP adapters."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandSpec] = {}
        self._undo_stack: list[dict[str, Any]] = []
        self._redo_stack: list[dict[str, Any]] = []
        self._transient_targets: dict[str, Any] = {}

    def bind_transient_target(self, target: Any) -> str:
        """Bind one editor-only object without placing it in command payloads."""

        token = uuid.uuid4().hex
        self._transient_targets[token] = target
        return token

    def unbind_transient_target(self, token: str) -> None:
        """Release a transient target when its owning editor surface closes."""

        self._transient_targets.pop(str(token), None)

    def resolve_transient_target(self, token: str) -> Any:
        """Resolve a transient target for a handler; missing tokens return ``None``."""

        return self._transient_targets.get(str(token))

    def register(self, spec: CommandSpec) -> None:
        command_id = str(spec.id).strip()
        if not command_id:
            raise ValueError("command id is required")
        if command_id in self._commands:
            raise ValueError(f"command already registered: {command_id}")
        self._commands[command_id] = spec

    def unregister(self, command_id: str) -> None:
        self._commands.pop(str(command_id), None)

    def get(self, command_id: str, default: Any = None) -> CommandSpec | Any:
        """Return the exact registered spec for lifecycle ownership checks."""

        return self._commands.get(str(command_id), default)

    def unregister_owner(self, owner: str) -> None:
        owner = str(owner)
        for command_id, spec in list(self._commands.items()):
            if spec.owner == owner:
                self._commands.pop(command_id, None)

    def list(self) -> list[Dict[str, Any]]:
        return [
            spec.describe()
            for _, spec in sorted(self._commands.items(), key=lambda item: item[0])
        ]

    def describe(self, command_id: str) -> Dict[str, Any]:
        spec = self._commands.get(str(command_id))
        if spec is None:
            raise KeyError(command_id)
        return spec.describe()

    def run(
        self,
        command_id: str,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._run_command(
            command_id,
            payload,
            context=context,
            track_undo=True,
            audit_action="execute",
        )

    def undo_last(self, *, context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if not self._undo_stack:
            return command_error("undo_empty", "No undoable command is available")
        op = self._undo_stack.pop()
        result = self._run_command(
            str(op["undo_command_id"]),
            op["undo_payload"],
            context=context,
            track_undo=False,
            audit_action="undo",
            source_audit_id=str(op.get("source_audit_id") or ""),
        )
        if result["ok"]:
            _attach_entity_create_redo_guard(op, result.get("result") or {})
            _attach_entity_delete_redo_guard(op, result.get("result") or {})
            _attach_project_ps_experiment_preset_redo_guard(op, result.get("result") or {})
            _attach_project_evolution_defaults_redo_guard(op, result.get("result") or {})
            _attach_project_active_scene_redo_guard(op, result.get("result") or {})
            _attach_scene_save_redo_guard(op, result.get("result") or {})
            self._redo_stack.append(op)
        else:
            self._undo_stack.append(op)
        return result

    def redo_last(self, *, context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        if not self._redo_stack:
            return command_error("redo_empty", "No redoable command is available")
        op = self._redo_stack.pop()
        result = self._run_command(
            str(op["redo_command_id"]),
            op["redo_payload"],
            context=context,
            track_undo=False,
            audit_action="redo",
            source_audit_id=str(op.get("source_audit_id") or ""),
        )
        if result["ok"]:
            self._undo_stack.append(op)
        else:
            self._redo_stack.append(op)
        return result

    def undo_project(
        self,
        project_path: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        project = _resolve_audit_path(str(project_path or ""))
        if project is None or not (project / "project.json").is_file():
            return command_error("project_not_found", "project_path must point to a project")
        if not project_command_audit_exists(project):
            return command_error("audit_history_missing", "No project command audit history exists")
        entry = _latest_replayable_audit_entry(project)
        if entry is None:
            return command_error("durable_undo_empty", "No durable undoable project command is available")
        source_audit_id = str(entry.get("audit_id") or "")
        pruned_receipts = _pruned_transaction_replay_receipts(project)
        if source_audit_id in pruned_receipts:
            return command_error(
                "durable_undo_pruned",
                "Durable undo was explicitly and irreversibly revoked by a transaction artifact prune",
                details={
                    "source_audit_id": source_audit_id,
                    "prune_receipts": pruned_receipts[source_audit_id],
                },
            )
        undo_record = _build_undo_record(
            str(entry.get("command_id") or ""),
            _mapping_or_empty(entry.get("payload")),
            _mapping_or_empty(entry.get("result")),
        )
        if undo_record is None:
            return command_error(
                "durable_undo_unsupported",
                "Latest audit entry cannot be replayed as a project undo",
            )
        source_audit_id = str(entry.get("audit_id") or "")
        result = self._run_command(
            str(undo_record["undo_command_id"]),
            undo_record["undo_payload"],
            context=context,
            track_undo=False,
            audit_action="durable_undo",
            source_audit_id=source_audit_id,
        )
        if result["ok"]:
            result["result"].update(
                {
                    "durable_replay": "project_undo",
                    "source_audit_id": source_audit_id,
                    "source_command_id": str(entry.get("command_id") or ""),
                }
            )
        return result

    def redo_project(
        self,
        project_path: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        project = _resolve_audit_path(str(project_path or ""))
        if project is None or not (project / "project.json").is_file():
            return command_error("project_not_found", "project_path must point to a project")
        if not project_command_audit_exists(project):
            return command_error("audit_history_missing", "No project command audit history exists")
        entries = _read_audit_entries(project)
        undo_entry, execute_entry = _latest_replayable_redo_entries(entries)
        if undo_entry is None:
            return command_error("durable_redo_empty", "No durable redoable project command is available")
        if execute_entry is None:
            return command_error(
                "durable_redo_source_missing",
                "Original execute audit for durable redo was not found",
            )
        execute_audit_id = str(execute_entry.get("audit_id") or "")
        pruned_receipts = _pruned_transaction_replay_receipts(project)
        if execute_audit_id in pruned_receipts:
            return command_error(
                "durable_redo_pruned",
                "Durable redo was explicitly and irreversibly revoked by a transaction artifact prune",
                details={
                    "source_execute_audit_id": execute_audit_id,
                    "prune_receipts": pruned_receipts[execute_audit_id],
                },
            )
        redo_record = _build_undo_record(
            str(execute_entry.get("command_id") or ""),
            _mapping_or_empty(execute_entry.get("payload")),
            _mapping_or_empty(execute_entry.get("result")),
        )
        if redo_record is None:
            return command_error(
                "durable_redo_unsupported",
                "Original audit entry cannot be replayed as a project redo",
            )
        undo_audit_id = str(undo_entry.get("audit_id") or "")
        redo_payload = _json_safe(redo_record["redo_payload"])
        _attach_entity_create_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        _attach_entity_delete_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        _attach_project_ps_experiment_preset_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        _attach_project_evolution_defaults_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        _attach_project_active_scene_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        _attach_scene_save_redo_guard(redo_record, _mapping_or_empty(undo_entry.get("result")))
        if isinstance(redo_record.get("redo_payload"), Mapping):
            redo_payload = _json_safe(redo_record["redo_payload"])
        result = self._run_command(
            str(redo_record["redo_command_id"]),
            redo_payload,
            context=context,
            track_undo=False,
            audit_action="durable_redo",
            source_audit_id=undo_audit_id,
        )
        if result["ok"]:
            result["result"].update(
                {
                    "durable_replay": "project_redo",
                    "source_audit_id": undo_audit_id,
                    "source_execute_audit_id": execute_audit_id,
                    "source_command_id": str(execute_entry.get("command_id") or ""),
                }
            )
            _annotate_last_audit_entry(
                str(result["result"].get("audit_path") or ""),
                {"source_execute_audit_id": execute_audit_id},
            )
        return result

    def _run_command(
        self,
        command_id: str,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        context: Optional[Mapping[str, Any]] = None,
        track_undo: bool = False,
        audit_action: str = "execute",
        source_audit_id: str = "",
    ) -> Dict[str, Any]:
        spec = self._commands.get(str(command_id))
        if spec is None:
            return command_error("unknown_command", f"Unknown command: {command_id}")
        data = dict(payload or {})
        schema_error = _validate_object_schema(spec.input_schema, data)
        if schema_error:
            return command_error(
                "schema_validation_failed",
                schema_error,
                details={"command_id": command_id},
            )
        try:
            handler_context = dict(context or {})
            handler_context.setdefault("command_registry", self)
            result = spec.handler(data, handler_context)
        except Exception as exc:
            return command_error(
                "command_failed",
                str(exc),
                details={"command_id": command_id, "exception": type(exc).__name__},
            )
        normalized = _normalize_result(result)
        if normalized["ok"] and spec.mutates and _should_append_command_audit(str(command_id)):
            audit = _append_command_audit(
                spec,
                data,
                normalized,
                action=audit_action,
                source_audit_id=source_audit_id,
            )
            if audit:
                normalized["result"].update(audit)
        if normalized["ok"] and track_undo and spec.mutates and spec.undoable:
            undo_record = _build_undo_record(str(command_id), data, normalized["result"])
            if undo_record:
                undo_record["source_audit_id"] = str(normalized["result"].get("audit_id") or "")
                self._undo_stack.append(undo_record)
                self._redo_stack.clear()
        return normalized


_GLOBAL_REGISTRY: Optional[CommandRegistry] = None


def get_command_registry() -> CommandRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = CommandRegistry()
        from core.VitaLoom.commands.runtime_commands import register_runtime_commands

        register_runtime_commands(_GLOBAL_REGISTRY)
    return _GLOBAL_REGISTRY


def reset_command_registry() -> CommandRegistry:
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = CommandRegistry()
    from core.VitaLoom.commands.runtime_commands import register_runtime_commands

    register_runtime_commands(_GLOBAL_REGISTRY)
    return _GLOBAL_REGISTRY


def _normalize_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, Mapping):
        return command_error("invalid_command_result", "Command returned a non-object result")
    if "ok" not in result:
        return command_ok(result)
    return {
        "ok": bool(result.get("ok")),
        "result": dict(result.get("result") or {}),
        "events": list(result.get("events") or []),
        "warnings": list(result.get("warnings") or []),
        "error": result.get("error"),
    }


def _append_command_audit(
    spec: CommandSpec,
    payload: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    action: str = "execute",
    source_audit_id: str = "",
) -> Dict[str, str] | None:
    project = _audit_project_root(payload)
    if project is None:
        return None
    audit_path = canonical_command_audit_path(project)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_id = uuid.uuid4().hex
    entry = {
        "audit_id": audit_id,
        "action": str(action or "execute"),
        "at": datetime.now(timezone.utc).isoformat(),
        "command_id": spec.id,
        "title": spec.title,
        "owner": spec.owner,
        "capability": spec.capability,
        "mutates": spec.mutates,
        "undoable": spec.undoable,
        "project_path": str(project),
        "payload": _json_safe(payload),
        "events": list(result.get("events") or []),
        "result": _json_safe(result.get("result") or {}),
    }
    if source_audit_id:
        entry["source_audit_id"] = str(source_audit_id)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return {"audit_id": audit_id, "audit_path": str(audit_path)}


def _attach_entity_create_redo_guard(op: Mapping[str, Any], result: Mapping[str, Any]) -> None:
    """Attach the successful guarded-delete post-state to one entity-create redo.

    The create command itself cannot know its eventual redo precondition.  Its
    guarded undo (``entity.delete``) is the point that observes the exact state
    after removal, so both memory and durable redo reuse that witness.
    """

    if (
        str(op.get("redo_command_id") or "") != "entity.create"
        or str(op.get("undo_command_id") or "") != "entity.delete"
    ):
        return
    expected_entities = result.get("history_redo_expected_entities")
    expected_connections = result.get("history_redo_expected_connections")
    if not isinstance(expected_entities, list) or not isinstance(expected_connections, list):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_entities"] = _json_safe(expected_entities)
    redo_payload["expected_connections"] = _json_safe(expected_connections)


def _attach_entity_delete_redo_guard(op: Mapping[str, Any], result: Mapping[str, Any]) -> None:
    """Attach the successful guarded-restore post-state to one entity-delete redo.

    A deletion redo must not rely only on the restored target snapshot: unrelated
    survivor or connection changes can make removing the target unsafe. The
    restore operation observes the complete canonical scene after reinsertion,
    and this helper carries that witness through both memory and durable replay.
    """

    if (
        str(op.get("redo_command_id") or "") != "entity.delete"
        or str(op.get("undo_command_id") or "") != "entity.restore_deleted_snapshot"
    ):
        return
    expected_entities = result.get("history_redo_expected_entities")
    expected_connections = result.get("history_redo_expected_connections")
    if not isinstance(expected_entities, list) or not isinstance(expected_connections, list):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_entities"] = _json_safe(expected_entities)
    redo_payload["expected_connections"] = _json_safe(expected_connections)


def _attach_project_ps_experiment_preset_redo_guard(
    op: Mapping[str, Any], result: Mapping[str, Any]
) -> None:
    """Attach the guarded restore post-state to preset redo without generic manifest replay."""

    if (
        str(op.get("redo_command_id") or "") != "project.set_ps_experiment_preset"
        or str(op.get("undo_command_id") or "") != "project.restore_ps_experiment_preset_snapshot"
    ):
        return
    expected_project = result.get("history_redo_expected_project")
    if not isinstance(expected_project, Mapping):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_project"] = _json_safe(dict(expected_project))


def _attach_project_evolution_defaults_redo_guard(
    op: Mapping[str, Any], result: Mapping[str, Any]
) -> None:
    """Attach the guarded restore post-state to evolution-defaults redo."""

    if (
        str(op.get("redo_command_id") or "") != "project.set_evolution_defaults"
        or str(op.get("undo_command_id") or "") != "project.restore_evolution_defaults_snapshot"
    ):
        return
    expected_project = result.get("history_redo_expected_project")
    if not isinstance(expected_project, Mapping):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_project"] = _json_safe(dict(expected_project))


def _attach_project_active_scene_redo_guard(
    op: Mapping[str, Any], result: Mapping[str, Any]
) -> None:
    """Attach the guarded restore post-state to active-scene redo."""

    if (
        str(op.get("redo_command_id") or "") != "project.set_active_scene"
        or str(op.get("undo_command_id") or "") != "project.restore_active_scene_snapshot"
    ):
        return
    expected_project = result.get("history_redo_expected_project")
    if not isinstance(expected_project, Mapping):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_project"] = _json_safe(dict(expected_project))


def _attach_scene_save_redo_guard(op: Mapping[str, Any], result: Mapping[str, Any]) -> None:
    """Attach the successful snapshot-restore post-state to a save redo.

    The exact snapshot observed after guarded undo is the only safe redo
    precondition.  This keeps ordinary in-memory and fresh-registry durable
    replay on the same terminal stale-guard contract.
    """

    if (
        str(op.get("redo_command_id") or "") != "scene.save"
        or str(op.get("undo_command_id") or "") != "scene.restore_snapshot"
    ):
        return
    expected_scene = result.get("history_redo_expected_scene")
    if not isinstance(expected_scene, Mapping):
        return
    redo_payload = op.get("redo_payload")
    if not isinstance(redo_payload, dict):
        return
    redo_payload["expected_scene"] = _json_safe(dict(expected_scene))


def _build_undo_record(
    command_id: str,
    payload: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any] | None:
    if command_id in {"asset.rename", "asset.delete", "asset.referenced.replace"}:
        project_path = payload.get("project_path") or result.get("project_path")
        transaction_id = result.get("transaction_id")
        if not project_path or not transaction_id:
            return None
        base = {"project_path": str(project_path), "transaction_id": str(transaction_id)}
        return {
            "redo_command_id": "asset.transaction.redo",
            "redo_payload": dict(base),
            "undo_command_id": "asset.transaction.undo",
            "undo_payload": dict(base),
        }
    if command_id == "scene.save":
        scene_path = payload.get("scene_path") or result.get("scene_path")
        previous_scene = result.get("previous_scene")
        scene_data = result.get("scene_data")
        expected_scene = result.get("history_undo_expected_scene")
        if (
            not scene_path
            or not isinstance(previous_scene, Mapping)
            or not isinstance(scene_data, Mapping)
            or not isinstance(expected_scene, Mapping)
        ):
            return None
        return {
            "redo_command_id": "scene.save",
            "redo_payload": {
                "scene_path": str(scene_path),
                "data": _json_safe(dict(scene_data)),
                "history_preserve_modified_at": True,
            },
            "undo_command_id": "scene.restore_snapshot",
            "undo_payload": {
                "scene_path": str(scene_path),
                "restore_scene": _json_safe(dict(previous_scene)),
                "expected_scene": _json_safe(dict(expected_scene)),
            },
        }
    if command_id == "project.set_active_scene":
        project_path = payload.get("project_path") or result.get("project_path")
        previous_present = result.get("history_previous_active_scene_present")
        expected_project = result.get("history_undo_expected_project")
        scene_path = result.get("scene_path")
        if (
            not project_path
            or not isinstance(previous_present, bool)
            or not isinstance(expected_project, Mapping)
            or not isinstance(scene_path, str)
        ):
            return None
        return {
            "redo_command_id": "project.set_active_scene",
            "redo_payload": {"project_path": str(project_path), "scene_path": scene_path},
            "undo_command_id": "project.restore_active_scene_snapshot",
            "undo_payload": {
                "project_path": str(project_path),
                "restore_active_scene_present": previous_present,
                "restore_active_scene_value": _json_safe(result.get("history_previous_active_scene_value")),
                "expected_project": _json_safe(dict(expected_project)),
            },
        }
    if command_id == "project.set_ps_experiment_preset":
        project_path = payload.get("project_path") or result.get("project_path")
        previous_present = result.get("history_previous_preset_present")
        expected_project = result.get("history_undo_expected_project")
        preset_path = result.get("ps_experiment_preset")
        if (
            not project_path
            or not isinstance(previous_present, bool)
            or not isinstance(expected_project, Mapping)
            or not isinstance(preset_path, str)
        ):
            return None
        return {
            "redo_command_id": "project.set_ps_experiment_preset",
            "redo_payload": {"project_path": str(project_path), "preset_path": preset_path},
            "undo_command_id": "project.restore_ps_experiment_preset_snapshot",
            "undo_payload": {
                "project_path": str(project_path),
                "restore_preset_present": previous_present,
                "restore_preset_value": _json_safe(result.get("history_previous_preset_value")),
                "expected_project": _json_safe(dict(expected_project)),
            },
        }
    if command_id == "project.set_evolution_defaults":
        project_path = payload.get("project_path") or result.get("project_path")
        previous_present = result.get("history_previous_defaults_present")
        expected_project = result.get("history_undo_expected_project")
        defaults = result.get("evolution_defaults")
        if (
            not project_path
            or not isinstance(previous_present, bool)
            or not isinstance(expected_project, Mapping)
            or not isinstance(defaults, Mapping)
        ):
            return None
        return {
            "redo_command_id": "project.set_evolution_defaults",
            "redo_payload": {
                "project_path": str(project_path),
                "defaults": _json_safe(dict(defaults)),
            },
            "undo_command_id": "project.restore_evolution_defaults_snapshot",
            "undo_payload": {
                "project_path": str(project_path),
                "restore_defaults_present": previous_present,
                "restore_defaults_value": _json_safe(result.get("history_previous_defaults_value")),
                "expected_project": _json_safe(dict(expected_project)),
            },
        }
    if command_id == "memory.edit":
        token = payload.get("target_token")
        old_snapshot = result.get("old_snapshot")
        new_snapshot = result.get("new_snapshot")
        if (
            not isinstance(token, str)
            or not token
            or not isinstance(old_snapshot, Mapping)
            or not isinstance(new_snapshot, Mapping)
        ):
            return None
        old_snapshot = _json_safe(dict(old_snapshot))
        new_snapshot = _json_safe(dict(new_snapshot))
        if old_snapshot == new_snapshot:
            return None
        base = {"target_token": token}
        return {
            "redo_command_id": "memory.edit",
            "redo_payload": {
                **base,
                "expected_snapshot": old_snapshot,
                "snapshot": new_snapshot,
            },
            "undo_command_id": "memory.edit",
            "undo_payload": {
                **base,
                "expected_snapshot": new_snapshot,
                "snapshot": old_snapshot,
            },
        }
    if command_id == "memory.store":
        token = payload.get("target_token")
        old_memories = result.get("old_memories")
        new_memories = result.get("new_memories")
        if (
            not isinstance(token, str)
            or not token
            or not isinstance(old_memories, list)
            or not isinstance(new_memories, list)
        ):
            return None
        old_memories = _json_safe(old_memories)
        new_memories = _json_safe(new_memories)
        if old_memories == new_memories:
            return None
        base = {"target_token": token}
        return {
            "redo_command_id": "memory.store",
            "redo_payload": {
                **base,
                "expected_memories": old_memories,
                "memory_entry": _json_safe(payload.get("memory_entry", {})),
            },
            "undo_command_id": "memory.restore",
            "undo_payload": {
                **base,
                "expected_memories": new_memories,
                "memories": old_memories,
            },
        }
    if command_id == "inspector.set_property":
        token = payload.get("target_token")
        property_path = payload.get("property_path") or result.get("property_path")
        if not isinstance(token, str) or not token or not isinstance(property_path, str):
            return None
        old_value = _json_safe(result.get("old_value"))
        new_value = _json_safe(result.get("new_value"))
        old_present = result.get("old_present")
        new_present = result.get("new_present", True)
        if not isinstance(old_present, bool) or not isinstance(new_present, bool):
            return None
        if old_present == new_present and old_value == new_value:
            return None
        base = {"target_token": token, "property_path": property_path}
        return {
            "redo_command_id": "inspector.set_property",
            "redo_payload": {
                **base,
                "value": new_value,
                "expected_value": old_value,
                "expected_present": old_present,
                "present": new_present,
            },
            "undo_command_id": "inspector.set_property",
            "undo_payload": {
                **base,
                "value": old_value,
                "expected_value": new_value,
                "expected_present": new_present,
                "present": old_present,
            },
        }
    scene_path = payload.get("scene_path") or result.get("scene_path")
    if not scene_path:
        return None
    if command_id == "entity.create":
        entity_id = result.get("entity_id")
        if not entity_id:
            entity = payload.get("entity")
            if isinstance(entity, Mapping):
                entity_id = entity.get("id")
        if not entity_id:
            return None
        entity = result.get("entity")
        entity_index = result.get("entity_index")
        if (
            not isinstance(entity, Mapping)
            or not isinstance(entity_index, int)
            or isinstance(entity_index, bool)
        ):
            return None
        return {
            "redo_command_id": "entity.create",
            "redo_payload": _json_safe(payload),
            "undo_command_id": "entity.delete",
            "undo_payload": {
                "scene_path": str(scene_path),
                "entity_id": str(entity_id),
                "expected_entity": _json_safe(dict(entity)),
                "expected_entity_index": entity_index,
                "expected_incident_connections": [],
            },
        }
    if command_id in {"prefab.place", "asset.apply_to_scene"}:
        entity_id = result.get("entity_id") or payload.get("entity_id")
        entity = result.get("entity")
        entity_index = result.get("entity_index")
        expected_entities = result.get("history_undo_expected_entities")
        expected_connections = result.get("history_undo_expected_connections")
        if (
            not entity_id
            or not isinstance(entity, Mapping)
            or not isinstance(entity_index, int)
            or isinstance(entity_index, bool)
            or not isinstance(expected_entities, list)
            or not isinstance(expected_connections, list)
        ):
            return None
        exact_entity = _json_safe(dict(entity))
        return {
            # Redo is source-independent: it inserts the captured serialized
            # entity snapshot and never reloads the prefab or asset source.
            "redo_command_id": "entity.create",
            "redo_payload": {
                "scene_path": str(scene_path),
                "entity": exact_entity,
                "entity_index": entity_index,
                "preserve_entity_snapshot": True,
            },
            "undo_command_id": "entity.delete",
            "undo_payload": {
                "scene_path": str(scene_path),
                "entity_id": str(entity_id),
                "expected_entity": exact_entity,
                "expected_entity_index": entity_index,
                "expected_incident_connections": [],
                "expected_entities": _json_safe(expected_entities),
                "expected_connections": _json_safe(expected_connections),
            },
        }
    if command_id == "entity.delete":
        entity_id = result.get("entity_id") or payload.get("entity_id")
        entity = result.get("entity")
        entity_index = result.get("entity_index")
        deleted_connections = result.get("deleted_connections")
        expected_entities = result.get("history_restore_expected_entities")
        expected_connections = result.get("history_restore_expected_connections")
        if (
            not entity_id
            or not isinstance(entity, Mapping)
            or not isinstance(entity_index, int)
            or isinstance(entity_index, bool)
            or not isinstance(deleted_connections, list)
            or not isinstance(expected_entities, list)
            or not isinstance(expected_connections, list)
        ):
            return None
        return {
            "redo_command_id": "entity.delete",
            "redo_payload": _json_safe(payload),
            "undo_command_id": "entity.restore_deleted_snapshot",
            "undo_payload": {
                "scene_path": str(scene_path),
                "entity_id": str(entity_id),
                "entity": _json_safe(entity),
                "entity_index": entity_index,
                "deleted_connections": _json_safe(deleted_connections),
                "expected_entities": _json_safe(expected_entities),
                "expected_connections": _json_safe(expected_connections),
            },
        }
    if command_id == "entity.set_property":
        entity_id = payload.get("entity_id") or result.get("entity_id")
        property_path = payload.get("property_path") or result.get("property_path")
        previous_entity = result.get("previous_entity")
        if not entity_id or not property_path or not isinstance(previous_entity, Mapping):
            return None
        return {
            "redo_command_id": "entity.set_property",
            "redo_payload": _json_safe(payload),
            "undo_command_id": "entity.restore_snapshot",
            "undo_payload": {
                "scene_path": str(scene_path),
                "entity_id": str(entity_id),
                "entity": _json_safe(previous_entity),
            },
        }
    if command_id == "transform.set":
        entity_id = payload.get("entity_id") or result.get("entity_id")
        changed = result.get("changed")
        if not entity_id or not isinstance(changed, Mapping):
            return None
        undo_payload: dict[str, Any] = {"scene_path": str(scene_path), "entity_id": str(entity_id)}
        redo_payload: dict[str, Any] = {"scene_path": str(scene_path), "entity_id": str(entity_id)}
        for key, values in changed.items():
            if not isinstance(values, Mapping):
                continue
            normalized_key = str(key)
            old_value = _json_safe(values.get("old"))
            new_value = _json_safe(values.get("new"))
            undo_payload[normalized_key] = old_value
            redo_payload[normalized_key] = new_value
            if normalized_key == "position":
                # The Inspector-owned position contract is a narrow finite 2D
                # domain. Its inverses must prove the exact canonical value they
                # are replacing, so a later edit cannot be silently overwritten.
                undo_payload["expected_position"] = new_value
                redo_payload["expected_position"] = old_value
        if len(undo_payload) <= 2:
            return None
        return {
            "redo_command_id": "transform.set",
            "redo_payload": redo_payload,
            "undo_command_id": "transform.set",
            "undo_payload": undo_payload,
        }
    if command_id == "transform.batch_set":
        changed = result.get("changed")
        if not isinstance(changed, list) or not changed:
            return None
        undo_transforms: list[dict[str, Any]] = []
        redo_transforms: list[dict[str, Any]] = []
        for item in changed:
            if not isinstance(item, Mapping):
                return None
            entity_id = str(item.get("entity_id") or "").strip()
            position = item.get("position")
            if not entity_id or not isinstance(position, Mapping):
                return None
            if "old" not in position or "new" not in position:
                return None
            undo_transforms.append({"entity_id": entity_id, "position": _json_safe(position["old"])})
            redo_transforms.append({"entity_id": entity_id, "position": _json_safe(position["new"])})
        return {
            "redo_command_id": "transform.batch_set",
            "redo_payload": {"scene_path": str(scene_path), "transforms": redo_transforms},
            "undo_command_id": "transform.batch_set",
            "undo_payload": {"scene_path": str(scene_path), "transforms": undo_transforms},
        }
    if command_id in {"connection.create", "connection.delete"}:
        connection = result.get("connection")
        connection_index = result.get("connection_index")
        if not isinstance(connection, Mapping) or not isinstance(connection_index, int):
            return None
        exact_payload = {
            "scene_path": str(scene_path),
            "connection": _json_safe(connection),
            "connection_index": connection_index,
        }
        if command_id == "connection.create":
            return {
                "redo_command_id": "connection.create",
                "redo_payload": exact_payload,
                "undo_command_id": "connection.delete",
                "undo_payload": exact_payload,
            }
        return {
            "redo_command_id": "connection.delete",
            "redo_payload": exact_payload,
            "undo_command_id": "connection.create",
            "undo_payload": exact_payload,
        }
    if command_id == "connection.set_weight":
        old_connection = result.get("old_connection")
        new_connection = result.get("new_connection")
        connection_index = result.get("connection_index")
        if (
            not isinstance(old_connection, Mapping)
            or not isinstance(new_connection, Mapping)
            or not isinstance(connection_index, int)
            or isinstance(connection_index, bool)
            or "weight" not in old_connection
            or "weight" not in new_connection
        ):
            return None
        undo_payload = {
            "scene_path": str(scene_path),
            "connection_index": connection_index,
            "connection": _json_safe(new_connection),
            "weight": _json_safe(old_connection["weight"]),
        }
        redo_payload = {
            "scene_path": str(scene_path),
            "connection_index": connection_index,
            "connection": _json_safe(old_connection),
            "weight": _json_safe(new_connection["weight"]),
        }
        return {
            "redo_command_id": "connection.set_weight",
            "redo_payload": redo_payload,
            "undo_command_id": "connection.set_weight",
            "undo_payload": undo_payload,
        }
    if command_id == "script.set_property":
        entity_id = payload.get("entity_id") or result.get("entity_id")
        script = payload.get("script") or result.get("script")
        prop_path = payload.get("property_path") or result.get("property_path")
        if not entity_id or not script or not prop_path:
            return None
        base = {
            "scene_path": str(scene_path),
            "entity_id": str(entity_id),
            "script": str(script),
            "property_path": str(prop_path),
        }
        undo_payload = dict(base)
        undo_payload["value"] = _json_safe(result.get("old_value"))
        redo_payload = dict(base)
        redo_payload["value"] = _json_safe(result.get("new_value"))
        return {
            "redo_command_id": "script.set_property",
            "redo_payload": redo_payload,
            "undo_command_id": "script.set_property",
            "undo_payload": undo_payload,
        }
    return None


def _should_append_command_audit(command_id: str) -> bool:
    return command_id not in {
        "command.undo",
        "command.redo",
        "command.undo_project",
        "command.redo_project",
    }


def _read_audit_entries(project: Path) -> list[dict[str, Any]]:
    """Read canonical audit history plus non-destructive legacy compatibility."""

    return read_project_command_audit_entries(project)


def _pruned_transaction_replay_receipts(project: Path) -> dict[str, list[dict[str, str]]]:
    """Return only strict terminal prune receipts keyed by source audit id.

    A malformed or provenance-inconsistent receipt must not silently alter replay
    selection.  The Authority owns receipt validation, while the Registry owns
    the user-facing durable undo/redo decision.
    """

    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            list_asset_transaction_artifact_prune_receipts,
        )

        listing = list_asset_transaction_artifact_prune_receipts(project)
    except (AssetReferenceTransactionError, OSError, ValueError):
        return {}
    revoked: dict[str, list[dict[str, str]]] = {}
    for raw in listing.get("receipts", []):
        if not isinstance(raw, Mapping) or str(raw.get("state") or "") != "pruned":
            continue
        audit_id = str(raw.get("source_audit_id") or "")
        prune_id = str(raw.get("prune_id") or "")
        if not audit_id or not prune_id:
            continue
        revoked.setdefault(audit_id, []).append(
            {
                "prune_id": prune_id,
                "transaction_id": str(raw.get("transaction_id") or ""),
                "source_command_id": str(raw.get("source_command_id") or ""),
            }
        )
    return revoked


def _latest_replayable_audit_entry(project: Path) -> dict[str, Any] | None:
    entries = _read_audit_entries(project)
    replay_state = _execute_audit_replay_state(entries)
    for entry in reversed(entries):
        audit_id = str(entry.get("audit_id") or "")
        if not audit_id or not replay_state.get(audit_id, False):
            continue
        if str(entry.get("action") or "execute") != "execute":
            continue
        if str(entry.get("command_id") or "") in {
            "entity.create",
            "entity.delete",
            "scene.save",
            "prefab.place",
            "asset.apply_to_scene",
            "project.set_active_scene",
            "project.set_ps_experiment_preset",
            "project.set_evolution_defaults",
            "transform.set",
            "transform.batch_set",
            "connection.create",
            "connection.delete",
            "connection.set_weight",
            "script.set_property",
            "entity.set_property",
            "asset.rename",
            "asset.delete",
            "asset.referenced.replace",
        }:
            return entry
    return None


def _execute_audit_replay_state(entries: list[dict[str, Any]]) -> dict[str, bool]:
    """Return whether each execute audit still represents the current state.

    A local undo followed by a local redo must leave the original execute eligible
    for a later fresh-registry durable undo.  Durable redo records point at their
    durable-undo audit, so they additionally carry ``source_execute_audit_id``.
    """

    state: dict[str, bool] = {}
    for entry in entries:
        action = str(entry.get("action") or "execute")
        audit_id = str(entry.get("audit_id") or "")
        if action == "execute" and audit_id:
            state[audit_id] = True
            continue
        if action in {"undo", "durable_undo"}:
            source_audit_id = str(entry.get("source_audit_id") or "")
            if source_audit_id:
                state[source_audit_id] = False
            continue
        if action == "redo":
            source_audit_id = str(entry.get("source_audit_id") or "")
            if source_audit_id:
                state[source_audit_id] = True
            continue
        if action == "durable_redo":
            execute_audit_id = str(entry.get("source_execute_audit_id") or "")
            if execute_audit_id:
                state[execute_audit_id] = True
    return state


def _latest_replayable_redo_entries(
    entries: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    by_audit_id = {str(entry.get("audit_id") or ""): entry for entry in entries}
    consumed_undos = {
        str(entry.get("source_audit_id") or "")
        for entry in entries
        if str(entry.get("action") or "") in {"redo", "durable_redo"}
    }
    for entry in reversed(entries):
        undo_audit_id = str(entry.get("audit_id") or "")
        if not undo_audit_id or undo_audit_id in consumed_undos:
            continue
        if str(entry.get("action") or "") != "durable_undo":
            continue
        execute_entry = by_audit_id.get(str(entry.get("source_audit_id") or ""))
        return entry, execute_entry if isinstance(execute_entry, dict) else None
    return None, None


def _annotate_last_audit_entry(raw_audit_path: str, values: Mapping[str, Any]) -> None:
    if not raw_audit_path:
        return
    path = _resolve_audit_path(raw_audit_path)
    if path is None or not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(entry, dict):
            return
        entry.update(_json_safe(values))
        lines[index] = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _audit_project_root(payload: Mapping[str, Any]) -> Path | None:
    project_path = payload.get("project_path")
    if project_path:
        project = _resolve_audit_path(str(project_path))
        if project and (project / "project.json").is_file():
            return project
    scene_path = payload.get("scene_path")
    if scene_path:
        scene = _resolve_audit_path(str(scene_path))
        if scene and scene.suffix == ".pond" and scene.parent.name == "scenes":
            project = scene.parent.parent
            if (project / "project.json").is_file():
                return project
    return None


def _resolve_audit_path(raw: str) -> Path | None:
    try:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()
    except OSError:
        return None


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _validate_object_schema(schema: Mapping[str, Any], payload: Mapping[str, Any]) -> str | None:
    if not schema:
        return None
    if schema.get("type", "object") != "object":
        return "Only object input schemas are supported"
    if not isinstance(payload, Mapping):
        return "Payload must be an object"
    required = schema.get("required") or []
    for key in required:
        if key not in payload:
            return f"Missing required field: {key}"
    properties = schema.get("properties") or {}
    if not isinstance(properties, Mapping):
        return None
    for key, rule in properties.items():
        if key not in payload or not isinstance(rule, Mapping):
            continue
        expected = rule.get("type")
        value = payload[key]
        if expected == "string" and not isinstance(value, str):
            return f"Field {key} must be a string"
        if expected == "integer" and not (isinstance(value, int) and not isinstance(value, bool)):
            return f"Field {key} must be an integer"
        if expected == "number" and not (
            isinstance(value, (int, float)) and not isinstance(value, bool)
        ):
            return f"Field {key} must be a number"
        if expected == "boolean" and not isinstance(value, bool):
            return f"Field {key} must be a boolean"
        if expected == "object" and not isinstance(value, Mapping):
            return f"Field {key} must be an object"
        if expected == "array" and not isinstance(value, list):
            return f"Field {key} must be an array"
    return None

