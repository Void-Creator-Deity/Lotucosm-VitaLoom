# -*- coding: utf-8 -*-
"""Thin MCP-facing adapter for VitaLoom commands.

This module is intentionally transport-agnostic: an MCP server can import these
functions and expose them as tools without reimplementing engine operations.
"""
from __future__ import annotations

from typing import Any, Mapping

from core.VitaLoom.commands.registry import get_command_registry


def list_commands() -> dict[str, Any]:
    return {"commands": get_command_registry().list()}


def describe_command(command_id: str) -> dict[str, Any]:
    return get_command_registry().describe(command_id)


def run_command(command_id: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return get_command_registry().run(command_id, dict(payload or {}))


def get_project_state(project_path: str) -> dict[str, Any]:
    return run_command("project.state", {"project_path": project_path})


def get_scene_snapshot(project_path: str = "", scene_path: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if project_path:
        payload["project_path"] = project_path
    if scene_path:
        payload["scene_path"] = scene_path
    return run_command("scene.summary", payload)


def create_entity(scene_path: str, entity: Mapping[str, Any]) -> dict[str, Any]:
    return run_command("entity.create", {"scene_path": scene_path, "entity": dict(entity)})


def set_transform(
    scene_path: str,
    entity_id: str,
    *,
    position: Any = None,
    rotation: Any = None,
    scale: Any = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"scene_path": scene_path, "entity_id": entity_id}
    if position is not None:
        payload["position"] = position
    if rotation is not None:
        payload["rotation"] = rotation
    if scale is not None:
        payload["scale"] = scale
    return run_command("transform.set", payload)


def set_script_property(
    scene_path: str,
    entity_id: str,
    script: str,
    property_path: str,
    value: Any,
) -> dict[str, Any]:
    return run_command(
        "script.set_property",
        {
            "scene_path": scene_path,
            "entity_id": entity_id,
            "script": script,
            "property_path": property_path,
            "value": value,
        },
    )


def undo_last() -> dict[str, Any]:
    return run_command("command.undo", {})


def redo_last() -> dict[str, Any]:
    return run_command("command.redo", {})


def undo_project(project_path: str) -> dict[str, Any]:
    return run_command("command.undo_project", {"project_path": project_path})


def redo_project(project_path: str) -> dict[str, Any]:
    return run_command("command.redo_project", {"project_path": project_path})


def get_runtime_replay_status(project_path: str = "", run_dir: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if project_path:
        payload["project_path"] = project_path
    if run_dir:
        payload["run_dir"] = run_dir
    return run_command("runtime.replay.status", payload)


def get_runtime_replay_admission_witness(project_path: str = "", run_dir: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"run_dir": run_dir}
    if project_path:
        payload["project_path"] = project_path
    return run_command("runtime.replay.admission_witness", payload)


def get_runtime_worldbridge_status(project_path: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if project_path:
        payload["project_path"] = project_path
    return run_command("runtime.worldbridge.status", payload)


def get_runtime_worldbridge_quarantine_diagnostic() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_diagnostic", {})


def get_runtime_worldbridge_quarantine_lifecycle_correlation() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_lifecycle_correlation", {})


def get_runtime_worldbridge_quarantine_operator_presentation() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_operator_presentation", {})


def get_runtime_worldbridge_quarantine_operator_presentation_export() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_operator_presentation_export", {})


def get_runtime_worldbridge_quarantine_operator_presentation_export_audit() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_operator_presentation_export_audit", {})


def get_runtime_worldbridge_quarantine_operator_evidence_bundle() -> dict[str, Any]:
    return run_command("runtime.worldbridge.quarantine_operator_evidence_bundle", {})


def get_runtime_worldbridge_provenance_receipt() -> dict[str, Any]:
    return run_command("runtime.worldbridge.provenance_receipt", {})


def get_runtime_worldbridge_mapping_audit() -> dict[str, Any]:
    return run_command("runtime.worldbridge.mapping_audit", {})


def get_runtime_worldbridge_component_decision() -> dict[str, Any]:
    return run_command("runtime.worldbridge.component_decision", {})


def get_runtime_worldbridge_component_projection() -> dict[str, Any]:
    return run_command("runtime.worldbridge.component_projection", {})


def get_runtime_worldbridge_component_projection_diagnostics() -> dict[str, Any]:
    return run_command("runtime.worldbridge.component_projection_diagnostics", {})

def get_runtime_ps_organism_discovery() -> dict[str, Any]:
    return run_command("runtime.ps.organism_discovery", {})


def get_runtime_ps_organism_snapshot(identity: Mapping[str, Any]) -> dict[str, Any]:
    return run_command(
        "runtime.ps.organism_snapshot",
        {"identity": dict(identity)},
    )


def get_runtime_ps_organism_component_projection(
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    return run_command(
        "runtime.ps.organism_component_projection",
        {"identity": dict(identity)},
    )


def get_runtime_sr_selected_entity_component_projection(
    identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if identity is not None:
        payload["identity"] = dict(identity)
    return run_command(
        "runtime.sr.selected_entity_component_projection",
        payload,
    )


def inspect_plugin_host(project_path: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if project_path:
        payload["project_path"] = project_path
    return run_command("plugin.host.inspect", payload)


def list_plugin_host_recovery(project_path: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if project_path:
        payload["project_path"] = project_path
    return run_command("plugin.host.recovery.list", payload)


def resolve_plugin_host_recovery(
    project_path: str,
    report_id: str,
    action: str,
    operator_confirmation: str,
) -> dict[str, Any]:
    return run_command(
        "plugin.host.recovery.resolve",
        {
            "project_path": project_path,
            "report_id": report_id,
            "action": action,
            "operator_confirmation": operator_confirmation,
        },
    )
