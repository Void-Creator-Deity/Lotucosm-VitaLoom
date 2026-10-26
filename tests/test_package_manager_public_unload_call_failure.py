# -*- coding: utf-8 -*-
"""E89 proofs for Package Manager public unload-call failure semantics."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _UnloadFailureHost:
    """Complete public Host stub; only the requested unload operation may fail."""

    def __init__(self, outcomes: dict[str, object]) -> None:
        self.outcomes = outcomes
        self.unload_calls: list[str] = []

    def observe_plugins(self) -> dict:
        return {
            "status": "ready",
            "catalog": [
                {"plugin_id": plugin_id, "protected": False, "active": True}
                for plugin_id in sorted(self.outcomes)
            ],
            "active_plugin_ids": sorted(self.outcomes),
        }

    def reload_plugin(self, plugin_id: str) -> dict:
        return {"status": "settled", "plugin_id": plugin_id}

    def unload_plugin(self, plugin_id: str) -> object:
        self.unload_calls.append(plugin_id)
        outcome = self.outcomes[plugin_id]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def scan_project_addons(self, project_path: object) -> dict:
        return {"status": "settled", "project_path": str(project_path)}

    def sync_plugins_for_project(
        self, project_data: dict, *, repo_root: object | None = None
    ) -> dict:
        return {"status": "settled"}


def _context(host: object) -> SimpleNamespace:
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    return SimpleNamespace(
        services=services,
        i18n_tr=lambda key, _default="": key,
    )


def _selected_plugin(host: _UnloadFailureHost) -> PackageManagerPlugin:
    plugin = PackageManagerPlugin()
    plugin.context = _context(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: "AlphaPlugin"
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result["ok"])
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()
    return plugin


@pytest.mark.parametrize(
    "outcome",
    [RuntimeError("public unload unavailable"), {"status": "partial"}, None],
    ids=["raised", "unsettled_report", "malformed_report"],
)
def test_selected_project_disable_reports_persistence_without_claiming_session_unload(
    outcome: object,
) -> None:
    host = _UnloadFailureHost({"AlphaPlugin": outcome})
    plugin = _selected_plugin(host)

    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "AlphaPlugin")
    ]
    assert host.unload_calls == ["AlphaPlugin"]
    plugin._append_result.assert_called_once_with(
        "package_manager.plugin.disabled_runtime_unsettled"
    )
    plugin._refresh.assert_called_once_with()
    plugin._on_selection_changed.assert_called_once_with()


def test_package_disable_reports_each_persisted_runtime_unload_outage_once() -> None:
    host = _UnloadFailureHost(
        {
            "AlphaPlugin": {"status": "settled"},
            "BetaPlugin": RuntimeError("public unload unavailable"),
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: None
    plugin._get_selected_package = lambda: {
        "id": "pkg.demo",
        "plugins": ["AlphaPlugin", "BetaPlugin"],
    }
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result["ok"])
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "AlphaPlugin"),
        call("plugin.disable", "BetaPlugin"),
    ]
    assert host.unload_calls == ["AlphaPlugin", "BetaPlugin"]
    plugin._append_result.assert_called_once_with(
        "package_manager.package.disabled_runtime_unsettled"
    )
    plugin._refresh.assert_called_once_with()
    plugin._on_selection_changed.assert_called_once_with()


def test_disable_does_not_hide_public_host_resolution_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtin.editor_extensions.plugin_runtime_ops as runtime_ops_module

    plugin = PackageManagerPlugin()
    plugin.context = SimpleNamespace()
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: "AlphaPlugin"
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(
        runtime_ops_module,
        "resolve_plugin_host",
        lambda _context: (_ for _ in ()).throw(RuntimeError("host unavailable")),
    )

    with pytest.raises(RuntimeError, match="host unavailable"):
        plugin._disable_selected()

    plugin._run_project_plugin_command.assert_not_called()


def test_disable_does_not_hide_incomplete_public_capability_interface() -> None:
    class _IncompleteHost:
        def observe_plugins(self) -> dict:
            return {}

        def reload_plugin(self, plugin_id: str) -> dict:
            return {}

        def scan_project_addons(self, project_path: object) -> dict:
            return {}

        def sync_plugins_for_project(
            self, project_data: dict, *, repo_root: object | None = None
        ) -> dict:
            return {}

    plugin = PackageManagerPlugin()
    plugin.context = _context(_IncompleteHost())
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: "AlphaPlugin"
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})

    with pytest.raises(TypeError, match="incomplete Interface"):
        plugin._disable_selected()

    plugin._run_project_plugin_command.assert_not_called()


def test_package_disable_only_unloads_plugins_with_persisted_disable_commands() -> None:
    host = _UnloadFailureHost(
        {
            "AlphaPlugin": {"status": "settled"},
            "BetaPlugin": {"status": "settled"},
        }
    )
    plugin = PackageManagerPlugin()
    plugin.context = _context(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: None
    plugin._get_selected_package = lambda: {
        "id": "pkg.demo",
        "plugins": ["AlphaPlugin", "BetaPlugin"],
    }
    plugin._run_project_plugin_command = MagicMock(
        side_effect=[{"ok": True}, {"ok": False}]
    )
    plugin._handle_project_plugin_command_result = lambda result: bool(result["ok"])
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "AlphaPlugin"),
        call("plugin.disable", "BetaPlugin"),
    ]
    assert host.unload_calls == ["AlphaPlugin"]
    plugin._append_result.assert_not_called()
    plugin._refresh.assert_called_once_with()
    plugin._on_selection_changed.assert_called_once_with()


def test_package_without_explicit_plugin_list_unloads_its_persisted_plugin_id() -> None:
    host = _UnloadFailureHost({"pkg.demo": {"status": "settled"}})
    plugin = PackageManagerPlugin()
    plugin.context = _context(host)
    plugin.kernel = object()
    plugin._get_selected_plugin_id = lambda: None
    plugin._get_selected_package = lambda: {"id": "pkg.demo", "plugins": []}
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result["ok"])
    plugin._append_result = MagicMock()
    plugin._refresh = MagicMock()
    plugin._on_selection_changed = MagicMock()

    plugin._disable_selected()

    assert plugin._run_project_plugin_command.call_args_list == [
        call("plugin.disable", "pkg.demo")
    ]
    assert host.unload_calls == ["pkg.demo"]
    plugin._append_result.assert_not_called()
    plugin._refresh.assert_called_once_with()
    plugin._on_selection_changed.assert_called_once_with()
