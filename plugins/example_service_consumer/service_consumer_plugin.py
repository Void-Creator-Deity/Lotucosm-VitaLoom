# -*- coding: utf-8 -*-
"""示例插件：从 EditorContext.services 消费已注册服务。

职责: on_editor_ready 解析 example.time_service 并打日志。
时机: 须在 ExampleServiceProvider 加载之后；可用 dependencies 声明。
排错: 服务为 None → 检查 provider 的 service_name 与 register 键。
"""

from __future__ import annotations

from typing import Any, Dict

from core.plugin.interfaces import IEditorPlugin
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ExampleServiceConsumer")


class ExampleServiceConsumerPlugin(IEditorPlugin):
    """服务消费者示例：依赖 example.time_service v1.0+。"""

    REQUIRED_TIME_SERVICE_VERSION = "1.0.0"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "ExampleServiceConsumer",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "示例服务消费者：读取 example.time_service",
            "dependencies": ["ExampleServiceProvider"],
            "provides": [],
        }

    def on_load(self, editor_context):
        self.context = editor_context

    def on_unload(self):
        return

    def on_editor_ready(self):
        services = getattr(self.context, "services", None)
        if not services or not hasattr(services, "get"):
            logger.warning("服务注册表不可用")
            return
        svc = services.get("example.time_service")
        if not svc or not hasattr(svc, "now_iso"):
            logger.warning("未找到示例服务: example.time_service")
            return

        svc_version = str(getattr(svc, "service_version", "0.0.0"))
        if not self._is_version_compatible(svc_version, self.REQUIRED_TIME_SERVICE_VERSION):
            logger.warning(
                "服务版本不兼容: required>=%s actual=%s service=example.time_service",
                self.REQUIRED_TIME_SERVICE_VERSION,
                svc_version,
            )
            return

        logger.info("示例服务调用成功: now=%s version=%s", svc.now_iso(), svc_version)

    @staticmethod
    def _parse_version(version: str) -> tuple[int, int, int]:
        parts = (version or "0.0.0").split(".")
        nums = []
        for i in range(3):
            try:
                nums.append(int(parts[i]) if i < len(parts) else 0)
            except Exception:
                nums.append(0)
        return nums[0], nums[1], nums[2]

    @classmethod
    def _is_version_compatible(cls, actual: str, required_min: str) -> bool:
        return cls._parse_version(actual) >= cls._parse_version(required_min)

