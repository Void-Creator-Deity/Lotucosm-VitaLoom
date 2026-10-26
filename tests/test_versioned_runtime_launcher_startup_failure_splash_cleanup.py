# -*- coding: utf-8 -*-
"""E128 regressions for Launcher startup-failure splash cleanup ownership."""
from __future__ import annotations

import logging
from pathlib import Path

import pytest


@pytest.mark.parametrize("failure_stage", ["construct", "project", "plugin"])
def test_launcher_dismisses_splash_once_and_preserves_each_startup_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure_stage: str,
) -> None:
    """Every normal startup failure releases Launcher-owned splash before re-raising."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    primary_error = RuntimeError(f"{failure_stage} failed")
    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("failed startup must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")
            if failure_stage == "construct":
                raise primary_error

        def set_startup_project(self, project_path: str) -> None:
            calls.append(("kernel.project", project_path))
            if failure_stage == "project":
                raise primary_error

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load", layers))
            if failure_stage == "plugin":
                raise primary_error

        def show(self) -> None:
            raise AssertionError("failed startup must not show the Kernel")

    monkeypatch.chdir(tmp_path)
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
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: calls.append(("plugin.layers", root)) or {"l1": []},
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(
            App(),
            tmp_path,
            project_path="world.pond",
            use_splash=True,
        )

    assert captured.value is primary_error
    expected: list[object] = ["splash.show", "splash.message", "kernel.construct"]
    if failure_stage != "construct":
        expected.append(("kernel.project", str(tmp_path / "world.pond")))
    if failure_stage == "plugin":
        expected.extend(
            [
                "splash.message",
                ("plugin.layers", str(tmp_path)),
                ("kernel.load", {"l1": []}),
            ]
        )
    expected.append(("splash.dismiss", splash))
    assert calls == expected


def test_launcher_dismisses_splash_and_preserves_controlled_system_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A controlled startup exit remains unchanged while Launcher releases splash."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("startup SystemExit must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def set_startup_project(self, project_path: str) -> None:
            calls.append(("kernel.project", project_path))
            raise SystemExit(71)

    monkeypatch.chdir(tmp_path)
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
        "dismiss_splash",
        lambda received: calls.append(("splash.dismiss", received)),
    )

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(App(), tmp_path, project_path="world.pond")

    assert captured.value.code == 71
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        ("kernel.project", str(tmp_path / "world.pond")),
        ("splash.dismiss", splash),
    ]


def test_launcher_preserves_controlled_system_exit_when_splash_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Cleanup failures stay secondary to the controlled startup exit."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[object] = []
    splash = object()

    class App:
        def exec(self) -> int:
            raise AssertionError("startup SystemExit must not enter app.exec()")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def set_startup_project(self, project_path: str) -> None:
            calls.append(("kernel.project", project_path))
            raise SystemExit(73)

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append(("splash.dismiss", received))
        raise cleanup_error

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(splash_screen, "show_vitaloom_splash", lambda _app: splash)
    monkeypatch.setattr(splash_screen, "splash_message", lambda *_args: None)
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(SystemExit) as captured:
            editor_launcher.launch_editor(App(), tmp_path, project_path="world.pond")

    assert captured.value.code == 73
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls == [
        "kernel.construct",
        ("kernel.project", str(tmp_path / "world.pond")),
        ("splash.dismiss", splash),
    ]
