"""Enum 事件总线：Event + EventBus 单例，供编辑器画布/生物体 UI 解耦（与 api.events 字符串总线并存）。

架构数据流::

    EventBus.register(EventType, callback) → emit(Event) → callback(event)

勿与 core.api.events 的 publish/subscribe 混用同一监听器。
"""
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ApiEventSystem")

class EventType(Enum):
    """编辑器与模拟器领域事件枚举（值为 snake_case 字符串）。"""

    # 生物相关事件
    ORGANISM_CREATED = "organism_created"  # 当新的AI生命体被创建时触发
    ORGANISM_DELETED = "organism_deleted"  # 当AI生命体被删除时触发
    ORGANISM_SELECTED = "organism_selected"  # 当AI生命体被选择时触发
    ORGANISM_UPDATED = "organism_updated"  # 当AI生命体的属性被更新时触发

    # 节点相关事件
    NODE_CREATED = "node_created"  # 当新节点（如传感器、执行器）被创建时触发
    NODE_DELETED = "node_deleted"  # 当节点被删除时触发
    NODE_MOVED = "node_moved"  # 当节点位置被移动时触发
    NODE_SELECTED = "node_selected"  # 当节点被选择时触发

    # 连接相关事件
    CONNECTION_CREATED = "connection_created"  # 当新连接被创建时触发
    CONNECTION_DELETED = "connection_deleted"  # 当连接被删除时触发
    CONNECTION_UPDATED = "connection_updated"  # 当连接属性被更新时触发

    # 模拟相关事件
    SIMULATION_STARTED = "simulation_started"  # 当模拟开始时触发
    SIMULATION_PAUSED = "simulation_paused"  # 当模拟暂停时触发
    SIMULATION_STOPPED = "simulation_stopped"  # 当模拟停止时触发
    SIMULATION_RESET = "simulation_reset"  # 当模拟重置时触发
    SIMULATION_STEP = "simulation_step"  # 当模拟执行一步时触发

    # 项目相关事件
    PROJECT_NEW = "project_new"  # 当新项目被创建时触发
    PROJECT_OPEN = "project_open"  # 当项目被打开时触发
    PROJECT_SAVED = "project_saved"  # 当项目被保存时触发
    PROJECT_MODIFIED = "project_modified"  # 当项目被修改时触发

    # 编辑器相关事件
    EDITOR_MODE_CHANGED = "editor_mode_changed"  # 当编辑器模式改变时触发

    # 画布相关事件
    CANVAS_UPDATED = "canvas_updated"  # 当画布内容更新时触发

class Event:
    """事件载荷：event_type + data dict。"""

    def __init__(self, event_type: EventType, data: Optional[Dict[str, Any]] = None):
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
        self.event_type = event_type  # 事件类型
        self.data = data or {}  # 事件数据，默认为空字典

    def __str__(self) -> str:
        return f"Event({self.event_type.value}, {self.data})"

class EventBus:
    """EventType → 回调列表；单例 event_bus 全局实例。

    生命周期:
        register → emit →（可选）unregister / clear
    """

    _instance = None  # 单例实例
    _listeners: Dict[EventType, List[Callable[[Optional[Event]], Any]]]  # 事件监听器字典

    def __new__(cls):
        """懒加载单例；首次创建时初始化 _listeners。"""
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            # 初始化监听器字典
            cls._instance._listeners = {}  # 事件类型到监听器列表的映射
        return cls._instance

    def register(self, event_type: EventType, callback: Callable[[Optional[Event]], Any]):
        """注册监听器（同回调不重复追加）。

        职责:
            维护 EventType 到回调列表映射。

        时机:
            编辑器面板/画布组件 __init__。

        不变量:
            callback 签名应接受 Event 参数。

        排错:
            未收到事件 → 发布侧须 emit 相同 EventType 枚举成员。
        """
        if event_type not in self._listeners:
            # 如果该事件类型还没有监听器列表，创建一个新的
            self._listeners[event_type] = []

        if callback not in self._listeners[event_type]:
            # 确保同一个回调函数不会被注册多次
            self._listeners[event_type].append(callback)

    def unregister(self, event_type: EventType, callback: Callable[[Optional[Event]], Any]):
        """移除监听器。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)

    def emit(self, event: Event):
        """调用该事件类型全部监听器；异常仅 warning 不中断。

        职责:
            按 event_type 分发 Event 至已注册 callback 列表。

        排错:
            日志「事件处理失败」→ 检查 callback 内是否假设 data 键存在。
        """
        if event.event_type in self._listeners:
            # 遍历该事件类型的所有监听器
            for callback in self._listeners[event.event_type]:
                try:
                    # 调用回调函数并传递事件对象
                    callback(event)
                except Exception as e:
                    # 捕获并打印事件处理过程中的错误，避免影响其他监听器
                    logger.warning("事件处理失败: %s", e)

    def clear(self):
        """清除全部监听器（重置或测试）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._listeners.clear()

# 创建全局事件总线实例
event_bus = EventBus()
