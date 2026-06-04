# -*- coding: utf-8 -*-
"""快捷键注册表：QAction 与可配置键位绑定。

排错: 快捷键无效 → 是否 register 到 QMainWindow 且未被插件覆盖。
"""

from typing import Optional, Dict, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import QWidget

from core.VitaLoom.core.logger import get_logger


logger = get_logger("ShortcutManager")


class ShortcutManager(QObject):
    """职责: 集中管理编辑器快捷键映射与冲突检测。"""
    """快捷键管理器单例"""
    
    _instance: Optional['ShortcutManager'] = None
    shortcut_triggered = pyqtSignal(str)  # Emits shortcut ID
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ShortcutManager.__init__。

        
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
        super().__init__()
        self._initialized = True
        
        # 快捷键注册表: shortcut_id -> (key_sequence, callback, description, context)
        self.shortcuts: Dict[str, tuple] = {}
        # QAction注册表: shortcut_id -> QAction
        self.actions: Dict[str, QAction] = {}
        # 默认快捷键配置
        self.default_shortcuts: Dict[str, str] = {}
        
        self._init_default_shortcuts()
    
    def _init_default_shortcuts(self):
        """初始化默认快捷键配置"""
        self.default_shortcuts = {
            # 文件操作
            "file.new_project": "Ctrl+N",
            "file.open_project": "Ctrl+O",
            "file.save": "Ctrl+S",
            "file.save_as": "Ctrl+Shift+S",
            "file.close": "Ctrl+W",
            "file.exit": "Alt+F4",
            
            # 编辑操作
            "edit.undo": "Ctrl+Z",
            "edit.redo": "Ctrl+Y",
            "edit.cut": "Ctrl+X",
            "edit.copy": "Ctrl+C",
            "edit.paste": "Ctrl+V",
            "edit.delete": "Delete",
            "edit.select_all": "Ctrl+A",
            "edit.duplicate": "Ctrl+D",
            
            # 视图操作
            "view.hierarchy": "Ctrl+1",
            "view.inspector": "Ctrl+2",
            "view.project": "Ctrl+3",
            "view.memory_editor": "Ctrl+4",
            "view.console": "Ctrl+5",
            "view.zoom_in": "Ctrl++",
            "view.zoom_out": "Ctrl+-",
            "view.zoom_reset": "Ctrl+0",
            "view.fullscreen": "F11",
            
            # 模拟操作
            "simulation.play": "F5",
            "simulation.pause": "F6",
            "simulation.stop": "Shift+F5",
            "simulation.step": "F10",
            "simulation.restart": "Ctrl+F5",
            
            # 工具操作
            "tool.select": "V",
            "tool.move": "W",
            "tool.rotate": "E",
            "tool.scale": "R",
            "tool.pan": "H",
            
            # 对象操作
            "object.create_organism": "Ctrl+Shift+O",
            "object.create_sensor": "Ctrl+Shift+S",
            "object.create_actuator": "Ctrl+Shift+A",
            "object.create_brain": "Ctrl+Shift+B",
            "object.group": "Ctrl+G",
            "object.ungroup": "Ctrl+Shift+G",
            
            # 搜索操作
            "search.find": "Ctrl+F",
            "search.find_next": "F3",
            "search.find_prev": "Shift+F3",
            "search.replace": "Ctrl+H",
            "search.goto": "Ctrl+G",
            
            # 帮助操作
            "help.documentation": "F1",
            "help.about": "Ctrl+Shift+H",
        }
    
    def register_shortcut(
        self,
        shortcut_id: str,
        callback: Callable,
        description: str = "",
        context: Optional[QWidget] = None,
        key_sequence: Optional[str] = None
    ):
        """注册快捷键。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        # 使用提供的按键序列或默认配置
        if key_sequence is None:
            key_sequence = self.default_shortcuts.get(shortcut_id, "")
        
        if not key_sequence:
            logger.warning(
                self._t("shortcut.no_key_sequence", "⚠️ 快捷键未配置按键序列: '{id}'").format(id=shortcut_id)
            )
            return
        
        # 保存快捷键信息
        self.shortcuts[shortcut_id] = (key_sequence, callback, description, context)
        
        # 创建QAction
        action = QAction(description or shortcut_id, context or QWidget())
        action.setShortcut(QKeySequence(key_sequence))
        action.triggered.connect(callback)
        
        # 如果有上下文，添加到上下文
        if context:
            context.addAction(action)
        
        self.actions[shortcut_id] = action
    
    def unregister_shortcut(self, shortcut_id: str):
        """注销快捷键。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if shortcut_id in self.shortcuts:
            del self.shortcuts[shortcut_id]
        
        if shortcut_id in self.actions:
            action = self.actions[shortcut_id]
            # 从父widget中移除
            if action.parent():
                action.parent().removeAction(action)
            del self.actions[shortcut_id]
    
    def update_shortcut(self, shortcut_id: str, new_key_sequence: str):
        """更新快捷键。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if shortcut_id not in self.shortcuts:
            logger.warning(
                self._t("shortcut.not_found", "⚠️ 未找到快捷键: '{id}'").format(id=shortcut_id)
            )
            return
        
        old_key_sequence, callback, description, context = self.shortcuts[shortcut_id]
        
        # 更新快捷键信息
        self.shortcuts[shortcut_id] = (new_key_sequence, callback, description, context)
        
        # 更新QAction
        if shortcut_id in self.actions:
            self.actions[shortcut_id].setShortcut(QKeySequence(new_key_sequence))
    
    def get_shortcut(self, shortcut_id: str) -> Optional[str]:
        """获取快捷键序列。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if shortcut_id in self.shortcuts:
            return self.shortcuts[shortcut_id][0]
        return None
    
    def get_all_shortcuts(self) -> Dict[str, tuple]:
        """获取所有快捷键。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.shortcuts.copy()
    
    def reset_to_defaults(self):
        """重置所有快捷键为默认值。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        for shortcut_id in list(self.shortcuts.keys()):
            if shortcut_id in self.default_shortcuts:
                self.update_shortcut(shortcut_id, self.default_shortcuts[shortcut_id])
    
    def export_shortcuts(self) -> Dict[str, str]:
        """导出快捷键配置。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return {sid: info[0] for sid, info in self.shortcuts.items()}
    
    def import_shortcuts(self, shortcuts_config: Dict[str, str]):
        """导入快捷键配置。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        for shortcut_id, key_sequence in shortcuts_config.items():
            if shortcut_id in self.shortcuts:
                self.update_shortcut(shortcut_id, key_sequence)

    def _t(self, key: str, default: str = "") -> str:
        try:
            from core.VitaLoom.core.editor_context import get_editor_context
            ctx = get_editor_context()
            tr_fn = getattr(ctx, "i18n_tr", None)
            if callable(tr_fn):
                return tr_fn(key, default)
        except Exception:
            pass
        return default or key


def get_shortcut_manager() -> ShortcutManager:
    """获取快捷键管理器单例"""
    return ShortcutManager()
