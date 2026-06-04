# -*- coding: utf-8 -*-
"""场景编辑工具链：选择/移动/连线/平移/缩放与 SceneViewport 协作。

排错: 工具无响应 → ToolManager.active_tool 与视口鼠标模式。
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QPointF

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus


class ToolType(Enum):
    """工具类型"""
    SELECT = "select"      # 选择工具
    MOVE = "move"         # 移动工具
    CONNECT = "connect"   # 连接工具
    PAN = "pan"           # 平移工具
    ZOOM = "zoom"         # 缩放工具


class BaseTool(QObject):
    """工具基类"""
    
    tool_activated = pyqtSignal()
    tool_deactivated = pyqtSignal()
    
    def __init__(self, tool_type: ToolType):
        """BaseTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__()
        self.tool_type = tool_type
        self.active = False
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
    
    def activate(self):
        """激活工具。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.active = True
        self.tool_activated.emit()
        self.signal_bus.emit_tool_changed(self.tool_type.value)
    
    def deactivate(self):
        """停用工具。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.active = False
        self.tool_deactivated.emit()
    
    def mouse_press(self, viewport: Any, event: Any) -> bool:
        """处理鼠标按下事件，返回True表示已处理。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return False
    
    def mouse_move(self, viewport: Any, event: Any) -> bool:
        """处理鼠标移动事件，返回True表示已处理。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return False
    
    def mouse_release(self, viewport: Any, event: Any) -> bool:
        """处理鼠标释放事件，返回True表示已处理。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return False
    
    def key_press(self, viewport: Any, event: Any) -> bool:
        """处理按键事件，返回True表示已处理。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return False
    
    def draw(self, viewport: Any, painter: Any):
        """绘制工具相关的视觉反馈。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        pass


class SelectTool(BaseTool):
    """选择工具"""
    
    def __init__(self):
        """SelectTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(ToolType.SELECT)
        self.selection_start: Optional[QPointF] = None
        self.selection_rect: Optional[Any] = None
    
    def mouse_press(self, viewport: Any, event: Any) -> bool:
        """处理鼠标按下。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton:
            world_pos = viewport._screen_to_world(event.pos())
            self.selection_start = world_pos
            return True
        return False
    
    def mouse_move(self, viewport: Any, event: Any) -> bool:
        """处理鼠标移动。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.selection_start:
            world_pos = viewport._screen_to_world(event.pos())
            from PyQt6.QtCore import QRectF
            self.selection_rect = QRectF(self.selection_start, world_pos)
            viewport.update()
            return True
        return False
    
    def mouse_release(self, viewport: Any, event: Any) -> bool:
        """处理鼠标释放。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.selection_start and self.selection_rect:
            # 框选逻辑
            selected_nodes = []
            for node in viewport.nodes:
                node_pos = QPointF(node.x, node.y)
                if self.selection_rect.contains(node_pos):
                    selected_nodes.append(node)
            
            if selected_nodes:
                viewport.editor_context.set_selection(selected_nodes)
            
            self.selection_start = None
            self.selection_rect = None
            viewport.update()
            return True
        return False
    
    def draw(self, viewport: Any, painter: Any):
        """绘制选择框。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.selection_rect:
            from PyQt6.QtGui import QPen, QColor
            pen = QPen(QColor(100, 150, 255), 2)
            painter.setPen(pen)
            painter.setBrush(QColor(100, 150, 255, 30))
            painter.drawRect(self.selection_rect)


class MoveTool(BaseTool):
    """移动工具"""
    
    def __init__(self):
        """MoveTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(ToolType.MOVE)
        self.dragging = False
        self.drag_start: Optional[QPointF] = None


class ConnectTool(BaseTool):
    """连接工具"""
    
    def __init__(self):
        """ConnectTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(ToolType.CONNECT)
        self.connecting = False
        self.connect_start_node: Optional[Any] = None


class PanTool(BaseTool):
    """平移工具"""
    
    def __init__(self):
        """PanTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(ToolType.PAN)
        self.panning = False
        self.pan_start: Optional[QPointF] = None
    
    def mouse_press(self, viewport: Any, event: Any) -> bool:
        """处理鼠标按下。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and 
            event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.panning = True
            self.pan_start = event.pos()
            return True
        return False
    
    def mouse_move(self, viewport: Any, event: Any) -> bool:
        """处理鼠标移动。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.panning and self.pan_start:
            delta = event.pos() - self.pan_start
            viewport.pan_offset += delta
            self.pan_start = event.pos()
            viewport.update()
            return True
        return False
    
    def mouse_release(self, viewport: Any, event: Any) -> bool:
        """处理鼠标释放。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.panning:
            self.panning = False
            self.pan_start = None
            return True
        return False


class ZoomTool(BaseTool):
    """缩放工具"""
    
    def __init__(self):
        """ZoomTool.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(ToolType.ZOOM)
    
    def wheel_event(self, viewport: Any, event: Any) -> bool:
        """处理滚轮事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        new_zoom = viewport.zoom_level * zoom_factor
        viewport.set_zoom(new_zoom)
        return True


class ToolManager(QObject):
    """职责: 注册并切换 BaseTool 实例，广播 tool_changed。"""
    """工具管理器 - 管理编辑器工具"""
    
    tool_changed = pyqtSignal(ToolType)  # 工具变化信号
    
    _instance: Optional['ToolManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ToolManager.__init__。

        
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
        
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        # 注册所有工具
        self.tools: Dict[ToolType, BaseTool] = {
            ToolType.SELECT: SelectTool(),
            ToolType.MOVE: MoveTool(),
            ToolType.CONNECT: ConnectTool(),
            ToolType.PAN: PanTool(),
            ToolType.ZOOM: ZoomTool(),
        }
        
        # 当前活动工具
        self._current_tool: ToolType = ToolType.SELECT
        self.tools[self._current_tool].activate()
        
        # 工具选项
        self.tool_options: Dict[str, Any] = {
            'snap_to_grid': False,
            'grid_size': 20,
            'snap_distance': 10,
            'show_grid': True,
        }
    
    def set_tool(self, tool_type: ToolType):
        """切换工具。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self._current_tool != tool_type:
            # 停用当前工具
            self.tools[self._current_tool].deactivate()
            
            # 激活新工具
            self._current_tool = tool_type
            self.tools[self._current_tool].activate()
            
            # 发送信号
            self.tool_changed.emit(tool_type)
            self.signal_bus.emit_tool_changed(tool_type.value)
    
    def get_current_tool(self) -> BaseTool:
        """获取当前工具。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.tools[self._current_tool]
    
    def get_tool(self, tool_type: ToolType) -> BaseTool:
        """获取指定工具。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.tools.get(tool_type)
    
    def set_tool_option(self, option: str, value: Any):
        """设置工具选项。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.tool_options[option] = value
    
    def get_tool_option(self, option: str, default: Any = None) -> Any:
        """获取工具选项。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self.tool_options.get(option, default)
    
    def snap_to_grid(self, pos: QPointF) -> QPointF:
        """吸附到网格。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.tool_options.get('snap_to_grid', False):
            grid_size = self.tool_options.get('grid_size', 20)
            snapped_x = round(pos.x() / grid_size) * grid_size
            snapped_y = round(pos.y() / grid_size) * grid_size
            return QPointF(snapped_x, snapped_y)
        return pos
    
    def snap_to_object(self, pos: QPointF, objects: list, snap_distance: float = None) -> QPointF:
        """吸附到对象。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if snap_distance is None:
            snap_distance = self.tool_options.get('snap_distance', 10)
        
        min_distance = float('inf')
        snapped_pos = pos
        
        for obj in objects:
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                obj_pos = QPointF(obj.x, obj.y)
                distance = ((pos.x() - obj_pos.x()) ** 2 + (pos.y() - obj_pos.y()) ** 2) ** 0.5
                if distance < min_distance and distance < snap_distance:
                    min_distance = distance
                    snapped_pos = obj_pos
        
        return snapped_pos


def get_tool_manager() -> ToolManager:
    """获取工具管理器单例"""
    return ToolManager()
