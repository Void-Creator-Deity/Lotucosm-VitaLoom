"""Unity Dark 主题插件：向 ThemeManager 注册 QSS 与色板。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IThemeProvider
from typing import Dict, Any


class UnityDarkThemePlugin(IThemeProvider):
    """Unity Dark 主题插件 - 提供 Unity 风格的深色主题"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "UnityDarkTheme",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "Unity 风格深色主题",
            "dependencies": [],
            "provides": ["theme"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        self.context = None
    
    def get_theme_name(self) -> str:
        return "Unity Dark"
    
    def get_stylesheet(self) -> str:
        return """
/* Unity Dark 主题 */
QMainWindow {
    background-color: #282828;
    color: #d0d0d0;
}

QMenuBar {
    background-color: #3c3c3c;
    color: #d0d0d0;
    border-bottom: 1px solid #202020;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 12px;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenu {
    background-color: #3c3c3c;
    color: #d0d0d0;
    border: 1px solid #202020;
}

QMenu::item:selected {
    background-color: #4a4a4a;
}

QToolBar {
    background-color: #3c3c3c;
    border-bottom: 1px solid #202020;
    spacing: 3px;
    padding: 4px;
}

QToolButton {
    background-color: transparent;
    color: #d0d0d0;
    border: none;
    padding: 5px;
    margin: 2px;
}

QToolButton:hover {
    background-color: #4a4a4a;
    border-radius: 2px;
}

QToolButton:pressed {
    background-color: #5a5a5a;
}

QDockWidget {
    background-color: #282828;
    color: #d0d0d0;
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(float.png);
}

QDockWidget::title {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #454545, stop:1 #383838);
    text-align: left;
    padding: 7px 10px;
    border-bottom: 1px solid #1a1a1a;
    font-weight: 600;
    color: #e8e8e8;
}

QTreeWidget, QListWidget {
    background-color: #252528;
    color: #e0e0e0;
    border: none;
    alternate-background-color: #2a2a2e;
    font-size: 12px;
}

QTreeWidget::item, QListWidget::item {
    padding: 5px 4px;
    border-radius: 3px;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #2a5a8a;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #3a3a3a;
}

QPushButton {
    background-color: #4a4a4a;
    color: #d0d0d0;
    border: 1px solid #202020;
    padding: 6px 12px;
    border-radius: 2px;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QPushButton:pressed {
    background-color: #6a6a6a;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2d2d2d;
    color: #d0d0d0;
    border: 1px solid #202020;
    padding: 4px;
    selection-background-color: #2a5a8a;
}

QLabel {
    color: #d0d0d0;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    min-height: 20px;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a5a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    min-width: 20px;
    border-radius: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5a5a5a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QTabWidget::pane {
    border: 1px solid #202020;
    background-color: #282828;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #d0d0d0;
    padding: 6px 12px;
    border: 1px solid #202020;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #282828;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}

QStatusBar {
    background-color: #3c3c3c;
    color: #d0d0d0;
    border-top: 1px solid #202020;
}
"""
    
    def get_color_scheme(self) -> Dict[str, str]:
        return {
            "background": "#282828",
            "menubar": "#3c3c3c",
            "text": "#d0d0d0",
            "border": "#202020",
            "highlight": "#2a5a8a",
            "hover": "#4a4a4a"
        }
