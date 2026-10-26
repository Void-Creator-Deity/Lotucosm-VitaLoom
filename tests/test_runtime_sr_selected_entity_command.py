# -*- coding: utf-8 -*-
"""Dedicated selected SR entity snapshot Command Registry Interface."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import ServiceRegistry
from core.VitaLoom.core.service_keys import SR_SELECTED_IDENTITY_HOST


COMMAND_ID = "runtime.sr.selected_entity_snapshot"


class _Host:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def resolve_selected_sr_runtime_entity(
        self,
        *,
        explicit_identity: object | None = None,
        selection_scene_path: str | None = None,
    ) -> dict[str, object]:
        self.calls.append({"explicit_identity": explicit_identity})
        return json.loads(json.dumps(self.result))


class _Context:
    def __init__(self, host: object | None = None) -> None:
        self.services = ServiceRegistry()
        if host is not None:
            self.services.register(SR_SELECTED_IDENTITY_HOST, host)


def _ok_result() -> dict[str, object]:
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
            "entity_id": "entity_1",
        },
        "snapshot": {
            "source": "read_only_json_snapshot",
            "entity_id": "entity_1",
            "serialized_scene_counterpart": True,
            "position": [1.0, 2.0],
        },
    }


def test_command_metadata_is_read_only_and_gui_optional() -> None:
    spec = get_command_registry().describe(COMMAND_ID)
    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.engine.sr2d"
    assert spec["input_schema"]["properties"]["identity"]["type"] == "object"


def test_command_without_registered_host_returns_deterministic_unavailable() -> None:
    result = get_command_registry().run(COMMAND_ID, {}, context={"editor_context": _Context()})
    assert result["ok"] is True
    assert result["result"]["status"] == "unavailable"
    assert result["result"]["reason"] == "selected_identity_host_unavailable"


def test_command_discovers_current_selection_without_epoch_input() -> None:
    host = _Host(_ok_result())
    result = get_command_registry().run(
        COMMAND_ID,
        {},
        context={"editor_context": _Context(host)},
    )
    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
    assert host.calls == [{"explicit_identity": None}]


def test_command_forwards_explicit_identity_for_stale_queries() -> None:
    stale = _ok_result()
    stale["status"] = "stale"
    stale.pop("snapshot")
    host = _Host(stale)
    identity = {
        "track": "sr_play",
        "runtime_epoch": "sr_old",
        "scene_path": "scenes/demo.pond",
        "entity_id": "entity_1",
    }
    result = get_command_registry().run(
        COMMAND_ID,
        {"identity": identity},
        context={"editor_context": _Context(host)},
    )
    assert result["ok"] is True
    assert result["result"]["status"] == "stale"
    assert host.calls == [{"explicit_identity": identity}]


def test_command_result_is_copy_isolated() -> None:
    host = _Host(_ok_result())
    context = {"editor_context": _Context(host)}
    first = get_command_registry().run(COMMAND_ID, {}, context=context)["result"]
    first["snapshot"]["position"][0] = 999.0
    second = get_command_registry().run(COMMAND_ID, {}, context=context)["result"]
    assert second["snapshot"]["position"] == [1.0, 2.0]


def test_command_discovery_and_unavailable_result_without_pyqt6() -> None:
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
import sys

real_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name == "PyQt6" or name.startswith("PyQt6."):
        raise ImportError("PyQt6 blocked for headless proof")
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
from core.VitaLoom.commands.registry import get_command_registry
registry = get_command_registry()
spec = registry.describe("runtime.sr.selected_entity_snapshot")
result = registry.run("runtime.sr.selected_entity_snapshot", {})
print(json.dumps({"spec": spec, "result": result}, ensure_ascii=False))
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
    assert payload["spec"]["requires_gui"] is False
    assert payload["result"]["ok"] is True
    assert payload["result"]["result"]["status"] == "unavailable"
