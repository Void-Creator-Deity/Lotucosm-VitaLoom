"""基于PyQt6的AI生命体编辑器 - 控制台模块"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ConsolePanel(QWidget):
    """控制台输出面板"""
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(200)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        self.layout = QVBoxLayout(self)
        
        # 标题和按钮栏
        header_layout = QHBoxLayout()
        
        # 标题
        self.title_label = QLabel("控制台")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        self.clear_button.clicked.connect(self.clear_console)
        header_layout.addWidget(self.clear_button)
        
        header_layout.addStretch()
        self.layout.addLayout(header_layout)
        
        # 分隔线
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.line.setStyleSheet("background-color: #404040;")
        self.layout.addWidget(self.line)
        
        # 控制台输出文本框
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.layout.addWidget(self.console_text)
        
        # 初始化控制台
        self.init_console()
    
    def init_console(self):
        """初始化控制台"""
        self.log("控制台已初始化", "info")
        self.log("AI生命体编辑器就绪", "success")
    
    def log(self, message, level="info"):
        """记录日志消息到控制台"""
        # 根据日志级别设置颜色
        colors = {
            "info": "#d4d4d4",
            "success": "#4ec9b0",
            "warning": "#ce9178",
            "error": "#f48771",
            "debug": "#9cdcfe"
        }
        color = colors.get(level, "#d4d4d4")
        
        # 格式化消息
        formatted_message = f"<span style='color: {color};'>[{level.upper()}] {message}</span><br>"
        
        # 添加到控制台
        self.console_text.insertHtml(formatted_message)
        
        # 滚动到底部
        self.console_text.verticalScrollBar().setValue(self.console_text.verticalScrollBar().maximum())
    
    def clear_console(self):
        """清空控制台"""
        self.console_text.clear()
        self.init_console()
    
    def append_text(self, text):
        """追加文本到控制台"""
        self.console_text.append(text)
        self.console_text.verticalScrollBar().setValue(self.console_text.verticalScrollBar().maximum())
