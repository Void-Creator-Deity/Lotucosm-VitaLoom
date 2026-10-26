"""已合并至 PackageManagerPlugin（插件管理器 Dock）。

保留本模块仅供旧测试导入 PluginRuntimeOpsMixin 相关行为；不再单独注册 Dock/菜单。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from builtin.editor_extensions.plugin_runtime_ops import PluginRuntimeOpsMixin
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PluginManagerPlugin")


class PluginManagerPlugin(PluginRuntimeOpsMixin):
    """兼容存根：运行时逻辑已并入 PackageManagerPlugin。"""

    DOCK_ID = "Plugin Manager"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PluginManagerPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "（已合并）请使用 PackageManagerPlugin / 工具→插件管理器",
            "dependencies": [],
            "provides": [],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.plugin_list: Optional[QListWidget] = None

    def on_unload(self):
        self.plugin_list = None

    @staticmethod
    def _public_observed_plugin_ids(snapshot: Mapping, field: str) -> set[str]:
        """Return displayable ids only from a documented non-string sequence."""
        values = snapshot.get(field)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            logger.warning("Plugin observation field is malformed; display omits it: %s", field)
            return set()
        return {str(plugin_id) for plugin_id in values}

    def _runtime_selected_plugin_id(self) -> Optional[str]:
        if not self.plugin_list:
            return None
        current_item = self.plugin_list.currentItem()
        if not current_item:
            return None
        role = current_item.data(Qt.ItemDataRole.UserRole)
        if role:
            return str(role)
        text = current_item.text().strip()
        return text.split()[0] if text else None

    def _runtime_refresh(self) -> None:
        self._refresh_plugin_list()

    def _refresh_plugin_list(self) -> None:
        """测试与旧脚本：展示 registry + 已加载状态。"""
        if not self.kernel or not self.plugin_list:
            return
        snapshot = self._runtime_plugin_observation()
        registry = self._public_observed_plugin_ids(snapshot, "plugin_ids")
        loaded = self._runtime_active_plugin_ids(snapshot)
        failed = self._public_observed_plugin_ids(snapshot, "failed_plugin_ids")
        self.plugin_list.clear()
        for plugin_name in sorted(registry):
            if loaded is None:
                status = self._runtime_t("plugin_manager.status.unknown", "[\u672a\u77e5]")
            elif plugin_name in loaded:
                status = self._runtime_t("plugin_manager.status.loaded", "[已加载]")
            elif plugin_name in failed:
                status = self._runtime_t("plugin_manager.status.failed", "[加载失败]")
            else:
                status = self._runtime_t("plugin_manager.status.inactive", "[未激活]")
            item = QListWidgetItem(f"{plugin_name}  {status}")
            item.setData(Qt.ItemDataRole.UserRole, plugin_name)
            self.plugin_list.addItem(item)
