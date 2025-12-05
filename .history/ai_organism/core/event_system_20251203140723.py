"""事件系统 - 用于组件间的解耦通信"""

from typing import Dict, List, Callable, Any
from enum import Enum
import inspect


class EventType(Enum):
    """事件类型枚举"""
    # 生物相关事件
    ORGANISM_CREATED = "organism_created"
    ORGANISM_DELETED = "organism_deleted"
    ORGANISM_SELECTED = "organism_selected"
    ORGANISM_UPDATED = "organism_updated"
    
    # 节点相关事件
    NODE_CREATED = "node_created"
    NODE_DELETED = "node_deleted"
    NODE_MOVED = "node_moved"
    NODE_SELECTED = "node_selected"
    
    # 连接相关事件
    CONNECTION_CREATED = "connection_created"
    CONNECTION_DELETED = "connection_deleted"
    CONNECTION_UPDATED = "connection_updated"
    
    # 模拟相关事件
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_STOPPED = "simulation_stopped"
    SIMULATION_RESET = "simulation_reset"
    SIMULATION_STEP = "simulation_step"
    
    # 项目相关事件
    PROJECT_NEW = "project_new"
    PROJECT_OPEN = "project_open"
    PROJECT_SAVED = "project_saved"
    PROJECT_MODIFIED = "project_modified"
    
    # 编辑器相关事件
    EDITOR_MODE_CHANGED = "editor_mode_changed"
    
    # 画布相关事件
    CANVAS_UPDATED = "canvas_updated"


class Event:
    """事件对象"""
    def __init__(self, event_type: EventType, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.data = data or {}
    
    def __str__(self):
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
