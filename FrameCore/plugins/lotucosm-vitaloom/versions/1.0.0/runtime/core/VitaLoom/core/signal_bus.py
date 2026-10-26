# -*- coding: utf-8 -*-
"""Qt 信号总线单例：对象/项目/场景/UI 事件的 pyqtSignal 集中定义。

排错: 与 kernel.EventBus 字符串事件并存，订阅须匹配 SignalType。
"""

from typing import Dict, List, Callable, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from enum import Enum


class SignalType(Enum):
    """信号类型枚举"""
    # 对象相关
    OBJECT_CREATED = "object_created"
    OBJECT_DELETED = "object_deleted"
    OBJECT_MODIFIED = "object_modified"
    OBJECT_SELECTED = "object_selected"
    OBJECT_DESELECTED = "object_deselected"
    
    # 项目相关
    PROJECT_OPENED = "project_opened"
    PROJECT_CLOSED = "project_closed"
    PROJECT_SAVED = "project_saved"
    PROJECT_MODIFIED = "project_modified"
    
    # 场景相关
    SCENE_LOADED = "scene_loaded"
    SCENE_SAVED = "scene_saved"
    SCENE_MODIFIED = "scene_modified"
    
    # 编辑器相关
    MODE_CHANGED = "mode_changed"
    TOOL_CHANGED = "tool_changed"
    
    # UI相关
    PANEL_SHOWN = "panel_shown"
    PANEL_HIDDEN = "panel_hidden"
    VIEWPORT_CHANGED = "viewport_changed"


class SignalBus(QObject):
    """职责: 编辑器内建 Qt 信号 hub，供面板 connect 与 emit_* 辅助方法。
    时机: 各 Dock/视口初始化时 get_signal_bus()。
    不变量: 单例；emit 须在 GUI 线程。
    排错: 面板不刷新 → 是否连接 object_selected / scene_loaded 等。
    """
    
    _instance: Optional['SignalBus'] = None
    
    # 定义所有信号
    object_created = pyqtSignal(object, dict)  # 对象, 属性
    object_deleted = pyqtSignal(object)
    object_modified = pyqtSignal(object, dict)  # 对象, 修改的属性
    object_selected = pyqtSignal(object)
    object_deselected = pyqtSignal(object)
    
    project_opened = pyqtSignal(str)  # 项目路径
    project_closed = pyqtSignal()
    project_saved = pyqtSignal(str)  # 项目路径
    project_modified = pyqtSignal(bool)  # 是否已修改
    
    scene_loaded = pyqtSignal(str)  # 场景路径
    scene_saved = pyqtSignal(str)  # 场景路径
    scene_modified = pyqtSignal(bool)  # 是否已修改
    
    mode_changed = pyqtSignal(str)  # 模式名称
    tool_changed = pyqtSignal(str)  # 工具名称
    
    panel_shown = pyqtSignal(str)  # 面板ID
    panel_hidden = pyqtSignal(str)  # 面板ID
    viewport_changed = pyqtSignal(str)  # 视图ID
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is not None:
            try:
                cls._instance.metaObject()
            except RuntimeError:
                cls._instance = None
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
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
        if self._initialized:
            return
        
        super().__init__()
        
        # 信号映射表
        self._signal_map: Dict[SignalType, pyqtSignal] = {
            SignalType.OBJECT_CREATED: self.object_created,
            SignalType.OBJECT_DELETED: self.object_deleted,
            SignalType.OBJECT_MODIFIED: self.object_modified,
            SignalType.OBJECT_SELECTED: self.object_selected,
            SignalType.OBJECT_DESELECTED: self.object_deselected,
            SignalType.PROJECT_OPENED: self.project_opened,
            SignalType.PROJECT_CLOSED: self.project_closed,
            SignalType.PROJECT_SAVED: self.project_saved,
            SignalType.PROJECT_MODIFIED: self.project_modified,
            SignalType.SCENE_LOADED: self.scene_loaded,
            SignalType.SCENE_SAVED: self.scene_saved,
            SignalType.SCENE_MODIFIED: self.scene_modified,
            SignalType.MODE_CHANGED: self.mode_changed,
            SignalType.TOOL_CHANGED: self.tool_changed,
            SignalType.PANEL_SHOWN: self.panel_shown,
            SignalType.PANEL_HIDDEN: self.panel_hidden,
            SignalType.VIEWPORT_CHANGED: self.viewport_changed,
        }
        
        self._initialized = True
    
    def emit_signal(self, signal_type: SignalType, *args):
        """发送信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        signal = self._signal_map.get(signal_type)
        if signal:
            signal.emit(*args)
    
    def connect_signal(self, signal_type: SignalType, slot: Callable):
        """连接信号到槽函数。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        signal = self._signal_map.get(signal_type)
        if signal:
            signal.connect(slot)
    
    def disconnect_signal(self, signal_type: SignalType, slot: Callable):
        """断开信号连接。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        signal = self._signal_map.get(signal_type)
        if signal:
            signal.disconnect(slot)
    
    # ========== 便捷方法 ==========
    
    def emit_object_created(self, obj: Any, attributes: Optional[dict] = None):
        """发送对象创建信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.object_created.emit(obj, attributes or {})
    
    def emit_object_deleted(self, obj: Any):
        """发送对象删除信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.object_deleted.emit(obj)
    
    def emit_object_modified(self, obj: Any, modified_attrs: Optional[dict] = None):
        """发送对象修改信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.object_modified.emit(obj, modified_attrs or {})
    
    def emit_object_selected(self, obj: Any):
        """发送对象选中信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.object_selected.emit(obj)
    
    def emit_object_deselected(self, obj: Any):
        """发送对象取消选中信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.object_deselected.emit(obj)
    
    def emit_project_opened(self, path: str):
        """发送项目打开信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.project_opened.emit(path)
    
    def emit_project_closed(self):
        """发送项目关闭信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.project_closed.emit()
    
    def emit_project_saved(self, path: str):
        """发送项目保存信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.project_saved.emit(path)
    
    def emit_project_modified(self, modified: bool):
        """发送项目修改信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.project_modified.emit(modified)
    
    def emit_scene_loaded(self, path: str):
        """发送场景加载信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.scene_loaded.emit(path)
    
    def emit_scene_saved(self, path: str):
        """发送场景保存信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.scene_saved.emit(path)
    
    def emit_scene_modified(self, modified: bool):
        """发送场景修改信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.scene_modified.emit(modified)
    
    def emit_mode_changed(self, mode: str):
        """发送模式变化信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.mode_changed.emit(mode)
    
    def emit_tool_changed(self, tool: str):
        """发送工具变化信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.tool_changed.emit(tool)
    
    def emit_panel_shown(self, panel_id: str):
        """发送面板显示信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.panel_shown.emit(panel_id)
    
    def emit_panel_hidden(self, panel_id: str):
        """发送面板隐藏信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.panel_hidden.emit(panel_id)
    
    def emit_viewport_changed(self, viewport_id: str):
        """发送视图变化信号。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.viewport_changed.emit(viewport_id)


def get_signal_bus() -> SignalBus:
    """获取信号总线单例"""
    return SignalBus()
