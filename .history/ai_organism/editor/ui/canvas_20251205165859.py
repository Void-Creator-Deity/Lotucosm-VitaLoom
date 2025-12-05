"""基于PyQt6的AI生命体编辑器 - 画布模块"""

from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient

# 导入节点和连接线类
from .nodes import Node, ConnectionLine

# 导入命令模式
from ai_organism.editor.command import CommandStack, AddNodeCommand, DeleteNodeCommand, MoveNodeCommand, CreateConnectionCommand, DeleteConnectionCommand


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
        
        # 创建生物体节点（细胞膜）
        organism = Node("organism_1", center_x, center_y, "organism")
        self.nodes.append(organism)
        
        # 创建中枢管理器节点
        central_brain = Node("central_1", center_x, center_y, "central_brain")
        self.nodes.append(central_brain)
        
        # 创建传感器节点
        sensor1 = Node("sensor_1", center_x - 100, center_y - 50, "sensor")
        sensor2 = Node("sensor_2", center_x + 100, center_y - 50, "sensor")
        self.nodes.extend([sensor1, sensor2])
        
        # 创建效应器节点
        actuator1 = Node("actuator_1", center_x - 100, center_y + 50, "actuator")
        actuator2 = Node("actuator_2", center_x + 100, center_y + 50, "actuator")
        self.nodes.extend([actuator1, actuator2])
        
        # 创建连接线（传感器→中枢，中枢→效应器，不直接连接到细胞膜）
        self.connections.append(ConnectionLine(sensor1, central_brain))
        self.connections.append(ConnectionLine(sensor2, central_brain))
        self.connections.append(ConnectionLine(central_brain, actuator1))
        self.connections.append(ConnectionLine(central_brain, actuator2))
    
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
                center_x, center_y = int(node.x), int(node.y)
                
                # 绘制细胞膜外环 - 现代化的渐变边框
                outer_rect = QRect(center_x - membrane_radius - 2, center_y - membrane_radius - 2, 
                                  membrane_radius * 2 + 4, membrane_radius * 2 + 4)
                outer_gradient = QLinearGradient(outer_rect.topLeft().x(), outer_rect.topLeft().y(), 
                                               outer_rect.bottomRight().x(), outer_rect.bottomRight().y())
                outer_gradient.setColorAt(0, QColor(100, 150, 255, 50))
                outer_gradient.setColorAt(1, QColor(100, 150, 255, 0))
                painter.setBrush(QBrush(outer_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(outer_rect)
                
                # 绘制细胞膜主体 - 双层渐变圆环
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
                painter.drawEllipse(center_x - membrane_radius, center_y - membrane_radius, 
                                   membrane_radius * 2, membrane_radius * 2)
                
                # 绘制细胞膜内环 - 更细的内边框，增加层次感
                inner_pen = QPen(QColor(150, 200, 255, 150), 1)
                painter.setPen(inner_pen)
                painter.drawEllipse(center_x - membrane_radius + 4, center_y - membrane_radius + 4, 
                                   (membrane_radius - 4) * 2, (membrane_radius - 4) * 2)
    
    def _draw_gradient_background(self, painter):
        """绘制渐变背景"""
        # 简化背景绘制，使用纯色背景替代渐变，提高性能
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())
    
    def _draw_grid(self, painter):
        """绘制网格背景"""
        grid_color = QColor(60, 60, 70)
        grid_size = 40  # 增加网格大小，减少绘制次数
        
        pen = QPen(grid_color, 0.3)
        painter.setPen(pen)
        
        # 只绘制视口内的网格线，减少绘制次数
        start_x = 0
        end_x = self.width()
        start_y = 0
        end_y = self.height()
        
        # 绘制垂直线，间隔增大一倍
        for x in range(start_x, end_x, grid_size):
            painter.drawLine(x, start_y, x, end_y)
        
        # 绘制水平线，间隔增大一倍
        for y in range(start_y, end_y, grid_size):
            painter.drawLine(start_x, y, end_x, y)
        
        # 只绘制中心十字线，移除不必要的虚线效果
        center_x, center_y = self.width() // 2, self.height() // 2
        center_pen = QPen(QColor(80, 80, 100), 1)
        painter.setPen(center_pen)
        painter.drawLine(center_x, start_y, center_x, end_y)
        painter.drawLine(start_x, center_y, end_x, center_y)
    
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
        elif event.button()