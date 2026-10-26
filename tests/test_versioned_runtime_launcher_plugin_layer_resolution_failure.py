# -*- coding: utf-8 -*-
"""E137 proofs for plugin-layer resolution after Launcher owns a splash."""
from __future__ import annotations

import pytest


def _install_reachable_startup_seam(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
    calls: list[object],
) -> object:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    splash = object()

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, _layers: object) -> None:
            pytest.fail("layer-resolution failure must not load plugins")

        def show(self) -> None:
            pytest.fail("layer-resolution failure must not show Kernel")

    def fail_layer_resolution(root: str) -> dict[str, list[str]]:
        calls.append(("plugin.layers", root))
        raise primary_error

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
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
        splash_screen,
        "finish_splash",
        lambda _splash, _kernel: pytest.fail("layer-resolution failure must not finish splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", fail_layer_resolution)
    return splash


@pytest.mark.parametrize(
    "primary_error",
    [SystemExit(181), RuntimeError("plugin-layer resolution failed")],
)
def test_launcher_cleans_splash_once_and_preserves_layer_resolution_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    primary_error: BaseException,
) -> None:
    """Normal and controlled startup failures retain the owned-splash cleanup path."""

    from core.VitaLoom import editor_launcher

    calls: list[object] = []
    splash = _install_reachable_startup_seam(monkeypatch, primary_error, calls)

    class App:
        def exec(self) -> int:
            pytest.fail("layer-resolution failure must not enter app.exec()")

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=True)

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:] == [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
        ("splash.dismiss", splash),
    ]


def test_launcher_keeps_keyboard_interrupt_outside_layer_resolution_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """KeyboardInterrupt is deliberately not converted into startup cleanup."""

    from core.VitaLoom import editor_launcher

    interrupt = KeyboardInterrupt()
    calls: list[object] = []
    _install_reachable_startup_seam(monkeypatch, interrupt, calls)

    class App:
        def exec(self) -> int:
            pytest.fail("KeyboardInterrupt must not enter app.exec()")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=True)

    assert captured.value is interrupt
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:] == [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
    ]