# -*- coding: utf-8 -*-
"""E127 regressions for normal versioned-runtime editor UI-host ownership."""
from __future__ import annotations

import os
import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


_OFFSCREEN_APPLICATION: object | None = None

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


def _install_package(monkeypatch: pytest.MonkeyPatch, name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = []  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, name, module)
    if "." in name:
        parent_name, attribute = name.rsplit(".", 1)
        monkeypatch.setattr(sys.modules[parent_name], attribute, module, raising=False)
    return module


def _install_normal_editor_stubs(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[object],
    *,
    existing_application: bool,
    launch_behavior: object,
) -> list[object]:
    """Install only normal-editor composition seams around the versioned runtime."""

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
        product_version=SimpleNamespace(
            product_id="lotucosm-vitaloom",
            version="1.0.0",
        )
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
    constructed: list[object] = []
    existing = object()

    class FakeQApplication:
        @staticmethod
        def instance() -> object | None:
            calls.append("qt.instance")
            if existing_application:
                return existing
            return constructed[0] if constructed else None

        def __init__(self, argv: list[str]) -> None:
            assert argv == sys.argv
            constructed.append(self)
            calls.append("qt.construct")

    qt_widgets.QApplication = FakeQApplication
    monkeypatch.setitem(sys.modules, qt_widgets.__name__, qt_widgets)
    monkeypatch.setattr(qt, "QtWidgets", qt_widgets, raising=False)

    design_tokens = types.ModuleType("core.VitaLoom.ui.design_tokens")

    def apply_app_baseline(app: object) -> None:
        expected_app = existing if existing_application else constructed[0]
        assert app is expected_app
        calls.append("apply_baseline")

    design_tokens.apply_app_baseline = apply_app_baseline
    monkeypatch.setitem(sys.modules, design_tokens.__name__, design_tokens)
    monkeypatch.setattr(sys.modules["core.VitaLoom.ui"], "design_tokens", design_tokens, raising=False)

    launcher = types.ModuleType("core.VitaLoom.editor_launcher")

    def launch_editor(
        app: object,
        repo_root: str,
        *,
        project_path: str | None,
        use_splash: bool,
    ) -> int:
        expected_app = existing if existing_application else constructed[0]
        assert app is expected_app
        assert repo_root == str(ROOT)
        assert use_splash is True
        calls.append(("launch", project_path))
        if isinstance(launch_behavior, BaseException):
            raise launch_behavior
        return int(launch_behavior)

    launcher.launch_editor = launch_editor
    monkeypatch.setitem(sys.modules, launcher.__name__, launcher)
    monkeypatch.setattr(sys.modules["core.VitaLoom"], "editor_launcher", launcher, raising=False)

    return constructed


def _run_normal_editor_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    argv: list[str],
    existing_application: bool,
    launch_behavior: object,
) -> tuple[list[object], list[object]]:
    calls: list[object] = []
    constructed = _install_normal_editor_stubs(
        monkeypatch,
        calls,
        existing_application=existing_application,
        launch_behavior=launch_behavior,
    )
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", [str(RUNTIME_MAIN), *argv])
    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(str(RUNTIME_MAIN), run_name="e127_runtime_normal_editor")

    with pytest.raises(SystemExit) as exit_info:
        namespace["main"]()

    return calls, [exit_info.value, *constructed]


def test_normal_editor_constructs_one_application_and_delegates_project_to_launcher(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The versioned runtime owns app construction, then delegates UI-host creation."""

    calls, outcome = _run_normal_editor_main(
        monkeypatch,
        tmp_path,
        argv=["--editor", "--project", "workspace.pond"],
        existing_application=False,
        launch_behavior=37,
    )

    exit_info, *constructed = outcome
    assert exit_info.code == 37
    assert len(constructed) == 1
    assert calls == [
        "ensure_cwd",
        "resource_root",
        "bootstrap",
        "qt.instance",
        "qt.construct",
        "apply_baseline",
        "resource_root",
        ("launch", str(tmp_path / "workspace.pond")),
    ]


def test_normal_editor_reuses_existing_application_without_constructing_another(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Embedding the runtime does not transfer QApplication ownership to Launcher."""

    calls, outcome = _run_normal_editor_main(
        monkeypatch,
        tmp_path,
        argv=["--editor"],
        existing_application=True,
        launch_behavior=41,
    )

    exit_info, *constructed = outcome
    assert exit_info.code == 41
    assert constructed == []
    assert calls == [
        "ensure_cwd",
        "resource_root",
        "bootstrap",
        "qt.instance",
        "apply_baseline",
        "resource_root",
        ("launch", None),
    ]


def test_normal_editor_preserves_launcher_system_exit_without_runtime_error_conversion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A controlled Launcher exit crosses the versioned-runtime boundary unchanged."""

    calls, outcome = _run_normal_editor_main(
        monkeypatch,
        tmp_path,
        argv=["--editor"],
        existing_application=True,
        launch_behavior=SystemExit(67),
    )

    exit_info, *constructed = outcome
    assert exit_info.code == 67
    assert constructed == []
    assert calls[-1] == ("launch", None)


def test_launcher_constructs_kernel_and_runs_its_ui_host_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Launcher, not FrameCore L0, creates the Kernel/UI-host composition."""

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    calls: list[object] = []
    captured: dict[str, object] = {}

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 53

    class Kernel:
        def __init__(self, *, capability_registry: object) -> None:
            captured["registry"] = capability_registry
            calls.append("kernel.construct")

        def set_startup_project(self, project_path: str) -> None:
            calls.append(("kernel.set_startup_project", project_path))

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(("kernel.load_plugins_layered", layers))

        def show(self) -> None:
            calls.append("kernel.show")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda root: {"root": [root]})

    assert editor_launcher.launch_editor(
        App(),
        tmp_path,
        project_path="world.pond",
        use_splash=False,
    ) == 53
    assert captured["registry"].__class__.__name__ == "InMemoryRuntimeCapabilityRegistry"
    assert calls == [
        "kernel.construct",
        ("kernel.set_startup_project", str(tmp_path / "world.pond")),
        ("kernel.load_plugins_layered", {"root": [str(tmp_path)]}),
        "kernel.show",
        "app.exec",
    ]

def test_normal_editor_kernel_shows_real_offscreen_pixels(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The legacy UI-host adapter can still render a real normal-editor frame offscreen."""

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("VITALOOM_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("VITALOOM_SKIP_AUTO_OPEN", "1")

    from PyQt6.QtWidgets import QApplication
    from core.VitaLoom.core import bundle_paths
    from core.VitaLoom.editor_launcher import default_plugin_layers
    from core.VitaLoom.kernel import EditorKernel
    from core.VitaLoom.project.project_world_host_composition import (
        dispose_project_world_host_if_idle,
    )
    from core.VitaLoom.ui.design_tokens import apply_app_baseline

    global _OFFSCREEN_APPLICATION
    original_system_config_dir = bundle_paths.system_config_dir
    bundle_paths.system_config_dir = lambda: tmp_path / "workspace" / "state" / "system"
    kernel: EditorKernel | None = None
    try:
        assert dispose_project_world_host_if_idle() is True
        app = QApplication.instance()
        if app is None:
            _OFFSCREEN_APPLICATION = QApplication([])
            app = _OFFSCREEN_APPLICATION
        apply_app_baseline(app)
        kernel = EditorKernel()
        kernel.load_plugins_layered(default_plugin_layers(str(ROOT)))
        kernel.show()
        app.processEvents()

        frame = kernel.grab().toImage()
        assert kernel.isVisible() is True
        assert frame.width() > 0 and frame.height() > 0
        assert frame.pixelColor(frame.width() // 2, frame.height() // 2).alpha() > 0
    finally:
        if kernel is not None:
            kernel.close()
            app = QApplication.instance()
            if app is not None:
                app.processEvents()
        bundle_paths.system_config_dir = original_system_config_dir
        assert dispose_project_world_host_if_idle() is True
