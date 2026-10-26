# -*- coding: utf-8 -*-
"""GameViewport plugin: declarative shell plus retained legacy SR content bridge.

The ``viewport_surface`` contribution is the stable shell Interface. The
current PyQt GameViewport remains a concrete legacy Host Adapter/content bridge
and owns SimulationTransport, SR snapshots, selected identity, rendering,
input, and playback behavior.
"""
from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtWidgets import QWidget

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

logger = get_logger("GameViewportPlugin")


class GameViewportPlugin(IRuntimePlugin):
    """Project one Game viewport shell while retaining the current SR content."""

    VIEWPORT_ID = "game"
    _EVENT_BINDINGS = (
        ("simulation_play", "on_play"),
        ("simulation_pause", "on_pause"),
        ("simulation_stop", "on_stop"),
        ("language_changed", "_on_language_changed"),
    )

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "GameViewportPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "\u6e38\u620f\u8fd0\u884c\u89c6\u53e3\uff0c\u7528\u4e8e\u8fd0\u884c\u548c\u89c2\u5bdf\u6a21\u62df",
            "dependencies": [],
            "provides": ["viewport", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "game.surface",
                    "kind": "viewport_surface",
                    "viewport_id": self.VIEWPORT_ID,
                    "name_key": "game_viewport.name",
                    "default_name": "\u6e38\u620f",
                    "order": 20,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context) -> None:
        """Retain the activation context; content creation owns event acquisition."""
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.viewport: QWidget | None = None
        self._event_subscriptions: list[tuple[str, object]] = []
        self._runtime_capabilities_active = False

    def prepare_host_teardown(self) -> None:
        """Release callbacks and capabilities before the Host removes the surface."""
        errors = self._release_event_subscriptions()
        capability_error = self._release_runtime_capabilities()
        if capability_error is not None:
            errors.append(capability_error)
        if errors:
            raise errors[0]

    def on_unload(self) -> None:
        """Finish staged teardown without competing with LayoutManager deletion."""
        self.prepare_host_teardown()
        self.viewport = None

    def create_viewport_widget(self) -> QWidget:
        """Create and retain the current concrete GameViewport exactly once."""
        existing = getattr(self, "viewport", None)
        if existing is not None:
            return existing

        widget: QWidget
        try:
            from core.VitaLoom.viewports.game_viewport import GameViewport

            widget = GameViewport()
            if hasattr(widget, "editor_context") and getattr(self, "context", None):
                widget.editor_context = self.context
            register = getattr(widget, "register_as_sr_host", None)
            if callable(register):
                register()
                self._runtime_capabilities_active = True
            logger.info("GameViewport created")
        except Exception as error:
            logger.exception("Unable to load GameViewport: %s", error)
            widget = self._create_placeholder_widget()

        self.viewport = widget
        try:
            self._acquire_event_subscriptions()
        except BaseException:
            rollback_errors = self._release_event_subscriptions()
            capability_error = self._release_runtime_capabilities()
            if capability_error is not None:
                rollback_errors.append(capability_error)
            if rollback_errors:
                logger.warning(
                    "GameViewport activation rollback retained content for unload retry: %s",
                    self._format_errors(rollback_errors),
                )
            else:
                widget.deleteLater()
                self.viewport = None
            raise
        return widget

    def _create_placeholder_widget(self) -> QWidget:
        try:
            from PyQt6.QtCore import Qt
            from PyQt6.QtWidgets import QLabel, QVBoxLayout

            widget = QWidget()
            layout = QVBoxLayout(widget)
            label = QLabel(
                self._t(
                    "game_viewport.placeholder",
                    "\u6e38\u620f\u89c6\u53e3\n\n\u70b9\u51fb\u201c\u8fd0\u884c\u201d\u540e\u6a21\u62df\u5c06\u5728\u8fd9\u91cc\u6267\u884c\u3002",
                )
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 14px; color: #888;")
            layout.addWidget(label)
            logger.info("GameViewport placeholder created")
            return widget
        except Exception as error:
            logger.warning("Unable to create GameViewport placeholder: %s", error)
            return QWidget()

    def get_viewport_id(self) -> str:
        return self.VIEWPORT_ID

    def get_viewport_name(self) -> str:
        return self._t("game_viewport.name", "\u6e38\u620f")

    def on_viewport_activated(self) -> None:
        logger.debug(
            "%s", self._t("game_viewport.activated", "\u6e38\u620f\u89c6\u53e3\u5df2\u6fc0\u6d3b")
        )

    def on_viewport_deactivated(self) -> None:
        logger.debug(
            "%s", self._t("game_viewport.deactivated", "\u6e38\u620f\u89c6\u53e3\u5df2\u505c\u7528")
        )

    def _is_real_game_viewport(self) -> bool:
        if not getattr(self, "viewport", None):
            return False
        try:
            from core.VitaLoom.viewports.game_viewport import GameViewport

            return isinstance(self.viewport, GameViewport)
        except Exception as error:
            logger.warning("GameViewport type check failed: %s", error)
            return False

    def on_play(self, _data=None) -> None:
        """Forward ``simulation_play`` to the concrete retained viewport."""
        try:
            if not self.viewport:
                logger.warning("GameViewport is not initialized")
                return
            if not self._is_real_game_viewport():
                logger.warning("Current viewport is not a GameViewport")
                return
            start = getattr(self.viewport, "start_simulation", None)
            if callable(start):
                start()
                logger.info(
                    "%s",
                    self._t(
                        "game_viewport.simulation.starting",
                        "\u6b63\u5728\u542f\u52a8\u6a21\u62df...",
                    ),
                )
            else:
                logger.warning("GameViewport has no start_simulation method")
        except Exception as error:
            logger.exception("Failed to start simulation: %s", error)

    def on_pause(self, _data=None) -> None:
        try:
            if not self.viewport:
                logger.warning("GameViewport is not initialized")
                return
            if not self._is_real_game_viewport():
                logger.warning("Current viewport is not a GameViewport")
                return
            pause = getattr(self.viewport, "pause_simulation", None)
            if callable(pause):
                pause()
                logger.info(
                    "%s",
                    self._t(
                        "game_viewport.simulation.pausing",
                        "\u6b63\u5728\u6682\u505c\u6a21\u62df...",
                    ),
                )
            else:
                logger.warning("GameViewport has no pause_simulation method")
        except Exception as error:
            logger.exception("Failed to pause simulation: %s", error)

    def on_stop(self, _data=None) -> None:
        try:
            if not self.viewport:
                logger.warning("GameViewport is not initialized")
                return
            if not self._is_real_game_viewport():
                logger.warning("Current viewport is not a GameViewport")
                return
            stop = getattr(self.viewport, "stop_simulation", None)
            if callable(stop):
                stop()
                logger.info(
                    "%s",
                    self._t(
                        "game_viewport.simulation.stopping",
                        "\u6b63\u5728\u505c\u6b62\u6a21\u62df...",
                    ),
                )
            else:
                logger.warning("GameViewport has no stop_simulation method")
        except Exception as error:
            logger.exception("Failed to stop simulation: %s", error)

    def _acquire_event_subscriptions(self) -> None:
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe):
            raise RuntimeError("event_bus.subscribe is unavailable")
        for event_name, callback_name in self._EVENT_BINDINGS:
            callback = getattr(self, callback_name)
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
            except BaseException as error:
                errors.append(error)
            else:
                subscriptions.pop(index)
        return errors

    def _release_runtime_capabilities(self) -> BaseException | None:
        if not getattr(self, "_runtime_capabilities_active", False):
            return None
        viewport = getattr(self, "viewport", None)
        dispose = getattr(viewport, "dispose_runtime_capabilities", None)
        if not callable(dispose):
            dispose = getattr(viewport, "unregister_as_sr_host", None)
        if not callable(dispose):
            self._runtime_capabilities_active = False
            return None
        try:
            dispose()
        except BaseException as error:
            return error
        self._runtime_capabilities_active = False
        return None

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(getattr(self, "context", None), "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data=None) -> None:
        """Refresh retained content in place; the Host owns the tab label."""
        viewport = getattr(self, "viewport", None)
        retranslate = getattr(viewport, "retranslate_ui", None)
        if callable(retranslate):
            retranslate()

    @staticmethod
    def _format_errors(errors: list[BaseException]) -> str:
        return "; ".join(f"{type(error).__name__}: {error}" for error in errors)
