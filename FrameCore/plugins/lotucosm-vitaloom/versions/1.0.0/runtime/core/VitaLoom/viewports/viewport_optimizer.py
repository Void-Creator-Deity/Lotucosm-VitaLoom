# -*- coding: utf-8 -*-
"""视口绘制优化：可见区裁剪与增量刷新辅助。

排错: 卡顿 → 检查 visible_rect 与节点数量阈值。
"""

from typing import List, Set, Optional, Any
from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QPainter

from core.VitaLoom.core.editor_context import get_editor_context


class ViewportOptimizer:
    """职责: 为大场景视口提供剔除与批绘制策略钩子。"""
    """视口优化器 - 优化视口渲染性能"""
    
    def __init__(self):
        """ViewportOptimizer.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.editor_context = get_editor_context()
        self._visible_objects: Set[Any] = set()
        self._dirty_objects: Set[Any] = set()
        self._last_viewport_rect: Optional[QRectF] = None
    
    def cull_objects(self, objects: List[Any], viewport_rect: QRectF) -> List[Any]:
        """对象剔除 - 只返回视口内可见的对象。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        visible = []
        
        for obj in objects:
            if self._is_object_visible(obj, viewport_rect):
                visible.append(obj)
        
        self._visible_objects = set(visible)
        self._last_viewport_rect = viewport_rect
        
        return visible
    
    def _is_object_visible(self, obj: Any, viewport_rect: QRectF) -> bool:
        """检查对象是否在视口内可见"""
        if not hasattr(obj, 'x') or not hasattr(obj, 'y'):
            return True  # 如果没有位置信息，假设可见
        
        obj_pos = QPointF(obj.x, obj.y)
        
        # 获取对象边界（如果有radius属性）
        if hasattr(obj, 'radius'):
            radius = obj.radius
            obj_rect = QRectF(
                obj_pos.x() - radius,
                obj_pos.y() - radius,
                radius * 2,
                radius * 2
            )
        else:
            # 默认边界
            obj_rect = QRectF(obj_pos.x() - 10, obj_pos.y() - 10, 20, 20)
        
        # 检查是否与视口相交
        return viewport_rect.intersects(obj_rect)
    
    def mark_dirty(self, obj: Any):
        """标记对象为脏（需要重绘）。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._dirty_objects.add(obj)
    
    def clear_dirty(self):
        """清除所有脏标记。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._dirty_objects.clear()
    
    def get_dirty_objects(self) -> Set[Any]:
        """获取所有脏对象。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._dirty_objects.copy()
    
    def batch_draw_nodes(self, painter: QPainter, nodes: List[Any], viewport_rect: QRectF):
        """批量绘制节点 - 优化绘制性能。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        # 按类型分组节点
        nodes_by_type: dict = {}
        for node in nodes:
            if self._is_object_visible(node, viewport_rect):
                node_type = getattr(node, 'type', 'default')
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append(node)
        
        # 按类型批量绘制
        for node_type, type_nodes in nodes_by_type.items():
            for node in type_nodes:
                if hasattr(node, 'draw'):
                    node.draw(painter)
    
    def batch_draw_connections(self, painter: QPainter, connections: List[Any], viewport_rect: QRectF):
        """批量绘制连接 - 优化绘制性能。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        # 只绘制视口内的连接
        for connection in connections:
            if self._is_connection_visible(connection, viewport_rect):
                if hasattr(connection, 'draw'):
                    connection.draw(painter)
    
    def _is_connection_visible(self, connection: Any, viewport_rect: QRectF) -> bool:
        """检查连接是否在视口内可见"""
        if not hasattr(connection, 'start_node') or not hasattr(connection, 'end_node'):
            return True
        
        start_pos = QPointF(connection.start_node.x, connection.start_node.y)
        end_pos = QPointF(connection.end_node.x, connection.end_node.y)
        
        # 检查连接的两个端点是否至少有一个在视口内
        return (viewport_rect.contains(start_pos) or 
                viewport_rect.contains(end_pos) or
                self._line_intersects_rect(start_pos, end_pos, viewport_rect))
    
    def _line_intersects_rect(self, p1: QPointF, p2: QPointF, rect: QRectF) -> bool:
        """检查线段是否与矩形相交"""
        # 简单的边界框检查
        min_x = min(p1.x(), p2.x())
        max_x = max(p1.x(), p2.x())
        min_y = min(p1.y(), p2.y())
        max_y = max(p1.y(), p2.y())
        
        line_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        return rect.intersects(line_rect)
    
    def incremental_update(self, viewport: Any, force_full: bool = False):
        """增量更新 - 只更新变化的部分。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if force_full or not self._last_viewport_rect:
            # 完整更新
            viewport.update()
            self.clear_dirty()
        else:
            # 增量更新 - 只更新脏对象
            if self._dirty_objects:
                # 计算需要更新的区域
                update_rect = None
                for obj in self._dirty_objects:
                    if hasattr(obj, 'x') and hasattr(obj, 'y'):
                        obj_pos = QPointF(obj.x, obj.y)
                        radius = getattr(obj, 'radius', 20)
                        obj_rect = QRectF(
                            obj_pos.x() - radius - 5,
                            obj_pos.y() - radius - 5,
                            (radius + 5) * 2,
                            (radius + 5) * 2
                        )
                        if update_rect is None:
                            update_rect = obj_rect
                        else:
                            update_rect = update_rect.united(obj_rect)
                
                if update_rect:
                    # 转换为屏幕坐标并更新
                    # 这里需要视口提供坐标转换方法
                    viewport.update()
                
                self.clear_dirty()


def get_viewport_optimizer() -> ViewportOptimizer:
    """获取视口优化器实例"""
    return ViewportOptimizer()
