# -*- coding: utf-8 -*-
"""示例插件：自定义视口（Qt-free IRuntimePlugin + 声明式 surface）。

职责: 声明式 viewport_surface + Adapter-local create_viewport_widget；可向 event_bus 发布 UI 事件。
时机: PluginLoader 加载后由 ViewportManager 注册切换。
排错: core/VitaLoom/README.md「视口不切换」；provides 须含 viewport。
"""

from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class CustomViewportPlugin(IRuntimePlugin):
    """自定义视口示例：演示与 CustomDock 事件联动。"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CustomViewportPlugin",
            "version": "1.0.0",
            "author": "Third Party Developer",
            "description": "一个自定义的视口示例，展示如何开发第三方视口插件",
            "dependencies": [],
            "provides": ["viewport", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "custom_viewport.surface",
                    "kind": "viewport_surface",
                    "viewport_id": "custom",
                    "name_key": "custom_viewport.title",
                    "default_name": "Custom View",
                    "order": 100,
                    "refresh_events": [],
                }
            ],
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.viewport = None
        self.counter = 0
        print("🎨 Custom Viewport Plugin loaded!")
    
    def on_unload(self):
        print("🎨 Custom Viewport Plugin unloaded!")
        if self.viewport:
            self.viewport.deleteLater()
    
    def create_viewport_widget(self) -> Any:
        """创建具体 Qt viewport payload；只在 LegacyEditorPluginAdapter 投影时导入 PyQt6。"""
        try:
            from PyQt6.QtCore import Qt
            from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "CustomViewportPlugin 的 Qt payload 需要 PyQt6；"
                "可在无 Qt 环境安全发现和读取 metadata。"
            ) from exc

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("🎨 Custom Viewport Example")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 描述
        description = QLabel(
            "This is an example of a third-party viewport plugin.\n"
            "You can create your own custom viewports\n"
            "by declaring a portable viewport surface on IRuntimePlugin."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(description)
        
        # 计数器标签
        self.counter_label = QLabel(f"Counter: {self.counter}")
        self.counter_label.setStyleSheet("font-size: 24px; margin: 20px;")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.counter_label)
        
        # 按钮
        button = QPushButton("Click Me!")
        button.clicked.connect(self.on_button_clicked)
        button.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(button)
        
        self.viewport = widget
        return widget
    
    def on_viewport_activated(self):
        """视口被激活时"""
        print("🎨 Custom viewport activated")
    
    def on_viewport_deactivated(self):
        """视口被停用时"""
        print("🎨 Custom viewport deactivated")
    
    def on_button_clicked(self):
        """按钮点击事件"""
        self.counter += 1
        self.counter_label.setText(f"Counter: {self.counter}")
        print(f"🎨 Button clicked! Counter: {self.counter}")
        
        # 发布自定义事件
        self.context.event_bus.publish("custom_button_clicked", {"count": self.counter})

