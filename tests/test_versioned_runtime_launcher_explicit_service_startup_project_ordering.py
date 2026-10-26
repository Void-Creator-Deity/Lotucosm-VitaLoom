# -*- coding: utf-8 -*-
"""E161 proof for explicit services with startup-project ordering."""
from __future__ import annotations

from pathlib import Path

import pytest


def _forbid_splash(monkeypatch: pytest.MonkeyPatch, splash_screen: object) -> None:
    def forbidden_splash_call(*_args: object, **_kwargs: object) -> object:
        pytest.fail("no-splash startup-project launch must not touch splash adapters")

    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden_splash_call)


def test_launcher_binds_normalized_project_after_explicit_services_before_plugins(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The public PathLike project request changes neither service nor load order."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus
    from core.VitaLoom.ui import splash_screen

    registry = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry()
    event_bus = runtime_event_bus.InMemoryRuntimeEventBus()
    require_registry = runtime_capability_registry.require_runtime_capability_registry
    require_event_bus = runtime_event_bus.require_runtime_event_bus
    project_path = Path("scenes") / "starter.pond"
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 291

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def set_startup_project(self, received_project: str) -> None:
            calls.append(("kernel.project", received_project))

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

    monkeypatch.chdir(tmp_path)
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
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )
    _forbid_splash(monkeypatch, splash_screen)

    assert editor_launcher.launch_editor(
        App(),
        tmp_path,
        project_path=project_path,
        use_splash=False,
        capability_registry=registry,
        event_bus=event_bus,
    ) == 291

    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
        (
            "kernel.construct",
            {"capability_registry": registry, "event_bus": event_bus},
        ),
        ("kernel.project", str(tmp_path / project_path)),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        "app.exec",
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text