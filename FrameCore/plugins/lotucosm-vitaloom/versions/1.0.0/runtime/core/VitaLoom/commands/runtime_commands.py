# -*- coding: utf-8 -*-
"""Built-in command implementations for the product-version runtime."""
from __future__ import annotations

import json
import os
import re
import hashlib
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from core.VitaLoom.commands.registry import (
    CommandRegistry,
    CommandSpec,
    command_error,
    command_ok,
)
from core.VitaLoom.project.asset_dependency import PATH_KEYS


def register_runtime_commands(registry: CommandRegistry) -> None:
    for spec in _command_specs():
        registry.register(spec)


def _command_specs() -> list[CommandSpec]:
    return [
        CommandSpec(
            id="project.state",
            title="Read Project State",
            description="Read project.json, project.lock.json status, and active scene metadata.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_project_state,
            mutates=False,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="project.open",
            title="Open Project",
            description="Prepare a Project World and apply it through an explicit Host capability.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_project_open,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.editor_essentials",
        ),
        CommandSpec(
            id="project.create",
            title="Create Project",
            description="Create a Project World through the Qt-free runtime authority.",
            input_schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "project_path": {"type": "string"},
                    "template": {"type": "string"},
                    "project_type": {"type": "string"},
                },
            },
            handler=_project_create,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="project.lock.check",
            title="Check Project Lock",
            description="Check whether project.lock.json exists and references this product version.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_project_lock_check,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="project.set_active_scene",
            title="Set Active Project Scene",
            description="Set one .pond scene as the current project's active scene through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["project_path", "scene_path"],
                "properties": {
                    "project_path": {"type": "string"},
                    "scene_path": {"type": "string"},
                    "expected_project": {"type": "object"},
                },
            },
            handler=_project_set_active_scene,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="project.restore_active_scene_snapshot",
            title="Restore Active Project Scene Snapshot",
            description="Internal guarded inverse for one project active-scene history record.",
            input_schema={
                "type": "object",
                "required": ["project_path", "restore_active_scene_present", "expected_project"],
                "properties": {
                    "project_path": {"type": "string"},
                    "restore_active_scene_present": {"type": "boolean"},
                    "restore_active_scene_value": {},
                    "expected_project": {"type": "object"},
                },
            },
            handler=_project_restore_active_scene_snapshot,
            mutates=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="project.set_ps_experiment_preset",
            title="Set PS Experiment Preset",
            description="Bind one PS experiment preset path to the current project contract.",
            input_schema={
                "type": "object",
                "required": ["project_path", "preset_path"],
                "properties": {
                    "project_path": {"type": "string"},
                    "preset_path": {"type": "string"},
                    "expected_project": {"type": "object"},
                },
            },
            handler=_project_set_ps_experiment_preset,
            mutates=True,
            undoable=True,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="project.restore_ps_experiment_preset_snapshot",
            title="Restore PS Experiment Preset Snapshot",
            description="Internal guarded inverse for one project PS experiment preset history record.",
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "restore_preset_present": {"type": "boolean"},
                    "expected_project": {"type": "object"},
                }
            ),
            handler=_project_restore_ps_experiment_preset_snapshot,
            mutates=True,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="project.set_evolution_defaults",
            title="Set Evolution Defaults",
            description="Write project-level evolution defaults through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["project_path", "defaults"],
                "properties": {
                    "project_path": {"type": "string"},
                    "defaults": {"type": "object"},
                    "expected_project": {"type": "object"},
                },
            },
            handler=_project_set_evolution_defaults,
            mutates=True,
            undoable=True,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="project.restore_evolution_defaults_snapshot",
            title="Restore Evolution Defaults Snapshot",
            description="Internal guarded inverse for one project evolution-defaults history record.",
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "restore_defaults_present": {"type": "boolean"},
                    "expected_project": {"type": "object"},
                }
            ),
            handler=_project_restore_evolution_defaults_snapshot,
            mutates=True,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="scene.summary",
            title="Read Scene Summary",
            description="Read a .pond scene summary without mutating project state.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "scene_path": {"type": "string"},
                },
            },
            handler=_scene_summary,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="scene.open",
            title="Open Scene",
            description="Open a .pond scene via SceneManager when a GUI/editor context exists.",
            input_schema=_schema({"scene_path": {"type": "string"}}),
            handler=_scene_open,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="scene.save",
            title="Save Project Scene Snapshot",
            description="Persist one explicit project-local .pond snapshot through Qt-free authority.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "data"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "data": {"type": "object"},
                    "expected_scene": {"type": "object"},
                    "history_preserve_modified_at": {"type": "boolean"},
                },
            },
            handler=_scene_save,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="scene.restore_snapshot",
            title="Restore Scene Snapshot",
            description="Restore one exact .pond snapshot as an internal guarded-history inverse.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "restore_scene", "expected_scene"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "restore_scene": {"type": "object"},
                    "expected_scene": {"type": "object"},
                },
            },
            handler=_scene_restore_snapshot,
            mutates=True,
            undoable=False,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="scene.validate",
            title="Validate Scene",
            description="Validate a .pond scene using the same project contract as editor tools.",
            input_schema=_schema({"scene_path": {"type": "string"}}),
            handler=_scene_validate,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="entity.create",
            title="Create Entity",
            description="Add one entity to a .pond scene through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "entity"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "entity": {"type": "object"},
                    "entity_index": {"type": "integer"},
                    # History replay can preserve an already-serialized entity
                    # exactly instead of applying the interactive-create defaults.
                    "preserve_entity_snapshot": {"type": "boolean"},
                    # Entity-create history redo supplies the exact canonical scene
                    # lists it expects to extend, so it cannot insert into a stale
                    # reordered or independently edited scene.
                    "expected_entities": {"type": "array"},
                    "expected_connections": {"type": "array"},
                },
            },
            handler=_entity_create,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="entity.set_property",
            title="Set Entity Property",
            description="Set one JSON property on an entity in a .pond scene.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "property_path": {"type": "string"},
                }
            ),
            handler=_entity_set_property,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="memory.edit",
            title="Edit Runtime Memory",
            description="Atomically edit one transient MemoryGene through the Qt-free command registry.",
            input_schema={
                "type": "object",
                "required": ["target_token", "expected_snapshot", "snapshot"],
                "properties": {
                    "target_token": {"type": "string"},
                    "expected_snapshot": {"type": "object"},
                    "snapshot": {"type": "object"},
                },
            },
            handler=_memory_edit,
            mutates=True,
            undoable=True,
            capability="vitalloom.core.platform",
            owner="core.memory_editor",
        ),
        CommandSpec(
            id="memory.store",
            title="Store Runtime Memory",
            description="Store one imported MemoryGene through the Qt-free command registry.",
            input_schema={
                "type": "object",
                "required": ["target_token", "expected_memories", "memory_entry"],
                "properties": {
                    "target_token": {"type": "string"},
                    "expected_memories": {"type": "array"},
                    "memory_entry": {"type": "object"},
                },
            },
            handler=_memory_store,
            mutates=True,
            undoable=True,
            capability="vitalloom.core.platform",
            owner="core.memory_editor",
        ),
        CommandSpec(
            id="memory.restore",
            title="Restore Runtime Memory Collection",
            description="Internal guarded inverse for one transient MemorySystem collection history record.",
            input_schema={
                "type": "object",
                "required": ["target_token", "expected_memories", "memories"],
                "properties": {
                    "target_token": {"type": "string"},
                    "expected_memories": {"type": "array"},
                    "memories": {"type": "array"},
                },
            },
            handler=_memory_restore,
            mutates=True,
            undoable=False,
            capability="vitalloom.core.platform",
            owner="core.memory_editor",
        ),
        CommandSpec(
            id="inspector.set_property",
            title="Set Inspector Property",
            description="Set one property on a transient Inspector target through the Qt-free command registry.",
            input_schema={
                "type": "object",
                "required": ["target_token", "property_path", "value"],
                "properties": {
                    "target_token": {"type": "string"},
                    "property_path": {"type": "string"},
                    "value": {},
                    "present": {"type": "boolean"},
                    "expected_present": {"type": "boolean"},
                    "expected_value": {},
                },
            },
            handler=_inspector_set_property,
            mutates=True,
            undoable=True,
            capability="vitalloom.editor_essentials",
            owner="core.inspector",
        ),
        CommandSpec(
            id="entity.restore_snapshot",
            title="Restore Entity Snapshot",
            description="Restore a complete entity snapshot as an internal semantic-history inverse.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "entity": {"type": "object"},
                }
            ),
            handler=_entity_restore_snapshot,
            mutates=True,
            undoable=False,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="entity.restore_deleted_snapshot",
            title="Restore Deleted Entity Snapshot",
            description="Restore a deleted entity and its incident connections as an internal semantic-history inverse.",
            input_schema={
                "type": "object",
                "required": [
                    "scene_path",
                    "entity_id",
                    "entity",
                    "entity_index",
                    "deleted_connections",
                ],
                "properties": {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "entity": {"type": "object"},
                    "entity_index": {"type": "integer"},
                    "deleted_connections": {"type": "array"},
                    # Entity-delete history undo supplies the exact canonical scene
                    # state observed after deletion, preventing snapshot restoration
                    # into a scene that has since diverged.
                    "expected_entities": {"type": "array"},
                    "expected_connections": {"type": "array"},
                },
            },
            handler=_entity_restore_deleted_snapshot,
            mutates=True,
            undoable=False,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="entity.delete",
            title="Delete Entity",
            description="Remove one entity from a .pond scene.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "entity_id"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    # Optional witnesses are supplied by semantic history inverses.
                    # Direct user deletes remain backward compatible without them.
                    "expected_entity": {"type": "object"},
                    "expected_entity_index": {"type": "integer"},
                    "expected_incident_connections": {"type": "array"},
                    "expected_entities": {"type": "array"},
                    "expected_connections": {"type": "array"},
                },
            },
            handler=_entity_delete,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="transform.set",
            title="Set Entity Transform",
            description="Set position, rotation, or scale on an entity through the shared scene command layer.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "entity_id"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "position": {"type": "array"},
                    # A position-only history inverse supplies the canonical position
                    # it expects to replace. The handler performs domain validation
                    # and exact canonical-state comparison before writing.
                    "expected_position": {"type": "array"},
                    "rotation": {},
                    "scale": {"type": "array"},
                },
            },
            handler=_transform_set,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="transform.batch_set",
            title="Set Multiple Entity Positions",
            description="Atomically set JSON-safe positions for multiple entities in one .pond scene.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "transforms": {"type": "array"},
                }
            ),
            handler=_transform_batch_set,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="connection.create",
            title="Create Scene Connection",
            description="Create one directed .pond connection through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "connection"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "connection": {"type": "object"},
                    "connection_index": {"type": "integer"},
                },
            },
            handler=_connection_create,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="connection.delete",
            title="Delete Scene Connection",
            description="Delete one exact .pond connection through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "connection", "connection_index"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "connection": {"type": "object"},
                    "connection_index": {"type": "integer"},
                },
            },
            handler=_connection_delete,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="connection.set_weight",
            title="Set Scene Connection Weight",
            description="Set one exact .pond connection weight through the shared command layer.",
            input_schema={
                "type": "object",
                "required": ["scene_path", "connection", "connection_index", "weight"],
                "properties": {
                    "scene_path": {"type": "string"},
                    "connection": {"type": "object"},
                    "connection_index": {"type": "integer"},
                    # Finite numeric validation belongs to the handler so it can
                    # reject bool/NaN/infinity with the stable domain error.
                    "weight": {},
                },
            },
            handler=_connection_set_weight,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="script.set_property",
            title="Set Script Property",
            description="Set one nested script property on an entity in a .pond scene.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                    "script": {"type": "string"},
                    "property_path": {"type": "string"},
                }
            ),
            handler=_script_set_property,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="prefab.place",
            title="Place Prefab",
            description="Instantiate a project prefab into a .pond scene through the same command used by editor placement tools.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "prefab_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                }
            ),
            handler=_prefab_place,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="asset.scan",
            title="Scan Project Assets",
            description="List project assets known to the workspace asset tree.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_scan,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.create",
            title="Create Project Asset",
            description="Create a project asset through the shared asset pipeline command.",
            input_schema={
                "type": "object",
                "required": ["project_path", "asset_type", "name", "folder"],
                "properties": {
                    "project_path": {"type": "string"},
                    "asset_type": {"type": "string"},
                    "name": {"type": "string"},
                    "folder": {"type": "string"},
                },
            },
            handler=_asset_create,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.import",
            title="Import Asset",
            description="Copy an external file into the current project asset tree.",
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "target_folder": {"type": "string"},
                }
            ),
            handler=_asset_import,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.refresh",
            title="Refresh Project Asset Registry",
            description="Persist and refresh stable project asset identities against current index facts.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_refresh,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.rename",
            title="Rename Project Asset",
            description="Rename one project-contained file while preserving its persistent asset identity.",
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "target_path": {"type": "string"},
                }
            ),
            handler=_asset_rename,
            mutates=True,
            undoable=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.delete",
            title="Delete Project Asset",
            description="Delete one project-contained file and retain a persistent identity tombstone.",
            input_schema=_schema(
                {"project_path": {"type": "string"}, "asset_path": {"type": "string"}}
            ),
            handler=_asset_delete,
            mutates=True,
            undoable=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.retirement.analyze",
            title="Analyze Referenced Asset Retirement",
            description="Read-only policy and impact analysis for retiring a referenced project asset.",
            input_schema={
                "type": "object",
                "required": ["project_path", "source_path"],
                "properties": {
                    "project_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "replacement_path": {"type": "string"},
                },
            },
            handler=_asset_retirement_analyze,
            mutates=False,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.referenced.replace",
            title="Replace Referenced Project Asset",
            description=(
                "Rewrite representable live references to an existing project file and retire the source "
                "into an identity tombstone without changing replacement bytes."
            ),
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "replacement_path": {"type": "string"},
                }
            ),
            handler=_asset_referenced_replace,
            mutates=True,
            undoable=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.undo",
            title="Undo Asset Transaction",
            description="Guardedly undo one durable asset reference transaction.",
            input_schema=_schema({"project_path": {"type": "string"}, "transaction_id": {"type": "string"}}),
            handler=_asset_transaction_undo,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.redo",
            title="Redo Asset Transaction",
            description="Guardedly redo one durable asset reference transaction.",
            input_schema=_schema({"project_path": {"type": "string"}, "transaction_id": {"type": "string"}}),
            handler=_asset_transaction_redo,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.retention.analyze",
            title="Analyze Asset Transaction Retention Policy",
            description="Read-only inventory and conservative retention policy for durable transaction journals and backups.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_transaction_retention_analyze,
            mutates=False,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.prune.plan",
            title="Plan Durable Transaction Artifact Prune",
            description="Read-only exact-bundle prune plan with strict policy, provenance, digest, and confirmation binding.",
            input_schema=_schema({
                "project_path": {"type": "string"},
                "artifact_paths": {"type": "array"},
                "expected_digests": {"type": "object"},
            }),
            handler=_asset_transaction_prune_plan,
            mutates=False,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.prune.apply",
            title="Apply Durable Transaction Artifact Prune",
            description="Irreversibly prune one operator-confirmed durable transaction artifact bundle after fresh Authority validation.",
            input_schema=_schema({
                "project_path": {"type": "string"},
                "artifact_paths": {"type": "array"},
                "expected_digests": {"type": "object"},
                "policy_snapshot_digest": {"type": "string"},
                "operator_confirmation": {"type": "string"},
            }),
            handler=_asset_transaction_prune_apply,
            mutates=True,
            undoable=False,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.inspect",
            title="Inspect Asset Transaction Recovery",
            description="Read digest-grounded recovery facts for one durable asset transaction without mutation.",
            input_schema=_schema({"project_path": {"type": "string"}, "transaction_id": {"type": "string"}}),
            handler=_asset_transaction_inspect,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.recovery.list",
            title="List Asset Transaction Recovery",
            description="List durable asset transaction journals that require explicit operator attention.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_transaction_recovery_list,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.transaction.recovery.resolve",
            title="Resolve Asset Transaction Recovery",
            description="Perform one explicitly safe, no-overwrite asset transaction recovery resolution.",
            input_schema=_schema(
                {
                    "project_path": {"type": "string"},
                    "transaction_id": {"type": "string"},
                    "action": {"type": "string"},
                }
            ),
            handler=_asset_transaction_recovery_resolve,
            mutates=True,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.validate",
            title="Validate Project Assets",
            description="Validate project scene/script/asset references through the shared dependency scanner.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_validate,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.dependencies",
            title="Read Asset Dependencies",
            description="Scan scenes for script and asset dependency edges and missing files.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_dependencies,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.export_closure",
            title="Read Asset Export Closure",
            description="Compute the project file/plugin closure used by player export and Hub risk summaries.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_asset_export_closure,
            capability="vitalloom.lotuspond.runtime",
        ),
        CommandSpec(
            id="asset.apply_to_scene",
            title="Apply Asset To Scene",
            description="Create a scene entity referencing a project asset through the shared command layer.",
            input_schema=_schema(
                {
                    "scene_path": {"type": "string"},
                    "asset_path": {"type": "string"},
                    "entity_id": {"type": "string"},
                }
            ),
            handler=_asset_apply_to_scene,
            mutates=True,
            undoable=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="selection.set",
            title="Set Selection",
            description="Set editor selection from object ids when editor context is active.",
            input_schema={"type": "object", "properties": {"object_ids": {"type": "array"}}},
            handler=_selection_set,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.editor_essentials",
        ),
        CommandSpec(
            id="simulation.transport.status",
            title="Read Simulation Transport Status",
            description="Read the canonical SR simulation transport phase and speed.",
            input_schema={"type": "object", "properties": {}},
            handler=_simulation_transport_status,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="simulation.play",
            title="Play Simulation",
            description="Request SR play through SimulationTransport.",
            input_schema={"type": "object", "properties": {}},
            handler=_simulation_play,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="simulation.toggle",
            title="Toggle Simulation",
            description="Request SR play/pause toggle through SimulationTransport.",
            input_schema={"type": "object", "properties": {}},
            handler=_simulation_toggle,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="simulation.pause",
            title="Pause Simulation",
            description="Request SR pause through SimulationTransport.",
            input_schema={"type": "object", "properties": {}},
            handler=_simulation_pause,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="simulation.stop",
            title="Stop Simulation",
            description="Request SR stop through SimulationTransport.",
            input_schema={"type": "object", "properties": {}},
            handler=_simulation_stop,
            mutates=True,
            requires_gui=True,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="ps.experiment.smoke",
            title="Run PS Experiment Smoke",
            description="Run a short PS experiment without exporting run artifacts.",
            input_schema={
                "type": "object",
                "properties": {
                    "ticks": {"type": "integer"},
                    "seed": {"type": "integer"},
                    "project_path": {"type": "string"},
                },
            },
            handler=_ps_experiment_smoke,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.replay.status",
            title="Read Runtime Replay Status",
            description="Read SR/PS/PS_REPLAY replay evidence without mutating scenes.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "run_dir": {"type": "string"},
                },
            },
            handler=_runtime_replay_status,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.replay.admission_witness",
            title="Read Replay Admission Witness",
            description="Build read-only provenance evidence for a real run artifact without admitting live replay.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "run_dir": {"type": "string"},
                },
                "required": ["run_dir"],
            },
            handler=_runtime_replay_admission_witness,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.status",
            title="Read WorldBridge Status",
            description="Read WorldBridge/unified Pond gate evidence without mutating scenes.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                },
            },
            handler=_runtime_worldbridge_status,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_diagnostic",
            title="Read WorldBridge Quarantine Diagnostic",
            description="Read current WorldBridge quarantine provenance without mutating or restarting runtime state.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_diagnostic,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_lifecycle_correlation",
            title="Read WorldBridge Quarantine Lifecycle Correlation",
            description="Read same-adapter WorldBridge quarantine lifecycle evidence without mutating runtime state.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_lifecycle_correlation,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_operator_presentation",
            title="Present WorldBridge Quarantine Lifecycle Evidence",
            description="Present bounded operator wording for lifecycle evidence without mutation authority.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_operator_presentation,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_operator_presentation_export",
            title="Export WorldBridge Quarantine Operator Evidence",
            description="Build bounded in-memory quarantine operator evidence export without persistence or mutation authority.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_operator_presentation_export,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_operator_presentation_export_audit",
            title="Audit WorldBridge Quarantine Operator Evidence Export",
            description="Audit bounded in-memory quarantine operator evidence without runtime-control authority.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_operator_presentation_export_audit,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.quarantine_operator_evidence_bundle",
            title="Read WorldBridge Quarantine Evidence Bundle",
            description="Consume matched bounded quarantine export/audit evidence without runtime-control authority.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_quarantine_operator_evidence_bundle,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.provenance_receipt",
            title="Read WorldBridge Provenance Receipt",
            description="Read cross-surface WorldBridge provenance evidence without runtime control authority.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_provenance_receipt,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.mapping_audit",
            title="Read WorldBridge Mapping Audit",
            description="Read WorldBridge mapping-loss evidence without mutating scenes.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_mapping_audit,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.component_decision",
            title="Read WorldBridge Component Decision",
            description="Read component/membrane mapping decision evidence without mutating scenes.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_component_decision,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.component_projection",
            title="Read WorldBridge Component Projection",
            description="Read component projection evidence without mutating scenes.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_component_projection,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.worldbridge.component_projection_diagnostics",
            title="Read WorldBridge Component Projection Diagnostics",
            description="Read component projection diagnostic summary without mutating scenes.",
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_worldbridge_component_projection_diagnostics,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.ps.organism_discovery",
            title="Discover Active PS Runtime Organisms",
            description=(
                "Acquire the active opaque PS run and exact current organism "
                "identities without inventing selection semantics."
            ),
            input_schema={"type": "object", "properties": {}},
            handler=_runtime_ps_organism_discovery,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.ps.organism_snapshot",
            title="Read PS Runtime Organism Snapshot",
            description=(
                "Query one live PS organism through an explicit run-scoped identity."
            ),
            input_schema={
                "type": "object",
                "required": ["identity"],
                "properties": {
                    "identity": {"type": "object"},
                },
            },
            handler=_runtime_ps_organism_snapshot,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.ps.organism_component_projection",
            title="Read PS Runtime Organism Component Projection",
            description=(
                "Project strict component facts for one explicitly identified PS "
                "runtime organism without exposing live component objects."
            ),
            input_schema={
                "type": "object",
                "required": ["identity"],
                "properties": {"identity": {"type": "object"}},
            },
            handler=_runtime_ps_organism_component_projection,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.pvaec.simulation",
        ),
        CommandSpec(
            id="runtime.sr.selected_entity_snapshot",
            title="Read Selected SR Runtime Entity Snapshot",
            description=(
                "Resolve the current editor-selected .pond entity to the active "
                "SR epoch and return its read-only snapshot."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "identity": {"type": "object"},
                },
            },
            handler=_runtime_sr_selected_entity_snapshot,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="runtime.sr.selected_entity_component_projection",
            title="Read Selected SR Runtime Entity Component Projection",
            description=(
                "Project attachment-proven component facts for the selected SR "
                "runtime organism without claiming PS component equivalence."
            ),
            input_schema={
                "type": "object",
                "properties": {"identity": {"type": "object"}},
            },
            handler=_runtime_sr_selected_entity_component_projection,
            mutates=False,
            requires_gui=False,
            capability="vitalloom.engine.sr2d",
        ),
        CommandSpec(
            id="capability.list",
            title="List Capability Catalog",
            description="List runtime builtin capability catalog entries.",
            input_schema={"type": "object", "properties": {}},
            handler=_capability_list,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="command.undo",
            title="Undo Last Command",
            description="Undo the last representative undoable command in the current Command Registry session.",
            input_schema={"type": "object", "properties": {}},
            handler=_command_undo,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="command.redo",
            title="Redo Last Command",
            description="Redo the last representative undone command in the current Command Registry session.",
            input_schema={"type": "object", "properties": {}},
            handler=_command_redo,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="command.undo_project",
            title="Undo Latest Project Audit Command",
            description="Undo the latest representative project-scoped command from durable audit history.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_command_undo_project,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="command.redo_project",
            title="Redo Latest Project Audit Undo",
            description="Redo the latest representative durable project undo from audit history.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_command_redo_project,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.list",
            title="List Project Plugins",
            description="List official and project-local Lotus Loom plugins for one project.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_plugin_list,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.resolve",
            title="Resolve Project Plugins",
            description="Compute the project plugin/capability lock suggestion without writing files.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_plugin_resolve,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.enable",
            title="Enable Project Plugin",
            description="Enable one Lotus Loom plugin/capability for the current project.",
            input_schema=_schema(
                {"project_path": {"type": "string"}, "plugin_id": {"type": "string"}}
            ),
            handler=_plugin_enable,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.disable",
            title="Disable Project Plugin",
            description="Disable one Lotus Loom plugin/capability for the current project.",
            input_schema=_schema(
                {"project_path": {"type": "string"}, "plugin_id": {"type": "string"}}
            ),
            handler=_plugin_disable,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.host.inspect",
            title="Inspect Live Plugin Host",
            description="Inspect the current L1 engine plugin's live downstream extension Host without mutation.",
            input_schema={
                "type": "object",
                "required": [],
                "properties": {"project_path": {"type": "string"}},
            },
            handler=_plugin_host_inspect,
            capability="vitalloom.core.platform",
            owner="core.plugin_host",
        ),
        CommandSpec(
            id="plugin.host.recovery.list",
            title="List Plugin Host Recovery",
            description="List confirmation-bound recovery work for the current live downstream extension Host.",
            input_schema={
                "type": "object",
                "required": [],
                "properties": {"project_path": {"type": "string"}},
            },
            handler=_plugin_host_recovery_list,
            capability="vitalloom.core.platform",
            owner="core.plugin_host",
        ),
        CommandSpec(
            id="plugin.host.recovery.resolve",
            title="Resolve Plugin Host Recovery",
            description="Retry the normal project lifecycle only after exact project/report/action confirmation.",
            input_schema={
                "type": "object",
                "required": ["project_path", "report_id", "action", "operator_confirmation"],
                "properties": {
                    "project_path": {"type": "string"},
                    "report_id": {"type": "string"},
                    "action": {"type": "string"},
                    "operator_confirmation": {"type": "string"},
                },
            },
            handler=_plugin_host_recovery_resolve,
            mutates=True,
            undoable=False,
            requires_gui=False,
            capability="vitalloom.core.platform",
            owner="core.plugin_host",
        ),
        CommandSpec(
            id="package.transaction.inspect",
            title="Inspect Package Transaction",
            description="Inspect one durable package transaction receipt without mutation.",
            input_schema=_schema({"project_path": {"type": "string"}, "transaction_id": {"type": "string"}}),
            handler=_package_transaction_inspect,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="package.transaction.recovery.list",
            title="List Package Transaction Recovery",
            description="List package transaction receipts requiring operator attention without mutation.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_package_transaction_recovery_list,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="package.transaction.recovery.resolve",
            title="Resolve Package Transaction Recovery",
            description="Perform one confirmation-bound, fail-closed package transaction recovery action.",
            input_schema={
                "type": "object",
                "required": ["project_path", "transaction_id", "action", "operator_confirmation"],
                "properties": {
                    "project_path": {"type": "string"},
                    "transaction_id": {"type": "string"},
                    "action": {"type": "string"},
                    "operator_confirmation": {"type": "string"},
                },
            },
            handler=_package_transaction_recovery_resolve,
            mutates=True,
            capability="vitalloom.core.platform",
        ),        CommandSpec(
            id="plugin.install",
            title="Install Project Plugin",
            description="Record a project-level plugin install from official catalog, project addon, workspace extension, or external path.",
            input_schema={
                "type": "object",
                "required": ["project_path", "plugin_id"],
                "properties": {
                    "project_path": {"type": "string"},
                    "plugin_id": {"type": "string"},
                    "source": {"type": "string"},
                    "path": {"type": "string"},
                    "version": {"type": "string"},
                },
            },
            handler=_plugin_install,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="plugin.uninstall",
            title="Uninstall Project Plugin",
            description="Remove one project-level plugin install or requirement from the current project.",
            input_schema=_schema(
                {"project_path": {"type": "string"}, "plugin_id": {"type": "string"}}
            ),
            handler=_plugin_uninstall,
            mutates=True,
            capability="vitalloom.core.platform",
        ),
        CommandSpec(
            id="export.player.prepare",
            title="Prepare Player Export Closure",
            description="Read the current project plugin/resource closure used by player export.",
            input_schema=_schema({"project_path": {"type": "string"}}),
            handler=_export_player_prepare,
            capability="vitalloom.core.platform",
        ),
    ]


def _schema(properties: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {"type": "object", "required": list(properties.keys()), "properties": dict(properties)}


def _workspace_root() -> Path:
    from core.VitaLoom.core.bundle_paths import application_root

    return application_root() / "workspace"


def _resolve_workspace_path(raw: str, *, must_exist: bool = True) -> Path | None:
    try:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            from core.VitaLoom.core.bundle_paths import application_root

            path = application_root() / path
        path = path.resolve()
        workspace = _workspace_root().resolve()
        if path != workspace and workspace not in path.parents:
            return None
        if must_exist and not path.exists():
            return None
        return path
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _json_safe(value: Any) -> Any:
    """Return a detached JSON-compatible value for scene audit and restore paths."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _project_root_for_scene(scene: Path) -> Path | None:
    try:
        parent = scene.resolve().parent
        if parent.name != "scenes":
            return None
        project = parent.parent
        if (project / "project.json").is_file():
            return project
    except OSError:
        return None
    return None


def _read_scene_from_payload(payload: Mapping[str, Any]) -> tuple[Path | None, dict[str, Any]]:
    scene = _scene_path_from_payload(payload)
    if scene is None or not scene.is_file() or scene.suffix != ".pond":
        return None, {}
    return scene, _read_json(scene)


def _scene_entities(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("entities")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _find_entity(entities: list[dict[str, Any]], entity_id: str) -> dict[str, Any] | None:
    for ent in entities:
        if str(ent.get("id", "")) == entity_id:
            return ent
    return None


def _touch_modified_at(data: dict[str, Any]) -> None:
    from datetime import datetime

    data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _set_nested_property(target: dict[str, Any], property_path: str, value: Any) -> Any:
    if property_path.startswith(".") or property_path.endswith(".") or ".." in property_path:
        raise ValueError("invalid property path")
    parts = [part for part in property_path.split(".") if part]
    if not parts:
        raise ValueError("invalid property path")
    current: dict[str, Any] = target
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    key = parts[-1]
    old = current.get(key)
    current[key] = value
    return old


def _duplicate_entity_ids(entities: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for ent in entities:
        entity_id = str(ent.get("id", "")).strip()
        if not entity_id:
            continue
        if entity_id in seen:
            dupes.add(entity_id)
        seen.add(entity_id)
    return sorted(dupes)


def _project_relative_path(project: Path, raw: str) -> str:
    path = Path(raw)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(project.resolve())).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")
    return raw.replace("\\", "/")


def _resolve_project_file(project: Path, raw: str, *, must_exist: bool = True) -> Path | None:
    path = Path(raw)
    if not path.is_absolute():
        path = project / path
    try:
        resolved = path.resolve()
        project_root = project.resolve()
    except OSError:
        return None
    if resolved != project_root and project_root not in resolved.parents:
        return None
    if must_exist and not resolved.is_file():
        return None
    return resolved


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_state(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    project_json = project / "project.json"
    if not project_json.is_file():
        return command_error("project_not_found", "project.json not found")
    data = _read_json(project_json)
    active_scene = str(data.get("active_scene", "") or "")
    scene_path = project / "scenes" / active_scene if active_scene else None
    lock_path = project / "project.lock.json"
    result = {
        "project_path": str(project),
        "name": data.get("name"),
        "version": data.get("version"),
        "active_scene": active_scene,
        "active_scene_exists": bool(scene_path and scene_path.is_file()),
        "project_lock_exists": lock_path.is_file(),
        "capabilities": data.get("capabilities") if isinstance(data.get("capabilities"), list) else [],
        "required_packages": data.get("required_packages")
        if isinstance(data.get("required_packages"), list)
        else [],
    }
    if lock_path.is_file():
        lock = _read_json(lock_path)
        result["resolved_product"] = lock.get("resolved_product")
        result["resolved_capabilities"] = lock.get("resolved_capabilities")
    try:
        from core.VitaLoom.core.bundle_paths import resource_root
        from core.VitaLoom.suite.project_lock import resolve_project_runtime

        resolved = resolve_project_runtime(project, repo_root=resource_root())
        result["lock_status"] = resolved.lock_status_text
        result["lock_admission"] = resolved.lock_admission_code
        result["blocking_issue_codes"] = list(resolved.blocking_issue_codes)
        result["lock_error"] = resolved.lock_error
        result["blocking_issue_summary"] = resolved.blocking_issue_summary
    except Exception as exc:
        result["lock_status"] = "锁无效"
        result["lock_admission"] = "invalid"
        result["blocking_issue_codes"] = ["invalid"]
        result["lock_error"] = str(exc)
    return command_ok(result)


def _project_open(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")

    host = context.get("project_world_open_host")
    previous_project_path = str(context.get("previous_project_path", "") or "")
    if host is not None:
        current_path = getattr(host, "current_project_world_path", None)
        if callable(current_path):
            try:
                previous_project_path = str(current_path() or "")
            except Exception:
                previous_project_path = ""

    from core.VitaLoom.core.bundle_paths import resource_root
    from core.VitaLoom.project.project_world_open import prepare_project_world_open

    preparation = prepare_project_world_open(
        project,
        previous_project_path=previous_project_path or None,
        repo_root=resource_root(),
    )
    if preparation.get("status") != "ready":
        return command_error(
            str(preparation.get("code", "project_open_blocked") or "project_open_blocked"),
            str(preparation.get("message", "Project World open was blocked") or ""),
            details={"preparation": preparation},
        )

    apply_open = getattr(host, "apply_project_world_open", None) if host is not None else None
    if not callable(apply_open):
        return command_error(
            "project_host_adapter_unavailable",
            "project.open requires an explicit project_world_open_host capability",
            details={"preparation": preparation},
        )
    try:
        raw_report = apply_open(preparation)
    except Exception as exc:
        return command_error(
            "project_host_adapter_exception",
            f"{type(exc).__name__}: {exc}",
            details={"preparation": preparation},
        )
    if not isinstance(raw_report, Mapping):
        return command_error(
            "project_host_adapter_invalid_report",
            "project_world_open_host must return a mapping report",
            details={"preparation": preparation},
        )
    report = dict(raw_report)
    status = str(report.get("status", "") or "")
    if status in {"opened", "opened_with_warnings"}:
        return command_ok(report, events=["project_opened"])
    return command_error(
        str(report.get("code", "project_open_failed") or "project_open_failed"),
        str(report.get("message", "Project World Host application failed") or ""),
        details={"preparation": preparation, "report": report},
    )


def _project_create(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        return command_error("invalid_project_name", "name is required")
    raw_path = str(payload.get("project_path", "") or "").strip()
    if raw_path:
        project = _resolve_workspace_path(raw_path, must_exist=False)
        if project is None:
            return command_error("path_outside_workspace", "Project path must be under workspace/")
    else:
        from core.VitaLoom.core.bundle_paths import user_projects_root
        project = user_projects_root() / name
    from core.VitaLoom.core.bundle_paths import resource_root
    from core.VitaLoom.project.project_world_creation import (
        ProjectWorldCreationError,
        create_project_world,
    )
    try:
        created = create_project_world(
            name,
            project,
            template=str(payload.get("template", "") or "") or None,
            templates_dir=resource_root() / "templates",
            description=str(payload.get("description", "") or ""),
            project_type=str(payload.get("project_type", "") or payload.get("template", "") or "sr2d"),
            repo_root=resource_root(),
        )
    except ProjectWorldCreationError as exc:
        return command_error(exc.code, str(exc))
    except Exception as exc:
        return command_error("project_create_failed", f"{type(exc).__name__}: {exc}")
    project = Path(created["project_path"])
    data = _read_json(project / "project.json")
    active_scene = str(data.get("active_scene", "") or "")
    return command_ok({"project_path": str(project),"project_type": data.get("project_type", ""),"required_capabilities": data.get("required_capabilities", {}),"project_json_exists": (project / "project.json").is_file(),"project_lock_exists": (project / "project.lock.json").is_file(),"active_scene": active_scene,"active_scene_exists": bool(active_scene and (project / "scenes" / active_scene).is_file()),"lock_error": created.get("lock_error", "")}, events=["project_created"])


def _project_lock_check(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    lock_path = project / "project.lock.json"
    from core.VitaLoom.core.bundle_paths import resource_root
    from core.VitaLoom.suite.project_lock import resolve_project_runtime

    try:
        resolved = resolve_project_runtime(project, repo_root=resource_root())
    except Exception as exc:
        return command_ok(
            {
                "exists": lock_path.is_file(),
                "valid": False,
                "lock_status": "锁无效",
                "lock_admission": "invalid",
                "blocking_issue_codes": ["invalid"],
                "lock_error": str(exc),
            },
            warnings=[str(exc)],
        )
    product = {
        "id": resolved.product_id,
        "version": resolved.product_version,
    }
    warnings: list[str] = []
    if resolved.lock_missing:
        warnings.append("project.lock.json missing")
    if resolved.blocking_issue_summary:
        warnings.append(resolved.blocking_issue_summary)
    return command_ok(
        {
            "exists": lock_path.is_file(),
            "valid": bool(lock_path.is_file() and not resolved.has_blocking_issues),
            "resolved_product": product,
            "lock_status": resolved.lock_status_text,
            "lock_admission": resolved.lock_admission_code,
            "blocking_issue_codes": list(resolved.blocking_issue_codes),
            "lock_error": resolved.lock_error,
            "blocking_issue_summary": resolved.blocking_issue_summary,
        },
        warnings=warnings,
    )


def _project_set_active_scene(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Persist one project-local active scene without opening it in a host.

    The manifest is the sole authority here.  UI adapters may explicitly open
    the selected scene after a successful direct command, but history replay
    must never cause a SceneManager to rewrite this project contract.
    """
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    if "expected_project" in payload:
        expected_project = payload.get("expected_project")
        if not isinstance(expected_project, Mapping):
            return command_error("invalid_expected_project", "expected_project must be an object")
        expected_project = _json_safe(dict(expected_project))
        actual_project = _json_safe(data)
        if actual_project != expected_project:
            return command_error(
                "stale_project_active_scene",
                "Project manifest no longer matches the expected canonical state",
                details={"expected_project": expected_project, "actual_project": actual_project},
            )
    scene = _resolve_workspace_path(str(payload.get("scene_path", "")))
    if scene is None or not scene.is_file() or scene.suffix != ".pond":
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    scenes_dir = (project / "scenes").resolve()
    try:
        active_scene = str(scene.resolve().relative_to(scenes_dir)).replace("\\", "/")
    except ValueError:
        return command_error("scene_outside_project", "Scene must live under the current project's scenes/")

    previous_active_scene_present = "active_scene" in data
    previous_active_scene_value = (
        _json_safe(data.get("active_scene")) if previous_active_scene_present else None
    )
    data["active_scene"] = active_scene
    _write_project(project, data)

    # ``load_scene`` was accepted by older UI callers. It is intentionally
    # ignored so this canonical manifest command has no host-side authority.
    return command_ok(
        {
            "project_path": str(project),
            "scene_path": str(scene),
            "active_scene": active_scene,
            "scene_loaded": False,
            "history_previous_active_scene_present": previous_active_scene_present,
            "history_previous_active_scene_value": previous_active_scene_value,
            "history_undo_expected_project": _json_safe(data),
            "history_rehydrate_scene": False,
        },
        events=["active_scene_changed"],
    )


def _project_restore_active_scene_snapshot(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    """Restore an exact active-scene key snapshot behind a full-manifest guard."""
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    expected_project = payload.get("expected_project")
    if not isinstance(expected_project, Mapping):
        return command_error("invalid_expected_project", "expected_project must be an object")
    expected_project = _json_safe(dict(expected_project))
    actual_project = _json_safe(data)
    if actual_project != expected_project:
        return command_error(
            "stale_project_active_scene",
            "Project manifest no longer matches the expected canonical state",
            details={"expected_project": expected_project, "actual_project": actual_project},
        )
    restore_active_scene_present = payload.get("restore_active_scene_present")
    if not isinstance(restore_active_scene_present, bool):
        return command_error(
            "invalid_restore_active_scene_present",
            "restore_active_scene_present must be a boolean",
        )
    if restore_active_scene_present:
        data["active_scene"] = _json_safe(payload.get("restore_active_scene_value"))
    else:
        data.pop("active_scene", None)
    _write_project(project, data)
    return command_ok(
        {
            "project_path": str(project),
            "active_scene_present": restore_active_scene_present,
            "active_scene": _json_safe(data.get("active_scene")) if restore_active_scene_present else None,
            "history_redo_expected_project": _json_safe(data),
            "history_rehydrate_scene": False,
        },
        events=["active_scene_snapshot_restored"],
    )

def _project_for_contract_command(payload: Mapping[str, Any]) -> tuple[Path | None, dict[str, Any] | None]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return None, None
    project_json = project / "project.json"
    if not project_json.is_file():
        return project, None
    return project, _read_json(project_json)


def _project_set_ps_experiment_preset(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    if "expected_project" in payload:
        expected_project = payload.get("expected_project")
        if not isinstance(expected_project, Mapping):
            return command_error("invalid_expected_project", "expected_project must be an object")
        expected_project = _json_safe(dict(expected_project))
        actual_project = _json_safe(data)
        if actual_project != expected_project:
            return command_error(
                "stale_project_ps_experiment_preset",
                "Project manifest no longer matches the expected canonical state",
                details={"expected_project": expected_project, "actual_project": actual_project},
            )
    preset_path = str(payload.get("preset_path", "") or "").strip()
    if not preset_path:
        return command_error("invalid_preset_path", "preset_path is required")

    previous_preset_present = "ps_experiment_preset" in data
    previous_preset_value = _json_safe(data.get("ps_experiment_preset")) if previous_preset_present else None
    data["ps_experiment_preset"] = preset_path.replace("\\", "/")
    _write_project(project, data)
    return command_ok(
        {
            "project_path": str(project),
            "ps_experiment_preset": data["ps_experiment_preset"],
            "history_previous_preset_present": previous_preset_present,
            "history_previous_preset_value": previous_preset_value,
            "history_undo_expected_project": _json_safe(data),
        },
        events=["ps_experiment_preset_changed"],
    )


def _project_restore_ps_experiment_preset_snapshot(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    expected_project = payload.get("expected_project")
    if not isinstance(expected_project, Mapping):
        return command_error("invalid_expected_project", "expected_project must be an object")
    expected_project = _json_safe(dict(expected_project))
    actual_project = _json_safe(data)
    if actual_project != expected_project:
        return command_error(
            "stale_project_ps_experiment_preset",
            "Project manifest no longer matches the expected canonical state",
            details={"expected_project": expected_project, "actual_project": actual_project},
        )
    restore_preset_present = payload.get("restore_preset_present")
    if not isinstance(restore_preset_present, bool):
        return command_error("invalid_restore_preset_present", "restore_preset_present must be a boolean")
    if restore_preset_present:
        data["ps_experiment_preset"] = _json_safe(payload.get("restore_preset_value"))
    else:
        data.pop("ps_experiment_preset", None)
    _write_project(project, data)
    return command_ok(
        {
            "project_path": str(project),
            "ps_experiment_preset_present": restore_preset_present,
            "ps_experiment_preset": _json_safe(data.get("ps_experiment_preset")) if restore_preset_present else None,
            "history_redo_expected_project": _json_safe(data),
        },
        events=["ps_experiment_preset_snapshot_restored"],
    )


def _project_set_evolution_defaults(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    if "expected_project" in payload:
        expected_project = payload.get("expected_project")
        if not isinstance(expected_project, Mapping):
            return command_error("invalid_expected_project", "expected_project must be an object")
        expected_project = _json_safe(dict(expected_project))
        actual_project = _json_safe(data)
        if actual_project != expected_project:
            return command_error(
                "stale_project_evolution_defaults",
                "Project manifest no longer matches the expected canonical state",
                details={"expected_project": expected_project, "actual_project": actual_project},
            )
    defaults = payload.get("defaults")
    if not isinstance(defaults, Mapping):
        return command_error("invalid_evolution_defaults", "defaults must be an object")

    previous_defaults_present = "evolution_defaults" in data
    previous_defaults_value = (
        _json_safe(data.get("evolution_defaults")) if previous_defaults_present else None
    )
    data["evolution_defaults"] = _json_safe(dict(defaults))
    _write_project(project, data)
    return command_ok(
        {
            "project_path": str(project),
            "evolution_defaults": _json_safe(data["evolution_defaults"]),
            "history_previous_defaults_present": previous_defaults_present,
            "history_previous_defaults_value": previous_defaults_value,
            "history_undo_expected_project": _json_safe(data),
        },
        events=["evolution_defaults_changed"],
    )


def _project_restore_evolution_defaults_snapshot(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    project, data = _project_for_contract_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    expected_project = payload.get("expected_project")
    if not isinstance(expected_project, Mapping):
        return command_error("invalid_expected_project", "expected_project must be an object")
    expected_project = _json_safe(dict(expected_project))
    actual_project = _json_safe(data)
    if actual_project != expected_project:
        return command_error(
            "stale_project_evolution_defaults",
            "Project manifest no longer matches the expected canonical state",
            details={"expected_project": expected_project, "actual_project": actual_project},
        )
    restore_defaults_present = payload.get("restore_defaults_present")
    if not isinstance(restore_defaults_present, bool):
        return command_error("invalid_restore_defaults_present", "restore_defaults_present must be a boolean")
    if restore_defaults_present:
        data["evolution_defaults"] = _json_safe(payload.get("restore_defaults_value"))
    else:
        data.pop("evolution_defaults", None)
    _write_project(project, data)
    return command_ok(
        {
            "project_path": str(project),
            "evolution_defaults_present": restore_defaults_present,
            "evolution_defaults": _json_safe(data.get("evolution_defaults"))
            if restore_defaults_present
            else None,
            "history_redo_expected_project": _json_safe(data),
        },
        events=["evolution_defaults_snapshot_restored"],
    )


def _scene_path_from_payload(payload: Mapping[str, Any]) -> Path | None:
    raw_scene = str(payload.get("scene_path", "") or "")
    if raw_scene:
        return _resolve_workspace_path(raw_scene)
    raw_project = str(payload.get("project_path", "") or "")
    project = _resolve_workspace_path(raw_project)
    if project is None:
        return None
    project_json = project / "project.json"
    if not project_json.is_file():
        return None
    active = str(_read_json(project_json).get("active_scene", "") or "")
    if not active:
        return None
    return (project / "scenes" / active).resolve()


def _scene_summary(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene = _scene_path_from_payload(payload)
    if scene is None or not scene.is_file() or scene.suffix != ".pond":
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    data = _read_json(scene)
    entities = data.get("entities") if isinstance(data.get("entities"), list) else []
    components = data.get("components") if isinstance(data.get("components"), list) else []
    scripts = 0
    for ent in entities:
        if isinstance(ent, dict) and isinstance(ent.get("scripts"), list):
            scripts += len(ent["scripts"])
    return command_ok(
        {
            "scene_path": str(scene),
            "name": data.get("name") or scene.stem,
            "entity_count": len(entities),
            "component_count": len(components),
            "script_count": scripts,
            "pond_config": data.get("pond_config") if isinstance(data.get("pond_config"), dict) else {},
        }
    )


def _scene_open(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene = _scene_path_from_payload(payload)
    if scene is None or not scene.is_file() or scene.suffix != ".pond":
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    from core.VitaLoom.scene.scene_manager import get_scene_manager

    ok = get_scene_manager().load_scene(str(scene))
    if not ok:
        return command_error("scene_open_failed", "SceneManager.load_scene returned False")
    return command_ok({"scene_path": str(scene)}, events=["scene_loaded"])


def _scene_save(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Persist an explicit project-local snapshot without touching a UI host.

    Direct saves retain the legacy timestamp-touch behavior.  Guarded history
    replays carry the already-canonical snapshot and explicitly preserve its
    ``modified_at`` value so redo is an exact snapshot transition rather than a
    new save with timestamp drift.
    """
    from core.VitaLoom.scene.scene_persistence import (
        ScenePersistenceError,
        persist_project_scene_snapshot,
    )

    raw_data = payload.get("data")
    if not isinstance(raw_data, Mapping):
        return command_error("invalid_scene_data", "data must be an object")
    scene_data = dict(raw_data)
    if not bool(payload.get("history_preserve_modified_at", False)):
        # Preserve the legacy save contract while keeping the mutation detached
        # from both caller-owned data and the UI-host SceneManager.
        scene_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_expected = payload.get("expected_scene")
    if raw_expected is not None and not isinstance(raw_expected, Mapping):
        return command_error("invalid_expected_scene", "expected_scene must be an object")
    try:
        persisted = persist_project_scene_snapshot(
            str(payload.get("scene_path", "")),
            scene_data,
            expected_scene=raw_expected,
        )
    except ScenePersistenceError as exc:
        return command_error(exc.code, str(exc))
    return command_ok(
        {
            "scene_path": persisted["scene_path"],
            "project_path": persisted["project_path"],
            "previous_scene": persisted["previous_scene"],
            "scene_data": persisted["scene_data"],
            "history_undo_expected_scene": persisted["scene_data"],
            "history_rehydrate_scene": False,
            "history_sync_host_scene": True,
        },
        events=["scene_saved"],
    )


def _scene_restore_snapshot(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Restore one exact canonical scene snapshot after a terminal stale guard."""
    from core.VitaLoom.scene.scene_persistence import (
        ScenePersistenceError,
        persist_project_scene_snapshot,
    )

    restore_scene = payload.get("restore_scene")
    expected_scene = payload.get("expected_scene")
    if not isinstance(restore_scene, Mapping):
        return command_error("invalid_restore_scene", "restore_scene must be an object")
    if not isinstance(expected_scene, Mapping):
        return command_error("invalid_expected_scene", "expected_scene must be an object")
    try:
        persisted = persist_project_scene_snapshot(
            str(payload.get("scene_path", "")),
            restore_scene,
            expected_scene=expected_scene,
        )
    except ScenePersistenceError as exc:
        return command_error(exc.code, str(exc))
    return command_ok(
        {
            "scene_path": persisted["scene_path"],
            "project_path": persisted["project_path"],
            "previous_scene": persisted["previous_scene"],
            "scene_data": persisted["scene_data"],
            "history_redo_expected_scene": persisted["scene_data"],
            "history_rehydrate_scene": False,
            "history_sync_host_scene": True,
        },
        events=["scene_snapshot_restored"],
    )


def _scene_validate(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    project = _project_root_for_scene(scene)
    if project is None:
        return command_error("project_not_found", "Scene must belong to a project with project.json")
    index = _project_asset_index(project)
    scene_label = str(scene.relative_to(project)).replace("\\", "/")
    edges = [edge for edge in index["dependencies"]["edges"] if edge.get("scene") == scene_label]
    missing_scripts = sorted(
        {edge["target"] for edge in edges if edge.get("kind") == "script" and edge.get("status") == "missing"}
    )
    missing_assets = sorted(
        {edge["target"] for edge in edges if edge.get("kind") == "asset" and edge.get("status") == "missing"}
    )
    outside_project = sorted({edge["raw_ref"] for edge in edges if edge.get("status") == "outside_project"})
    invalid_references = sorted({edge["raw_ref"] for edge in edges if edge.get("status") == "invalid"})
    duplicate_ids = _duplicate_entity_ids(_scene_entities(data))
    return command_ok(
        {
            "scene_path": str(scene),
            "index_revision": index["index_revision"],
            "valid": not duplicate_ids and not missing_scripts and not missing_assets and not outside_project and not invalid_references,
            "duplicate_entity_ids": duplicate_ids,
            "missing_scripts": missing_scripts,
            "missing_assets": missing_assets,
            "outside_project": outside_project,
            "invalid_references": invalid_references,
            "dependency_edges": edges,
        }
    )


def _entity_create(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity = payload.get("entity")
    if not isinstance(entity, Mapping):
        return command_error("invalid_entity", "entity must be an object")
    ent = _json_safe(dict(entity))
    entity_id = str(ent.get("id", "")).strip()
    if not entity_id:
        return command_error("invalid_entity", "entity.id is required")
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        raw_entities = []
    raw_connections = data.get("connections")
    canonical_connections = raw_connections if isinstance(raw_connections, list) else []
    if "expected_entities" in payload:
        expected_entities = payload.get("expected_entities")
        if not isinstance(expected_entities, list):
            return command_error("invalid_expected_entities", "expected_entities must be a list")
        actual_entities = _json_safe(raw_entities)
        expected_entities = _json_safe(expected_entities)
        if actual_entities != expected_entities:
            return command_error(
                "stale_entity_create_scene",
                "Entity list no longer matches the expected canonical state",
                details={"expected_entities": expected_entities, "actual_entities": actual_entities},
            )
    if "expected_connections" in payload:
        expected_connections = payload.get("expected_connections")
        if not isinstance(expected_connections, list):
            return command_error("invalid_expected_connections", "expected_connections must be a list")
        actual_connections = _json_safe(canonical_connections)
        expected_connections = _json_safe(expected_connections)
        if actual_connections != expected_connections:
            return command_error(
                "stale_entity_create_scene",
                "Connection list no longer matches the expected canonical state",
                details={"expected_connections": expected_connections, "actual_connections": actual_connections},
            )
    if _find_entity(raw_entities, entity_id) is not None:
        return command_error("entity_id_exists", f"Entity already exists: {entity_id}")
    requested_index = payload.get("entity_index")
    if requested_index is None:
        entity_index = len(raw_entities)
    elif not isinstance(requested_index, int) or isinstance(requested_index, bool):
        return command_error("invalid_entity_index", "entity_index must be an integer")
    elif requested_index < 0 or requested_index > len(raw_entities):
        return command_error("entity_index_out_of_range", "entity_index must address the current entity list")
    else:
        entity_index = requested_index
    preserve_entity_snapshot = payload.get("preserve_entity_snapshot", False)
    if not isinstance(preserve_entity_snapshot, bool):
        return command_error(
            "invalid_preserve_entity_snapshot",
            "preserve_entity_snapshot must be a boolean",
        )
    ent["id"] = entity_id
    if not preserve_entity_snapshot:
        ent.setdefault("name", entity_id)
        ent.setdefault("type", "game_prop")
        ent.setdefault("position", [0.0, 0.0])
        ent.setdefault("radius", 12.0)
        ent.setdefault("scripts", [])
    if not isinstance(data.get("entities"), list):
        data["entities"] = raw_entities
    raw_entities.insert(entity_index, ent)
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {"scene_path": str(scene), "entity_id": entity_id, "entity": ent, "entity_index": entity_index},
        events=["entity_created"],
    )


def _entity_set_property(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    prop_path = str(payload.get("property_path", "")).strip()
    if not prop_path:
        return command_error("invalid_property_path", "property_path is required")
    ent = _find_entity(_scene_entities(data), entity_id)
    if ent is None:
        return command_error("entity_not_found", f"Entity not found: {entity_id}")
    previous_entity = _json_safe(ent)
    value = payload.get("value")
    old = _set_nested_property(ent, prop_path, value)
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "entity_id": entity_id,
            "property_path": prop_path,
            "old_value": old,
            "new_value": value,
            "previous_entity": previous_entity,
        },
        events=["entity_property_set"],
    )


def _memory_collection_snapshot(target: Any) -> list[dict[str, Any]] | None:
    """Serialize a MemorySystem collection without retaining live objects."""

    memories = getattr(target, "memories", None)
    if not isinstance(memories, list):
        return None
    records: list[dict[str, Any]] = []
    for memory in memories:
        snapshot = _memory_snapshot(memory)
        if snapshot is None:
            return None
        snapshot["strength"] = _json_safe(getattr(memory, "strength", 1.0))
        snapshot["age"] = _json_safe(getattr(memory, "age", 0))
        records.append(snapshot)
    return records


def _memory_collection_equal(left: Any, right: Any) -> bool:
    return (
        isinstance(left, list)
        and isinstance(right, list)
        and _json_safe(left) == _json_safe(right)
    )


def _memory_restore_collection(target: Any, records: list[Mapping[str, Any]]) -> None:
    """Restore collection state while preserving list identity where possible."""

    memories = getattr(target, "memories", None)
    if not isinstance(memories, list):
        raise TypeError("memory target does not expose a memories list")
    from core.Lotucosm.memory import MemoryGene

    restored: list[Any] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError("memory collection records must be objects")
        required = ("situation", "action_pattern", "success_rate")
        if any(key not in record for key in required):
            raise ValueError("memory collection record is incomplete")
        if not isinstance(record["situation"], str) or not isinstance(record["action_pattern"], Mapping):
            raise TypeError("memory collection record has invalid editable fields")
        if index < len(memories) and memories[index].__class__ is MemoryGene:
            memory = memories[index]
            _memory_apply_snapshot(memory, record)
        else:
            memory = MemoryGene(
                record["situation"],
                dict(record["action_pattern"]),
                record["success_rate"],
            )
        if "strength" in record:
            setattr(memory, "strength", record["strength"])
        if "age" in record:
            setattr(memory, "age", record["age"])
        restored.append(memory)
    memories[:] = restored


def _memory_store(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Guarded atomic store for explicit MemoryEditor import operations."""

    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    token = str(payload.get("target_token", "")).strip()
    expected = payload.get("expected_memories")
    entry = payload.get("memory_entry")
    if not token:
        return command_error("invalid_target_token", "target_token is required")
    if not isinstance(expected, list) or not isinstance(entry, Mapping):
        return command_error("invalid_memory_collection", "expected_memories must be an array and memory_entry an object")
    target = registry.resolve_transient_target(token)
    if target is None:
        return command_error("transient_memory_system_not_found", "Transient memory system is no longer bound")
    actual = _memory_collection_snapshot(target)
    if actual is None:
        return command_error("memory_system_invalid", "Transient target is not an editable memory system")
    if not _memory_collection_equal(actual, expected):
        return command_error("stale_memory_system", "Memory system changed outside this command history")
    try:
        target.store(dict(entry))
    except Exception as exc:
        try:
            _memory_restore_collection(target, actual)
        except Exception:
            pass
        return command_error("memory_store_failed", str(exc))
    updated = _memory_collection_snapshot(target)
    if updated is None:
        try:
            _memory_restore_collection(target, actual)
        except Exception:
            pass
        return command_error("memory_system_invalid", "Stored memory system cannot be read")
    return command_ok(
        {
            "target_token": token,
            "old_memories": actual,
            "new_memories": updated,
        },
        events=["memory_stored"],
    )


def _memory_snapshot(target: Any) -> dict[str, Any] | None:
    """Read the stable editable MemoryGene fields without mutating the target."""

    try:
        situation = getattr(target, "situation")
        action_pattern = getattr(target, "action_pattern")
        success_rate = getattr(target, "success_rate")
    except AttributeError:
        return None
    if not isinstance(action_pattern, Mapping):
        return None
    return {
        "situation": str(situation),
        "action_pattern": _json_safe(dict(action_pattern)),
        "success_rate": _json_safe(success_rate),
    }


def _memory_snapshot_equal(left: Any, right: Any) -> bool:
    return isinstance(left, Mapping) and isinstance(right, Mapping) and _json_safe(dict(left)) == _json_safe(dict(right))


def _memory_apply_snapshot(target: Any, snapshot: Mapping[str, Any]) -> None:
    """Apply one validated snapshot atomically for the in-memory MemoryGene shape."""

    required = ("situation", "action_pattern", "success_rate")
    if any(key not in snapshot for key in required):
        raise ValueError("memory snapshot requires situation, action_pattern, and success_rate")
    if not isinstance(snapshot["situation"], str):
        raise TypeError("memory situation must be a string")
    if not isinstance(snapshot["action_pattern"], Mapping):
        raise TypeError("memory action_pattern must be an object")
    # Validate all values and attributes before the first write. MemoryGene uses
    # plain attributes, but the rollback keeps this contract safe for adapters.
    old = _memory_snapshot(target)
    if old is None:
        raise AttributeError("target is not an editable memory")
    new = {
        "situation": snapshot["situation"],
        "action_pattern": _json_safe(dict(snapshot["action_pattern"])),
        "success_rate": _json_safe(snapshot["success_rate"]),
    }
    try:
        setattr(target, "situation", new["situation"])
        setattr(target, "action_pattern", new["action_pattern"])
        setattr(target, "success_rate", new["success_rate"])
    except Exception:
        try:
            setattr(target, "situation", old["situation"])
            setattr(target, "action_pattern", old["action_pattern"])
            setattr(target, "success_rate", old["success_rate"])
        except Exception:
            pass
        raise


def _memory_restore(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Guardedly restore a transient MemorySystem collection for history undo."""

    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    token = str(payload.get("target_token", "")).strip()
    expected = payload.get("expected_memories")
    memories = payload.get("memories")
    if not token:
        return command_error("invalid_target_token", "target_token is required")
    if not isinstance(expected, list) or not isinstance(memories, list):
        return command_error("invalid_memory_collection", "memory snapshots must be arrays")
    target = registry.resolve_transient_target(token)
    if target is None:
        return command_error("transient_memory_system_not_found", "Transient memory system is no longer bound")
    actual = _memory_collection_snapshot(target)
    if actual is None:
        return command_error("memory_system_invalid", "Transient target is not an editable memory system")
    if not _memory_collection_equal(actual, expected):
        return command_error("stale_memory_system", "Memory system changed outside this command history")
    try:
        _memory_restore_collection(target, memories)
    except Exception as exc:
        try:
            _memory_restore_collection(target, actual)
        except Exception:
            pass
        return command_error("memory_restore_failed", str(exc))
    updated = _memory_collection_snapshot(target)
    if updated is None or not _memory_collection_equal(updated, memories):
        try:
            _memory_restore_collection(target, actual)
        except Exception:
            pass
        return command_error("memory_system_invalid", "Restored memory system cannot be verified")
    return command_ok(
        {
            "target_token": token,
            "old_memories": actual,
            "new_memories": updated,
        },
        events=["memory_restored"],
    )


def _memory_edit(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Guarded atomic edit for one transient MemoryGene target."""

    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    token = str(payload.get("target_token", "")).strip()
    expected = payload.get("expected_snapshot")
    snapshot = payload.get("snapshot")
    if not token:
        return command_error("invalid_target_token", "target_token is required")
    if not isinstance(expected, Mapping) or not isinstance(snapshot, Mapping):
        return command_error("invalid_memory_snapshot", "memory snapshots must be objects")
    target = registry.resolve_transient_target(token)
    if target is None:
        return command_error("transient_memory_not_found", "Transient memory target is no longer bound")
    actual = _memory_snapshot(target)
    if actual is None:
        return command_error("memory_target_invalid", "Transient target is not an editable memory")
    if not _memory_snapshot_equal(actual, expected):
        return command_error(
            "stale_memory",
            "Memory changed outside this command history",
        )
    try:
        _memory_apply_snapshot(target, snapshot)
    except Exception as exc:
        return command_error("memory_write_failed", str(exc))
    updated = _memory_snapshot(target)
    if updated is None:
        # A custom adapter may accept writes but fail to expose a complete
        # snapshot afterwards. Restore the guarded pre-state before returning.
        try:
            _memory_apply_snapshot(target, actual)
        except Exception:
            pass
        return command_error("memory_target_invalid", "Edited memory cannot be read")
    return command_ok(
        {
            "target_token": token,
            "old_snapshot": actual,
            "new_snapshot": updated,
        },
        events=["memory_edited"],
    )


def _inspector_set_property(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Guarded property mutation for editor-only Inspector targets."""

    from core.VitaLoom.inspector.transient_property import (
        property_value_equal,
        read_property,
        write_property,
    )

    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    token = str(payload.get("target_token", "")).strip()
    property_path = str(payload.get("property_path", "")).strip()
    if not token:
        return command_error("invalid_target_token", "target_token is required")
    if not property_path:
        return command_error("invalid_property_path", "property_path is required")
    target = registry.resolve_transient_target(token)
    if target is None:
        return command_error("transient_target_not_found", "Transient Inspector target is no longer bound")

    old_present, old_value = read_property(target, property_path)
    expected_present = payload.get("expected_present", old_present)
    if not isinstance(expected_present, bool):
        return command_error("invalid_expected_state", "expected_present must be a boolean")
    if expected_present != old_present:
        return command_error(
            "stale_inspector_property",
            "Inspector property presence no longer matches the expected state",
        )
    if "expected_value" in payload and not property_value_equal(
        old_value, payload.get("expected_value")
    ):
        return command_error(
            "stale_inspector_property",
            "Inspector property value changed outside this command history",
        )

    present = payload.get("present", True)
    if not isinstance(present, bool):
        return command_error("invalid_property_presence", "present must be a boolean")
    value = payload.get("value")
    try:
        write_property(target, property_path, value, present=present)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        return command_error("inspector_property_write_failed", str(exc))
    new_present, new_value = read_property(target, property_path)
    return command_ok(
        {
            "target_token": token,
            "property_path": property_path,
            "old_present": old_present,
            "old_value": old_value,
            "new_present": new_present,
            "new_value": new_value,
        },
        events=["inspector_property_set"],
    )


def _entity_restore_snapshot(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Restore the pre-mutation JSON entity for a semantic-history inverse."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    snapshot = payload.get("entity")
    if not isinstance(snapshot, Mapping):
        return command_error("invalid_entity_snapshot", "entity must be an object snapshot")
    if str(snapshot.get("id", "")).strip() != entity_id:
        return command_error("entity_snapshot_mismatch", "entity snapshot id must match entity_id")
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        return command_error("entity_not_found", f"Entity not found: {entity_id}")
    for index, entity in enumerate(raw_entities):
        if not isinstance(entity, dict) or str(entity.get("id", "")).strip() != entity_id:
            continue
        raw_entities[index] = _json_safe(snapshot)
        _touch_modified_at(data)
        _write_json(scene, data)
        return command_ok(
            {"scene_path": str(scene), "entity_id": entity_id},
            events=["entity_snapshot_restored"],
        )
    return command_error("entity_not_found", f"Entity not found: {entity_id}")

def _entity_delete(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Atomically delete one entity plus every compatible incident connection."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    if not entity_id:
        return command_error("invalid_entity", "entity_id is required")
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        return command_error("entity_not_found", f"Entity not found: {entity_id}")
    raw_connections = data.get("connections")
    canonical_connections = raw_connections if isinstance(raw_connections, list) else []
    if "expected_entities" in payload:
        expected_entities = payload.get("expected_entities")
        if not isinstance(expected_entities, list):
            return command_error("invalid_expected_entities", "expected_entities must be a list")
        expected_entities = _json_safe(expected_entities)
        actual_entities = _json_safe(raw_entities)
        if actual_entities != expected_entities:
            return command_error(
                "stale_entity_delete",
                "Entity list no longer matches the expected canonical state",
                details={"expected_entities": expected_entities, "actual_entities": actual_entities},
            )
    if "expected_connections" in payload:
        expected_connections = payload.get("expected_connections")
        if not isinstance(expected_connections, list):
            return command_error("invalid_expected_connections", "expected_connections must be a list")
        expected_connections = _json_safe(expected_connections)
        actual_connections = _json_safe(canonical_connections)
        if actual_connections != expected_connections:
            return command_error(
                "stale_entity_delete",
                "Connection list no longer matches the expected canonical state",
                details={"expected_connections": expected_connections, "actual_connections": actual_connections},
            )
    entity_index = next(
        (
            index
            for index, entity in enumerate(raw_entities)
            if isinstance(entity, Mapping) and str(entity.get("id", "")).strip() == entity_id
        ),
        None,
    )
    if entity_index is None:
        return command_error("entity_not_found", f"Entity not found: {entity_id}")

    deleted_entity = _json_safe(raw_entities[entity_index])
    if "expected_entity" in payload:
        expected_entity = payload.get("expected_entity")
        if not isinstance(expected_entity, Mapping):
            return command_error("invalid_expected_entity", "expected_entity must be an object")
        expected_entity = _json_safe(dict(expected_entity))
        if deleted_entity != expected_entity:
            return command_error(
                "stale_entity_delete",
                "Entity snapshot no longer matches the expected canonical state",
                details={"entity_id": entity_id, "expected_entity": expected_entity, "actual_entity": deleted_entity},
            )
    if "expected_entity_index" in payload:
        expected_entity_index = payload.get("expected_entity_index")
        if not isinstance(expected_entity_index, int) or isinstance(expected_entity_index, bool):
            return command_error("invalid_expected_entity_index", "expected_entity_index must be an integer")
        if entity_index != expected_entity_index:
            return command_error(
                "stale_entity_delete",
                "Entity index no longer matches the expected canonical state",
                details={"entity_id": entity_id, "expected_entity_index": expected_entity_index, "actual_entity_index": entity_index},
            )

    deleted_connections: list[dict[str, Any]] = []
    retained_connections: list[Any] | None = None
    if isinstance(raw_connections, list):
        retained_connections = []
        for index, connection in enumerate(raw_connections):
            if isinstance(connection, Mapping) and _connection_references_entity(connection, entity_id):
                deleted_connections.append(
                    {"connection": _json_safe(connection), "connection_index": index}
                )
            else:
                retained_connections.append(connection)
    if "expected_incident_connections" in payload:
        expected_incident_connections = payload.get("expected_incident_connections")
        if not isinstance(expected_incident_connections, list):
            return command_error(
                "invalid_expected_incident_connections",
                "expected_incident_connections must be a list",
            )
        expected_incident_connections = _json_safe(expected_incident_connections)
        if deleted_connections != expected_incident_connections:
            return command_error(
                "stale_entity_delete",
                "Incident connections no longer match the expected canonical state",
                details={
                    "entity_id": entity_id,
                    "expected_incident_connections": expected_incident_connections,
                    "actual_incident_connections": deleted_connections,
                },
            )

    del raw_entities[entity_index]
    if retained_connections is not None:
        data["connections"] = retained_connections
    _touch_modified_at(data)
    _write_json(scene, data)
    result = {
        "scene_path": str(scene),
        "entity_id": entity_id,
        "entity": deleted_entity,
        "entity_index": entity_index,
        "deleted_connections": deleted_connections,
        # The delete itself is the only point that can observe the exact
        # post-delete canonical scene required by its restore inverse.
        "history_restore_expected_entities": _json_safe(raw_entities),
        "history_restore_expected_connections": _json_safe(
            retained_connections if retained_connections is not None else canonical_connections
        ),
    }
    if any(
        key in payload
        for key in ("expected_entity", "expected_entity_index", "expected_incident_connections")
    ):
        # A guarded create-undo is the only producer.  Persist its actual post-undo
        # canonical state so same-process and fresh-registry redo can prove the
        # scene has not changed before reinserting the entity.
        result["history_redo_expected_entities"] = _json_safe(raw_entities)
        result["history_redo_expected_connections"] = _json_safe(
            retained_connections if retained_connections is not None else []
        )
    return command_ok(result, events=["entity_deleted"])


def _entity_restore_deleted_snapshot(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Restore one deleted entity and its incident connection snapshots atomically."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    snapshot = payload.get("entity")
    entity_index = payload.get("entity_index")
    deleted_connections = payload.get("deleted_connections", [])
    if not entity_id or not isinstance(snapshot, Mapping):
        return command_error("invalid_entity_snapshot", "entity_id and entity snapshot are required")
    if str(snapshot.get("id", "")).strip() != entity_id:
        return command_error("entity_snapshot_mismatch", "entity snapshot id must match entity_id")
    if not isinstance(entity_index, int) or isinstance(entity_index, bool):
        return command_error("invalid_entity_index", "entity_index must be an integer")
    if not isinstance(deleted_connections, list):
        return command_error("invalid_deleted_connections", "deleted_connections must be a list")

    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        raw_entities = []
    raw_connections = data.get("connections")
    if not isinstance(raw_connections, list):
        raw_connections = []
    if "expected_entities" in payload:
        expected_entities = payload.get("expected_entities")
        if not isinstance(expected_entities, list):
            return command_error("invalid_expected_entities", "expected_entities must be a list")
        expected_entities = _json_safe(expected_entities)
        actual_entities = _json_safe(raw_entities)
        if actual_entities != expected_entities:
            return command_error(
                "stale_entity_restore_deleted_snapshot",
                "Entity list no longer matches the expected canonical post-delete state",
                details={"expected_entities": expected_entities, "actual_entities": actual_entities},
            )
    if "expected_connections" in payload:
        expected_connections = payload.get("expected_connections")
        if not isinstance(expected_connections, list):
            return command_error("invalid_expected_connections", "expected_connections must be a list")
        expected_connections = _json_safe(expected_connections)
        actual_connections = _json_safe(raw_connections)
        if actual_connections != expected_connections:
            return command_error(
                "stale_entity_restore_deleted_snapshot",
                "Connection list no longer matches the expected canonical post-delete state",
                details={"expected_connections": expected_connections, "actual_connections": actual_connections},
            )
    if _find_entity(raw_entities, entity_id) is not None:
        return command_error("entity_id_exists", f"Entity already exists: {entity_id}")
    if entity_index < 0 or entity_index > len(raw_entities):
        return command_error("entity_index_out_of_range", "entity_index must address the current entity list")

    restore_rows: list[tuple[int, dict[str, Any]]] = []
    for row in deleted_connections:
        if not isinstance(row, Mapping):
            return command_error("invalid_deleted_connections", "deleted connection entries must be objects")
        connection = row.get("connection")
        connection_index = row.get("connection_index")
        if not isinstance(connection, Mapping):
            return command_error("invalid_deleted_connections", "deleted connection snapshot must be an object")
        if not isinstance(connection_index, int) or isinstance(connection_index, bool):
            return command_error("invalid_connection_index", "connection_index must be an integer")
        start = _connection_endpoint(connection, ("start", "start_id", "from"))
        end = _connection_endpoint(connection, ("end", "end_id", "to"))
        if not start or not end or entity_id not in {start, end}:
            return command_error("invalid_deleted_connections", "connection must reference the restored entity")
        other_id = end if start == entity_id else start
        if other_id != entity_id and _find_entity(raw_entities, other_id) is None:
            return command_error("connection_endpoint_missing", f"Connection endpoint not found: {other_id}")
        restore_rows.append((connection_index, _json_safe(dict(connection))))

    restore_indices = [connection_index for connection_index, _ in restore_rows]
    if len(restore_indices) != len(set(restore_indices)):
        return command_error("duplicate_connection_index", "deleted connection indices must be unique")
    for offset, (connection_index, _) in enumerate(sorted(restore_rows, key=lambda item: item[0])):
        if connection_index < 0 or connection_index > len(raw_connections) + offset:
            return command_error("connection_index_out_of_range", "connection_index must address the restored connection list")

    if not isinstance(data.get("entities"), list):
        data["entities"] = raw_entities
    raw_entities.insert(entity_index, _json_safe(dict(snapshot)))
    if not isinstance(data.get("connections"), list):
        data["connections"] = raw_connections
    for connection_index, connection in sorted(restore_rows, key=lambda item: item[0]):
        raw_connections.insert(connection_index, connection)
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "entity_id": entity_id,
            "entity": _json_safe(dict(snapshot)),
            "entity_index": entity_index,
            "deleted_connections": [
                {"connection": connection, "connection_index": connection_index}
                for connection_index, connection in restore_rows
            ],
            # The successful restore observes the exact post-restore scene used
            # as the full current-state witness for a later redo delete.
            "history_redo_expected_entities": _json_safe(raw_entities),
            "history_redo_expected_connections": _json_safe(raw_connections),
        },
        events=["entity_deleted_snapshot_restored"],
    )


def _connection_references_entity(connection: Mapping[str, Any], entity_id: str) -> bool:
    return entity_id in {
        _connection_endpoint(connection, ("start", "start_id", "from")),
        _connection_endpoint(connection, ("end", "end_id", "to")),
    }


def _transform_set(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    ent = _find_entity(_scene_entities(data), entity_id)
    if ent is None:
        return command_error("entity_not_found", f"Entity not found: {entity_id}")
    if "expected_position" in payload and "position" not in payload:
        return command_error(
            "expected_position_requires_position",
            "expected_position may only guard a position update",
        )

    normalized_position: list[float] | None = None
    if "position" in payload:
        normalized_position, position_error = _normalized_finite_position(payload.get("position"))
        if position_error:
            return command_error("invalid_position", position_error)
    if "expected_position" in payload:
        expected_position, expected_error = _normalized_finite_position(payload.get("expected_position"))
        if expected_error:
            return command_error("invalid_expected_position", expected_error)
        actual_position = _json_safe(ent.get("position"))
        if actual_position != expected_position:
            return command_error(
                "stale_transform_position",
                "Entity position no longer matches the expected canonical state",
                details={
                    "entity_id": entity_id,
                    "expected_position": expected_position,
                    "actual_position": actual_position,
                },
            )

    changed: dict[str, dict[str, Any]] = {}
    for key in ("position", "rotation", "scale"):
        if key not in payload:
            continue
        old = _json_safe(ent.get(key))
        new = normalized_position if key == "position" else payload.get(key)
        ent[key] = new
        changed[key] = {"old": old, "new": _json_safe(new)}
    if not changed:
        return command_error("empty_transform_update", "At least one of position, rotation, or scale is required")
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {"scene_path": str(scene), "entity_id": entity_id, "changed": changed},
        events=["transform_changed"],
    )


def _transform_batch_set(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Atomically apply validated entity positions through one canonical scene write."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    raw_transforms = payload.get("transforms")
    if not isinstance(raw_transforms, list) or not raw_transforms:
        return command_error("invalid_transforms", "transforms must be a non-empty list")

    updates: list[tuple[str, list[float]]] = []
    seen_entity_ids: set[str] = set()
    for index, raw_transform in enumerate(raw_transforms):
        if not isinstance(raw_transform, Mapping):
            return command_error("invalid_transform", f"transforms[{index}] must be an object")
        entity_id = str(raw_transform.get("entity_id", "")).strip()
        if not entity_id:
            return command_error("invalid_entity", f"transforms[{index}].entity_id is required")
        if entity_id in seen_entity_ids:
            return command_error("duplicate_entity_id", f"transforms contains duplicate entity_id: {entity_id}")
        normalized_position, position_error = _normalized_finite_position(raw_transform.get("position"))
        if position_error:
            return command_error("invalid_position", f"transforms[{index}].position {position_error}")
        seen_entity_ids.add(entity_id)
        updates.append((entity_id, normalized_position))

    entities = _scene_entities(data)
    resolved: list[tuple[str, dict[str, Any], list[float]]] = []
    for entity_id, position in updates:
        entity = _find_entity(entities, entity_id)
        if entity is None:
            return command_error("entity_not_found", f"Entity not found: {entity_id}")
        resolved.append((entity_id, entity, position))

    changed: list[dict[str, Any]] = []
    for entity_id, entity, position in resolved:
        old_position = _json_safe(entity.get("position"))
        entity["position"] = position
        changed.append(
            {
                "entity_id": entity_id,
                "position": {"old": old_position, "new": _json_safe(position)},
            }
        )
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {"scene_path": str(scene), "changed": changed},
        events=["transforms_changed"],
    )


def _connection_create(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Insert one validated connection without changing any unrelated list entry."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    connection, error = _validated_connection_snapshot(payload.get("connection"), data)
    if error:
        return command_error("invalid_connection", error)
    raw_connections = data.get("connections")
    if raw_connections is None:
        raw_connections = []
        data["connections"] = raw_connections
    if not isinstance(raw_connections, list):
        return command_error("invalid_connections", "scene.connections must be a list")
    requested_index = payload.get("connection_index")
    if requested_index is None:
        index = len(raw_connections)
    elif isinstance(requested_index, int) and not isinstance(requested_index, bool):
        index = requested_index
    else:
        return command_error("invalid_connection_index", "connection_index must be an integer")
    if index < 0 or index > len(raw_connections):
        return command_error("connection_index_out_of_range", "connection_index must address the current connection list")
    stored = _json_safe(dict(payload["connection"]))
    raw_connections.insert(index, stored)
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "connection": stored,
            "connection_index": index,
        },
        events=["connection_created"],
    )


def _connection_delete(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Delete a specific list slot after checking its JSON-safe connection snapshot."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    expected, error = _validated_connection_snapshot(payload.get("connection"), data)
    if error:
        return command_error("invalid_connection", error)
    index = payload.get("connection_index")
    if not isinstance(index, int) or isinstance(index, bool):
        return command_error("invalid_connection_index", "connection_index must be an integer")
    raw_connections = data.get("connections")
    if not isinstance(raw_connections, list):
        return command_error("connection_not_found", "Connection not found")
    if index < 0 or index >= len(raw_connections):
        return command_error("connection_not_found", "Connection not found")
    existing = raw_connections[index]
    if not isinstance(existing, Mapping) or not _connections_equivalent(existing, expected):
        return command_error("connection_mismatch", "Connection snapshot no longer matches the requested list entry")
    deleted = _json_safe(existing)
    del raw_connections[index]
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "connection": deleted,
            "connection_index": index,
        },
        events=["connection_deleted"],
    )


def _connection_set_weight(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Replace only one exact connection weight after a guarded list-slot match."""
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    expected, error = _validated_connection_snapshot(payload.get("connection"), data)
    if error:
        return command_error("invalid_connection", error)
    index = payload.get("connection_index")
    if not isinstance(index, int) or isinstance(index, bool):
        return command_error("invalid_connection_index", "connection_index must be an integer")
    raw_weight = payload.get("weight")
    if not _is_finite_number(raw_weight):
        return command_error("invalid_connection_weight", "connection weight must be a finite number")
    raw_connections = data.get("connections")
    if not isinstance(raw_connections, list) or index < 0 or index >= len(raw_connections):
        return command_error("connection_not_found", "Connection not found")
    existing = raw_connections[index]
    if not isinstance(existing, Mapping) or not _connections_equivalent(existing, expected):
        return command_error("connection_mismatch", "Connection snapshot no longer matches the requested list entry")

    old_connection = dict(expected)
    new_connection = dict(expected)
    new_connection["weight"] = float(raw_weight)
    updated = dict(existing)
    updated["weight"] = new_connection["weight"]
    raw_connections[index] = updated
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "connection_index": index,
            "old_connection": old_connection,
            "new_connection": new_connection,
        },
        events=["connection_weight_changed"],
    )


def _validated_connection_snapshot(
    raw_connection: Any,
    scene_data: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(raw_connection, Mapping):
        return None, "connection must be an object"
    start = _connection_endpoint(raw_connection, ("start", "start_id", "from"))
    end = _connection_endpoint(raw_connection, ("end", "end_id", "to"))
    if not start or not end:
        return None, "connection start and end are required"
    if start == end:
        return None, "connection start and end must be different"
    entities = _scene_entities(scene_data)
    if _find_entity(entities, start) is None or _find_entity(entities, end) is None:
        return None, "connection endpoints must reference existing entities"
    weight = raw_connection.get("weight", 1.0)
    if not _is_finite_number(weight):
        return None, "connection weight must be a finite number"
    return {"start": start, "end": end, "weight": float(weight)}, None


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _normalized_finite_position(value: Any) -> tuple[list[float] | None, str | None]:
    """Validate the canonical finite 2D position shape used by scene transforms."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None, "must be a numeric [x, y]"
    if any(not _is_finite_number(component) for component in value):
        return None, "must contain finite numbers"
    return [float(value[0]), float(value[1])], None


def _connection_endpoint(connection: Mapping[str, Any], names: tuple[str, ...]) -> str:
    for name in names:
        value = str(connection.get(name, "")).strip()
        if value:
            return value
    return ""


def _connections_equivalent(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_start = _connection_endpoint(left, ("start", "start_id", "from"))
    left_end = _connection_endpoint(left, ("end", "end_id", "to"))
    right_start = _connection_endpoint(right, ("start", "start_id", "from"))
    right_end = _connection_endpoint(right, ("end", "end_id", "to"))
    left_weight = left.get("weight", 1.0)
    right_weight = right.get("weight", 1.0)
    return (
        left_start == right_start
        and left_end == right_end
        and _is_finite_number(left_weight)
        and _is_finite_number(right_weight)
        and float(left_weight) == float(right_weight)
    )


def _script_set_property(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    entity_id = str(payload.get("entity_id", "")).strip()
    script_name = str(payload.get("script", "")).strip()
    prop_path = str(payload.get("property_path", "")).strip()
    if not script_name:
        return command_error("invalid_script", "script is required")
    if not prop_path:
        return command_error("invalid_property_path", "property_path is required")
    ent = _find_entity(_scene_entities(data), entity_id)
    if ent is None:
        return command_error("entity_not_found", f"Entity not found: {entity_id}")
    scripts = ent.get("scripts")
    if not isinstance(scripts, list):
        return command_error("script_not_found", f"Script not found: {script_name}")
    target: dict[str, Any] | None = None
    for script in scripts:
        if not isinstance(script, dict):
            continue
        candidates = {
            str(script.get("name", "")).strip(),
            str(script.get("type", "")).strip(),
            str(script.get("path", "")).strip(),
        }
        if script_name in candidates:
            target = script
            break
    if target is None:
        return command_error("script_not_found", f"Script not found: {script_name}")
    props = target.get("properties")
    if not isinstance(props, dict):
        props = {}
        target["properties"] = props
    value = payload.get("value")
    try:
        old = _set_nested_property(props, prop_path, value)
    except ValueError:
        return command_error("invalid_property_path", "property_path is invalid")
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "entity_id": entity_id,
            "script": script_name,
            "property_path": prop_path,
            "old_value": old,
            "new_value": value,
        },
        events=["script_property_changed"],
    )


def _prefab_place(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    project = _project_root_for_scene(scene)
    if project is None:
        return command_error("project_not_found", "Scene must belong to a project with project.json")
    prefab = _resolve_project_file(project, str(payload.get("prefab_path", "")))
    if prefab is None:
        return command_error("prefab_not_found", "Prefab path must point to a project file")
    try:
        source = _read_json(prefab)
    except (OSError, json.JSONDecodeError):
        return command_error("invalid_prefab", "Prefab must be a JSON object")
    entity_id = str(payload.get("entity_id", "")).strip()
    if not entity_id:
        return command_error("invalid_entity", "entity_id is required")
    entities = _scene_entities(data)
    if _find_entity(entities, entity_id) is not None:
        return command_error("entity_id_exists", f"Entity already exists: {entity_id}")
    ent = dict(source)
    ent["id"] = entity_id
    ent.setdefault("name", entity_id)
    ent.setdefault("type", "prefab_instance")
    if "position" in payload:
        ent["position"] = payload.get("position")
    ent["prefab_path"] = _project_relative_path(project, str(prefab))
    ent.setdefault("scripts", [])
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        data["entities"] = raw_entities = []
    entity_index = len(raw_entities)
    raw_entities.append(ent)
    raw_connections = data.get("connections")
    canonical_connections = raw_connections if isinstance(raw_connections, list) else []
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "entity_id": entity_id,
            "prefab_path": ent["prefab_path"],
            # Persist the exact expanded entity and canonical post-place lists so
            # history never needs to reread the mutable prefab source.
            "entity": _json_safe(ent),
            "entity_index": entity_index,
            "history_undo_expected_entities": _json_safe(raw_entities),
            "history_undo_expected_connections": _json_safe(canonical_connections),
        },
        events=["prefab_placed"],
    )


def _project_asset_index(project: Path) -> dict[str, Any]:
    from core.VitaLoom.project.asset_index import build_project_asset_index

    return build_project_asset_index(project)


def _asset_scan(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    index = _project_asset_index(project)
    return command_ok(
        {
            "project_path": str(project),
            "assets": index["assets"],
            "asset_count": index["asset_count"],
            "index_revision": index["index_revision"],
            "provenance": index["provenance"],
            "coverage": index["coverage"],
        }
    )


def _valid_script_class_name(raw_name: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z_]+", "_", raw_name or "").strip("_")
    if not sanitized:
        sanitized = "UserScript"
    if sanitized[0].isdigit():
        sanitized = f"Script_{sanitized}"
    parts = [part for part in sanitized.split("_") if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) if parts else sanitized


def _resolve_project_folder(project: Path, raw_folder: str) -> Path | None:
    folder = Path(raw_folder)
    if not folder.is_absolute():
        folder = project / folder
    try:
        resolved = folder.resolve()
        project_root = project.resolve()
    except OSError:
        return None
    if resolved != project_root and project_root not in resolved.parents:
        return None
    return resolved


def _asset_registry_snapshot(project: Path, *, rename_hints: Mapping[str, str] | None = None) -> dict[str, Any]:
    from core.VitaLoom.project.asset_registry import refresh_project_asset_registry

    return refresh_project_asset_registry(project, rename_hints=rename_hints)


def _asset_registry_fields(project: Path, path: Path, *, rename_hints: Mapping[str, str] | None = None) -> dict[str, Any]:
    snapshot = _asset_registry_snapshot(project, rename_hints=rename_hints)
    relative_path = str(path.resolve().relative_to(project.resolve())).replace("\\", "/")
    asset_id = next(
        (
            row["asset_id"]
            for row in snapshot["asset_projection"]
            if row["path"] == relative_path
        ),
        None,
    )
    fields: dict[str, Any] = {
        "asset_registry_revision": snapshot["registry_revision"],
        "asset_registry_generation": snapshot["generation"],
    }
    if asset_id is not None:
        fields["asset_id"] = asset_id
    return fields


def _asset_result_with_registry(
    project: Path,
    path: Path,
    result: Mapping[str, Any],
    *,
    rename_hints: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    enriched = dict(result)
    try:
        enriched.update(_asset_registry_fields(project, path, rename_hints=rename_hints))
    except Exception as exc:
        enriched["asset_registry"] = {
            "status": "refresh_failed",
            "error": type(exc).__name__,
        }
    return enriched


def _protected_asset_relative_path(relative_path: str) -> bool:
    return relative_path in {"project.json", "project.lock.json"} or relative_path.startswith(".vitaloom/")


def _asset_refresh(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    try:
        snapshot = _asset_registry_snapshot(project)
    except Exception as exc:
        return command_error("asset_registry_refresh_failed", "Asset registry refresh failed", details={"error": type(exc).__name__})
    return command_ok(snapshot, events=["asset_registry_refreshed"])


def _asset_rename(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    source = _resolve_project_file(project, str(payload.get("source_path", "")))
    target = _resolve_project_file(project, str(payload.get("target_path", "")), must_exist=False)
    if source is None or target is None or source == project or target == project:
        return command_error("asset_path_outside_project", "Asset paths must be project-contained files")
    if not source.is_file():
        return command_error("asset_not_found", "Source asset file does not exist")
    if target.exists():
        return command_error("asset_exists", "Target asset already exists", details={"path": str(target)})
    if not target.parent.is_dir():
        return command_error("asset_target_folder_not_found", "Target folder must already exist under the project")
    source_relative = str(source.relative_to(project)).replace("\\", "/")
    target_relative = str(target.relative_to(project)).replace("\\", "/")
    if _protected_asset_relative_path(source_relative) or _protected_asset_relative_path(target_relative):
        return command_error("asset_path_protected", "Project manifests and Registry metadata cannot be renamed as assets")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            apply_asset_reference_mutation,
            plan_asset_reference_mutation,
        )

        plan = plan_asset_reference_mutation(
            project,
            operation="rename",
            source_path=source_relative,
            target_path=target_relative,
        )
        receipt = apply_asset_reference_mutation(project, plan)
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    except OSError as exc:
        return command_error("asset_rename_failed", "Asset rename failed", details={"error": type(exc).__name__})
    registry = receipt["registry"]
    return command_ok(
        {
            "project_path": str(project),
            "path": str(target),
            "source_path": source_relative,
            "target_path": target_relative,
            "asset_id": receipt["asset_id"],
            "transaction_id": receipt["transaction_id"],
            "reference_edits": receipt["reference_edits"],
            "asset_registry_revision": registry["registry_revision"],
            "asset_registry_generation": registry["generation"],
        },
        events=["asset_renamed", "asset_references_migrated", "asset_registry_refreshed"],
    )

def _asset_delete(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    target = _resolve_project_file(project, str(payload.get("asset_path", "")), must_exist=False)
    if target is None or target == project:
        return command_error("asset_path_outside_project", "Asset path must be a project-contained file")
    if target.is_dir():
        return command_error("asset_delete_requires_file", "Asset delete only supports one file")
    if not target.is_file():
        return command_error("asset_not_found", "Asset file does not exist")
    relative_path = str(target.relative_to(project)).replace("\\", "/")
    if _protected_asset_relative_path(relative_path):
        return command_error("asset_path_protected", "Project manifests and Registry metadata cannot be deleted as assets")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            apply_asset_reference_mutation,
            plan_asset_reference_mutation,
        )

        plan = plan_asset_reference_mutation(project, operation="delete", source_path=relative_path)
        receipt = apply_asset_reference_mutation(project, plan)
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    except OSError as exc:
        return command_error("asset_delete_failed", "Asset delete failed", details={"error": type(exc).__name__})
    registry = receipt["registry"]
    return command_ok(
        {
            "project_path": str(project),
            "path": str(target),
            "relative_path": relative_path,
            "asset_id": receipt["asset_id"],
            "transaction_id": receipt["transaction_id"],
            "asset_registry_revision": registry["registry_revision"],
            "asset_registry_generation": registry["generation"],
        },
        events=["asset_deleted", "asset_transaction_applied", "asset_registry_refreshed"],
    )


def _asset_retirement_analyze(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            analyze_asset_retirement_policy,
        )

        result = analyze_asset_retirement_policy(
            project,
            source_path=str(payload.get("source_path", "")),
            replacement_path=(
                None
                if payload.get("replacement_path") is None
                else str(payload.get("replacement_path"))
            ),
        )
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(result)


def _asset_referenced_replace(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Run the narrow, guarded structural replacement transaction Authority."""

    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            apply_asset_reference_mutation,
            plan_asset_reference_mutation,
        )

        plan = plan_asset_reference_mutation(
            project,
            operation="replace_referenced",
            source_path=str(payload.get("source_path", "")),
            target_path=str(payload.get("replacement_path", "")),
        )
        receipt = apply_asset_reference_mutation(project, plan)
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    except OSError as exc:
        return command_error(
            "asset_referenced_replacement_failed",
            "Referenced asset replacement failed",
            details={"error": type(exc).__name__},
        )
    registry = receipt["registry"]
    return command_ok(
        {
            "project_path": str(project),
            "source_path": receipt["source_path"],
            "replacement_path": receipt["target_path"],
            "asset_id": receipt["asset_id"],
            "transaction_id": receipt["transaction_id"],
            "reference_edits": receipt["reference_edits"],
            "warnings": ["replacement_semantic_compatibility_not_inferred"],
            "asset_registry_revision": registry["registry_revision"],
            "asset_registry_generation": registry["generation"],
        },
        events=["asset_references_replaced", "asset_retired", "asset_transaction_applied", "asset_registry_refreshed"],
    )


def _asset_transaction_undo(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            undo_asset_reference_mutation,
        )

        receipt = undo_asset_reference_mutation(project, str(payload.get("transaction_id", "")))
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    registry = receipt["registry"]
    return command_ok(
        {
            "project_path": str(project),
            "transaction_id": receipt["transaction_id"],
            "asset_id": receipt["asset_id"],
            "asset_registry_revision": registry["registry_revision"],
            "asset_registry_generation": registry["generation"],
        },
        events=["asset_transaction_undone", "asset_registry_refreshed"],
    )


def _asset_transaction_redo(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            redo_asset_reference_mutation,
        )

        receipt = redo_asset_reference_mutation(project, str(payload.get("transaction_id", "")))
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    registry = receipt["registry"]
    return command_ok(
        {
            "project_path": str(project),
            "transaction_id": receipt["transaction_id"],
            "asset_id": receipt["asset_id"],
            "asset_registry_revision": registry["registry_revision"],
            "asset_registry_generation": registry["generation"],
        },
        events=["asset_transaction_redone", "asset_registry_refreshed"],
    )

def _asset_transaction_retention_analyze(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Thin read-only Adapter for the transaction retention policy Authority."""

    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            analyze_asset_transaction_retention_policy,
        )

        policy = analyze_asset_transaction_retention_policy(project)
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(policy)


def _asset_transaction_prune_plan(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Thin read-only Adapter for one exact Authority prune plan."""

    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            plan_asset_transaction_artifact_prune,
        )

        plan = plan_asset_transaction_artifact_prune(
            project,
            artifact_paths=payload.get("artifact_paths"),
            expected_digests=payload.get("expected_digests"),
        )
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(plan)


def _asset_transaction_prune_apply(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Adapter that re-plans before the Authority performs irreversible prune I/O."""

    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            apply_asset_transaction_artifact_prune,
            plan_asset_transaction_artifact_prune,
        )

        plan = plan_asset_transaction_artifact_prune(
            project,
            artifact_paths=payload.get("artifact_paths"),
            expected_digests=payload.get("expected_digests"),
        )
        if str(payload.get("policy_snapshot_digest") or "") != plan["policy_snapshot_digest"]:
            return command_error(
                "asset_transaction_prune_stale",
                "Provided policy snapshot does not match current Authority facts",
                details={
                    "provided_policy_snapshot_digest": str(payload.get("policy_snapshot_digest") or ""),
                    "current_policy_snapshot_digest": plan["policy_snapshot_digest"],
                },
            )
        receipt = apply_asset_transaction_artifact_prune(
            project,
            plan,
            operator_confirmation=str(payload.get("operator_confirmation") or ""),
        )
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok({"project_path": str(project), **receipt}, events=["asset_transaction_pruned"])


def _asset_transaction_inspect(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            inspect_asset_reference_transaction,
        )

        inspection = inspect_asset_reference_transaction(project, str(payload.get("transaction_id", "")))
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(inspection)


def _asset_transaction_recovery_list(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            list_asset_reference_transaction_recovery,
        )

        recovery = list_asset_reference_transaction_recovery(project)
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(recovery)


def _asset_transaction_recovery_resolve(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from core.VitaLoom.project.asset_reference_transaction import (
            AssetReferenceTransactionError,
            resolve_asset_reference_transaction,
        )

        resolution = resolve_asset_reference_transaction(
            project,
            str(payload.get("transaction_id", "")),
            action=str(payload.get("action", "")),
        )
    except AssetReferenceTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok(
        {"project_path": str(project), **resolution},
        events=["asset_transaction_recovery_resolved"],
    )


def _plugin_host_adapter(context: Mapping[str, Any]):
    from core.VitaLoom.project.plugin_host_operator import get_plugin_host_operator_adapter

    return get_plugin_host_operator_adapter(context)


def _plugin_host_command_error(exc: Exception) -> dict[str, Any]:
    from core.VitaLoom.project.plugin_host_operator import PluginHostOperatorError

    if isinstance(exc, PluginHostOperatorError):
        return command_error(exc.code, exc.message, details=exc.details)
    return command_error(
        "plugin_host_operator_error",
        str(exc) or type(exc).__name__,
        details={"error": type(exc).__name__},
    )


def _plugin_host_inspect(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    adapter = _plugin_host_adapter(context)
    if adapter is None or not callable(getattr(adapter, "inspect_plugin_host", None)):
        return command_error(
            "plugin_host_unavailable",
            "No live downstream plugin Host Adapter is available in this process",
        )
    try:
        inspection = adapter.inspect_plugin_host(str(payload.get("project_path") or ""))
        return command_ok(inspection)
    except Exception as exc:
        return _plugin_host_command_error(exc)


def _plugin_host_recovery_list(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    adapter = _plugin_host_adapter(context)
    if adapter is None or not callable(
        getattr(adapter, "list_plugin_host_recoveries", None)
    ):
        return command_error(
            "plugin_host_unavailable",
            "No live downstream plugin Host Adapter is available in this process",
        )
    try:
        result = adapter.list_plugin_host_recoveries(
            str(payload.get("project_path") or "")
        )
        return command_ok(result)
    except Exception as exc:
        return _plugin_host_command_error(exc)


def _plugin_host_recovery_resolve(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    adapter = _plugin_host_adapter(context)
    if adapter is None or not callable(
        getattr(adapter, "resolve_plugin_host_recovery", None)
    ):
        return command_error(
            "plugin_host_unavailable",
            "No live downstream plugin Host Adapter is available in this process",
        )
    try:
        result = adapter.resolve_plugin_host_recovery(
            project_path=str(payload.get("project_path") or ""),
            report_id=str(payload.get("report_id") or ""),
            action=str(payload.get("action") or ""),
            operator_confirmation=str(payload.get("operator_confirmation") or ""),
        )
    except Exception as exc:
        return _plugin_host_command_error(exc)
    if str(result.get("status") or "") != "settled":
        return command_error(
            "plugin_host_recovery_not_settled",
            "Plugin Host recovery completed without reaching a settled lifecycle",
            details=result,
        )
    return command_ok(
        result,
        events=["project_plugin_lifecycle_recovery_settled"],
    )


def _package_transaction_inspect(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from builtin.editor_extensions.package_domain.package_transactions import (
            PackageTransactionError,
            PackageTransactionStore,
        )

        inspection = PackageTransactionStore(project).inspect(str(payload.get("transaction_id", "")))
    except PackageTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok({"project_path": str(project), **inspection})


def _package_transaction_recovery_list(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    try:
        from builtin.editor_extensions.package_domain.package_transactions import (
            PackageTransactionError,
            PackageTransactionStore,
        )

        recovery = PackageTransactionStore(project).list_recoverable()
    except PackageTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    return command_ok({"project_path": str(project), **recovery})


def _package_transaction_expected_action(receipt: Mapping[str, Any]) -> tuple[str | None, str | None]:
    action = str(receipt.get("action", ""))
    state = str(receipt.get("state", ""))
    if state == "prepared":
        return None, "transaction_state_ambiguous"
    if (action, state) in {("install", "local_applied"), ("install", "failed_recoverable")}:
        return "retry_project_install", None
    if (action, state) == ("install", "project_applied"):
        return "finalize", None
    if (action, state) in {("uninstall", "project_applied"), ("uninstall", "failed_recoverable")}:
        return "retry_local_uninstall", None
    return None, "transaction_not_recoverable"


def _package_transaction_recovery_resolve(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    transaction_id = str(payload.get("transaction_id", "")).strip()
    requested_action = str(payload.get("action", "")).strip()
    try:
        from builtin.editor_extensions.package_domain.package_transactions import (
            PackageTransactionError,
            PackageTransactionStore,
            ProjectPackageArtifactPort,
        )
        from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations

        store = PackageTransactionStore(project)
        receipt = store.read(transaction_id)
        expected_action, policy_error = _package_transaction_expected_action(receipt)
        if policy_error:
            return command_error(
                policy_error,
                "Package transaction cannot be resolved automatically in its current state",
                details={"transaction_id": transaction_id, "action": receipt.get("action"), "state": receipt.get("state")},
            )
        if requested_action != expected_action:
            return command_error(
                "package_transaction_action_mismatch",
                "Requested recovery action does not match the durable receipt state",
                details={"transaction_id": transaction_id, "requested_action": requested_action, "expected_action": expected_action},
            )
        expected_confirmation = f"resolve_package_transaction:{transaction_id}:{expected_action}"
        if str(payload.get("operator_confirmation", "")) != expected_confirmation:
            return command_error(
                "package_transaction_confirmation_required",
                "Operator confirmation must bind the transaction id and recovery action",
                details={"transaction_id": transaction_id, "action": expected_action, "expected_confirmation": expected_confirmation},
            )

        def run_project_command(command_id: str, package_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
            if command_id != "plugin.install":
                return command_error("package_transaction_invalid_command", "Unsupported package transaction project command")
            command_payload = {
                "project_path": str(project),
                "plugin_id": str(package_id),
                "source": str(operation.get("source", "") or ""),
                "path": str(operation.get("path", "") or ""),
                "version": str(operation.get("version", "") or ""),
            }
            return _plugin_install(command_payload, context)

        resolution = PackageProjectOperations.recover_transaction(
            transaction_id,
            transaction_store=store,
            operation_service=ProjectPackageArtifactPort(project),
            run_project_command=run_project_command,
        )
    except PackageTransactionError as exc:
        return command_error(exc.code, str(exc), details=exc.details)
    if not resolution.get("ok"):
        error = str(resolution.get("error", "package_transaction_recovery_failed"))
        details = {"project_path": str(project), **{key: value for key, value in resolution.items() if key not in {"ok", "error"}}}
        return command_error(error, "Package transaction recovery did not complete", details=details)
    return command_ok(
        {"project_path": str(project), **resolution},
        events=["package_transaction_recovery_resolved"],
    )

def _asset_create(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")

    asset_type = str(payload.get("asset_type", "") or "").strip()
    asset_name = str(payload.get("name", "") or "").strip()
    folder = _resolve_project_folder(project, str(payload.get("folder", "") or ""))
    if not asset_type or not asset_name:
        return command_error("invalid_asset_request", "asset_type and name are required")
    if folder is None:
        return command_error("asset_folder_outside_project", "Asset folder must live under the project")

    folder.mkdir(parents=True, exist_ok=True)
    if asset_type == "folder":
        created = (folder / asset_name).resolve()
        try:
            if created != project.resolve() and project.resolve() not in created.parents:
                return command_error("asset_folder_outside_project", "Asset folder must live under the project")
        except OSError:
            return command_error("asset_folder_outside_project", "Asset folder must live under the project")
        created.mkdir(parents=True, exist_ok=True)
        return command_ok(
            _asset_result_with_registry(
                project,
                created,
                {"project_path": str(project), "path": str(created), "asset_type": asset_type},
            ),
            events=["asset_created", "asset_registry_refreshed"],
        )

    filename = asset_name
    content = "{}"
    if asset_type == "scene":
        if not filename.endswith(".pond"):
            filename += ".pond"
        scene_name = filename[:-5] if filename.endswith(".pond") else asset_name
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            created_scene = get_scene_manager().create_scene(scene_name, str(project))
        except Exception:
            created_scene = None
        if created_scene:
            created_path = Path(created_scene)
            return command_ok(
                _asset_result_with_registry(
                    project,
                    created_path,
                    {"project_path": str(project), "path": str(created_path), "asset_type": asset_type},
                ),
                events=["asset_created", "asset_registry_refreshed"],
            )
        content = json.dumps({"name": scene_name, "entities": [], "components": []}, ensure_ascii=False, indent=2)
    elif asset_type == "entity":
        if not filename.endswith(".json"):
            filename += ".json"
        content = json.dumps(
            {
                "type": "entity",
                "name": asset_name,
                "entity_type": "blank",
                "components": [],
                "scripts": [],
                "children": [],
            },
            ensure_ascii=False,
            indent=2,
        )
    elif asset_type == "organism":
        if not filename.endswith(".json"):
            filename += ".json"
        content = json.dumps(
            {
                "type": "entity",
                "name": asset_name,
                "entity_type": "organism",
                "components": ["Transform", "Renderer"],
                "scripts": [],
                "children": [],
            },
            ensure_ascii=False,
            indent=2,
        )
    elif asset_type == "food":
        if not filename.endswith(".json"):
            filename += ".json"
        content = json.dumps(
            {
                "type": "entity",
                "name": asset_name,
                "entity_type": "food",
                "components": ["Transform", "Renderer", "Nutrition"],
                "scripts": [],
                "children": [],
            },
            ensure_ascii=False,
            indent=2,
        )
    elif asset_type == "component":
        if not filename.endswith(".py"):
            filename += ".py"
        class_name = _valid_script_class_name(asset_name)
        content = (
            "from core.Lotucosm.scripts import ScriptBase\n\n"
            f"class {class_name}(ScriptBase):\n"
            f"    \"\"\"{asset_name} script.\"\"\"\n\n"
            "    def start(self):\n"
            "        pass\n\n"
            "    def update(self, delta_time: float):\n"
            "        pass\n"
        )
    else:
        return command_error("unsupported_asset_type", f"Unsupported asset_type: {asset_type}")

    target = (folder / filename).resolve()
    try:
        if target != project.resolve() and project.resolve() not in target.parents:
            return command_error("asset_folder_outside_project", "Asset path must live under the project")
    except OSError:
        return command_error("asset_folder_outside_project", "Asset path must live under the project")
    if target.exists():
        return command_error("asset_exists", "Asset already exists", details={"path": str(target)})
    target.write_text(content, encoding="utf-8")
    return command_ok(
        _asset_result_with_registry(
            project,
            target,
            {"project_path": str(project), "path": str(target), "asset_type": asset_type},
        ),
        events=["asset_created", "asset_registry_refreshed"],
    )


def _asset_import(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if not (project / "project.json").is_file():
        return command_error("project_not_found", "project.json not found")
    source = Path(str(payload.get("source_path", "") or "")).expanduser()
    if not source.is_absolute():
        source = (_workspace_root() / source).resolve()
    try:
        source = source.resolve()
    except OSError:
        return command_error("asset_source_not_found", "source_path does not exist")
    if not source.is_file():
        return command_error("asset_source_not_found", "source_path does not exist")
    target_folder = _resolve_project_folder(project, str(payload.get("target_folder", "") or "assets"))
    if target_folder is None:
        return command_error("asset_folder_outside_project", "Target folder must live under the project")
    filename = str(payload.get("name", "") or source.name).strip()
    if not filename or any(sep in filename for sep in ("/", "\\")):
        return command_error("invalid_asset_name", "Imported asset name must be a plain filename")
    target_folder.mkdir(parents=True, exist_ok=True)
    target = (target_folder / filename).resolve()
    try:
        if target != project.resolve() and project.resolve() not in target.parents:
            return command_error("asset_folder_outside_project", "Target path must live under the project")
    except OSError:
        return command_error("asset_folder_outside_project", "Target path must live under the project")
    if target.exists() and not bool(payload.get("overwrite", False)):
        return command_error("asset_exists", "Asset already exists", details={"path": str(target)})
    shutil.copyfile(source, target)
    return command_ok(
        _asset_result_with_registry(
            project,
            target,
            {
                "project_path": str(project),
                "path": str(target),
                "relative_path": str(target.relative_to(project)).replace("\\", "/"),
                "bytes": target.stat().st_size,
                "sha256": _file_digest(target),
            },
        ),
        events=["asset_imported", "asset_registry_refreshed"],
    )


def _asset_validate(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    deps = _asset_dependencies(payload, context)
    if not deps.get("ok"):
        return deps
    result = dict(deps.get("result", {}))
    result["valid"] = bool(result.get("ready", False))
    return command_ok(result)


def _asset_dependencies(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    index = _project_asset_index(project)
    deps = index["dependencies"]
    return command_ok(
        {
            "project_path": str(project),
            "index_revision": index["index_revision"],
            "total_edges": deps["total_edges"],
            "edges": deps["edges"],
            "by_kind": deps["by_kind"],
            "missing_scripts": deps["missing_scripts"],
            "missing_assets": deps["missing_assets"],
            "missing_total": deps["missing_total"],
            "missing_by_kind": deps["missing_by_kind"],
            "outside_project": deps["outside_project"],
            "outside_project_total": deps["outside_project_total"],
            "outside_project_by_kind": deps["outside_project_by_kind"],
            "invalid_references": deps["invalid_references"],
            "invalid_total": deps["invalid_total"],
            "invalid_by_kind": deps["invalid_by_kind"],
            "malformed_scenes": deps["malformed_scenes"],
            "ready": deps["ready"],
        }
    )


def _build_asset_export_closure(project: Path, data: dict[str, Any]) -> dict[str, Any]:
    index = _project_asset_index(project)
    deps = index["dependencies"]
    export = index["export"]
    enabled_plugins = [row for row in _plugin_rows(project, data) if row.get("project_enabled")]
    return {
        "project_path": str(project),
        "index_revision": index["index_revision"],
        "files": export["files"],
        "file_count": export["file_count"],
        "file_metadata": export["file_metadata"],
        "dependency_edges": deps["edges"],
        "missing_scripts": deps["missing_scripts"],
        "missing_assets": deps["missing_assets"],
        "missing_total": deps["missing_total"],
        "missing_by_kind": deps["missing_by_kind"],
        "outside_project": deps["outside_project"],
        "outside_project_total": deps["outside_project_total"],
        "outside_project_by_kind": deps["outside_project_by_kind"],
        "invalid_references": deps["invalid_references"],
        "invalid_total": deps["invalid_total"],
        "invalid_by_kind": deps["invalid_by_kind"],
        "malformed_scenes": deps["malformed_scenes"],
        "provenance": index["provenance"],
        "coverage": index["coverage"],
        "enabled_plugins": enabled_plugins,
        "warnings": export["warnings"],
        "ready": export["ready"],
    }


def _asset_export_closure(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    return command_ok(_build_asset_export_closure(project, data))


def _asset_apply_to_scene(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    scene, data = _read_scene_from_payload(payload)
    if scene is None:
        return command_error("scene_not_found", "Scene path must point to a .pond under workspace/")
    project = _project_root_for_scene(scene)
    if project is None:
        return command_error("project_not_found", "Scene must belong to a project with project.json")
    asset = _resolve_project_file(project, str(payload.get("asset_path", "")))
    if asset is None:
        return command_error("asset_not_found", "Asset path must point to a project file")
    entity_id = str(payload.get("entity_id", "")).strip()
    if not entity_id:
        return command_error("invalid_entity", "entity_id is required")
    entities = _scene_entities(data)
    if _find_entity(entities, entity_id) is not None:
        return command_error("entity_id_exists", f"Entity already exists: {entity_id}")
    rel = str(asset.relative_to(project)).replace("\\", "/")
    ent = {
        "id": entity_id,
        "name": str(payload.get("name", "") or asset.stem),
        "type": str(payload.get("entity_type", "") or "asset_reference"),
        "position": payload.get("position", [0.0, 0.0]),
        "radius": float(payload.get("radius", 12.0) or 12.0),
        "asset_path": rel,
        "sr_visual": {"asset_path": rel, "sprite_path": rel},
        "scripts": [],
    }
    raw_entities = data.get("entities")
    if not isinstance(raw_entities, list):
        data["entities"] = raw_entities = []
    entity_index = len(raw_entities)
    raw_entities.append(ent)
    raw_connections = data.get("connections")
    canonical_connections = raw_connections if isinstance(raw_connections, list) else []
    _touch_modified_at(data)
    _write_json(scene, data)
    return command_ok(
        {
            "scene_path": str(scene),
            "entity_id": entity_id,
            "asset_path": rel,
            # Persist the exact output entity and canonical post-apply lists so
            # guarded history never depends on the mutable project asset again.
            "entity": _json_safe(ent),
            "entity_index": entity_index,
            "history_undo_expected_entities": _json_safe(raw_entities),
            "history_undo_expected_connections": _json_safe(canonical_connections),
        },
        events=["asset_applied_to_scene"],
    )


def _selection_set(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.core.editor_context import get_editor_context

    object_ids = payload.get("object_ids") if isinstance(payload.get("object_ids"), list) else []
    get_editor_context().set_selection(list(object_ids))
    return command_ok({"selection": list(object_ids)}, events=["selection_changed"])


def _simulation_transport_status(
    payload: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

    transport = get_simulation_transport()
    if transport is None:
        return command_error(
            "simulation_transport_unavailable",
            "SimulationTransport is not initialized",
        )
    state = transport.state
    is_playing = bool(state.is_playing)
    is_paused = bool(state.is_paused)
    phase = (
        "paused"
        if is_playing and is_paused
        else "playing"
        if is_playing
        else "stopped"
    )
    return command_ok(
        {
            "phase": phase,
            "is_playing": is_playing,
            "is_paused": is_paused,
            "speed": float(state.speed),
        }
    )


def _simulation_play(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

    transport = get_simulation_transport()
    if transport is None:
        return command_error("simulation_transport_unavailable", "SimulationTransport is not initialized")
    transport.request_play()
    return command_ok({"state": "play_requested"}, events=["simulation_play"])


def _simulation_toggle(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

    transport = get_simulation_transport()
    if transport is None:
        return command_error("simulation_transport_unavailable", "SimulationTransport is not initialized")
    transport.request_toggle()
    return command_ok({"state": "toggle_requested"}, events=["simulation_toggle"])


def _simulation_pause(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

    transport = get_simulation_transport()
    if transport is None:
        return command_error("simulation_transport_unavailable", "SimulationTransport is not initialized")
    transport.request_pause()
    return command_ok({"state": "pause_requested"}, events=["simulation_pause"])


def _simulation_stop(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

    transport = get_simulation_transport()
    if transport is None:
        return command_error("simulation_transport_unavailable", "SimulationTransport is not initialized")
    transport.request_stop()
    return command_ok({"state": "stop_requested"}, events=["simulation_stop"])


def _ps_experiment_smoke(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from builtin.systems.ps_experiment_runner import PsExperimentRunner
    from core.Lotucosm.experiment_config import PsExperimentConfig
    from core.VitaLoom.project.evolution_context import (
        apply_evolution_defaults_to_ps_config,
        load_project_evolution_context,
    )

    cfg = PsExperimentConfig(
        name="command_ps_smoke",
        ticks=max(1, int(payload.get("ticks", 5) or 5)),
        seed=int(payload.get("seed", 42) or 42),
        initial_organisms=4,
        max_population=8,
        snapshot_interval=5,
        output_dir=str(_workspace_root() / "state" / "experiment_runs"),
    )
    if payload.get("project_path"):
        project = _resolve_workspace_path(str(payload["project_path"]))
        if project is None:
            return command_error("path_outside_workspace", "Project path must exist under workspace/")
        meta = _read_json(project / "project.json")
        apply_evolution_defaults_to_ps_config(cfg, load_project_evolution_context(meta))
        cfg.ticks = max(1, int(payload.get("ticks", cfg.ticks) or cfg.ticks))
    summary = PsExperimentRunner(cfg).run()
    return command_ok({"final": summary.get("final"), "config": cfg.to_dict()})


def _runtime_replay_status(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.runtime_replay_status import build_runtime_replay_status

    project_path = None
    run_dir = None
    if payload.get("project_path"):
        project_path = _resolve_workspace_path(str(payload["project_path"]))
        if project_path is None:
            return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if payload.get("run_dir"):
        run_dir = _resolve_workspace_path(str(payload["run_dir"]))
        if run_dir is None:
            return command_error("path_outside_workspace", "Run directory must exist under workspace/")
    return command_ok(build_runtime_replay_status(project_path=project_path, run_dir=run_dir))


def _runtime_replay_admission_witness(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_replay_admission_witness import (
        build_worldbridge_replay_admission_witness,
    )

    raw_run_dir = payload.get("run_dir")
    if not isinstance(raw_run_dir, str) or not raw_run_dir:
        return command_error("run_dir_required", "run_dir is required")
    run_dir = _resolve_workspace_path(raw_run_dir)
    if run_dir is None:
        return command_error("path_outside_workspace", "Run directory must exist under workspace/")
    project_path = None
    project_lock = None
    if payload.get("project_path"):
        project_path = _resolve_workspace_path(str(payload["project_path"]))
        if project_path is None:
            return command_error("path_outside_workspace", "Project path must exist under workspace/")
        lock_path = project_path / "project.lock.json"
        if lock_path.is_file():
            try:
                project_lock = _read_json(lock_path)
            except (OSError, ValueError, json.JSONDecodeError):
                return command_error("project_lock_invalid", "project.lock.json is not valid JSON")
    try:
        return command_ok(build_worldbridge_replay_admission_witness(
            run_dir=run_dir, project_path=project_path, project_lock=project_lock
        ))
    except (OSError, TypeError, ValueError) as exc:
        return command_error("replay_witness_rejected", str(exc) or type(exc).__name__)


def _runtime_worldbridge_status(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

    project_path = None
    if payload.get("project_path"):
        project_path = _resolve_workspace_path(str(payload["project_path"]))
        if project_path is None:
            return command_error("path_outside_workspace", "Project path must exist under workspace/")
    return command_ok(build_runtime_worldbridge_status(project_path=project_path))


def _runtime_worldbridge_quarantine_diagnostic(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
    )

    host = get_worldbridge_quarantine_diagnostic_host(context)
    return command_ok(host.query_worldbridge_quarantine_diagnostic())


def _runtime_worldbridge_provenance_receipt(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_e512_provenance_receipt import (
        build_worldbridge_e512_provenance_receipt_status,
    )
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
    )

    host = get_worldbridge_quarantine_diagnostic_host(context)
    provider = getattr(host, "query_worldbridge_e512_provenance_receipt", None)
    if not callable(provider):
        return command_ok(build_worldbridge_e512_provenance_receipt_status())
    try:
        return command_ok(build_worldbridge_e512_provenance_receipt_status(provider()))
    except Exception:
        return command_ok(build_worldbridge_e512_provenance_receipt_status({}))


def _runtime_worldbridge_quarantine_lifecycle_correlation(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_lifecycle_host,
    )

    host = get_worldbridge_quarantine_lifecycle_host(context)
    return command_ok(host.query_worldbridge_quarantine_lifecycle_correlation())


def _worldbridge_artifact_import_diagnostic(host: Any) -> dict[str, Any] | None:
    """Expose only the bounded artifact rejection record to presentation consumers."""
    diagnostic = host.query_worldbridge_quarantine_diagnostic()
    nested = diagnostic.get("restore_diagnostic") if isinstance(diagnostic, Mapping) else None
    if not isinstance(nested, Mapping) or nested.get("code") != "worldbridge_checkpoint_artifact_rejected":
        return None
    return {
        "recorded": True,
        "schema_version": nested.get("schema_version"),
        "code": nested.get("code"),
        "errors": nested.get("errors"),
        "diagnostic_digest": nested.get("diagnostic_digest"),
    }


def _worldbridge_replay_persistence_diagnostic(host: Any) -> dict[str, Any] | None:
    diagnostic = host.query_worldbridge_quarantine_diagnostic()
    nested = diagnostic.get("restore_diagnostic") if isinstance(diagnostic, Mapping) else None
    if not isinstance(nested, Mapping) or nested.get("code") != "worldbridge_replay_persistence_rejected":
        return None
    return {
        "recorded": True,
        "schema_version": nested.get("schema_version"),
        "code": nested.get("code"),
        "errors": nested.get("errors"),
        "diagnostic_digest": nested.get("diagnostic_digest"),
    }


def _runtime_worldbridge_quarantine_operator_presentation(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
        present_worldbridge_quarantine_lifecycle,
    )
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
        get_worldbridge_quarantine_lifecycle_host,
    )

    source = get_worldbridge_quarantine_lifecycle_host(context).query_worldbridge_quarantine_lifecycle_correlation()
    diagnostic_host = get_worldbridge_quarantine_diagnostic_host(context)
    return command_ok(present_worldbridge_quarantine_lifecycle(
        source,
        artifact_import_diagnostic=_worldbridge_artifact_import_diagnostic(diagnostic_host),
        replay_persistence_diagnostic=_worldbridge_replay_persistence_diagnostic(diagnostic_host),
    ))


def _runtime_worldbridge_quarantine_operator_presentation_export(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
        present_worldbridge_quarantine_lifecycle,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
        export_worldbridge_quarantine_operator_presentation,
    )
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
        get_worldbridge_quarantine_lifecycle_host,
    )

    source = get_worldbridge_quarantine_lifecycle_host(context).query_worldbridge_quarantine_lifecycle_correlation()
    diagnostic_host = get_worldbridge_quarantine_diagnostic_host(context)
    presentation = present_worldbridge_quarantine_lifecycle(
        source,
        artifact_import_diagnostic=_worldbridge_artifact_import_diagnostic(diagnostic_host),
        replay_persistence_diagnostic=_worldbridge_replay_persistence_diagnostic(diagnostic_host),
    )
    return command_ok(export_worldbridge_quarantine_operator_presentation(presentation))


def _runtime_worldbridge_quarantine_operator_presentation_export_audit(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
        present_worldbridge_quarantine_lifecycle,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
        export_worldbridge_quarantine_operator_presentation,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
        audit_worldbridge_quarantine_operator_presentation_export,
    )
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
        get_worldbridge_quarantine_lifecycle_host,
    )

    source = get_worldbridge_quarantine_lifecycle_host(context).query_worldbridge_quarantine_lifecycle_correlation()
    diagnostic_host = get_worldbridge_quarantine_diagnostic_host(context)
    presentation = present_worldbridge_quarantine_lifecycle(
        source,
        artifact_import_diagnostic=_worldbridge_artifact_import_diagnostic(diagnostic_host),
        replay_persistence_diagnostic=_worldbridge_replay_persistence_diagnostic(diagnostic_host),
    )
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    return command_ok(audit_worldbridge_quarantine_operator_presentation_export(export_record))


def _runtime_worldbridge_quarantine_operator_evidence_bundle(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import (
        consume_worldbridge_quarantine_operator_evidence_pair,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
        present_worldbridge_quarantine_lifecycle,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export import (
        export_worldbridge_quarantine_operator_presentation,
    )
    from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_export_audit import (
        audit_worldbridge_quarantine_operator_presentation_export,
    )
    from core.VitaLoom.simulation.worldbridge_quarantine_diagnostic_host import (
        get_worldbridge_quarantine_diagnostic_host,
        get_worldbridge_quarantine_lifecycle_host,
    )

    source = get_worldbridge_quarantine_lifecycle_host(context).query_worldbridge_quarantine_lifecycle_correlation()
    diagnostic_host = get_worldbridge_quarantine_diagnostic_host(context)
    presentation = present_worldbridge_quarantine_lifecycle(
        source,
        artifact_import_diagnostic=_worldbridge_artifact_import_diagnostic(diagnostic_host),
        replay_persistence_diagnostic=_worldbridge_replay_persistence_diagnostic(diagnostic_host),
    )
    export_record = export_worldbridge_quarantine_operator_presentation(presentation)
    audit = audit_worldbridge_quarantine_operator_presentation_export(export_record)
    return command_ok(consume_worldbridge_quarantine_operator_evidence_pair(export_record, audit))


def _runtime_worldbridge_mapping_audit(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit

    return command_ok(build_worldbridge_mapping_audit())


def _runtime_worldbridge_component_decision(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_component_decision import (
        build_worldbridge_component_decision,
    )

    return command_ok(build_worldbridge_component_decision())


def _runtime_worldbridge_component_projection(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_component_projection import (
        build_worldbridge_component_projection,
    )

    return command_ok(build_worldbridge_component_projection())


def _runtime_worldbridge_component_projection_diagnostics(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.world_bridge_component_projection import (
        build_worldbridge_component_projection_diagnostics,
    )

    return command_ok(build_worldbridge_component_projection_diagnostics())


def _runtime_ps_organism_discovery(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.VitaLoom.simulation.ps_runtime_snapshot_host import (
        get_ps_runtime_snapshot_host,
    )

    host = get_ps_runtime_snapshot_host(context)
    return command_ok(host.discover_ps_runtime_organisms())


def _runtime_ps_organism_snapshot(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.VitaLoom.simulation.ps_runtime_snapshot_host import (
        get_ps_runtime_snapshot_host,
    )

    host = get_ps_runtime_snapshot_host(context)
    return command_ok(
        host.query_ps_runtime_organism_snapshot(payload.get("identity"))
    )


def _runtime_ps_organism_component_projection(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.runtime_snapshot_component_projection import (
        project_ps_runtime_snapshot_components,
    )
    from core.VitaLoom.simulation.ps_runtime_snapshot_host import (
        get_ps_runtime_snapshot_host,
    )

    host = get_ps_runtime_snapshot_host(context)
    snapshot = host.query_ps_runtime_organism_snapshot(payload.get("identity"))
    return command_ok(project_ps_runtime_snapshot_components(snapshot))


def _runtime_sr_selected_entity_snapshot(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.VitaLoom.simulation.sr_selected_identity_host import (
        get_sr_selected_identity_host,
    )

    host = get_sr_selected_identity_host(context)
    return command_ok(
        host.resolve_selected_sr_runtime_entity(
            explicit_identity=payload.get("identity"),
        )
    )


def _runtime_sr_selected_entity_component_projection(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    from core.Lotucosm.runtime.runtime_snapshot_component_projection import (
        project_sr_runtime_snapshot_components,
    )
    from core.VitaLoom.simulation.sr_selected_identity_host import (
        get_sr_selected_identity_host,
    )

    host = get_sr_selected_identity_host(context)
    snapshot = host.resolve_selected_sr_runtime_entity(
        explicit_identity=payload.get("identity"),
    )
    return command_ok(project_sr_runtime_snapshot_components(snapshot))


def _capability_list(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    from core.VitaLoom.core.bundle_paths import resource_root

    path = resource_root() / "builtin" / "package_index.json"
    if not path.is_file():
        return command_error("capability_catalog_missing", "builtin/package_index.json not found")
    data = _read_json(path)
    packages = data.get("packages") if isinstance(data.get("packages"), list) else []
    return command_ok({"catalog_path": str(path), "packages": packages})


def _command_undo(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    return registry.undo_last(context=context)


def _command_redo(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    return registry.redo_last(context=context)


def _command_undo_project(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    return registry.undo_project(str(payload.get("project_path", "")), context=context)


def _command_redo_project(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    registry = context.get("command_registry")
    if not isinstance(registry, CommandRegistry):
        return command_error("registry_unavailable", "Command Registry context is unavailable")
    return registry.redo_project(str(payload.get("project_path", "")), context=context)


def _load_catalog_packages() -> list[dict[str, Any]]:
    from core.VitaLoom.core.bundle_paths import resource_root

    path = resource_root() / "builtin" / "package_index.json"
    data = _read_json(path) if path.is_file() else {}
    packages = data.get("packages") if isinstance(data.get("packages"), list) else []
    return [dict(pkg) for pkg in packages if isinstance(pkg, Mapping)]


def _load_project(project: Path) -> dict[str, Any]:
    project_json = project / "project.json"
    if not project_json.is_file():
        raise FileNotFoundError("project.json not found")
    return _read_json(project_json)


def _write_project(project: Path, data: Mapping[str, Any]) -> None:
    """Persist a project manifest only when its derived lock also commits."""

    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    manifest_before = manifest_path.read_bytes()
    lock_before = lock_path.read_bytes() if lock_path.is_file() else None
    _write_json(manifest_path, data)
    if _refresh_project_lock(project):
        return
    try:
        manifest_path.write_bytes(manifest_before)
        if lock_before is None:
            lock_path.unlink(missing_ok=True)
        else:
            lock_path.write_bytes(lock_before)
    except OSError as exc:
        raise RuntimeError(
            f"project_lock_refresh_failed; manifest rollback failed: {exc}"
        ) from exc
    raise RuntimeError("project_lock_refresh_failed; project manifest was rolled back")


def _package_state(data: dict[str, Any]) -> dict[str, Any]:
    state = data.get("package_state")
    if not isinstance(state, dict):
        state = {}
    state.setdefault("installed", {})
    state.setdefault("version_overrides", {})
    state.setdefault("operation_log", [])
    state.setdefault("history", [])
    state.setdefault("rollback_points", [])
    data["package_state"] = state
    return state


def _required_capabilities(data: dict[str, Any]) -> dict[str, str]:
    raw = data.get("required_capabilities")
    if not isinstance(raw, dict):
        raw = {}
    cleaned = {str(k): str(v or ">=1.0.0") for k, v in raw.items() if str(k).strip()}
    data["required_capabilities"] = cleaned
    return cleaned


def _effective_required_plugin_ids(data: dict[str, Any]) -> set[str]:
    ids = set(_required_capabilities(data).keys())
    old_required = data.get("required_packages")
    if isinstance(old_required, list):
        ids.update(str(item) for item in old_required if str(item).strip())
    return ids


def _disabled_plugins(data: dict[str, Any]) -> list[str]:
    raw = data.get("disabled_plugins")
    if not isinstance(raw, list):
        raw = []
    cleaned = [str(item) for item in raw if str(item).strip()]
    data["disabled_plugins"] = cleaned
    return cleaned


def _plugin_ids_for_row(row: Mapping[str, Any]) -> list[str]:
    plugins = row.get("plugins")
    if not isinstance(plugins, list):
        return []
    return [str(item).strip() for item in plugins if str(item).strip()]


def _append_plugin_history(data: dict[str, Any], action: str, plugin_id: str, metadata: Mapping[str, Any] | None = None) -> None:
    from datetime import datetime

    state = _package_state(data)
    history = state.get("history")
    if not isinstance(history, list):
        history = []
    entry = {
        "action": action,
        "plugin_id": plugin_id,
        "at": datetime.now().isoformat(timespec="seconds"),
        "metadata": dict(metadata or {}),
    }
    history.append(entry)
    state["history"] = history[-200:]
    op_log = state.get("operation_log")
    if not isinstance(op_log, list):
        op_log = []
    op_log.append(entry)
    state["operation_log"] = op_log[-200:]


def _refresh_project_lock(project: Path) -> bool:
    try:
        from core.VitaLoom.core.bundle_paths import resource_root
        from core.VitaLoom.project.project_write_authority import (
            project_write_interlock,
        )
        from core.VitaLoom.suite.project_lock import ensure_project_lock

        with project_write_interlock(
            project,
            authority_action="project_lock_refresh",
        ):
            ensure_project_lock(
                project,
                repo_root=resource_root(),
                overwrite=True,
            )
        return True
    except Exception:
        return False


def _persist_project_manifest_and_lock(
    project: Path,
    data: Mapping[str, Any],
    *,
    manifest_before: bytes,
    lock_before: bytes | None,
) -> bool:
    """Commit project metadata only when its derived lock can be committed too."""

    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    _write_json(project / "project.json", data)
    if _refresh_project_lock(project):
        return True
    try:
        manifest_path.write_bytes(manifest_before)
        if lock_before is None:
            lock_path.unlink(missing_ok=True)
        else:
            lock_path.write_bytes(lock_before)
    except OSError:
        # The mutation remains failed even if recovery itself cannot be completed.
        return False
    return False


def _project_for_plugin_command(payload: Mapping[str, Any]) -> tuple[Path | None, dict[str, Any] | None]:
    project = _resolve_workspace_path(str(payload.get("project_path", "")))
    if project is None:
        return None, None
    try:
        return project, _load_project(project)
    except (OSError, FileNotFoundError, json.JSONDecodeError):
        return project, None


def _project_addons(project: Path) -> list[dict[str, Any]]:
    addons_dir = project / "addons"
    if not addons_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for child in sorted(p for p in addons_dir.iterdir() if p.is_dir()):
        plugin_id = child.name
        manifest = child / "plugin.json"
        version = "0.0.0"
        display_name = child.name
        if manifest.is_file():
            try:
                meta = _read_json(manifest)
                plugin_id = str(meta.get("id") or meta.get("name") or plugin_id)
                display_name = str(meta.get("display_name") or meta.get("name") or display_name)
                version = str(meta.get("version") or version)
            except (OSError, json.JSONDecodeError):
                pass
        rows.append(
            {
                "id": plugin_id,
                "display_name": display_name,
                "version": version,
                "source": "project_addon",
                "origin": "project",
                "status": "optional",
                "path": str(child),
                "plugins": [plugin_id],
            }
        )
    return rows


def _workspace_extensions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = _workspace_root() / "extensions"
    for scope in ("user", "community"):
        scope_root = root / scope
        if not scope_root.is_dir():
            continue
        for child in sorted(p for p in scope_root.iterdir() if p.is_dir()):
            rows.append(
                {
                    "id": child.name,
                    "display_name": child.name,
                    "version": "0.0.0",
                    "source": f"workspace_{scope}",
                    "origin": "workspace_extension",
                    "status": "available",
                    "path": str(child),
                    "plugins": [child.name],
                    "enabled": False,
                }
            )
    return rows


def _plugin_rows(project: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    required = _required_capabilities(data)
    effective_required = _effective_required_plugin_ids(data)
    disabled = set(_disabled_plugins(data))
    state = _package_state(data)
    installed = state.get("installed") if isinstance(state.get("installed"), dict) else {}
    lock = _read_json(project / "project.lock.json") if (project / "project.lock.json").is_file() else {}
    locked = lock.get("resolved_capabilities") if isinstance(lock.get("resolved_capabilities"), dict) else {}
    rows: list[dict[str, Any]] = []

    for pkg in _load_catalog_packages():
        pkg_id = str(pkg.get("id", "")).strip()
        if not pkg_id:
            continue
        row = dict(pkg)
        row["id"] = pkg_id
        row_plugins = _plugin_ids_for_row(row)
        row["project_required"] = pkg_id in effective_required
        row_disabled = pkg_id in disabled or bool(row_plugins and all(p in disabled for p in row_plugins))
        row["project_enabled"] = pkg_id in effective_required and not row_disabled
        row["project_locked_version"] = str(locked.get(pkg_id, "") or "")
        row["project_installed"] = pkg_id in installed
        row["source_kind"] = "official"
        rows.append(row)

    for row in _project_addons(project):
        plugin_id = str(row["id"])
        row["project_required"] = plugin_id in effective_required or plugin_id in installed
        row["project_enabled"] = plugin_id not in disabled and row["project_required"]
        row["project_locked_version"] = str(locked.get(plugin_id, "") or "")
        row["project_installed"] = plugin_id in installed or row["source"] == "project_addon"
        row["source_kind"] = "project_addon"
        rows.append(row)

    for row in _workspace_extensions():
        plugin_id = str(row["id"])
        row["project_required"] = plugin_id in effective_required or plugin_id in installed
        row["project_enabled"] = plugin_id not in disabled and row["project_required"]
        row["project_locked_version"] = str(locked.get(plugin_id, "") or "")
        row["project_installed"] = plugin_id in installed
        row["source_kind"] = "workspace_extension_source"
        rows.append(row)
    return rows


def _find_plugin(project: Path, data: dict[str, Any], plugin_id: str) -> dict[str, Any] | None:
    for row in _plugin_rows(project, data):
        if str(row.get("id", "")) == plugin_id:
            return row
    return None


def _find_plugin_target(
    project: Path, data: dict[str, Any], plugin_id: str
) -> tuple[dict[str, Any] | None, str, str]:
    """Resolve a user-facing plugin id to either a package or a plugin inside a package."""
    for row in _plugin_rows(project, data):
        row_id = str(row.get("id", "")).strip()
        if row_id == plugin_id:
            return row, "package", row_id
        if plugin_id in _plugin_ids_for_row(row):
            return row, "contained_plugin", row_id
    return None, "", ""


def _plugin_list(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    return command_ok(
        {
            "project_path": str(project),
            "plugins": _plugin_rows(project, data),
            "note": "workspace extensions are sources only; they are not globally enabled",
        }
    )


def _plugin_resolve(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    try:
        from core.VitaLoom.core.bundle_paths import resource_root
        from core.VitaLoom.suite.project_lock import build_project_lock_for_path, resolve_project_runtime

        suggested = build_project_lock_for_path(project, repo_root=resource_root())
        resolved = resolve_project_runtime(project, repo_root=resource_root())
        return command_ok(
            {
                "project_path": str(project),
                "suggested_lock": suggested,
                "lock_status": resolved.lock_status_text,
                "lock_admission": resolved.lock_admission_code,
                "missing_capabilities": list(resolved.missing_capabilities),
                "blocking_issue_codes": list(resolved.blocking_issue_codes),
                "blocking_issue_summary": resolved.blocking_issue_summary,
            }
        )
    except Exception as exc:
        return command_error("plugin_resolve_failed", str(exc))


def _plugin_enable(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    return _set_plugin_enabled(payload, enabled=True)


def _plugin_disable(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    return _set_plugin_enabled(payload, enabled=False)


def _set_plugin_enabled(payload: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    plugin_id = str(payload.get("plugin_id", "")).strip()
    if not plugin_id:
        return command_error("invalid_plugin_id", "plugin_id is required")
    row, target_kind, package_id = _find_plugin_target(project, data, plugin_id)
    if row is None:
        return command_error("plugin_not_found", f"Plugin not found: {plugin_id}")
    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    manifest_before = manifest_path.read_bytes()
    lock_before = lock_path.read_bytes() if lock_path.is_file() else None
    required = _required_capabilities(data)
    disabled = _disabled_plugins(data)
    affected = _plugin_ids_for_row(row)
    if target_kind == "contained_plugin":
        affected = [plugin_id]
    elif not affected:
        affected = [package_id or plugin_id]
    package_version = str(row.get("version", "1.0.0") or "1.0.0")
    if enabled:
        required.setdefault(package_id or plugin_id, f">={package_version}")
        disabled = [item for item in disabled if item not in set(affected + [package_id, plugin_id])]
        event = "plugin_enabled"
        action = "enable"
    else:
        for item in affected:
            if item not in disabled:
                disabled.append(item)
        if target_kind == "package" and package_id and package_id not in disabled:
            disabled.append(package_id)
        event = "plugin_disabled"
        action = "disable"
    data["disabled_plugins"] = sorted(set(disabled))
    _append_plugin_history(
        data,
        action,
        plugin_id,
        {"target_kind": target_kind, "package_id": package_id, "affected_plugins": affected},
    )
    lock_refreshed = _persist_project_manifest_and_lock(
        project,
        data,
        manifest_before=manifest_before,
        lock_before=lock_before,
    )
    if not lock_refreshed:
        return command_error(
            "project_lock_refresh_failed",
            "Project manifest and lock were not committed",
            details={"project_path": str(project), "lock_refreshed": False},
        )
    return command_ok(
        {
            "project_path": str(project),
            "plugin_id": plugin_id,
            "package_id": package_id,
            "target_kind": target_kind,
            "affected_plugins": affected,
            "enabled": enabled,
            "lock_refreshed": lock_refreshed,
        },
        events=[event],
    )


def _plugin_install(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    manifest_before = manifest_path.read_bytes()
    lock_before = lock_path.read_bytes() if lock_path.is_file() else None
    plugin_id = str(payload.get("plugin_id", "")).strip()
    if not plugin_id:
        return command_error("invalid_plugin_id", "plugin_id is required")
    source = str(payload.get("source", "") or "official").strip() or "official"
    raw_path = str(payload.get("path", "") or "").strip()
    if raw_path:
        candidate = _resolve_workspace_path(raw_path, must_exist=True)
        if candidate is None:
            return command_error("path_outside_workspace", "Plugin source path must exist under workspace/")
        source_path = str(candidate)
    else:
        source_path = ""
    row = _find_plugin(project, data, plugin_id)
    version = str(payload.get("version", "") or (row or {}).get("version", "") or "0.0.0")
    state = _package_state(data)
    installed = state.get("installed")
    if not isinstance(installed, dict):
        installed = {}
    installed[plugin_id] = {
        "version": version,
        "source": source,
        "path": source_path,
        "scope": "project",
    }
    state["installed"] = installed
    _required_capabilities(data).setdefault(plugin_id, f">={version}")
    data["disabled_plugins"] = [item for item in _disabled_plugins(data) if item != plugin_id]
    _append_plugin_history(data, "install", plugin_id, {"source": source, "path": source_path})
    lock_refreshed = _persist_project_manifest_and_lock(
        project,
        data,
        manifest_before=manifest_before,
        lock_before=lock_before,
    )
    if not lock_refreshed:
        return command_error(
            "project_lock_refresh_failed",
            "Project manifest and lock were not committed",
            details={"project_path": str(project), "lock_refreshed": False},
        )
    return command_ok(
        {
            "project_path": str(project),
            "plugin_id": plugin_id,
            "version": version,
            "source": source,
            "path": source_path,
            "lock_refreshed": lock_refreshed,
        },
        events=["plugin_installed"],
    )


def _plugin_uninstall(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    manifest_path = project / "project.json"
    lock_path = project / "project.lock.json"
    manifest_before = manifest_path.read_bytes()
    lock_before = lock_path.read_bytes() if lock_path.is_file() else None
    plugin_id = str(payload.get("plugin_id", "")).strip()
    if not plugin_id:
        return command_error("invalid_plugin_id", "plugin_id is required")

    row, target_kind, package_id = _find_plugin_target(project, data, plugin_id)
    state = _package_state(data)
    installed = state.get("installed")
    if not isinstance(installed, dict):
        installed = {}
    if row is None and plugin_id in installed:
        row = {"id": plugin_id, "plugins": []}
        target_kind = "package"
        package_id = plugin_id
    if row is None:
        return command_error("plugin_not_found", f"Plugin not found: {plugin_id}")

    package_id = package_id or plugin_id
    affected = _plugin_ids_for_row(row)
    if target_kind == "contained_plugin":
        affected = [plugin_id]
    elif not affected:
        affected = [package_id]

    installed.pop(package_id, None)
    installed.pop(plugin_id, None)
    state["installed"] = installed
    version_overrides = state.get("version_overrides")
    if isinstance(version_overrides, dict):
        version_overrides.pop(package_id, None)
        version_overrides.pop(plugin_id, None)
        state["version_overrides"] = version_overrides

    top_overrides = data.get("package_version_overrides")
    if isinstance(top_overrides, dict):
        top_overrides.pop(package_id, None)
        top_overrides.pop(plugin_id, None)
        data["package_version_overrides"] = top_overrides

    required = _required_capabilities(data)
    required.pop(package_id, None)
    required.pop(plugin_id, None)
    for legacy_key in ("required_packages", "recommended_packages"):
        legacy = data.get(legacy_key)
        if isinstance(legacy, list):
            data[legacy_key] = [
                item
                for item in legacy
                if str(item).strip() not in {package_id, plugin_id}
            ]

    remove_disabled = set(affected + [package_id, plugin_id])
    data["disabled_plugins"] = [
        item for item in _disabled_plugins(data) if item not in remove_disabled
    ]
    _append_plugin_history(
        data,
        "uninstall",
        plugin_id,
        {"target_kind": target_kind, "package_id": package_id, "affected_plugins": affected},
    )
    lock_refreshed = _persist_project_manifest_and_lock(
        project,
        data,
        manifest_before=manifest_before,
        lock_before=lock_before,
    )
    if not lock_refreshed:
        return command_error(
            "project_lock_refresh_failed",
            "Project manifest and lock were not committed",
            details={"project_path": str(project), "lock_refreshed": False},
        )
    return command_ok(
        {
            "project_path": str(project),
            "plugin_id": plugin_id,
            "package_id": package_id,
            "target_kind": target_kind,
            "affected_plugins": affected,
            "lock_refreshed": lock_refreshed,
        },
        events=["plugin_uninstalled"],
    )


def _export_player_prepare(payload: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    project, data = _project_for_plugin_command(payload)
    if project is None:
        return command_error("path_outside_workspace", "Project path must exist under workspace/")
    if data is None:
        return command_error("project_not_found", "project.json not found")
    closure = _build_asset_export_closure(project, data)
    lock_path = project / "project.lock.json"
    ready = bool(lock_path.is_file()) and bool(closure.get("ready"))
    return command_ok(
        {
            "project_path": str(project),
            "project_lock": str(lock_path) if lock_path.is_file() else "",
            "enabled_plugins": closure["enabled_plugins"],
            "asset_dependencies": {
                "total_edges": len(closure["dependency_edges"]),
                "edges": closure["dependency_edges"],
                "missing_scripts": closure["missing_scripts"],
                "missing_assets": closure["missing_assets"],
                "missing_total": closure["missing_total"],
                "missing_by_kind": closure["missing_by_kind"],
                "outside_project": closure["outside_project"],
                "outside_project_total": closure["outside_project_total"],
                "outside_project_by_kind": closure["outside_project_by_kind"],
                "invalid_references": closure["invalid_references"],
                "invalid_total": closure["invalid_total"],
                "invalid_by_kind": closure["invalid_by_kind"],
                "malformed_scenes": closure["malformed_scenes"],
            },
            "asset_export_closure": closure,
            "ready": ready,
        }
    )
