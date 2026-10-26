# -*- coding: utf-8 -*-
"""示例插件：自定义视口（IViewportProvider 模板）。

职责: create_viewport_widget + get_viewport_id；可向 event_bus 发布 UI 事件。
时机: PluginLoader 加载后由 ViewportManager 注册切换。
排错: core/VitaLoom/README.md「视口不切换」；provides 须含 viewport。
"""

from core.VitaLoom.kernel.plugin_interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from typing import Dict, Any


class CustomViewportPlugin(IViewportProvider):
    """自定义视口示例：演示与 CustomDock 事件联动。"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CustomViewport",
            "version": "1.0.0",
            "author": "Third Party Developer",
            "description": "一个自定义的视口示例，展示如何开发第三方视口插件",
            "dependencies": [],
            "provides": ["viewport"]
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
    
    def create_viewport_widget(self) -> QWidget:
        """创建自定义视口部件"""
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
            "by implementing the IViewportProvider interface."
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
    
    def get_viewport_id(self) -> str:
        return "custom"
    
    def get_viewport_name(self) -> str:
        return "Custom View"
    
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
