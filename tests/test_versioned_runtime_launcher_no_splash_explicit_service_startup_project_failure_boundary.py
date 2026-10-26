# -*- coding: utf-8 -*-
"""E163 proofs for no-splash explicit project-binding failure boundaries."""
from __future__ import annotations

import logging

import pytest


def _forbid_splash_creation(
    monkeypatch: pytest.MonkeyPatch,
    splash_screen: object,
    calls: list[object],
) -> None:
    def forbidden_splash_call(*_args: object, **_kwargs: object) -> object:
        pytest.fail("no-splash project binding failure must not allocate or finish splash")

    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_call)
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )


@pytest.mark.parametrize(
    "primary_error",
    [RuntimeError("no-splash explicit project binding failed"), SystemExit(311)],
)
def test_no_splash_launcher_preserves_explicit_project_binding_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
    primary_error: BaseException,
) -> None:
    """A no-splash project failure uses only the established safe null cleanup."""

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
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            pytest.fail("project binding failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def set_startup_project(self, received_project: str) -> None:
            calls.append(("kernel.project", received_project))
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
        pytest.fail("project binding failure must stop before plugins")

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
    _forbid_splash_creation(monkeypatch, splash_screen, calls)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(type(primary_error)) as captured:
            editor_launcher.launch_editor(
                App(),
                tmp_path,
                project_path=project_path,
                use_splash=False,
                capability_registry=registry,
                event_bus=event_bus,
            )

    assert captured.value is primary_error
    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
        (
            "kernel.construct",
            {"capability_registry": registry, "event_bus": event_bus},
        ),
        ("kernel.project", str(project_path)),
        ("splash.dismiss", None),
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text