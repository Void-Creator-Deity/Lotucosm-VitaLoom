# -*- coding: utf-8 -*-
"""Legacy PyQt signal Adapter for the Host-scoped runtime string event bus."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from core.VitaLoom.core.runtime_event_bus import (
    InMemoryRuntimeEventBus,
    RuntimeEventBus,
    RuntimeEventCallback,
    require_runtime_event_bus,
)


class EventBus(QObject):
    """Add the legacy `event_fired` Qt signal to a Qt-free runtime bus."""

    event_fired = pyqtSignal(str, object)

    def __init__(
        self,
        runtime_bus: RuntimeEventBus | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._runtime_bus = (
            InMemoryRuntimeEventBus()
            if runtime_bus is None
            else require_runtime_event_bus(runtime_bus)
        )

    @property
    def runtime_bus(self) -> RuntimeEventBus:
        return self._runtime_bus

    def subscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None:
        self._runtime_bus.subscribe(event_name, callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None:
        self._runtime_bus.unsubscribe(event_name, callback)

    def publish(self, event_name: str, data: object | None = None) -> None:
        self._runtime_bus.publish(event_name, data)
        self.event_fired.emit(event_name.strip(), data)


__all__ = ["EventBus"]
