# -*- coding: utf-8 -*-
"""E129 regression for post-handoff Launcher SystemExit splash ownership."""
from __future__ import annotations

import logging

import pytest


def test_launcher_preserves_event_loop_system_exit_after_completed_splash_handoff(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Post-handoff SystemExit must not re-enter E128 startup cleanup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    callbacks: list[object] = []
    calls: list[str] = []
    exit_code = 89

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise SystemExit(exit_code)

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail(
            "post-handoff app.exec() SystemExit must not dismiss the splash"
        ),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            editor_launcher.launch_editor(App(), "repo-e129")

        assert captured.value.code == exit_code
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
            "app.exec",
        ]
        assert len(callbacks) == 1
        callback = callbacks.pop()
        assert callable(callback)
        callback()

    assert calls[-1] == "splash.deleteLater"
    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    assert "Failed to delete splash after editor startup handoff" not in caplog.text

def test_launcher_real_qt_timer_survives_post_handoff_system_exit(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A real deferred callback remains adapter-owned after app.exec() SystemExit."""

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None
    event_loop = QEventLoop()
    calls: list[str] = []
    exit_code = 91

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            QTimer.singleShot(0, event_loop.quit)

    splash = Splash()

    class AppAdapter:
        def processEvents(self) -> None:
            qt_app.processEvents()

        def exec(self) -> int:
            calls.append("app.exec")
            raise SystemExit(exit_code)

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail(
            "post-handoff app.exec() SystemExit must not dismiss the splash"
        ),
    )
    QTimer.singleShot(1000, event_loop.quit)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            editor_launcher.launch_editor(AppAdapter(), "repo-e129-real-qt")

        assert captured.value.code == exit_code
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "app.exec",
        ]
        event_loop.exec()

    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert calls[-1] == "splash.deleteLater"
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    assert "Failed to delete splash after editor startup handoff" not in caplog.text
