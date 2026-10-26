# -*- coding: utf-8 -*-
"""E135 proofs for default L1 registry construction before splash ownership."""
from __future__ import annotations

import pytest


def _forbid_later_launcher_work(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("registry construction failure must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("registry construction failure must not show splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("registry construction failure must not clean splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("registry construction failure must not resolve plugins"),
    )


def _fail_default_registry_construction(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
    calls: list[str],
) -> None:
    from core.VitaLoom.core import runtime_capability_registry

    class FailingRegistry:
        def __init__(self) -> None:
            calls.append("registry.construct")
            raise primary_error

    monkeypatch.setattr(
        runtime_capability_registry,
        "InMemoryRuntimeCapabilityRegistry",
        FailingRegistry,
    )


@pytest.mark.parametrize(
    "primary_error",
    [SystemExit(161), RuntimeError("default registry construction failed")],
)
def test_launcher_preserves_default_registry_construction_failure_before_splash(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
) -> None:
    """Default registry construction has no cleanup owner before splash allocation."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_later_launcher_work(monkeypatch)
    _fail_default_registry_construction(monkeypatch, primary_error, calls)

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("registry construction must fail before app validation")

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), "repo-e135")

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert calls == ["registry.construct"]


def test_launcher_keeps_keyboard_interrupt_outside_default_registry_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt before allocation remains unclassified and cleanup-free."""

    from core.VitaLoom import editor_launcher

    interrupt = KeyboardInterrupt()
    calls: list[str] = []
    _forbid_later_launcher_work(monkeypatch)
    _fail_default_registry_construction(monkeypatch, interrupt, calls)

    class App:
        @property
        def exec(self) -> object:
            pytest.fail("KeyboardInterrupt must fail before app validation")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), "repo-e135-keyboard-interrupt")

    assert captured.value is interrupt
    assert calls == ["registry.construct"]