# -*- coding: utf-8 -*-
"""Legacy Editor Adapter shutdown cleanup and E52 command-authority boundary."""
from __future__ import annotations

from types import SimpleNamespace
import pytest


class _Plugin:
    def get_plugin_info(self):
        return {"name": "LegacyPlugin", "version": "1.0.0", "provides": []}

    def on_load(self, _context):
        return None

    def on_unload(self):
        return None


def _adapter():
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import LegacyEditorPluginAdapter

    kernel = SimpleNamespace(
        get_context=lambda: object(),
        plugin_loaded=SimpleNamespace(emit=lambda _plugin_id: None),
        plugin_unloaded=SimpleNamespace(emit=lambda _plugin_id: None),
    )
    return LegacyEditorPluginAdapter(kernel)


def test_dynamic_unload_and_shutdown_cleanup_are_both_strict() -> None:
    adapter = _adapter()
    plugin = _Plugin()
    info = plugin.get_plugin_info()

    with pytest.raises(AttributeError):
        adapter.before_plugin_unload(plugin, "LegacyPlugin", info)
    with pytest.raises(AttributeError):
        adapter.before_plugin_shutdown(plugin, "LegacyPlugin", info)


def test_adapter_exposes_no_post_unload_command_release_authority() -> None:
    adapter = _adapter()

    assert not hasattr(adapter, "after_plugin_unload_callback")
    assert not hasattr(adapter, "after_plugin_shutdown_callback")
