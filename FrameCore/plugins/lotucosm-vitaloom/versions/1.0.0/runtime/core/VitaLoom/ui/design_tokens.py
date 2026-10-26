# -*- coding: utf-8 -*-
"""设计令牌：Hub 与编辑器共享的现代暗色配色（Fusion + 圆角 + 统一字阶）。"""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QStyleFactory


FONT_FAMILY = '"Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "Noto Sans CJK SC", Arial, sans-serif'
FONT_SIZE_PT = 10


class Colors:
    BG_APP = "#101214"
    BG_SURFACE = "#171a1d"
    BG_ELEVATED = "#20252a"
    BG_INPUT = "#121518"
    BORDER = "#30363d"
    BORDER_FOCUS = "#4fb7a7"
    TEXT_PRIMARY = "#eef2f4"
    TEXT_SECONDARY = "#a7b0b8"
    TEXT_MUTED = "#6f7a83"
    ACCENT = "#42b7a8"
    ACCENT_HOVER = "#62d0c1"
    ACCENT_MUTED = "#183c39"
    SIDEBAR = "#131618"
    RADIUS_SM = "6px"
    RADIUS_MD = "8px"


def apply_app_baseline(app: QApplication) -> None:
    """Fusion 基底 + 系统字体，跨 Hub/编辑器一致。"""
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    available = set(QFontDatabase.families())
    preferred = [
        "Segoe UI",
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "SimSun",
        "Noto Sans CJK SC",
        "Arial",
    ]
    families = [name for name in preferred if not available or name in available]
    font = QFont()
    font.setFamilies(families or preferred)
    font.setPointSize(FONT_SIZE_PT)
    app.setFont(font)


def hub_stylesheet() -> str:
    """Hub 全应用 QSS（含 QMessageBox / QDialog）。"""
    c = Colors
    return f"""
    QWidget {{
        background-color: {c.BG_APP};
        color: {c.TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_PT}pt;
    }}
    QFrame#sidebar {{
        background-color: {c.SIDEBAR};
        border-right: 1px solid {c.BORDER};
    }}
    QLabel#vitaloomSidebarTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel#vitaloomPageTitle {{
        font-size: 18px;
        font-weight: 700;
    }}
    QLabel#vitaloomNavActive {{
        color: {c.ACCENT};
        font-weight: 600;
    }}
    QLabel#vitaloomHint {{
        color: {c.TEXT_SECONDARY};
        font-size: 11px;
    }}
    QLabel#vitaloomSubtle {{
        color: {c.TEXT_MUTED};
        font-size: 11px;
    }}
    QLabel#vitaloomStatus {{
        color: {c.ACCENT_HOVER};
        font-size: 11px;
    }}
    QPushButton {{
        background-color: {c.BG_ELEVATED};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_SM};
        padding: 8px 16px;
        color: {c.TEXT_PRIMARY};
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: #243040;
        border-color: #3d5068;
    }}
    QPushButton:pressed {{
        background-color: {c.BG_INPUT};
    }}
    QPushButton:disabled {{
        color: {c.TEXT_MUTED};
        background-color: {c.BG_SURFACE};
    }}
    QPushButton#primary {{
        background-color: #2a5a9a;
        border-color: {c.ACCENT};
        color: #f0f6ff;
        font-weight: 600;
    }}
    QPushButton#primary:hover {{
        background-color: #3568ad;
        border-color: {c.ACCENT_HOVER};
    }}
    QLineEdit {{
        background-color: {c.BG_INPUT};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_SM};
        padding: 8px 12px;
        color: {c.TEXT_PRIMARY};
        selection-background-color: {c.ACCENT_MUTED};
    }}
    QLineEdit:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QListWidget {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_MD};
        outline: none;
    }}
    QListWidget::item {{
        padding: 12px 14px;
        border-bottom: 1px solid #1a2430;
    }}
    QListWidget::item:selected {{
        background-color: {c.ACCENT_MUTED};
        color: {c.TEXT_PRIMARY};
    }}
    QListWidget::item:hover:!selected {{
        background-color: #1a2430;
    }}
    QTableWidget {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_SM};
        gridline-color: {c.BORDER};
        color: {c.TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: {c.BG_ELEVATED};
        color: {c.TEXT_SECONDARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {c.BORDER};
        font-weight: 600;
    }}
    QDialog, QMessageBox {{
        background-color: {c.BG_APP};
        color: {c.TEXT_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {c.TEXT_PRIMARY};
    }}
    QScrollBar:vertical {{
        background: {c.BG_APP};
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #3d4d62;
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #4d6078;
    }}
    QScrollBar:horizontal {{
        background: {c.BG_APP};
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: #3d4d62;
        border-radius: 5px;
        min-width: 28px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}
    """


def modern_editor_overlay() -> str:
    """叠加在编辑器全局 QSS 上的圆角/滚动条/焦点环补丁。"""
    c = Colors
    return f"""
    QMainWindow {{
        background-color: {c.BG_APP};
    }}
    QMenuBar, QToolBar {{
        background-color: {c.BG_SURFACE};
        border-bottom: 1px solid {c.BORDER};
        color: {c.TEXT_SECONDARY};
    }}
    QMenuBar::item {{
        padding: 6px 12px;
    }}
    QMenuBar::item:selected, QToolButton:hover {{
        background-color: {c.BG_ELEVATED};
        color: {c.TEXT_PRIMARY};
    }}
    QToolBar {{
        spacing: 4px;
        padding: 4px 6px;
    }}
    QToolButton {{
        border: 1px solid transparent;
        border-radius: {c.RADIUS_SM};
        padding: 5px 10px;
        color: {c.TEXT_SECONDARY};
    }}
    QToolButton:pressed {{
        background-color: {c.ACCENT_MUTED};
        border-color: {c.BORDER_FOCUS};
        color: {c.TEXT_PRIMARY};
    }}
    QStatusBar {{
        background-color: {c.BG_SURFACE};
        border-top: 1px solid {c.BORDER};
        color: {c.TEXT_SECONDARY};
        padding: 2px 8px;
    }}
    QWidget#editorPanel {{
        background-color: transparent;
    }}
    QLabel#editorPanelTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
    }}
    QFrame#editorPanelDivider {{
        background-color: {c.BORDER};
        max-height: 1px;
    }}
    QLabel#vitaloomHint {{
        color: {c.TEXT_SECONDARY};
        font-size: 11px;
    }}
    QPushButton {{
        border-radius: {c.RADIUS_SM};
        padding: 6px 14px;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        border-radius: {c.RADIUS_SM};
        padding: 6px 10px;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {c.BORDER_FOCUS};
    }}
    QTabBar::tab {{
        border-top-left-radius: {c.RADIUS_SM};
        border-top-right-radius: {c.RADIUS_SM};
        padding: 8px 16px;
    }}
    QScrollBar:vertical {{
        background: {c.BG_APP};
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #3d4d62;
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #4d6078;
    }}
    QScrollBar:horizontal {{
        background: {c.BG_APP};
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: #3d4d62;
        border-radius: 5px;
        min-width: 28px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}
    QToolTip {{
        background-color: {c.BG_ELEVATED};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 4px;
        padding: 6px 10px;
    }}
    """
