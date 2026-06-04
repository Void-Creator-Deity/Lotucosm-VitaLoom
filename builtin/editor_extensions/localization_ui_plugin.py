"""本地化 UI 插件：菜单栏语言切换（依赖 LocalizationPlugin）。

排错: 见 `builtin/README.md`。
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.plugin.interfaces import IMenuProvider
from core.VitaLoom.core.logger import get_logger

logger = get_logger("LocalizationUIPlugin")


class LocalizationUIPlugin(IMenuProvider):
    """菜单栏语言项；on_load 挂接 LocalizationPlugin 并发布 language_changed。"""

    def __init__(self):
        self.context = None
        self.kernel = None
        self._plugin_name = "LocalizationUI"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": self._plugin_name,
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "语言切换菜单插件",
            "dependencies": ["Localization"],
            "provides": ["menu"],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        if hasattr(self.context, "event_bus"):
            self.context.event_bus.subscribe("language_changed", self._on_language_changed)

    def on_unload(self):
        if hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.warning(
                    self._t(
                        "localization_ui.log.unsubscribe_failed",
                        "⚠️  LocalizationUI 取消语言订阅失败: {error}",
                    ).format(error=e)
                )

    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": f"{self._t('menu.tools', '工具')}/{self._t('menu.language', '语言')}/{self._t('menu.language.zh', '简体中文')}",
                "action": self.switch_language_zh,
            },
            {
                "path": f"{self._t('menu.tools', '工具')}/{self._t('menu.language', '语言')}/{self._t('menu.language.en', 'English')}",
                "action": self.switch_language_en,
            },
        ]

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        return []

    def switch_language_zh(self):
        self._set_lang("zh_CN")

    def switch_language_en(self):
        self._set_lang("en_US")

    def _set_lang(self, lang: str):
        set_lang = getattr(self.context, "i18n_set_language", None)
        if callable(set_lang):
            set_lang(lang)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        if not self.kernel or not hasattr(self.kernel, "layout_manager"):
            return
        lm = self.kernel.layout_manager
        if hasattr(lm, "remove_plugin_ui"):
            lm.remove_plugin_ui(self._plugin_name)
        lm.add_menu_items(self.get_menu_items(), self._plugin_name)
