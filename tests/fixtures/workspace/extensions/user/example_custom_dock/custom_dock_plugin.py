# -*- coding: utf-8 -*-
"""示例插件：自定义 Dock 面板（第三方 IDockProvider 模板）。

职责: 演示 create_dock_widget、事件总线订阅与 on_unload 清理。
时机: PluginLoader 扫描 plugins/ 后 on_load → LayoutManager 挂载 Dock。
排错: 见 docs/comment_standard.md；Dock 未显示 → VitaLoom README 插件表。
"""

from core.VitaLoom.kernel.plugin_interfaces import IDockProvider
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTextEdit, 
    QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt
from typing import Dict, Any


class CustomDockPlugin(IDockProvider):
    """自定义 Dock 示例：与 CustomViewport 通过 event_bus 联动。"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CustomDock",
            "version": "1.0.0",
            "author": "Third Party Developer",
            "description": "一个自定义的 Dock 面板示例，展示如何开发第三方面板插件",
            "dependencies": [],
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        """加载：订阅 custom_button_clicked，延迟创建 Dock 由 LayoutManager 拉取。

        排错: 无 Dock → get_plugin_info provides 含 dock；依赖 StandardUI 布局阶段。
        """
        self.context = editor_context
        self.dock = None
        self.text_edit = None
        
        # 订阅自定义按钮点击事件（由 CustomViewportPlugin 发布）
        editor_context.event_bus.subscribe("custom_button_clicked", self.on_custom_event)
        
        print("📝 Custom Dock Plugin loaded!")
    
    def on_unload(self):
        # 取消订阅
        self.context.event_bus.unsubscribe("custom_button_clicked", self.on_custom_event)
        
        print("📝 Custom Dock Plugin unloaded!")
        if self.dock:
            self.dock.deleteLater()
    
    def create_dock_widget(self) -> QDockWidget:
        """创建自定义 Dock 窗口"""
        self.dock = QDockWidget("My Custom Panel")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 标题
        title = QLabel("📝 Custom Dock Panel Example")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # 描述
        description = QLabel(
            "This panel demonstrates plugin-to-plugin communication\n"
            "via the event bus. Click the button in the Custom Viewport!"
        )
        description.setStyleSheet("font-size: 10px; color: #888; margin-bottom: 8px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Event log will appear here...")
        self.text_edit.append("✅ Custom Dock Plugin initialized")
        self.text_edit.append("📡 Listening for events from other plugins...")
        layout.addWidget(self.text_edit)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)
        
        test_btn = QPushButton("Send Test Event")
        test_btn.clicked.connect(self.send_test_event)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        self.dock.setWidget(widget)
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": "Custom Panel",
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": True,
            "can_close": True
        }
    
    def on_custom_event(self, data):
        """接收自定义事件
        
        Args:
            data: 事件数据
        """
        if self.text_edit:
            count = data.get("count", "?")
            self.text_edit.append(f"📨 Received event: Button clicked {count} times")
            print(f"📝 Custom Dock received event: {data}")
    
    def clear_log(self):
        """清空日志"""
        if self.text_edit:
            self.text_edit.clear()
            self.text_edit.append("🗑️ Log cleared")
    
    def send_test_event(self):
        """发送测试事件"""
        self.context.event_bus.publish("test_event", {"source": "CustomDock"})
        if self.text_edit:
            self.text_edit.append("📤 Sent test event to event bus")
