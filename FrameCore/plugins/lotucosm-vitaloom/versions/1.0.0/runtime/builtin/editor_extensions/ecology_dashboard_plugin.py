# -*- coding: utf-8 -*-
"""生态统计 Dock：展示 ecology registry 聚合的 SR/PS 只读快照。"""
from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.logger import get_logger

logger = get_logger("EcologyDashboardPlugin")


class EcologyDashboardPlugin(IRuntimePlugin):
    """L3 ecology observation extension projected by the Editor Host Adapter."""

    DOCK_ID = "EcologyDashboard"
    _OBSERVATION_EVENTS = (
        "ps_experiment_state",
        "ps_experiment_finished",
        "simulation_transport_state",
    )

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "EcologyDashboardPlugin",
            "version": "1.0.0",
            "author": "Lotucosm",
            "description": "SR/PS 莲池生态只读统计",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "ecology_dashboard.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "ecology_dashboard.dock_title",
                    "default_title": "生态统计",
                    "area": "right",
                    "default_visible": False,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 90,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context: Any) -> None:
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self.panel = None
        self._event_subscriptions: list[tuple[str, object]] = []
        self._panel_timer_owned = False

    def on_unload(self) -> None:
        errors: list[BaseException] = []
        errors.extend(self._release_event_subscriptions())
        errors.extend(self._release_panel_timer())

        if self._all_exact_resources_released():
            dock = getattr(self, "dock", None)
            if dock is not None:
                dock.deleteLater()
            self.dock = None
            self.panel = None
            self.context = None
            self.kernel = None

        if errors:
            logger.warning(
                "EcologyDashboard 卸载未完全释放，保留精确状态供重试: %s",
                self._format_errors(errors),
            )
            raise errors[0]

    def create_dock_widget(self) -> QDockWidget:
        existing = getattr(self, "dock", None)
        if existing is not None:
            return existing

        dock = QDockWidget(self._t("ecology_dashboard.dock_title", "生态统计"))
        dock.setObjectName(self.DOCK_ID)
        try:
            from core.VitaLoom.docks.ecology_dashboard import EcologyDashboardPanel

            panel = EcologyDashboardPanel(self.context)
        except Exception as exc:
            logger.warning("无法加载 EcologyDashboardPanel: %s", exc)
            from PyQt6.QtWidgets import QLabel

            panel = QLabel("生态面板加载失败")

        dock.setWidget(panel)
        self.dock = dock
        self.panel = panel
        self._panel_timer_owned = callable(
            getattr(panel, "stop_refresh_timer", None)
        )

        try:
            self._acquire_event_subscriptions()
        except BaseException:
            rollback_errors: list[BaseException] = []
            rollback_errors.extend(self._release_event_subscriptions())
            rollback_errors.extend(self._release_panel_timer())
            if rollback_errors:
                logger.warning(
                    "EcologyDashboard 激活回滚未完全释放，保留 Panel 供 unload 重试: %s",
                    self._format_errors(rollback_errors),
                )
            else:
                dock.deleteLater()
                self.dock = None
                self.panel = None
            raise
        return dock


    def _acquire_event_subscriptions(self) -> None:
        panel = getattr(self, "panel", None)
        refresh = getattr(panel, "refresh", None)
        if not callable(refresh):
            return

        bus = getattr(getattr(self, "context", None), "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe):
            return

        refresh_callback = self._on_refresh_requested
        callbacks = tuple(
            (event_name, refresh_callback)
            for event_name in self._OBSERVATION_EVENTS
        ) + (("language_changed", self._on_language_changed),)
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

    def _release_panel_timer(self) -> list[BaseException]:
        if not bool(getattr(self, "_panel_timer_owned", False)):
            return []
        panel = getattr(self, "panel", None)
        stop_refresh_timer = getattr(panel, "stop_refresh_timer", None)
        if not callable(stop_refresh_timer):
            return [RuntimeError("EcologyDashboard Panel timer stop is unavailable")]
        try:
            stop_refresh_timer()
        except BaseException as exc:
            return [exc]
        self._panel_timer_owned = False
        return []

    def _all_exact_resources_released(self) -> bool:
        return (
            not getattr(self, "_event_subscriptions", [])
            and not bool(getattr(self, "_panel_timer_owned", False))
        )

    def _on_refresh_requested(self, _data: Any = None) -> None:
        panel = getattr(self, "panel", None)
        refresh = getattr(panel, "refresh", None)
        if callable(refresh):
            refresh()

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
