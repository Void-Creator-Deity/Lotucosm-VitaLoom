# -*- coding: utf-8 -*-
"""E125 regressions for the FrameCore-to-versioned-runtime composition boundary."""
from __future__ import annotations

import os
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


def _install_runtime_editor_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    selected_version: object,
    launch_behavior: object,
    calls: list[str],
) -> list[object]:
    """Install only the runtime composition seams; no real Qt/UI host is loaded."""

    _install_package(monkeypatch, "core")
    _install_package(monkeypatch, "core.VitaLoom")
    _install_package(monkeypatch, "core.VitaLoom.core")
    _install_package(monkeypatch, "core.VitaLoom.suite")
    _install_package(monkeypatch, "core.VitaLoom.ui")

    bundle_paths = types.ModuleType("core.VitaLoom.core.bundle_paths")
    bundle_paths.ensure_cwd_application_root = lambda: calls.append("ensure_cwd")
    bundle_paths.resource_root = lambda: calls.append("resource_root") or ROOT
    monkeypatch.setitem(sys.modules, bundle_paths.__name__, bundle_paths)
    monkeypatch.setattr(sys.modules["core.VitaLoom.core"], "bundle_paths", bundle_paths, raising=False)

    runtime = SimpleNamespace(
        suite=SimpleNamespace(suite_id="lotucosm.vitaloom.suite"),
        product_version=selected_version,
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
    app = object()
    constructed: list[object] = []

    class FakeQApplication:
        def __init__(self, *args: object) -> None:
            constructed.append(args)

        @staticmethod
        def instance() -> object:
            calls.append("qt.instance")
            return app

    qt_widgets.QApplication = FakeQApplication
    monkeypatch.setitem(sys.modules, qt_widgets.__name__, qt_widgets)
    monkeypatch.setattr(qt, "QtWidgets", qt_widgets, raising=False)

    design_tokens = types.ModuleType("core.VitaLoom.ui.design_tokens")

    def apply_app_baseline(received_app: object) -> None:
        assert received_app is app
        calls.append("apply_baseline")

    design_tokens.apply_app_baseline = apply_app_baseline
    monkeypatch.setitem(sys.modules, design_tokens.__name__, design_tokens)
    monkeypatch.setattr(sys.modules["core.VitaLoom.ui"], "design_tokens", design_tokens, raising=False)

    launcher = types.ModuleType("core.VitaLoom.editor_launcher")

    def launch_editor(
        received_app: object,
        received_root: str,
        *,
        project_path: str | None,
        use_splash: bool,
    ) -> int:
        assert received_app is app
        assert received_root == str(ROOT)
        assert use_splash is True
        calls.append(f"launch:{project_path}")
        if isinstance(launch_behavior, Exception):
            raise launch_behavior
        return int(launch_behavior)

    launcher.launch_editor = launch_editor
    monkeypatch.setitem(sys.modules, launcher.__name__, launcher)
    monkeypatch.setattr(sys.modules["core.VitaLoom"], "editor_launcher", launcher, raising=False)

    return constructed


def test_frame_api_runtime_environment_selects_the_same_manifest_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The selected FrameCore ProductVersion is the runtime bootstrap identity."""
    from core.VitaLoom.suite.runtime_bootstrap import bootstrap_suite_runtime

    api = _frame_api()
    selected = api.select_product_version("lotucosm-vitaloom")
    assert selected.version == "1.0.0"
    assert selected.entrypoints["editor"] == "runtime/main.py --editor"

    monkeypatch.setattr(sys, "path", list(sys.path))
    api.install_runtime_env(selected)
    runtime = bootstrap_suite_runtime(ROOT)

    assert runtime.product_version == selected
    assert runtime.product_version.version_root == selected.version_root
    assert Path(os.environ["VITALOOM_SUITE_ROOT"]).resolve() == api.suite.suite_root
    assert Path(os.environ["VITALOOM_PRODUCT_VERSION_ROOT"]).resolve() == selected.version_root


def test_frame_api_editor_entry_hands_selected_version_and_project_to_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The real runpy boundary preserves manifest entry arguments and Qt ownership."""
    api = _frame_api()
    selected = api.select_product_version("lotucosm-vitaloom")
    calls: list[str] = []
    constructed = _install_runtime_editor_stubs(
        monkeypatch,
        selected_version=selected,
        launch_behavior=47,
        calls=calls,
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pytest"])
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        api.run_product_entry(selected, "editor", ["--project", "workspace.pond"])

    assert exit_info.value.code == 47
    assert sys.argv == [
        str(RUNTIME_MAIN),
        "--editor",
        "--project",
        "workspace.pond",
    ]
    assert calls == [
        "ensure_cwd",
        "resource_root",
        "bootstrap",
        "qt.instance",
        "apply_baseline",
        "resource_root",
        f"launch:{tmp_path / 'workspace.pond'}",
    ]
    assert constructed == []


def test_runtime_converts_launcher_exception_at_its_own_boundary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A launcher failure becomes runtime SystemExit(1), not an L0 lifecycle action."""
    api = _frame_api()
    selected = api.select_product_version("lotucosm-vitaloom")
    calls: list[str] = []
    constructed = _install_runtime_editor_stubs(
        monkeypatch,
        selected_version=selected,
        launch_behavior=RuntimeError("launcher boundary failure"),
        calls=calls,
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["pytest"])
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        api.run_product_entry(selected, "editor", ["--project", "workspace.pond"])

    assert exit_info.value.code == 1
    assert "ERROR: failed to start VitaLoom product runtime: launcher boundary failure" in capsys.readouterr().out
    assert calls == [
        "ensure_cwd",
        "resource_root",
        "bootstrap",
        "qt.instance",
        "apply_baseline",
        "resource_root",
        f"launch:{tmp_path / 'workspace.pond'}",
    ]
    assert constructed == []
