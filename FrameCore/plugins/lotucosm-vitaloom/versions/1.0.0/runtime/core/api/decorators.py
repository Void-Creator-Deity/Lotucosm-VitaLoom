"""元数据装饰器：暴露属性、注册组件/系统、标记脚本可调用方法。

架构数据流::

    @register_component → 工厂/Inspector 扫描 cls._registered_component
    @expose_property → 编辑器属性面板
    @script_method → ScriptRuntime 反射（若接入）

装饰器仅附加类/函数属性，不改变被装饰 callable 的运行时行为。
"""
from typing import Callable, Any
import functools


def expose_property(property_name: str = None, **kwargs: Any) -> Callable:
    """标记函数为可暴露属性（编辑器/脚本元数据）。

    职责:
        在 wrapper 上设置 _exposed_property、_property_name、_property_metadata。

    时机:
        组件/实体类定义期。

    不变量:
        property_name 默认取 func.__name__。

    排错:
            Inspector 无字段 → 扫描逻辑须识别 _exposed_property 而非仅 dataclass。
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs_inner):
            return func(*args, **kwargs_inner)

        # 添加暴露属性标记
        wrapper._exposed_property = True
        wrapper._property_name = property_name or func.__name__
        wrapper._property_metadata = kwargs

        return wrapper
    return decorator


def register_component(component_type: str, **kwargs: Any) -> Callable:
    """标记类为可注册组件类型。

    职责:
        设置 cls._registered_component、_component_type、_component_metadata。

    排错:
        组件库未列出 → ComponentFactory 是否扫描该标记。
    """
    def decorator(cls: type) -> type:
        # 添加注册组件标记
        cls._registered_component = True
        cls._component_type = component_type
        cls._component_metadata = kwargs

        return cls
    return decorator


def register_system(system_name: str, **kwargs: Any) -> Callable:
    """标记类为可注册系统（priority/description 等元数据）。"""
    def decorator(cls: type) -> type:
        # 添加注册系统标记
        cls._registered_system = True
        cls._system_name = system_name
        cls._system_metadata = kwargs

        return cls
    return decorator


def script_method(method_name: str = None, **kwargs: Any) -> Callable:
    """标记方法可供脚本系统按名调用。

    职责:
        设置 _script_method、_method_name、_method_metadata。

    排错:
        脚本找不到方法 → 反射须读取 _script_method 而非仅 public 名称。
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs_inner):
            return func(*args, **kwargs_inner)

        # 添加脚本方法标记
        wrapper._script_method = True
        wrapper._method_name = method_name or func.__name__
        wrapper._method_metadata = kwargs

        return wrapper
    return decorator
