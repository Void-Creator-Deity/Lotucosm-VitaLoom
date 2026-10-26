# -*- coding: utf-8 -*-
"""Suite Hub visual baseline independent from product runtime UI code."""
from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication, QStyleFactory

FONT_FAMILY = '"Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC", "SimSun", sans-serif'
FONT_SIZE_PT = 10


class Colors:
    BG_APP = "#0e1112"
    BG_SURFACE = "#15191b"
    BG_ELEVATED = "#1c2225"
    BG_INPUT = "#111517"
    BORDER = "#2a3236"
    BORDER_STRONG = "#39454a"
    BORDER_FOCUS = "#4aa89b"
    TEXT_PRIMARY = "#edf2f2"
    TEXT_SECONDARY = "#aab4b7"
    TEXT_MUTED = "#778287"
    ACCENT = "#3fa99a"
    ACCENT_HOVER = "#59c1b1"
    ACCENT_MUTED = "#173b37"
    WARNING = "#c7964d"
    DANGER = "#cf6464"
    SIDEBAR = "#111516"
    RADIUS_SM = "6px"
    RADIUS_MD = "9px"


def apply_app_baseline(app: QApplication) -> None:
    if "Fusion" in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create("Fusion"))
    available = set(QFontDatabase.families())
    preferred = [
        "Segoe UI",
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "Noto Sans CJK SC",
        "SimSun",
        "Arial",
    ]
    families = [name for name in preferred if not available or name in available]
    font = QFont()
    font.setFamilies(families or preferred)
    font.setPointSize(FONT_SIZE_PT)
    app.setFont(font)


def hub_stylesheet() -> str:
    c = Colors
    return f"""
    QWidget {{
        background-color: {c.BG_APP};
        color: {c.TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_PT}pt;
    }}
    QWidget#mainSurface {{
        background-color: {c.BG_APP};
    }}
    QFrame#sidebar {{
        background-color: {c.SIDEBAR};
        border-right: 1px solid {c.BORDER};
    }}
    QFrame#sidebarFooter {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_MD};
    }}
    QLabel#sidebarSection {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#sidebarFooterKey {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        background: transparent;
    }}
    QLabel#sidebarVersion {{
        color: {c.TEXT_SECONDARY};
        font-size: 10pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#vitaloomSidebarTitle {{
        font-size: 17pt;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#vitaloomPageTitle {{
        font-size: 22pt;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#vitaloomHint {{
        color: {c.TEXT_SECONDARY};
        font-size: 10pt;
        background: transparent;
    }}
    QLabel#vitaloomSubtle {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        background: transparent;
    }}
    QLabel#vitaloomStatus {{
        color: {c.TEXT_SECONDARY};
        font-size: 9pt;
        background: transparent;
    }}
    QLabel#listTitle {{
        color: {c.TEXT_PRIMARY};
        font-size: 11pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#projectCount {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        background: transparent;
        padding-left: 2px;
    }}
    QPushButton {{
        background-color: {c.BG_ELEVATED};
        border: 1px solid {c.BORDER_STRONG};
        border-radius: {c.RADIUS_SM};
        padding: 0 16px;
        color: {c.TEXT_PRIMARY};
        min-height: 38px;
        font-size: 10pt;
    }}
    QPushButton:hover {{
        background-color: #242c30;
        border-color: #4a575d;
    }}
    QPushButton:pressed {{
        background-color: {c.BG_INPUT};
    }}
    QPushButton:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QPushButton:disabled {{
        color: {c.TEXT_MUTED};
        background-color: #171b1d;
        border-color: {c.BORDER};
    }}
    QPushButton#primary {{
        background-color: #2d8277;
        border-color: #3fa99a;
        color: #f4fffc;
        font-weight: 600;
        padding: 0 22px;
    }}
    QPushButton#primary:hover {{
        background-color: #35978a;
        border-color: {c.ACCENT_HOVER};
    }}
    QPushButton#primary:disabled {{
        background-color: #1b3330;
        border-color: #274a45;
        color: #6f8d88;
    }}
    QPushButton#navActive {{
        background-color: {c.ACCENT_MUTED};
        border: 1px solid #24524c;
        color: #dff8f3;
        font-weight: 600;
        text-align: left;
        padding-left: 13px;
        min-height: 38px;
    }}
    QPushButton#navSecondary {{
        background-color: transparent;
        border: 1px solid transparent;
        color: {c.TEXT_SECONDARY};
        text-align: left;
        padding-left: 13px;
        min-height: 38px;
    }}
    QPushButton#navSecondary:hover {{
        background-color: #1a2022;
        border-color: {c.BORDER};
        color: {c.TEXT_PRIMARY};
    }}
    QToolButton {{
        background-color: {c.BG_ELEVATED};
        border: 1px solid {c.BORDER_STRONG};
        border-radius: {c.RADIUS_SM};
        padding: 0 15px;
        color: {c.TEXT_PRIMARY};
        min-height: 38px;
        font-size: 10pt;
    }}
    QToolButton:hover {{
        background-color: #242c30;
        border-color: #4a575d;
    }}
    QToolButton::menu-indicator {{
        image: none;
        width: 0;
    }}
    QMenu {{
        background-color: {c.BG_ELEVATED};
        border: 1px solid {c.BORDER_STRONG};
        border-radius: {c.RADIUS_SM};
        padding: 5px;
        color: {c.TEXT_PRIMARY};
    }}
    QMenu::item {{
        padding: 8px 18px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c.ACCENT_MUTED};
    }}
    QLineEdit {{
        background-color: {c.BG_INPUT};
        border: 1px solid {c.BORDER_STRONG};
        border-radius: {c.RADIUS_SM};
        padding: 0 12px;
        color: {c.TEXT_PRIMARY};
        min-height: 38px;
        selection-background-color: {c.ACCENT_MUTED};
    }}
    QLineEdit:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QLineEdit:disabled {{
        color: {c.TEXT_MUTED};
    }}
    QListWidget {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_MD};
        outline: none;
        padding: 5px;
    }}
    QListWidget::item {{
        padding: 2px;
        border: none;
    }}
    QListWidget::item:selected {{
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
    }}
    QListWidget::item:hover:!selected {{
        background-color: transparent;
    }}
    QFrame#projectRow {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: {c.RADIUS_MD};
    }}
    QFrame#projectRow:hover {{
        background-color: #192023;
        border-color: #2c373b;
    }}
    QFrame#projectRow[selected="true"] {{
        background-color: #19302d;
        border-color: #335f58;
    }}
    QFrame#projectRow[focused="true"] {{
        border-color: {c.BORDER_FOCUS};
    }}
    QLabel#projectTitle {{
        font-size: 11pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#projectDescription {{
        color: {c.TEXT_SECONDARY};
        font-size: 9pt;
        background: transparent;
    }}
    QLabel#rowStatus {{
        font-size: 9pt;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 8px;
        color: {c.TEXT_SECONDARY};
        background-color: #252c2f;
    }}
    QLabel#rowStatus[status="ok"] {{
        color: #bfe9e2;
        background-color: #1b3935;
    }}
    QLabel#rowStatus[status="warning"] {{
        color: #e8c997;
        background-color: #3a3020;
    }}
    QLabel#rowStatus[status="danger"] {{
        color: #efbaba;
        background-color: #3c2527;
    }}
    QFrame#projectDetailPanel {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_MD};
    }}
    QLabel#detailCaption {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#detailTitle {{
        font-size: 15pt;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#detailStatus {{
        font-size: 9pt;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 8px;
        color: {c.TEXT_SECONDARY};
        background-color: #252c2f;
    }}
    QLabel#detailStatus[status="ok"] {{
        color: #bfe9e2;
        background-color: #1b3935;
    }}
    QLabel#detailStatus[status="warning"] {{
        color: #e8c997;
        background-color: #3a3020;
    }}
    QLabel#detailStatus[status="danger"] {{
        color: #efbaba;
        background-color: #3c2527;
    }}
    QLabel#detailDesc {{
        color: {c.TEXT_SECONDARY};
        font-size: 10pt;
        background: transparent;
    }}
    QLabel#detailKey {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        background: transparent;
    }}
    QLabel#detailValue {{
        color: {c.TEXT_PRIMARY};
        font-size: 10pt;
        background: transparent;
    }}
    QFrame#divider {{
        background-color: {c.BORDER};
        border: none;
        max-height: 1px;
    }}
    QLabel#emptyTitle {{
        color: {c.TEXT_PRIMARY};
        font-size: 12pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#emptyHint {{
        color: {c.TEXT_MUTED};
        font-size: 9pt;
        background: transparent;
    }}
    QTableWidget {{
        background-color: {c.BG_SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_SM};
        gridline-color: {c.BORDER};
        color: {c.TEXT_PRIMARY};
        selection-background-color: {c.ACCENT_MUTED};
    }}
    QHeaderView::section {{
        background-color: {c.BG_ELEVATED};
        color: {c.TEXT_SECONDARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {c.BORDER};
        font-weight: 600;
    }}
    QTabWidget::pane {{
        border: 1px solid {c.BORDER};
        border-radius: {c.RADIUS_MD};
        background: {c.BG_SURFACE};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {c.BG_INPUT};
        color: {c.TEXT_SECONDARY};
        border: 1px solid {c.BORDER};
        border-bottom: none;
        border-top-left-radius: {c.RADIUS_SM};
        border-top-right-radius: {c.RADIUS_SM};
        padding: 8px 14px;
        margin-right: 4px;
    }}
    QTabBar::tab:selected {{
        background: {c.BG_SURFACE};
        color: {c.TEXT_PRIMARY};
        border-color: {c.BORDER_FOCUS};
    }}
    QDialog, QMessageBox {{
        background-color: {c.BG_APP};
        color: {c.TEXT_PRIMARY};
    }}
    QMessageBox QLabel {{
        color: {c.TEXT_PRIMARY};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #384247;
        border-radius: 4px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #4b585e;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    """
