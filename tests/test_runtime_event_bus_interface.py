# -*- coding: utf-8 -*-
"""E15 proofs for the Qt-free Host-scoped string runtime event seam."""
from __future__ import annotations

import builtins
import importlib
import inspect
import logging
import sys

import pytest


MODULE_NAME = "core.VitaLoom.core.runtime_event_bus"


def _event_module():
    return importlib.import_module(MODULE_NAME)


def test_runtime_event_module_import_is_qt_free(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    parent = importlib.import_module("core.VitaLoom.core")
    parent_attribute = "runtime_event_bus"
    missing = object()
    previous_parent_attribute = vars(parent).get(parent_attribute, missing)
    previous = sys.modules.pop(MODULE_NAME, None)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.InMemoryRuntimeEventBus.__name__ == "InMemoryRuntimeEventBus"
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous
        if previous_parent_attribute is missing:
            vars(parent).pop(parent_attribute, None)
        else:
            setattr(parent, parent_attribute, previous_parent_attribute)

def test_in_memory_event_bus_has_strict_interface_contract() -> None:
    module = _event_module()
    bus = module.InMemoryRuntimeEventBus()
    callback = lambda _payload: None

    for invalid in (None, 1, object()):
        with pytest.raises(TypeError, match="event name must be a string"):
            bus.subscribe(invalid, callback)
    with pytest.raises(ValueError, match="event name must not be empty"):
        bus.subscribe("   ", callback)
    with pytest.raises(TypeError, match="callback must be callable"):
        bus.subscribe("runtime.event", object())
    with pytest.raises(TypeError, match="callback must be callable"):
        bus.unsubscribe("runtime.event", object())
    with pytest.raises(ValueError, match="event name must not be empty"):
        bus.publish("  ")


def test_in_memory_event_bus_preserves_order_duplicates_and_exact_unsubscribe() -> None:
    module = _event_module()
    bus = module.InMemoryRuntimeEventBus()
    observed: list[tuple[str, object]] = []

    def first(payload):
        observed.append(("first", payload))

    def second(payload):
        observed.append(("second", payload))

    bus.subscribe("  project.opened  ", first)
    bus.subscribe("project.opened", first)
    bus.subscribe("project.opened", second)
    bus.publish(" project.opened ", {"id": 7})
    assert observed == [
        ("first", {"id": 7}),
        ("first", {"id": 7}),
        ("second", {"id": 7}),
    ]

    bus.unsubscribe("project.opened", first)
    observed.clear()
    bus.publish("project.opened", 8)
    assert observed == [("first", 8), ("second", 8)]


def test_callback_failure_is_logged_and_does_not_stop_later_callbacks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    module = _event_module()
    bus = module.InMemoryRuntimeEventBus()
    observed: list[object] = []

    def broken(_payload):
        raise RuntimeError("boom-e15")

    bus.subscribe("runtime.tick", broken)
    bus.subscribe("runtime.tick", observed.append)

    with caplog.at_level(logging.WARNING):
        bus.publish("runtime.tick", 15)

    assert observed == [15]
    assert "runtime.tick" in caplog.text
    assert "boom-e15" in caplog.text


def test_event_bus_instances_are_host_scoped_and_state_isolated() -> None:
    module = _event_module()
    first = module.InMemoryRuntimeEventBus()
    second = module.InMemoryRuntimeEventBus()
    observed: list[str] = []

    first.subscribe("runtime.ready", lambda _payload: observed.append("first"))
    second.publish("runtime.ready")
    assert observed == []
    first.publish("runtime.ready")
    assert observed == ["first"]
    assert isinstance(first, module.RuntimeEventBus)


def test_legacy_qt_event_bus_is_a_signal_adapter_over_runtime_interface() -> None:
    module = _event_module()
    from core.VitaLoom.kernel.event_bus import EventBus

    delegate = module.InMemoryRuntimeEventBus()
    adapter = EventBus(runtime_bus=delegate)
    callbacks: list[object] = []
    signals: list[tuple[str, object]] = []
    adapter.subscribe("project.closed", callbacks.append)
    adapter.event_fired.connect(lambda name, payload: signals.append((name, payload)))

    adapter.publish("project.closed", {"path": "pond"})

    assert callbacks == [{"path": "pond"}]
    assert signals == [("project.closed", {"path": "pond"})]
    assert adapter.runtime_bus is delegate
    assert isinstance(adapter, module.RuntimeEventBus)


def test_editor_and_player_entrypoints_expose_event_bus_composition_seams() -> None:
    from core.VitaLoom.editor_launcher import launch_editor
    from core.VitaLoom.kernel.editor_kernel import EditorKernel
    from core.VitaLoom.player.player_shell import PlayerShell, run_player_shell, run_player_smoke

    for callable_object in (
        EditorKernel,
        launch_editor,
        PlayerShell,
        run_player_shell,
        run_player_smoke,
    ):
        assert "event_bus" in inspect.signature(callable_object).parameters


def test_launch_editor_forwards_the_exact_event_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _event_module()
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    event_bus = module.InMemoryRuntimeEventBus()
    captured: dict[str, object] = {}

    class App:
        def exec(self) -> int:
            return 51

    class Kernel:
        def __init__(self, *, capability_registry, event_bus):
            captured["registry"] = capability_registry
            captured["event_bus"] = event_bus

        def load_plugins_layered(self, layers) -> None:
            captured["layers"] = layers

        def show(self) -> None:
            captured["shown"] = True

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    assert editor_launcher.launch_editor(
        App(),
        "repo-e15",
        use_splash=False,
        event_bus=event_bus,
    ) == 51
    assert captured["event_bus"] is event_bus
    assert captured["layers"] == {"l1": []}
    assert captured["shown"] is True


def test_run_player_shell_forwards_the_exact_event_bus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _event_module()
    from core.VitaLoom.player import player_shell as player_module

    event_bus = module.InMemoryRuntimeEventBus()
    captured: dict[str, object] = {}

    class App:
        def exec(self) -> int:
            return 52

    class Shell:
        def __init__(self, repo_root, project_path, *, capability_registry, event_bus):
            captured.update(
                repo_root=repo_root,
                project_path=project_path,
                capability_registry=capability_registry,
                event_bus=event_bus,
            )

        def show(self) -> None:
            captured["shown"] = True

    monkeypatch.setattr(player_module, "PlayerShell", Shell)

    assert player_module.run_player_shell(
        App(),
        "repo-e15",
        "project-e15",
        event_bus=event_bus,
    ) == 52
    assert captured["event_bus"] is event_bus
    assert captured["shown"] is True
