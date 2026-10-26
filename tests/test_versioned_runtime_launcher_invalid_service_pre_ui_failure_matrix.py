# -*- coding: utf-8 -*-
"""E158 proofs for invalid Launcher L1 services before UI allocation."""
from __future__ import annotations

import pytest


def _forbid_post_service_validation_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail if a malformed caller service reaches any UI or Kernel work."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    def forbidden(*_args: object, **_kwargs: object) -> object:
        pytest.fail("invalid service validation must fail before UI or Kernel work")

    monkeypatch.setattr(kernel_package, "EditorKernel", forbidden)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", forbidden)
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", forbidden)
    monkeypatch.setattr(splash_screen, "splash_message", forbidden)
    monkeypatch.setattr(splash_screen, "finish_splash", forbidden)
    monkeypatch.setattr(splash_screen, "dismiss_splash", forbidden)


def test_launcher_rejects_dual_invalid_services_at_registry_validator_first(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Registry validation is observable first when both explicit services fail."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus

    require_registry = runtime_capability_registry.require_runtime_capability_registry
    invalid_registry = object()
    invalid_event_bus = object()
    calls: list[tuple[str, object]] = []
    _forbid_post_service_validation_work(monkeypatch)

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("service validation must fail before app event-loop validation")

    def validate_registry(candidate: object) -> object:
        calls.append(("registry.validate", candidate))
        return require_registry(candidate)

    def forbidden_default_registry() -> object:
        pytest.fail("an explicit invalid registry must not construct a default")

    def forbidden_event_bus_validation(_candidate: object) -> object:
        pytest.fail("event-bus validation must be unreachable after invalid registry")

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

    with pytest.raises(TypeError) as captured:
        editor_launcher.launch_editor(
            App(),
            tmp_path,
            capability_registry=invalid_registry,
            event_bus=invalid_event_bus,
        )

    assert str(captured.value) == (
        "runtime capability registry must provide register/unregister/get/has"
    )
    assert calls == [("registry.validate", invalid_registry)]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text


def test_launcher_rejects_invalid_event_bus_after_valid_registry_before_ui(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A valid registry cannot move malformed event-bus validation past UI setup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom.core import runtime_capability_registry
    from core.VitaLoom.core import runtime_event_bus

    registry = runtime_capability_registry.InMemoryRuntimeCapabilityRegistry()
    require_registry = runtime_capability_registry.require_runtime_capability_registry
    require_event_bus = runtime_event_bus.require_runtime_event_bus
    invalid_event_bus = object()
    calls: list[tuple[str, object]] = []
    _forbid_post_service_validation_work(monkeypatch)

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("event-bus validation must fail before app event-loop validation")

    def validate_registry(candidate: object) -> object:
        calls.append(("registry.validate", candidate))
        return require_registry(candidate)

    def validate_event_bus(candidate: object) -> object:
        calls.append(("event_bus.validate", candidate))
        return require_event_bus(candidate)

    def forbidden_default_registry() -> object:
        pytest.fail("an explicit registry must not construct a default")

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

    with pytest.raises(TypeError) as captured:
        editor_launcher.launch_editor(
            App(),
            tmp_path,
            capability_registry=registry,
            event_bus=invalid_event_bus,
        )

    assert str(captured.value) == (
        "runtime event bus must implement subscribe/unsubscribe/publish"
    )
    assert calls == [
        ("registry.validate", registry),
        ("event_bus.validate", invalid_event_bus),
    ]
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text