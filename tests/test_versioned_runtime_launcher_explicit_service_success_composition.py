# -*- coding: utf-8 -*-
"""E155 proof for explicit L1 service identity at the Launcher composition seam."""
from __future__ import annotations

import logging

import pytest


def test_launcher_validates_and_forwards_exact_explicit_runtime_services(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Valid explicit services remain caller-owned through successful startup."""

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

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 241

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

    def forbid_default_registry() -> object:
        pytest.fail("explicit registry path must not construct a default registry")

    def finish(received_splash: object, received_kernel: object) -> None:
        assert received_splash is splash
        assert isinstance(received_kernel, Kernel)
        calls.append("splash.finish")

    def unexpected_dismiss(received_splash: object) -> None:
        calls.append(("splash.dismiss", received_splash))
        pytest.fail("successful explicit-service startup must not dismiss splash")

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        forbid_default_registry,
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
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, text, _app: calls.append(("splash.message", text)),
    )
    monkeypatch.setattr(splash_screen, "finish_splash", finish)
    monkeypatch.setattr(splash_screen, "dismiss_splash", unexpected_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(
            App(),
            tmp_path,
            capability_registry=registry,
            event_bus=event_bus,
        ) == 241

    assert calls[:2] == [
        ("registry.validate", registry),
        ("event_bus.validate", event_bus),
    ]
    assert calls[2:] == [
        "splash.show",
        ("splash.message", "初始化织机内核..."),
        (
            "kernel.construct",
            {"capability_registry": registry, "event_bus": event_bus},
        ),
        ("splash.message", "加载官方能力包与用户扩展..."),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        ("splash.message", "恢复布局与项目..."),
        "kernel.show",
        "splash.finish",
        "app.exec",
    ]
    kernel_kwargs = calls[4][1]
    assert kernel_kwargs["capability_registry"] is registry
    assert kernel_kwargs["event_bus"] is event_bus
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
