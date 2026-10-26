# -*- coding: utf-8 -*-
"""E165 proofs for no-splash explicit project-binding interrupt escape."""
from __future__ import annotations

import pytest


def test_no_splash_launcher_allows_explicit_project_binding_interrupt_to_escape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """KeyboardInterrupt remains outside the Launcher startup-cleanup policy."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus
    from core.VitaLoom.ui import splash_screen

    registry = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry()
    event_bus = runtime_event_bus.InMemoryRuntimeEventBus()
    require_registry = runtime_capability_registry.require_runtime_capability_registry
    require_event_bus = runtime_event_bus.require_runtime_event_bus
    project_path = tmp_path / "starter.pond"
    interrupt = KeyboardInterrupt()
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            pytest.fail("project binding interrupt must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def set_startup_project(self, received_project: str) -> None:
            calls.append(("kernel.project", received_project))
            raise interrupt

    def validate_registry(candidate: object) -> object:
        calls.append(("registry.validate", candidate))
        return require_registry(candidate)

    def validate_event_bus(candidate: object) -> object:
        calls.append(("event_bus.validate", candidate))
        return require_event_bus(candidate)

    def forbidden_default_registry() -> object:
        pytest.fail("explicit registry path must not construct a default registry")

    def forbidden_splash_adapter(*_args: object, **_kwargs: object) -> object:
        pytest.fail("project binding interrupt must not access a splash adapter")

    def forbidden_later_startup(*_args: object, **_kwargs: object) -> object:
        pytest.fail("project binding interrupt must stop before plugins")

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        forbidden_default_registry,
    )
    monkeypatch.setattr(
        runtime_capability_registry,
        "require_runtime_capability_registry",
        validate_registry,
    )
    monkeypatch.setattr(
        runtime_event_bus,
        "require_runtime_event_bus",
        validate_event_bus,
    )
    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", forbidden_later_startup)
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_adapter)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_adapter)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_adapter)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden_splash_adapter)

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(
            App(),
            tmp_path,
            project_path=project_path,
            use_splash=False,
            capability_registry=registry,
            event_bus=event_bus,
        )

    assert captured.value is interrupt
    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
        (
            "kernel.construct",
            {"capability_registry": registry, "event_bus": event_bus},
        ),
        ("kernel.project", str(project_path)),
    ]
