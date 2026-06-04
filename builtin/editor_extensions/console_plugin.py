"""控制台 Dock 插件：聚合运行时日志到可滚动面板。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.ui.logging_bridge import attach_console_logging, detach_console_logging

logger = get_logger("ConsolePlugin")


class ConsolePlugin(IDockProvider):
    """控制台插件 - 提供日志输出面板"""
    
    DOCK_ID = "Console"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Console",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "控制台日志输出面板",
            "dependencies": [],
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        if hasattr(editor_context, "event_bus"):
            editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_unload(self):
        detach_console_logging()
        if hasattr(self, "context") and self.context and hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception:
                pass
        if hasattr(self, "context") and self.context and hasattr(self.context, "services"):
            try:
                self.context.services.unregister("ui.console_panel")
            except Exception:
                pass
        if self.dock:
            self.dock.deleteLater()
    
    def create_dock_widget(self) -> QDockWidget:
        """创建控制台 Dock 窗口"""
        self.dock = QDockWidget(self._t("console.title", "控制台"))
        self.dock.setObjectName(self.DOCK_ID)
        
        # 尝试复用现有的 ConsolePanel
        try:
            from core.VitaLoom.ui.console import ConsolePanel
            console_panel = ConsolePanel()
        except Exception as e:
            logger.warning("ConsolePanel 加载失败，使用简化面板: %s", e)
            # 如果导入失败，创建一个简单的控制台
            from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout
            
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            console_text = QTextEdit()
            console_text.setReadOnly(True)
            console_text.setPlaceholderText(self._t("console.placeholder", "控制台输出会显示在这里..."))
            
            layout.addWidget(console_text)
            console_panel = widget
        
        self.dock.setWidget(console_panel)
        if hasattr(self, "context") and self.context and hasattr(self.context, "services"):
            try:
                from core.VitaLoom.ui.console import ConsolePanel as _ConsolePanelCls

                if isinstance(console_panel, _ConsolePanelCls):
                    self.context.services.register("ui.console_panel", console_panel)
                    attach_console_logging(console_panel)
            except Exception:
                pass
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.BottomDockWidgetArea,
            "default_visible": True,
            "can_close": True,
            "tabbed_with": "Project"
        }

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        if self.dock:
            self.dock.setWindowTitle(self._t("console.title", "控制台"))
