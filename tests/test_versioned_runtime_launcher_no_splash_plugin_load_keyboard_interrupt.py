# -*- coding: utf-8 -*-
"""E143 proof for an unclassified no-splash plugin-load interruption."""
from __future__ import annotations

import pytest


def test_launcher_keeps_no_splash_plugin_load_keyboard_interrupt_outside_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """KeyboardInterrupt skips even the safe null-cleanup adapter."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    error = KeyboardInterrupt()
    calls: list[object] = []

    class App:
        def exec(self) -> int:
            pytest.fail("no-splash plugin-load KeyboardInterrupt must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))
            raise error

        def show(self) -> None:
            pytest.fail("no-splash plugin-load KeyboardInterrupt must not show Kernel")

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
        lambda *_args: pytest.fail("no-splash interruption must not finish splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _value: pytest.fail("KeyboardInterrupt must not enter null cleanup"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=False)

    assert captured.value is error
    assert calls[0][0] == "kernel.construct"
    assert set(calls[0][1]) == {"capability_registry"}
    assert calls[1:] == [
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
    ]
