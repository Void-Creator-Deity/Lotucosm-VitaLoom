"""事件系统 - 用于组件间的解耦通信"""

from typing import Dict, List, Callable, Any
from enum import Enum
import inspect


class EventType(Enum):
    """事件类型枚举
    
    定义了系统中所有可能的事件类型，用于组件间的解耦通信。
    事件类型按功能分类，便于管理和使用。
    """
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
    """事件对象
    
    用于封装事件类型和事件数据，是组件间通信的基本单位。
    
    属性:
        event_type: EventType - 事件的类型
        data: Dict[str, Any] - 事件相关的数据
    """
    
    def __init__(self, event_type: EventType, data: Dict[str, Any] = None):
        """初始化事件对象
        
        参数:
            event_type: EventType - 事件的类型
            data: Dict[str, Any] - 事件相关的数据，默认为空字典
        """
        self.event_type = event_type  # 事件类型
        self.data = data or {}  # 事件数据，默认为空字典
    
    def __str__(self) -> str:
        """返回事件对象的字符串表示
        
        返回:
            str - 事件对象的字符串表示，格式为"Event(事件类型, 事件数据)"
        """
        return f"Event({self.event_type.value}, {self.data})"


class EventBus:
    """事件总线 - 单例模式
    
    实现了发布-订阅模式，用于组件间的解耦通信。
    采用单例模式设计，确保整个系统只有一个事件总线实例。
    
    属性:
        _listeners: Dict[EventType, List[Callable]] - 事件监听器字典，
                     键为事件类型，值为该事件类型对应的监听器列表
    """
    
    _instance = None  # 单例实例
    
    def __new__(cls):
        """创建单例实例
        
        确保整个系统只有一个EventBus实例，采用懒加载方式创建。
        
        返回:
            EventBus - EventBus的单例实例
        """
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            # 初始化监听器字典
            cls._instance._listeners = {}  # 事件类型到监听器列表的映射
        return cls._instance
    
    def register(self, event_type: EventType, callback: Callable):
        """注册事件监听器
        
        为指定的事件类型注册一个回调函数，当该事件类型被发布时，
        所有注册的回调函数都会被调用。
        
        参数:
            event_type: EventType - 要注册的事件类型
            callback: Callable - 事件触发时要调用的回调函数
        """
        if event_type not in self._listeners:
            # 如果该事件类型还没有监听器列表，创建一个新的
            self._listeners[event_type] = []
        
        if callback not in self._listeners[event_type]:
            # 确保同一个回调函数不会被注册多次
            self._listeners[event_type].append(callback)
    
    def unregister(self, event_type: EventType, callback: Callable):
        """取消注册事件监听器
        
        从指定的事件类型中移除一个回调函数，该回调函数将不再接收
        该事件类型的通知。
        
        参数:
            event_type: EventType - 要取消注册的事件类型
            callback: Callable - 要移除的回调函数
        """
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
    
    def emit(self, event: Event):
        """发布事件
        
        发布一个事件，所有注册了该事件类型的监听器都会被调用。
        
        参数:
            event: Event - 要发布的事件对象
        """
        if event.event_type in self._listeners:
            # 遍历该事件类型的所有监听器
            for callback in self._listeners[event.event_type]:
                try:
                    # 检查回调函数的参数数量，以支持不同类型的回调
                    sig = inspect.signature(callback)
                    if len(sig.parameters) == 1:
                        # 如果回调函数需要一个参数，将事件对象传递给它
                        callback(event)
                    else:
                        # 否则，直接调用回调函数
                        callback()
                except Exception as e:
                    # 捕获并打印事件处理过程中的错误，避免影响其他监听器
                    print(f"事件处理错误: {e}")
    
    def clear(self):
        """清除所有事件监听器
        
        移除所有已注册的事件监听器，用于重置事件总线。
        """
        self._listeners.clear()


# 创建全局事件总线实例
event_bus = EventBus()
