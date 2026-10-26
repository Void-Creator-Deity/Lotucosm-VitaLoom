# -*- coding: utf-8 -*-
"""E126 regressions for versioned runtime entrypoint-mode precedence."""
from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from FrameCore.lifecycle import FrameApi
from FrameCore.suite_registry import load_default_suite_manifest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_MAIN = (
    ROOT
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
    / "main.py"
)


def _frame_api() -> FrameApi:
    return FrameApi(
        app_root=ROOT,
        resource_root=ROOT,
        suite=load_default_suite_manifest(ROOT),
    )


def _install_package(monkeypatch: pytest.MonkeyPatch, name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = []  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, name, module)
    if "." in name:
        parent_name, attribute = name.rsplit(".", 1)
        monkeypatch.setattr(sys.modules[parent_name], attribute, module, raising=False)
    return module


def _install_runtime_import_stubs(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    _install_package(monkeypatch, "core")
    _install_package(monkeypatch, "core.VitaLoom")
    _install_package(monkeypatch, "core.VitaLoom.core")
    _install_package(monkeypatch, "core.VitaLoom.suite")
    _install_package(monkeypatch, "core.VitaLoom.ui")
    _install_package(monkeypatch, "core.VitaLoom.commands")

    bundle_paths = types.ModuleType("core.VitaLoom.core.bundle_paths")
    bundle_paths.ensure_cwd_application_root = lambda: calls.append("ensure_cwd")
    bundle_paths.resource_root = lambda: calls.append("resource_root") or ROOT
    monkeypatch.setitem(sys.modules, bundle_paths.__name__, bundle_paths)
    monkeypatch.setattr(sys.modules["core.VitaLoom.core"], "bundle_paths", bundle_paths, raising=False)

    runtime = SimpleNamespace(
        suite=SimpleNamespace(
            display_name="Lotucosm-VitaLoom",
            suite_id="lotucosm.vitaloom.suite",
            version="2026.7",
        ),
        product_version=SimpleNamespace(
            product_id="lotucosm-vitaloom",
            version="1.0.0",
        ),
    )
    bootstrap = types.ModuleType("core.VitaLoom.suite.runtime_bootstrap")

    def bootstrap_suite_runtime(received_root: Path) -> object:
        assert received_root == ROOT
        calls.append("bootstrap")
        return runtime

    bootstrap.bootstrap_suite_runtime = bootstrap_suite_runtime
    monkeypatch.setitem(sys.modules, bootstrap.__name__, bootstrap)
    monkeypatch.setattr(sys.modules["core.VitaLoom.suite"], "runtime_bootstrap", bootstrap, raising=False)

    qt = _install_package(monkeypatch, "PyQt6")
    qt_widgets = types.ModuleType("PyQt6.QtWidgets")

    class UnexpectedQApplication:
        @staticmethod
        def instance() -> None:
            calls.append("qt.instance")
            return None

        def __init__(self, *_args: object) -> None:
            calls.append("qt.construct")
            raise AssertionError("non-editor runtime mode must not construct QApplication")

    qt_widgets.QApplication = UnexpectedQApplication
    monkeypatch.setitem(sys.modules, qt_widgets.__name__, qt_widgets)
    monkeypatch.setattr(qt, "QtWidgets", qt_widgets, raising=False)

    launcher = types.ModuleType("core.VitaLoom.editor_launcher")
    launcher.launch_editor = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("non-editor runtime mode must not call launch_editor")
    )
    monkeypatch.setitem(sys.modules, launcher.__name__, launcher)
    monkeypatch.setattr(sys.modules["core.VitaLoom"], "editor_launcher", launcher, raising=False)

    design_tokens = types.ModuleType("core.VitaLoom.ui.design_tokens")
    design_tokens.apply_app_baseline = lambda *_args: calls.append("apply_baseline")
    monkeypatch.setitem(sys.modules, design_tokens.__name__, design_tokens)
    monkeypatch.setattr(sys.modules["core.VitaLoom.ui"], "design_tokens", design_tokens, raising=False)


def test_manifest_command_entry_forwards_only_command_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The manifest `command` token is removed before the CLI sees user args."""
    calls: list[str] = []
    _install_runtime_import_stubs(monkeypatch, calls)
    command = types.ModuleType("core.VitaLoom.commands.cli")

    def command_main(args: list[str]) -> int:
        assert args == ["inspect", "--strict"]
        calls.append("command")
        return 73

    command.main = command_main
    monkeypatch.setitem(sys.modules, command.__name__, command)
    monkeypatch.setattr(sys.modules["core.VitaLoom.commands"], "cli", command, raising=False)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pytest"])

    api = _frame_api()
    selected = api.select_product_version("lotucosm-vitaloom")
    with pytest.raises(SystemExit) as exit_info:
        api.run_product_entry(selected, "command", ["inspect", "--strict"])

    assert exit_info.value.code == 73
    assert sys.argv == [str(RUNTIME_MAIN), "command", "inspect", "--strict"]
    assert calls == ["command"]


def test_runtime_version_mode_precedes_normal_editor_composition(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--version` may coexist with editor flags but creates no editor resources."""
    calls: list[str] = []
    _install_runtime_import_stubs(monkeypatch, calls)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", [str(RUNTIME_MAIN), "--editor", "--version"])

    namespace = runpy.run_path(str(RUNTIME_MAIN), run_name="e126_runtime_version")
    assert namespace["main"]() is None

    assert capsys.readouterr().out.strip() == (
        "Lotucosm-VitaLoom 2026.7 / lotucosm-vitaloom 1.0.0"
    )
    assert calls == ["resource_root", "bootstrap"]


def test_runtime_smoke_mode_precedes_normal_editor_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Root editor routing with `--smoke-editor` stays on the dedicated smoke path."""
    calls: list[str] = []
    _install_runtime_import_stubs(monkeypatch, calls)
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(
        sys,
        "argv",
        [str(RUNTIME_MAIN), "--editor", "--smoke-editor", "--project", "world.pond"],
    )

    namespace = runpy.run_path(str(RUNTIME_MAIN), run_name="e126_runtime_smoke")
    namespace["main"].__globals__["_run_editor_smoke"] = lambda: calls.append("smoke") or 31

    with pytest.raises(SystemExit) as exit_info:
        namespace["main"]()

    assert exit_info.value.code == 31
    assert calls == ["smoke"]
