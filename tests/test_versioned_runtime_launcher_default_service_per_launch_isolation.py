# -*- coding: utf-8 -*-
"""E156 proof for per-launch default registry isolation at the Launcher seam."""
from __future__ import annotations

import logging

import pytest


def test_launcher_creates_fresh_default_registry_for_each_no_splash_launch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Omitted services remain per-launch and do not become Launcher-owned globals."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.ui import splash_screen

    registry_type = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry
    calls: list[object] = []
    kernel_kwargs: list[dict[str, object]] = []

    class App:
        def __init__(self, label: str, result: int) -> None:
            self.label = label
            self.result = result

        def exec(self) -> int:
            calls.append((self.label, "app.exec"))
            return self.result

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            kernel_kwargs.append(dict(kwargs))
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")

    def create_default_registry() -> object:
        registry = registry_type()
        calls.append(("registry.default", registry))
        return registry

    def forbidden_splash_call(*_args: object, **_kwargs: object) -> object:
        pytest.fail("successful no-splash launch must not touch the splash adapter")

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        create_default_registry,
    )
    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden_splash_call)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden_splash_call)

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(
            App("first", 251),
            tmp_path,
            use_splash=False,
        ) == 251
        assert editor_launcher.launch_editor(
            App("second", 252),
            tmp_path,
            use_splash=False,
        ) == 252

    assert len(kernel_kwargs) == 2
    first_registry = kernel_kwargs[0]["capability_registry"]
    second_registry = kernel_kwargs[1]["capability_registry"]
    assert isinstance(first_registry, registry_type)
    assert isinstance(second_registry, registry_type)
    assert first_registry is not second_registry
    assert kernel_kwargs == [
        {"capability_registry": first_registry},
        {"capability_registry": second_registry},
    ]
    assert all("event_bus" not in kwargs for kwargs in kernel_kwargs)
    assert calls == [
        ("registry.default", first_registry),
        ("kernel.construct", {"capability_registry": first_registry}),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        ("first", "app.exec"),
        ("registry.default", second_registry),
        ("kernel.construct", {"capability_registry": second_registry}),
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        ("second", "app.exec"),
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
