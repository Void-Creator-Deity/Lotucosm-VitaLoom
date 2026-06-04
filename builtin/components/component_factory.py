"""PS 组件工厂：类型名 → ComponentBase 实例。

架构数据流::

    PondSerializer / 编辑器 → ComponentFactory.create_component → component_library

排错: 见 `builtin/README.md`（未知类型、Inspector 缺项）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from builtin.components.components_base import ComponentBase
from builtin.components.component_library import (
    get_component_class,
    list_component_type_names,
    register_component_class,
)

__all__ = ["ComponentFactory", "normalize_component_type"]

# 旧版 vitalloom 工厂使用小写 type；与 component_library 注册名对齐
_LEGACY_TYPE_ALIASES: dict[str, str] = {
    "sensor": "Sensor",
    "actuator": "Actuator",
    "pvaecengine": "PVAECEngine",
    "hybrid": "HybridComponent",
    "hybridcomponent": "HybridComponent",
    "membrane": "Membrane",
    "touchsensor": "Sensor",
    "proximitysensor": "Sensor",
    "lightsensor": "LightSensor",
}


def normalize_component_type(component_type: str) -> str:
    """将序列化/旧版 type 字符串规范为注册表类名。"""
    key = (component_type or "").strip()
    if not key:
        return key
    known = set(list_component_type_names())
    if key in known:
        return key
    mapped = _LEGACY_TYPE_ALIASES.get(key.lower())
    if mapped and mapped in known:
        return mapped
    return key


class ComponentFactory:
    """从注册表类型名构造组件，兼容历史 `create_component` 签名。"""

    def create_component(
        self,
        component_type: str,
        component_id: str,
        organism_id: str = "",
        name: Optional[str] = None,
        **params: Any,
    ) -> ComponentBase:
        """按类型名实例化组件并绑定 organism_id。

        职责: 查 `get_component_class(component_type)`，以 `component_id`/`name` 构造实例。
        时机: 反序列化、细胞编辑器拖放、运行时按需补组件时调用。
        不变量: `component_type` 须在 `component_library` 注册；`component_id` 在生物体内唯一。
        排错: 抛错或 AttributeError → 查 `list_component_type_names()` 与注册名拼写。
        """
        resolved = normalize_component_type(component_type)
        cls = get_component_class(resolved)
        display_name = name or component_id
        return cls(
            component_id=component_id,
            organism_id=organism_id,
            name=display_name,
            **params,
        )

    def create_component_from_template(
        self,
        template: Dict[str, Any],
        component_id: str,
        organism_id: str = "",
    ) -> ComponentBase:
        """按模板 dict 构造组件（兼容旧版 component_factory）。"""
        if not isinstance(template, dict):
            raise ValueError("组件模板须为 dict")
        raw_type = template.get("type", "")
        if not raw_type:
            raise ValueError("组件模板缺少 type 字段")
        params = dict(template)
        params.pop("type", None)
        params.pop("id", None)
        return self.create_component(
            str(raw_type),
            component_id,
            organism_id=organism_id,
            name=params.pop("name", None),
            **params,
        )

    def register_component_type(self, component_type: str, component_class: type[ComponentBase]) -> None:
        """注册类型别名（小写键与类名键均写入注册表）。"""
        register_component_class(component_type, component_class)
        register_component_class(component_type.lower(), component_class)

    def get_available_component_types(self) -> list[str]:
        """返回已注册类型名（与旧版 get_available_component_types 对齐）。"""
        return list_component_type_names()
