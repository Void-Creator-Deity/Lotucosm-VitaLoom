# -*- coding: utf-8 -*-
"""E138 proofs for Kernel show failure before splash handoff."""
from __future__ import annotations

import pytest


def _install_reachable_show_seam(
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

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")
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
        lambda _splash, _kernel: pytest.fail("Kernel-show failure must not finish splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )
    return splash


def _assert_reached_show(
    calls: list[object],
    tmp_path,
    *,
    splash: object | None,
) -> None:
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    assert calls[3:7] == [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "splash.message",
    ]
    assert calls[7] == "kernel.show"
    if splash is None:
        assert calls[8:] == []
    else:
        assert calls[8:] == [("splash.dismiss", splash)]


@pytest.mark.parametrize(
    "primary_error",
    [SystemExit(191), RuntimeError("kernel show failed")],
)
def test_launcher_cleans_splash_once_and_preserves_kernel_show_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    primary_error: BaseException,
) -> None:
    """Failures from Kernel show retain E128 cleanup before splash handoff."""

    from core.VitaLoom import editor_launcher

    calls: list[object] = []
    splash = _install_reachable_show_seam(monkeypatch, primary_error, calls)

    class App:
        def exec(self) -> int:
            pytest.fail("Kernel-show failure must not enter app.exec()")

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=True)

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    _assert_reached_show(calls, tmp_path, splash=splash)


def test_launcher_keeps_keyboard_interrupt_outside_kernel_show_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """KeyboardInterrupt at Kernel show remains unclassified and cleanup-free."""

    from core.VitaLoom import editor_launcher

    interrupt = KeyboardInterrupt()
    calls: list[object] = []
    _install_reachable_show_seam(monkeypatch, interrupt, calls)

    class App:
        def exec(self) -> int:
            pytest.fail("KeyboardInterrupt must not enter app.exec()")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=True)

    assert captured.value is interrupt
    _assert_reached_show(calls, tmp_path, splash=None)