# -*- coding: utf-8 -*-
"""E153 proof for the successful Launcher-to-event-loop handoff boundary."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    ("outcome", "expected_type"),
    [
        pytest.param(239, None, id="normal-return"),
        pytest.param(RuntimeError("event loop failed"), RuntimeError, id="runtime-error"),
        pytest.param(SystemExit(237), SystemExit, id="controlled-exit"),
        pytest.param(KeyboardInterrupt(), KeyboardInterrupt, id="interrupt"),
    ],
)
def test_launcher_hands_off_completed_splash_startup_to_event_loop_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
    outcome: object,
    expected_type: type[BaseException] | None,
) -> None:
    """A completed startup returns or propagates from app.exec without cleanup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            if isinstance(outcome, BaseException):
                raise outcome
            assert isinstance(outcome, int)
            return outcome

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")

    def finish(received_splash: object, received_kernel: object) -> None:
        assert received_splash is splash
        assert isinstance(received_kernel, Kernel)
        calls.append("splash.finish")

    def unexpected_dismiss(received_splash: object) -> None:
        calls.append(("splash.dismiss", received_splash))
        pytest.fail("completed splash handoff must not trigger startup cleanup")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda *_args: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "finish_splash", finish)
    monkeypatch.setattr(splash_screen, "dismiss_splash", unexpected_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        if expected_type is None:
            assert editor_launcher.launch_editor(App(), tmp_path) == outcome
        else:
            with pytest.raises(expected_type) as captured:
                editor_launcher.launch_editor(App(), tmp_path)
            assert captured.value is outcome

    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:] == [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "splash.message",
        "kernel.show",
        "splash.finish",
        "app.exec",
    ]
    assert calls.count("app.exec") == 1
    assert not any(
        isinstance(call, tuple) and call[0] == "splash.dismiss" for call in calls
    )
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
