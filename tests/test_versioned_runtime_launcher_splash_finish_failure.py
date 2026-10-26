# -*- coding: utf-8 -*-
"""E150 proofs for splash-finish failures after a successful Kernel show."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("primary_error", "cleanup_expected"),
    [
        (RuntimeError("splash finish failed"), True),
        (SystemExit(229), True),
        (KeyboardInterrupt(), False),
    ],
    ids=["runtime-error", "system-exit", "keyboard-interrupt"],
)
def test_launcher_preserves_splash_finish_failure_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    primary_error: BaseException,
    cleanup_expected: bool,
) -> None:
    """Only classified finish failures traverse owned-splash cleanup."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            pytest.fail("splash-finish failure must not enter app.exec()")

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
        raise primary_error

    def dismiss(received: object) -> None:
        if not cleanup_expected:
            pytest.fail("KeyboardInterrupt must not enter owned-splash cleanup")
        assert received is splash
        calls.append(("splash.dismiss", received))

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
    monkeypatch.setattr(splash_screen, "dismiss_splash", dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), tmp_path)

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == 229
    assert calls[:2] == ["splash.show", "splash.message"]
    assert calls[2][0] == "kernel.construct"
    assert set(calls[2][1]) == {"capability_registry"}
    expected: list[object] = [
        "splash.message",
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "splash.message",
        "kernel.show",
        "splash.finish",
    ]
    if cleanup_expected:
        expected.append(("splash.dismiss", splash))
    assert calls[3:] == expected
