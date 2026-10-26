# -*- coding: utf-8 -*-
"""E25 red proofs for Qt-free nested runtime plugin shutdown authority."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest


class _Plugin:
    def __init__(self, plugin_id: str, events: list[str], dependencies=(), *, fail_unload=False):
        self.plugin_id = plugin_id
        self.events = events
        self.dependencies = tuple(dependencies)
        self.fail_unload = fail_unload

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": "1.0.0",
            "dependencies": list(self.dependencies),
            "provides": [],
            "activation_context": "runtime",
        }

    def on_load(self, _context):
        self.events.append(f"load:{self.plugin_id}")

    def on_unload(self):
        self.events.append(f"unload:{self.plugin_id}")
        if self.fail_unload:
            raise RuntimeError(f"unload failed: {self.plugin_id}")


@dataclass
class _Failure:
    plugin_id: str
    stage: str


class _Adapter:
    def __init__(self, events: list[str], failure: _Failure | None = None):
        self.events = events
        self.failure = failure
        self.host = None

    def _record(self, plugin_id: str, stage: str) -> None:
        self.events.append(f"{stage}:{plugin_id}")
        if self.failure == _Failure(plugin_id, stage):
            raise RuntimeError(f"{stage} failed: {plugin_id}")

    def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
        return None

    def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
        self._record(plugin_id, "ordinary_cleanup")

    def before_plugin_shutdown(self, plugin, plugin_id, plugin_info) -> None:
        self._record(plugin_id, "adapter_cleanup")


    def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
        assert self.host is not None
        self.events.append(
            f"unload_signal:{plugin_id}:active={plugin_id in self.host.loaded_plugins}"
        )
        if self.failure == _Failure(plugin_id, "unload_signal"):
            raise RuntimeError(f"unload_signal failed: {plugin_id}")


def _instrument_command_release(host, events: list[str], failure: _Failure | None = None):
    original_release = host._release_plugin_commands

    def release(plugin_id: str) -> None:
        events.append(f"command_owner_release:{plugin_id}")
        if failure == _Failure(plugin_id, "command_owner_release"):
            raise RuntimeError(f"command_owner_release failed: {plugin_id}")
        original_release(plugin_id)

    host._release_plugin_commands = release
    return host


def _host(events: list[str], *, failure: _Failure | None = None, fail_unload=()):
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    adapter = _Adapter(events, failure)
    host = RuntimePluginHost(adapter=adapter)
    adapter.host = host
    _instrument_command_release(host, events, failure)
    plugins = {
        "AlphaPlugin": _Plugin(
            "AlphaPlugin", events, fail_unload="AlphaPlugin" in fail_unload
        ),
        "BetaPlugin": _Plugin(
            "BetaPlugin",
            events,
            ("AlphaPlugin",),
            fail_unload="BetaPlugin" in fail_unload,
        ),
        "GammaPlugin": _Plugin(
            "GammaPlugin",
            events,
            ("BetaPlugin",),
            fail_unload="GammaPlugin" in fail_unload,
        ),
    }
    for plugin_id in ("AlphaPlugin", "BetaPlugin", "GammaPlugin"):
        host.register_plugin(
            plugins[plugin_id],
            scope=host.SCOPE_CORE if plugin_id == "AlphaPlugin" else host.SCOPE_OFFICIAL,
            source=f"{plugin_id}.py",
        )
        host.loaded_plugins[plugin_id] = plugins[plugin_id]
    host.resolve_dependencies()
    return host


def test_shutdown_deactivates_dependents_before_dependencies_including_protected() -> None:
    events: list[str] = []
    host = _host(events)

    assert host.unload_plugin("AlphaPlugin") is False
    assert set(host.loaded_plugins) == {"AlphaPlugin", "BetaPlugin", "GammaPlugin"}

    report = host.shutdown_plugins()

    assert report["status"] == "settled"
    assert report["source"] == "shutdown"
    assert report["requested_plugin_ids"] == []
    assert report["target_plugin_ids"] == []
    assert report["retained_plugin_ids"] == []
    assert report["deactivate_plugin_ids"] == [
        "GammaPlugin",
        "BetaPlugin",
        "AlphaPlugin",
    ]
    assert report["completed"]["deactivated"] == report["deactivate_plugin_ids"]
    assert report["failed_action"] is None
    assert report["remaining_active_plugin_ids"] == []
    assert host.loaded_plugins == {}
    assert events == [
        "adapter_cleanup:GammaPlugin",
        "unload:GammaPlugin",
        "command_owner_release:GammaPlugin",
        "unload_signal:GammaPlugin:active=False",
        "adapter_cleanup:BetaPlugin",
        "unload:BetaPlugin",
        "command_owner_release:BetaPlugin",
        "unload_signal:BetaPlugin:active=False",
        "adapter_cleanup:AlphaPlugin",
        "unload:AlphaPlugin",
        "command_owner_release:AlphaPlugin",
        "unload_signal:AlphaPlugin:active=False",
    ]


@pytest.mark.parametrize(
    ("failure", "fail_unload", "completed", "remaining", "stage"),
    [
        (_Failure("BetaPlugin", "adapter_cleanup"), (), ["GammaPlugin"], ["AlphaPlugin", "BetaPlugin"], "adapter_cleanup"),
        (None, ("BetaPlugin",), ["GammaPlugin"], ["AlphaPlugin", "BetaPlugin"], "plugin_on_unload"),
        (_Failure("BetaPlugin", "command_owner_release"), (), ["GammaPlugin"], ["AlphaPlugin", "BetaPlugin"], "command_owner_release"),
        (_Failure("BetaPlugin", "unload_signal"), (), ["GammaPlugin", "BetaPlugin"], ["AlphaPlugin"], "unload_signal"),
    ],
)
def test_shutdown_is_fail_closed_and_reports_exact_failed_stage(
    failure: _Failure | None,
    fail_unload: tuple[str, ...],
    completed: list[str],
    remaining: list[str],
    stage: str,
) -> None:
    events: list[str] = []
    host = _host(events, failure=failure, fail_unload=fail_unload)

    report = host.shutdown_plugins()

    assert report["status"] == "failed"
    assert report["completed"]["deactivated"] == completed
    assert report["failed_action"]["action"] == "deactivate"
    assert report["failed_action"]["plugin_id"] == "BetaPlugin"
    assert report["failed_action"]["stage"] == stage
    assert report["failed_action"]["error"] == "RuntimeError"
    assert report["remaining_active_plugin_ids"] == remaining
    assert sorted(host.loaded_plugins) == remaining
    assert not any("AlphaPlugin" in event for event in events)


def test_shutdown_of_empty_host_is_deterministic_noop() -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    host = RuntimePluginHost()

    first = host.shutdown_plugins()
    second = host.shutdown_plugins()

    expected = {
        "status": "noop",
        "source": "shutdown",
        "requested_plugin_ids": [],
        "target_plugin_ids": [],
        "retained_plugin_ids": [],
        "deactivate_plugin_ids": [],
        "activate_plugin_ids": [],
        "completed": {"deactivated": [], "activated": []},
        "failed_action": None,
        "remaining_active_plugin_ids": [],
        "transition_attempted": False,
    }
    for report in (first, second):
        for key, value in expected.items():
            assert report[key] == value
    assert first == second
    assert host.last_lifecycle_report is second


def test_host_prepares_plugin_before_concrete_surface_cleanup() -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []

    class Plugin(_Plugin):
        def prepare_host_teardown(self) -> None:
            events.append("prepare:GameViewportPlugin")

    class Adapter(_Adapter):
        def before_plugin_shutdown(self, plugin, plugin_id, plugin_info) -> None:
            assert events[-1] == "prepare:GameViewportPlugin"
            events.append("surface_destroy:GameViewportPlugin")

    adapter = Adapter(events)
    host = RuntimePluginHost(adapter=adapter)
    adapter.host = host
    _instrument_command_release(host, events)
    plugin = Plugin("GameViewportPlugin", events)
    host.register_plugin(plugin, scope=host.SCOPE_CORE, source="game_viewport_plugin.py")
    host.loaded_plugins["GameViewportPlugin"] = plugin
    host.resolve_dependencies()

    report = host.shutdown_plugins()

    assert report["status"] == "settled"
    assert events == [
        "prepare:GameViewportPlugin",
        "surface_destroy:GameViewportPlugin",
        "unload:GameViewportPlugin",
        "command_owner_release:GameViewportPlugin",
        "unload_signal:GameViewportPlugin:active=False",
    ]


def test_prepare_failure_retains_plugin_and_skips_surface_cleanup_for_retry() -> None:
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []

    class Plugin(_Plugin):
        fail_prepare_once = True

        def prepare_host_teardown(self) -> None:
            events.append("prepare:GameViewportPlugin")
            if self.fail_prepare_once:
                self.fail_prepare_once = False
                raise RuntimeError("capability release failed")

    adapter = _Adapter(events)
    host = RuntimePluginHost(adapter=adapter)
    adapter.host = host
    _instrument_command_release(host, events)
    plugin = Plugin("GameViewportPlugin", events)
    host.register_plugin(plugin, scope=host.SCOPE_CORE, source="game_viewport_plugin.py")
    host.loaded_plugins["GameViewportPlugin"] = plugin
    host.resolve_dependencies()

    first = host.shutdown_plugins()

    assert first["status"] == "failed"
    assert first["failed_action"]["stage"] == "plugin_prepare_host_teardown"
    assert host.loaded_plugins["GameViewportPlugin"] is plugin
    assert events == ["prepare:GameViewportPlugin"]

    second = host.shutdown_plugins()

    assert second["status"] == "settled"
    assert events == [
        "prepare:GameViewportPlugin",
        "prepare:GameViewportPlugin",
        "adapter_cleanup:GameViewportPlugin",
        "unload:GameViewportPlugin",
        "command_owner_release:GameViewportPlugin",
        "unload_signal:GameViewportPlugin:active=False",
    ]
