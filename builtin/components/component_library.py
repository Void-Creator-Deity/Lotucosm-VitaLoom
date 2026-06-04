"""PS 组件类型注册表：类型名字符串 → ComponentBase 子类。

架构数据流::

    get_component_class ← ComponentFactory / 反序列化

不变量: 类型名与 `PondSerializer.deserialize_component` 的 `type` 字段一致。

排错: 见 `builtin/README.md`（未知类型）。
"""

from __future__ import annotations

from typing import Dict, Optional, Type

from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

_logger = get_logger("ComponentLibrary")

__all__ = ["get_component_class", "list_component_type_names", "register_component_class"]


_COMPONENT_REGISTRY: Dict[str, Type[ComponentBase]] = {}


def _bootstrap_builtin_types() -> None:
    if _COMPONENT_REGISTRY:
        return
    from builtin.components.sensors import Sensor, LightSensor
    from builtin.components.actuators import Actuator
    from builtin.components.hybrid import HybridComponent
    from builtin.components.membrane import Membrane

    _COMPONENT_REGISTRY.update(
        {
            "Sensor": Sensor,
            "LightSensor": LightSensor,
            "TouchSensor": Sensor,
            "Actuator": Actuator,
            "HybridComponent": HybridComponent,
            "Membrane": Membrane,
            "ComponentBase": ComponentBase,
        }
    )
    try:
        from builtin.components.PVAECEngine import PVAECEngine

        _COMPONENT_REGISTRY["PVAECEngine"] = PVAECEngine
    except Exception as exc:
        _logger.warning("PVAECEngine 未纳入组件目录: %s", exc)


def register_component_class(type_name: str, cls: Type[ComponentBase]) -> None:
    """注册或覆盖某类型名对应的组件类。"""
    _COMPONENT_REGISTRY[type_name] = cls


def list_component_type_names() -> list[str]:
    """返回当前已注册的全部组件类型名（类名字符串）。"""
    _bootstrap_builtin_types()
    return sorted(_COMPONENT_REGISTRY.keys())


def get_component_class(type_name: str) -> Type[ComponentBase]:
    """按序列化/配置中的 type 字段解析组件类；未知类型回退为 ComponentBase。"""
    _bootstrap_builtin_types()
    return _COMPONENT_REGISTRY.get(type_name, ComponentBase)
