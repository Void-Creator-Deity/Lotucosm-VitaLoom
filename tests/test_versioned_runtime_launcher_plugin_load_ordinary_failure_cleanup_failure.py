# -*- coding: utf-8 -*-
"""E141 proof that plugin-load cleanup failures cannot mask an ordinary error."""
from __future__ import annotations

import logging

import pytest


def test_launcher_preserves_plugin_load_runtime_error_when_splash_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An ordinary cleanup error remains secondary to the plugin-load error."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_error = RuntimeError("plugin-load primary failure")
    cleanup_error = RuntimeError("plugin-load splash cleanup failed")
    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            pytest.fail("plugin-load failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))
            raise primary_error

        def show(self) -> None:
            pytest.fail("plugin-load failure must not show Kernel")

    def fail_to_dismiss(received: object) -> None:
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
        lambda *_args: pytest.fail("plugin-load failure must not finish splash"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
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
        ("splash.dismiss", splash),
    ]


