"""本地化服务插件：加载 `locales/*.json` 并提供 translate API。

排错: 见 `builtin/README.md`。
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any

from core.plugin.interfaces import IEditorPlugin
from core.plugin.interfaces import IMenuProvider
from core.VitaLoom.core.logger import get_logger

logger = get_logger("LocalizationPlugin")


class LocalizationPlugin(IEditorPlugin):
    """加载 builtin 语言包并向 editor_context 注入 translate；on_load 注册服务。"""

    def __init__(self):
        self.context = None
        self.kernel = None
        self.language = "zh_CN"
        self.fallback: Dict[str, str] = {}
        self.messages: Dict[str, str] = {}
        self.locale_dir = os.path.join(os.path.dirname(__file__), "locales")

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Localization",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "语言包与翻译服务",
            "dependencies": [],
            "provides": [],
            "protected": True,
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.fallback = self._load_locale("en_US")
        self.messages = self._load_locale(self.language)

        setattr(self.context, "i18n_tr", self.tr)
        setattr(self.context, "i18n_set_language", self.set_language)
        setattr(self.context, "i18n_get_language", lambda: self.language)

    def on_unload(self):
        # 清理上下文挂载，避免热重载后引用旧函数
        if self.context:
            for attr in ("i18n_tr", "i18n_set_language", "i18n_get_language"):
                if hasattr(self.context, attr):
                    delattr(self.context, attr)

    def on_editor_ready(self):
        # editor ready 后通知一次语言状态，便于其他插件初始化文案
        if self.context and hasattr(self.context, "event_bus"):
            self.context.event_bus.publish("language_changed", {"language": self.language})

    def tr(self, key: str, default: str = "") -> str:
        return self.messages.get(key) or self.fallback.get(key) or default or key

    def set_language(self, language: str):
        if language == self.language:
            return
        self.language = language
        self.messages = self._load_locale(language)
        if self.context and hasattr(self.context, "event_bus"):
            self.context.event_bus.publish("language_changed", {"language": language})
        # 兜底刷新所有菜单提供者，避免语言事件漏订阅导致中英文菜单并存。
        self._refresh_all_menu_providers()

    def _refresh_all_menu_providers(self):
        if not self.kernel or not hasattr(self.kernel, "layout_manager"):
            return
        if not hasattr(self.kernel, "plugin_loader"):
            return
        lm = self.kernel.layout_manager
        loader = self.kernel.plugin_loader
        loaded_plugins = getattr(loader, "loaded_plugins", {})
        for plugin in loaded_plugins.values():
            if not isinstance(plugin, IMenuProvider):
                continue
            try:
                info = plugin.get_plugin_info()
                plugin_name = info.get("name")
                if plugin_name and hasattr(lm, "remove_plugin_ui"):
                    lm.remove_plugin_ui(plugin_name)
                lm.add_menu_items(plugin.get_menu_items(), plugin_name)
                lm.add_toolbar_items(plugin.get_toolbar_items(), plugin_name)
            except Exception:
                # 菜单刷新失败不应影响语言切换主流程
                continue

    def _load_locale(self, language: str) -> Dict[str, str]:
        path = os.path.join(self.locale_dir, f"{language}.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                return {str(k): str(v) for k, v in payload.items()}
        except Exception as e:
            logger.warning("Localization 语言包加载失败 %s: %s", language, e)
        return {}
