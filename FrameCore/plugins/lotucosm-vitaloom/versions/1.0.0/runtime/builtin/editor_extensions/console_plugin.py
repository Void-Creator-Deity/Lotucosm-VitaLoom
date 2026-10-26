# -*- coding: utf-8 -*-
"""Console Dock plugin and concrete legacy content Adapter lifecycle.

The portable Dock shell is declared through ``console.surface``.  Concrete
PyQt content, ``UI_CONSOLE_PANEL`` publication, and the logging handler remain
inside the current legacy Host Adapter path until a replacement Host proves
content parity.
"""
from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.VitaLoom.core.capability_publication import publish_capabilities
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.ui.logging_bridge import (
    attach_console_logging,
    detach_console_logging,
)


logger = get_logger("ConsolePlugin")


class ConsolePlugin(IRuntimePlugin):
    """Provide the Console shell and its current concrete PyQt content bridge."""

    DOCK_ID = "Console"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "ConsolePlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "控制台日志输出面板",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "console.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "console.title",
                    "default_title": "控制台",
                    "area": "bottom",
                    "default_visible": True,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": "Project",
                    "order": 60,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context) -> None:
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self.console_panel = None
        self._console_publication = None
        self._logging_handler = None
        self._event_subscriptions = []

        event_bus = getattr(editor_context, "event_bus", None)
        if event_bus is None:
            return
        try:
            event_bus.subscribe("language_changed", self._on_language_changed)
            self._event_subscriptions.append(
                (event_bus, "language_changed", self._on_language_changed)
            )
        except BaseException:
            self._release_event_subscriptions()
            raise

    def on_unload(self) -> None:
        release_error: BaseException | None = None
        try:
            self._release_console_adapter()
        except BaseException as error:
            release_error = error

        self._release_event_subscriptions()

        # A failed concrete-resource release keeps the panel alive so a later
        # unload attempt can retry without leaving a handler pointing at a
        # deleted QObject.
        if (
            getattr(self, "_logging_handler", None) is None
            and getattr(self, "_console_publication", None) is None
        ):
            dock = getattr(self, "dock", None)
            self.dock = None
            self.console_panel = None
            if dock is not None:
                dock.deleteLater()

        if release_error is not None:
            raise release_error

    def _release_event_subscriptions(self) -> None:
        subscriptions = list(getattr(self, "_event_subscriptions", ()))
        self._event_subscriptions = []
        failed = []
        for event_bus, event_name, callback in subscriptions:
            try:
                event_bus.unsubscribe(event_name, callback)
            except Exception as error:
                failed.append((event_bus, event_name, callback))
                logger.warning(
                    "Console event unsubscribe failed: event=%s error=%s",
                    event_name,
                    error,
                )
        self._event_subscriptions.extend(failed)

    def create_dock_widget(self) -> QDockWidget:
        """Create one concrete Console Dock and transactionally own its bridges."""

        # Repeated construction is replacement, not accumulation.  If release
        # fails the previous concrete resources remain intact and construction
        # aborts before a second panel is created.
        self._release_console_adapter()
        previous_dock = getattr(self, "dock", None)
        if previous_dock is not None:
            self.dock = None
            self.console_panel = None
            previous_dock.deleteLater()

        dock = QDockWidget()
        dock.setObjectName(self.DOCK_ID)
        panel = None
        try:
            panel, is_full_console = self._create_console_panel()
            dock.setWidget(panel)
            services = getattr(getattr(self, "context", None), "services", None)
            if is_full_console and services is not None:
                self._acquire_console_adapter(panel, services)
        except BaseException:
            if (
                getattr(self, "_logging_handler", None) is not None
                or getattr(self, "_console_publication", None) is not None
            ):
                # Rollback itself failed. Retain the exact concrete objects so
                # unload can retry instead of losing ownership evidence.
                self.dock = dock
                self.console_panel = panel
            else:
                dock.deleteLater()
                self.dock = None
                self.console_panel = None
            raise

        self.dock = dock
        self.console_panel = panel
        return dock

    def _create_console_panel(self) -> tuple[object, bool]:
        """Construct full Console content, preserving the legacy fallback UI."""

        try:
            from core.VitaLoom.ui.console import ConsolePanel

            return ConsolePanel(), True
        except Exception as error:
            logger.warning(
                "ConsolePanel load failed; using simplified panel: %s", error
            )
            from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

            widget = QWidget()
            layout = QVBoxLayout(widget)
            console_text = QTextEdit()
            console_text.setReadOnly(True)
            console_text.setPlaceholderText(
                self._t(
                    "console.placeholder",
                    "控制台输出会显示在这里……",
                )
            )
            layout.addWidget(console_text)
            return widget, False

    def _acquire_console_adapter(self, panel: object, services: object) -> None:
        publication = publish_capabilities(
            services,
            owner="adapter.console-panel",
            capabilities={UI_CONSOLE_PANEL: panel},
        )
        self._console_publication = publication
        try:
            handler = attach_console_logging(panel)
        except BaseException as attach_error:
            try:
                publication.release()
            except BaseException as rollback_error:
                logger.error(
                    "Console capability rollback failed after logging attach error: %s",
                    rollback_error,
                    exc_info=True,
                )
            else:
                self._console_publication = None
            raise attach_error

        self._logging_handler = handler

    def _release_console_adapter(self) -> None:
        """Release exact concrete resources in reverse order, with retry state."""

        first_error: BaseException | None = None

        handler = getattr(self, "_logging_handler", None)
        if handler is not None:
            try:
                detach_console_logging(handler)
            except BaseException as error:
                first_error = error
            else:
                # False means a later Console already replaced this exact
                # handler, so this plugin no longer owns an active root handler.
                self._logging_handler = None

        publication = getattr(self, "_console_publication", None)
        if publication is not None:
            try:
                publication.release()
            except BaseException as error:
                if first_error is None:
                    first_error = error
                else:
                    logger.error(
                        "Console capability release also failed: %s",
                        error,
                        exc_info=True,
                    )
            else:
                self._console_publication = None

        if first_error is not None:
            raise first_error


    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(getattr(self, "context", None), "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data=None) -> None:
        panel = getattr(self, "console_panel", None)
        retranslate = getattr(panel, "retranslate_ui", None)
        if callable(retranslate):
            retranslate()
