"""细胞内部编辑视口：PS 组件图编辑（传感器/执行器/连接）。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("CellEditorPlugin")


class CellEditorPlugin(IViewportProvider):
    """细胞编辑器插件 - 细胞内部编辑视口"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CellEditor",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "细胞内部编辑视口，用于编辑细胞内组件和连接",
            "dependencies": [],
            "provides": ["viewport"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.viewport = None
        self._placeholder_label: QLabel | None = None
        self.current_cell = None
        
        # 订阅进入细胞编辑事件
        editor_context.event_bus.subscribe("enter_cell_edit", self.on_enter_cell_edit)
        editor_context.event_bus.subscribe("exit_cell_edit", self.on_exit_cell_edit)
        if hasattr(editor_context, "event_bus"):
            editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_unload(self):
        # 取消订阅
        self.context.event_bus.unsubscribe("enter_cell_edit", self.on_enter_cell_edit)
        self.context.event_bus.unsubscribe("exit_cell_edit", self.on_exit_cell_edit)
        if hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.debug("CellEditor 取消订阅失败: %s", e)
        
        if self.viewport:
            self.viewport.deleteLater()
    
    def create_viewport_widget(self) -> QWidget:
        """创建细胞编辑器视口部件"""
        # 创建一个简单的占位符
        # TODO: 未来可以实现完整的细胞内部编辑器
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(self._t(
            "cell_editor.placeholder",
            "细胞编辑视口\n\n"
            "在层级面板双击一个细胞以编辑其内部结构。\n"
            "你可以在这里添加传感器、执行器和连接。"
        ))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #888;")
        label.setWordWrap(True)
        
        layout.addWidget(label)
        self._placeholder_label = label
        self.viewport = widget
        
        return self.viewport
    
    def get_viewport_id(self) -> str:
        return "cell_editor"
    
    def get_viewport_name(self) -> str:
        return self._t("cell_editor.name", "细胞编辑")
    
    def on_viewport_activated(self):
        """细胞编辑器视口被激活"""
        logger.debug("🔬 %s", self._t('cell_editor.activated', '细胞编辑视口已激活'))
    
    def on_viewport_deactivated(self):
        """细胞编辑器视口被停用"""
        logger.debug("🔬 %s", self._t('cell_editor.deactivated', '细胞编辑视口已停用'))
    
    def on_enter_cell_edit(self, cell_data):
        """进入细胞编辑模式
        
        Args:
            cell_data: 细胞数据
        """
        self.current_cell = cell_data
        logger.info(self._t("cell_editor.entering", "🔬 进入细胞编辑模式：{cell}").format(cell=cell_data))
        self._refresh_placeholder_for_cell(cell_data)
        
        # 切换到细胞编辑器视口
        if hasattr(self.context, 'kernel') and self.context.kernel:
            self.context.kernel.layout_manager.switch_viewport("cell_editor")
        
        # TODO: 完整 PS 组件图编辑（传感器/执行器/连接画布）
    
    def _refresh_placeholder_for_cell(self, cell_data: Any) -> None:
        """在占位视口中显示当前细胞名称与类型（完整编辑器待实现）。"""
        if not self._placeholder_label:
            return
        name = ""
        entity_type = ""
        if isinstance(cell_data, dict):
            inner = cell_data.get("data") if isinstance(cell_data.get("data"), dict) else cell_data
            name = str(inner.get("entity_name") or inner.get("name") or inner.get("id") or "")
            entity_type = str(inner.get("type") or inner.get("entity_type") or "")
        title = name or self._t("cell_editor.unknown_cell", "未命名细胞")
        type_hint = f" ({entity_type})" if entity_type else ""
        self._placeholder_label.setText(
            self._t(
                "cell_editor.placeholder_active",
                "细胞编辑视口\n\n当前：{title}{type_hint}\n\n"
                "完整组件图编辑尚未实现；可在层级面板返回场景视图。",
            ).format(title=title, type_hint=type_hint)
        )

    def on_exit_cell_edit(self, data):
        """退出细胞编辑模式"""
        self.current_cell = None
        if self._placeholder_label:
            self._placeholder_label.setText(
                self._t(
                    "cell_editor.placeholder",
                    "细胞编辑视口\n\n"
                    "在层级面板双击一个细胞以编辑其内部结构。\n"
                    "你可以在这里添加传感器、执行器和连接。",
                )
            )
        logger.info("🔬 %s", self._t('cell_editor.exiting', '退出细胞编辑模式'))
        
        # 返回场景视图
        if hasattr(self.context, 'kernel') and self.context.kernel:
            self.context.kernel.layout_manager.switch_viewport("scene")

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        # 刷新标签页名称
        if self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            try:
                if getattr(lm, "viewport_tabs", None) and self.viewport:
                    tabs = lm.viewport_tabs
                    idx = tabs.indexOf(self.viewport)
                    if idx >= 0:
                        tabs.setTabText(idx, self.get_viewport_name())
            except Exception as e:
                logger.debug("刷新细胞编辑标签页标题失败: %s", e)
