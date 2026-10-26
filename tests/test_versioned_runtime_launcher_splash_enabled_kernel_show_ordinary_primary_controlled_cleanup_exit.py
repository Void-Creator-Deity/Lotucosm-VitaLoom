# -*- coding: utf-8 -*-
"""E149 proof for owned-splash controlled cleanup after an ordinary show error."""
from __future__ import annotations

import logging

import pytest


def test_launcher_preserves_kernel_show_runtime_error_when_owned_cleanup_exits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A controlled cleanup exit cannot replace the active Kernel-show error."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_error = RuntimeError("owned-splash Kernel-show failed")
    cleanup_error = SystemExit(224)
    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            pytest.fail("Kernel-show failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")
            raise primary_error

    def exit_during_dismiss(received: object) -> None:
        assert received is splash
        calls.append(("splash.dismiss", received))
        raise cleanup_error

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
    monkeypatch.setattr(
        splash_screen,
        "finish_splash",
        lambda *_args: pytest.fail("Kernel-show failure must not finish splash"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", exit_during_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(App(), tmp_path)

    assert captured.value is primary_error
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:] == [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "splash.message",
        "kernel.show",
        ("splash.dismiss", splash),
    ]
