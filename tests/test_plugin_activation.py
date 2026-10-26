# -*- coding: utf-8 -*-
"""工程驱动插件按需激活（plugin_registry / sync_plugins_for_project）。"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _KernelStub:
    def __init__(self, project_root: str | None = None) -> None:
        self.plugin_loaded = _SignalStub()
        self.plugin_unloaded = _SignalStub()
        self.layout_manager = None
        self._project_root = project_root

    def get_context(self):
        ctx = MagicMock()
        ctx.project_root = self._project_root
        return ctx


class PluginActivationLogicTests(unittest.TestCase):
    def test_bootstrap_and_pvaec_mapping(self) -> None:
        from core.VitaLoom.project.plugin_activation import (
            collect_active_plugin_ids,
            get_bootstrap_plugin_ids,
        )

        repo_root = Path(__file__).resolve().parents[1]
        bootstrap = get_bootstrap_plugin_ids(repo_root)
        self.assertIn("StandardUIPlugin", bootstrap)
        self.assertNotIn("PsExperimentPlugin", bootstrap)

        project_data = {
            "required_packages": ["vitalloom.pvaec.simulation"],
            "capabilities": [],
            "disabled_plugins": [],
        }
        active = collect_active_plugin_ids(project_data, repo_root=repo_root)
        self.assertIn("PsExperimentPlugin", active)
        self.assertIn("StandardUIPlugin", active)

    def test_disabled_plugins_respected(self) -> None:
        from core.VitaLoom.project.plugin_activation import collect_active_plugin_ids

        repo_root = Path(__file__).resolve().parents[1]
        active = collect_active_plugin_ids(
            {
                "required_packages": ["vitalloom.pvaec.simulation"],
                "capabilities": [],
                "disabled_plugins": ["PsExperimentPlugin"],
            },
            repo_root=repo_root,
        )
        self.assertNotIn("PsExperimentPlugin", active)


class PluginLoaderActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._prev_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
        os.environ["VITALOOM_EAGER_PLUGINS"] = "0"

    def tearDown(self) -> None:
        if self._prev_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = self._prev_eager

    def _write_plugin(self, root: Path, filename: str, plugin_name: str) -> None:
        (root / filename).write_text(
            f"""
from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin

class {plugin_name}(IEditorPlugin):
    def get_plugin_info(self):
        return {{"name": "{plugin_name}", "version": "1.0", "provides": []}}

    def on_load(self, editor_context):
        pass

    def on_unload(self):
        pass
""".strip()
            + "\n",
            encoding="utf-8",
        )

    @patch(
        "core.VitaLoom.project.plugin_activation.get_bootstrap_plugin_ids",
        return_value={"BootstrapPlugin"},
    )
    def test_cold_start_only_bootstrap_plugins(self, _mock_bootstrap) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        repo_root = Path(__file__).resolve().parents[1]
        kernel = _KernelStub(project_root=str(repo_root))
        loader = PluginLoader(kernel)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "bootstrap_plugin.py", "BootstrapPlugin")
            self._write_plugin(root, "extra_plugin.py", "ExtraDemoPlugin")
            loader.load_from_directories([str(root)])

        self.assertIn("BootstrapPlugin", loader.loaded_plugins)
        self.assertIn("ExtraDemoPlugin", loader.plugin_registry)
        self.assertNotIn("ExtraDemoPlugin", loader.loaded_plugins)

    @patch(
        "core.VitaLoom.project.plugin_activation.get_bootstrap_plugin_ids",
        return_value={"BootstrapPlugin"},
    )
    def test_user_mod_is_source_not_auto_enabled_on_cold_start(self, _mock_bootstrap) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        repo_root = Path(__file__).resolve().parents[1]
        kernel = _KernelStub(project_root=str(repo_root))
        loader = PluginLoader(kernel)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            official = root / "official"
            user = root / "user"
            official.mkdir()
            user.mkdir()
            self._write_plugin(official, "bootstrap_plugin.py", "BootstrapPlugin")
            self._write_plugin(user, "workspace_tool_plugin.py", "WorkspaceToolPlugin")
            loader.load_from_layered_directories(
                {
                    "official_mod": [str(official)],
                    "user_mod": [str(user)],
                }
            )

        self.assertIn("BootstrapPlugin", loader.loaded_plugins)
        self.assertIn("WorkspaceToolPlugin", loader.plugin_registry)
        self.assertNotIn("WorkspaceToolPlugin", loader.loaded_plugins)

    @patch(
        "core.VitaLoom.project.plugin_activation.get_bootstrap_plugin_ids",
        return_value=set(),
    )
    @patch(
        "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
        return_value={"TargetPlugin"},
    )
    def test_sync_activates_and_unloads(self, _mock_collect, _mock_bootstrap) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        repo_root = Path(__file__).resolve().parents[1]
        kernel = _KernelStub(project_root=str(repo_root))
        loader = PluginLoader(kernel)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(root, "target_plugin.py", "TargetPlugin")
            self._write_plugin(root, "drop_plugin.py", "DropPlugin")
            loader.load_from_directories([str(root)])

        self.assertNotIn("TargetPlugin", loader.loaded_plugins)
        self.assertNotIn("DropPlugin", loader.loaded_plugins)

        loader.sync_plugins_for_project(
            {"required_packages": [], "capabilities": []},
            repo_root=repo_root,
        )

        self.assertIn("TargetPlugin", loader.loaded_plugins)
        self.assertNotIn("DropPlugin", loader.loaded_plugins)
        self.assertIn("DropPlugin", loader.plugin_registry)

    @patch(
        "core.VitaLoom.project.plugin_activation.get_bootstrap_plugin_ids",
        return_value=set(),
    )
    @patch(
        "core.VitaLoom.project.plugin_activation.collect_active_plugin_ids",
        return_value={"TargetPlugin"},
    )
    def test_project_sync_does_not_auto_enable_user_mod_sources(self, _mock_collect, _mock_bootstrap) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        repo_root = Path(__file__).resolve().parents[1]
        kernel = _KernelStub(project_root=str(repo_root))
        loader = PluginLoader(kernel)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            official = root / "official"
            user = root / "user"
            official.mkdir()
            user.mkdir()
            self._write_plugin(official, "target_plugin.py", "TargetPlugin")
            self._write_plugin(user, "workspace_tool_plugin.py", "WorkspaceToolPlugin")
            loader.load_from_layered_directories(
                {
                    "official_mod": [str(official)],
                    "user_mod": [str(user)],
                }
            )

        loader.sync_plugins_for_project(
            {"required_packages": [], "capabilities": []},
            repo_root=repo_root,
        )

        self.assertIn("TargetPlugin", loader.loaded_plugins)
        self.assertIn("WorkspaceToolPlugin", loader.plugin_registry)
        self.assertNotIn("WorkspaceToolPlugin", loader.loaded_plugins)


if __name__ == "__main__":
    unittest.main()
