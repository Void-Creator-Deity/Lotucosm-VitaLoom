"""模拟控制 Dock：倍速预设与参数（Transport 已负责 play/stop，此处不重复）。"""

from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.plugin.interfaces import IDockProvider
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.simulation.simulation_control import SimulationControlPanel

logger = get_logger("SimulationControlPlugin")


class SimulationControlPlugin(IDockProvider):
    DOCK_ID = "SimulationControl"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "SimulationControl",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "模拟倍速与参数 Dock（Transport 驱动播放）",
            "dependencies": [],
            "provides": ["dock"],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.panel: SimulationControlPanel | None = None
        if hasattr(editor_context, "event_bus"):
            editor_context.event_bus.subscribe(
                "simulation_transport_state", self._on_transport_state
            )
            editor_context.event_bus.subscribe("language_changed", self._on_language_changed)

    def on_unload(self):
        if hasattr(self, "context") and self.context and hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe(
                    "simulation_transport_state", self._on_transport_state
                )
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception:
                pass

    def create_dock_widget(self) -> QDockWidget:
        dock = QDockWidget(self._t("sim_control.dock_title", "模拟"))
        dock.setObjectName(self.DOCK_ID)
        self.panel = SimulationControlPanel()
        dock.setWidget(self.panel)
        return dock

    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.LeftDockWidgetArea,
            "default_visible": False,
            "can_close": True,
            "tabbed_with": "Hierarchy",
        }

    def _on_transport_state(self, state) -> None:
        if not self.panel:
            return
        playing = bool(getattr(state, "is_playing", False))
        paused = bool(getattr(state, "is_paused", False))
        self.panel.play_btn.setEnabled(not playing or paused)
        self.panel.pause_btn.setEnabled(playing and not paused)
        self.panel.stop_btn.setEnabled(playing)
        if playing and not paused:
            self.panel._set_status(
                self.panel._t("sim_control.status.playing", "模拟运行中 · PVAEC 帧循环 + 世代编排")
            )
        elif playing and paused:
            self.panel._set_status(
                self.panel._t("sim_control.status.paused", "已暂停 · 可继续播放或停止")
            )

    def _on_language_changed(self, _data):
        if self.panel and hasattr(self.panel, "_t"):
            pass

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
