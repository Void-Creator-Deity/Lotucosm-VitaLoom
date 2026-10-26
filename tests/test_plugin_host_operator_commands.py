# -*- coding: utf-8 -*-
"""Shared command registry Adapter for live downstream plugin Host operations."""
from __future__ import annotations

from core.VitaLoom.commands.registry import reset_command_registry


class _OperatorAdapter:
    def __init__(self) -> None:
        self.resolve_calls: list[dict[str, str]] = []
        self.inspection = {
            "schema_version": 1,
            "status": "blocked",
            "project_path": "C:/world",
            "report_id": "a" * 64,
            "recoveries": [
                {
                    "action": "retry_project_lifecycle",
                    "operator_confirmation_required": "confirm",
                }
            ],
        }

    def inspect_plugin_host(self, project_path: str = ""):
        if project_path and project_path != self.inspection["project_path"]:
            raise AssertionError("project assertion was not forwarded")
        return dict(self.inspection)

    def list_plugin_host_recoveries(self, project_path: str = ""):
        return {
            "project_path": self.inspection["project_path"],
            "report_id": self.inspection["report_id"],
            "records": list(self.inspection["recoveries"]),
        }

    def resolve_plugin_host_recovery(self, **payload):
        self.resolve_calls.append(dict(payload))
        return {"status": "settled", "before_report_id": payload["report_id"]}


def test_commands_are_registered_with_correct_mutation_flags() -> None:
    registry = reset_command_registry()
    inspect_spec = registry.describe("plugin.host.inspect")
    list_spec = registry.describe("plugin.host.recovery.list")
    resolve_spec = registry.describe("plugin.host.recovery.resolve")
    assert inspect_spec["mutates"] is False
    assert list_spec["mutates"] is False
    assert resolve_spec["mutates"] is True
    assert resolve_spec["undoable"] is False
    assert resolve_spec["requires_gui"] is False


def test_commands_use_explicit_qt_free_adapter_context() -> None:
    registry = reset_command_registry()
    adapter = _OperatorAdapter()
    context = {"plugin_host_operator": adapter}

    inspected = registry.run("plugin.host.inspect", {"project_path": "C:/world"}, context=context)
    assert inspected["ok"] is True
    assert inspected["result"]["report_id"] == "a" * 64

    listed = registry.run("plugin.host.recovery.list", {"project_path": "C:/world"}, context=context)
    assert listed["ok"] is True
    assert listed["result"]["records"][0]["action"] == "retry_project_lifecycle"

    resolved = registry.run(
        "plugin.host.recovery.resolve",
        {
            "project_path": "C:/world",
            "report_id": "a" * 64,
            "action": "retry_project_lifecycle",
            "operator_confirmation": "confirm",
        },
        context=context,
    )
    assert resolved["ok"] is True
    assert adapter.resolve_calls == [
        {
            "project_path": "C:/world",
            "report_id": "a" * 64,
            "action": "retry_project_lifecycle",
            "operator_confirmation": "confirm",
        }
    ]


def test_no_live_host_fails_explicitly_without_importing_ui() -> None:
    from core.VitaLoom.project.plugin_host_operator import unbind_plugin_host_operator_adapter

    unbind_plugin_host_operator_adapter()
    registry = reset_command_registry()
    result = registry.run("plugin.host.inspect", {})
    assert result["ok"] is False
    assert result["error"]["code"] == "plugin_host_unavailable"


def test_commands_can_use_same_process_qt_free_live_binding() -> None:
    from core.VitaLoom.project.plugin_host_operator import (
        bind_plugin_host_operator_adapter,
        unbind_plugin_host_operator_adapter,
    )

    adapter = _OperatorAdapter()
    bind_plugin_host_operator_adapter(adapter)
    try:
        result = reset_command_registry().run("plugin.host.inspect", {})
        assert result["ok"] is True
        assert result["result"]["project_path"] == "C:/world"
    finally:
        unbind_plugin_host_operator_adapter(adapter)

def test_mcp_helpers_forward_operator_payloads(monkeypatch) -> None:
    from core.VitaLoom.commands import mcp_adapter

    calls: list[tuple[str, dict[str, str]]] = []

    def fake_run(command_id: str, payload: dict[str, str]):
        calls.append((command_id, dict(payload)))
        return {"ok": True, "result": {"command_id": command_id}}

    monkeypatch.setattr(mcp_adapter, "run_command", fake_run)

    assert mcp_adapter.inspect_plugin_host("C:/world")["ok"] is True
    assert mcp_adapter.list_plugin_host_recovery("C:/world")["ok"] is True
    assert mcp_adapter.resolve_plugin_host_recovery(
        "C:/world",
        "a" * 64,
        "retry_project_lifecycle",
        "confirm",
    )["ok"] is True
    assert calls == [
        ("plugin.host.inspect", {"project_path": "C:/world"}),
        ("plugin.host.recovery.list", {"project_path": "C:/world"}),
        (
            "plugin.host.recovery.resolve",
            {
                "project_path": "C:/world",
                "report_id": "a" * 64,
                "action": "retry_project_lifecycle",
                "operator_confirmation": "confirm",
            },
        ),
    ]

