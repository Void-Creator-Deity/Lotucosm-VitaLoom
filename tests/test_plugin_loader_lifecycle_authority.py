# -*- coding: utf-8 -*-
"""PluginLoader as the concrete Adapter for Qt-free lifecycle authority."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _ContextStub:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = str(repo_root)
        self.project_root = str(repo_root)


class _KernelStub:
    def __init__(self, repo_root: Path) -> None:
        self.plugin_loaded = _SignalStub()
        self.plugin_unloaded = _SignalStub()
        self.layout_manager = None
        self._context = _ContextStub(repo_root)

    def get_context(self):
        return self._context


class _Plugin:
    def __init__(
        self,
        plugin_id: str,
        events: list[str],
        *,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.plugin_id = plugin_id
        self.dependencies = dependencies
        self.events = events

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": "1.0.0",
            "dependencies": list(self.dependencies),
            "provides": [],
        }

    def on_load(self, _context):
        self.events.append(f"load:{self.plugin_id}")

    def on_editor_ready(self):
        pass

    def on_unload(self):
        self.events.append(f"unload:{self.plugin_id}")


def _write_addon(
    project: Path,
    *,
    folder: str,
    plugin_id: str,
    dependencies: tuple[str, ...] = (),
    manifest_version: str = "1.0.0",
    code_version: str = "1.0.0",
) -> None:
    addon = project / "addons" / folder
    addon.mkdir(parents=True)
    entry = f"{folder}_plugin.py"
    class_name = plugin_id
    (addon / entry).write_text(
        f"""
from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin

class {class_name}(IEditorPlugin):
    def get_plugin_info(self):
        return {{
            "name": "{plugin_id}",
            "version": "{code_version}",
            "dependencies": {list(dependencies)!r},
            "provides": [],
        }}

    def on_load(self, editor_context):
        self.loaded = True

    def on_unload(self):
        self.loaded = False
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (addon / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": plugin_id,
                "version": manifest_version,
                "entry": entry,
                "runtime": {
                    "plugin_id": "lotucosm-vitaloom",
                    "version": ">=1.0.0,<2.0.0",
                },
                "dependencies": list(dependencies),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_failed_new_project_addon_discovery_preserves_previous_catalog_and_active_state(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    previous_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
    os.environ["VITALOOM_EAGER_PLUGINS"] = "0"
    try:
        loader = PluginLoader(_KernelStub(tmp_path))
        old_project = tmp_path / "old"
        old_project.mkdir()
        _write_addon(old_project, folder="old", plugin_id="OldPlugin")

        discovery = loader.scan_project_addons(old_project)
        assert discovery["status"] == "ready"
        with patch(
            "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
            return_value=set(),
        ):
            lifecycle = loader.sync_plugins_for_project({}, repo_root=tmp_path)
        assert lifecycle["status"] == "settled"
        assert "OldPlugin" in loader.loaded_plugins

        broken_project = tmp_path / "broken"
        broken_project.mkdir()
        _write_addon(
            broken_project,
            folder="broken",
            plugin_id="BrokenPlugin",
            manifest_version="1.0.0",
            code_version="2.0.0",
        )
        failed = loader.scan_project_addons(broken_project)
        assert failed["status"] == "blocked"
        assert failed["diagnostics"][0]["code"] == "addon_metadata_mismatch"
        assert "OldPlugin" in loader.plugin_registry
        assert "OldPlugin" in loader.loaded_plugins
        assert "BrokenPlugin" not in loader.plugin_registry
    finally:
        if previous_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = previous_eager


def test_sync_executes_reverse_dependency_deactivation_order(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    previous_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
    os.environ["VITALOOM_EAGER_PLUGINS"] = "0"
    try:
        events: list[str] = []
        loader = PluginLoader(_KernelStub(tmp_path))
        plugins = {
            "BasePlugin": _Plugin("BasePlugin", events),
            "MiddlePlugin": _Plugin(
                "MiddlePlugin", events, dependencies=("BasePlugin",)
            ),
            "LeafPlugin": _Plugin(
                "LeafPlugin", events, dependencies=("MiddlePlugin",)
            ),
        }
        loader.plugin_registry.update(plugins)
        loader.loaded_plugins.update(plugins)
        loader.plugin_dependencies.update(
            {
                "BasePlugin": [],
                "MiddlePlugin": ["BasePlugin"],
                "LeafPlugin": ["MiddlePlugin"],
            }
        )
        loader.plugin_scopes.update({name: loader.SCOPE_OFFICIAL for name in plugins})
        loader.plugin_files.update({name: f"/{name}.py" for name in plugins})

        with patch(
            "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
            return_value={"BasePlugin"},
        ):
            report = loader.sync_plugins_for_project({}, repo_root=tmp_path)

        assert report["status"] == "settled"
        assert report["completed"]["deactivated"] == ["LeafPlugin", "MiddlePlugin"]
        assert events == ["unload:LeafPlugin", "unload:MiddlePlugin"]
        assert set(loader.loaded_plugins) == {"BasePlugin"}
    finally:
        if previous_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = previous_eager


def test_missing_dependency_blocks_sync_without_partial_actions(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    previous_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
    os.environ["VITALOOM_EAGER_PLUGINS"] = "0"
    try:
        events: list[str] = []
        loader = PluginLoader(_KernelStub(tmp_path))
        existing = _Plugin("ExistingPlugin", events)
        broken = _Plugin("BrokenPlugin", events, dependencies=("MissingPlugin",))
        loader.plugin_registry.update(
            {"ExistingPlugin": existing, "BrokenPlugin": broken}
        )
        loader.loaded_plugins["ExistingPlugin"] = existing
        loader.plugin_dependencies.update(
            {"ExistingPlugin": [], "BrokenPlugin": ["MissingPlugin"]}
        )
        loader.plugin_scopes.update(
            {
                "ExistingPlugin": loader.SCOPE_OFFICIAL,
                "BrokenPlugin": loader.SCOPE_OFFICIAL,
            }
        )
        loader.plugin_files.update(
            {"ExistingPlugin": "/existing.py", "BrokenPlugin": "/broken.py"}
        )

        with patch(
            "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
            return_value={"BrokenPlugin"},
        ):
            report = loader.sync_plugins_for_project({}, repo_root=tmp_path)

        assert report["status"] == "blocked"
        assert report["diagnostics"][0]["code"] == "plugin_dependency_missing"
        assert list(loader.loaded_plugins) == ["ExistingPlugin"]
        assert events == []
    finally:
        if previous_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = previous_eager
