# -*- coding: utf-8 -*-
"""E146 proof that no-splash Kernel-show cleanup cannot mask an ordinary error."""
from __future__ import annotations

import logging

import pytest


def test_launcher_preserves_no_splash_kernel_show_runtime_error_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A null-splash cleanup error remains secondary to the Kernel-show error."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_error = RuntimeError("no-splash Kernel-show failed")
    cleanup_error = RuntimeError("no-splash Kernel-show cleanup failed")
    calls: list[object] = []

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

    def fail_to_dismiss(received: object) -> None:
        assert received is None
        calls.append(("splash.dismiss", received))
        raise cleanup_error

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("use_splash=False must not show splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda *_args: pytest.fail("use_splash=False must not send splash message"),
    )
    monkeypatch.setattr(
        splash_screen,
        "finish_splash",
        lambda *_args: pytest.fail("Kernel-show failure must not finish splash"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(App(), tmp_path, use_splash=False)

    assert captured.value is primary_error
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls[0][0] == "kernel.construct"
    assert set(calls[0][1]) == {"capability_registry"}
    assert calls[1:] == [
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
        ("splash.dismiss", None),
    ]
