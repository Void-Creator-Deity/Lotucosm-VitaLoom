# -*- coding: utf-8 -*-
"""主题/QSS 切换：暗色默认与插件 ThemeProvider 注册。

排错: 样式未变 → LayoutManager.register_theme 是否被调用。
"""

from enum import Enum
from typing import Optional, Dict
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class ThemeType(Enum):
    """主题类型"""
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"


class ThemeManager(QObject):
    """职责: 应用全局 stylesheet 并缓存 ThemeType。"""
    """主题管理器单例"""
    
    _instance: Optional['ThemeManager'] = None
    theme_changed = pyqtSignal(str)  # Emits theme name
    
    # 深色主题样式
    DARK_THEME = """
        /* 主窗口 */
        QMainWindow {
            background-color: #1e1e1e;
            color: #cccccc;
        }
        
        /* 菜单栏 */
        QMenuBar {
            background-color: #2d2d30;
            color: #cccccc;
            border-bottom: 1px solid #3e3e42;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #3e3e42;
        }
        
        QMenuBar::item:pressed {
            background-color: #4a9eff;
        }
        
        /* 菜单 */
        QMenu {
            background-color: #252526;
            color: #cccccc;
            border: 1px solid #454545;
        }
        
        QMenu::item {
            padding: 4px 24px;
        }
        
        QMenu::item:selected {
            background-color: #094771;
        }
        
        /* 工具栏 */
        QToolBar {
            background-color: #2d2d30;
            border: none;
            spacing: 3px;
            padding: 3px;
        }
        
        QToolButton {
            background-color: transparent;
            color: #cccccc;
            border: none;
            padding: 5px;
            margin: 2px;
        }
        
        QToolButton:hover {
            background-color: #3e3e42;
        }
        
        QToolButton:pressed {
            background-color: #4a9eff;
        }
        
        /* 停靠面板 */
        QDockWidget {
            color: #cccccc;
        }
        
        QDockWidget::title {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #353540, stop:1 #2d2d30);
            padding: 7px 10px;
            border: 1px solid #3e3e42;
            font-weight: 600;
            color: #e0e0e0;
        }
        
        QDockWidget::close-button, QDockWidget::float-button {
            background-color: transparent;
            border: none;
            padding: 2px;
        }
        
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background-color: #3e3e42;
        }
        
        /* 树形视图 */
        QTreeWidget, QTreeView {
            background-color: #252526;
            color: #cccccc;
            border: 1px solid #3e3e42;
            selection-background-color: #094771;
            outline: none;
        }
        
        QTreeWidget::item, QTreeView::item {
            padding: 4px;
        }
        
        QTreeWidget::item:hover, QTreeView::item:hover {
            background-color: #2a2d2e;
        }
        
        QTreeWidget::item:selected, QTreeView::item:selected {
            background-color: #094771;
        }
        
        /* 列表视图 */
        QListWidget, QListView {
            background-color: #252526;
            color: #cccccc;
            border: 1px solid #3e3e42;
            selection-background-color: #094771;
            outline: none;
        }
        
        QListWidget::item, QListView::item {
            padding: 4px;
        }
        
        QListWidget::item:hover, QListView::item:hover {
            background-color: #2a2d2e;
        }
        
        QListWidget::item:selected, QListView::item:selected {
            background-color: #094771;
        }
        
        /* 标签页 */
        QTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }
        
        QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 6px 12px;
            border: 1px solid #3e3e42;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #252526;
            border-bottom: 2px solid #4a9eff;
        }
        
        QTabBar::tab:hover {
            background-color: #3e3e42;
        }
        
        /* 按钮 */
        QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 2px;
        }
        
        QPushButton:hover {
            background-color: #1177bb;
        }
        
        QPushButton:pressed {
            background-color: #094771;
        }
        
        QPushButton:disabled {
            background-color: #3e3e42;
            color: #656565;
        }
        
        /* 输入框 */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #3c3c3c;
            color: #cccccc;
            border: 1px solid #3e3e42;
            padding: 4px;
            selection-background-color: #094771;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid #4a9eff;
        }
        
        /* 滚动条 */
        QScrollBar:vertical {
            background-color: #1e1e1e;
            width: 14px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #424242;
            min-height: 20px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #4e4e4e;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #1e1e1e;
            height: 14px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #424242;
            min-width: 20px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #4e4e4e;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* 分组框 */
        QGroupBox {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            color: #cccccc;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
            color: #cccccc;
        }
        
        /* 状态栏 */
        QStatusBar {
            background-color: #4a9eff;
            color: #ffffff;
        }
        
        /* 分隔器 */
        QSplitter::handle {
            background-color: #3e3e42;
        }
        
        QSplitter::handle:hover {
            background-color: #4a9eff;
        }
        
        /* 复选框 */
        QCheckBox {
            color: #cccccc;
            spacing: 6px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #3e3e42;
            background-color: #3c3c3c;
        }
        
        QCheckBox::indicator:checked {
            background-color: #4a9eff;
            border-color: #4a9eff;
        }
        
        /* 单选按钮 */
        QRadioButton {
            color: #cccccc;
            spacing: 6px;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            background-color: #3c3c3c;
        }
        
        QRadioButton::indicator:checked {
            background-color: #4a9eff;
            border-color: #4a9eff;
        }
        
        /* 下拉框 */
        QComboBox {
            background-color: #3c3c3c;
            color: #cccccc;
            border: 1px solid #3e3e42;
            padding: 4px;
        }
        
        QComboBox:hover {
            border-color: #4a9eff;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #252526;
            color: #cccccc;
            selection-background-color: #094771;
            border: 1px solid #3e3e42;
        }
        
        /* 滑块 */
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #3e3e42;
            border-radius: 2px;
        }
        
        QSlider::handle:horizontal {
            background-color: #4a9eff;
            width: 12px;
            height: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #1177bb;
        }
        
        /* 进度条 */
        QProgressBar {
            background-color: #3c3c3c;
            border: 1px solid #3e3e42;
            border-radius: 2px;
            text-align: center;
            color: #cccccc;
        }
        
        QProgressBar::chunk {
            background-color: #4a9eff;
        }

        /* 弹窗 / 文件对话框（避免继承浅色字 + 白底） */
        QDialog, QMessageBox, QFileDialog, QInputDialog {
            background-color: #2d2d30;
            color: #e8e8e8;
        }
        QMessageBox QLabel, QDialog QLabel, QFileDialog QLabel, QInputDialog QLabel {
            color: #e8e8e8;
            background-color: transparent;
        }
        QDialogButtonBox QPushButton, QMessageBox QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            min-width: 72px;
            border-radius: 2px;
        }
        QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover {
            background-color: #1177bb;
        }

        /* VitaLoom 织机 · 模拟控制 / 控制台 */
        #simControlPanel QGroupBox#simControlGroup {
            font-weight: 600;
            margin-top: 10px;
        }
        #simControlStatus {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 6px;
        }
        #simControlStatusLabel {
            color: #9cdcfe;
            font-size: 12px;
        }
        QPushButton#simControlPlay {
            background-color: #0e7a0e;
            font-weight: bold;
            min-width: 76px;
        }
        QPushButton#simControlPlay:hover {
            background-color: #129612;
        }
        QPushButton#simControlSecondary {
            background-color: #3c3c3c;
            color: #cccccc;
        }
        QPushButton#simControlSecondary:hover {
            background-color: #4a4a4a;
        }
        QPushButton#simControlPreset {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 4px 10px;
            font-size: 11px;
            min-width: 36px;
        }
        QPushButton#simControlPreset:hover {
            background-color: #3e3e42;
        }
        #simControlHint {
            color: #858585;
            font-size: 11px;
            padding: 2px 4px;
        }
        #consolePanel {
            background-color: #1e1e1e;
        }
        #consolePanel QLabel#consoleTitle {
            color: #cccccc;
            font-size: 13px;
            font-weight: bold;
        }
        #consolePanel QTextEdit#consoleText {
            background-color: #1a1a1a;
            color: #d4d4d4;
            border: 1px solid #333333;
            border-radius: 4px;
            font-family: Consolas, 'Courier New', monospace;
            font-size: 12px;
        }
        QPushButton#consoleClearBtn {
            background-color: #3c3c3c;
            color: #cccccc;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 3px 10px;
            font-size: 11px;
        }
        QPushButton#consoleClearBtn:hover {
            background-color: #4c4c4c;
        }

        /* 游戏视口 · SR 模拟 HUD */
        #gameViewport {
            background-color: #0a0e16;
        }
        #gameViewportCanvas {
            background-color: #0a0e16;
            border: none;
        }
        #gameViewportHud {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e2838, stop:1 #141c28
            );
            border-bottom: 1px solid #3a5070;
        }
        #gameViewportHud QLabel#gameViewportHudLabel,
        #gameViewportHud QLabel#gameViewportSpeedValue {
            color: #a8c4e8;
            font-size: 12px;
            font-weight: 600;
        }
        #gameViewportHud QLabel#gameViewportHudStatus {
            color: #c8e4ff;
            font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
            font-size: 11px;
            padding: 2px 8px;
            background-color: rgba(20, 40, 70, 0.45);
            border: 1px solid #3a5880;
            border-radius: 6px;
        }
        #gameViewportHud QLabel#gameViewportHudHint {
            color: #7a9ab8;
            font-size: 11px;
            padding: 2px 4px;
        }
        QPushButton#gameViewportPlayBtn {
            background-color: #16803a;
            color: #f0fff4;
            border: 1px solid #1fa34a;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: bold;
            min-width: 72px;
        }
        QPushButton#gameViewportPlayBtn:hover {
            background-color: #1a9644;
        }
        QPushButton#gameViewportStopBtn {
            background-color: #4a3040;
            color: #ffd8e0;
            border: 1px solid #704058;
            border-radius: 6px;
            padding: 6px 14px;
            min-width: 64px;
        }
        QPushButton#gameViewportStopBtn:hover {
            background-color: #5c3a4c;
        }
        #gameViewportHud QSlider#gameViewportSpeedSlider::groove:horizontal {
            height: 6px;
            background-color: #2a3548;
            border-radius: 3px;
        }
        #gameViewportHud QSlider#gameViewportSpeedSlider::handle:horizontal {
            background-color: #6ec4ff;
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
            border: 1px solid #a8e0ff;
        }
        #gameViewportHud QSlider#gameViewportSpeedSlider::sub-page:horizontal {
            background-color: #2a6a9a;
            border-radius: 3px;
        }
    """
    
    # 浅色主题样式
    LIGHT_THEME = """
        /* 主窗口 */
        QMainWindow {
            background-color: #f3f3f3;
            color: #1e1e1e;
        }
        
        /* 菜单栏 */
        QMenuBar {
            background-color: #f3f3f3;
            color: #1e1e1e;
            border-bottom: 1px solid #d4d4d4;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #e5e5e5;
        }
        
        QMenuBar::item:pressed {
            background-color: #4a9eff;
            color: #ffffff;
        }
        
        /* 菜单 */
        QMenu {
            background-color: #ffffff;
            color: #1e1e1e;
            border: 1px solid #d4d4d4;
        }
        
        QMenu::item {
            padding: 4px 24px;
        }
        
        QMenu::item:selected {
            background-color: #e5e5e5;
        }
        
        /* 工具栏 */
        QToolBar {
            background-color: #f3f3f3;
            border: none;
            spacing: 3px;
            padding: 3px;
        }
        
        QToolButton {
            background-color: transparent;
            color: #1e1e1e;
            border: none;
            padding: 5px;
            margin: 2px;
        }
        
        QToolButton:hover {
            background-color: #e5e5e5;
        }
        
        QToolButton:pressed {
            background-color: #4a9eff;
            color: #ffffff;
        }
        
        /* 停靠面板 */
        QDockWidget {
            color: #1e1e1e;
        }
        
        QDockWidget::title {
            background-color: #f3f3f3;
            padding: 6px;
            border: 1px solid #d4d4d4;
        }
        
        QDockWidget::close-button, QDockWidget::float-button {
            background-color: transparent;
            border: none;
            padding: 2px;
        }
        
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {
            background-color: #e5e5e5;
        }
        
        /* 树形视图 */
        QTreeWidget, QTreeView {
            background-color: #ffffff;
            color: #1e1e1e;
            border: 1px solid #d4d4d4;
            selection-background-color: #cce8ff;
            outline: none;
        }
        
        QTreeWidget::item, QTreeView::item {
            padding: 4px;
        }
        
        QTreeWidget::item:hover, QTreeView::item:hover {
            background-color: #f3f3f3;
        }
        
        QTreeWidget::item:selected, QTreeView::item:selected {
            background-color: #cce8ff;
        }
        
        /* 列表视图 */
        QListWidget, QListView {
            background-color: #ffffff;
            color: #1e1e1e;
            border: 1px solid #d4d4d4;
            selection-background-color: #cce8ff;
            outline: none;
        }
        
        QListWidget::item, QListView::item {
            padding: 4px;
        }
        
        QListWidget::item:hover, QListView::item:hover {
            background-color: #f3f3f3;
        }
        
        QListWidget::item:selected, QListView::item:selected {
            background-color: #cce8ff;
        }
        
        /* 标签页 */
        QTabWidget::pane {
            border: 1px solid #d4d4d4;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f3f3f3;
            color: #1e1e1e;
            padding: 6px 12px;
            border: 1px solid #d4d4d4;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #4a9eff;
        }
        
        QTabBar::tab:hover {
            background-color: #e5e5e5;
        }
        
        /* 按钮 */
        QPushButton {
            background-color: #4a9eff;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            border-radius: 2px;
        }
        
        QPushButton:hover {
            background-color: #1177bb;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #d4d4d4;
            color: #a0a0a0;
        }
        
        /* 输入框 */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #1e1e1e;
            border: 1px solid #d4d4d4;
            padding: 4px;
            selection-background-color: #cce8ff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid #4a9eff;
        }
        
        /* 滚动条 */
        QScrollBar:vertical {
            background-color: #f3f3f3;
            width: 14px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c4c4c4;
            min-height: 20px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #f3f3f3;
            height: 14px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #c4c4c4;
            min-width: 20px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        /* 分组框 */
        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            color: #1e1e1e;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
            color: #1e1e1e;
        }
        
        /* 状态栏 */
        QStatusBar {
            background-color: #4a9eff;
            color: #ffffff;
        }
        
        /* 分隔器 */
        QSplitter::handle {
            background-color: #d4d4d4;
        }
        
        QSplitter::handle:hover {
            background-color: #4a9eff;
        }
        
        /* 复选框 */
        QCheckBox {
            color: #1e1e1e;
            spacing: 6px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #d4d4d4;
            background-color: #ffffff;
        }
        
        QCheckBox::indicator:checked {
            background-color: #4a9eff;
            border-color: #4a9eff;
        }
        
        /* 单选按钮 */
        QRadioButton {
            color: #1e1e1e;
            spacing: 6px;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #d4d4d4;
            border-radius: 8px;
            background-color: #ffffff;
        }
        
        QRadioButton::indicator:checked {
            background-color: #4a9eff;
            border-color: #4a9eff;
        }
        
        /* 下拉框 */
        QComboBox {
            background-color: #ffffff;
            color: #1e1e1e;
            border: 1px solid #d4d4d4;
            padding: 4px;
        }
        
        QComboBox:hover {
            border-color: #4a9eff;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #1e1e1e;
            selection-background-color: #cce8ff;
            border: 1px solid #d4d4d4;
        }
        
        /* 滑块 */
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #d4d4d4;
            border-radius: 2px;
        }
        
        QSlider::handle:horizontal {
            background-color: #4a9eff;
            width: 12px;
            height: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #1177bb;
        }
        
        /* 进度条 */
        QProgressBar {
            background-color: #ffffff;
            border: 1px solid #d4d4d4;
            border-radius: 2px;
            text-align: center;
            color: #1e1e1e;
        }
        
        QProgressBar::chunk {
            background-color: #4a9eff;
        }

        QDialog, QMessageBox, QFileDialog, QInputDialog {
            background-color: #ffffff;
            color: #1e1e1e;
        }
        QMessageBox QLabel, QDialog QLabel, QFileDialog QLabel, QInputDialog QLabel {
            color: #1e1e1e;
            background-color: transparent;
        }
        QDialogButtonBox QPushButton, QMessageBox QPushButton {
            background-color: #4a9eff;
            color: #ffffff;
            border: none;
            padding: 6px 16px;
            min-width: 72px;
            border-radius: 2px;
        }
    """
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ThemeManager.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        self.current_theme = ThemeType.DARK
        self.custom_themes: Dict[str, str] = {}
    
    def apply_theme(self, theme_type: ThemeType):
        """应用主题。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        app = QApplication.instance()
        if not app:
            return
        
        from core.VitaLoom.ui.design_tokens import apply_app_baseline, modern_editor_overlay

        apply_app_baseline(app)
        if theme_type == ThemeType.DARK:
            app.setStyleSheet(self.DARK_THEME + modern_editor_overlay())
        elif theme_type == ThemeType.LIGHT:
            app.setStyleSheet(self.LIGHT_THEME + modern_editor_overlay())
        
        self.current_theme = theme_type
        self.theme_changed.emit(theme_type.value)
    
    def register_custom_theme(self, name: str, stylesheet: str):
        """注册自定义主题。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.custom_themes[name] = stylesheet
    
    def apply_custom_theme(self, name: str):
        """应用自定义主题。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if name in self.custom_themes:
            app = QApplication.instance()
            if app:
                app.setStyleSheet(self.custom_themes[name])
                self.current_theme = ThemeType.CUSTOM
                self.theme_changed.emit(name)
    
    def get_current_theme(self) -> ThemeType:
        """获取当前主题。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.current_theme


def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例"""
    return ThemeManager()
