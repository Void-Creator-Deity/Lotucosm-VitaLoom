# -*- coding: utf-8 -*-
"""VitaLoom 织机启动画面。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _find_splash_logo() -> Optional[Path]:
    """引擎级 Logo；不读取各 user project（如 PVAEC 演示）下的 branding。"""
    root = _repo_root()
    for rel in (
        "assets/branding/vitaloom_logo.png",
        "assets/branding/logo.png",
    ):
        p = root / rel
        if p.is_file():
            return p
    return None


_SPLASH_SUBTITLE = "莲池生命织机 · 场景与运行时编辑器"


def create_vitaloom_splash() -> QSplashScreen:
    """创建品牌启动图（520×320），可选叠加项目 Logo。"""
    w, h = 520, 320
    pix = QPixmap(w, h)
    pix.fill(QColor(10, 14, 24))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor(12, 18, 32))
    grad.setColorAt(0.5, QColor(18, 28, 48))
    grad.setColorAt(1.0, QColor(8, 12, 22))
    p.fillRect(0, 0, w, h, grad)

    logo_path = _find_splash_logo()
    if logo_path is not None:
        logo = QPixmap(str(logo_path))
        if not logo.isNull():
            scaled = logo.scaled(
                96,
                96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.drawPixmap(w - scaled.width() - 28, 36, scaled)

    p.setPen(QPen(QColor(80, 160, 220, 60), 2))
    for i in range(7):
        cx = 60 + i * 58
        cy = 200 + (i % 3) * 10
        p.drawEllipse(int(cx - 6), int(cy - 6), 12, 12)

    title_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
    p.setFont(title_font)
    p.setPen(QColor(190, 230, 255))
    p.drawText(36, 88, "VitaLoom")
    sub_font = QFont("Microsoft YaHei UI", 12)
    p.setFont(sub_font)
    p.setPen(QColor(150, 185, 225))
    p.drawText(38, 118, _SPLASH_SUBTITLE)
    p.setPen(QColor(110, 150, 190))
    p.drawText(38, h - 52, "加载插件与布局…")
    p.end()
    splash = QSplashScreen(pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    return splash


def show_vitaloom_splash(app: QApplication) -> Optional[QSplashScreen]:
    """显示启动画面；环境变量 VITALOOM_NO_SPLASH=1 时跳过。"""
    if os.environ.get("VITALOOM_NO_SPLASH", "").strip().lower() in ("1", "true", "yes"):
        return None
    splash = create_vitaloom_splash()
    splash.show()
    app.processEvents()
    return splash


def splash_message(splash: Optional[QSplashScreen], text: str, app: QApplication) -> None:
    if splash is None:
        return
    splash.showMessage(
        text,
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        QColor(160, 200, 240),
    )
    app.processEvents()


def finish_splash(splash: Optional[QSplashScreen], widget) -> None:
    if splash is None:
        return
    splash.finish(widget)
    QTimer.singleShot(0, splash.deleteLater)
