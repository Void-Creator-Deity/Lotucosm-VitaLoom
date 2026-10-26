# -*- coding: utf-8 -*-
"""E130 regressions for splash-presentation controlled-exit cleanup ownership."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    ("failure_stage", "exit_code"),
    [("show", 101), ("process_events", 103)],
)
def test_show_vitaloom_splash_dismisses_allocated_splash_for_controlled_exit(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
    exit_code: int,
) -> None:
    """A controlled presentation exit releases the adapter-owned splash once."""

    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")
            if failure_stage == "show":
                raise SystemExit(exit_code)

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            if failure_stage == "process_events":
                raise SystemExit(exit_code)

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)

    with pytest.raises(SystemExit) as captured:
        splash_screen.show_vitaloom_splash(App())

    assert captured.value.code == exit_code
    expected = ["splash.show"]
    if failure_stage == "process_events":
        expected.append("app.processEvents")
    expected.extend(["splash.hide", "splash.deleteLater"])
    assert calls == expected


def test_show_vitaloom_splash_keeps_controlled_exit_primary_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Presentation cleanup faults stay secondary to the controlled exit."""

    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            raise SystemExit(107)

    def fail_to_dismiss(received: object) -> None:
        assert isinstance(received, Splash)
        calls.append("splash.dismiss")
        raise cleanup_error

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            splash_screen.show_vitaloom_splash(App())

    assert captured.value.code == 107
    assert calls == ["splash.show", "app.processEvents", "splash.dismiss"]
    assert "Failed to dismiss splash after splash presentation failure" in caplog.text


def test_launcher_does_not_construct_kernel_or_duplicate_partial_splash_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pre-return splash exit remains owned by the splash adapter, not Launcher."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            raise SystemExit(109)

        def exec(self) -> int:
            raise AssertionError("splash presentation exit must not enter app.exec()")

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)
    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("presentation exit must not construct a Kernel"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("presentation exit must not resolve plugin layers"),
    )

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(App(), "repo-e130")

    assert captured.value.code == 109
    assert calls == [
        "splash.show",
        "app.processEvents",
        "splash.hide",
        "splash.deleteLater",
    ]

def test_show_vitaloom_splash_dismisses_allocated_splash_for_regular_show_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter keeps the existing ordinary-exception cleanup behavior at show()."""

    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    primary_error = RuntimeError("splash show failed")
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")
            raise primary_error

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    class App:
        def processEvents(self) -> None:
            raise AssertionError("failed splash show must not process events")

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)

    with pytest.raises(RuntimeError) as captured:
        splash_screen.show_vitaloom_splash(App())

    assert captured.value is primary_error
    assert calls == ["splash.show", "splash.hide", "splash.deleteLater"]

def test_show_vitaloom_splash_real_offscreen_app_cleans_up_after_process_events_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The controlled-exit cleanup boundary also holds with a real offscreen splash."""

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtWidgets import QApplication, QSplashScreen

    from core.VitaLoom.ui import splash_screen

    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None
    calls: list[str] = []

    class ObservedSplash(QSplashScreen):
        def __init__(self) -> None:
            super().__init__(QPixmap(8, 8))

        def show(self) -> None:
            calls.append("splash.show")
            super().show()

        def hide(self) -> None:
            calls.append("splash.hide")
            super().hide()

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            super().deleteLater()

    class AppAdapter:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            qt_app.processEvents()
            raise SystemExit(113)

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", ObservedSplash)

    with pytest.raises(SystemExit) as captured:
        splash_screen.show_vitaloom_splash(AppAdapter())

    assert captured.value.code == 113
    assert calls == [
        "splash.show",
        "app.processEvents",
        "splash.hide",
        "splash.deleteLater",
    ]

def test_show_vitaloom_splash_does_not_reclassify_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt remains outside the controlled startup-exit cleanup policy."""

    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")
            raise KeyboardInterrupt

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    class App:
        def processEvents(self) -> None:
            raise AssertionError("KeyboardInterrupt from show must not process events")

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)

    with pytest.raises(KeyboardInterrupt):
        splash_screen.show_vitaloom_splash(App())

    assert calls == ["splash.show"]
