"""基于PyQt6的AI生命体编辑器 - 面板模块"""

from typing import Any

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox

from PyQt6.QtCore import pyqtSignal

# 导入命令模式

from vitalloom.editor.commands.command import CommandStack, ModifyNodePropertyCommand, ModifyConnectionPropertyCommand


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

        self._layout = QVBoxLayout(self)

        # 标题

        self.title_label = QLabel("属性编辑")

        self.title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")

        self._layout.addWidget(self.title_label)

        # 分隔线

        self.line = QFrame()

        self.line.setFrameShape(QFrame.Shape.HLine)

        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.line.setStyleSheet("background-color: #404040;")

        self._layout.addWidget(self.line)

        # 状态信息

        self.status_label = QLabel("未选择对象")

        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")

        self._layout.addWidget(self.status_label)

        # 对象属性容器

        self.properties_container = QWidget()

        self.properties_layout = QVBoxLayout(self.properties_container)

        self.properties_layout.setContentsMargins(0, 0, 0, 0)

        self._layout.addWidget(self.properties_container)

        # 空控件填充剩余空间

        self._layout.addStretch()

        # 当前选中的对象

        self._selected_object = None

        # 命令栈

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

        # 大小属性组

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

    def clear_properties(self):

        """清空属性面板内容（公共方法）"""

        self._clear_properties()

    def update_properties(self, selected_object: Any):

        """更新属性面板内容"""

        self._clear_properties()

        if not selected_object:

            return

        # 更新状态标签

        self.status_label.setText(f"已选择: {selected_object.__class__.__name__}")

        # 添加通用属性组

        self.properties_layout.addWidget(self.general_group)

        self.general_group.show()

        # 保存当前选中对象

        self._selected_object = selected_object

        # 根据对象类型显示不同属性

        if hasattr(selected_object, "id"):

            # 节点属性

            self.id_label.setText(selected_object.id)

            if hasattr(selected_object, "type"):

                type_names = {

                    "organism": "生物",

                    "sensor": "传感器", 

                    "actuator": "效应器",

                    "central_brain": "中枢管理器"

                }

                self.type_label.setText(type_names.get(selected_object.type, selected_object.type))

            # 添加位置属性

            self.properties_layout.addWidget(self.position_group)

            self.position_group.show()

            # 设置位置值

            self.x_spin.setValue(int(selected_object.x))

            self.y_spin.setValue(int(selected_object.y))

            # 连接位置变化信号

            self.x_spin.valueChanged.connect(self._on_position_changed)  # type: ignore

            self.y_spin.valueChanged.connect(self._on_position_changed)  # type: ignore

            # 添加大小属性

            if hasattr(selected_object, "radius"):

                self.properties_layout.addWidget(self.size_group)

                self.size_group.show()

                # 设置半径值

                self.radius_spin.setValue(int(selected_object.radius))

                # 连接半径变化信号

            self.radius_spin.valueChanged.connect(self._on_radius_changed)  # type: ignore

        # 处理连接属性

        elif hasattr(selected_object, "start_node") and hasattr(selected_object, "end_node"):

            # 连接线属性

            self.type_label.setText("连接线")

            # 添加连接属性

            self.properties_layout.addWidget(self.connection_group)

            self.connection_group.show()

            # 设置权重值

            self.weight_spin.setValue(selected_object.weight)

            self.source_label.setText(selected_object.start_node.id)

            self.target_label.setText(selected_object.end_node.id)

            # 连接权重变化信号

            self.weight_spin.valueChanged.connect(self._on_weight_changed)  # type: ignore

    def _on_position_changed(self, _: int = 0):

        """位置属性变化处理"""

        if not self._selected_object:

            return

        # 获取新位置值

        new_x = self.x_spin.value()

        new_y = self.y_spin.value()

        # 执行修改命令

        command = ModifyNodePropertyCommand(

            self._selected_object,

            "position",

            (self._selected_object.x, self._selected_object.y),

            (new_x, new_y)

        )

        self.command_stack.execute(command)

        # 通知项目已修改

        self.projectModified.emit()

        self.commandExecuted.emit()

    def _on_radius_changed(self, _: int = 0):

        """半径属性变化处理"""

        if not self._selected_object or not hasattr(self._selected_object, "radius"):

            return

        # 获取新半径值

        new_radius = self.radius_spin.value()

        # 执行修改命令

        command = ModifyNodePropertyCommand(

            self._selected_object,

            "radius",

            self._selected_object.radius,

            new_radius

        )

        self.command_stack.execute(command)

        # 通知项目已修改

        self.projectModified.emit()

        self.commandExecuted.emit()

    def _on_weight_changed(self, _: float = 0.0):

        """权重属性变化处理"""

        if not self._selected_object or not hasattr(self._selected_object, "weight"):

            return

        # 获取新权重值

        new_weight = self.weight_spin.value()

        # 执行修改命令

        command = ModifyConnectionPropertyCommand(

            self._selected_object,

            "weight",

            self._selected_object.weight,

            new_weight

        )

        self.command_stack.execute(command)

        # 通知项目已修改

        self.projectModified.emit()

        self.commandExecuted.emit()
