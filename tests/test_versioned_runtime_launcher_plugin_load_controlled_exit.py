# -*- coding: utf-8 -*-
"""E139 proofs for plugin-load controlled exits before splash handoff."""
from __future__ import annotations

import pytest


def _install_plugin_load_failure(monkeypatch, error, calls):
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    splash = object()

    class Kernel:
        def __init__(self, **kwargs):
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers):
            calls.append(("kernel.load", layers))
            raise error

        def show(self):
            pytest.fail("plugin-load failure must not show Kernel")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", lambda _app: calls.append("splash.show") or splash)
    monkeypatch.setattr(splash_screen, "splash_message", lambda *_args: calls.append("splash.message"))
    monkeypatch.setattr(splash_screen, "finish_splash", lambda *_args: pytest.fail("plugin-load failure must not finish splash"))
    monkeypatch.setattr(splash_screen, "dismiss_splash", lambda value: calls.append(("splash.dismiss", value)))
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda root: calls.append(("plugin.layers", root)) or {"l1": []})
    return splash


def _assert_load_boundary(calls, tmp_path, splash):
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:] == ["splash.message", ("plugin.layers", str(tmp_path)), ("kernel.load", {"l1": []})] + ([] if splash is None else [("splash.dismiss", splash)])


def test_launcher_cleans_splash_once_and_preserves_plugin_load_system_exit(monkeypatch, tmp_path):
    from core.VitaLoom import editor_launcher

    error = SystemExit(201)
    calls = []
    splash = _install_plugin_load_failure(monkeypatch, error, calls)

    class App:
        def exec(self):
            pytest.fail("plugin-load SystemExit must not enter app.exec")

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(App(), tmp_path)

    assert captured.value is error
    assert captured.value.code == 201
    _assert_load_boundary(calls, tmp_path, splash)


def test_launcher_keeps_keyboard_interrupt_outside_plugin_load_cleanup(monkeypatch, tmp_path):
    from core.VitaLoom import editor_launcher

    error = KeyboardInterrupt()
    calls = []
    _install_plugin_load_failure(monkeypatch, error, calls)

    class App:
        def exec(self):
            pytest.fail("plugin-load KeyboardInterrupt must not enter app.exec")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), tmp_path)

    assert captured.value is error
    _assert_load_boundary(calls, tmp_path, None)
