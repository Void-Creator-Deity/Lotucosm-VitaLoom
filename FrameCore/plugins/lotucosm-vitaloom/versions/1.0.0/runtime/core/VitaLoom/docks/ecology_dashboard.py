# -*- coding: utf-8 -*-
"""生态统计 Dock：经 ecology_registry 聚合 SR/PS 只读快照。

排错: 见 core/VitaLoom/README.md「生态面板」
"""
from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.simulation.ecology_registry import collect_ecology_snapshots
from core.Lotucosm.runtime.ecology_observation import EcologyLane
from core.Lotucosm.runtime.comparability import (
    comparability_dock_lines,
    should_show_comparability_dock,
)

logger = get_logger("EcologyDashboard")


class EcologyDashboardPanel(QWidget):
    """每 400ms 刷新各模拟轨道生态指标；事件刷新由插件精确拥有。"""

    def __init__(self, editor_context: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._ctx = editor_context
        self._labels: list[QLabel] = []
        layout = QVBoxLayout(self)
        self._title_label = QLabel(
            self._t(
                "ecology_dashboard.title",
                "莲池生态（SR 场景播放 + PS 批实验）",
            )
        )
        self._title_label.setStyleSheet("font-weight: bold; color: #c0d8ff;")
        layout.addWidget(self._title_label)
        self._hint_label = QLabel(
            self._t(
                "ecology_dashboard.hint",
                "SR 段：▶ 场景播放（GameViewport tick）。"
                "PS 段：演化实验 Dock 批处理（独立 tick；统一路线图见 docs/runtime_unification_roadmap.md）。",
            )
        )
        self._hint_label.setWordWrap(True)
        self._hint_label.setStyleSheet("color: #6a7a8a; font-size: 10px;")
        layout.addWidget(self._hint_label)
        for _ in range(30):
            lab = QLabel("—")
            lab.setStyleSheet(
                "color: #a8c0e0; font-family: Consolas, 'Microsoft YaHei', sans-serif; font-size: 11px;"
            )
            self._labels.append(lab)
            layout.addWidget(lab)
        layout.addStretch()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(400)

    def retranslate_ui(self) -> None:
        """Refresh retained static labels without replacing current ecology output."""
        self._title_label.setText(
            self._t(
                "ecology_dashboard.title",
                "莲池生态（SR 场景播放 + PS 批实验）",
            )
        )
        self._hint_label.setText(
            self._t(
                "ecology_dashboard.hint",
                "SR 段：▶ 场景播放（GameViewport tick）。"
                "PS 段：演化实验 Dock 批处理（独立 tick；统一路线图见 docs/runtime_unification_roadmap.md）。",
            )
        )

    def stop_refresh_timer(self) -> None:
        """Stop the retained polling timer; safe to call repeatedly."""
        self._timer.stop()

    def refresh(self) -> None:
        lines: list[str] = []
        try:
            snaps = collect_ecology_snapshots(self._ctx)
            sr_snap = next((s for s in snaps if s.lane == EcologyLane.SR_PLAY), None)
            ps_snap = next((s for s in snaps if s.lane == EcologyLane.PS_BATCH), None)
            for snap in snaps:
                if snap.lane == EcologyLane.PS_REPLAY:
                    continue
                lines.extend(snap.to_display_lines())
            if (
                sr_snap is not None
                and ps_snap is not None
                and should_show_comparability_dock(sr_snap, ps_snap)
            ):
                lines.extend(comparability_dock_lines(sr_snap, ps_snap))
        except Exception as exc:
            logger.debug("生态快照聚合失败: %s", exc)
            lines = [
                self._t(
                    "ecology_dashboard.data_unavailable",
                    "生态数据不可用",
                )
            ]
        for i, lab in enumerate(self._labels):
            lab.setText(lines[i] if i < len(lines) else "—")

    def _refresh(self) -> None:
        """Compatibility alias for existing diagnostics and tests."""
        self.refresh()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self._ctx, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
