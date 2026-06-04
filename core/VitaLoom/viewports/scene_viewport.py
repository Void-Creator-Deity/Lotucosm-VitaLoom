# -*- coding: utf-8 -*-
"""场景编辑视口：节点图、连线、命令栈与 .pond 数据双向同步。

架构数据流::

    load_scene_data ← SceneManager → paintEvent / CommandStack

排错: 见 core/VitaLoom/README.md「场景重载」「撤销」
"""

import os
from typing import List, Optional, Any, Dict
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPaintEvent, QMouseEvent, QWheelEvent, QContextMenuEvent, QKeyEvent
)
from PyQt6.QtWidgets import QWidget, QMenu, QToolBar, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

# 导入节点和连接线类
from core.VitaLoom.tools.selection_tool import Node, ConnectionLine

# 导入命令模式
from core.VitaLoom.commands.command import (
    CommandStack, AddNodeCommand, DeleteNodeCommand,
    MoveNodeCommand, CreateConnectionCommand, DeleteConnectionCommand
)

# 导入编辑器上下文
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus, SignalType
from core.VitaLoom.core.logger import get_logger


logger = get_logger("SceneViewport")


class SceneViewport(QWidget):
    """职责: 编辑模式下的 2D 节点画布（平移/缩放/框选/连线）。
    时机: 作为 IViewportProvider 嵌入 LayoutManager；场景加载后 `load_scene_data`。
    不变量: 修改经 CommandStack；`get_scene_data` 与 SceneManager.save 字段契约一致。
    排错: 空白画布 → scene_loaded 回调；撤销无效 → command_stack 是否 execute。
    """

    # 自定义信号
    updateRequest = pyqtSignal()
    projectModified = pyqtSignal()
    commandExecuted = pyqtSignal()

    def __init__(self):
        """SceneViewport.__init__。

        
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
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # 获取编辑器上下文和信号总线
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        # 父窗口引用
        self.parent_widget: Optional[Any] = None

        # 节点和连接线
        self.nodes: List[Node] = []
        self.connections: List[ConnectionLine] = []

        # 交互状态
        self.selected_node: Optional[Node] = None
        self.selected_nodes: List[Node] = []
        self.hovered_node: Optional[Node] = None
        self.hovered_connection: Optional[ConnectionLine] = None
        self.dragging = False
        self.drag_start = QPoint()
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self.connecting = False
        self.connect_start_node: Optional[Node] = None
        self.connect_temp_pos = QPoint()
        
        # 相机控制状态（参考 Unity/Godot）
        self.panning = False  # 平移状态
        self.pan_start = QPoint()  # 平移起始点
        self.box_selecting = False  # 框选状态
        self.box_select_start = QPoint()  # 框选起始点
        self.box_select_end = QPoint()  # 框选结束点
        
        # 视图状态
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.pan_offset = QPointF(0, 0)
        self.show_grid = True
        self.snap_to_grid = False
        self.grid_size = 20
        self.show_gizmos = True  # 显示操作手柄
        self.show_viewport_info = True  # 显示视口信息

        # 命令栈
        self.command_stack = CommandStack()

        # 顶部工具栏 + 画布区域（stretch 以下为场景绘制区）
        self._toolbar_container = QWidget(self)
        tb_layout = QHBoxLayout(self._toolbar_container)
        tb_layout.setContentsMargins(4, 4, 4, 4)
        self._populate_scene_toolbar(tb_layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._toolbar_container)
        outer.addStretch(1)

        # 连接编辑器上下文信号
        self.editor_context.selection_changed.connect(self._on_context_selection_changed)  # type: ignore
        
        # 不要在这里订阅事件，交由 SceneViewportPlugin 统一管理
        # 这可以避免双重创建或双重加载的问题
        
        # 如果没有场景数据，不要自动创建默认节点（用户要求空白）
        # if not self.nodes:
        #     self._create_default_nodes()
        #     self.update()
        
        # 启用拖拽支持
        self.setAcceptDrops(True)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _chrome_top(self) -> int:
        """顶部工具栏占用高度（用于坐标映射与裁剪）。"""
        if hasattr(self, "_toolbar_container") and self._toolbar_container is not None:
            h = self._toolbar_container.height()
            if h > 0:
                return h
            return max(self._toolbar_container.sizeHint().height(), 28)
        return 0

    def _populate_scene_toolbar(self, toolbar_layout: QHBoxLayout) -> None:
        """填充场景视口顶部工具栏。"""
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(lambda: self.set_zoom(self.zoom_level * 1.2))  # type: ignore
        toolbar_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(lambda: self.set_zoom(self.zoom_level * 0.8))  # type: ignore
        toolbar_layout.addWidget(zoom_out_btn)

        zoom_reset_btn = QPushButton(self._t("scene_viewport.toolbar.reset_zoom", "重置"))
        zoom_reset_btn.setMaximumWidth(50)
        zoom_reset_btn.clicked.connect(lambda: self.set_zoom(1.0))  # type: ignore
        toolbar_layout.addWidget(zoom_reset_btn)

        toolbar_layout.addStretch()

        grid_btn = QPushButton(self._t("scene_viewport.toolbar.grid", "网格"))
        grid_btn.setCheckable(True)
        grid_btn.setChecked(True)
        grid_btn.toggled.connect(self._toggle_grid)  # type: ignore
        toolbar_layout.addWidget(grid_btn)

        snap_btn = QPushButton(self._t("scene_viewport.toolbar.snap", "吸附"))
        snap_btn.setCheckable(True)
        snap_btn.toggled.connect(self._toggle_snap)  # type: ignore
        toolbar_layout.addWidget(snap_btn)

    def set_zoom(self, zoom: float):
        """设置缩放级别。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, zoom))
        self.update()

    def _toggle_grid(self, checked: bool):
        """切换网格显示"""
        self.show_grid = checked
        self.update()

    def _toggle_snap(self, checked: bool):
        """切换吸附到网格"""
        self.snap_to_grid = checked

    def _on_context_selection_changed(self, objects: List[Any]):
        """编辑器上下文选中对象变化处理"""
        # 更新画布选择
        self.selected_nodes = [obj for obj in objects if isinstance(obj, Node)]
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
        else:
            self.selected_node = None
        self.update()

    def set_parent(self, parent: Optional[Any]):
        """设置父窗口引用。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.parent_widget = parent

    def _create_default_nodes(self):
        """创建默认节点（确保编辑器首次启动不空白）"""
        # 清空现有节点
        self.nodes.clear()
        self.connections.clear()
        
        # 获取视口中心位置
        center_x, center_y = 400, 300

        # 创建生物体节点（细胞膜）- 作为根节点
        organism = Node("organism_1", center_x, center_y, "organism")
        if hasattr(organism, 'radius'):
            organism.radius = 50
        self.nodes.append(organism)

        # 创建中枢管理器节点
        central_brain = Node("central_1", center_x, center_y, "central_brain")
        if hasattr(central_brain, 'radius'):
            central_brain.radius = 30
        self.nodes.append(central_brain)

        # 创建传感器节点
        sensor1 = Node("sensor_1", center_x - 120, center_y - 60, "sensor")
        if hasattr(sensor1, 'radius'):
            sensor1.radius = 20
        sensor2 = Node("sensor_2", center_x + 120, center_y - 60, "sensor")
        if hasattr(sensor2, 'radius'):
            sensor2.radius = 20
        self.nodes.extend([sensor1, sensor2])

        # 创建效应器节点
        actuator1 = Node("actuator_1", center_x - 120, center_y + 60, "actuator")
        if hasattr(actuator1, 'radius'):
            actuator1.radius = 20
        actuator2 = Node("actuator_2", center_x + 120, center_y + 60, "actuator")
        if hasattr(actuator2, 'radius'):
            actuator2.radius = 20
        self.nodes.extend([actuator1, actuator2])
        
        # 创建一些连接
        try:
            connection1 = ConnectionLine(central_brain, sensor1)
            connection2 = ConnectionLine(central_brain, sensor2)
            connection3 = ConnectionLine(central_brain, actuator1)
            connection4 = ConnectionLine(central_brain, actuator2)
            self.connections.extend([connection1, connection2, connection3, connection4])
        except Exception as e:
            logger.exception("创建默认连接失败: %s", e)
        
        logger.info("已创建默认节点（编辑器首次启动）")

        # 创建连接线
        self.connections.append(ConnectionLine(sensor1, central_brain))
        self.connections.append(ConnectionLine(sensor2, central_brain))
        self.connections.append(ConnectionLine(central_brain, actuator1))
        self.connections.append(ConnectionLine(central_brain, actuator2))

    # === 绘制: 网格、节点、连线、框选 ==========================================
    def paintEvent(self, event: Optional[QPaintEvent]):
        """绘制画布内容。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        chrome = self._chrome_top()

        # 检查是否有场景加载
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        sm = get_scene_manager()
        current_scene = sm.get_current_scene_path()

        if not current_scene:
            # 绘制未打开场景的提示信息
            self._draw_background(painter)
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.setFont(self.font())
            hint_rect = self.rect().adjusted(0, chrome, 0, 0) if chrome > 0 else self.rect()
            painter.drawText(
                hint_rect,
                Qt.AlignmentFlag.AlignCenter,
                self._t(
                    "scene_viewport.hint.open_scene",
                    "未打开场景\n\n请在项目面板中双击 .pond 文件打开",
                ),
            )
            return

        # 世界坐标：先下移画布区，再平移/缩放，与 _screen_to_world 一致
        painter.save()
        painter.translate(0, chrome)
        painter.setClipRect(0, 0, self.width(), max(1, self.height() - chrome))
        painter.translate(self.pan_offset)
        painter.scale(self.zoom_level, self.zoom_level)

        # 绘制背景
        self._draw_background(painter)

        # 绘制网格
        if self.show_grid:
            self._draw_grid(painter)

        # 绘制连接线
        for connection in self.connections:
            if connection == self.hovered_connection:
                # 高亮悬停的连接线
                glow_pen = QPen(QColor(255, 255, 0, 100), connection.width + 6)
                painter.setPen(glow_pen)
                painter.drawLine(
                    QPointF(float(connection.start_node.x), float(connection.start_node.y)),
                    QPointF(float(connection.end_node.x), float(connection.end_node.y))
                )
            connection.draw(painter)

        # 绘制临时连接线
        if self.connecting and self.connect_start_node:
            pen = QPen(QColor(255, 255, 255, 150), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            world_pos = self._screen_to_world(self.connect_temp_pos)
            painter.drawLine(
                QPointF(float(self.connect_start_node.x), float(self.connect_start_node.y)),
                world_pos
            )

        # 绘制框选矩形
        if self.box_selecting:
            self._draw_box_selection(painter)
        
        # 绘制节点
        for node in self.nodes:
            is_selected = node in self.selected_nodes
            is_hovered = node == self.hovered_node

            if is_selected:
                # 绘制选中效果
                glow_brush = QBrush(QColor(255, 255, 255, 80))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                rect = QRectF(
                    node.x - node.radius - 10,
                    node.y - node.radius - 10,
                    node.radius * 2 + 20,
                    node.radius * 2 + 20
                )
                painter.drawEllipse(rect)

                # 绘制选中边框
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                rect = QRectF(
                    node.x - node.radius - 5,
                    node.y - node.radius - 5,
                    node.radius * 2 + 10,
                    node.radius * 2 + 10
                )
                painter.drawEllipse(rect)
            elif is_hovered:
                # 绘制悬停效果
                glow_brush = QBrush(QColor(255, 255, 255, 50))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                rect = QRectF(
                    node.x - node.radius - 8,
                    node.y - node.radius - 8,
                    node.radius * 2 + 16,
                    node.radius * 2 + 16
                )
                painter.drawEllipse(rect)

            # 绘制节点
            node.draw(painter)

        # 为生物体节点绘制细胞膜效果
        for node in self.nodes:
            if node.type == "organism":
                membrane_radius = int(node.radius * 3)
                center_x, center_y = int(node.x), int(node.y)

                # 绘制细胞膜外环
                outer_rect = QRect(center_x - membrane_radius - 2, center_y - membrane_radius - 2,
                                  membrane_radius * 2 + 4, membrane_radius * 2 + 4)
                outer_gradient = QLinearGradient(outer_rect.topLeft().x(), outer_rect.topLeft().y(),
                                               outer_rect.bottomRight().x(), outer_rect.bottomRight().y())
                outer_gradient.setColorAt(0, QColor(100, 150, 255, 50))
                outer_gradient.setColorAt(1, QColor(100, 150, 255, 0))
                painter.setBrush(QBrush(outer_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(outer_rect)

                # 绘制细胞膜主体
                membrane_pen = QPen()
                membrane_gradient = QLinearGradient(center_x - membrane_radius, center_y - membrane_radius,
                                                 center_x + membrane_radius, center_y + membrane_radius)
                membrane_gradient.setColorAt(0, QColor(100, 150, 255, 255))
                membrane_gradient.setColorAt(1, QColor(50, 100, 200, 255))
                membrane_pen.setBrush(membrane_gradient)
                membrane_pen.setWidth(3)
                membrane_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(membrane_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                # 确保所有参数都是 int 类型
                x1 = int(center_x - membrane_radius)
                y1 = int(center_y - membrane_radius)
                w1 = int(membrane_radius * 2)
                h1 = int(membrane_radius * 2)
                painter.drawEllipse(x1, y1, w1, h1)

                # 绘制细胞膜内环
                inner_pen = QPen(QColor(150, 200, 255, 150), 1)
                painter.setPen(inner_pen)
                x2 = int(center_x - membrane_radius + 4)
                y2 = int(center_y - membrane_radius + 4)
                w2 = int((membrane_radius - 4) * 2)
                h2 = int((membrane_radius - 4) * 2)
                painter.drawEllipse(x2, y2, w2, h2)
        
        painter.restore()

        # 绘制视口信息（参考 Unity/Godot）
        if self.show_viewport_info:
            self._draw_viewport_info(painter)

    def _draw_box_selection(self, painter: QPainter):
        """绘制框选矩形（屏幕坐标，不改变外部 painter 变换栈）"""
        painter.save()
        painter.resetTransform()

        rect = QRectF(
            min(self.box_select_start.x(), self.box_select_end.x()),
            min(self.box_select_start.y(), self.box_select_end.y()),
            abs(self.box_select_end.x() - self.box_select_start.x()),
            abs(self.box_select_end.y() - self.box_select_start.y())
        )

        fill_brush = QBrush(QColor(100, 150, 255, 30))
        painter.setBrush(fill_brush)
        painter.setPen(QPen(QColor(100, 150, 255, 200), 2, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

        painter.restore()
    
    def _draw_viewport_info(self, painter: QPainter):
        """绘制视口信息（坐标、缩放级别等）"""
        # 恢复变换以绘制屏幕坐标
        painter.resetTransform()
        
        try:
            # 获取鼠标位置对应的世界坐标
            from PyQt6.QtWidgets import QApplication
            mouse_pos = self.mapFromGlobal(QApplication.cursor().pos())
            if self.rect().contains(mouse_pos):
                world_pos = self._screen_to_world(mouse_pos)
                
                # 绘制信息文本
                info_text = f"缩放: {self.zoom_level:.2f}x | 坐标: ({world_pos.x():.1f}, {world_pos.y():.1f})"
                if self.selected_nodes:
                    info_text += f" | 选中: {len(self.selected_nodes)}"
                
                # 背景
                font_metrics = painter.fontMetrics()
                text_rect = font_metrics.boundingRect(info_text)
                text_rect.adjust(-4, -2, 4, 2)
                text_rect.moveBottomLeft(QPoint(10, self.height() - 10))
                
                bg_brush = QBrush(QColor(0, 0, 0, 180))
                painter.setBrush(bg_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(text_rect)
                
                # 文本
                painter.setPen(QPen(QColor(255, 255, 255, 255)))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, info_text)
        except:
            # 如果获取鼠标位置失败，只显示缩放级别
            info_text = f"缩放: {self.zoom_level:.2f}x"
            if self.selected_nodes:
                info_text += f" | 选中: {len(self.selected_nodes)}"
            
            font_metrics = painter.fontMetrics()
            text_rect = font_metrics.boundingRect(info_text)
            text_rect.adjust(-4, -2, 4, 2)
            text_rect.moveBottomLeft(QPoint(10, self.height() - 10))
            
            bg_brush = QBrush(QColor(0, 0, 0, 180))
            painter.setBrush(bg_brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(text_rect)
            
            painter.setPen(QPen(QColor(255, 255, 255, 255)))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, info_text)
        
    def _finish_box_selection(self):
        """完成框选操作"""
        if not self.box_selecting:
            return
        
        # 计算框选区域（世界坐标）
        world_start = self._screen_to_world(self.box_select_start)
        world_end = self._screen_to_world(self.box_select_end)
        
        box_rect = QRectF(
            min(world_start.x(), world_end.x()),
            min(world_start.y(), world_end.y()),
            abs(world_end.x() - world_start.x()),
            abs(world_end.y() - world_start.y())
        )
        
        # 选择框内的所有节点
        selected = []
        for node in self.nodes:
            node_rect = QRectF(
                node.x - node.radius,
                node.y - node.radius,
                node.radius * 2,
                node.radius * 2
            )
            if box_rect.intersects(node_rect):
                selected.append(node)
        
        # 更新选择（框选默认替换选择，除非按住 Ctrl/Shift）
        from PyQt6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl: 添加到选择
            for node in selected:
                if node not in self.selected_nodes:
                    self.selected_nodes.append(node)
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Shift: 添加到选择
            for node in selected:
                if node not in self.selected_nodes:
                    self.selected_nodes.append(node)
        else:
            # 替换选择
            self.selected_nodes = selected
        
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
            self.editor_context.set_selection(self.selected_nodes)
        else:
            self.selected_node = None
            self.editor_context.clear_selection()
        
        self.update()
        self.updateRequest.emit()

    def _draw_background(self, painter: QPainter):
        """绘制背景"""
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

    def _draw_grid(self, painter: QPainter):
        """绘制网格（改进的网格渲染，参考 Unity/Godot）"""
        # 根据缩放级别自适应网格大小
        effective_grid_size = self.grid_size
        grid_alpha = 255
        
        # 如果缩放级别太小，显示更粗的网格
        if self.zoom_level < 0.5:
            effective_grid_size = self.grid_size * 4
            grid_alpha = 200
        elif self.zoom_level < 1.0:
            effective_grid_size = self.grid_size * 2
            grid_alpha = 220
        else:
            effective_grid_size = self.grid_size
            grid_alpha = 255
        
        # 主网格颜色（较暗）
        main_grid_color = QColor(60, 60, 70, grid_alpha)
        main_pen = QPen(main_grid_color, 0.5)
        painter.setPen(main_pen)

        # 计算可见区域
        visible_rect = self._get_visible_rect()
        start_x = int((visible_rect.left() // effective_grid_size) * effective_grid_size)
        end_x = int((visible_rect.right() // effective_grid_size) * effective_grid_size)
        start_y = int((visible_rect.top() // effective_grid_size) * effective_grid_size)
        end_y = int((visible_rect.bottom() // effective_grid_size) * effective_grid_size)

        # 绘制主网格线
        for x in range(start_x, end_x + effective_grid_size, effective_grid_size):
            painter.drawLine(x, start_y, x, end_y)

        for y in range(start_y, end_y + effective_grid_size, effective_grid_size):
            painter.drawLine(start_x, y, end_x, y)
        
        # 如果缩放级别足够大，绘制子网格（更细的线）
        if self.zoom_level >= 1.0 and effective_grid_size >= self.grid_size * 2:
            sub_grid_color = QColor(50, 50, 55, int(grid_alpha * 0.5))
            sub_pen = QPen(sub_grid_color, 0.3)
            painter.setPen(sub_pen)
            
            sub_grid_size = self.grid_size
            for x in range(start_x, end_x + sub_grid_size, sub_grid_size):
                if x % effective_grid_size != 0:  # 跳过主网格线
                    painter.drawLine(x, start_y, x, end_y)
            
            for y in range(start_y, end_y + sub_grid_size, sub_grid_size):
                if y % effective_grid_size != 0:  # 跳过主网格线
                    painter.drawLine(start_x, y, end_x, y)
        
        # 绘制中心十字线（参考 Unity）
        center_color = QColor(100, 100, 120, 150)
        center_pen = QPen(center_color, 1.0)
        painter.setPen(center_pen)
        painter.drawLine(0, start_y, 0, end_y)  # 垂直中心线
        painter.drawLine(start_x, 0, end_x, 0)  # 水平中心线

    def _get_visible_rect(self) -> QRectF:
        """获取可见区域（世界坐标）"""
        # 将屏幕坐标转换为世界坐标
        top_left = self._screen_to_world(QPoint(0, 0))
        bottom_right = self._screen_to_world(QPoint(self.width(), self.height()))
        return QRectF(top_left, bottom_right)

    def _screen_to_world(self, screen_pos: QPoint) -> QPointF:
        """屏幕坐标转世界坐标（扣除顶部工具栏）"""
        ey = screen_pos.y() - self._chrome_top()
        world_x = (screen_pos.x() - self.pan_offset.x()) / self.zoom_level
        world_y = (ey - self.pan_offset.y()) / self.zoom_level
        return QPointF(world_x, world_y)

    def _world_to_screen(self, world_pos: QPointF) -> QPoint:
        """世界坐标转屏幕坐标（含顶部工具栏偏移）"""
        screen_x = int(world_pos.x() * self.zoom_level + self.pan_offset.x())
        screen_y = int(world_pos.y() * self.zoom_level + self.pan_offset.y()) + self._chrome_top()
        return QPoint(screen_x, screen_y)

    # === 交互: 鼠标、滚轮、拖放 ==================================================
    def mousePressEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标按下事件（参考 Unity/Godot 的交互方式）。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了节点
            clicked_node = None
            world_pos = self._screen_to_world(event.pos())
            
            for node in reversed(self.nodes):
                if node.contains(world_pos):
                    clicked_node = node
                    break

            if clicked_node:
                # 处理多选
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    if clicked_node in self.selected_nodes:
                        self.selected_nodes.remove(clicked_node)
                        if self.selected_node == clicked_node:
                            self.selected_node = None
                    else:
                        self.selected_nodes.append(clicked_node)
                        self.selected_node = clicked_node
                elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                    if self.selected_node:
                        # 范围选择
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(clicked_node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                        self.selected_node = clicked_node
                    else:
                        self.selected_nodes = [clicked_node]
                        self.selected_node = clicked_node
                else:
                    self.selected_nodes = [clicked_node]
                    self.selected_node = clicked_node

                # 更新编辑器上下文
                self.editor_context.set_selection(self.selected_nodes)
                
                self.dragging = True
                self.drag_start = event.pos()
                self._drag_start_x = clicked_node.x
                self._drag_start_y = clicked_node.y
            else:
                # 点击空白处，开始框选或取消选择
                modifiers = event.modifiers()
                if not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                    # 开始框选
                    self.box_selecting = True
                    self.box_select_start = event.pos()
                    self.box_select_end = event.pos()
                    
                    # 如果没有按住 Ctrl/Shift，取消选择
                    self.selected_nodes.clear()
                    self.selected_node = None
                    self.editor_context.clear_selection()

            self.update()
            self.updateRequest.emit()

        elif event.button() == Qt.MouseButton.MiddleButton:
            # 鼠标中键开始平移（Unity/Godot 标准）
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
        elif event.button() == Qt.MouseButton.RightButton:
            world_pos = self._screen_to_world(event.pos())

            # 右键优先处理连接线删除
            for connection in self.connections:
                if connection.contains(world_pos):
                    command = DeleteConnectionCommand(self, connection)
                    self.command_stack.execute(command)
                    self.update()
                    self.projectModified.emit()
                    self.commandExecuted.emit()
                    return

            # 再处理节点选择
            clicked_node = None
            for node in reversed(self.nodes):
                if node.contains(world_pos):
                    clicked_node = node
                    break

            if clicked_node:
                # 处理多选
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    if clicked_node in self.selected_nodes:
                        self.selected_nodes.remove(clicked_node)
                        if self.selected_node == clicked_node:
                            self.selected_node = None
                    else:
                        self.selected_nodes.append(clicked_node)
                        self.selected_node = clicked_node
                elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                    if self.selected_node:
                        # 范围选择
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(clicked_node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                        self.selected_node = clicked_node
                    else:
                        self.selected_nodes = [clicked_node]
                        self.selected_node = clicked_node
                else:
                    self.selected_nodes = [clicked_node]
                    self.selected_node = clicked_node

                # 更新编辑器上下文
                self.editor_context.set_selection(self.selected_nodes)
                
                self.dragging = True
                self.drag_start = event.pos()
                self._drag_start_x = clicked_node.x
                self._drag_start_y = clicked_node.y
            else:
                # 点击空白处，取消选择
                if not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                    self.selected_nodes.clear()
                    self.selected_node = None
                    self.editor_context.clear_selection()

            self.update()
            self.updateRequest.emit()

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标释放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 处理框选完成
            if self.box_selecting:
                self.box_selecting = False
                # 执行框选逻辑
                self._finish_box_selection()
                self.update()
            
            if self.dragging:
                self.dragging = False
                if self.selected_node:
                    new_x = self.selected_node.x
                    new_y = self.selected_node.y
                    dx = new_x - self._drag_start_x
                    dy = new_y - self._drag_start_y

                    if dx != 0 or dy != 0:
                        if len(self.selected_nodes) > 1:
                            for node in self.selected_nodes:
                                old_x, old_y = node.x, node.y
                                new_node_x = old_x + dx
                                new_node_y = old_y + dy
                                command = MoveNodeCommand(
                                    node,
                                    int(old_x), int(old_y),
                                    int(new_node_x), int(new_node_y)
                                )
                                self.command_stack.execute(command)
                        else:
                            command = MoveNodeCommand(
                                self.selected_node,
                                int(self._drag_start_x), int(self._drag_start_y),
                                int(new_x), int(new_y)
                            )
                            self.command_stack.execute(command)

                        self.projectModified.emit()
                        self.commandExecuted.emit()

            # 处理连接完成
            if self.connecting and self.connect_start_node:
                world_pos = self._screen_to_world(event.pos())
                for node in self.nodes:
                    if node.contains(world_pos) and node != self.connect_start_node:
                        if self.connect_start_node.type != "organism" and node.type != "organism":
                            new_connection = ConnectionLine(self.connect_start_node, node)
                            connect_command = CreateConnectionCommand(self, new_connection)
                            self.command_stack.execute(connect_command)
                            self.projectModified.emit()
                            self.commandExecuted.emit()
                            break

                self.connecting = False
                self.connect_start_node = None
                self.update()
                self.updateRequest.emit()
        
        elif event.button() == Qt.MouseButton.MiddleButton:
            # 鼠标中键结束平移
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标移动事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return
        if event is None:
            return

        # 处理平移（鼠标中键或右键）
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_offset += QPointF(delta.x(), delta.y())
            self.pan_start = event.pos()
            self.update()
            return

        # 处理框选
        if self.box_selecting:
            self.box_select_end = event.pos()
            self.update()
            return

        world_pos = self._screen_to_world(event.pos())
        self._update_hover_states(world_pos)

        if self.dragging and self.selected_node:
            dx = (event.pos().x() - self.drag_start.x()) / self.zoom_level
            dy = (event.pos().y() - self.drag_start.y()) / self.zoom_level

            if len(self.selected_nodes) > 1:
                for node in self.selected_nodes:
                    new_x = node.x + dx
                    new_y = node.y + dy
                    # 应用吸附
                    if self.snap_to_grid:
                        new_x = round(new_x / self.grid_size) * self.grid_size
                        new_y = round(new_y / self.grid_size) * self.grid_size
                    node.update_position(new_x, new_y)
            else:
                new_x = self.selected_node.x + dx
                new_y = self.selected_node.y + dy
                # 应用吸附
                if self.snap_to_grid:
                    new_x = round(new_x / self.grid_size) * self.grid_size
                    new_y = round(new_y / self.grid_size) * self.grid_size
                self.selected_node.update_position(new_x, new_y)

            self.drag_start = event.pos()
            self.update()

        if self.connecting:
            self.connect_temp_pos = event.pos()
            self.update()

    def _update_hover_states(self, pos: QPointF):
        """更新悬停状态"""
        self.hovered_node = None
        for node in self.nodes:
            if node.contains(pos):
                self.hovered_node = node
                break

        self.hovered_connection = None
        for connection in self.connections:
            if connection.contains(pos):
                self.hovered_connection = connection
                break

        self.update()

    def wheelEvent(self, event: Optional[QWheelEvent]):
        """处理鼠标滚轮缩放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return
        if event is None:
            return

        # 获取鼠标位置（屏幕坐标）
        mouse_pos = event.position().toPoint()
        
        # 获取鼠标位置对应的世界坐标
        world_pos_before = self._screen_to_world(mouse_pos)
        
        # 计算缩放因子
        delta = event.angleDelta().y()
        zoom_speed = 0.1  # 缩放速度
        zoom_factor = 1.0 + (delta / 1200.0) * zoom_speed
        zoom_factor = max(0.9, min(1.1, zoom_factor))  # 限制单次缩放范围
        
        # 应用缩放
        new_zoom = self.zoom_level * zoom_factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # 计算缩放后的偏移，使鼠标位置对应的世界坐标保持不变
        if new_zoom != self.zoom_level:
            zoom_ratio = new_zoom / self.zoom_level
            self.pan_offset = QPointF(
                mouse_pos.x() - world_pos_before.x() * new_zoom,
                mouse_pos.y() - world_pos_before.y() * new_zoom
            )
            self.zoom_level = new_zoom
            self.update()

    def contextMenuEvent(self, event: Optional[QContextMenuEvent]):
        """上下文菜单事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        menu = QMenu(self)
        world_pos = self._screen_to_world(event.pos())
        pos_list = [world_pos.x(), world_pos.y()]

        # 创建基本实体菜单
        menu.addAction(self._t("scene_viewport.menu.create_empty_entity", "创建空实体"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.empty", "Empty Entity"), "entity_type": "empty", "position": pos_list
        }))
        menu.addAction(self._t("scene_viewport.menu.create_organism", "创建生物体"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.organism", "Organism"), "entity_type": "organism", "position": pos_list
        }))
        
        submenu = menu.addMenu(self._t("scene_viewport.menu.biological_components", "生物组件"))
        submenu.addAction(self._t("scene_viewport.menu.create_sensor", "创建传感器"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.sensor", "Sensor"), "entity_type": "sensor", "position": pos_list
        }))
        submenu.addAction(self._t("scene_viewport.menu.create_actuator", "创建效应器"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.actuator", "Actuator"), "entity_type": "actuator", "position": pos_list
        }))
        submenu.addAction(self._t("scene_viewport.menu.create_central_brain", "创建中枢管理器"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.central_brain", "Central Brain"), "entity_type": "central_brain", "position": pos_list
        }))

        menu.addSeparator()
        menu.addAction(self._t("scene_viewport.menu.create_official_cell", "创建官方细胞模板"), lambda: self.editor_context.event_bus.publish("create_entity", {
            "entity_name": self._t("scene_viewport.entity_name.official_cell", "Official Cell"),
            "entity_type": "organism",
            "position": pos_list,
            "scripts": [
                {
                    "name": "OfficialCellBehavior",
                    "path": os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__),
                            "..",
                            "..",
                            "..",
                            "builtin",
                            "templates",
                            "official_cell_behavior.py",
                        )
                    ),
                }
            ],
        }))

        menu.addSeparator()

        if self.selected_node:
            connect_action = menu.addAction(self._t("scene_viewport.menu.start_connection", "开始连接"))
            connect_action.triggered.connect(self._start_connection)

            delete_action = menu.addAction(self._t("scene_viewport.menu.delete_entity", "删除实体"))
            delete_action.triggered.connect(self._delete_node)

        menu.exec(event.globalPos())

    def dragEnterEvent(self, event):
        """处理拖入事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-vitaloom-asset"):
            event.acceptProposedAction()

    def dropEvent(self, event):
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
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            # 虽然不能在这里注入实体，但如果是拖拽 .pond 文件，应该允许执行
            if not event.mimeData().hasUrls():
                return
            elif not any(url.toLocalFile().lower().endswith('.pond') for url in event.mimeData().urls()):
                return

        world_pos = self._screen_to_world(event.position().toPoint())
        pos_list = [world_pos.x(), world_pos.y()]

        if event.mimeData().hasUrls():
            # 处理文件拖入
            for url in event.mimeData().urls():
                import os
                file_path = url.toLocalFile()
                file_name = os.path.basename(file_path)
                
                # 根据文件类型创建实体
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    logger.info("拖入图片: %s", file_name)
                    
                    # 检查是否是外部文件（不在项目目录内）
                    project_path = self.editor_context.current_project_path
                    
                    if project_path:
                        # 判断文件是否在项目外
                        if not file_path.startswith(project_path):
                            # 外部文件，需要复制到项目Assets文件夹
                            import shutil
                            assets_dir = os.path.join(project_path, "Assets")
                            os.makedirs(assets_dir, exist_ok=True)
                            
                            # 生成目标路径，避免重名
                            target_path = os.path.join(assets_dir, file_name)
                            counter = 1
                            name_without_ext, ext = os.path.splitext(file_name)
                            while os.path.exists(target_path):
                                target_path = os.path.join(assets_dir, f"{name_without_ext}_{counter}{ext}")
                                counter += 1
                            
                            # 复制文件
                            shutil.copy2(file_path, target_path)
                            file_path = target_path
                            import os
                            logger.info("已复制资源到项目: %s", os.path.relpath(target_path, project_path))
                            
                            # 刷新Project面板
                            self.editor_context.event_bus.publish("refresh_project_browser", {})
                    
                    self.editor_context.event_bus.publish("create_entity", {
                        "entity_name": file_name, 
                        "entity_type": "sprite", 
                        "position": pos_list, 
                        "sprite_path": file_path
                    })
                elif file_path.lower().endswith('.pond'):
                    # 检查是否按住 Alt 或 Shift，如果是，则作为预制体放入；否则询问是否切换场景
                    # 简化逻辑：如果是从项目中的场景文件夹拖入，通常是想打开场景
                    msg = f"检测到场景文件: {file_name}\n\n你想打开这个场景，还是将其作为预制体放入当前场景？"
                    from PyQt6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(self, "场景操作", msg, 
                                               QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel)
                    
                    if reply == QMessageBox.StandardButton.Open:
                        from core.VitaLoom.scene.scene_manager import get_scene_manager
                        get_scene_manager().load_scene(file_path)
                    elif reply == QMessageBox.StandardButton.Apply:
                        logger.info("拖入预制体: %s", file_name)
                        self.editor_context.event_bus.publish("create_entity", {
                            "entity_name": file_name, "entity_type": "prefab", "position": pos_list, "prefab_path": file_path
                        })
                else:
                    self.editor_context.event_bus.publish("create_entity", {
                        "entity_name": file_name, "entity_type": "asset", "position": pos_list, "asset_path": file_path
                    })
            
            event.acceptProposedAction()

    def _add_node(self, pos: QPointF, node_type: str):
        """添加节点"""
        node_id = f"{node_type}_{len([n for n in self.nodes if n.type == node_type]) + 1}"
        new_x = float(pos.x())
        new_y = float(pos.y())

        # 应用吸附
        if self.snap_to_grid:
            new_x = round(new_x / self.grid_size) * self.grid_size
            new_y = round(new_y / self.grid_size) * self.grid_size

        # 如果不是生物体节点，确保它在某个细胞膜内或细胞膜上
        if node_type != "organism":
            organism_node = None
            for node in self.nodes:
                if node.type == "organism":
                    organism_node = node
                    break

            if organism_node:
                membrane_radius = organism_node.radius * 3
                distance = ((new_x - organism_node.x) ** 2 + (new_y - organism_node.y) ** 2) ** 0.5

                if distance > membrane_radius:
                    dx_dir = new_x - organism_node.x
                    dy_dir = new_y - organism_node.y
                    if distance > 0:
                        dx_dir /= distance
                        dy_dir /= distance
                    new_x = float(organism_node.x + dx_dir * membrane_radius)
                    new_y = float(organism_node.y + dy_dir * membrane_radius)

        new_node = Node(node_id, float(new_x), float(new_y), node_type)
        command = AddNodeCommand(self, new_node, pos)
        self.command_stack.execute(command)

        self.selected_node = new_node
        self.selected_nodes = [new_node]
        self.editor_context.set_selection([new_node])

        if self.parent_widget:
            if hasattr(self.parent_widget, 'project_tree'):
                project_tree = getattr(self.parent_widget, 'project_tree')
                if hasattr(project_tree, 'update_tree'):
                    project_tree.update_tree(self.nodes, self.connections)

        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()
        
        # 发送信号
        self.signal_bus.emit_object_created(new_node, {'type': node_type})
        
        # 更新编辑器上下文
        self.editor_context.set_selection([new_node])

    def _delete_node(self):
        """删除节点"""
        if self.selected_nodes:
            deleted_nodes = self.selected_nodes.copy()
            
            # 获取场景管理器
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            
            for node in deleted_nodes:
                node_id = getattr(node, "id", None)
                command = DeleteNodeCommand(self, node)
                self.command_stack.execute(command)
                self.signal_bus.emit_object_deleted(node)
                
                # 同时从场景管理器的数据中删除
                if scene_data and "entities" in scene_data and node_id:
                    scene_data["entities"] = [e for e in scene_data["entities"] if e.get("id") != node_id]

            # 更新场景管理器数据
            if scene_data:
                sm.update_scene_data(scene_data)
                
            # 发送事件通知
            for node in deleted_nodes:
                node_id = getattr(node, "id", None)
                if node_id:
                    self.editor_context.event_bus.publish("entity_deleted", {"id": node_id})

            self.selected_nodes.clear()
            self.selected_node = None
            self.editor_context.clear_selection()

            self.update()
            self.updateRequest.emit()
            self.projectModified.emit()
            self.commandExecuted.emit()
            logger.info("已从场景中删除 %s 个实体并同步数据", len(deleted_nodes))

    def _delete_node_by_instance(self, node):
        """按实例删除节点"""
        node_id = getattr(node, "id", None)
        command = DeleteNodeCommand(self, node)
        self.command_stack.execute(command)
        self.signal_bus.emit_object_deleted(node)
        
        if node_id:
            # 发布删除事件，注意避免循环：如果这个删除动作是由事件引起的，可能需要特殊处理
            # 这里我们假定调用者会处理好事件循环
            
            # 同时从场景管理器的数据中删除
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if scene_data and "entities" in scene_data:
                scene_data["entities"] = [e for e in scene_data["entities"] if e.get("id") != node_id]
                sm.update_scene_data(scene_data)
        
        if node in self.selected_nodes:
            self.selected_nodes.remove(node)
        if self.selected_node == node:
            self.selected_node = None
            
        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()

    def keyPressEvent(self, event):
        """处理键盘事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self._delete_node()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Z 撤销
            self.command_stack.undo()
            self.update()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Y 重做
            self.command_stack.redo()
            self.update()
        else:
            super().keyPressEvent(event)

    def _start_connection(self):
        """开始连接节点"""
        if self.selected_node:
            self.connecting = True
            self.connect_start_node = self.selected_node
            self.connect_temp_pos = self._world_to_screen(QPointF(self.selected_node.x, self.selected_node.y))
            self.update()
    
    # === 场景数据: 与 SceneManager 同步 ==========================================
    def load_scene_data(self, scene_data: Dict[str, Any]):
        """职责: 从 `.pond` JSON 重建 nodes/connections 并清空命令栈。
        时机: scene_loaded 事件或项目打开后。
        不变量: 空 entities 时保留默认演示节点逻辑见 `_create_default_nodes`。
        排错: 加载后空白 → scene_data 键名 nodes/connections 是否与导出一致。
        """
        try:
            # 清空现有节点和连接
            self.nodes.clear()
            self.connections.clear()
            self.selected_node = None
            self.selected_nodes.clear()
            
            # 加载实体（节点）
            entities = scene_data.get("entities", [])
            if entities:
                for entity_data in entities:
                    try:
                        entity_id = entity_data.get("id", "")
                        entity_type = entity_data.get("type", "organism")
                        position = entity_data.get("position", [0, 0])
                        
                        # 处理位置数据（可能是列表、元组或字典）
                        if isinstance(position, (list, tuple)):
                            pos_x = float(position[0]) if len(position) > 0 else 0.0
                            pos_y = float(position[1]) if len(position) > 1 else 0.0
                        elif isinstance(position, dict):
                            pos_x = float(position.get("x", 0.0))
                            pos_y = float(position.get("y", 0.0))
                        else:
                            pos_x = 0.0
                            pos_y = 0.0
                        
                        # 创建节点
                        node = Node(entity_id, pos_x, pos_y, entity_type)
                        
                        # 恢复名称和脚本
                        if "name" in entity_data:
                            node.name = entity_data["name"]
                        if "scripts" in entity_data:
                            node.scripts = entity_data["scripts"]
                        if "sprite_path" in entity_data:
                            node.sprite_path = entity_data["sprite_path"]
                        if "radius" in entity_data:
                            node.radius = entity_data["radius"]
                        if entity_data.get("pinned") is True:
                            node.pinned = True
                        raw_vis = entity_data.get("sr_visual")
                        if isinstance(raw_vis, dict):
                            node.sr_visual = dict(raw_vis)
                        else:
                            try:
                                from core.VitaLoom.core.editor_context import get_editor_context
                                from core.Lotucosm.sr_game_defaults import (
                                    default_sr_visual_for_entity,
                                    infer_engine_game_project,
                                )

                                project_path = getattr(get_editor_context(), "current_project_path", None)
                                if infer_engine_game_project(project_path):
                                    vis = default_sr_visual_for_entity(entity_id, entity_type)
                                    if vis.sprite:
                                        node.sr_visual = {"sprite": vis.sprite}
                                        if vis.alpha < 0.999:
                                            node.sr_visual["alpha"] = vis.alpha
                            except Exception:
                                pass
                            
                        self.nodes.append(node)
                    except Exception as e:
                        logger.warning("加载实体失败: %s", e)
                        continue
            
            # 如果没有实体，保持空白（用户要求）
            # if not self.nodes:
            #     print("📝 场景中没有实体，创建默认节点")
            #     self._create_default_nodes()
            
            # 加载连接（需要根据场景数据格式调整）
            # 尝试多种可能的连接数据格式
            connections_data = scene_data.get("connections", [])
            if not connections_data:
                # 也可能在 components 中
                components = scene_data.get("components", [])
                for comp in components:
                    if isinstance(comp, dict) and "connections" in comp:
                        connections_data.extend(comp["connections"])
            
            for conn_data in connections_data:
                try:
                    # 支持多种连接数据格式
                    if isinstance(conn_data, dict):
                        start_id = conn_data.get("start", conn_data.get("start_id", conn_data.get("from", "")))
                        end_id = conn_data.get("end", conn_data.get("end_id", conn_data.get("to", "")))
                    elif isinstance(conn_data, (list, tuple)) and len(conn_data) >= 2:
                        start_id = str(conn_data[0])
                        end_id = str(conn_data[1])
                    else:
                        continue
                    
                    # 查找对应的节点
                    start_node = next((n for n in self.nodes if n.id == start_id), None)
                    end_node = next((n for n in self.nodes if n.id == end_id), None)
                    
                    if start_node and end_node:
                        connection = ConnectionLine(start_node, end_node)
                        self.connections.append(connection)
                except Exception as e:
                    logger.warning("加载连接失败: %s", e)
                    continue
            
            # 恢复视口平移/缩放（上次保存于 .pond viewport_state）
            vp_state = scene_data.get("viewport_state")
            if isinstance(vp_state, dict):
                pan = vp_state.get("pan_offset")
                if isinstance(pan, (list, tuple)) and len(pan) >= 2:
                    self.pan_offset = QPointF(float(pan[0]), float(pan[1]))
                zoom = vp_state.get("zoom_level")
                if zoom is not None:
                    try:
                        self.zoom_level = max(0.1, min(4.0, float(zoom)))
                    except (TypeError, ValueError):
                        pass

            # 更新显示
            self.update()
            self.updateRequest.emit()
            
            logger.info("场景数据已加载到视口: %s 个节点, %s 个连接", len(self.nodes), len(self.connections))
            
        except Exception as e:
            logger.exception("加载场景数据失败: %s", e)
            if not self.nodes:
                self._create_default_nodes()
                self.update()

    def get_scene_data(self) -> Dict[str, Any]:
        """职责: 序列化当前画布为 SceneManager 可保存的 dict 片段。
        时机: 保存场景前由插件或 SceneManager 拉取。
        不变量: 与 load_scene_data 字段对称（nodes、connections、resources）。
        排错: 保存丢失编辑 → 是否调用本方法合并进 save_scene(data=...)。
        """
        from core.Lotucosm.sr_game_defaults import default_sr_visual_for_entity, infer_engine_game_project
        from core.Lotucosm.sr_game_scene import normalize_game_scene_data
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        sm = get_scene_manager()
        base_data = sm.get_scene_data() or {}

        try:
            from core.VitaLoom.core.editor_context import get_editor_context

            project_path = getattr(get_editor_context(), "current_project_path", None)
        except Exception:
            project_path = None

        if infer_engine_game_project(project_path):
            for node in self.nodes:
                if not isinstance(node.sr_visual, dict) or not node.sr_visual.get("sprite"):
                    vis = default_sr_visual_for_entity(node.id, node.type)
                    if vis.sprite:
                        node.sr_visual = {"sprite": vis.sprite}
                        if vis.alpha < 0.999:
                            node.sr_visual["alpha"] = vis.alpha

        base_data["entities"] = [node.to_dict() for node in self.nodes]
        base_data["connections"] = [conn.to_dict() for conn in self.connections]

        base_data["viewport_state"] = {
            "pan_offset": [self.pan_offset.x(), self.pan_offset.y()],
            "zoom_level": self.zoom_level,
        }

        return normalize_game_scene_data(base_data, project_path)

    def _on_create_entity_event(self, data: Dict[str, Any]):
        """创建实体事件处理"""
        try:
            entity_name = data.get("entity_name", data.get("entity_type", "Entity"))
            entity_type = data.get("entity_type", "organism")
            position = data.get("position", [0, 0])
            sprite_path = data.get("sprite_path", "")
            scripts = data.get("scripts", [])
            
            self.create_entity_node(entity_name, entity_type, position, sprite_path, scripts=scripts)
        except Exception as e:
            logger.exception("处理创建实体事件失败: %s", e)
    
    def _on_scene_loaded_event(self, data):
        """场景加载事件处理"""
        try:
            # 重新加载当前场景数据到视口
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if scene_data:
                self.load_scene_data(scene_data)
        except Exception as e:
            logger.exception("处理场景加载事件失败: %s", e)
    
    def create_entity_node(
        self,
        entity_name: str,
        entity_type: str,
        position: List[float],
        sprite_path: str = "",
        scripts: Optional[List[Dict[str, Any]]] = None,
    ):
        """在场景中创建实体节点。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        try:
            # 生成唯一ID
            import uuid
            entity_id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
            
            # 获取位置
            pos_x = float(position[0]) if len(position) > 0 else 0.0
            pos_y = float(position[1]) if len(position) > 1 else 0.0
            
            # 创建节点
            node = Node(entity_id, pos_x, pos_y, entity_type)
            node.name = entity_name  # 设置显示名称
            node.scripts = list(scripts or [])
            
            # 处理 Sprite 类型
            if entity_type == "sprite" and sprite_path:
                node.sprite_path = sprite_path
                node.radius = 40.0  # 稍微增大显示
            
            # 使用命令模式添加节点
            from PyQt6.QtCore import QPoint
            command = AddNodeCommand(self, node, QPoint(int(pos_x), int(pos_y)))
            self.command_stack.execute(command)
            
            # 选中新创建的节点
            self.selected_node = node
            self.selected_nodes = [node]
            
            # 通知选择变化
            self.editor_context.set_selection([node])
            
            # 1. 更新场景管理器中的数据 (先更新数据，后发送事件，确保Hierarchy能查到最新数据)
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if scene_data:
                if "entities" not in scene_data:
                    scene_data["entities"] = []
                entity_entry = {
                    'id': entity_id,
                    'name': entity_name,
                    'type': entity_type,
                    'position': [pos_x, pos_y],
                    'scripts': list(scripts or []),
                }
                if sprite_path:
                    entity_entry['sprite_path'] = sprite_path
                    
                scene_data["entities"].append(entity_entry)
                sm.update_scene_data(scene_data)
            
            # 2. 通知场景层级更新
            self.editor_context.event_bus.publish("entity_created", {
                'id': entity_id,
                'name': entity_name,
                'type': entity_type,
                'position': [pos_x, pos_y],
                'sprite_path': sprite_path,
                'scripts': list(scripts or []),
            })
            
            # 3. 更新显示
            self.update()
            self.updateRequest.emit()
            self.projectModified.emit()
            self.commandExecuted.emit()
            
            logger.info("在场景中创建实体: %s (%s)", entity_name, entity_id)
        except Exception as e:
            logger.exception("创建实体节点失败: %s", e)


# 为了向后兼容，保留OrganismCanvas作为别名
OrganismCanvas = SceneViewport
