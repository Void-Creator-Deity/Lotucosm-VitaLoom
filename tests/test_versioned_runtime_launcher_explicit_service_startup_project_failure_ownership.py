# -*- coding: utf-8 -*-
"""E162 proofs for owned-splash cleanup after explicit project binding failure."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    "primary_error",
    [RuntimeError("explicit project binding failed"), SystemExit(301)],
)
def test_launcher_cleans_owned_splash_when_explicit_project_binding_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
    primary_error: BaseException,
) -> None:
    """A project-binding failure remains primary and dismisses the owned splash once."""

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
    splash = object()
    project_path = tmp_path / "starter.pond"

    class App:
        def exec(self) -> int:
            pytest.fail("project binding failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def set_startup_project(self, project_path: str) -> None:
            calls.append(("kernel.project", project_path))
            raise primary_error

    def validate_registry(candidate: object) -> object:
        calls.append(("registry.validate", candidate))
        return require_registry(candidate)

    def validate_event_bus(candidate: object) -> object:
        calls.append(("event_bus.validate", candidate))
        return require_event_bus(candidate)

    def forbidden_default_registry() -> object:
        pytest.fail("explicit registry path must not construct a default registry")

    def forbidden_later_startup(*_args: object, **_kwargs: object) -> object:
        pytest.fail("project binding failure must stop before plugins or splash finish")

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
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda *_args: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_later_startup)
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(type(primary_error)) as captured:
            editor_launcher.launch_editor(
                App(),
                tmp_path,
                project_path=project_path,
                capability_registry=registry,
                event_bus=event_bus,
            )

    assert captured.value is primary_error
    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
        "splash.show",
        "splash.message",
        (
            "kernel.construct",
            {"capability_registry": registry, "event_bus": event_bus},
        ),
        ("kernel.project", str(project_path)),
        ("splash.dismiss", splash),
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text