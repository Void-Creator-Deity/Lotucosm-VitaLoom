# -*- coding: utf-8 -*-
"""E142 proofs for plugin-load failures with Launcher splash disabled."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "primary_error",
    [RuntimeError("plugin-load ordinary failure"), SystemExit(205)],
    ids=["runtime-error", "system-exit"],
)
def test_launcher_preserves_no_splash_plugin_load_failure_with_null_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    primary_error: BaseException,
) -> None:
    """The existing null cleanup path cannot affect a no-splash startup failure."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []

    class App:
        def exec(self) -> int:
            pytest.fail("no-splash plugin-load failure must not enter app.exec()")

    class Kernel:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("kernel.construct", kwargs))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))
            raise primary_error

        def show(self) -> None:
            pytest.fail("no-splash plugin-load failure must not show Kernel")

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
        lambda *_args: pytest.fail("no-splash plugin-load failure must not finish splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda value: calls.append(("splash.dismiss", value)),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), tmp_path, use_splash=False)

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == 205
    assert calls[0][0] == "kernel.construct"
    assert set(calls[0][1]) == {"capability_registry"}
    assert calls[1:] == [
        ("plugin.layers", str(tmp_path)),
        ("kernel.load", {"l1": []}),
        ("splash.dismiss", None),
    ]
