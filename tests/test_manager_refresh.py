# -*- coding: utf-8
"""包/插件管理器列表刷新与 language_changed 竞态。"""
from __future__ import annotations

import unittest

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from builtin.editor_extensions.plugin_manager_plugin import PluginManagerPlugin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PLUGIN_HOST_CONTROL_OBSERVATION


class _FakeListWidget:
    def __init__(self) -> None:
        self._items: list[str] = []

    def clear(self) -> None:
        self._items.clear()

    def addItem(self, item: QListWidgetItem) -> None:
        self._items.append(item.text())

    def count(self) -> int:
        return len(self._items)


class PackageManagerRefreshTests(unittest.TestCase):
    def test_language_changed_during_build_deferred(self):
        plugin = PackageManagerPlugin()
        plugin._ui_building = True
        plugin._pending_language_rebuild = False
        plugin._on_language_changed({})
        self.assertTrue(plugin._pending_language_rebuild)

    def test_project_plugins_synced_calls_refresh(self):
        plugin = PackageManagerPlugin()
        plugin._ensure_ui_refs = MagicMock(return_value=True)  # type: ignore[method-assign]
        plugin._refresh = MagicMock()  # type: ignore[method-assign]
        plugin._on_selection_changed = MagicMock()  # type: ignore[method-assign]
        plugin._capture_dock_floating_geometry = MagicMock()  # type: ignore[method-assign]
        plugin._on_project_plugins_synced({"project_path": "/tmp/demo"})
        plugin._refresh.assert_called_once()


class PluginManagerRefreshTests(unittest.TestCase):
    def test_lists_registry_with_loaded_marker(self):
        class PluginHostCapability:
            def observe_plugins(self):
                return {
                    "plugin_ids": ["AlphaPlugin", "BetaPlugin"],
                    "active_plugin_ids": ["AlphaPlugin"],
                    "failed_plugin_ids": [],
                }

            def reload_plugin(self, plugin_id):
                return {"status": "settled", "plugin_id": plugin_id}

            def unload_plugin(self, plugin_id):
                return {"status": "settled", "plugin_id": plugin_id}

            def scan_project_addons(self, project_path):
                return {"status": "settled", "project_path": str(project_path)}

            def sync_plugins_for_project(self, project_data, *, repo_root=None):
                return {"status": "settled"}

        services = InMemoryRuntimeCapabilityRegistry()
        services.register(PLUGIN_HOST_CONTROL_OBSERVATION, PluginHostCapability())
        plugin = PluginManagerPlugin()
        plugin.context = SimpleNamespace(
            services=services,
            i18n_tr=lambda k, d="": d or k,
        )
        plugin.kernel = object()
        plugin.plugin_list = _FakeListWidget()

        plugin._refresh_plugin_list()
        labels = plugin.plugin_list._items
        self.assertEqual(len(labels), 2)
        self.assertTrue(any("AlphaPlugin" in t and "已加载" in t for t in labels))
        self.assertTrue(any("BetaPlugin" in t and "未激活" in t for t in labels))


@pytest.mark.parametrize(
    ("snapshot", "expected_labels"),
    [
        (None, []),
        (
            {
                "plugin_ids": ["AlphaPlugin"],
                "active_plugin_ids": None,
                "failed_plugin_ids": [],
            },
            ["AlphaPlugin  RUNTIME_UNKNOWN"],
        ),
        (
            {
                "plugin_ids": ["AlphaPlugin"],
                "active_plugin_ids": "AlphaPlugin",
                "failed_plugin_ids": [],
            },
            ["AlphaPlugin  RUNTIME_UNKNOWN"],
        ),
        (
            {
                "plugin_ids": None,
                "active_plugin_ids": [],
                "failed_plugin_ids": [],
            },
            [],
        ),
        (
            {
                "plugin_ids": ["AlphaPlugin"],
                "active_plugin_ids": [],
                "failed_plugin_ids": None,
            },
            ["AlphaPlugin  RUNTIME_INACTIVE"],
        ),
    ],
    ids=[
        "non_mapping_snapshot",
        "none_active_ids",
        "string_active_ids",
        "none_registry_ids",
        "none_failed_ids",
    ],
)
def test_legacy_plugin_manager_display_treats_untrustworthy_active_ids_as_unknown(
    snapshot: object,
    expected_labels: list[str],
) -> None:
    """E81: legacy display reads use public facts only and never assert false state."""

    class PluginHostCapability:
        def __init__(self, public_snapshot: object) -> None:
            self.public_snapshot = public_snapshot
            self.reload_calls: list[str] = []
            self.unload_calls: list[str] = []

        def observe_plugins(self) -> object:
            return self.public_snapshot

        def reload_plugin(self, plugin_id: str) -> dict[str, str]:
            self.reload_calls.append(plugin_id)
            return {"status": "settled", "plugin_id": plugin_id}

        def unload_plugin(self, plugin_id: str) -> dict[str, str]:
            self.unload_calls.append(plugin_id)
            return {"status": "settled", "plugin_id": plugin_id}

        def scan_project_addons(self, project_path: object) -> dict[str, str]:
            return {"status": "settled", "project_path": str(project_path)}

        def sync_plugins_for_project(
            self, project_data: dict[str, object], *, repo_root: object | None = None
        ) -> dict[str, str]:
            return {"status": "settled"}

    host = PluginHostCapability(snapshot)
    services = InMemoryRuntimeCapabilityRegistry()
    services.register(PLUGIN_HOST_CONTROL_OBSERVATION, host)
    plugin = PluginManagerPlugin()
    plugin.context = SimpleNamespace(
        services=services,
        i18n_tr=lambda key, default="": {
            "plugin_manager.status.loaded": "RUNTIME_LOADED",
            "plugin_manager.status.failed": "RUNTIME_FAILED",
            "plugin_manager.status.inactive": "RUNTIME_INACTIVE",
            "plugin_manager.status.unknown": "RUNTIME_UNKNOWN",
        }.get(key, default),
    )
    plugin.kernel = object()
    plugin.plugin_list = _FakeListWidget()

    plugin._refresh_plugin_list()

    labels = plugin.plugin_list._items
    assert labels == expected_labels
    if expected_labels == ["AlphaPlugin  RUNTIME_UNKNOWN"]:
        assert "RUNTIME_LOADED" not in labels[0]
        assert "RUNTIME_INACTIVE" not in labels[0]
    assert host.reload_calls == []
    assert host.unload_calls == []


if __name__ == "__main__":
    unittest.main()
