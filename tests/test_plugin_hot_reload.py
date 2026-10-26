"""PluginLoader.reload_plugin：从磁盘重新加载非保护插件。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PLUGIN_SOURCE = '''
from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin
from typing import Dict, Any

class DummyHotReloadPlugin(IEditorPlugin):
    MARKER = {marker}

    def get_plugin_info(self) -> Dict[str, Any]:
        return {{
            "name": "DummyHotReload",
            "version": "1.0.0",
            "author": "test",
            "description": "hot reload test",
            "dependencies": [],
            "provides": [],
        }}

    def on_load(self, editor_context):
        pass

    def on_unload(self):
        pass
'''


class PluginHotReloadTests(unittest.TestCase):
    def test_reload_plugin_picks_up_file_changes(self):
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        kernel = MagicMock()
        kernel.get_context.return_value = MagicMock()
        kernel.plugin_loaded = MagicMock()
        kernel.plugin_unloaded = MagicMock()
        loader = PluginLoader(kernel)

        with tempfile.TemporaryDirectory() as tmp:
            plugin_path = Path(tmp) / "dummy_hot_reload_plugin.py"
            plugin_path.write_text(PLUGIN_SOURCE.format(marker=1), encoding="utf-8")
            loader._discover_plugin(plugin_path, loader.SCOPE_USER)
            plugin_id = "DummyHotReloadPlugin"
            self.assertIn(plugin_id, loader.plugin_registry)
            loader._resolve_dependencies()
            loader._activate_plugins_matching({plugin_id})
            first = loader.loaded_plugins[plugin_id]
            self.assertEqual(first.MARKER, 1)

            plugin_path.write_text(PLUGIN_SOURCE.format(marker=2), encoding="utf-8")
            report = loader.reload_plugin(plugin_id)
            self.assertEqual(report["status"], "settled")
            self.assertTrue(report["completed"]["registry_replaced"])
            second = loader.loaded_plugins[plugin_id]
            self.assertEqual(second.MARKER, 2)
            self.assertIsNot(first, second)


if __name__ == "__main__":
    unittest.main()
