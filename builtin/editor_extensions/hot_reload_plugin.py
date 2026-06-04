"""开发热重载插件：F5 重载 user_mod 插件，无需重启编辑器。

第一性原理：改插件代码 → 卸载 UI/订阅 → 从磁盘重新 import → 重新注册。
排错: 核心/protected 插件不可重载；失败见控制台 PluginLoader 日志。
"""

from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtWidgets import QInputDialog

from core.plugin.interfaces import IEditorPlugin, IMenuProvider
from core.VitaLoom.core.logger import get_logger

logger = get_logger("HotReloadPlugin")


class HotReloadPlugin(IEditorPlugin, IMenuProvider):
    """官方开发工具：菜单 + 快捷键触发热重载。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "HotReload",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "开发期插件热重载（F5）",
            "dependencies": [],
            "provides": ["menu"],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)

    def on_unload(self):
        self.context = None
        self.kernel = None

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _reloadable_plugins(self) -> list[str]:
        if not self.kernel:
            return []
        loader = self.kernel.plugin_loader
        names: list[str] = []
        for name in sorted(loader.loaded_plugins.keys()):
            if loader.is_plugin_protected(name):
                continue
            scope = loader.get_plugin_scope(name)
            if scope == loader.SCOPE_CORE:
                continue
            names.append(name)
        return names

    def reload_selected_plugin(self) -> None:
        """弹出列表，重载选中的非保护插件。"""
        if not self.kernel:
            return
        candidates = self._reloadable_plugins()
        if not candidates:
            logger.warning(self._t("hot_reload.none", "没有可热重载的插件"))
            return
        title = self._t("hot_reload.dialog.title", "热重载插件")
        label = self._t("hot_reload.dialog.prompt", "选择要重载的插件：")
        choice, ok = QInputDialog.getItem(
            self.kernel,
            title,
            label,
            candidates,
            0,
            False,
        )
        if not ok or not choice:
            return
        self._reload_plugin(str(choice))

    def reload_user_mod_plugins(self) -> None:
        """重载所有 user_mod 插件（plugins/ 目录）。"""
        if not self.kernel:
            return
        loader = self.kernel.plugin_loader
        targets = [
            name
            for name in self._reloadable_plugins()
            if loader.get_plugin_scope(name) == loader.SCOPE_USER
        ]
        if not targets:
            logger.info(self._t("hot_reload.no_user_mod", "未发现 user_mod 插件"))
            return
        ok_count = 0
        for name in targets:
            if self._reload_plugin(name):
                ok_count += 1
        logger.info(
            self._t("hot_reload.batch_done", "user_mod 热重载完成: {ok}/{total}").format(
                ok=ok_count,
                total=len(targets),
            )
        )

    def _reload_plugin(self, plugin_name: str) -> bool:
        if not self.kernel:
            return False
        logger.info(
            self._t("hot_reload.start", "正在热重载插件: {name}").format(name=plugin_name)
        )
        ok = bool(self.kernel.plugin_loader.reload_plugin(plugin_name))
        if ok:
            logger.info(
                self._t("hot_reload.ok", "热重载成功: {name}").format(name=plugin_name)
            )
        else:
            logger.warning(
                self._t("hot_reload.fail", "热重载失败: {name}").format(name=plugin_name)
            )
        return ok

    def get_menu_items(self) -> List[Dict[str, Any]]:
        dev = self._t("menu.develop", "开发")
        return [
            {
                "path": f"{dev}/{self._t('hot_reload.menu.one', '热重载插件…')}",
                "action": self.reload_selected_plugin,
                "shortcut": "F5",
            },
            {
                "path": f"{dev}/{self._t('hot_reload.menu.user_mod', '热重载全部 user_mod')}",
                "action": self.reload_user_mod_plugins,
                "shortcut": "Ctrl+Shift+F5",
            },
        ]
