# -*- coding: utf-8 -*-
"""视口类型注册表，桥接 LayoutManager 与具体 QWidget 视口。

排错: 见 README「视口标签页」。
"""

from enum import Enum
from typing import Dict, Optional, Any
from PyQt6.QtWidgets import QWidget

from core.VitaLoom.core.editor_context import get_editor_context


class ViewportType(Enum):
    """视图类型"""
    SCENE = "scene"  # 场景视图（编辑模式）
    GAME = "game"    # 游戏视图（模拟模式）


class ViewportManager:
    """职责: 按 ViewportType 缓存视口实例并协调切换。"""
    """视图管理器 - 管理多个视图的切换和状态"""
    
    _instance: Optional['ViewportManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ViewportManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ViewportManager.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self._initialized:
            return
        self._initialized = True
        
        self.viewports: Dict[str, QWidget] = {}
        self.viewport_types: Dict[str, ViewportType] = {}
        self.active_viewport_id: Optional[str] = None
        self.editor_context = get_editor_context()
    
    def register_viewport(self, viewport_id: str, viewport: QWidget, viewport_type: ViewportType):
        """注册视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.viewports[viewport_id] = viewport
        self.viewport_types[viewport_id] = viewport_type
    
    def unregister_viewport(self, viewport_id: str):
        """注销视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if viewport_id in self.viewports:
            del self.viewports[viewport_id]
        if viewport_id in self.viewport_types:
            del self.viewport_types[viewport_id]
        if self.active_viewport_id == viewport_id:
            self.active_viewport_id = None
    
    def get_viewport(self, viewport_id: str) -> Optional[QWidget]:
        """获取视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.viewports.get(viewport_id)
    
    def set_active_viewport(self, viewport_id: str):
        """设置活动视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if viewport_id in self.viewports:
            self.active_viewport_id = viewport_id
    
    def get_active_viewport(self) -> Optional[QWidget]:
        """获取活动视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.active_viewport_id:
            return self.viewports.get(self.active_viewport_id)
        return None
    
    def get_viewport_by_type(self, viewport_type: ViewportType) -> Optional[QWidget]:
        """根据类型获取视图。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        for vid, vtype in self.viewport_types.items():
            if vtype == viewport_type:
                return self.viewports.get(vid)
        return None


def get_viewport_manager() -> ViewportManager:
    """获取视图管理器单例"""
    return ViewportManager()
