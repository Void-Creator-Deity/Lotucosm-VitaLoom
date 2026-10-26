# -*- coding: utf-8 -*-
"""E160 proofs for no-splash explicit services through event-loop handoff."""
from __future__ import annotations

import logging

import pytest


def _forbid_splash_adapters(monkeypatch: pytest.MonkeyPatch, splash_screen: object) -> None:
    def forbidden_splash_call(*_args: object, **_kwargs: object) -> object:
        pytest.fail("no-splash explicit-service launch must not touch splash adapters")

    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden_splash_call)


@pytest.mark.parametrize(
    ("outcome", "expected_type"),
    [
        pytest.param(281, None, id="normal-return"),
        pytest.param(RuntimeError("no-splash explicit-service event loop failed"), RuntimeError, id="ordinary-error"),
        pytest.param(SystemExit(279), SystemExit, id="controlled-exit"),
    ],
)
def test_no_splash_launcher_hands_off_explicit_services_without_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
    outcome: object,
    expected_type: type[BaseException] | None,
) -> None:
    """No-splash startup forwards exact services and leaves app.exec() alone."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus
    from core.VitaLoom.ui import splash_screen

    registry = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry()
    event_bus = runtime_event_bus.InMemoryRuntimeEventBus()
    require_registry = runtime_capability_registry.require_runtime_capability_registry
    require_event_bus = runtime_event_bus.require_runtime_event_bus
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            if isinstance(outcome, BaseException):
                raise outcome
            assert isinstance(outcome, int)
            return outcome

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")

    def validate_registry(candidate: object) -> object:
        calls.append(("registry.validate", candidate))
        return require_registry(candidate)

    def validate_event_bus(candidate: object) -> object:
        calls.append(("event_bus.validate", candidate))
        return require_event_bus(candidate)

    def forbidden_default_registry() -> object:
        pytest.fail("explicit registry path must not construct a default registry")

    monkeypatch.setattr(runtime_capability_registry, "InMemoryRuntimeCapabilityRegistry", forbidden_default_registry)
    monkeypatch.setattr(runtime_capability_registry, "require_runtime_capability_registry", validate_registry)
    monkeypatch.setattr(runtime_event_bus, "require_runtime_event_bus", validate_event_bus)
    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda root: calls.append(("plugin.layers", root)) or {"l1": []})
    _forbid_splash_adapters(monkeypatch, splash_screen)

    with caplog.at_level(logging.WARNING):
        if expected_type is None:
            assert editor_launcher.launch_editor(App(), tmp_path, use_splash=False, capability_registry=registry, event_bus=event_bus) == outcome
        else:
            with pytest.raises(expected_type) as captured:
                editor_launcher.launch_editor(App(), tmp_path, use_splash=False, capability_registry=registry, event_bus=event_bus)
            assert captured.value is outcome

    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
        ("kernel.construct", {"capability_registry": registry, "event_bus": event_bus}),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        "app.exec",
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text