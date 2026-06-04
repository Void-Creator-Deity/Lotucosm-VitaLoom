# -*- coding: utf-8 -*-
"""PluginLoader：单插件失败不拖垮整批加载。

职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock PluginLoader。
排错: 失败见 docs/comment_standard.md 与 core/VitaLoom/README.md。
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _KernelStub:
    def __init__(self) -> None:
        self.plugin_loaded = _SignalStub()
        self.layout_manager = None

    def get_context(self):
        return MagicMock()


class PluginLoaderFailureIsolationTests(unittest.TestCase):
    def _write_plugin(self, root: Path, name: str, body: str) -> None:
        (root / name).write_text(body.strip() + "\n", encoding="utf-8")

    def test_bad_plugin_does_not_prevent_good_plugin(self) -> None:
        from core.VitaLoom.kernel.plugin_loader import PluginLoader

        kernel = _KernelStub()
        loader = PluginLoader(kernel)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_plugin(
                root,
                "good_plugin.py",
                """
from core.plugin.interfaces import IEditorPlugin

class GoodPlugin(IEditorPlugin):
    def get_plugin_info(self):
        return {"name": "good_plugin", "version": "1.0", "provides": []}

    def on_load(self, editor_context):
        self.loaded = True

    def on_unload(self):
        self.loaded = False
""",
            )
            self._write_plugin(
                root,
                "bad_plugin.py",
                """
from core.plugin.interfaces import IEditorPlugin

class BadPlugin(IEditorPlugin):
    def get_plugin_info(self):
        return {"name": "bad_plugin", "version": "1.0", "provides": []}

    def on_load(self, editor_context):
        raise RuntimeError("boom")

    def on_unload(self):
        pass
""",
            )

            loader.load_from_directories([str(root)])

        self.assertIn("good_plugin", loader.loaded_plugins)
        self.assertIn("bad_plugin", loader.failed_plugins)
        self.assertIn("good_plugin", kernel.plugin_loaded.events)
        self.assertNotIn("bad_plugin", kernel.plugin_loaded.events)


if __name__ == "__main__":
    unittest.main()
