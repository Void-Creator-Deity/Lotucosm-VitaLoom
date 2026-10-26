# -*- coding: utf-8 -*-
"""E144 proofs for no-splash Kernel show failures after plugin loading."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("primary_error", "cleanup_expected"),
    [
        (RuntimeError("kernel show failed"), True),
        (SystemExit(211), True),
        (KeyboardInterrupt(), False),
    ],
    ids=["runtime-error", "system-exit", "keyboard-interrupt"],
)
def test_launcher_preserves_no_splash_kernel_show_failure_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    primary_error: BaseException,
    cleanup_expected: bool,
) -> None:
    """Only ordinary and controlled exits traverse the safe null cleanup path."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []

    class App:
        def exec(self) -> int:
            pytest.fail("no-splash Kernel-show failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))

        def show(self) -> None:
            calls.append("kernel.show")
            raise primary_error

    def dismiss(value: object) -> None:
        if not cleanup_expected:
            pytest.fail("KeyboardInterrupt must not enter null cleanup")
        calls.append(("splash.dismiss", value))

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
        lambda *_args: pytest.fail("no-splash Kernel-show failure must not finish splash"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=False)

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == 211
    assert calls[0][0] == "kernel.construct"
    assert set(calls[0][1]) == {"capability_registry"}
    expected: list[object] = [
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        "kernel.show",
    ]
    if cleanup_expected:
        expected.append(("splash.dismiss", None))
    assert calls[1:] == expected
