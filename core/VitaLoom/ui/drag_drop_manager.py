# -*- coding: utf-8 -*-
"""全局拖放 MIME 与 SceneViewport.dropEvent 协作。

排错: 资源拖入无效 → DragDataType 与 library_browser 载荷一致。
"""

from typing import Optional, Any, Callable, Dict
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QMimeData, Qt
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QWidget


class DragDataType(Enum):
    """拖放数据类型"""
    COMPONENT = "component"  # 组件
    ORGANISM = "organism"    # 生物体
    NODE = "node"            # 节点
    FILE = "file"            # 文件
    CUSTOM = "custom"        # 自定义


class DragDropManager(QObject):
    """职责: 注册拖放类型与解析拖入 payload 的单一入口。"""
    """拖放管理器单例"""
    
    _instance: Optional['DragDropManager'] = None
    
    # 信号
    drag_started = pyqtSignal(str, object)  # (data_type, data)
    drag_ended = pyqtSignal(bool)  # (success)
    drop_occurred = pyqtSignal(str, object, object)  # (data_type, data, target)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """DragDropManager.__init__。

        
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
        
        # 当前拖放数据
        self.current_drag_data: Optional[Any] = None
        self.current_drag_type: Optional[DragDataType] = None
        
        # 拖放处理器注册表: data_type -> handler
        self.drop_handlers: Dict[str, Callable] = {}
        
        # MIME类型前缀
        self.MIME_PREFIX = "application/x-vitaloom-"
    
    def start_drag(
        self,
        source_widget: QWidget,
        data_type: DragDataType,
        data: Any,
        pixmap: Optional[Any] = None
    ) -> Qt.DropAction:
        """开始拖放操作。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.current_drag_data = data
        self.current_drag_type = data_type
        
        # 创建MIME数据
        mime_data = QMimeData()
        mime_type = f"{self.MIME_PREFIX}{data_type.value}"
        
        # 将数据序列化为字符串
        if isinstance(data, str):
            mime_data.setData(mime_type, data.encode('utf-8'))
        elif isinstance(data, dict):
            import json
            mime_data.setData(mime_type, json.dumps(data).encode('utf-8'))
        else:
            mime_data.setText(str(data))
        
        # 创建拖放对象
        drag = QDrag(source_widget)
        drag.setMimeData(mime_data)
        
        if pixmap:
            drag.setPixmap(pixmap)
        
        # 发射拖放开始信号
        self.drag_started.emit(data_type.value, data)
        
        # 执行拖放
        drop_action = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        
        # 发射拖放结束信号
        success = drop_action != Qt.DropAction.IgnoreAction
        self.drag_ended.emit(success)
        
        # 清理
        self.current_drag_data = None
        self.current_drag_type = None
        
        return drop_action
    
    def register_drop_handler(self, data_type: str, handler: Callable):
        """注册拖放处理器。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.drop_handlers[data_type] = handler
    
    def unregister_drop_handler(self, data_type: str):
        """注销拖放处理器。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if data_type in self.drop_handlers:
            del self.drop_handlers[data_type]
    
    def handle_drop(
        self,
        mime_data: QMimeData,
        target_widget: QWidget,
        drop_position: Optional[Any] = None
    ) -> bool:
        """处理拖放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        # 检查MIME数据类型
        for format_str in mime_data.formats():
            if format_str.startswith(self.MIME_PREFIX):
                # 提取数据类型
                data_type = format_str[len(self.MIME_PREFIX):]
                
                # 获取数据
                raw_data = mime_data.data(format_str).data()
                
                try:
                    # 尝试解码数据
                    data_str = raw_data.decode('utf-8')
                    
                    # 尝试解析JSON
                    try:
                        import json
                        data = json.loads(data_str)
                    except:
                        data = data_str
                except:
                    data = raw_data
                
                # 调用处理器
                if data_type in self.drop_handlers:
                    handler = self.drop_handlers[data_type]
                    success = handler(data, target_widget, drop_position)
                    
                    if success:
                        self.drop_occurred.emit(data_type, data, target_widget)
                    
                    return success
        
        return False
    
    def can_accept_drop(self, mime_data: QMimeData, data_type: Optional[str] = None) -> bool:
        """检查是否可以接受拖放。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if data_type:
            mime_type = f"{self.MIME_PREFIX}{data_type}"
            return mime_data.hasFormat(mime_type)
        else:
            # 检查是否有任何VitaLoom格式
            for format_str in mime_data.formats():
                if format_str.startswith(self.MIME_PREFIX):
                    return True
            return False
    
    def get_current_drag_data(self) -> Optional[tuple]:
        """获取当前拖放数据。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self.current_drag_data and self.current_drag_type:
            return (self.current_drag_type, self.current_drag_data)
        return None


def get_drag_drop_manager() -> DragDropManager:
    """获取拖放管理器单例"""
    return DragDropManager()
