"""字符串事件总线 API：线程安全 subscribe/publish（与 event_system.Enum 总线分离）。

架构数据流::

    subscribe(event_type, callback) → publish(type, data) → 回调同步执行

全局单例 get_event_bus()；便捷函数 subscribe/publish 操作同一实例。
"""
from typing import Callable, Dict, List, Any
import threading
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ApiEvents")


class EventBus:
    """按 event_type 字符串分组的订阅者列表（带锁）。"""

    def __init__(self):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """注册回调到 event_type 列表。

        职责:
            线程安全追加 callback。

        时机:
            插件 on_load、脚本 subscribe()。

        不变量:
            同一 callback 可重复注册（不去重）。

        排错:
            未触发 → 发布类型字符串须与订阅完全一致；勿与 event_system.EventType Enum 混用。
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """移除已注册的 callback。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, event_data: Dict[str, Any] = None) -> None:
        """同步调用该类型所有订阅者；单回调异常不影响其余。

        职责:
            拷贝订阅列表后于锁外调用，避免死锁。

        时机:
            编辑器/模拟器状态变更后广播。

        不变量:
            event_data 默认为 {}。

        排错:
            日志「事件处理失败」→ 查具体 callback 堆栈。
        """
        if event_data is None:
            event_data = {}

        with self._lock:
            subscribers = self._subscribers.get(event_type, []).copy()

        # 异步调用所有订阅者
        for callback in subscribers:
            try:
                callback(event_data)
            except Exception as e:
                logger.exception("事件处理失败: %s", e)

    def clear(self) -> None:
        """清空所有订阅（测试或重置用）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        with self._lock:
            self._subscribers.clear()


# 全局事件总线实例
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """返回模块级全局 EventBus 单例。"""
    return _global_event_bus


def subscribe(event_type: str, callback: Callable) -> None:
    """订阅全局总线（便捷函数）。"""
    _global_event_bus.subscribe(event_type, callback)


def unsubscribe(event_type: str, callback: Callable) -> None:
    """取消订阅全局总线。"""
    _global_event_bus.unsubscribe(event_type, callback)


def publish(event_type: str, event_data: Dict[str, Any] = None) -> None:
    """发布到全局总线。"""
    _global_event_bus.publish(event_type, event_data)


# 预定义事件类型
class EventType:
    """点分字符串事件名常量（与 event_system.EventType Enum 不同命名空间）。"""

    # 实体事件
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"
    ENTITY_MOVED = "entity.moved"

    # 组件事件
    COMPONENT_ADDED = "component.added"
    COMPONENT_REMOVED = "component.removed"
    COMPONENT_UPDATED = "component.updated"

    # 系统事件
    SYSTEM_REGISTERED = "system.registered"
    SYSTEM_UNREGISTERED = "system.unregistered"
    SYSTEM_UPDATED = "system.updated"

    # 项目事件
    PROJECT_OPENED = "project.opened"
    PROJECT_SAVED = "project.saved"
    PROJECT_CLOSED = "project.closed"

    # 编辑器事件
    EDITOR_MODE_CHANGED = "editor.mode_changed"
    EDITOR_SELECTION_CHANGED = "editor.selection_changed"
    EDITOR_UNDO = "editor.undo"
    EDITOR_REDO = "editor.redo"

    # 模拟事件
    SIMULATION_STARTED = "simulation.started"
    SIMULATION_STOPPED = "simulation.stopped"
    SIMULATION_PAUSED = "simulation.paused"
    SIMULATION_RESUMED = "simulation.resumed"
    SIMULATION_UPDATED = "simulation.updated"
