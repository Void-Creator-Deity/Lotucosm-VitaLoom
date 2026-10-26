# -*- coding: utf-8 -*-
"""FrameCore 服务注册表：Frame/Suite 之间的最小服务发现接口。"""
from __future__ import annotations

from typing import Any


class ServiceRegistry:
    """职责: 注册与查询 Suite 级服务。"""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        key = str(name or "").strip()
        if not key:
            raise ValueError("service name must not be empty")
        self._services[key] = service

    def get(self, name: str, default: Any = None) -> Any:
        return self._services.get(str(name or "").strip(), default)

    def has(self, name: str) -> bool:
        return str(name or "").strip() in self._services
