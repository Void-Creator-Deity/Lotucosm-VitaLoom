# -*- coding: utf-8 -*-
"""E136 proofs for explicit L1 event-bus validation before splash ownership."""
from __future__ import annotations

import importlib

import pytest


def _forbid_later_launcher_work(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("event-bus validation failure must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("event-bus validation failure must not show splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("event-bus validation failure must not clean splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("event-bus validation failure must not resolve plugins"),
    )


def _install_default_registry_and_failing_event_bus_validator(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
    calls: list[str],
) -> None:
    runtime_capability_registry = importlib.import_module('core.VitaLoom.core.runtime_capability_registry')
    runtime_event_bus = importlib.import_module('core.VitaLoom.core.runtime_event_bus')

    class CapturingRegistry:
        def __init__(self) -> None:
            calls.append("registry.construct")

    def fail_event_bus_validation(_candidate: object) -> object:
        calls.append("event_bus.validate")
        raise primary_error

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        CapturingRegistry,
    )
    monkeypatch.setattr(
        runtime_event_bus,
        "require_runtime_event_bus",
        fail_event_bus_validation,
    )


@pytest.mark.parametrize(
    "primary_error",
    [SystemExit(171), RuntimeError("event-bus validation failed")],
)
def test_launcher_preserves_event_bus_validation_failure_before_splash(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
) -> None:
    """Explicit event-bus validation fails after registry construction, before allocation."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_later_launcher_work(monkeypatch)
    _install_default_registry_and_failing_event_bus_validator(
        monkeypatch,
        primary_error,
        calls,
    )

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("event-bus validation must fail before app validation")

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(
            App(),
            "repo-e136",
            event_bus=object(),
        )

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert calls == ["registry.construct", "event_bus.validate"]


def test_launcher_keeps_keyboard_interrupt_outside_event_bus_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt during validation remains unclassified and cleanup-free."""

    from core.VitaLoom import editor_launcher

    interrupt = KeyboardInterrupt()
    calls: list[str] = []
    _forbid_later_launcher_work(monkeypatch)
    _install_default_registry_and_failing_event_bus_validator(
        monkeypatch,
        interrupt,
        calls,
    )

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("KeyboardInterrupt must fail before app validation")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(
            App(),
            "repo-e136-keyboard-interrupt",
            event_bus=object(),
        )

    assert captured.value is interrupt
    assert calls == ["registry.construct", "event_bus.validate"]