# -*- coding: utf-8 -*-
"""E131 regressions for Launcher-held splash-message controlled-exit cleanup."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    ("message_site", "failed_message_number", "exit_code"),
    [
        ("initial", 1, 121),
        ("plugin_loading", 2, 123),
        ("restore_status", 3, 125),
    ],
)
def test_launcher_dismisses_held_splash_once_for_each_message_system_exit(
    monkeypatch: pytest.MonkeyPatch,
    message_site: str,
    failed_message_number: int,
    exit_code: int,
) -> None:
    """Every pre-handoff message position preserves its controlled exit and stops work."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []
    splash = object()
    message_count = 0

    class App:
        def exec(self) -> int:
            raise AssertionError("message SystemExit must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    def fail_message(_splash: object, _text: str, _app: object) -> None:
        nonlocal message_count
        message_count += 1
        calls.append(f"splash.message:{message_count}")
        if message_count == failed_message_number:
            raise SystemExit(exit_code)

    def dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "splash_message", fail_message)
    monkeypatch.setattr(splash_screen, "dismiss_splash", dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(App(), f"repo-e131-{message_site}")

    assert captured.value.code == exit_code
    expected = ["splash.show", "splash.message:1"]
    if failed_message_number >= 2:
        expected.extend(["kernel.construct", "splash.message:2"])
    if failed_message_number >= 3:
        expected.extend(
            ["plugin.layers", "kernel.load:{'l1': []}", "splash.message:3"]
        )
    expected.append("splash.dismiss")
    assert calls == expected


def test_launcher_keeps_message_system_exit_primary_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A secondary held-splash cleanup fault cannot replace the controlled exit."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []
    splash = object()
    cleanup_error = RuntimeError("splash cleanup failed")

    class App:
        def exec(self) -> int:
            raise AssertionError("message SystemExit must not enter app.exec()")

    def fail_message(*_args: object) -> None:
        calls.append("splash.message")
        raise SystemExit(127)

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")
        raise cleanup_error

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("initial message SystemExit must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "splash_message", fail_message)
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("initial message SystemExit must not resolve plugin layers"),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            editor_launcher.launch_editor(App(), "repo-e131-cleanup")

    assert captured.value.code == 127
    assert calls == ["splash.show", "splash.message", "splash.dismiss"]
    assert "Failed to dismiss splash after editor startup failure" in caplog.text


def test_launcher_keeps_keyboard_interrupt_outside_message_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt remains unclassified at the Launcher-held message boundary."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("KeyboardInterrupt must not enter app.exec()")

    def interrupt_message(*_args: object) -> None:
        calls.append("splash.message")
        raise KeyboardInterrupt

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("KeyboardInterrupt must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "splash_message", interrupt_message)
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("KeyboardInterrupt must not enter controlled cleanup"),
    )

    with pytest.raises(KeyboardInterrupt):
        editor_launcher.launch_editor(App(), "repo-e131-keyboard-interrupt")

    assert calls == ["splash.show", "splash.message"]


def test_launcher_preserves_ordinary_initial_message_error_with_held_splash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ordinary-error contract remains aligned with the new SystemExit evidence."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_error = RuntimeError("initial message failed")
    calls: list[str] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("initial message error must not enter app.exec()")

    def raise_message(*_args: object) -> None:
        calls.append("splash.message")
        raise primary_error

    def dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("initial message error must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "splash_message", raise_message)
    monkeypatch.setattr(splash_screen, "dismiss_splash", dismiss)

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(App(), "repo-e131-runtime-error")

    assert captured.value is primary_error
    assert calls == ["splash.show", "splash.message", "splash.dismiss"]

def test_launcher_releases_held_splash_when_real_message_adapter_process_events_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real splash_message adapter propagates into the E128 cleanup boundary."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []

    class Splash:
        def showMessage(self, *_args: object) -> None:
            calls.append("splash.showMessage")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            raise SystemExit(129)

        def exec(self) -> int:
            raise AssertionError("message SystemExit must not enter app.exec()")

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("initial message SystemExit must not construct Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.presented") or splash,
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("initial message SystemExit must not resolve plugin layers"),
    )

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(App(), "repo-e131-real-message")

    assert captured.value.code == 129
    assert calls == [
        "splash.presented",
        "splash.showMessage",
        "app.processEvents",
        "splash.hide",
        "splash.deleteLater",
    ]
