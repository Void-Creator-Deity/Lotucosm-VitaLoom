"""基于PyQt6的AI生命体编辑器原型"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QBrush, QLinearGradient
import sys


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
        shadow_rect = QRect(self.x - self.radius - 2, self.y - self.radius - 2, 
                           self.radius * 2 + 4, self.radius * 2 + 4)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(shadow_rect)
        
        # 绘制节点主体
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(self.x - self.radius, self.y - self.radius, 
                           self.radius * 2, self.radius * 2)
        
        # 绘制节点标签
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(self.x - 15, self.y + 5, self.id[-3:])
    
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
        
        # 计算线条
        start_pos = QPoint(self.start_node.x, self.start_node.y)
        end_pos = QPoint(self.end_node.x, self.end_node.y)
        
        # 绘制直线
        painter.drawLine(start_pos, end_pos)
        
        # 手动计算角度（PyQt6中QPoint.angle()已移除）
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        import math
        angle = math.atan2(dy, dx) * 180 / math.pi
        
        arrow_size = 8
        
        # 计算箭头点
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
        
        a = QPoint(self.start_node.x, self.start_node.y)
        b = QPoint(self.end_node.x, self.end_node.y)
        return distance_point_line(point, a, b) <= tolerance


class OrganismCanvas(QWidget):
    """生物可视化编辑画布 - 节点连线编辑器"""
    # 自定义信号，用于通知属性面板更新
    updateRequest = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # 节点和连接线
        self.nodes = []
        self.connections = []
        
        # 交互状态
        self.selected_node = None
        self.hovered_node = None
        self.hovered_connection = None
        self.dragging = False
        self.drag_start = QPoint()
        self.connecting = False
        self.connect_start_node = None
        self.connect_temp_pos = QPoint()
        
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
                    QPoint(connection.start_node.x, connection.start_node.y),
                    QPoint(connection.end_node.x, connection.end_node.y)
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
                    QPoint(connection.start_node.x, connection.start_node.y),
                    QPoint(connection.end_node.x, connection.end_node.y)
                )
                
                connection.draw(painter)
        
        # 绘制临时连接线
        if self.connecting and self.connect_start_node:
            # 绘制临时线发光效果
            glow_pen = QPen(QColor(255, 255, 255, 50), 4, Qt.PenStyle.DashLine)
            painter.setPen(glow_pen)
            painter.drawLine(QPoint(self.connect_start_node.x, self.connect_start_node.y), 
                           self.connect_temp_pos)
            
            # 绘制主虚线
            pen = QPen(QColor(255, 255, 255, 150), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPoint(self.connect_start_node.x, self.connect_start_node.y), 
                           self.connect_temp_pos)
        
        # 绘制节点
        for node in self.nodes:
            # 高亮选中或悬停的节点
            if node == self.selected_node:
                # 绘制选中发光效果
                glow_brush = QBrush(QColor(255, 255, 255, 80))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(node.x - node.radius - 10, node.y - node.radius - 10, 
                                   node.radius * 2 + 20, node.radius * 2 + 20)
                
                # 绘制选中边框
                painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.drawEllipse(node.x - node.radius - 5, node.y - node.radius - 5, 
                                   node.radius * 2 + 10, node.radius * 2 + 10)
            elif node == self.hovered_node:
                # 绘制悬停发光效果
                glow_brush = QBrush(QColor(255, 255, 255, 50))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(node.x - node.radius - 8, node.y - node.radius - 8, 
                                   node.radius * 2 + 16, node.radius * 2 + 16)
                
                # 绘制悬停边框
                painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawEllipse(node.x - node.radius - 3, node.y - node.radius - 3, 
                                   node.radius * 2 + 6, node.radius * 2 + 6)
            
            # 绘制节点
            node.draw(painter)
    
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
                self.selected_node = clicked_node
                self.dragging = True
                self.drag_start = event.pos()
            else:
                self.selected_node = None
            
            self.update()
            # 触发更新信号
            self.updateRequest.emit()
        
        # 右键点击连线
        elif event.button() == Qt.MouseButton.RightButton:
            # 检查是否点击了连接线
            for connection in self.connections:
                if connection.contains(event.pos()):
                    self.connections.remove(connection)
                    self.update()
                    break
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
            
            # 处理连接完成
            if self.connecting:
                # 检查是否点击了另一个节点
                for node in self.nodes:
                    if node.contains(event.pos()) and node != self.connect_start_node:
                        # 创建新连接
                        new_connection = ConnectionLine(self.connect_start_node, node)
                        self.connections.append(new_connection)
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
            
            self.selected_node.update_position(
                self.selected_node.x + dx, 
                self.selected_node.y + dy
            )
            
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
        new_node = Node(node_id, pos.x(), pos.y(), node_type)
        self.nodes.append(new_node)
        self.selected_node = new_node
        self.update()
        self.updateRequest.emit()
    
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
        # 这里可以添加属性变化的处理逻辑
        # 例如：更新选中对象的属性并触发重绘
        pass


class ProjectTree(QWidget):
    """项目树面板"""
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)
        self.setStyleSheet("background-color: #252526;")
        
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
        button_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet(new_btn.styleSheet())
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)


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
        
        # 设置样式
        self.setStyleSheet("background-color: #1e1e1e;")
        
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
        
        self.central_tab.addTab(self.simulation_tab, "模拟运行")
        
        # 初始化模拟
        from ai_organism.simulation import Simulation
        self.simulation = Simulation(800, 600)
        # 将编辑的生物应用到模拟
        self.apply_to_simulation()
        
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
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 监听画布选择变化，更新属性面板
        self.canvas.updateRequest.connect(self._on_canvas_updated)
        
        # 为模拟画布添加绘制事件
        self.simulation_canvas.paintEvent = self.draw_simulation
        
        # 添加键盘事件
        self.simulation_canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.simulation_canvas.keyPressEvent = self.handle_simulation_key
        self.simulation_canvas.mousePressEvent = self.handle_simulation_mouse
    
    def _on_canvas_updated(self):
        """画布更新时的处理"""
        # 更新属性面板
        self.property_panel.update_properties(self.canvas.selected_node)
        
        # 更新状态栏提示
        if self.canvas.selected_node:
            self.status_bar.showMessage(f"已选择: {self.canvas.selected_node.id}")
        else:
            self.status_bar.showMessage("就绪")
    
    def draw_simulation(self, event):
        """绘制模拟内容"""
        painter = QPainter(self.simulation_canvas)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 清屏
        painter.fillRect(event.rect(), QColor(20, 20, 30))
        
        # 绘制模拟
        import pygame
        surface = pygame.Surface((800, 600))
        self.simulation.draw(surface)
        
        # 将Pygame表面转换为Qt图像
        import numpy as np
        from PyQt6.QtGui import QImage
        
        # 获取Pygame表面数据
        data = pygame.surfarray.array3d(surface)
        data = data.swapaxes(0, 1)  # 交换x和y轴
        data = np.flipud(data)  # 翻转y轴
        
        # 创建QImage
        height, width, channels = data.shape
        bytes_per_line = channels * width
        qimage = QImage(data.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        # 绘制到Qt画布
        painter.drawImage(0, 0, qimage)
    
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
        """将编辑的生物应用到模拟中"""
        # 从画布获取节点和连接信息
        nodes = self.canvas.nodes
        connections = self.canvas.connections
        
        # 清除现有生物
        self.simulation.organisms.clear()
        
        # 创建新生物
        from ai_organism.core import Organism
        organism = Organism("editor_org", (400, 300))
        
        # 添加传感器和效应器
        for node in nodes:
            if node.type == "sensor":
                from ai_organism.tools import LightSensor
                sensor = LightSensor(node.id, node.position)
                organism.add_sensor(sensor)
            elif node.type == "actuator":
                from ai_organism.tools import MuscleActuator
                actuator = MuscleActuator(node.id, node.position)
                organism.add_actuator(actuator)
        
        # 添加连接
        for connection in connections:
            organism.connect_tools(
                connection.start_node.id,
                connection.end_node.id,
                connection.weight
            )
        
        # 添加到模拟
        self.simulation.organisms.append(organism)
        self.simulation.selected_organism = organism
        self.console.add_output("已将编辑的生物应用到模拟中")
    
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
        self.console.add_output("新建项目")
        self.status_bar.showMessage("新建项目")
    
    def open_project(self):
        """打开项目"""
        self.console.add_output("打开项目")
        self.status_bar.showMessage("打开项目")
    
    def save_project(self):
        """保存项目"""
        self.console.add_output("保存项目")
        self.status_bar.showMessage("保存项目")
    
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
        self.console.add_output("复制操作")
        self.status_bar.showMessage("复制操作")
    
    def paste(self):
        """粘贴操作"""
        self.console.add_output("粘贴操作")
        self.status_bar.showMessage("粘贴操作")
    
    def delete(self):
        """删除操作"""
        self.console.add_output("删除操作")
        self.status_bar.showMessage("删除操作")
    
    def toggle_project_tree(self):
        """切换项目树显示"""
        self.console.add_output("切换项目树显示")
        self.status_bar.showMessage("切换项目树显示")
    
    def toggle_property_panel(self):
        """切换属性面板显示"""
        self.console.add_output("切换属性面板显示")
        self.status_bar.showMessage("切换属性面板显示")
    
    def toggle_console(self):
        """切换控制台显示"""
        self.console.add_output("切换控制台显示")
        self.console.setVisible(not self.console.isVisible())
        self.status_bar.showMessage("切换控制台显示")
    
    def run_simulation(self):
        """运行模拟"""
        self.console.add_output("运行模拟")
        self.status_bar.showMessage("运行模拟")
    
    def stop_simulation(self):
        """停止模拟"""
        self.console.add_output("停止模拟")
        self.status_bar.showMessage("停止模拟")
    
    def export_organism(self):
        """导出生物"""
        self.console.add_output("导出生物")
        self.status_bar.showMessage("导出生物")
    
    def import_organism(self):
        """导入生物"""
        self.console.add_output("导入生物")
        self.status_bar.showMessage("导入生物")
    
    def show_help(self):
        """显示帮助"""
        self.console.add_output("显示帮助")
        self.status_bar.showMessage("显示帮助")
    
    def show_about(self):
        """显示关于"""
        self.console.add_output("显示关于")
        self.status_bar.showMessage("显示关于")
    
    def change_mode(self, mode):
        """切换编辑模式"""
        self.console.add_output(f"切换到{mode}模式")
        self.status_bar.showMessage(f"模式: {mode}")
        for widget in self.status_bar.findChildren(QLabel):
            if widget.text().startswith("模式:"):
                widget.setText(f"模式: {mode}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = PyQtOrganismEditor()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
