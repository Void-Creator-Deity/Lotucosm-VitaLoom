# -*- coding: utf-8 -*-
"""示例插件：通过 Qt-free IRuntimePlugin 向 runtime context.services 注册可发现服务。

职责: on_load 注册 TimeService；on_unload 注销。
时机: 须在消费方 ExampleServiceConsumer 之前加载（dependencies 可声明）。
排错: 消费方拿不到服务 → service_name 与 register 键一致。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin


class TimeService:
    service_name = "example.time_service"
    service_version = "1.1.0"

    def now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")


class ExampleServiceProviderPlugin(IRuntimePlugin):
    """服务提供者示例：注册 example.time_service。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "ExampleServiceProviderPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "示例服务提供者：注册 time_service",
            "dependencies": [],
            "provides": [],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.service = TimeService()
        services = getattr(self.context, "services", None)
        if services and hasattr(services, "register"):
            services.register("example.time_service", self.service)

    def on_unload(self):
        services = getattr(self.context, "services", None)
        if services and hasattr(services, "unregister"):
            services.unregister("example.time_service")



