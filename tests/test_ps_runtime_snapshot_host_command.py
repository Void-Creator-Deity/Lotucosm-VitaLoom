# -*- coding: utf-8 -*-
"""PS runtime discovery and explicit organism snapshot Command Interfaces."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from builtin.editor_extensions.ps_experiment_plugin import PsExperimentPlugin
from core.VitaLoom.commands.mcp_adapter import (
    get_runtime_ps_organism_discovery,
    get_runtime_ps_organism_snapshot,
)
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.core.editor_context import EditorContext, ServiceRegistry
from core.VitaLoom.core.service_keys import PS_EXPERIMENT, PS_RUNTIME_SNAPSHOT_HOST
from core.VitaLoom.simulation.ps_runtime_snapshot_host import (
    IPsRuntimeSnapshotHost,
    PsRuntimeSnapshotHostAdapter,
    get_ps_runtime_snapshot_host,
)


DISCOVERY_COMMAND = "runtime.ps.organism_discovery"
SNAPSHOT_COMMAND = "runtime.ps.organism_snapshot"


def _identity(run_id: str = "ps_run", organism_id: str = "org_1") -> dict[str, str]:
    return {
        "track": "ps_batch",
        "run_id": run_id,
        "organism_id": organism_id,
    }


def _discovery() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "ok",
        "scope": "ps_runtime_population",
        "authority": "ps_runtime_snapshot_authority",
        "track": "ps_batch",
        "read_only": True,
        "identity_relation": "run_scoped_not_cross_track",
        "run_id": "ps_run",
        "revision": 3,
        "organism_count": 1,
        "identities": [_identity()],
    }


def _snapshot(status: str = "ok") -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "scope": "ps_runtime_organism",
        "authority": "ps_runtime_snapshot_authority",
        "track": "ps_batch",
        "read_only": True,
        "identity_relation": "run_scoped_not_cross_track",
        "identity": _identity(),
    }
    if status == "ok":
        result["revision"] = 3
        result["snapshot"] = {
            "source": "read_only_json_snapshot",
            "organism_id": "org_1",
            "position": [1.0, 2.0],
        }
    return result


class _Source:
    def __init__(self) -> None:
        self.discovery_result = _discovery()
        self.snapshot_result = _snapshot()
        self.discovery_calls = 0
        self.query_calls: list[object] = []

    def discover_runtime_organisms(self) -> dict[str, Any]:
        self.discovery_calls += 1
        return self.discovery_result

    def query_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]:
        self.query_calls.append(identity)
        return self.snapshot_result


class _Context:
    def __init__(self, host: object | None = None, *, project_root: Path | None = None) -> None:
        self.services = ServiceRegistry()
        self.project_root = project_root
        self.current_project_path = None
        self.event_bus = None
        self.kernel = None
        if host is not None:
            self.services.register(PS_RUNTIME_SNAPSHOT_HOST, host)


def test_host_adapter_is_a_real_protocol_adapter_and_copy_isolates_results() -> None:
    source = _Source()
    host = PsRuntimeSnapshotHostAdapter(source)

    assert isinstance(host, IPsRuntimeSnapshotHost)
    first_discovery = host.discover_ps_runtime_organisms()
    first_discovery["identities"][0]["organism_id"] = "mutated"
    assert host.discover_ps_runtime_organisms()["identities"][0]["organism_id"] == "org_1"

    first_snapshot = host.query_ps_runtime_organism_snapshot(_identity())
    first_snapshot["snapshot"]["position"][0] = 999.0
    assert host.query_ps_runtime_organism_snapshot(_identity())["snapshot"]["position"] == [1.0, 2.0]
    assert source.discovery_calls == 2
    assert source.query_calls == [_identity(), _identity()]


def test_host_adapter_rejects_invalid_source_and_non_json_results() -> None:
    with pytest.raises(TypeError, match="runtime snapshot source"):
        PsRuntimeSnapshotHostAdapter(object())

    source = _Source()
    source.discovery_result = {"status": "ok", "bad": object()}
    host = PsRuntimeSnapshotHostAdapter(source)
    with pytest.raises(TypeError, match="JSON-compatible object"):
        host.discover_ps_runtime_organisms()


def test_null_host_is_deterministic_and_does_not_guess_selection() -> None:
    host = get_ps_runtime_snapshot_host(_Context())
    discovery = host.discover_ps_runtime_organisms()
    query = host.query_ps_runtime_organism_snapshot(_identity())

    assert discovery["status"] == "unavailable"
    assert discovery["reason"] == "ps_runtime_snapshot_host_unavailable"
    assert discovery["run_id"] is None
    assert discovery["identities"] == []
    assert query["status"] == "unavailable"
    assert query["reason"] == "ps_runtime_snapshot_host_unavailable"
    assert query["identity"] == _identity()
    json.dumps({"discovery": discovery, "query": query}, allow_nan=False)


def test_command_metadata_separates_discovery_from_required_explicit_query() -> None:
    registry = get_command_registry()
    discovery = registry.describe(DISCOVERY_COMMAND)
    snapshot = registry.describe(SNAPSHOT_COMMAND)

    for spec in (discovery, snapshot):
        assert spec["mutates"] is False
        assert spec["requires_gui"] is False
        assert spec["capability"] == "vitalloom.pvaec.simulation"
    assert discovery["input_schema"].get("required", []) == []
    assert snapshot["input_schema"]["required"] == ["identity"]
    assert snapshot["input_schema"]["properties"]["identity"]["type"] == "object"


def test_snapshot_command_rejects_empty_or_bare_organism_payload() -> None:
    registry = get_command_registry()
    empty = registry.run(SNAPSHOT_COMMAND, {})
    bare = registry.run(SNAPSHOT_COMMAND, {"organism_id": "org_1"})

    assert empty["ok"] is False
    assert empty["error"]["code"] == "schema_validation_failed"
    assert bare["ok"] is False
    assert bare["error"]["code"] == "schema_validation_failed"


def test_commands_return_unavailable_without_registered_host() -> None:
    registry = get_command_registry()
    context = {"editor_context": _Context()}

    discovery = registry.run(DISCOVERY_COMMAND, {}, context=context)
    snapshot = registry.run(
        SNAPSHOT_COMMAND,
        {"identity": _identity()},
        context=context,
    )

    assert discovery["ok"] is True
    assert discovery["result"]["status"] == "unavailable"
    assert snapshot["ok"] is True
    assert snapshot["result"]["status"] == "unavailable"


def test_discovery_then_explicit_query_uses_only_registered_host_interface() -> None:
    source = _Source()
    host = PsRuntimeSnapshotHostAdapter(source)
    context = {"editor_context": _Context(host)}
    registry = get_command_registry()

    discovery = registry.run(DISCOVERY_COMMAND, {}, context=context)
    identity = discovery["result"]["identities"][0]
    snapshot = registry.run(
        SNAPSHOT_COMMAND,
        {"identity": identity},
        context=context,
    )

    assert discovery["ok"] is True
    assert discovery["result"]["organism_count"] == 1
    assert snapshot["ok"] is True
    assert snapshot["result"]["status"] == "ok"
    assert source.query_calls == [identity]
    json.dumps({"discovery": discovery, "snapshot": snapshot}, allow_nan=False)


@pytest.mark.parametrize("status", ["invalid_identity", "unsupported_track", "stale", "missing"])
def test_snapshot_command_preserves_authority_statuses(status: str) -> None:
    source = _Source()
    source.snapshot_result = _snapshot(status)
    context = {"editor_context": _Context(PsRuntimeSnapshotHostAdapter(source))}

    result = get_command_registry().run(
        SNAPSHOT_COMMAND,
        {"identity": _identity()},
        context=context,
    )

    assert result["ok"] is True
    assert result["result"]["status"] == status


def test_ps_plugin_registers_and_unregisters_separate_host_adapter(tmp_path: Path) -> None:
    context = _Context(project_root=tmp_path)
    plugin = PsExperimentPlugin()

    plugin.on_load(context)
    try:
        service = context.services.get(PS_EXPERIMENT)
        host = context.services.get(PS_RUNTIME_SNAPSHOT_HOST)
        assert service is not None
        assert host is not service
        assert isinstance(host, IPsRuntimeSnapshotHost)
        assert host.discover_ps_runtime_organisms()["status"] == "not_running"
    finally:
        plugin.on_unload()

    assert context.services.has(PS_EXPERIMENT) is False
    assert context.services.has(PS_RUNTIME_SNAPSHOT_HOST) is False


def test_mcp_adapter_exposes_both_ps_runtime_interfaces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(EditorContext, "_instance", None)
    discovery = get_runtime_ps_organism_discovery()
    snapshot = get_runtime_ps_organism_snapshot(_identity())

    assert EditorContext._instance is None
    assert discovery["ok"] is True
    assert discovery["result"]["status"] == "unavailable"
    assert snapshot["ok"] is True
    assert snapshot["result"]["status"] == "unavailable"

def test_commands_are_headless_importable_and_deterministic_without_pyqt6() -> None:
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
from core.VitaLoom.commands.mcp_adapter import (
    get_runtime_ps_organism_discovery,
    get_runtime_ps_organism_snapshot,
)
from core.VitaLoom.commands.registry import get_command_registry
registry = get_command_registry()
discovery_spec = registry.describe("runtime.ps.organism_discovery")
snapshot_spec = registry.describe("runtime.ps.organism_snapshot")
discovery = registry.run("runtime.ps.organism_discovery", {})
snapshot = registry.run(
    "runtime.ps.organism_snapshot",
    {"identity": {"track": "ps_batch", "run_id": "ps_x", "organism_id": "org_1"}},
)
print(json.dumps({
    "discovery_spec": discovery_spec,
    "snapshot_spec": snapshot_spec,
    "discovery": discovery,
    "snapshot": snapshot,
}, ensure_ascii=False))
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
    assert payload["discovery_spec"]["requires_gui"] is False
    assert payload["snapshot_spec"]["requires_gui"] is False
    assert payload["discovery"]["result"]["status"] == "unavailable"
    assert payload["snapshot"]["result"]["status"] == "unavailable"
