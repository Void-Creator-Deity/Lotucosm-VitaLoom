# -*- coding: utf-8 -*-
"""Plugins can contribute AI/CLI/MCP-visible commands through PluginLoader."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from core.VitaLoom.commands.registry import reset_command_registry


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _KernelStub:
    def __init__(self) -> None:
        self.plugin_loaded = _SignalStub()
        self.plugin_unloaded = _SignalStub()
        self.layout_manager = MagicMock()

    def get_context(self):
        return MagicMock()


class PluginCommandContributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()

    def test_loader_registers_and_unregisters_plugin_commands(self) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "command_plugin.py").write_text(
                """
from core.VitaLoom.commands.registry import CommandSpec, command_ok
from core.VitaLoom.kernel.plugin_interfaces import ICommandProvider, IEditorPlugin

class CommandPlugin(ICommandProvider, IEditorPlugin):
    def get_plugin_info(self):
        return {"name": "CommandPlugin", "version": "1.0.0", "provides": ["command"]}

    def on_load(self, editor_context):
        pass

    def on_unload(self):
        pass

    def get_command_specs(self):
        return [
            CommandSpec(
                id="fixture.plugin.echo",
                title="Fixture Echo",
                input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
                handler=lambda payload, context: command_ok({"echo": payload.get("text", "")}),
                owner="CommandPlugin",
                capability="fixture.command",
            )
        ]
""".strip()
                + "\n",
                encoding="utf-8",
            )

            loader = PluginLoader(_KernelStub())
            loader.load_from_directories([str(root)])

            result = self.registry.run("fixture.plugin.echo", {"text": "hi"})
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["result"]["echo"], "hi")

            self.assertTrue(loader.unload_plugin("CommandPlugin"))
            result = self.registry.run("fixture.plugin.echo", {"text": "hi"})
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "unknown_command")

    def test_builtin_package_commands_resolve_to_registry_capabilities(self) -> None:
        from core.VitaLoom.commands.registry import reset_command_registry
        from core.VitaLoom.core.bundle_paths import resource_root

        registry = reset_command_registry()
        catalog_path = resource_root() / "builtin" / "package_index.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        packages = [row for row in catalog.get("packages", []) if isinstance(row, dict)]
        package_ids = {str(row.get("id", "")).strip() for row in packages}
        command_ids = {
            str(command_id).strip()
            for row in packages
            for command_id in row.get("commands", [])
            if str(command_id).strip()
        }

        missing: list[str] = []
        invalid_capabilities: list[str] = []
        for command_id in sorted(command_ids):
            try:
                spec = registry.describe(command_id)
            except KeyError:
                missing.append(command_id)
                continue
            capability = str(spec.get("capability", "")).strip()
            if capability not in package_ids:
                invalid_capabilities.append(f"{command_id}:{capability}")

        self.assertEqual([], missing)
        self.assertEqual([], invalid_capabilities)


if __name__ == "__main__":
    unittest.main()
