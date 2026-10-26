"""
扩展 API 包：装饰器、字符串事件总线（events）、Enum 事件总线（event_system）、脚本运行时。 排错: 见同目录 README 或 docs/lotucosm_core_troubleshooting.md。
"""

from .decorators import expose_property, register_component, register_system, script_method
from .events import EventBus, get_event_bus, subscribe, unsubscribe, publish, EventType
from .scripting import ScriptRuntime, get_script_runtime, execute_script, execute_script_file

__all__ = [
    # 装饰器
    'expose_property',
    'register_component',
    'register_system',
    'script_method',

    # 事件系统
    'EventBus',
    'get_event_bus',
    'subscribe',
    'unsubscribe',
    'publish',
    'EventType',

    # 脚本系统
    'ScriptRuntime',
    'get_script_runtime',
    'execute_script',
    'execute_script_file'
]
