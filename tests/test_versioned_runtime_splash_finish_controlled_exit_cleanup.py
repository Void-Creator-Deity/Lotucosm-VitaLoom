# -*- coding: utf-8 -*-
"""E132 proofs for controlled exits before versioned-runtime splash handoff completes."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    ("failure_stage", "primary_error"),
    [
        ("finish_system_exit", SystemExit(131)),
        ("schedule_system_exit", SystemExit(133)),
        ("finish_runtime_error", RuntimeError("native splash finish failed")),
    ],
)
def test_launcher_releases_incomplete_splash_handoff_and_preserves_primary_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
    primary_error: BaseException,
) -> None:
    """Failures before deferred deletion is scheduled stay in E128 cleanup ownership."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []
    scheduled_callbacks: list[object] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")
            if failure_stage in {"finish_system_exit", "finish_runtime_error"}:
                raise primary_error

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            raise AssertionError("incomplete splash handoff must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            assert layers == {"l1": []}
            calls.append("kernel.load")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(_milliseconds: int, callback: object) -> None:
            calls.append("timer.singleShot")
            if failure_stage == "schedule_system_exit":
                raise primary_error
            scheduled_callbacks.append(callback)

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

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), "repo-e132-incomplete-handoff")

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert scheduled_callbacks == []

    expected = [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load",
        "splash.message",
        "kernel.show",
        "splash.finish",
    ]
    if failure_stage == "schedule_system_exit":
        expected.append("timer.singleShot")
    expected.extend(["splash.hide", "splash.deleteLater"])
    assert calls == expected


def test_launcher_preserves_finish_system_exit_when_incomplete_handoff_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A cleanup warning cannot replace a controlled exit from native splash finish."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_exit = SystemExit(135)
    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[str] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("finish SystemExit must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, _layers: object) -> None:
            calls.append("kernel.load")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    def fail_finish(_splash: object, received_widget: object) -> None:
        assert _splash is splash
        assert received_widget is kernel
        calls.append("splash.finish")
        raise primary_exit

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")
        raise cleanup_error

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
    monkeypatch.setattr(splash_screen, "finish_splash", fail_finish)
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            editor_launcher.launch_editor(App(), "repo-e132-cleanup-warning")

    assert captured.value is primary_exit
    assert captured.value.code == 135
    assert calls.count("splash.dismiss") == 1
    assert "Failed to dismiss splash after editor startup failure" in caplog.text


def test_launcher_keeps_keyboard_interrupt_outside_incomplete_handoff_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt is not a controlled exit and bypasses Launcher cleanup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[str] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("KeyboardInterrupt must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, _layers: object) -> None:
            calls.append("kernel.load")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    def interrupt_finish(received_splash: object, received_widget: object) -> None:
        assert received_splash is splash
        assert received_widget is kernel
        calls.append("splash.finish")
        raise KeyboardInterrupt

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
    monkeypatch.setattr(splash_screen, "finish_splash", interrupt_finish)
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("KeyboardInterrupt must not enter controlled cleanup"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with pytest.raises(KeyboardInterrupt):
        editor_launcher.launch_editor(App(), "repo-e132-keyboard-interrupt")

    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load",
        "splash.message",
        "kernel.show",
        "splash.finish",
    ]