"""简化版AI生命体编辑器"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal, QRect, QTimer
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QBrush, QLinearGradient
import sys
import math

# 导入命令模式
from ai_organism.editor.command import CommandStack, AddNodeCommand, DeleteNodeCommand, MoveNodeCommand, CreateConnectionCommand, DeleteConnectionCommand, ModifyNodePropertyCommand, ModifyConnectionPropertyCommand


class Node:
    """节点类"""
    def __init__(self, node_id, x, y, node_type="sensor"):
        self.id = node_id
        self.x = x
        self.y = y
        self.type = node_type  # sensor, actuator, organism, central_brain
        self.radius = 25
        self.connections = []
        
        # 根据类型设置颜色
        if node_type == "organism":
            self.color = QColor(100, 150, 255)  # 蓝色
            self.radius = 30
        elif node_type == "sensor":
            self.color = QColor(0, 255, 0)  # 绿色
        elif node_type == "actuator":
            self.color = QColor(255, 0, 0)  # 红色
        elif node_type == "central_brain":
            self.color = QColor(255, 255, 0)  # 黄色
        else:
            self.color = QColor(255, 255, 255)  # 白色
    
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
        
        # 计算线条
        start_pos = QPoint(int(self.start_node.x), int(self.start_node.y))
        end_pos = QPoint(int(self.end_node.x), int(self.end_node.y))
        
        # 绘制直线
        painter.drawLine(start_pos, end_pos)
        
        # 手动计算角度
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
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
            
            A = p.x() - a.x()
            B = p.y() - a.y()
            C = b.x() - a.x()
            D = b.y() - a.y()
            
            dot = A * C + B * D
            len_sq = C * C + D * D
            param = -1
            if len_sq != 0:  # in case of 0 length line
                param = dot / len_sq
            
            xx = 0
            yy = 0
            
            if param < 0:
                xx = a.x()
                yy = a.y()
            elif param > 1:
                xx = b.x()
                yy = b.y()
            else:
                xx = a.x() + param * C
                yy = a.y() + param * D
            
            dx = p.x() - xx
            dy = p.y() - yy
            return (dx * dx + dy * dy) ** 0.5
        
        start_pos = QPoint(int(self.start_node.x), int(self.start_node.y))
        end_pos = QPoint(int(self.end_node.x), int(self.end_node.y))
        
        return distance_point_line(point, start_pos, end_pos) <= tolerance


class OrganismCanvas(QWidget):
    """生物可视化编辑画布"""
    # 自定义信号
    updateRequest = pyqtSignal()
    projectModified = pyqtSignal()
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
        self.selected_nodes = []
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
        
        # 创建细胞中枢节点
        central_brain = Node("central_1", center_x, center_y, "central_brain")
        self.nodes.append(central_brain)
        
        # 创建传感器节点（在细胞膜内）
        sensor1 = Node("sensor_1", center_x - 80, center_y - 50, "sensor")
        sensor2 = Node("sensor_2", center_x + 80, center_y - 50, "sensor")
        self.nodes.extend([sensor1, sensor2])
        
        # 创建效应器节点（在细胞膜内）
        actuator1 = Node("actuator_1", center_x - 80, center_y + 50, "actuator")
        actuator2 = Node("actuator_2", center_x + 80, center_y + 50, "actuator")
        self.nodes.extend([actuator1, actuator2])
        
        # 创建连接线（传感器→中枢，中枢→效应器）
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
        
        # 绘制网格背景
        self._draw_grid(painter)
        
        # 绘制连接线
        for connection in self.connections:
            connection.draw(painter)
        
        # 绘制临时连接线
        if self.connecting and self.connect_start_node:
            # 绘制主虚线
            pen = QPen(QColor(255, 255, 255, 150), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(
                QPoint(int(self.connect_start_node.x), int(self.connect_start_node.y)), 
                self.connect_temp_pos
            )
        
        # 绘制节点（除了生物体节点）
        for node in self.nodes:
            if node.type != "organism":
                node.draw(painter)
        
        # 绘制细胞膜（生物体节点只显示圆环）
        for node in self.nodes:
            if node.type == "organism":
                # 计算细胞膜半径（比生物体节点大50%）
                membrane_radius = int(node.radius * 3)
                
                # 只绘制细胞膜圆环
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(100, 150, 255, 200), 2))
                membrane_rect = QRect(
                    int(node.x - membrane_radius),
                    int(node.y - membrane_radius),
                    membrane_radius * 2,
                    membrane_radius * 2
                )
                painter.drawEllipse(membrane_rect)
    
    def _draw_grid(self, painter):
        """绘制网格背景"""
        # 绘制淡灰色网格
        grid_color = QColor(50, 50, 50)
        pen = QPen(grid_color, 1)
        painter.setPen(pen)
        
        # 计算网格线位置
        width, height = self.width(), self.height()
        grid_size = 20
        
        # 绘制垂直线
        for x in range(0, width, grid_size):
            painter.drawLine(x, 0, x, height)
        
        # 绘制水平线
        for y in range(0, height, grid_size):
            painter.drawLine(0, y, width, y)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        # 检查是否点击了节点
        for node in self.nodes:
            if node.contains(event.pos()):
                # 处理选择逻辑
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # 按住Ctrl键添加/移除选择
                    if node in self.selected_nodes:
                        self.selected_nodes.remove(node)
                    else:
                        self.selected_nodes.append(node)
                elif event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # 按住Shift键从当前选择到点击节点进行多选
                    if self.selected_node:
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                else:
                    # 普通点击，只选择一个节点
                    self.selected_nodes = [node]
                
                self.selected_node = node
                self.dragging = True
                self.drag_start = event.pos()
                self.update()
                self.updateRequest.emit()
                return
        
        # 点击空白处，取消所有选择
        self.selected_nodes.clear()
        self.selected_node = None
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
            
            if organism_node:
                # 计算细胞膜半径
                membrane_radius = organism_node.radius * 3
                
                for node in self.selected_nodes:
                    # 计算新位置
                    new_x = node.x + dx
                    new_y = node.y + dy
                    
                    # 如果是生物体节点，可以自由移动
                    if node.type != "organism":
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
            
            self.drag_start = event.pos()
            self.update()
        
        # 处理临时连接线
        if self.connecting:
            self.connect_temp_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
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
    
    def _add_node(self, pos, node_type):
        """添加节点"""
        # 找到生物体节点（细胞膜）
        organism_node = None
        for node in self.nodes:
            if node.type == "organism":
                organism_node = node
                break
        
        node_id = f"{node_type}_{len([n for n in self.nodes if n.type == node_type]) + 1}"
        
        # 获取新节点的初始位置
        new_x = pos.x()
        new_y = pos.y()
        
        # 如果有细胞膜，确保新节点在细胞膜内
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
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        
        # 检查是否点击了节点
        clicked_node = None
        for node in self.nodes:
            if node.contains(event.pos()):
                clicked_node = node
                break
        
        if clicked_node:
            # 节点右键菜单
            delete_action = QAction("删除节点", self)
            delete_action.triggered.connect(lambda: self._delete_node(clicked_node))
            menu.addAction(delete_action)
        else:
            # 空白处右键菜单
            add_sensor_action = QAction("添加传感器", self)
            add_sensor_action.triggered.connect(lambda: self._add_node(event.pos(), "sensor"))
            menu.addAction(add_sensor_action)
            
            add_actuator_action = QAction("添加效应器", self)
            add_actuator_action.triggered.connect(lambda: self._add_node(event.pos(), "actuator"))
            menu.addAction(add_actuator_action)
            
            add_central_brain_action = QAction("添加细胞中枢", self)
            add_central_brain_action.triggered.connect(lambda: self._add_node(event.pos(), "central_brain"))
            menu.addAction(add_central_brain_action)
        
        menu.exec(event.globalPos())
    
    def _delete_node(self, node):
        """删除节点"""
        # 使用命令模式删除节点
        command = DeleteNodeCommand(self, node)
        self.command_stack.execute(command)
        # 删除节点后标记为已修改
        self.projectModified.emit()
        self.commandExecuted.emit()
    
    def _start_connection(self):
        """开始创建连接"""
        if self.selected_node:
            self.connecting = True
            self.connect_start_node = self.selected_node
            self.connect_temp_pos = QPoint(int(self.selected_node.x), int(self.selected_node.y))
            self.update()


class PyQtOrganismEditor(QMainWindow):
    """基于PyQt6的AI生命体编辑器"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI生命体编辑器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧控制面板
        left_panel = QVBoxLayout()
        
        # 添加按钮
        add_sensor_btn = QPushButton("添加传感器")
        add_actuator_btn = QPushButton("添加效应器")
        add_central_btn = QPushButton("添加细胞中枢")
        connect_btn = QPushButton("开始连接")
        
        left_panel.addWidget(add_sensor_btn)
        left_panel.addWidget(add_actuator_btn)
        left_panel.addWidget(add_central_btn)
        left_panel.addWidget(connect_btn)
        left_panel.addStretch()
        
        # 右侧编辑区域
        right_panel = QVBoxLayout()
        
        # 画布
        self.canvas = OrganismCanvas()
        right_panel.addWidget(self.canvas)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 信号连接
        add_sensor_btn.clicked.connect(lambda: self.canvas._add_node(QPoint(300, 200), "sensor"))
        add_actuator_btn.clicked.connect(lambda: self.canvas._add_node(QPoint(300, 200), "actuator"))
        add_central_btn.clicked.connect(lambda: self.canvas._add_node(QPoint(300, 200), "central_brain"))
        connect_btn.clicked.connect(self.canvas._start_connection)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        splitter.setSizes([200, 1000])
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)
    
    def closeEvent(self, event):
        """关闭事件"""
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = PyQtOrganismEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
