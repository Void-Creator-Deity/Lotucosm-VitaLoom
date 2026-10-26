# -*- coding: utf-8 -*-
"""FrameCore 事件总线：Suite 级别的轻量发布/订阅接口。"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """职责: 为 Frame/Suite 交互提供最小事件接口。"""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        name = str(event_name or "").strip()
        if not name:
            raise ValueError("event_name must not be empty")
        self._handlers[name].append(handler)

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        name = str(event_name or "").strip()
        if not name:
            raise ValueError("event_name must not be empty")
        data = dict(payload or {})
        for handler in list(self._handlers.get(name, [])):
            handler(data)
