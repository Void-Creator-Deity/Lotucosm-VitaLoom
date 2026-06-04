# -*- coding: utf-8 -*-
"""SR 生态统计 Dock：定时拉取 `sr_game_viewport.get_sr_ecology_snapshot`。

排错: 见 core/VitaLoom/README.md「生态面板」
"""
from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.VitaLoom.core.logger import get_logger

logger = get_logger("EcologyDashboard")


class EcologyDashboardPanel(QWidget):
    """职责: 每 400ms 刷新 SR 模拟快照（人口、世代、能量、目标达成）。
    时机: Ecology Dock 插件创建后；依赖 editor_context.sr_game_viewport。
    不变量: 无 SR 视口时标签显示「—」，不抛异常到 UI。
    排错: 全「—」→ sr_game_viewport 未挂载或未开始模拟会话。
    """

    def __init__(self, editor_context: Any, parent: Optional[QWidget] = None):
        """EcologyDashboardPanel.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(parent)
        self._ctx = editor_context
        self._labels: list[QLabel] = []
        layout = QVBoxLayout(self)
        title = QLabel("莲池生态（SR 运行时）")
        title.setStyleSheet("font-weight: bold; color: #c0d8ff;")
        layout.addWidget(title)
        for _ in range(9):
            lab = QLabel("—")
            lab.setStyleSheet(
                "color: #a8c0e0; font-family: Consolas, 'Microsoft YaHei', sans-serif; font-size: 11px;"
            )
            self._labels.append(lab)
            layout.addWidget(lab)
        layout.addStretch()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(400)

    def _goals_status_text(self, snap: dict[str, Any]) -> str:
        sat = snap.get("play_goals_satisfied")
        if sat is None:
            return "无"
        return "已达" if sat else "未达"

    def _refresh(self) -> None:
        gv = getattr(self._ctx, "sr_game_viewport", None)
        snap: dict[str, Any] = {}
        try:
            if gv is not None and hasattr(gv, "get_sr_ecology_snapshot"):
                snap = gv.get_sr_ecology_snapshot()
        except Exception as exc:
            logger.debug("生态快照读取失败: %s", exc)
            snap = {}
        sim_running = bool(snap.get("sim_running"))
        tick_active = bool(snap.get("active"))
        lines = [
            f"模拟会话: {'进行中' if sim_running else '未开始'}（tick: {'运行' if tick_active else '暂停/停止'}）",
            f"暂停中: {'是' if snap.get('paused') else '否'}",
            f"模拟时间: {float(snap.get('sim_time', 0.0)):.1f} s",
            f"总人口（细胞）: {int(snap.get('population', 0))}",
            f"种群峰值: {int(snap.get('population_peak', 0))}",
            f"平均世代: {float(snap.get('avg_generation', 0.0)):.2f}",
            f"wander_amp 方差: {float(snap.get('wander_amp_variance', 0.0)):.3f}",
            f"总生物能量: {float(snap.get('total_energy', 0.0)):.1f}",
            f"演示目标: {self._goals_status_text(snap)}",
        ]
        for i, lab in enumerate(self._labels):
            lab.setText(lines[i] if i < len(lines) else "—")
