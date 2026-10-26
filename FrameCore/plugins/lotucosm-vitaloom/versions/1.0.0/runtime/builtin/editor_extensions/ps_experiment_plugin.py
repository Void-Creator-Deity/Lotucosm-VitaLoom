# -*- coding: utf-8 -*-
"""莲池 PS 演化实验 Dock 插件。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.VitaLoom.core.bundle_paths import application_root
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.capability_publication import publish_capabilities
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.service_keys import (
    PS_EXPERIMENT,
    PS_RUNTIME_SNAPSHOT_HOST,
)
from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService
from core.VitaLoom.simulation.ps_runtime_snapshot_host import (
    PsRuntimeSnapshotHostAdapter,
)

logger = get_logger("PsExperimentPlugin")


def _resolve_application_root(editor_context: Any) -> Path:
    """Resolve the Project World root without assuming the plugin's install path."""
    for attribute in ("application_root", "repo_root"):
        raw = getattr(editor_context, attribute, None)
        if raw:
            return Path(raw).resolve()
    return application_root()


class PsExperimentPlugin(IRuntimePlugin):
    """L3 PsExperiment extension projected by the existing Editor Host Adapter."""

    DOCK_ID = "PsExperiment"
    _PANEL_EVENTS = (
        "project_opened",
        "ps_experiment_finished",
        "ps_experiment_config_changed",
        "language_changed",
    )

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PsExperimentPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "莲池 PS 演化实验：编辑器内运行 PVAEC + 世代编排",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "ps_experiment.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "ps_experiment.dock_title",
                    "default_title": "莲池演化实验",
                    "area": "right",
                    "default_visible": False,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": "EcologyDashboard",
                    "order": 80,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context: Any) -> None:
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self._panel = None
        self._panel_event_subscriptions: list[tuple[str, object]] = []
        self._service = None
        self._runtime_snapshot_host = None
        self._service_publication = None
        self._service_bound = False

        service = PsExperimentService(_resolve_application_root(editor_context))
        self._service = service
        try:
            service.bind_editor_context(editor_context)
            self._service_bound = True
            runtime_snapshot_host = PsRuntimeSnapshotHostAdapter(service)
            self._runtime_snapshot_host = runtime_snapshot_host
            self._service_publication = publish_capabilities(
                editor_context.services,
                owner="adapter.ps-experiment",
                capabilities={
                    PS_EXPERIMENT: service,
                    PS_RUNTIME_SNAPSHOT_HOST: runtime_snapshot_host,
                },
            )
        except BaseException:
            rollback_errors = self._release_activation_resources()
            self._clear_service_references_if_released()
            if rollback_errors:
                logger.warning(
                    "PsExperiment 激活回滚未完全释放，保留精确状态供 unload 重试: %s",
                    self._format_errors(rollback_errors),
                )
            raise
        logger.info("PsExperimentService 与 PS Runtime Snapshot Host 已注册")

    def on_unload(self) -> None:
        errors: list[BaseException] = []
        service = getattr(self, "_service", None)
        if service is not None and bool(getattr(service, "is_running", False)):
            request_cancel = getattr(service, "request_cancel", None)
            if callable(request_cancel):
                try:
                    request_cancel()
                except BaseException as exc:
                    errors.append(exc)

        errors.extend(self._release_panel_event_subscriptions())
        errors.extend(self._release_service_publication())
        errors.extend(self._release_service_binding())
        self._clear_service_references_if_released()

        if self._all_exact_resources_released():
            dock = getattr(self, "dock", None)
            if dock is not None:
                dock.deleteLater()
            self.dock = None
            self._panel = None
            self.context = None
            self.kernel = None

        if errors:
            logger.warning(
                "PsExperiment 卸载未完全释放，保留精确状态供重试: %s",
                self._format_errors(errors),
            )
            raise errors[0]

    def create_dock_widget(self) -> QDockWidget:
        existing = getattr(self, "dock", None)
        if existing is not None:
            return existing

        dock = QDockWidget(self._t("ps_experiment.dock_title", "莲池演化实验"))
        dock.setObjectName(self.DOCK_ID)
        try:
            from core.VitaLoom.docks.ps_experiment_panel import PsExperimentPanel

            panel = PsExperimentPanel(self.context)
        except Exception as exc:
            logger.warning("无法加载 PsExperimentPanel: %s", exc)
            from PyQt6.QtWidgets import QLabel

            panel = QLabel("莲池演化实验面板加载失败")

        dock.setWidget(panel)
        self.dock = dock
        self._panel = panel
        try:
            self._acquire_panel_event_subscriptions(panel)
        except BaseException:
            rollback_errors = self._release_panel_event_subscriptions()
            if rollback_errors:
                logger.warning(
                    "PsExperiment Panel 订阅回滚未完全释放，保留 Panel 供 unload 重试: %s",
                    self._format_errors(rollback_errors),
                )
            else:
                dock.deleteLater()
                self.dock = None
                self._panel = None
            raise
        return dock


    def _acquire_panel_event_subscriptions(self, panel: object) -> None:
        bus = getattr(self.context, "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe):
            return
        callbacks = (
            ("project_opened", getattr(panel, "_on_project_opened", None)),
            (
                "ps_experiment_finished",
                getattr(panel, "_on_experiment_finished", None),
            ),
            (
                "ps_experiment_config_changed",
                getattr(panel, "_on_config_changed", None),
            ),
            ("language_changed", self._on_language_changed),
        )
        for event_name, callback in callbacks:
            if not callable(callback):
                continue
            subscribe(event_name, callback)
            self._panel_event_subscriptions.append((event_name, callback))

    def _release_panel_event_subscriptions(self) -> list[BaseException]:
        errors: list[BaseException] = []
        subscriptions = getattr(self, "_panel_event_subscriptions", [])
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        unsubscribe = getattr(bus, "unsubscribe", None)
        for index in range(len(subscriptions) - 1, -1, -1):
            event_name, callback = subscriptions[index]
            try:
                if callable(unsubscribe):
                    unsubscribe(event_name, callback)
            except BaseException as exc:
                errors.append(exc)
            else:
                subscriptions.pop(index)
        return errors

    def _release_service_publication(self) -> list[BaseException]:
        publication = getattr(self, "_service_publication", None)
        if publication is None:
            return []
        try:
            publication.release()
        except BaseException as exc:
            return [exc]
        self._service_publication = None
        return []

    def _release_service_binding(self) -> list[BaseException]:
        if not bool(getattr(self, "_service_bound", False)):
            return []
        service = getattr(self, "_service", None)
        unbind = getattr(service, "unbind_editor_context", None)
        try:
            if callable(unbind):
                unbind()
        except BaseException as exc:
            return [exc]
        self._service_bound = False
        return []

    def _release_activation_resources(self) -> list[BaseException]:
        errors: list[BaseException] = []
        errors.extend(self._release_service_publication())
        errors.extend(self._release_service_binding())
        return errors

    def _clear_service_references_if_released(self) -> None:
        if getattr(self, "_service_publication", None) is not None:
            return
        if bool(getattr(self, "_service_bound", False)):
            return
        self._runtime_snapshot_host = None
        self._service = None

    def _all_exact_resources_released(self) -> bool:
        return (
            not getattr(self, "_panel_event_subscriptions", [])
            and getattr(self, "_service_publication", None) is None
            and not bool(getattr(self, "_service_bound", False))
        )

    def _on_language_changed(self, _data: Any = None) -> None:
        panel = getattr(self, "_panel", None)
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