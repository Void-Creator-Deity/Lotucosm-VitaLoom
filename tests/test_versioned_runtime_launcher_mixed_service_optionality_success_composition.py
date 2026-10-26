# -*- coding: utf-8 -*-
"""E157 proof for mixed optional-service Launcher success composition."""
from __future__ import annotations

import pytest


def _forbid_splash(monkeypatch: pytest.MonkeyPatch, splash_screen: object) -> None:
    def forbidden_splash_call(*_args: object, **_kwargs: object) -> object:
        pytest.fail("successful no-splash launch must not touch the splash adapter")

    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden_splash_call)


def test_launcher_forwards_explicit_registry_without_event_bus(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """An explicit registry must not synthesize a registry or an omitted event bus."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus
    from core.VitaLoom.ui import splash_screen

    registry = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry()
    require_registry = runtime_capability_registry.require_runtime_capability_registry
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 261

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

    def forbidden_default_registry() -> object:
        pytest.fail("explicit registry path must not construct a default registry")

    def forbidden_event_bus_validation(_candidate: object) -> object:
        pytest.fail("omitted event bus must not be validated")

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
        forbidden_event_bus_validation,
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
        use_splash=False,
        capability_registry=registry,
    ) == 261
    assert calls == [
        ("registry.validate", registry),
        ("kernel.construct", {"capability_registry": registry}),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        "app.exec",
    ]


def test_launcher_constructs_default_registry_and_forwards_explicit_event_bus(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """A supplied event bus composes with one per-launch default registry."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus
    from core.VitaLoom.ui import splash_screen

    registry_type = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry
    event_bus = runtime_event_bus.InMemoryRuntimeEventBus()
    require_event_bus = runtime_event_bus.require_runtime_event_bus
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 262

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")

    def create_default_registry() -> object:
        registry = registry_type()
        calls.append(("registry.default", registry))
        return registry

    def validate_event_bus(candidate: object) -> object:
        calls.append(("event_bus.validate", candidate))
        return require_event_bus(candidate)

    def forbidden_registry_validation(_candidate: object) -> object:
        pytest.fail("default registry path must not validate an absent caller registry")

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        create_default_registry,
    )
    monkeypatch.setattr(
        runtime_capability_registry,
        "require_runtime_capability_registry",
        forbidden_registry_validation,
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
        use_splash=False,
        event_bus=event_bus,
    ) == 262

    default_registry = calls[0][1]
    assert isinstance(default_registry, registry_type)
    assert calls == [
        ("registry.default", default_registry),
        ("event_bus.validate", event_bus),
        (
            "kernel.construct",
            {
                "capability_registry": default_registry,
                "event_bus": event_bus,
            },
        ),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        "app.exec",
    ]