# -*- coding: utf-8 -*-
"""Qt-free Host-scoped string event bus Interface and in-memory Implementation.

This Module belongs to the versioned runtime of the sole L1
`lotucosm-vitaloom` engine plugin. It is not a process-global event system and
must not be confused with the legacy Enum-based buses under `core.api`.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol, TypeAlias, runtime_checkable


RuntimeEventCallback: TypeAlias = Callable[[object | None], object]
logger = logging.getLogger("VitaLoom.RuntimeEventBus")


def _normalize_event_name(event_name: object) -> str:
    if not isinstance(event_name, str):
        raise TypeError("event name must be a string")
    normalized = event_name.strip()
    if not normalized:
        raise ValueError("event name must not be empty")
    return normalized


def _require_callback(callback: object) -> RuntimeEventCallback:
    if not callable(callback):
        raise TypeError("callback must be callable")
    return callback


@runtime_checkable
class RuntimeEventBus(Protocol):
    """Minimal synchronous string-event Interface for one composed L1 Host."""

    def subscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None: ...

    def unsubscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None: ...

    def publish(self, event_name: str, data: object | None = None) -> None: ...


class InMemoryRuntimeEventBus:
    """Ordered, synchronous, per-instance runtime event dispatch."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[RuntimeEventCallback]] = {}

    def subscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None:
        normalized = _normalize_event_name(event_name)
        validated_callback = _require_callback(callback)
        self._subscribers.setdefault(normalized, []).append(validated_callback)

    def unsubscribe(
        self,
        event_name: str,
        callback: RuntimeEventCallback,
    ) -> None:
        normalized = _normalize_event_name(event_name)
        validated_callback = _require_callback(callback)
        subscribers = self._subscribers.get(normalized)
        if not subscribers:
            return
        try:
            subscribers.remove(validated_callback)
        except ValueError:
            return
        if not subscribers:
            self._subscribers.pop(normalized, None)

    def publish(self, event_name: str, data: object | None = None) -> None:
        normalized = _normalize_event_name(event_name)
        for callback in tuple(self._subscribers.get(normalized, ())):
            try:
                callback(data)
            except Exception as exc:
                logger.warning(
                    "Runtime event callback failed: event=%s error=%s",
                    normalized,
                    exc,
                )


def require_runtime_event_bus(candidate: object) -> RuntimeEventBus:
    """Validate and return an explicit Host-scoped runtime event bus."""

    if not isinstance(candidate, RuntimeEventBus):
        raise TypeError(
            "runtime event bus must implement subscribe/unsubscribe/publish"
        )
    return candidate


__all__ = [
    "InMemoryRuntimeEventBus",
    "RuntimeEventBus",
    "RuntimeEventCallback",
    "require_runtime_event_bus",
]
