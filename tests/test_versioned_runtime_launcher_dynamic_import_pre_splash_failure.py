# -*- coding: utf-8 -*-
"""E134 proofs for dynamic Launcher imports before splash ownership begins."""
from __future__ import annotations

import builtins

import pytest


_RUNTIME_REGISTRY_MODULE = "core.VitaLoom.core.runtime_capability_registry"


def _forbid_resource_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("import failure must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("import failure must not show a splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("import failure must not attempt splash cleanup"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("import failure must not resolve plugin layers"),
    )


def _fail_runtime_registry_import(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
    import_calls: list[str],
) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=(), fromlist=(), level=0):
        import_calls.append(name)
        if name == _RUNTIME_REGISTRY_MODULE:
            raise primary_error
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


@pytest.mark.parametrize(
    "primary_error",
    [SystemExit(151), RuntimeError("runtime registry import failed")],
)
def test_launcher_preserves_dynamic_import_failure_before_splash_allocation(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
) -> None:
    """The first actual dynamic import precedes all Launcher-owned resources."""

    from core.VitaLoom import editor_launcher

    _forbid_resource_startup(monkeypatch)
    import_calls: list[str] = []
    _fail_runtime_registry_import(monkeypatch, primary_error, import_calls)

    class App:
        def exec(self) -> int:
            raise AssertionError("import failure must not enter app.exec()")

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), "repo-e134")

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert import_calls == [_RUNTIME_REGISTRY_MODULE]


def test_launcher_keeps_keyboard_interrupt_outside_dynamic_import_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt from import remains unclassified with no cleanup attempt."""

    from core.VitaLoom import editor_launcher

    _forbid_resource_startup(monkeypatch)
    interrupt = KeyboardInterrupt()
    import_calls: list[str] = []
    _fail_runtime_registry_import(monkeypatch, interrupt, import_calls)

    class App:
        def exec(self) -> int:
            raise AssertionError("KeyboardInterrupt must not enter app.exec()")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(App(), "repo-e134-keyboard-interrupt")

    assert captured.value is interrupt
    assert import_calls == [_RUNTIME_REGISTRY_MODULE]