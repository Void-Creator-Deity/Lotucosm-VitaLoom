# -*- coding: utf-8 -*-
"""编辑器上下文单例：项目/场景/选区/模式/服务注册表。

排错: 见 core/VitaLoom/README.md；双总线勿与 core/api 混用。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from .runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
    RuntimeCapabilityRegistry,
    require_runtime_capability_registry,
)

# Legacy plugin import compatibility. The Implementation itself is Qt-free.
ServiceRegistry = InMemoryRuntimeCapabilityRegistry


class EditorMode(Enum):
    """编辑器模式。"""

    EDIT = "edit"
    SIMULATE = "simulate"
    PLAY = "play"
    PAUSE = "pause"


class EditorContext(QObject):
    """职责: 全局可写状态（当前项目、场景 dict、选区、EditorMode）与 kernel 引用。
    时机: 各模块通过 get_editor_context() 读取；项目/场景切换时更新字段。
    不变量: 单例；kernel/event_bus 由 EditorKernel 注入。
    排错: 插件取不到莲池 → current_scene 是否已 load_scene 填充。
    """

    _instance: Optional["EditorContext"] = None

    selection_changed = pyqtSignal(list)
    project_changed = pyqtSignal(str)
    project_modified_changed = pyqtSignal(bool)
    mode_changed = pyqtSignal(EditorMode)

    def __new__(cls, capability_registry: object | None = None):
        if cls._instance is not None:
            try:
                cls._instance.metaObject()
            except RuntimeError:
                cls._instance = None
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, capability_registry: object | None = None):
        """EditorContext.__init__。

        
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
            if (
                capability_registry is not None
                and self.services is not capability_registry
            ):
                raise RuntimeError(
                    "EditorContext runtime capability registry is already bound"
                )
            return

        if capability_registry is None:
            services: RuntimeCapabilityRegistry = (
                InMemoryRuntimeCapabilityRegistry()
            )
        else:
            services = require_runtime_capability_registry(capability_registry)

        self._selected_objects: List[Any] = []
        self._current_project_path: Optional[str] = None
        self._project_modified: bool = False
        self._current_mode: EditorMode = EditorMode.EDIT
        self._current_scene: Optional[Any] = None
        self._canvas: Optional[Any] = None
        self.services = services
        self._qobject_initialized = False

        self._try_init_qobject()
        self._initialized = True

    def _try_init_qobject(self):
        """尽量在 QApplication 可用时完成 QObject 初始化。"""
        if self._qobject_initialized:
            return
        try:
            from PyQt6.QtWidgets import QApplication

            if QApplication.instance() is not None:
                super().__init__()
                self._qobject_initialized = True
        except Exception:
            self._qobject_initialized = False

    def _ensure_qobject_initialized(self):
        if not self._qobject_initialized:
            self._try_init_qobject()

    @property
    def selected_objects(self) -> List[Any]:
        """EditorContext.selected_objects。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._selected_objects.copy()

    @property
    def primary_selection(self) -> Optional[Any]:
        """EditorContext.primary_selection。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._selected_objects[0] if self._selected_objects else None

    def set_selection(self, objects: List[Any]):
        """EditorContext.set_selection。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        self._selected_objects = objects.copy() if objects else []
        self.selection_changed.emit(self._selected_objects)

    def add_selection(self, obj: Any):
        """EditorContext.add_selection。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        if obj not in self._selected_objects:
            self._selected_objects.append(obj)
            self.selection_changed.emit(self._selected_objects)

    def remove_selection(self, obj: Any):
        """EditorContext.remove_selection。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        if obj in self._selected_objects:
            self._selected_objects.remove(obj)
            self.selection_changed.emit(self._selected_objects)

    def clear_selection(self):
        """EditorContext.clear_selection。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        self._selected_objects.clear()
        self.selection_changed.emit(self._selected_objects)

    def is_selected(self, obj: Any) -> bool:
        """EditorContext.is_selected。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return obj in self._selected_objects

    @property
    def current_project_path(self) -> Optional[str]:
        """EditorContext.current_project_path。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._current_project_path

    @current_project_path.setter
    def current_project_path(self, path: Optional[str]):
        """EditorContext.current_project_path。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        if self._current_project_path != path:
            self._current_project_path = path
            self.project_changed.emit(path or "")

    @property
    def project_modified(self) -> bool:
        """EditorContext.project_modified。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._project_modified

    @project_modified.setter
    def project_modified(self, modified: bool):
        """EditorContext.project_modified。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        if self._project_modified != modified:
            self._project_modified = modified
            self.project_modified_changed.emit(modified)

    @property
    def current_mode(self) -> EditorMode:
        """EditorContext.current_mode。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._current_mode

    @current_mode.setter
    def current_mode(self, mode: EditorMode):
        """EditorContext.current_mode。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._ensure_qobject_initialized()
        if self._current_mode != mode:
            self._current_mode = mode
            self.mode_changed.emit(mode)

    def set_mode(self, mode: EditorMode) -> None:
        """Set the editor/player mode via the public mode property."""
        self.current_mode = mode

    @property
    def current_scene(self) -> Optional[Any]:
        """EditorContext.current_scene。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._current_scene

    @current_scene.setter
    def current_scene(self, scene: Optional[Any]):
        """EditorContext.current_scene。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._current_scene = scene

    @property
    def canvas(self) -> Optional[Any]:
        """EditorContext.canvas。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._canvas

    @canvas.setter
    def canvas(self, canvas: Optional[Any]):
        """EditorContext.canvas。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._canvas = canvas

    def reset(self):
        """EditorContext.reset。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.clear_selection()
        self.current_project_path = None
        self.project_modified = False
        self.current_mode = EditorMode.EDIT
        self._current_scene = None


def get_existing_editor_context() -> Optional[EditorContext]:
    """Return the existing editor context without creating a QObject singleton."""
    return EditorContext._instance


def get_editor_context(
    capability_registry: object | None = None,
) -> EditorContext:
    """Return the singleton; first composition may bind the L1 registry."""
    return EditorContext(capability_registry)
