"""基于PyQt6的AI生命体编辑器 - 项目树模块"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QFrame, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class ProjectTree(QWidget):
    """项目结构树面板"""
    # 自定义信号，用于通知属性面板更新
    treeItemSelected = pyqtSignal(object)
    # 定义信号，用于通知主窗口新建或删除生物
    organism_created = pyqtSignal(str)  # 生物名称
    organism_deleted = pyqtSignal(str)  # 生物名称
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(200)
        self.setStyleSheet("background-color: #252526;")
        
        self.layout = QVBoxLayout(self)
        
        # 标题
        self.title_label = QLabel("项目结构")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # 分隔线
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.line.setStyleSheet("background-color: #404040;")
        self.layout.addWidget(self.line)
        
        # 树控件
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QTreeWidget::item {
                height: 20px;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #264f78;
                color: #ffffff;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-image: url(:/qt-project.org/styles/commonstyle/images/branch-vertical.png) 0;
            }
            QTreeWidget::branch:has-siblings:adjoins-item {
                border-image: url(:/qt-project.org/styles/commonstyle/images/branch-more.png) 0;
            }
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(:/qt-project.org/styles/commonstyle/images/branch-end.png) 0;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/qt-project.org/styles/commonstyle/images/branch-closed.png);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(:/qt-project.org/styles/commonstyle/images/branch-open.png);
            }
        """)
        self.layout.addWidget(self.tree_widget)
        
        # 连接信号
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # 创建默认树结构
        self._create_default_tree()
    
    def _create_default_tree(self):
        """创建默认树结构"""
        # 根节点
        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "AI生命体项目")
        root.setExpanded(True)
        
        # 生物体节点
        organism_item = QTreeWidgetItem(root)
        organism_item.setText(0, "生物体")
        organism_item.setExpanded(True)
        
        # 细胞膜节点
        membrane_item = QTreeWidgetItem(organism_item)
        membrane_item.setText(0, "细胞膜")
        membrane_item.setData(0, Qt.ItemDataRole.UserRole, "membrane")
        
        # 中枢管理器节点
        brain_item = QTreeWidgetItem(organism_item)
        brain_item.setText(0, "中枢管理器")
        brain_item.setData(0, Qt.ItemDataRole.UserRole, "central_brain")
        
        # 传感器节点
        sensors_item = QTreeWidgetItem(organism_item)
        sensors_item.setText(0, "传感器")
        sensors_item.setExpanded(True)
        
        # 默认传感器
        sensor1_item = QTreeWidgetItem(sensors_item)
        sensor1_item.setText(0, "触觉传感器")
        sensor1_item.setData(0, Qt.ItemDataRole.UserRole, "sensor_1")
        
        sensor2_item = QTreeWidgetItem(sensors_item)
        sensor2_item.setText(0, "光感传感器")
        sensor2_item.setData(0, Qt.ItemDataRole.UserRole, "sensor_2")
        
        # 效应器节点
        actuators_item = QTreeWidgetItem(organism_item)
        actuators_item.setText(0, "效应器")
        actuators_item.setExpanded(True)
        
        # 默认效应器
        actuator1_item = QTreeWidgetItem(actuators_item)
        actuator1_item.setText(0, "肌肉效应器")
        actuator1_item.setData(0, Qt.ItemDataRole.UserRole, "actuator_1")
        
        actuator2_item = QTreeWidgetItem(actuators_item)
        actuator2_item.setText(0, "纤毛效应器")
        actuator2_item.setData(0, Qt.ItemDataRole.UserRole, "actuator_2")
        
        # 连接节点
        connections_item = QTreeWidgetItem(root)
        connections_item.setText(0, "连接")
        connections_item.setExpanded(True)
        
        # 默认连接
        connection1_item = QTreeWidgetItem(connections_item)
        connection1_item.setText(0, "传感器→中枢管理器")
        connection1_item.setData(0, Qt.ItemDataRole.UserRole, "connection_1")
        
        connection2_item = QTreeWidgetItem(connections_item)
        connection2_item.setText(0, "中枢管理器→效应器")
        connection2_item.setData(0, Qt.ItemDataRole.UserRole, "connection_2")
    
    def on_item_clicked(self, item):
        """树项被点击时的处理"""
        # 获取数据
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data:
            # 发送信号
            self.treeItemSelected.emit(item_data)
    
    def show_context_menu(self, pos):
        """显示上下文菜单"""
        menu = QMenu()
        
        # 添加菜单项
        add_sensor_action = QAction("添加传感器", self)
        add_sensor_action.triggered.connect(self.add_sensor)
        menu.addAction(add_sensor_action)
        
        add_actuator_action = QAction("添加效应器", self)
        add_actuator_action.triggered.connect(self.add_actuator)
        menu.addAction(add_actuator_action)
        
        menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_item)
        menu.addAction(delete_action)
        
        menu.exec(self.tree_widget.mapToGlobal(pos))
    
    def add_sensor(self):
        """添加传感器"""
        # 找到传感器节点
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            organism_item = root.child(i)
            if organism_item.text(0) == "AI生命体项目":
                for j in range(organism_item.childCount()):
                    child_item = organism_item.child(j)
                    if child_item.text(0) == "生物体":
                        for k in range(child_item.childCount()):
                            sensors_item = child_item.child(k)
                            if sensors_item.text(0) == "传感器":
                                # 添加新传感器
                                new_sensor = QTreeWidgetItem(sensors_item)
                                sensor_count = sensors_item.childCount()
                                new_sensor.setText(0, f"新传感器_{sensor_count}")
                                new_sensor.setData(0, Qt.ItemDataRole.UserRole, f"sensor_{sensor_count}")
                                sensors_item.setExpanded(True)
                                break
    
    def add_actuator(self):
        """添加效应器"""
        # 找到效应器节点
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            organism_item = root.child(i)
            if organism_item.text(0) == "AI生命体项目":
                for j in range(organism_item.childCount()):
                    child_item = organism_item.child(j)
                    if child_item.text(0) == "生物体":
                        for k in range(child_item.childCount()):
                            actuators_item = child_item.child(k)
                            if actuators_item.text(0) == "效应器":
                                # 添加新效应器
                                new_actuator = QTreeWidgetItem(actuators_item)
                                actuator_count = actuators_item.childCount()
                                new_actuator.setText(0, f"新效应器_{actuator_count}")
                                new_actuator.setData(0, Qt.ItemDataRole.UserRole, f"actuator_{actuator_count}")
                                actuators_item.setExpanded(True)
                                break
    
    def delete_item(self):
        """删除选中项"""
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            parent = item.parent()
            if parent:
                parent.removeChild(item)
    
    def update_tree(self, nodes, connections):
        """根据画布中的节点和连接线更新树结构"""
        # 清空现有树结构
        self.tree_widget.clear()
        
        # 根节点
        root = QTreeWidgetItem(self.tree_widget)
        root.setText(0, "AI生命体项目")
        root.setExpanded(True)
        
        # 生物体节点
        organism_item = QTreeWidgetItem(root)
        organism_item.setText(0, "生物体")
        organism_item.setExpanded(True)
        
        # 按类型分组节点
        nodes_by_type = {
            "organism": [],
            "membrane": [],
            "central_brain": [],
            "sensor": [],
            "actuator": []
        }
        
        for node in nodes:
            if node.type in nodes_by_type:
                nodes_by_type[node.type].append(node)
        
        # 添加细胞膜节点（如果有的话）
        if nodes_by_type["organism"]:
            for organism in nodes_by_type["organism"]:
                membrane_item = QTreeWidgetItem(organism_item)
                membrane_item.setText(0, f"细胞膜 {organism.id}")
                membrane_item.setData(0, Qt.ItemDataRole.UserRole, organism.id)
        
        # 添加中枢管理器节点
        if nodes_by_type["central_brain"]:
            brain_item = QTreeWidgetItem(organism_item)
            brain_item.setText(0, "中枢管理器")
            brain_item.setExpanded(True)
            
            for brain in nodes_by_type["central_brain"]:
                brain_node_item = QTreeWidgetItem(brain_item)
                brain_node_item.setText(0, f"中枢 {brain.id}")
                brain_node_item.setData(0, Qt.ItemDataRole.UserRole, brain.id)
        
        # 添加传感器节点
        if nodes_by_type["sensor"]:
            sensors_item = QTreeWidgetItem(organism_item)
            sensors_item.setText(0, "传感器")
            sensors_item.setExpanded(True)
            
            for sensor in nodes_by_type["sensor"]:
                sensor_item = QTreeWidgetItem(sensors_item)
                sensor_item.setText(0, f"传感器 {sensor.id}")
                sensor_item.setData(0, Qt.ItemDataRole.UserRole, sensor.id)
        
        # 添加效应器节点
        if nodes_by_type["actuator"]:
            actuators_item = QTreeWidgetItem(organism_item)
            actuators_item.setText(0, "效应器")
            actuators_item.setExpanded(True)
            
            for actuator in nodes_by_type["actuator"]:
                actuator_item = QTreeWidgetItem(actuators_item)
                actuator_item.setText(0, f"效应器 {actuator.id}")
                actuator_item.setData(0, Qt.ItemDataRole.UserRole, actuator.id)
        
        # 连接节点
        connections_item = QTreeWidgetItem(root)
        connections_item.setText(0, "连接")
        connections_item.setExpanded(True)
        
        # 添加连接线
        for i, connection in enumerate(connections):
            connection_item = QTreeWidgetItem(connections_item)
            connection_item.setText(0, f"连接 {i+1}: {connection.start_node.id} → {connection.end_node.id}")
            connection_item.setData(0, Qt.ItemDataRole.UserRole, f"connection_{i+1}")
