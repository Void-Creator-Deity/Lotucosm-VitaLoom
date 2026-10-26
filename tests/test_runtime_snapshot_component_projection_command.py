# -*- coding: utf-8 -*-
"""Command/MCP surfaces for track-specific runtime component projection."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.VitaLoom.commands import mcp_adapter
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import (
    PS_RUNTIME_SNAPSHOT_HOST,
    SR_SELECTED_IDENTITY_HOST,
)


PS_COMMAND = "runtime.ps.organism_component_projection"
SR_COMMAND = "runtime.sr.selected_entity_component_projection"


def _ps_identity() -> dict[str, str]:
    return {
        "track": "ps_batch",
        "run_id": "ps_run",
        "organism_id": "org_1",
    }


def _ps_snapshot() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "ok",
        "scope": "ps_runtime_organism",
        "authority": "ps_runtime_snapshot_authority",
        "track": "ps_batch",
        "read_only": True,
        "identity_relation": "run_scoped_not_cross_track",
        "identity": _ps_identity(),
        "revision": 4,
        "snapshot": {
            "source": "read_only_json_snapshot",
            "organism_id": "org_1",
            "component_facts": [
                {
                    "source": "ps_component_registry",
                    "identity_relation": "ps_component_registry_member",
                    "component_id": "sensor_1",
                    "component_type": "sensor",
                    "location": "external",
                    "acquired": False,
                    "congenital": True,
                    "attach_point": None,
                    "connection_count": 0,
                    "inspectable_properties": {"signal_threshold": 0.2},
                    "component_fields": {"signal_threshold": 0.2},
                }
            ],
        },
    }


def _sr_snapshot() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "ok",
        "scope": "selected_sr_runtime_entity",
        "authority": "sr_selected_identity_correlation",
        "track": "sr_play",
        "read_only": True,
        "selection_relation": "scene_correlated_not_unified",
        "identity": {
            "track": "sr_play",
            "runtime_epoch": "sr_epoch",
            "scene_path": "scenes/demo.pond",
            "entity_id": "org_1",
        },
        "revision": 2,
        "snapshot": {
            "source": "read_only_json_snapshot",
            "entity_id": "org_1",
            "component_facts": [
                {
                    "source": "sr_attached_runtime_entity",
                    "identity_relation": "attached_projection_not_ps_component_equivalence",
                    "component_id": "sensor_1",
                    "component_type": "sensor",
                    "location": "attached",
                    "attach_point": [1.0, 2.0],
                    "connection_count": 1,
                    "inspectable_properties": {},
                    "component_fields": {},
                }
            ],
        },
    }


class _PsHost:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def discover_ps_runtime_organisms(self) -> dict[str, Any]:
        return {"status": "ok"}

    def query_ps_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]:
        self.calls.append(identity)
        return _ps_snapshot()


class _SrHost:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def resolve_selected_sr_runtime_entity(
        self,
        *,
        explicit_identity: object | None = None,
        selection_scene_path: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(explicit_identity)
        return _sr_snapshot()


class _Context:
    def __init__(self, *, ps_host: object | None = None, sr_host: object | None = None):
        self.services = ServiceRegistry()
        if ps_host is not None:
            self.services.register(PS_RUNTIME_SNAPSHOT_HOST, ps_host)
        if sr_host is not None:
            self.services.register(SR_SELECTED_IDENTITY_HOST, sr_host)


def test_projection_commands_are_track_specific_read_only_interfaces() -> None:
    registry = get_command_registry()
    ps_spec = registry.describe(PS_COMMAND)
    sr_spec = registry.describe(SR_COMMAND)

    assert ps_spec["mutates"] is False
    assert ps_spec["requires_gui"] is False
    assert ps_spec["capability"] == "vitalloom.pvaec.simulation"
    assert ps_spec["input_schema"]["required"] == ["identity"]
    assert sr_spec["mutates"] is False
    assert sr_spec["requires_gui"] is False
    assert sr_spec["capability"] == "vitalloom.engine.sr2d"


def test_ps_command_queries_explicit_identity_then_projects_mapping_only() -> None:
    host = _PsHost()
    result = get_command_registry().run(
        PS_COMMAND,
        {"identity": _ps_identity()},
        context={"editor_context": _Context(ps_host=host)},
    )

    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
    assert result["result"]["component_count"] == 1
    assert result["result"]["track"] == "ps_batch"
    assert host.calls == [_ps_identity()]


def test_sr_command_reuses_selected_identity_host_without_unifying_identity() -> None:
    host = _SrHost()
    explicit = _sr_snapshot()["identity"]
    result = get_command_registry().run(
        SR_COMMAND,
        {"identity": explicit},
        context={"editor_context": _Context(sr_host=host)},
    )

    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
    assert result["result"]["identity_relation"] == (
        "attached_projection_not_ps_component_equivalence"
    )
    assert host.calls == [explicit]


def test_mcp_helpers_delegate_to_command_registry(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_run(command_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        calls.append((command_id, payload))
        return {"ok": True, "result": {"status": "ok"}}

    monkeypatch.setattr(mcp_adapter, "run_command", fake_run)
    assert mcp_adapter.get_runtime_ps_organism_component_projection(
        _ps_identity()
    )["ok"] is True
    assert mcp_adapter.get_runtime_sr_selected_entity_component_projection()["ok"] is True
    assert calls == [
        (PS_COMMAND, {"identity": _ps_identity()}),
        (SR_COMMAND, {}),
    ]


def test_projection_commands_are_headless_import_safe() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = (
        root
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    script = r'''
import builtins
import json
real_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name == "PyQt6" or name.startswith("PyQt6."):
        raise ImportError("PyQt6 blocked for headless proof")
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
from core.VitaLoom.commands.registry import get_command_registry
registry = get_command_registry()
results = {
    "ps": registry.run("runtime.ps.organism_component_projection", {"identity": {"track": "ps_batch", "run_id": "ps_x", "organism_id": "org"}}),
    "sr": registry.run("runtime.sr.selected_entity_component_projection", {}),
}
print(json.dumps(results, ensure_ascii=False))
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(runtime), str(root), env.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=root,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["ps"]["result"]["status"] == "unavailable"
    assert payload["sr"]["result"]["status"] == "unavailable"
