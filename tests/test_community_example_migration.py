"""Migration gate for community examples and the Headless plugin seam."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from FrameCore.project_lock import resolve_project_runtime


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = SUITE_ROOT / "versions" / "1.0.0"
RUNTIME_ROOT = VERSION_ROOT / "runtime"
COMMUNITY_ROOT = ROOT / "workspace" / "extensions" / "community"
LEGACY_FIXTURE_ROOT = (
    ROOT / "tests" / "fixtures" / "workspace" / "extensions" / "user"
)
PS_SAMPLE_ROOT = ROOT / "workspace" / "projects" / "samples" / "ps-基础生态实验"


class _Signal:
    def __init__(self) -> None:
        self.values: list[str] = []

    def emit(self, value: str) -> None:
        self.values.append(value)


class _Services:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def register(self, name: str, service: object) -> None:
        self.values[name] = service

    def get(self, name: str) -> object | None:
        return self.values.get(name)

    def unregister(self, name: str) -> None:
        self.values.pop(name, None)


class _LayoutManager:
    def process_pending_dock_tabify(self) -> None:
        return

    def remove_plugin_ui(self, _plugin_name: str) -> None:
        return


class _Context:
    def __init__(self) -> None:
        self.services = _Services()
        self.repo_root = str(ROOT)


class _Kernel:
    def __init__(self) -> None:
        self.context = _Context()
        self.layout_manager = _LayoutManager()
        self.plugin_loaded = _Signal()
        self.plugin_unloaded = _Signal()

    def get_context(self) -> _Context:
        return self.context


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "FRAMECORE_ROOT": str(ROOT / "FrameCore"),
            "VITALOOM_SUITE_ROOT": str(SUITE_ROOT),
            "VITALOOM_PRODUCT_VERSION_ROOT": str(VERSION_ROOT),
            "VITALOOM_APP_ROOT": str(ROOT),
            "PYTHONPATH": os.pathsep.join(
                (str(RUNTIME_ROOT), str(ROOT), env.get("PYTHONPATH", ""))
            ),
        }
    )
    return env


def test_plugin_interfaces_import_without_pyqt6() -> None:
    code = """
import sys
sys.modules['PyQt6'] = None
from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin, IDockProvider, IViewportProvider
assert IEditorPlugin.__name__ == 'IEditorPlugin'
assert IDockProvider.__name__ == 'IDockProvider'
assert IViewportProvider.__name__ == 'IViewportProvider'
print('headless-plugin-interface-ok')
"""
    proc = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=str(ROOT),
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "headless-plugin-interface-ok" in proc.stdout


def test_simulation_requires_pygame_only_for_window_mode(monkeypatch) -> None:
    from builtin.systems import simulation as simulation_module

    monkeypatch.setattr(simulation_module, "pygame", None)

    with pytest.raises(RuntimeError, match="pass enable_pygame=False"):
        simulation_module.Simulation()

    simulation = simulation_module.Simulation(enable_pygame=False)
    assert simulation.pygame_enabled is False
    assert simulation.font is None
    assert simulation.time == 0


def test_service_examples_load_headless_in_dependency_order(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_EAGER_PLUGINS", "1")
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    kernel = _Kernel()
    loader = PluginLoader(kernel)
    loader.load_from_layered_directories(
        {
            "user_mod": [
                str(COMMUNITY_ROOT / "example_service_consumer"),
                str(COMMUNITY_ROOT / "example_service_provider"),
            ]
        }
    )

    assert not loader.discovery_errors
    assert not loader.failed_plugins
    assert set(loader.loaded_plugins) == {
        "ExampleServiceProviderPlugin",
        "ExampleServiceConsumerPlugin",
    }
    assert loader.plugin_order.index("ExampleServiceProviderPlugin") < loader.plugin_order.index(
        "ExampleServiceConsumerPlugin"
    )
    assert kernel.context.services.get("example.time_service") is not None

    assert loader.unload_plugin("ExampleServiceConsumerPlugin")
    assert loader.unload_plugin("ExampleServiceProviderPlugin")
    assert kernel.context.services.get("example.time_service") is None


def _load_community_plugin(relative: str, class_name: str) -> type[object]:
    path = COMMUNITY_ROOT / relative
    module_name = f"e57_{path.stem}_{class_name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def test_community_examples_are_direct_runtime_plugins_without_legacy_ui_imports() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

    expected = {
        "example_service_provider/service_provider_plugin.py": "ExampleServiceProviderPlugin",
        "example_service_consumer/service_consumer_plugin.py": "ExampleServiceConsumerPlugin",
        "example_custom_dock/custom_dock_plugin.py": "CustomDockPlugin",
        "example_custom_viewport/custom_viewport_plugin.py": "CustomViewportPlugin",
    }
    actual = {
        path.relative_to(COMMUNITY_ROOT).as_posix()
        for path in COMMUNITY_ROOT.rglob("*_plugin.py")
    }
    assert set(expected) <= actual
    assert not (ROOT / "plugins").exists()
    assert not (ROOT / "examples").exists()

    violations: list[str] = []
    for relative, class_name in expected.items():
        text = (COMMUNITY_ROOT / relative).read_text(encoding="utf-8")
        for token in (
            "from core.VitaLoom.kernel.plugin_interfaces import",
            "core.plugin",
            "from lotucosm",
            "from vitalloom",
        ):
            if token in text:
                violations.append(f"{relative}: {token}")
        plugin_class = _load_community_plugin(relative, class_name)
        assert plugin_class.__bases__ == (IRuntimePlugin,)
    assert violations == []


def test_community_dock_and_viewport_samples_publish_parseable_surfaces() -> None:
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorDockSurfaceContribution,
        EditorViewportSurfaceContribution,
        parse_editor_contributions,
    )

    dock_plugin = _load_community_plugin(
        "example_custom_dock/custom_dock_plugin.py", "CustomDockPlugin"
    )()
    dock_info = dock_plugin.get_plugin_info()
    assert parse_editor_contributions(
        dock_info["name"], dock_info["editor_contributions"]
    ) == (
        EditorDockSurfaceContribution(
            owner_plugin_id="CustomDockPlugin",
            id="custom_dock.surface",
            kind="dock_surface",
            dock_id="custom_dock",
            title_key="custom_dock.title",
            default_title="Custom Panel",
            area="right",
            default_visible=True,
            can_close=True,
            can_float=True,
            can_move=True,
            tabbed_with=None,
            order=100,
            refresh_events=(),
        ),
    )

    viewport_plugin = _load_community_plugin(
        "example_custom_viewport/custom_viewport_plugin.py", "CustomViewportPlugin"
    )()
    viewport_info = viewport_plugin.get_plugin_info()
    assert parse_editor_contributions(
        viewport_info["name"], viewport_info["editor_contributions"]
    ) == (
        EditorViewportSurfaceContribution(
            owner_plugin_id="CustomViewportPlugin",
            id="custom_viewport.surface",
            kind="viewport_surface",
            viewport_id="custom",
            name_key="custom_viewport.title",
            default_name="Custom View",
            order=100,
            refresh_events=(),
        ),
    )


def test_official_author_docs_keep_the_qt_free_contract_explicit() -> None:
    community_readme = (COMMUNITY_ROOT / "README.md").read_text(encoding="utf-8")
    for sample in (
        "example_service_provider/",
        "example_service_consumer/",
        "example_custom_dock/",
        "example_custom_viewport/",
    ):
        row = next(line for line in community_readme.splitlines() if f"`{sample}`" in line)
        assert "`IRuntimePlugin`" in row
    assert "Host 复制的 JSON-safe 外壳事实" in community_readme
    assert "Adapter-local payload seam" in community_readme
    assert "not an official new-plugin template" in community_readme

    guide = (ROOT / "docs" / "guides" / "USER_GUIDE.md").read_text(encoding="utf-8")
    theme_section = guide.split("### 4. 主题插件", 1)[1].split("### 5. 实体类型插件", 1)[0]
    assert "from core.VitaLoom.kernel.plugin_interfaces import IThemeProvider" not in theme_section
    assert "class MyThemePlugin(IRuntimePlugin):" in theme_section
    assert '"kind": "theme_profile"' in theme_section
    assert "Adapter-local 的具体 PyQt payload seam" in theme_section
    assert "历史兼容导入，但不再是新主题插件的作者模板" in theme_section

def test_legacy_community_fixture_quarantine_stays_explicit() -> None:
    readme = LEGACY_FIXTURE_ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "compatibility-only regression surface" in text
    assert "not an official new-plugin template" in text

    expected = {
        "example_service_provider/service_provider_plugin.py": "IEditorPlugin",
        "example_service_consumer/service_consumer_plugin.py": "IEditorPlugin",
        "example_custom_dock/custom_dock_plugin.py": "IDockProvider",
        "example_custom_viewport/custom_viewport_plugin.py": "IViewportProvider",
    }
    for relative, legacy_base in expected.items():
        fixture = LEGACY_FIXTURE_ROOT / relative
        fixture_text = fixture.read_text(encoding="utf-8")
        assert "from core.VitaLoom.kernel.plugin_interfaces import" in fixture_text
        assert f"({legacy_base}):" in fixture_text

def test_ps_sample_project_lock_resolves() -> None:
    resolved = resolve_project_runtime(PS_SAMPLE_ROOT, repo_root=ROOT)
    assert resolved.product_id == "lotucosm-vitaloom"
    assert resolved.product_version == "1.0.0"
    assert not resolved.has_blocking_issues
    assert resolved.lock_status_text == "已锁定"


def test_ps_sample_tools_run_short_headless_smoke() -> None:
    commands = (
        [
            sys.executable,
            "-B",
            str(PS_SAMPLE_ROOT / "tools" / "component_ecosystem.py"),
            "--steps",
            "1",
            "--components",
            "2",
        ],
        [
            sys.executable,
            "-B",
            str(PS_SAMPLE_ROOT / "tools" / "ps_pacman_demo.py"),
            "--steps",
            "1",
            "--food-count",
            "2",
        ],
    )
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "step=000" in proc.stdout



