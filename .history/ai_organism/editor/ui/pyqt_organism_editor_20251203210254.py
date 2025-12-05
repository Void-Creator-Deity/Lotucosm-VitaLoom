"""基于PyQt6的AI生命体编辑器原型"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QBrush, QLinearGradient
import sys

# 导入命令模式
from ai_organism.editor.command import CommandStack, AddNodeCommand, DeleteNodeCommand, MoveNodeCommand, CreateConnectionCommand, DeleteConnectionCommand, ModifyNodePropertyCommand, ModifyConnectionPropertyCommand


class Node:
    """节点类"""
    def __init__(self, node_id, x, y, node_type="sensor"):
        self.id = node_id
        self.x = x
        self.y = y
        self.type = node_type  # sensor, actuator, or organism
        self.radius = 25
        self.connections = []
        
        # 根据类型设置颜色
        if node_type == "organism":
            self.color = QColor(100, 150, 200)  # 蓝色
            self.radius = 30
        elif node_type == "sensor":
            self.color = QColor(0, 255, 0)  # 绿色
        elif node_type == "actuator":
            self.color = QColor(255, 0, 0)  # 红色
        else:
            self.color = QColor(255, 255, 0)  # 黄色
    
    def contains(self, point):
        """判断点是否在节点内"""
        return (point.x() - self.x) ** 2 + (point.y() - self.y) ** 2 <= self.radius ** 2
    
    def draw(self, painter):
        """绘制节点"""
        # 绘制节点阴影效果
        shadow_rect = QRect(int(self.x - self.radius - 2), int(self.y - self.radius - 2), 
                           int(self.radius * 2 + 4), int(self.radius * 2 + 4))
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(shadow_rect)
        
        # 绘制节点主体
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        body_rect = QRect(int(self.x - self.radius), int(self.y - self.radius), 
                           int(self.radius * 2), int(self.radius * 2))
        painter.drawEllipse(body_rect)
        
        # 绘制节点标签
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(int(self.x - 15), int(self.y + 5), self.id[-3:])
    
    def update_position(self, x, y):
        """更新节点位置"""
        self.x = x
        self.y = y


class ConnectionLine:
    """连接线类"""
    def __init__(self, start_node, end_node):
        self.start_node = start_node
        self.end_node = end_node
        self.weight = 1.0
        self.color = QColor(100, 100, 255)
        self.width = 2
    
    def draw(self, painter):
        """绘制连接线"""
        # 绘制箭头
        pen = QPen(self.color, self.width)
        painter.setPen(pen)
        
        # 计算线条（使用整数）
        start_pos = QPoint(int(self.start_node.x), int(self.start_node.y))
        end_pos = QPoint(int(self.end_node.x), int(self.end_node.y))
        
        # 绘制直线
        painter.drawLine(start_pos, end_pos)
        
        # 手动计算角度（PyQt6中QPoint.angle()已移除）
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        import math
        angle = math.atan2(dy, dx) * 180 / math.pi
        
        arrow_size = 8
        
        # 计算箭头点（使用整数）
        arrow_p1 = QPoint(
            end_pos.x() - int(arrow_size * math.cos(math.radians(angle - 45))),
            end_pos.y() - int(arrow_size * math.sin(math.radians(angle - 45)))
        )
        arrow_p2 = QPoint(
            end_pos.x() - int(arrow_size * math.cos(math.radians(angle + 45))),
            end_pos.y() - int(arrow_size * math.sin(math.radians(angle + 45)))
        )
        
        # 绘制箭头
        painter.drawLine(end_pos, arrow_p1)
        painter.drawLine(end_pos, arrow_p2)
    
    def contains(self, point, tolerance=5):
        """判断点是否在线附近"""
        # 计算点到线段的距离
        def distance_point_line(p, a, b):
            if a == b:
                return (p - a).manhattanLength()
            
            # 计算向量
            ap = p - a
            ab = b - a
            
            # 使用静态方法计算点积
            dot_ap_ab = QPoint.dotProduct(ap, ab)
            dot_ab_ab = QPoint.dotProduct(ab, ab)
            
            if dot_ab_ab == 0:
                return (p - a).manhattanLength()
            
            t = max(0, min(1, dot_ap_ab / dot_ab_ab))
            
            # 计算投影点
            projection_x = int(a.x() + t * ab.x())
            projection_y = int(a.y() + t * ab.y())
            projection = QPoint(projection_x, projection_y)
            
            return (p - projection).manhattanLength()
        
        a = QPoint(int(self.start_node.x), int(self.start_node.y))
        b = QPoint(int(self.end_node.x), int(self.end_node.y))
        return distance_point_line(point, a, b) <= tolerance


class OrganismCanvas(QWidget):
    """生物可视化编辑画布 - 节点连线编辑器"""
    # 自定义信号，用于通知属性面板更新
    updateRequest = pyqtSignal()
    # 自定义信号，用于通知项目已修改
    projectModified = pyqtSignal()
    # 自定义信号，用于通知命令执行
    commandExecuted = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # 节点和连接线
        self.nodes = []
        self.connections = []
        
        # 交互状态
        self.selected_node = None
        self.selected_nodes = []  # 多选节点列表
        self.hovered_node = None
        self.hovered_connection = None
        self.dragging = False
        self.drag_start = QPoint()
        self.connecting = False
        self.connect_start_node = None
        self.connect_temp_pos = QPoint()
        
        # 命令栈
        self.command_stack = CommandStack()
        
        # 创建默认节点
        self._create_default_nodes()
    
    def _create_default_nodes(self):
        """创建默认节点"""
        center_x, center_y = 300, 200
        
        # 创建生物体节点
        organism = Node("organism_1", center_x, center_y, "organism")
        self.nodes.append(organism)
        
        # 创建传感器节点
        sensor1 = Node("sensor_1", center_x - 100, center_y - 50, "sensor")
        sensor2 = Node("sensor_2", center_x + 100, center_y - 50, "sensor")
        self.nodes.extend([sensor1, sensor2])
        
        # 创建效应器节点
        actuator1 = Node("actuator_1", center_x - 100, center_y + 50, "actuator")
        actuator2 = Node("actuator_2", center_x + 100, center_y + 50, "actuator")
        self.nodes.extend([actuator1, actuator2])
        
        # 创建连接线
        self.connections.append(ConnectionLine(sensor1, organism))
        self.connections.append(ConnectionLine(sensor2, organism))
        self.connections.append(ConnectionLine(organism, actuator1))
        self.connections.append(ConnectionLine(organism, actuator2))
    
    def paintEvent(self, event):
        """绘制画布内容"""
        painter = QPainter(self)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # 绘制渐变背景
        self._draw_gradient_background(painter)
        
        # 绘制网格背景
        self._draw_grid(painter)
        
        # 绘制连接线
        for connection in self.connections:
            # 高亮悬停的连接线
            if connection == self.hovered_connection:
                # 保存原始属性
                original_color = connection.color
                original_width = connection.width
                
                # 绘制高亮效果
                connection.color = QColor(255, 255, 0)
                connection.width = 4
                
                # 绘制发光效果
                glow_pen = QPen(QColor(255, 255, 0, 100), connection.width + 6)
                painter.setPen(glow_pen)
                painter.drawLine(
                    QPointF(connection.start_node.x, connection.start_node.y),
                    QPointF(connection.end_node.x, connection.end_node.y)
                )
                
                connection.draw(painter)
                
                # 恢复原始属性
                connection.color = original_color
                connection.width = original_width
            else:
                # 绘制连接线发光效果
                glow_pen = QPen(QColor(100, 100, 255, 30), connection.width + 4)
                painter.setPen(glow_pen)
                painter.drawLine(
                    QPointF(connection.start_node.x, connection.start_node.y),
                    QPointF(connection.end_node.x, connection.end_node.y)
                )
                
                connection.draw(painter)
        
        # 绘制临时连接线
        if self.connecting and self.connect_start_node:
            # 绘制临时线发光效果
            glow_pen = QPen(QColor(255, 255, 255, 50), 4, Qt.PenStyle.DashLine)
            painter.setPen(glow_pen)
            painter.drawLine(QPoint(int(self.connect_start_node.x), int(self.connect_start_node.y)),
                           self.connect_temp_pos)
            
            # 绘制主虚线
            pen = QPen(QColor(255, 255, 255, 150), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPoint(int(self.connect_start_node.x), int(self.connect_start_node.y)),
                           self.connect_temp_pos)
        
        # 绘制节点
        for node in self.nodes:
            # 高亮选中或悬停的节点
            is_selected = node in self.selected_nodes
            is_hovered = node == self.hovered_node
            
            if is_selected:
                # 绘制选中发光效果
                glow_brush = QBrush(QColor(255, 255, 255, 80))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                # 使用QRectF对象绘制椭圆
                rect = QRectF(
                    node.x - node.radius - 10, 
                    node.y - node.radius - 10, 
                    node.radius * 2 + 20, 
                    node.radius * 2 + 20
                )
                painter.drawEllipse(rect)
                
                # 绘制选中边框
                painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                rect = QRectF(
                    node.x - node.radius - 5, 
                    node.y - node.radius - 5, 
                    node.radius * 2 + 10, 
                    node.radius * 2 + 10
                )
                painter.drawEllipse(rect)
            elif is_hovered:
                # 绘制悬停发光效果
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
                
                # 绘制悬停边框
                painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                rect = QRectF(
                    node.x - node.radius - 3, 
                    node.y - node.radius - 3, 
                    node.radius * 2 + 6, 
                    node.radius * 2 + 6
                )
                painter.drawEllipse(rect)
            
            # 绘制节点
            node.draw(painter)
        
        # 为生物体节点绘制细胞膜效果（只保留圆环）
        for node in self.nodes:
            if node.type == "organism":
                # 计算细胞膜半径（比生物体节点大50%）
                membrane_radius = int(node.radius * 3)
                
                # 只绘制细胞膜圆环
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(100, 150, 255, 200), 2))
                # 使用整数坐标绘制
                center_x, center_y = int(node.x), int(node.y)
                painter.drawEllipse(center_x - membrane_radius, center_y - membrane_radius, 
                                   membrane_radius * 2, membrane_radius * 2)
    
    def _draw_gradient_background(self, painter):
        """绘制渐变背景"""
        # 创建线性渐变
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(30, 30, 35))    # 左上角深色
        gradient.setColorAt(0.5, QColor(25, 25, 30))  # 中间稍浅
        gradient.setColorAt(1, QColor(20, 20, 25))    # 右下角深色
        
        # 填充背景
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())
    
    def _draw_grid(self, painter):
        """绘制网格背景"""
        grid_color = QColor(60, 60, 70)
        grid_size = 20
        
        pen = QPen(grid_color, 0.3)
        painter.setPen(pen)
        
        # 绘制垂直线
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        
        # 绘制水平线
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
        
        # 绘制中心十字线
        center_x, center_y = self.width() // 2, self.height() // 2
        center_pen = QPen(QColor(80, 80, 100), 1, Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        painter.drawLine(center_x, 0, center_x, self.height())
        painter.drawLine(0, center_y, self.width(), center_y)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了节点
            clicked_node = None
            for node in reversed(self.nodes):
                if node.contains(event.pos()):
                    clicked_node = node
                    break
            
            if clicked_node:
                # 处理多选
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # 按住Ctrl键进行多选
                    if clicked_node in self.selected_nodes:
                        # 取消选择
                        self.selected_nodes.remove(clicked_node)
                        if self.selected_node == clicked_node:
                            self.selected_node = None
                    else:
                        # 添加选择
                        self.selected_nodes.append(clicked_node)
                        self.selected_node = clicked_node
                elif event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # 按住Shift键从当前选择到点击节点进行多选
                    if self.selected_node:
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(clicked_node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                        self.selected_node = clicked_node
                    else:
                        # 没有当前选择，直接选择
                        self.selected_nodes = [clicked_node]
                        self.selected_node = clicked_node
                else:
                    # 普通点击，只选择一个节点
                    self.selected_nodes = [clicked_node]
                    self.selected_node = clicked_node
                
                self.dragging = True
                self.drag_start = event.pos()
                # 记录节点的初始位置
                self._drag_start_x = clicked_node.x
                self._drag_start_y = clicked_node.y
            else:
                # 点击空白处，取消所有选择
                if not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                    self.selected_nodes.clear()
                    self.selected_node = None
            
            self.update()
            # 触发更新信号
            self.updateRequest.emit()
        
        # 右键点击连线
        elif event.button() == Qt.MouseButton.RightButton:
            # 检查是否点击了连接线
            for connection in self.connections:
                if connection.contains(event.pos()):
                    # 使用命令模式删除连接
                    command = DeleteConnectionCommand(self, connection)
                    self.command_stack.execute(command)
                    self.update()
                    self.projectModified.emit()
                    self.commandExecuted.emit()
                    break
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
                # 检查节点是否被移动
                if self.selected_node:
                    # 记录所有选中节点的初始位置
                    initial_positions = {}
                    for node in self.selected_nodes:
                        initial_positions[node] = (node.x, node.y)
                    
                    # 计算移动偏移量
                    new_x = self.selected_node.x
                    new_y = self.selected_node.y
                    dx = new_x - self._drag_start_x
                    dy = new_y - self._drag_start_y
                    
                    if dx != 0 or dy != 0:
                        # 如果有多个选中节点，批量移动
                        if len(self.selected_nodes) > 1:
                            # 执行所有移动命令
                            for node in self.selected_nodes:
                                old_x, old_y = initial_positions[node]
                                new_node_x = old_x + dx
                                new_node_y = old_y + dy
                                command = MoveNodeCommand(
                                    node, 
                                    old_x, old_y, 
                                    new_node_x, new_node_y
                                )
                                self.command_stack.execute(command)
                        else:
                            # 单个节点移动
                            command = MoveNodeCommand(
                                self.selected_node, 
                                self._drag_start_x, self._drag_start_y, 
                                new_x, new_y
                            )
                            self.command_stack.execute(command)
                        
                        # 拖拽节点后标记为已修改
                        self.projectModified.emit()
                        self.commandExecuted.emit()
            
            # 处理连接完成
            if self.connecting:
                # 检查是否点击了另一个节点
                for node in self.nodes:
                    if node.contains(event.pos()) and node != self.connect_start_node:
                        # 确保不能直接连接到细胞膜
                        if self.connect_start_node.type != "organism" and node.type != "organism":
                            # 创建新连接
                            new_connection = ConnectionLine(self.connect_start_node, node)
                            # 使用命令模式创建连接
                            command = CreateConnectionCommand(self, new_connection)
                            self.command_stack.execute(command)
                            # 连接创建后标记为已修改
                            self.projectModified.emit()
                            self.commandExecuted.emit()
                            break
                
                self.connecting = False
                self.connect_start_node = None
                self.update()
                self.updateRequest.emit()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        # 更新悬停状态
        self._update_hover_states(event.pos())
        
        # 处理节点拖拽
        if self.dragging and self.selected_node:
            dx = event.pos().x() - self.drag_start.x()
            dy = event.pos().y() - self.drag_start.y()
            
            # 找到生物体节点（细胞膜）
            organism_node = None
            for node in self.nodes:
                if node.type == "organism":
                    organism_node = node
                    break
            
            if len(self.selected_nodes) > 1:
                # 批量移动多个节点
                for node in self.selected_nodes:
                    # 计算新位置
                    new_x = node.x + dx
                    new_y = node.y + dy
                    
                    # 如果是生物体节点，可以自由移动
                    if node.type != "organism" and organism_node:
                        # 计算细胞膜半径
                        membrane_radius = organism_node.radius * 3
                        
                        # 计算节点到细胞膜中心的距离
                        distance = ((new_x - organism_node.x) ** 2 + (new_y - organism_node.y) ** 2) ** 0.5
                        
                        # 如果节点超出细胞膜范围，限制在细胞膜上
                        if distance > membrane_radius:
                            # 计算方向向量
                            dx_dir = new_x - organism_node.x
                            dy_dir = new_y - organism_node.y
                            
                            # 归一化方向向量
                            if distance > 0:
                                dx_dir /= distance
                                dy_dir /= distance
                            
                            # 计算限制后的位置
                            new_x = organism_node.x + dx_dir * membrane_radius
                            new_y = organism_node.y + dy_dir * membrane_radius
                    
                    # 更新节点位置
                    node.update_position(new_x, new_y)
            else:
                # 移动单个节点
                # 计算新位置
                new_x = self.selected_node.x + dx
                new_y = self.selected_node.y + dy
                
                # 如果是生物体节点，可以自由移动
                if self.selected_node.type != "organism" and organism_node:
                    # 计算细胞膜半径
                    membrane_radius = organism_node.radius * 3
                    
                    # 计算节点到细胞膜中心的距离
                    distance = ((new_x - organism_node.x) ** 2 + (new_y - organism_node.y) ** 2) ** 0.5
                    
                    # 如果节点超出细胞膜范围，限制在细胞膜上
                    if distance > membrane_radius:
                        # 计算方向向量
                        dx_dir = new_x - organism_node.x
                        dy_dir = new_y - organism_node.y
                        
                        # 归一化方向向量
                        if distance > 0:
                            dx_dir /= distance
                            dy_dir /= distance
                        
                        # 计算限制后的位置
                        new_x = organism_node.x + dx_dir * membrane_radius
                        new_y = organism_node.y + dy_dir * membrane_radius
                
                # 更新节点位置
                self.selected_node.update_position(new_x, new_y)
            
            self.drag_start = event.pos()
            self.update()
        
        # 处理临时连接线
        if self.connecting:
            self.connect_temp_pos = event.pos()
            self.update()
    

    
    def _update_hover_states(self, pos):
        """更新悬停状态"""
        # 检查节点悬停
        self.hovered_node = None
        for node in self.nodes:
            if node.contains(pos):
                self.hovered_node = node
                break
        
        # 检查连接线悬停
        self.hovered_connection = None
        for connection in self.connections:
            if connection.contains(pos):
                self.hovered_connection = connection
                break
        
        self.update()
    
    def contextMenuEvent(self, event):
        """处理右键菜单"""
        menu = QMenu()
        
        # 添加节点菜单项
        add_sensor_action = QAction("添加传感器", self)
        add_sensor_action.triggered.connect(lambda: self._add_node(event.pos(), "sensor"))
        menu.addAction(add_sensor_action)
        
        add_actuator_action = QAction("添加效应器", self)
        add_actuator_action.triggered.connect(lambda: self._add_node(event.pos(), "actuator"))
        menu.addAction(add_actuator_action)
        
        menu.addSeparator()
        
        # 添加连接线菜单项
        if self.selected_node:
            connect_action = QAction("开始连接", self)
            connect_action.triggered.connect(self._start_connection)
            menu.addAction(connect_action)
        
        # 添加删除菜单项
        if self.selected_node:
            delete_action = QAction("删除节点", self)
            delete_action.triggered.connect(self._delete_node)
            menu.addAction(delete_action)
        
        menu.exec(event.globalPos())
    
    def _add_node(self, pos, node_type):
        """添加节点"""
        node_id = f"{node_type}_{len([n for n in self.nodes if n.type == node_type]) + 1}"
        
        # 获取新节点的初始位置
        new_x = pos.x()
        new_y = pos.y()
        
        # 如果不是生物体节点，确保它在细胞膜内或细胞膜上
        if node_type != "organism":
            # 找到生物体节点（细胞膜）
            organism_node = None
            for node in self.nodes:
                if node.type == "organism":
                    organism_node = node
                    break
            
            if organism_node:
                # 计算细胞膜半径
                membrane_radius = organism_node.radius * 3
                
                # 计算新节点到细胞膜中心的距离
                distance = ((new_x - organism_node.x) ** 2 + (new_y - organism_node.y) ** 2) ** 0.5
                
                # 如果节点超出细胞膜范围，限制在细胞膜上
                if distance > membrane_radius:
                    # 计算方向向量
                    dx_dir = new_x - organism_node.x
                    dy_dir = new_y - organism_node.y
                    
                    # 归一化方向向量
                    if distance > 0:
                        dx_dir /= distance
                        dy_dir /= distance
                    
                    # 计算限制后的位置
                    new_x = organism_node.x + dx_dir * membrane_radius
                    new_y = organism_node.y + dy_dir * membrane_radius
        
        new_node = Node(node_id, new_x, new_y, node_type)
        # 使用命令模式添加节点
        command = AddNodeCommand(self, new_node, pos)
        self.command_stack.execute(command)
        self.selected_node = new_node
        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()
    
    def _delete_node(self):
        """删除节点"""
        if self.selected_nodes:
            # 如果有多个选中的节点，批量删除
            if len(self.selected_nodes) > 1:
                # 记录删除的节点，用于撤销
                deleted_nodes = self.selected_nodes.copy()
                
                # 执行批量删除
                for node in deleted_nodes:
                    command = DeleteNodeCommand(self, node)
                    self.command_stack.execute(command)
            elif self.selected_node:
                # 单个节点删除
                command = DeleteNodeCommand(self, self.selected_node)
                self.command_stack.execute(command)
            
            # 清空选择
            self.selected_nodes.clear()
            self.selected_node = None
            
            self.update()
            self.updateRequest.emit()
            self.projectModified.emit()
            self.commandExecuted.emit()
    
    def _start_connection(self):
        """开始连接节点"""
        if self.selected_node:
            self.connecting = True
            self.connect_start_node = self.selected_node
            self.connect_temp_pos = QPoint(self.selected_node.x, self.selected_node.y)
            self.update()
    
    def _delete_node(self):
        """删除节点"""
        if self.selected_node:
            # 删除相关连接
            self.connections = [c for c in self.connections \
                              if c.start_node != self.selected_node \
                              and c.end_node != self.selected_node]
            
            # 删除节点
            self.nodes.remove(self.selected_node)
            self.selected_node = None
            self.update()
            self.updateRequest.emit()
            self.projectModified.emit()
    
    def wheelEvent(self, event):
        """处理滚轮事件 - 缩放功能"""
        # 简单的缩放实现
        delta = event.angleDelta().y()
        if delta > 0:
            # 放大
            for node in self.nodes:
                node.radius = min(50, node.radius + 1)
        else:
            # 缩小
            for node in self.nodes:
                node.radius = max(15, node.radius - 1)
        
        self.update()


class PropertyPanel(QWidget):
    """属性编辑面板"""
    # 自定义信号，用于通知项目已修改
    projectModified = pyqtSignal()
    # 自定义信号，用于通知命令执行
    commandExecuted = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(250)
        self.setStyleSheet("background-color: #2d2d2d;")
        
        self.layout = QVBoxLayout(self)
        
        # 标题
        self.title_label = QLabel("属性编辑")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # 分隔线
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.line.setStyleSheet("background-color: #404040;")
        self.layout.addWidget(self.line)
        
        # 状态信息
        self.status_label = QLabel("未选择对象")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.layout.addWidget(self.status_label)
        
        # 对象属性容器
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.properties_container)
        
        # 空控件填充剩余空间
        self.layout.addStretch()
        
        # 当前选中的对象
        self._selected_object = None
        
        # 命令栈
        from ai_organism.editor.command import CommandStack
        self.command_stack = CommandStack()
        
        # 初始化属性控件
        self._create_property_controls()
        self._clear_properties()
    
    def _create_property_controls(self):
        """创建属性控件"""
        # 通用属性组
        self.general_group = QGroupBox("通用属性")
        self.general_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        self.general_layout = QFormLayout()
        self.general_group.setLayout(self.general_layout)
        
        # ID标签
        self.id_label = QLabel("-")
        self.id_label.setStyleSheet("color: #888888;")
        self.general_layout.addRow("ID:", self.id_label)
        
        # 类型标签
        self.type_label = QLabel("-")
        self.type_label.setStyleSheet("color: #888888;")
        self.general_layout.addRow("类型:", self.type_label)
        
        # 位置属性组
        self.position_group = QGroupBox("位置属性")
        self.position_group.setStyleSheet(self.general_group.styleSheet())
        self.position_layout = QFormLayout()
        self.position_group.setLayout(self.position_layout)
        
        # X坐标
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-10000, 10000)
        self.x_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.position_layout.addRow("X坐标:", self.x_spin)
        
        # Y坐标
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-10000, 10000)
        self.y_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.position_layout.addRow("Y坐标:", self.y_spin)
        
        # 半径/大小属性组
        self.size_group = QGroupBox("大小属性")
        self.size_group.setStyleSheet(self.general_group.styleSheet())
        self.size_layout = QFormLayout()
        self.size_group.setLayout(self.size_layout)
        
        # 半径
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(10, 100)
        self.radius_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.size_layout.addRow("半径:", self.radius_spin)
        
        # 连接属性组
        self.connection_group = QGroupBox("连接属性")
        self.connection_group.setStyleSheet(self.general_group.styleSheet())
        self.connection_layout = QFormLayout()
        self.connection_group.setLayout(self.connection_layout)
        
        # 权重
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(-5.0, 5.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.connection_layout.addRow("权重:", self.weight_spin)
        
        # 源节点
        self.source_label = QLabel("-")
        self.source_label.setStyleSheet("color: #888888;")
        self.connection_layout.addRow("源节点:", self.source_label)
        
        # 目标节点
        self.target_label = QLabel("-")
        self.target_label.setStyleSheet("color: #888888;")
        self.connection_layout.addRow("目标节点:", self.target_label)
    
    def _clear_properties(self):
        """清空属性面板"""
        # 隐藏所有属性组
        for widget in self.properties_layout.findChildren(QWidget):
            widget.hide()
        
        # 更新状态标签
        self.status_label.setText("未选择对象")
    
    def update_properties(self, selected_object):
        """更新属性面板内容"""
        self._clear_properties()
        
        if not selected_object:
            return
        
        # 更新状态标签
        self.status_label.setText(f"已选择: {selected_object.__class__.__name__}")
        
        # 添加通用属性组
        self.properties_layout.addWidget(self.general_group)
        self.general_group.show()
        
        # 根据对象类型显示不同属性
        if hasattr(selected_object, "id"):
            # 节点属性
            self.id_label.setText(selected_object.id)
            
            if hasattr(selected_object, "type"):
                type_names = {
                    "organism": "生物",
                    "sensor": "传感器", 
                    "actuator": "效应器"
                }
                self.type_label.setText(type_names.get(selected_object.type, selected_object.type))
            
            # 添加位置属性
            self.properties_layout.addWidget(self.position_group)
            self.position_group.show()
            
            self.x_spin.setValue(selected_object.x)
            self.y_spin.setValue(selected_object.y)
            
            # 添加大小属性
            if hasattr(selected_object, "radius"):
                self.properties_layout.addWidget(self.size_group)
                self.size_group.show()
                self.radius_spin.setValue(selected_object.radius)
            
            # 连接信号
            self.x_spin.valueChanged.connect(lambda value: self._on_property_changed("x", value))
            self.y_spin.valueChanged.connect(lambda value: self._on_property_changed("y", value))
            self.radius_spin.valueChanged.connect(lambda value: self._on_property_changed("radius", value))
        
        elif isinstance(selected_object, ConnectionLine):
            # 连接线属性
            self.id_label.setText(f"Connection_{id(selected_object) % 1000:03d}")
            self.type_label.setText("连接")
            
            # 添加连接属性
            self.properties_layout.addWidget(self.connection_group)
            self.connection_group.show()
            
            self.weight_spin.setValue(selected_object.weight)
            self.source_label.setText(selected_object.start_node.id)
            self.target_label.setText(selected_object.end_node.id)
            
            # 连接信号
            self.weight_spin.valueChanged.connect(lambda value: self._on_property_changed("weight", value))
    
    def _on_property_changed(self, property_name, value):
        """属性变化回调"""
        from ai_organism.editor.command import ModifyNodePropertyCommand, ModifyConnectionPropertyCommand
        
        # 获取当前选中的对象
        current_object = self._selected_object
        
        if current_object:
            # 保存原始值
            old_value = getattr(current_object, property_name, None)
            
            # 检查值是否发生变化
            if old_value != value:
                # 根据对象类型创建不同的命令
                if hasattr(current_object, 'type'):  # 节点对象
                    command = ModifyNodePropertyCommand(
                        current_object, property_name, old_value, value
                    )
                else:  # 连接对象
                    command = ModifyConnectionPropertyCommand(
                        current_object, property_name, old_value, value
                    )
                
                # 执行命令
                self.command_stack.execute(command)
                
                # 触发画布更新
                self.update()
                
                # 通知画布属性已修改
                if hasattr(self, 'projectModified'):
                    self.projectModified.emit()
                if hasattr(self, 'commandExecuted'):
                    self.commandExecuted.emit()
    
    def update_properties(self, selected_object):
        """更新属性面板内容"""
        self._clear_properties()
        self._selected_object = selected_object
        
        if not selected_object:
            return
        
        # 更新状态标签
        self.status_label.setText(f"已选择: {selected_object.__class__.__name__}")
        
        # 添加通用属性组
        self.properties_layout.addWidget(self.general_group)
        self.general_group.show()
        
        # 根据对象类型显示不同属性
        if hasattr(selected_object, 'id'):
            # 节点属性
            self.id_label.setText(selected_object.id)
            
            if hasattr(selected_object, 'type'):
                type_names = {
                    "organism": "生物",
                    "sensor": "传感器", 
                    "actuator": "效应器"
                }
                self.type_label.setText(type_names.get(selected_object.type, selected_object.type))
            
            # 添加位置属性
            self.properties_layout.addWidget(self.position_group)
            self.position_group.show()
            
            # 断开之前的信号连接，避免重复连接
            try:
                self.x_spin.valueChanged.disconnect()
            except TypeError:
                pass
            try:
                self.y_spin.valueChanged.disconnect()
            except TypeError:
                pass
            
            self.x_spin.setValue(selected_object.x)
            self.y_spin.setValue(selected_object.y)
            
            # 连接新的信号
            self.x_spin.valueChanged.connect(lambda value: self._on_property_changed("x", value))
            self.y_spin.valueChanged.connect(lambda value: self._on_property_changed("y", value))
            
            # 添加大小属性
            if hasattr(selected_object, "radius"):
                self.properties_layout.addWidget(self.size_group)
                self.size_group.show()
                
                # 断开之前的信号连接
                try:
                    self.radius_spin.valueChanged.disconnect()
                except TypeError:
                    pass
                
                self.radius_spin.setValue(selected_object.radius)
                
                # 连接新的信号
                self.radius_spin.valueChanged.connect(lambda value: self._on_property_changed("radius", value))
        
        elif isinstance(selected_object, ConnectionLine):
            # 连接线属性
            self.id_label.setText(f"Connection_{id(selected_object) % 1000:03d}")
            self.type_label.setText("连接")
            
            # 添加连接属性
            self.properties_layout.addWidget(self.connection_group)
            self.connection_group.show()
            
            # 断开之前的信号连接
            try:
                self.weight_spin.valueChanged.disconnect()
            except TypeError:
                pass
            
            self.weight_spin.setValue(selected_object.weight)
            self.source_label.setText(selected_object.start_node.id)
            self.target_label.setText(selected_object.end_node.id)
            
            # 连接新的信号
            self.weight_spin.valueChanged.connect(lambda value: self._on_property_changed("weight", value))


class ProjectTree(QWidget):
    """项目树面板"""
    # 定义信号，用于通知主窗口新建或删除生物
    organism_created = pyqtSignal(str)  # 生物名称
    organism_deleted = pyqtSignal(str)  # 生物名称
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)
        self.setStyleSheet("background-color: #252526;")
        # 保存当前选中的生物
        self.current_organism = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 标题
        title = QLabel("项目")
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 4px 0;
        """)
        layout.addWidget(title)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("""
            background-color: #404040;
            margin: 4px 0;
        """)
        layout.addWidget(line)
        
        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("生物项目")
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 2px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
                border-radius: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTreeWidget::item:selected {
                background-color: #108ee9;
                color: #ffffff;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
            QTreeWidget::branch:open {
                background-color: transparent;
            }
            QTreeWidget::branch:closed {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid #404040;
            }
        """)
        
        # 添加示例项目
        project_item = QTreeWidgetItem(self.tree, ["AI生命体项目"])
        project_item.setIcon(0, QIcon.fromTheme("folder"))
        
        # 添加生物
        organism_item = QTreeWidgetItem(project_item, ["生物列表"])
        organism_item.setIcon(0, QIcon.fromTheme("list-add"))
        
        organism1 = QTreeWidgetItem(organism_item, ["生物1"])
        organism1.setIcon(0, QIcon.fromTheme("object-group"))
        
        organism2 = QTreeWidgetItem(organism_item, ["生物2"])
        organism2.setIcon(0, QIcon.fromTheme("object-group"))
        
        # 添加模板
        template_item = QTreeWidgetItem(project_item, ["模板库"])
        template_item.setIcon(0, QIcon.fromTheme("applications-system"))
        
        template1 = QTreeWidgetItem(template_item, ["基础生物"])
        template1.setIcon(0, QIcon.fromTheme("document-new"))
        
        template2 = QTreeWidgetItem(template_item, ["传感器丰富生物"])
        template2.setIcon(0, QIcon.fromTheme("document-new"))
        
        template3 = QTreeWidgetItem(template_item, ["效应器丰富生物"])
        template3.setIcon(0, QIcon.fromTheme("document-new"))
        
        # 添加环境
        environment_item = QTreeWidgetItem(project_item, ["环境"])
        environment_item.setIcon(0, QIcon.fromTheme("preferences-system-environment"))
        
        env1 = QTreeWidgetItem(environment_item, ["默认环境"])
        env1.setIcon(0, QIcon.fromTheme("world"))
        
        self.tree.expandAll()
        layout.addWidget(self.tree)
        
        # 添加操作按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        
        new_btn = QPushButton("新建")
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666666;
            }
        """)
        new_btn.clicked.connect(self._on_new_organism)
        button_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet(new_btn.styleSheet())
        delete_btn.clicked.connect(self._on_delete_organism)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
    
    def _on_new_organism(self):
        """新建生物"""
        # 找到生物列表节点
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            project_item = root.child(i)
            if project_item.text(0) == "AI生命体项目":
                for j in range(project_item.childCount()):
                    child_item = project_item.child(j)
                    if child_item.text(0) == "生物列表":
                        # 创建新生物节点
                        organism_count = child_item.childCount() + 1
                        organism_name = f"生物{organism_count}"
                        new_organism = QTreeWidgetItem(child_item, [organism_name])
                        new_organism.setIcon(0, QIcon.fromTheme("object-group"))
                        # 展开父节点
                        child_item.setExpanded(True)
                        # 选中新创建的生物
                        self.tree.setCurrentItem(new_organism)
                        # 发送生物创建信号
                        self.organism_created.emit(organism_name)
                        # 更新当前选中的生物
                        self.current_organism = organism_name
                        break
    
    def _on_delete_organism(self):
        """删除生物"""
        selected_item = self.tree.currentItem()
        if selected_item:
            parent = selected_item.parent()
            if parent and parent.text(0) == "生物列表":
                organism_name = selected_item.text(0)
                # 确认删除
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(self, "确认删除", 
                                          f"确定要删除{organism_name}吗？",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 删除节点
                    index = parent.indexOfChild(selected_item)
                    parent.takeChild(index)
                    # 发送生物删除信号
                    self.organism_deleted.emit(organism_name)
                    # 更新当前选中的生物
                    self.current_organism = None


class ConsolePanel(QWidget):
    """控制台输出面板"""
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(150)
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 标题和清除按钮
        title_layout = QHBoxLayout()
        title = QLabel("控制台")
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
            padding: 2px 0;
        """)
        title_layout.addWidget(title)
        
        clear_btn = QPushButton("清除")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666666;
            }
        """)
        clear_btn.clicked.connect(self.clear_output)
        title_layout.addWidget(clear_btn)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #404040; margin: 2px 0;")
        layout.addWidget(line)
        
        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #4ec9b0;
                border: 1px solid #333333;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                padding: 6px;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background-color: #2d2d2d;
                height: 0;
            }
        """)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_edit)
    
    def add_output(self, text):
        """添加输出文本"""
        self.text_edit.append(text)
        # 自动滚动到底部
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
    
    def clear_output(self):
        """清除输出文本"""
        self.text_edit.clear()


class PyQtOrganismEditor(QMainWindow):
    """基于PyQt6的AI生命体编辑器主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI生命体编辑器 - PyQt6版")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置现代深色主题样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QMenuBar {
                background-color: #252526;
                color: #ffffff;
                border-bottom: 1px solid #3e3e42;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 3px;
            }
            
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            
            QMenu {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 3px;
            }
            
            QMenu::item {
                padding: 8px 20px;
                border-radius: 2px;
            }
            
            QMenu::item:selected {
                background-color: #0e639c;
            }
            
            QToolBar {
                background-color: #252526;
                border-bottom: 1px solid #3e3e42;
            }
            
            QToolBar::handle {
                background-color: #3e3e42;
            }
            
            QToolButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 6px 8px;
                border-radius: 3px;
            }
            
            QToolButton:hover {
                background-color: #3c3c3c;
            }
            
            QToolButton:pressed {
                background-color: #0e639c;
            }
            
            QTabWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTabBar {
                background-color: #252526;
                color: #ffffff;
                border-bottom: 1px solid #3e3e42;
            }
            
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 10px 20px;
                margin-right: 1px;
                border: 1px solid #3e3e42;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-color: #3e3e42;
            }
            
            QTabBar::tab:hover {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            
            QStatusBar {
                background-color: #252526;
                color: #cccccc;
                border-top: 1px solid #3e3e42;
            }
            
            QSplitter {
                background-color: #1e1e1e;
            }
            
            QSplitter::handle {
                background-color: #3e3e42;
                width: 4px;
                height: 4px;
            }
            
            QSplitter::handle:hover {
                background-color: #555555;
            }
            
            QGroupBox {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                margin-top: 10px;
            }
            
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLabel {
                color: #cccccc;
            }
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2d2d30;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 6px 8px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #0e639c;
                outline: none;
            }
            
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #1177bb;
            }
            
            QPushButton:pressed {
                background-color: #0d5a8c;
            }
            
            QTreeWidget {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
            }
            
            QTreeWidget::item {
                padding: 6px 8px;
                border-radius: 2px;
            }
            
            QTreeWidget::item:hover {
                background-color: #3c3c3c;
            }
            
            QTreeWidget::item:selected {
                background-color: #0e639c;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 6px 10px;
                border: none;
                border-right: 1px solid #3e3e42;
                border-bottom: 1px solid #3e3e42;
            }
            
            QTextEdit {
                background-color: #1e1e1e;
                color: #4ec9b0;
                border: 1px solid #3e3e42;
                border-radius: 4px;
            }
            
            QScrollBar {
                background-color: #2d2d30;
                width: 12px;
                height: 12px;
            }
            
            QScrollBar::handle {
                background-color: #424242;
                border-radius: 6px;
            }
            
            QScrollBar::handle:hover {
                background-color: #555555;
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                background-color: transparent;
            }
        """)
        
        # 保存所有生物的状态
        self.organisms = {}  # 键: 生物名称, 值: (节点列表, 连接列表)
        self.current_organism = None
        
        # 保存状态
        self.is_dirty = False  # 标记是否有未保存的更改
        
        # 配置文件路径
        self.config_file = "ai_organism_config.json"
        
        # VSCode风格的自动保存配置
        self.auto_save_enabled = True
        self.auto_save_delay = 1000  # 1秒后自动保存
        self.auto_save_mode = "afterDelay"  # afterDelay, onFocusChange, onWindowChange
        self.save_on_focus_change = True
        self.save_on_close = True
        
        # 初始化模板管理器
        from ai_organism.editor.template_manager import TemplateManager
        self.template_manager = TemplateManager()
        
        # 加载配置
        self.load_config()
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建水平分割器（左侧面板 + 中央编辑区 + 右侧属性面板）
        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.horizontal_splitter.setStyleSheet("QSplitter::handle { background-color: #404040; } QSplitter::handle:hover { background-color: #606060; }")
        
        # 创建左侧面板（项目树）
        self.project_tree = ProjectTree()
        self.horizontal_splitter.addWidget(self.project_tree)
        
        # 连接项目树的信号
        self.project_tree.organism_created.connect(self.on_organism_created)
        self.project_tree.organism_deleted.connect(self.on_organism_deleted)
        # 连接项目树的选中信号
        self.project_tree.tree.itemSelectionChanged.connect(self.on_organism_selected)
        
        # 创建中央编辑区
        self.central_tab = QTabWidget()
        self.central_tab.setStyleSheet("""
            QTabWidget {
                background-color: #252526;
                color: #ffffff;
            }
            QTabBar::tab {
                background-color: #333333;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #444444;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-bottom: 2px solid #108ee9;
            }
            QTabBar::tab:hover {
                background-color: #404040;
            }
        """)
        
        # 添加编辑画布
        self.canvas = OrganismCanvas()
        self.central_tab.addTab(self.canvas, "生物编辑")
        
        # 添加模拟运行标签页
        self.simulation_tab = QWidget()
        self.simulation_layout = QVBoxLayout(self.simulation_tab)
        self.simulation_tab.setLayout(self.simulation_layout)
        
        # 初始化pygame
        import pygame
        pygame.init()
        
        # 创建模拟画布
        self.simulation_canvas = QWidget()
        self.simulation_canvas.setMinimumSize(800, 600)
        self.simulation_layout.addWidget(self.simulation_canvas)
        
        # 模拟参数调整面板
        self.params_group = QGroupBox("实时参数调整")
        self.params_layout = QHBoxLayout()
        self.params_group.setLayout(self.params_layout)
        
        # 添加参数控制
        # 能量参数
        self.energy_label = QLabel("初始能量:")
        self.energy_spin = QDoubleSpinBox()
        self.energy_spin.setRange(0, 1000)
        self.energy_spin.setValue(100)
        self.energy_spin.setSingleStep(10)
        self.params_layout.addWidget(self.energy_label)
        self.params_layout.addWidget(self.energy_spin)
        
        # 速度参数
        self.speed_label = QLabel("移动速度:")
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10)
        self.speed_spin.setValue(2)
        self.speed_spin.setSingleStep(0.5)
        self.params_layout.addWidget(self.speed_label)
        self.params_layout.addWidget(self.speed_spin)
        
        # 感知范围参数
        self.range_label = QLabel("感知范围:")
        self.range_spin = QDoubleSpinBox()
        self.range_spin.setRange(10, 200)
        self.range_spin.setValue(50)
        self.range_spin.setSingleStep(10)
        self.params_layout.addWidget(self.range_label)
        self.params_layout.addWidget(self.range_spin)
        
        # 应用参数按钮
        self.apply_params_btn = QPushButton("应用参数")
        self.apply_params_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
        """)
        self.apply_params_btn.clicked.connect(self.apply_parameters)
        self.params_layout.addWidget(self.apply_params_btn)
        
        self.params_layout.addStretch()
        
        self.simulation_layout.addWidget(self.params_group)
        
        # 模拟控制和编辑控制结合的布局
        self.control_layout = QHBoxLayout()
        
        # 模拟运行控制
        self.run_btn = QPushButton("运行模拟")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #108ee9;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        self.run_btn.clicked.connect(self.run_simulation)
        self.control_layout.addWidget(self.run_btn)
        
        self.pause_btn = QPushButton("暂停模拟")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #faad14;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ffc53d;
            }
        """)
        self.pause_btn.clicked.connect(self.pause_simulation)
        self.control_layout.addWidget(self.pause_btn)
        
        self.reset_btn = QPushButton("重置模拟")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5222d;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ff4d4f;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_simulation)
        self.control_layout.addWidget(self.reset_btn)
        
        self.control_layout.addStretch()
        
        # 编辑-模拟集成按钮
        self.apply_btn = QPushButton("应用到模拟")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_to_simulation)
        self.control_layout.addWidget(self.apply_btn)
        
        self.simulation_layout.addLayout(self.control_layout)
        
        # 添加生物行为预览标签
        self.preview_tab = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_tab)
        self.preview_tab.setLayout(self.preview_layout)
        
        # 创建预览画布
        self.preview_canvas = QWidget()
        self.preview_canvas.setMinimumSize(800, 400)
        self.preview_layout.addWidget(self.preview_canvas)
        
        # 预览控制
        self.preview_control_layout = QHBoxLayout()
        self.preview_run_btn = QPushButton("开始预览")
        self.preview_run_btn.setStyleSheet(self.run_btn.styleSheet())
        self.preview_run_btn.clicked.connect(self.start_preview)
        self.preview_control_layout.addWidget(self.preview_run_btn)
        
        self.preview_pause_btn = QPushButton("暂停预览")
        self.preview_pause_btn.setStyleSheet(self.pause_btn.styleSheet())
        self.preview_pause_btn.clicked.connect(self.pause_preview)
        self.preview_control_layout.addWidget(self.preview_pause_btn)
        
        self.preview_reset_btn = QPushButton("重置预览")
        self.preview_reset_btn.setStyleSheet(self.reset_btn.styleSheet())
        self.preview_reset_btn.clicked.connect(self.reset_preview)
        self.preview_control_layout.addWidget(self.preview_reset_btn)
        
        self.preview_control_layout.addStretch()
        
        self.preview_layout.addLayout(self.preview_control_layout)
        
        self.central_tab.addTab(self.simulation_tab, "模拟运行")
        self.central_tab.addTab(self.preview_tab, "行为预览")
        
        # 初始化模拟
        from ai_organism.simulation import Simulation
        self.simulation = Simulation(800, 600)
        
        # 初始化预览
        self.preview_simulation = Simulation(800, 400)
        self.is_preview_running = False
        self.preview_timer = None
        
        # 为预览画布添加绘制事件
        self.preview_canvas.paintEvent = self.draw_preview
        
        self.horizontal_splitter.addWidget(self.central_tab)
        
        # 创建右侧属性面板
        self.property_panel = PropertyPanel()
        self.horizontal_splitter.addWidget(self.property_panel)
        
        # 设置分割器比例
        self.horizontal_splitter.setSizes([200, 700, 250])
        
        # 添加分割器到主布局
        self.main_layout.addWidget(self.horizontal_splitter)
        
        # 创建控制台面板
        self.console = ConsolePanel()
        self.main_layout.addWidget(self.console)
        
        # 将编辑的生物应用到模拟
        self.apply_to_simulation()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #252526; color: #ffffff; border-top: 1px solid #404040;")
        self.setStatusBar(self.status_bar)
        
        # 初始化状态栏
        self.status_bar.showMessage("就绪")
        self.mode_label = QLabel("模式: 查看")
        self.mode_label.setStyleSheet("margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.mode_label)
        
        # 添加操作提示
        self.hint_label = QLabel("提示: 右键点击画布添加节点，拖拽节点调整位置")
        self.hint_label.setStyleSheet("color: #888888; font-size: 12px; margin-right: 20px;")
        self.status_bar.addPermanentWidget(self.hint_label)
        
        # 初始化控制台
        self.console.add_output("AI生命体编辑器已启动")
        self.console.add_output("欢迎使用PyQt6版编辑器")
        self.console.add_output("操作提示:")
        self.console.add_output("- 右键点击画布：添加传感器或效应器")
        self.console.add_output("- 拖拽节点：调整位置")
        self.console.add_output("- 右键点击节点：开始连接或删除节点")
        self.console.add_output("- 右键点击连接线：删除连接")
        self.console.add_output("- 滚轮：缩放节点")
        
        # 连接信号
        self._connect_signals()
        
        # 模拟运行状态
        self.is_simulation_running = False
        self.simulation_timer = None
        
        # 设置自动保存
        self.setup_auto_save()
        
        # 提示用户加载上次保存的项目
        import sys
        # 延迟执行，确保UI已完全初始化
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, self.prompt_load_last_project)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 监听画布选择变化，更新属性面板
        self.canvas.updateRequest.connect(self._on_canvas_updated)
        
        # 监听画布修改事件，标记项目为已修改
        self.canvas.projectModified.connect(self.mark_dirty)
        
        # 监听命令执行事件，更新撤销/重做状态
        self.canvas.commandExecuted.connect(self._update_undo_redo_status)
        
        # 为模拟画布添加绘制事件
        self.simulation_canvas.paintEvent = self.draw_simulation
        
        # 添加键盘事件
        self.simulation_canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.simulation_canvas.keyPressEvent = self.handle_simulation_key
        self.simulation_canvas.mousePressEvent = self.handle_simulation_mouse
    
    def _update_undo_redo_status(self):
        """更新撤销/重做按钮状态"""
        if hasattr(self, 'undo_action') and hasattr(self, 'redo_action'):
            self.undo_action.setEnabled(self.canvas.command_stack.can_undo())
            self.redo_action.setEnabled(self.canvas.command_stack.can_redo())
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为...", self)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        # 撤销/重做菜单项
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        # 查看菜单
        view_menu = menu_bar.addMenu("查看")
        
        # 模板菜单
        template_menu = menu_bar.addMenu("模板")
        
        # 保存模板
        save_template_action = QAction("保存当前生物为模板", self)
        save_template_action.setShortcut("Ctrl+Shift+S")
        save_template_action.triggered.connect(self.save_current_as_template)
        template_menu.addAction(save_template_action)
        
        template_menu.addSeparator()
        
        # 加载模板子菜单
        load_template_menu = template_menu.addMenu("加载模板")
        self.load_template_actions = []
        self.refresh_template_menu(load_template_menu)
        
        template_menu.addSeparator()
        
        # 管理模板
        manage_templates_action = QAction("管理模板", self)
        manage_templates_action.triggered.connect(self.manage_templates)
        template_menu.addAction(manage_templates_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        tool_bar = self.addToolBar("主工具栏")
        
        # 文件操作
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        tool_bar.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        tool_bar.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        tool_bar.addAction(save_action)
        
        tool_bar.addSeparator()
        
        # 撤销/重做
        self.undo_action_tool = QAction("撤销", self)
        self.undo_action_tool.setShortcut("Ctrl+Z")
        self.undo_action_tool.triggered.connect(self.undo)
        self.undo_action_tool.setEnabled(False)
        tool_bar.addAction(self.undo_action_tool)
        
        self.redo_action_tool = QAction("重做", self)
        self.redo_action_tool.setShortcut("Ctrl+Y")
        self.redo_action_tool.triggered.connect(self.redo)
        self.redo_action_tool.setEnabled(False)
        tool_bar.addAction(self.redo_action_tool)
        
        tool_bar.addSeparator()
        
        # 编辑操作
        delete_action = QAction("删除", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        tool_bar.addAction(delete_action)
        
        tool_bar.addSeparator()
        
        # 模拟控制
        run_action = QAction("运行模拟", self)
        run_action.triggered.connect(self.run_simulation)
        tool_bar.addAction(run_action)
        
        pause_action = QAction("暂停模拟", self)
        pause_action.triggered.connect(self.pause_simulation)
        tool_bar.addAction(pause_action)
        
        reset_action = QAction("重置模拟", self)
        reset_action.triggered.connect(self.reset_simulation)
        tool_bar.addAction(reset_action)
        
        tool_bar.addSeparator()
        
        # 编辑-模拟集成
        apply_action = QAction("应用到模拟", self)
        apply_action.triggered.connect(self.apply_to_simulation)
        tool_bar.addAction(apply_action)
    
    def undo(self):
        """撤销操作"""
        self.canvas.command_stack.undo()
        self.canvas.update()
        self._update_undo_redo_status()
        self.updateRequest.emit()
        self.console.add_output("撤销操作")
    
    def redo(self):
        """重做操作"""
        self.canvas.command_stack.redo()
        self.canvas.update()
        self._update_undo_redo_status()
        self.updateRequest.emit()
        self.console.add_output("重做操作")
    
    def delete_selected(self):
        """删除选中的对象"""
        if self.canvas.selected_node:
            # 使用命令模式删除节点
            command = DeleteNodeCommand(self.canvas, self.canvas.selected_node)
            self.canvas.command_stack.execute(command)
            self.canvas.selected_node = None
            self.canvas.update()
            self._update_undo_redo_status()
            self.mark_dirty()
            self.canvas.commandExecuted.emit()
            self.console.add_output("删除选中节点")
        
    def new_project(self):
        """新建项目"""
        self.console.add_output("新建项目")
    
    def open_project(self):
        """打开项目"""
        self.console.add_output("打开项目")
    
    def save_project(self):
        """保存项目"""
        self.console.add_output("保存项目")
    
    def save_project_as(self):
        """另存为项目"""
        self.console.add_output("另存为项目")
    
    def show_about(self):
        """显示关于信息"""
        self.console.add_output("显示关于信息")
    
    def updateRequest(self):
        """更新请求信号"""
        pass
    
    def refresh_template_menu(self, menu):
        """刷新模板菜单"""
        # 清除现有操作
        for action in self.load_template_actions:
            menu.removeAction(action)
        self.load_template_actions.clear()
        
        # 获取所有模板
        all_templates = self.template_manager.get_all_templates()
        
        # 按类型分组
        preset_templates = [t for t in all_templates if t["type"] == "preset"]
        custom_templates = [t for t in all_templates if t["type"] == "custom"]
        
        # 添加预设模板
        if preset_templates:
            preset_menu = menu.addMenu("预设模板")
            for template in preset_templates:
                action = QAction(template["name"], self)
                action.setToolTip(template["description"])
                action.triggered.connect(lambda checked, t=template: self.load_template_by_id(t["id"]))
                preset_menu.addAction(action)
                self.load_template_actions.append(action)
        
        # 添加自定义模板
        if custom_templates:
            custom_menu = menu.addMenu("自定义模板")
            for template in custom_templates:
                action = QAction(template["name"], self)
                action.setToolTip(template["description"])
                action.triggered.connect(lambda checked, t=template: self.load_template_by_id(t["id"]))
                custom_menu.addAction(action)
                self.load_template_actions.append(action)
    
    def save_current_as_template(self):
        """保存当前生物为模板"""
        # 从画布获取节点和连接信息
        nodes = self.canvas.nodes
        connections = self.canvas.connections
        
        # 转换为模板数据格式
        template_data = {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "x": node.x,
                    "y": node.y,
                    "radius": node.radius
                } for node in nodes
            ],
            "connections": [
                {
                    "start_node": conn.start_node.id,
                    "end_node": conn.end_node.id,
                    "weight": conn.weight
                } for conn in connections
            ]
        }
        
        # 弹出对话框获取模板名称和描述
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("保存为模板")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("输入模板名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.template_name_edit)
        layout.addLayout(name_layout)
        
        # 描述输入
        desc_layout = QHBoxLayout()
        desc_label = QLabel("描述:")
        self.template_desc_edit = QTextEdit()
        self.template_desc_edit.setPlaceholderText("输入模板描述")
        self.template_desc_edit.setMinimumHeight(100)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.template_desc_edit)
        layout.addLayout(desc_layout)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = self.template_name_edit.text().strip()
            description = self.template_desc_edit.toPlainText().strip()
            
            if name:
                # 保存模板
                template_id = self.template_manager.create_template_from_organism(template_data, name, description)
                self.console.add_output(f"成功保存模板: {name} (ID: {template_id})")
                
                # 刷新模板菜单
                self.refresh_template_menu(self.menuBar().findChild(QMenu, "加载模板"))
            else:
                self.console.add_output("保存模板失败: 模板名称不能为空")
    
    def load_template_by_id(self, template_id):
        """根据ID加载模板"""
        try:
            template = self.template_manager.load_template(template_id)
            self.console.add_output(f"加载模板: {template['name']}")
            
            # 清除当前画布内容
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            
            # 加载模板数据
            template_data = template["data"]
            
            # 创建节点
            node_dict = {}
            for node_data in template_data["nodes"]:
                node = Node(
                    node_data["id"],
                    node_data["x"],
                    node_data["y"],
                    node_data["type"]
                )
                if "radius" in node_data:
                    node.radius = node_data["radius"]
                self.canvas.nodes.append(node)
                node_dict[node.id] = node
            
            # 创建连接
            for conn_data in template_data["connections"]:
                start_node = node_dict.get(conn_data["start_node"])
                end_node = node_dict.get(conn_data["end_node"])
                if start_node and end_node:
                    connection = ConnectionLine(start_node, end_node)
                    if "weight" in conn_data:
                        connection.weight = conn_data["weight"]
                    self.canvas.connections.append(connection)
            
            # 更新画布
            self.canvas.update()
            self.canvas.updateRequest.emit()
            self.mark_dirty()
            
        except Exception as e:
            self.console.add_output(f"加载模板失败: {str(e)}")
    
    def manage_templates(self):
        """管理模板"""
        self.console.add_output("打开模板管理器")
        # 这里可以实现模板管理对话框
        # 包括查看、编辑、删除自定义模板等功能
    
    def _on_canvas_updated(self):
        """画布更新时的处理"""
        # 更新属性面板
        self.property_panel.update_properties(self.canvas.selected_node)
        
        # 更新状态栏提示
        if self.canvas.selected_node:
            # 显示选中对象的详细信息
            node = self.canvas.selected_node
            selected_count = len(self.canvas.selected_nodes)
            if selected_count > 1:
                self.status_bar.showMessage(f"已选择 {selected_count} 个对象")
            else:
                self.status_bar.showMessage(f"已选择: {node.id} ({node.type})")
        else:
            self.status_bar.showMessage("就绪")
    
    def mark_dirty(self):
        """标记项目为已修改"""
        self.is_dirty = True
        # 更新窗口标题，添加星号表示已修改
        current_title = self.windowTitle()
        if not current_title.endswith(" *"):
            self.setWindowTitle(current_title + " *")
    
    def unmark_dirty(self):
        """标记项目为未修改"""
        self.is_dirty = False
        # 更新窗口标题，移除星号
        current_title = self.windowTitle()
        if current_title.endswith(" *"):
            self.setWindowTitle(current_title[:-2])
    
    def show_status_message(self, message: str, duration: int = 3000):
        """显示临时状态消息"""
        self.status_bar.showMessage(message)
        # 设置定时器，一段时间后恢复默认消息
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, self._restore_status_message)
    
    def _restore_status_message(self):
        """恢复默认状态消息"""
        self._on_canvas_updated()
    
    def confirm_action(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def draw_simulation(self, event):
        """绘制模拟内容"""
        painter = QPainter(self.simulation_canvas)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 清屏
        painter.fillRect(event.rect(), QColor(20, 20, 30))
        
        # 绘制模拟
        import pygame
        # 在PyQt应用中使用pygame，不需要设置视频模式
        # 使用基本Surface格式，避免convert_alpha()导致的错误
        surface = pygame.Surface((800, 600))
        self.simulation.draw(surface)
        
        # 将Pygame表面转换为Qt图像
        from PyQt6.QtGui import QImage
        
        try:
            # 使用pygame.image.tostring方法，避免numpy数组转换的坐标系问题
            # 首先将表面转换为RGB格式
            rgb_surface = pygame.transform.scale(surface, (800, 600))
            # 使用tostring获取图像数据
            image_data = pygame.image.tostring(rgb_surface, "RGB")
            
            # 创建QImage
            qimage = QImage(image_data, 800, 600, 800 * 3, QImage.Format.Format_RGB888)
            
            # 绘制到Qt画布
            painter.drawImage(0, 0, qimage)
        except Exception as e:
            # 如果转换失败，绘制简单的背景和错误信息
            painter.fillRect(event.rect(), QColor(20, 20, 30))
            error_text = f"绘制错误: {str(e)}"
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(100, 100, error_text)
    
    def draw_preview(self, event):
        """绘制生物行为预览"""
        painter = QPainter(self.preview_canvas)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 清屏
        painter.fillRect(event.rect(), QColor(20, 20, 30))
        
        # 绘制预览
        import pygame
        surface = pygame.Surface((800, 400))
        self.preview_simulation.draw(surface)
        
        # 将Pygame表面转换为Qt图像
        from PyQt6.QtGui import QImage
        
        try:
            # 使用pygame.image.tostring方法，避免numpy数组转换的坐标系问题
            rgb_surface = pygame.transform.scale(surface, (800, 400))
            image_data = pygame.image.tostring(rgb_surface, "RGB")
            
            # 创建QImage
            qimage = QImage(image_data, 800, 400, 800 * 3, QImage.Format.Format_RGB888)
            
            # 绘制到Qt画布
            painter.drawImage(0, 0, qimage)
        except Exception as e:
            # 如果转换失败，绘制简单的背景和错误信息
            painter.fillRect(event.rect(), QColor(20, 20, 30))
            error_text = f"预览绘制错误: {str(e)}"
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(100, 100, error_text)
    
    def start_preview(self):
        """开始行为预览"""
        if not self.is_preview_running:
            self.is_preview_running = True
            from PyQt6.QtCore import QTimer
            self.preview_timer = QTimer()
            self.preview_timer.timeout.connect(self.update_preview)
            self.preview_timer.start(16)  # 60 FPS
            self.console.add_output("开始生物行为预览")
    
    def pause_preview(self):
        """暂停行为预览"""
        if self.is_preview_running:
            self.is_preview_running = False
            if self.preview_timer:
                self.preview_timer.stop()
                self.preview_timer = None
            self.console.add_output("暂停生物行为预览")
    
    def reset_preview(self):
        """重置行为预览"""
        self.pause_preview()
        from ai_organism.simulation import Simulation
        self.preview_simulation = Simulation(800, 400)
        # 应用当前编辑的生物到预览
        self.apply_to_preview()
        self.preview_canvas.update()
        self.console.add_output("重置生物行为预览")
    
    def update_preview(self):
        """更新行为预览"""
        self.preview_simulation.update()
        self.preview_canvas.update()
    
    def apply_to_preview(self):
        """将编辑的生物应用到预览"""
        # 从画布获取节点和连接信息
        nodes = self.canvas.nodes
        connections = self.canvas.connections
        
        # 清除现有生物
        self.preview_simulation.organisms.clear()
        
        # 找出生物节点
        organism_nodes = [node for node in nodes if node.type == "organism"]
        
        if organism_nodes:
            # 将节点和连接转换为生物对象
            # 这里需要根据实际的生物模型进行转换
            self.console.add_output(f"应用{len(organism_nodes)}个生物到预览")
    
    def apply_parameters(self):
        """应用参数调整"""
        # 获取参数值
        energy = self.energy_spin.value()
        speed = self.speed_spin.value()
        range_value = self.range_spin.value()
        
        # 应用到当前模拟
        self.console.add_output(f"应用参数: 初始能量={energy}, 移动速度={speed}, 感知范围={range_value}")
        
        # 应用到预览模拟
        if hasattr(self, 'preview_simulation'):
            self.console.add_output(f"应用参数到预览模拟")
        
        # 触发模拟更新
        self.simulation_canvas.update()
        if hasattr(self, 'preview_canvas'):
            self.preview_canvas.update()
    
    def run_simulation(self):
        """运行模拟"""
        if not self.is_simulation_running:
            self.is_simulation_running = True
            from PyQt6.QtCore import QTimer
            self.simulation_timer = QTimer()
            self.simulation_timer.timeout.connect(self.update_simulation)
            self.simulation_timer.start(16)  # 60 FPS
            self.console.add_output("模拟已启动")
    
    def pause_simulation(self):
        """暂停模拟"""
        if self.is_simulation_running:
            self.is_simulation_running = False
            if self.simulation_timer:
                self.simulation_timer.stop()
                self.simulation_timer = None
            self.console.add_output("模拟已暂停")
    
    def stop_simulation(self):
        """停止模拟（与暂停功能相同）"""
        self.pause_simulation()
    
    def reset_simulation(self):
        """重置模拟"""
        self.pause_simulation()
        from ai_organism.simulation import Simulation
        self.simulation = Simulation(800, 600)
        self.simulation_canvas.update()
        self.console.add_output("模拟已重置")
    
    def update_simulation(self):
        """更新模拟"""
        self.simulation.update()
        self.simulation_canvas.update()
    
    def handle_simulation_key(self, event):
        """处理模拟键盘事件"""
        import pygame
        # 将Qt键盘事件转换为Pygame事件
        pygame_key = getattr(pygame, f"K_{event.key.name}", None)
        if pygame_key:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame_key))
    
    def handle_simulation_mouse(self, event):
        """处理模拟鼠标事件"""
        # 传递点击事件给模拟
        self.simulation.handle_click((event.pos().x(), event.pos().y()))
        self.simulation_canvas.update()
    
    def apply_to_simulation(self):
        """将编辑的生物应用到模拟中"""
        # 从画布获取节点和连接信息
        nodes = self.canvas.nodes
        connections = self.canvas.connections
        
        # 清除现有生物
        self.simulation.organisms.clear()
        
        # 找出生物节点
        organism_nodes = [node for node in nodes if node.type == "organism"]
        if not organism_nodes:
            self.console.add_output("错误: 画布上没有生物节点")
            return
        
        # 使用第一个生物节点作为中心
        organism_node = organism_nodes[0]
        
        # 创建新生物
        from ai_organism.core import Organism
        organism = Organism(organism_node.id, (400, 300))
        
        # 添加传感器和效应器
        sensor_ids = []
        actuator_ids = []
        
        for node in nodes:
            if node == organism_node:
                continue  # 跳过生物节点
            
            # 计算相对于生物体中心的位置
            rel_x = node.x - 300  # 画布中心是300, 200
            rel_y = node.y - 200
            
            if node.type == "sensor":
                # 根据节点ID生成有效的传感器ID
                sensor_id = f"sensor_{node.id[-1]}"  # 只保留最后一个字符
                from ai_organism.tools import LightSensor, TouchSensor
                
                # 随机选择传感器类型
                import random
                if random.random() > 0.5:
                    sensor = LightSensor(sensor_id, (rel_x, rel_y))
                    self.console.add_output(f"添加光感传感器: {sensor_id} at ({rel_x}, {rel_y})")
                else:
                    sensor = TouchSensor(sensor_id, (rel_x, rel_y))
                    self.console.add_output(f"添加触觉传感器: {sensor_id} at ({rel_x}, {rel_y})")
                
                organism.add_sensor(sensor)
                sensor_ids.append(sensor_id)
            elif node.type == "actuator":
                # 根据节点ID生成有效的效应器ID
                actuator_id = f"actuator_{node.id[-1]}"  # 只保留最后一个字符
                from ai_organism.tools import MuscleActuator, CiliaActuator
                
                # 随机选择效应器类型
                import random
                if random.random() > 0.5:
                    actuator = MuscleActuator(actuator_id, (rel_x, rel_y))
                    self.console.add_output(f"添加肌肉效应器: {actuator_id} at ({rel_x}, {rel_y})")
                else:
                    actuator = CiliaActuator(actuator_id, (rel_x, rel_y))
                    self.console.add_output(f"添加纤毛效应器: {actuator_id} at ({rel_x}, {rel_y})")
                
                organism.add_actuator(actuator)
                actuator_ids.append(actuator_id)
        
        # 添加连接
        for connection in connections:
            try:
                # 处理连接
                start_node = connection.start_node
                end_node = connection.end_node
                
                # 生成有效的工具ID
                start_id = None
                end_id = None
                
                if start_node.type == "sensor":
                    start_id = f"sensor_{start_node.id[-1]}"
                elif start_node.type == "actuator":
                    start_id = f"actuator_{start_node.id[-1]}"
                
                if end_node.type == "sensor":
                    end_id = f"sensor_{end_node.id[-1]}"
                elif end_node.type == "actuator":
                    end_id = f"actuator_{end_node.id[-1]}"
                
                # 只有当连接的两端都是传感器或效应器时，才添加连接
                if start_id and end_id:
                    organism.connect_tools(
                        start_id,
                        end_id,
                        connection.weight
                    )
                    self.console.add_output(f"创建连接: {start_id} -> {end_id} (权重: {connection.weight})")
                else:
                    self.console.add_output(f"跳过无效连接: {start_node.id} -> {end_node.id}")
            except Exception as e:
                self.console.add_output(f"连接失败: {e}")
        
        # 添加到模拟中，确保生物有实际功能
        self.simulation.organisms.append(organism)
        self.simulation.selected_organism = organism
        
        # 添加一些基础记忆，使生物能够行动
        from ai_organism.core import MemoryGene
        # 添加光感传感器到效应器的连接记忆
        if sensor_ids and actuator_ids:
            base_memory = MemoryGene(
                "LIGHT_high",
                {actuator_id: 0.7 for actuator_id in actuator_ids},
                0.8
            )
            organism.memory_bank.append(base_memory)
        
        self.console.add_output(f"已将编辑的生物应用到模拟中，包含 {len(nodes)} 个节点和 {len(connections)} 个连接")
        self.console.add_output(f"生物ID: {organism.id}, 传感器: {len(sensor_ids)}, 效应器: {len(actuator_ids)}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        menu_bar.setStyleSheet("background-color: #252526; color: #ffffff;")
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        menu_bar.addMenu(file_menu)
        
        # 编辑菜单
        edit_menu = QMenu("编辑", self)
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        delete_action = QAction("删除", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.delete)
        edit_menu.addAction(delete_action)
        
        menu_bar.addMenu(edit_menu)
        
        # 视图菜单
        view_menu = QMenu("视图", self)
        view_project_tree_action = QAction("显示项目树", self)
        view_project_tree_action.setShortcut("Ctrl+1")
        view_project_tree_action.triggered.connect(self.toggle_project_tree)
        view_menu.addAction(view_project_tree_action)
        
        view_property_panel_action = QAction("显示属性面板", self)
        view_property_panel_action.setShortcut("Ctrl+2")
        view_property_panel_action.triggered.connect(self.toggle_property_panel)
        view_menu.addAction(view_property_panel_action)
        
        view_console_action = QAction("显示控制台", self)
        view_console_action.setShortcut("Ctrl+3")
        view_console_action.triggered.connect(self.toggle_console)
        view_menu.addAction(view_console_action)
        
        menu_bar.addMenu(view_menu)
        
        # 工具菜单
        tool_menu = QMenu("工具", self)
        run_simulation_action = QAction("运行模拟", self)
        run_simulation_action.setShortcut("F5")
        run_simulation_action.triggered.connect(self.run_simulation)
        tool_menu.addAction(run_simulation_action)
        
        stop_simulation_action = QAction("停止模拟", self)
        stop_simulation_action.setShortcut("F6")
        stop_simulation_action.triggered.connect(self.stop_simulation)
        tool_menu.addAction(stop_simulation_action)
        
        tool_menu.addSeparator()
        
        export_organism_action = QAction("导出生物", self)
        export_organism_action.triggered.connect(self.export_organism)
        tool_menu.addAction(export_organism_action)
        
        import_organism_action = QAction("导入生物", self)
        import_organism_action.triggered.connect(self.import_organism)
        tool_menu.addAction(import_organism_action)
        
        menu_bar.addMenu(tool_menu)
        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        help_action = QAction("使用帮助", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        menu_bar.addMenu(help_menu)
        
        self.setMenuBar(menu_bar)
    
    def create_tool_bar(self):
        """创建工具栏"""
        tool_bar = QToolBar("主工具栏")
        tool_bar.setStyleSheet("""
            QToolBar {
                background-color: #252526;
                color: #ffffff;
                border: none;
            }
            QToolButton {
                color: #ffffff;
                padding: 4px 8px;
                border: 1px solid transparent;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #404040;
                border: 1px solid #606060;
            }
            QToolButton:pressed {
                background-color: #505050;
            }
            QLabel {
                color: #ffffff;
                margin-right: 5px;
            }
        """)
        
        # 添加工具栏按钮
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        tool_bar.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        tool_bar.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        tool_bar.addAction(save_action)
        
        tool_bar.addSeparator()
        
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        tool_bar.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        tool_bar.addAction(redo_action)
        
        tool_bar.addSeparator()
        
        run_action = QAction("运行", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_simulation)
        tool_bar.addAction(run_action)
        
        stop_action = QAction("停止", self)
        stop_action.setShortcut("F6")
        stop_action.triggered.connect(self.stop_simulation)
        tool_bar.addAction(stop_action)
        
        tool_bar.addSeparator()
        
        # 添加模式选择
        mode_combo = QComboBox()
        mode_combo.addItems(["查看", "添加传感器", "添加效应器", "连接"])
        mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #666666;
            }
            QComboBox::drop-down {
                border-left: 1px solid #444444;
            }
            QComboBox::down-arrow {
                color: #ffffff;
            }
        """)
        mode_combo.currentTextChanged.connect(self.change_mode)
        tool_bar.addWidget(QLabel("模式: "))
        tool_bar.addWidget(mode_combo)
        
        self.addToolBar(tool_bar)
    
    # 菜单和工具栏操作
    def new_project(self):
        """新建项目"""
        # 重置画布
        self.canvas.nodes.clear()
        self.canvas.connections.clear()
        self.canvas._create_default_nodes()
        self.canvas.update()
        # 清除当前项目数据
        self.organisms.clear()
        self.current_organism = None
        self.last_project_path = None
        # 标记为已修改
        self.mark_dirty()
        self.console.add_output("新建项目")
        self.status_bar.showMessage("新建项目")
    
    def open_project(self):
        """打开项目"""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "AI生命体项目 (*.json);;所有文件 (*.*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                # 清空当前项目
                self.organisms.clear()
                self.canvas.nodes.clear()
                self.canvas.connections.clear()
                self.current_organism = None
                
                # 重建项目树
                root = self.project_tree.tree.invisibleRootItem()
                for i in range(root.childCount()):
                    project_item = root.child(i)
                    if project_item.text(0) == "AI生命体项目":
                        for j in range(project_item.childCount()):
                            child_item = project_item.child(j)
                            if child_item.text(0) == "生物列表":
                                # 清空生物列表
                                while child_item.childCount() > 0:
                                    child_item.takeChild(0)
                                
                                # 从文件中加载生物
                                if "organisms" in project_data:
                                    for organism_name, organism_data in project_data["organisms"].items():
                                        # 创建生物节点
                                        new_organism = QTreeWidgetItem(child_item, [organism_name])
                                        new_organism.setIcon(0, QIcon.fromTheme("object-group"))
                                        
                                        # 保存生物状态到内存
                                        nodes = []
                                        for node_data in organism_data["nodes"]:
                                            node = Node(node_data["id"], node_data["x"], node_data["y"], node_data["type"])
                                            node.radius = node_data["radius"]
                                            nodes.append(node)
                                        
                                        connections = []
                                        # 创建节点ID到节点的映射
                                        node_map = {node.id: node for node in nodes}
                                        for conn_data in organism_data["connections"]:
                                            start_node = node_map[conn_data["start_node_id"]]
                                            end_node = node_map[conn_data["end_node_id"]]
                                            conn = ConnectionLine(start_node, end_node)
                                            conn.weight = conn_data["weight"]
                                            connections.append(conn)
                                        
                                        self.organisms[organism_name] = (nodes, connections)
                                
                                # 展开生物列表
                                child_item.setExpanded(True)
                                break
                
                # 保存项目路径
                self.last_project_path = file_path
                # 重置dirty状态
                self.is_dirty = False
                
                self.console.add_output(f"成功打开项目: {file_path}")
                self.status_bar.showMessage(f"已打开项目: {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "打开项目失败", f"无法打开项目文件: {str(e)}")
                self.console.add_output(f"打开项目失败: {str(e)}")
    
    def save_project(self, file_path=None):
        """保存项目"""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        # 如果没有提供文件路径，使用上次保存的路径或打开文件选择对话框
        if not file_path:
            file_path = self.last_project_path
            if not file_path:
                file_path, _ = QFileDialog.getSaveFileName(self, "保存项目", "", "AI生命体项目 (*.json);;所有文件 (*.*)")
        
        if file_path:
            try:
                # 确保当前生物的状态已保存
                if self.current_organism:
                    self.save_current_organism()
                
                # 准备项目数据
                project_data = {
                    "version": "1.0",
                    "organisms": {}
                }
                
                # 保存所有生物的状态
                for organism_name, (nodes, connections) in self.organisms.items():
                    organism_data = {
                        "nodes": [],
                        "connections": []
                    }
                    
                    # 保存节点
                    for node in nodes:
                        organism_data["nodes"].append({
                            "id": node.id,
                            "x": node.x,
                            "y": node.y,
                            "type": node.type,
                            "radius": node.radius
                        })
                    
                    # 保存连接
                    for conn in connections:
                        organism_data["connections"].append({
                            "start_node_id": conn.start_node.id,
                            "end_node_id": conn.end_node.id,
                            "weight": conn.weight
                        })
                    
                    project_data["organisms"][organism_name] = organism_data
                
                # 保存到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)
                
                # 保存项目路径
                self.last_project_path = file_path
                # 重置dirty状态
                self.is_dirty = False
                
                self.console.add_output(f"成功保存项目: {file_path}")
                self.status_bar.showMessage(f"已保存项目: {file_path}")
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "保存项目失败", f"无法保存项目文件: {str(e)}")
                self.console.add_output(f"保存项目失败: {str(e)}")
    
    def prompt_load_last_project(self):
        """提示用户加载上次保存的项目"""
        import os
        if self.last_project_path and os.path.exists(self.last_project_path):
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "加载上次项目", 
                                      f"是否加载上次保存的项目？\n{self.last_project_path}",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.open_project_from_path(self.last_project_path)
    
    def open_project_from_path(self, file_path):
        """从指定路径打开项目"""
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 清空当前项目
            self.organisms.clear()
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            self.current_organism = None
            
            # 重建项目树
            root = self.project_tree.tree.invisibleRootItem()
            for i in range(root.childCount()):
                project_item = root.child(i)
                if project_item.text(0) == "AI生命体项目":
                    for j in range(project_item.childCount()):
                        child_item = project_item.child(j)
                        if child_item.text(0) == "生物列表":
                            # 清空生物列表
                            while child_item.childCount() > 0:
                                child_item.takeChild(0)
                            
                            # 从文件中加载生物
                            if "organisms" in project_data:
                                for organism_name, organism_data in project_data["organisms"].items():
                                    # 创建生物节点
                                    new_organism = QTreeWidgetItem(child_item, [organism_name])
                                    new_organism.setIcon(0, QIcon.fromTheme("object-group"))
                                    
                                    # 保存生物状态到内存
                                    nodes = []
                                    for node_data in organism_data["nodes"]:
                                        node = Node(node_data["id"], node_data["x"], node_data["y"], node_data["type"])
                                        node.radius = node_data["radius"]
                                        nodes.append(node)
                                    
                                    connections = []
                                    # 创建节点ID到节点的映射
                                    node_map = {node.id: node for node in nodes}
                                    for conn_data in organism_data["connections"]:
                                        start_node = node_map[conn_data["start_node_id"]]
                                        end_node = node_map[conn_data["end_node_id"]]
                                        conn = ConnectionLine(start_node, end_node)
                                        conn.weight = conn_data["weight"]
                                        connections.append(conn)
                                    
                                    self.organisms[organism_name] = (nodes, connections)
                            
                            # 展开生物列表
                            child_item.setExpanded(True)
                            break
            
            # 保存项目路径
            self.last_project_path = file_path
            
            self.console.add_output(f"成功打开项目: {file_path}")
            self.status_bar.showMessage(f"已打开项目: {file_path}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "打开项目失败", f"无法打开项目文件: {str(e)}")
            self.console.add_output(f"打开项目失败: {str(e)}")
    
    def setup_auto_save(self):
        """设置自动保存功能，参考VSCode风格"""
        from PyQt6.QtCore import QTimer
        
        # 清理之前的定时器
        if hasattr(self, 'auto_save_timer') and self.auto_save_timer:
            self.auto_save_timer.stop()
            self.auto_save_timer.deleteLater()
        
        if self.auto_save_enabled:
            if self.auto_save_mode == "afterDelay":
                # 延迟一段时间后自动保存
                self.auto_save_timer = QTimer()
                self.auto_save_timer.timeout.connect(self.auto_save)
                self.auto_save_timer.start(self.auto_save_delay)  # 使用配置的延迟时间
                self.console.add_output(f"自动保存已启用: {self.auto_save_mode}, 延迟 {self.auto_save_delay} 毫秒")
            elif self.auto_save_mode == "onFocusChange":
                # 当编辑器失去焦点时自动保存
                self.console.add_output(f"自动保存已启用: {self.auto_save_mode}")
            elif self.auto_save_mode == "onWindowChange":
                # 当窗口失去焦点时自动保存
                self.console.add_output(f"自动保存已启用: {self.auto_save_mode}")
        else:
            self.console.add_output("自动保存已禁用")
    
    def auto_save(self):
        """自动保存项目"""
        if self.is_dirty and self.last_project_path and self.organisms:
            self.save_project(self.last_project_path)
            self.is_dirty = False  # 保存后重置dirty状态
            self.console.add_output(f"自动保存项目: {self.last_project_path}")
            self.status_bar.showMessage(f"已自动保存项目")
    
    def mark_dirty(self):
        """标记项目有未保存的更改"""
        self.is_dirty = True
        self.status_bar.showMessage("项目已修改")
    
    def save_all(self):
        """保存所有内容，参考VSCode的Save All"""
        if self.last_project_path:
            self.save_project(self.last_project_path)
            self.is_dirty = False
            self.console.add_output(f"已保存所有内容到: {self.last_project_path}")
            self.status_bar.showMessage("已保存所有内容")
        else:
            # 如果没有保存路径，显示保存对话框
            self.save_project()
    
    def focusOutEvent(self, event):
        """处理失去焦点事件"""
        super().focusOutEvent(event)
        
        if self.auto_save_mode == "onFocusChange" or self.save_on_focus_change:
            self.auto_save()
    
    def changeEvent(self, event):
        """处理窗口状态变化事件"""
        super().changeEvent(event)
        
        # 处理窗口失去焦点事件
        if event.type() == event.Type.WindowStateChange and not self.isActiveWindow():
            if self.auto_save_mode == "onWindowChange":
                self.auto_save()
    
    def load_config(self):
        """加载配置文件"""
        import os
        import json
        
        # 默认配置
        self.last_project_path = None
        self.auto_save_enabled = True
        self.auto_save_delay = 1000
        self.auto_save_mode = "afterDelay"
        self.save_on_focus_change = True
        self.save_on_close = True
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载配置项
                if "last_project_path" in config:
                    self.last_project_path = config["last_project_path"]
                if "auto_save_enabled" in config:
                    self.auto_save_enabled = config["auto_save_enabled"]
                if "auto_save_delay" in config:
                    self.auto_save_delay = config["auto_save_delay"]
                if "auto_save_mode" in config:
                    self.auto_save_mode = config["auto_save_mode"]
                if "save_on_focus_change" in config:
                    self.save_on_focus_change = config["save_on_focus_change"]
                if "save_on_close" in config:
                    self.save_on_close = config["save_on_close"]
                
                self.console.add_output(f"已加载配置: {self.last_project_path}")
            except Exception as e:
                self.console.add_output(f"加载配置失败: {str(e)}")
    
    def save_config(self):
        """保存配置文件"""
        import json
        try:
            config = {
                "last_project_path": self.last_project_path,
                "auto_save_enabled": self.auto_save_enabled,
                "auto_save_delay": self.auto_save_delay,
                "auto_save_mode": self.auto_save_mode,
                "save_on_focus_change": self.save_on_focus_change,
                "save_on_close": self.save_on_close
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.console.add_output(f"已保存配置: {self.last_project_path}")
        except Exception as e:
            self.console.add_output(f"保存配置失败: {str(e)}")
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 检查是否有未保存的更改
        if self.organisms:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "保存项目", 
                                      "您有未保存的更改，是否保存项目？",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                      QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                # 保存项目
                self.save_project()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                # 不保存，直接关闭
                event.accept()
            else:
                # 取消关闭
                event.ignore()
        
        # 保存配置
        self.save_config()
        event.accept()
    
    def undo(self):
        """撤销操作"""
        self.console.add_output("撤销操作")
        self.status_bar.showMessage("撤销操作")
    
    def redo(self):
        """重做操作"""
        self.console.add_output("重做操作")
        self.status_bar.showMessage("重做操作")
    
    def copy(self):
        """复制操作"""
        if self.canvas.selected_node:
            self.console.add_output(f"复制节点: {self.canvas.selected_node.id}")
            self.status_bar.showMessage(f"复制节点: {self.canvas.selected_node.id}")
    
    def paste(self):
        """粘贴操作"""
        self.console.add_output("粘贴操作")
        self.status_bar.showMessage("粘贴操作")
    
    def delete(self):
        """删除操作"""
        if self.canvas.selected_node:
            self.canvas._delete_node()
            self.console.add_output("删除节点")
            self.status_bar.showMessage("删除节点")
    
    def toggle_project_tree(self):
        """切换项目树显示"""
        # 切换项目树的可见性
        self.project_tree.setVisible(not self.project_tree.isVisible())
        self.console.add_output("切换项目树显示")
        self.status_bar.showMessage("切换项目树显示")
    
    def toggle_property_panel(self):
        """切换属性面板显示"""
        # 切换属性面板的可见性
        self.property_panel.setVisible(not self.property_panel.isVisible())
        self.console.add_output("切换属性面板显示")
        self.status_bar.showMessage("切换属性面板显示")
    
    def toggle_console(self):
        """切换控制台显示"""
        self.console.setVisible(not self.console.isVisible())
        self.console.add_output("切换控制台显示")
        self.status_bar.showMessage("切换控制台显示")
    
    def export_organism(self):
        """导出生物"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "导出生物", "", "AI生命体 (*.json);;所有文件 (*.*)")
        if file_path:
            self.console.add_output(f"导出生物: {file_path}")
            self.status_bar.showMessage(f"导出生物: {file_path}")
    
    def import_organism(self):
        """导入生物"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "导入生物", "", "AI生命体 (*.json);;所有文件 (*.*)")
        if file_path:
            self.console.add_output(f"导入生物: {file_path}")
            self.status_bar.showMessage(f"导入生物: {file_path}")
    
    def show_help(self):
        """显示帮助"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "使用帮助", "AI生命体编辑器使用说明:\n\n"+
                                "- 右键点击画布添加节点\n"+
                                "- 拖拽节点调整位置\n"+
                                "- 右键点击节点开始连接\n"+
                                "- 右键点击连接线删除连接\n"+
                                "- 滚轮缩放节点\n"+
                                "- 应用到模拟按钮将编辑的生物应用到模拟")
        self.console.add_output("显示帮助")
    
    def show_about(self):
        """显示关于"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于AI生命体编辑器", "AI生命体编辑器 - PyQt6版\n\n"+
                         "基于PyQt6开发的AI生命体可视化编辑器\n"+
                         "支持节点连线编辑和实时模拟\n\n"+
                         "版本: 1.0")
        self.console.add_output("显示关于")
    
    def change_mode(self, mode):
        """切换编辑模式"""
        self.console.add_output(f"切换到{mode}模式")
        self.status_bar.showMessage(f"模式: {mode}")
        for widget in self.status_bar.findChildren(QLabel):
            if widget.text().startswith("模式:"):
                widget.setText(f"模式: {mode}")
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 检查是否有未保存的更改
        if self.organisms:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "保存项目", 
                                      "您有未保存的更改，是否保存项目？",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                      QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                # 保存项目
                self.save_project()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                # 不保存，直接关闭
                event.accept()
            else:
                # 取消关闭
                event.ignore()
    
    def on_organism_created(self, organism_name):
        """处理生物创建信号"""
        # 保存当前生物的状态（如果有）
        if self.current_organism and self.current_organism in self.organisms:
            self.save_current_organism()
        
        # 清除当前画布的节点和连接
        self.canvas.nodes.clear()
        self.canvas.connections.clear()
        
        # 创建新的生物节点和相关工具
        center_x, center_y = 300, 200
        
        # 创建生物体节点
        organism_node = Node(organism_name, center_x, center_y, "organism")
        self.canvas.nodes.append(organism_node)
        
        # 创建传感器节点
        sensor1 = Node(f"{organism_name}_sensor_1", center_x - 100, center_y - 50, "sensor")
        sensor2 = Node(f"{organism_name}_sensor_2", center_x + 100, center_y - 50, "sensor")
        self.canvas.nodes.extend([sensor1, sensor2])
        
        # 创建效应器节点
        actuator1 = Node(f"{organism_name}_actuator_1", center_x - 100, center_y + 50, "actuator")
        actuator2 = Node(f"{organism_name}_actuator_2", center_x + 100, center_y + 50, "actuator")
        self.canvas.nodes.extend([actuator1, actuator2])
        
        # 创建连接线
        self.canvas.connections.append(ConnectionLine(sensor1, organism_node))
        self.canvas.connections.append(ConnectionLine(sensor2, organism_node))
        self.canvas.connections.append(ConnectionLine(organism_node, actuator1))
        self.canvas.connections.append(ConnectionLine(organism_node, actuator2))
        
        # 保存新生物的状态
        self.current_organism = organism_name
        self.save_current_organism()
        
        # 标记为已修改
        self.mark_dirty()
        
        # 更新画布
        self.canvas.update()
        self.console.add_output(f"创建生物: {organism_name}")
        self.status_bar.showMessage(f"创建生物: {organism_name}")
    
    def on_organism_deleted(self, organism_name):
        """处理生物删除信号"""
        # 从字典中删除生物状态
        if organism_name in self.organisms:
            del self.organisms[organism_name]
        
        # 如果删除的是当前正在编辑的生物
        if self.current_organism == organism_name:
            # 清除画布
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            # 重置当前生物
            self.current_organism = None
            # 清空项目修改状态
            self.is_dirty = False
        
        # 更新画布
        self.canvas.update()
        # 输出日志
        self.console.add_output(f"删除生物: {organism_name}")
        self.status_bar.showMessage(f"删除生物: {organism_name}")
    
    def on_organism_selected(self):
        """处理生物选择信号"""
        selected_item = self.project_tree.tree.currentItem()
        if selected_item:
            parent = selected_item.parent()
            if parent and parent.text(0) == "生物列表":
                organism_name = selected_item.text(0)
                
                # 保存当前生物的状态
                if self.current_organism and self.current_organism in self.organisms:
                    self.save_current_organism()
                
                # 切换到选中的生物
                self.load_organism(organism_name)
                self.current_organism = organism_name
                self.console.add_output(f"切换到生物: {organism_name}")
                self.status_bar.showMessage(f"当前生物: {organism_name}")
                # 切换生物不标记为已修改，除非后续编辑
                # self.mark_dirty()
    
    def save_current_organism(self):
        """保存当前生物的状态"""
        if self.current_organism:
            # 保存当前画布的节点和连接
            # 需要创建深拷贝，避免引用问题
            import copy
            nodes_copy = []
            for node in self.canvas.nodes:
                new_node = Node(node.id, node.x, node.y, node.type)
                new_node.connections = []
                new_node.radius = node.radius
                nodes_copy.append(new_node)
            
            connections_copy = []
            # 创建节点ID到新节点的映射
            node_map = {node.id: new_node for node, new_node in zip(self.canvas.nodes, nodes_copy)}
            for conn in self.canvas.connections:
                start_node = node_map[conn.start_node.id]
                end_node = node_map[conn.end_node.id]
                new_conn = ConnectionLine(start_node, end_node)
                new_conn.weight = conn.weight
                new_conn.color = conn.color
                new_conn.width = conn.width
                connections_copy.append(new_conn)
            
            self.organisms[self.current_organism] = (nodes_copy, connections_copy)
    
    def load_organism(self, organism_name):
        """加载指定生物的状态"""
        if organism_name in self.organisms:
            # 清除当前画布的节点和连接
            self.canvas.nodes.clear()
            self.canvas.connections.clear()
            
            # 加载保存的节点和连接
            saved_nodes, saved_connections = self.organisms[organism_name]
            
            # 创建节点ID到新节点的映射
            node_map = {}
            
            # 先创建所有节点
            for saved_node in saved_nodes:
                new_node = Node(saved_node.id, saved_node.x, saved_node.y, saved_node.type)
                new_node.radius = saved_node.radius
                self.canvas.nodes.append(new_node)
                node_map[saved_node.id] = new_node
            
            # 再创建所有连接
            for saved_conn in saved_connections:
                start_node = node_map[saved_conn.start_node.id]
                end_node = node_map[saved_conn.end_node.id]
                new_conn = ConnectionLine(start_node, end_node)
                new_conn.weight = saved_conn.weight
                new_conn.color = saved_conn.color
                new_conn.width = saved_conn.width
                self.canvas.connections.append(new_conn)
            
            # 更新画布
            self.canvas.update()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置全局字体，确保中文显示正常
    from PyQt6.QtGui import QFont
    font = QFont("Microsoft YaHei", 9)  # 使用微软雅黑字体，适合中文显示
    app.setFont(font)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = PyQtOrganismEditor()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
