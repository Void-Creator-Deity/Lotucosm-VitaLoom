"""Inspector Dock 插件：选中对象属性编辑。

排错: 见 `builtin/README.md`（Dock 未出现）。
"""

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("InspectorPlugin")


class InspectorPlugin(IRuntimePlugin):
    """属性检视器 Dock：on_load 订阅选择事件，create_dock_widget 嵌入 Inspector 面板。"""
    
    DOCK_ID = "Inspector"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "InspectorPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "属性检视器，显示和编辑对象属性",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "inspector.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "inspector.title",
                    "default_title": "检视器",
                    "area": "right",
                    "default_visible": True,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 40,
                    "refresh_events": ["language_changed"],
                }
            ],
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self.inspector_panel = None
    
    def on_unload(self):
        if self.dock:
            self.dock.deleteLater()
    
    def create_dock_widget(self) -> QDockWidget:
        """创建 Inspector Dock 窗口"""
        self.dock = QDockWidget(self._t("inspector.title", "检视器"))
        self.dock.setObjectName(self.DOCK_ID)
        
        # 尝试复用现有的 InspectorPanel
        try:
            from core.VitaLoom.docks.inspector import InspectorPanel
            self.inspector_panel = InspectorPanel()
        except Exception as e:
            logger.warning("无法加载 InspectorPanel: %s", e)
            # 如果导入失败，创建一个简单的占位符
            from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
            widget = QWidget()
            layout = QVBoxLayout(widget)
            label = QLabel(self._t("inspector.placeholder", "选择场景中的对象以查看和编辑属性。"))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            self.inspector_panel = widget
        
        self.dock.setWidget(self.inspector_panel)
        return self.dock
    

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

