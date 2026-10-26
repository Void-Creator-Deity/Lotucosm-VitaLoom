# -*- coding: utf-8 -*-
"""E154 proof for the no-splash Launcher-to-event-loop handoff boundary."""
from __future__ import annotations

import logging

import pytest


@pytest.mark.parametrize(
    ("outcome", "expected_type"),
    [
        pytest.param(241, None, id="normal-return"),
        pytest.param(RuntimeError("no-splash event loop failed"), RuntimeError, id="runtime-error"),
        pytest.param(SystemExit(239), SystemExit, id="controlled-exit"),
        pytest.param(KeyboardInterrupt(), KeyboardInterrupt, id="interrupt"),
    ],
)
def test_launcher_hands_off_completed_no_splash_startup_to_event_loop_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
    outcome: object,
    expected_type: type[BaseException] | None,
) -> None:
    """No-splash startup returns or propagates from app.exec without UI cleanup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []

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

    def unexpected_splash_api(*_args: object, **_kwargs: object) -> None:
        pytest.fail("use_splash=False must not consume a splash adapter API")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", unexpected_splash_api)
    monkeypatch.setattr(splash_screen, "splash_message", unexpected_splash_api)
    monkeypatch.setattr(splash_screen, "finish_splash", unexpected_splash_api)
    monkeypatch.setattr(splash_screen, "dismiss_splash", unexpected_splash_api)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        if expected_type is None:
            assert editor_launcher.launch_editor(App(), tmp_path, use_splash=False) == outcome
        else:
            with pytest.raises(expected_type) as captured:
                editor_launcher.launch_editor(App(), tmp_path, use_splash=False)
            assert captured.value is outcome

    assert calls[0][0] == "kernel.construct"
    assert set(calls[0][1]) == {"capability_registry"}
    assert calls[1:] == [
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        "app.exec",
    ]
    assert calls.count("app.exec") == 1
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
