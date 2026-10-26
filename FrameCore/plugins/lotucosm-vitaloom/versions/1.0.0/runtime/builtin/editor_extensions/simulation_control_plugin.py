# -*- coding: utf-8 -*-
"""模拟控制 Dock：倍速预设与参数，播放权威仍由 SimulationTransport 持有。"""

from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.simulation.simulation_control import SimulationControlPanel

logger = get_logger("SimulationControlPlugin")


class SimulationControlPlugin(IRuntimePlugin):
    """L3 simulation-control extension projected by the Editor Host Adapter."""

    DOCK_ID = "SimulationControl"
    _PANEL_EVENTS = (
        "simulation_transport_state",
        "language_changed",
    )

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "SimulationControlPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "模拟倍速与参数 Dock；播放状态由 SimulationTransport 驱动",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "simulation_control.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "sim_control.dock_title",
                    "default_title": "模拟",
                    "area": "left",
                    "default_visible": False,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": "Hierarchy",
                    "order": 70,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context: Any) -> None:
        self.context = editor_context
        self.dock = None
        self.panel = None
        self._event_subscriptions: list[tuple[str, object]] = []

    def on_unload(self) -> None:
        errors = self._release_event_subscriptions()
        if not self._event_subscriptions:
            dock = getattr(self, "dock", None)
            if dock is not None:
                dock.deleteLater()
            self.dock = None
            self.panel = None
            self.context = None

        if errors:
            logger.warning(
                "SimulationControl 卸载未完全释放，保留精确状态供重试: %s",
                self._format_errors(errors),
            )
            raise errors[0]

    def create_dock_widget(self) -> QDockWidget:
        existing = getattr(self, "dock", None)
        if existing is not None:
            return existing

        dock = QDockWidget(self._t("sim_control.dock_title", "模拟"))
        dock.setObjectName(self.DOCK_ID)
        panel = SimulationControlPanel(editor_context=self.context)
        dock.setWidget(panel)
        self.dock = dock
        self.panel = panel

        try:
            self._acquire_event_subscriptions()
        except BaseException:
            rollback_errors = self._release_event_subscriptions()
            if rollback_errors:
                logger.warning(
                    "SimulationControl Panel 订阅回滚未完全释放，保留 Panel 供 unload 重试: %s",
                    self._format_errors(rollback_errors),
                )
            else:
                dock.deleteLater()
                self.dock = None
                self.panel = None
            raise
        return dock


    def _acquire_event_subscriptions(self) -> None:
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe):
            return

        callbacks = (
            ("simulation_transport_state", self._on_transport_state),
            ("language_changed", self._on_language_changed),
        )
        for event_name, callback in callbacks:
            subscribe(event_name, callback)
            self._event_subscriptions.append((event_name, callback))

    def _release_event_subscriptions(self) -> list[BaseException]:
        errors: list[BaseException] = []
        subscriptions = getattr(self, "_event_subscriptions", [])
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        unsubscribe = getattr(bus, "unsubscribe", None)

        if subscriptions and not callable(unsubscribe):
            return [RuntimeError("event_bus.unsubscribe is unavailable")]

        for index in range(len(subscriptions) - 1, -1, -1):
            event_name, callback = subscriptions[index]
            try:
                unsubscribe(event_name, callback)
            except BaseException as exc:
                errors.append(exc)
            else:
                subscriptions.pop(index)
        return errors

    def _on_transport_state(self, state: Any) -> None:
        panel = getattr(self, "panel", None)
        if panel is None:
            return
        playing = bool(getattr(state, "is_playing", False))
        paused = bool(getattr(state, "is_paused", False))
        panel.play_btn.setEnabled(not playing or paused)
        panel.pause_btn.setEnabled(playing and not paused)
        panel.stop_btn.setEnabled(playing)
        if playing and not paused:
            panel._set_status(
                panel._t(
                    "sim_control.status.playing",
                    "模拟运行中 · PVAEC 帧循环 + 世代编排",
                )
            )
        elif playing and paused:
            panel._set_status(
                panel._t(
                    "sim_control.status.paused",
                    "已暂停 · 可继续播放或停止",
                )
            )

    def _on_language_changed(self, _data: Any = None) -> None:
        panel = getattr(self, "panel", None)
        retranslate = getattr(panel, "retranslate_ui", None)
        if callable(retranslate):
            retranslate()

    @staticmethod
    def _format_errors(errors: list[BaseException]) -> str:
        return "; ".join(f"{type(exc).__name__}: {exc}" for exc in errors)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(getattr(self, "context", None), "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
