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
    """事件总线 - 单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._listeners = {}
        return cls._instance
    
    def register(self, event_type: EventType, callback: Callable):
        """注册事件监听器"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)
    
    def unregister(self, event_type: EventType, callback: Callable):
        """取消注册事件监听器"""
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
    
    def emit(self, event: Event):
        """发布事件"""
        if event.event_type in self._listeners:
            for callback in self._listeners[event.event_type]:
                try:
                    # 检查回调函数的参数数量
                    sig = inspect.signature(callback)
                    if len(sig.parameters) == 1:
                        callback(event)
                    else:
                        callback()
                except Exception as e:
                    print(f"事件处理错误: {e}")
    
    def clear(self):
        """清除所有事件监听器"""
        self._listeners.clear()


# 创建全局事件总线实例
event_bus = EventBus()
