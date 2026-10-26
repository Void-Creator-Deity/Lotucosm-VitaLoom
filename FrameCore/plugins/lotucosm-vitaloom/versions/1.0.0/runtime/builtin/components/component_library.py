"""PS 组件类型注册表：类型名字符串 → ComponentBase 子类。

架构数据流::

    get_component_class ← ComponentFactory / 反序列化

不变量: 类型名与 `PondSerializer.deserialize_component` 的 `type` 字段一致。

排错: 见 `builtin/README.md`（未知类型）。
"""

from __future__ import annotations

from typing import Dict, Optional, Type, Any

from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

_logger = get_logger("ComponentLibrary")

__all__ = [
    "get_component_class",
    "list_component_type_names",
    "register_component_class",
    "canonical_component_type",
]


_COMPONENT_REGISTRY: Dict[str, Type[ComponentBase]] = {}

# 序列化 type 是持久化契约：优先使用稳定的注册名，而不是 Python 具体类名。
# 这样旧 .pond 中的 Actuator 仍恢复为 MuscleActuator，同时新代码不会写出
# 无法被 ComponentFactory 反解的 MuscleActuator。
_CANONICAL_TYPE_BY_CLASS: Dict[Type[ComponentBase], str] = {}



def _bootstrap_builtin_types() -> None:
    if _COMPONENT_REGISTRY:
        return
    from builtin.components.sensors import Sensor, LightSensor
    from builtin.components.actuators import Actuator, CiliaActuator, ReproductionActuator
    from builtin.components.hybrid import HybridComponent
    from builtin.components.membrane import Membrane

    _COMPONENT_REGISTRY.update(
        {
            "Sensor": Sensor,
            "LightSensor": LightSensor,
            "TouchSensor": Sensor,
            "Actuator": Actuator,
            "CiliaActuator": CiliaActuator,
            "ReproductionActuator": ReproductionActuator,
            "HybridComponent": HybridComponent,
            "Membrane": Membrane,
            "ComponentBase": ComponentBase,
        }
    )
    _CANONICAL_TYPE_BY_CLASS.update({
        Sensor: "Sensor",
        LightSensor: "LightSensor",
        Actuator: "Actuator",
        CiliaActuator: "CiliaActuator",
        ReproductionActuator: "ReproductionActuator",
        HybridComponent: "HybridComponent",
        Membrane: "Membrane",
        ComponentBase: "ComponentBase",
    })
    try:
        from builtin.components.PVAECEngine import PVAECEngine

        _COMPONENT_REGISTRY["PVAECEngine"] = PVAECEngine
        _CANONICAL_TYPE_BY_CLASS[PVAECEngine] = "PVAECEngine"
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


def canonical_component_type(component: Any) -> str:
    """Return the stable registry type for a component instance or class.

    Concrete implementation names (for example ``MuscleActuator``) are not
    emitted into the persistence format when a compatibility registration
    exists. Unknown plugin classes retain their class name for diagnostics.
    """
    _bootstrap_builtin_types()
    cls = component if isinstance(component, type) else type(component)
    for registered_class, canonical in _CANONICAL_TYPE_BY_CLASS.items():
        if cls is registered_class:
            return canonical
    return cls.__name__
