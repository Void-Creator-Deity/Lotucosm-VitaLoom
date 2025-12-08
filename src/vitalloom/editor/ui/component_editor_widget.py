# -*- coding: utf-8 -*-
"""组件编辑器GUI组件"""

from typing import Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                           QPushButton, QLineEdit, QComboBox, QGroupBox, QFormLayout, 
                           QDoubleSpinBox, QSplitter, QMessageBox, 
                           QTabWidget, QCheckBox, QTextEdit, QListWidgetItem) 

from PyQt6.QtCore import Qt, pyqtSignal

from vitalloom.editor.commands.command import ModifyNodePropertyCommand, AddNodeCommand, DeleteNodeCommand

from vitalloom.editor.ui.nodes import Node

from vitalloom.editor.ui.base_editor_widget import BaseEditorWidget


class ComponentEditorWidget(BaseEditorWidget):

    """组件编辑器GUI界面"""

    # 自定义信号

    component_edited = pyqtSignal()  # 组件被编辑时发出信号

    component_added = pyqtSignal()  # 组件被添加时发出信号

    component_deleted = pyqtSignal()  # 组件被删除时发出信号

    def __init__(self, canvas: Optional[Any] = None):

        """初始化组件编辑器"""

        super().__init__()

        self.canvas: Optional[Any] = canvas

        self.current_component: Optional[Node] = None

        # 初始化界面

        self._init_ui()

        # 如果有画布，初始化组件列表

        if canvas:

            self.set_canvas(canvas)

    def _init_ui(self):

        """初始化界面"""

        # 主布局

        main_layout = QVBoxLayout(self)

        # 使用基类方法创建标题部分

        self._create_title_section("组件编辑器", main_layout)

        # 画布信息

        self.canvas_info = QLabel("未选择画布")

        self.canvas_info.setStyleSheet("color: #888888; font-size: 12px;")

        main_layout.addWidget(self.canvas_info)

        # 分割器

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板：组件列表

        left_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)

        # 组件列表组

        component_list_group = QGroupBox("组件列表")

        component_list_layout = QVBoxLayout(component_list_group)

        self.component_list = QListWidget()

        self.component_list.itemClicked.connect(self._on_component_selected)  # type: ignore

        component_list_layout.addWidget(self.component_list)

        left_layout.addWidget(component_list_group)

        # 操作按钮组

        action_group = QGroupBox("操作")

        action_layout = QVBoxLayout(action_group)

        self.add_component_btn = QPushButton("添加组件")

        self.add_component_btn.clicked.connect(self._add_component)  # type: ignore

        action_layout.addWidget(self.add_component_btn)

        self.delete_component_btn = QPushButton("删除组件")

        self.delete_component_btn.clicked.connect(self._delete_component)  # type: ignore

        action_layout.addWidget(self.delete_component_btn)

        self.refresh_btn = QPushButton("刷新列表")

        self.refresh_btn.clicked.connect(self._refresh_component_list)  # type: ignore

        action_layout.addWidget(self.refresh_btn)

        left_layout.addWidget(action_group)

        splitter.addWidget(left_panel)

        # 右侧面板：组件编辑

        right_panel = QWidget()

        right_layout = QVBoxLayout(right_panel)

        # 标签页

        self.tab_widget = QTabWidget()

        # 组件属性编辑标签

        self.properties_tab = QWidget()

        self._init_properties_tab()

        self.tab_widget.addTab(self.properties_tab, "组件属性")

        # 高级属性标签

        self.advanced_tab = QWidget()

        self._init_advanced_tab()

        self.tab_widget.addTab(self.advanced_tab, "高级属性")

        right_layout.addWidget(self.tab_widget)

        splitter.addWidget(right_panel)

        # 设置分割器大小

        splitter.setSizes([300, 500])  # type: ignore

        main_layout.addWidget(splitter)

        # 底部按钮

        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("保存修改")

        self.save_btn.clicked.connect(self._save_component)  # type: ignore

        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清空")

        self.clear_btn.clicked.connect(self._clear_component)  # type: ignore

        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(btn_layout)

        # 禁用所有按钮，直到选择组件

        self._disable_buttons()

    def _init_properties_tab(self):

        """初始化属性编辑标签"""

        properties_layout = QVBoxLayout(self.properties_tab)

        # 基本属性组

        basic_group = QGroupBox("基本属性")

        basic_layout = QFormLayout(basic_group)

        # ID

        self.id_label = QLabel("ID:")

        self.id_input = QLineEdit()

        basic_layout.addRow(self.id_label, self.id_input)

        # 类型

        self.type_label = QLabel("类型:")

        self.type_input = QLineEdit()

        self.type_input.setReadOnly(True)

        basic_layout.addRow(self.type_label, self.type_input)

        # 名称

        self.name_label = QLabel("名称:")

        self.name_input = QLineEdit()

        basic_layout.addRow(self.name_label, self.name_input)

        # 位置

        self.location_label = QLabel("位置:")

        self.location_combo = QComboBox()

        self.location_combo.addItems(["internal", "external", "both"])  # type: ignore

        basic_layout.addRow(self.location_label, self.location_combo)

        # 附着点

        self.attach_point_label = QLabel("附着点 X:")

        self.attach_point_x = QDoubleSpinBox()

        self.attach_point_x.setRange(-1000, 1000)

        self.attach_point_x.setSingleStep(1.0)

        basic_layout.addRow(self.attach_point_label, self.attach_point_x)

        self.attach_point_y_label = QLabel("附着点 Y:")

        self.attach_point_y = QDoubleSpinBox()

        self.attach_point_y.setRange(-1000, 1000)

        self.attach_point_y.setSingleStep(1.0)

        basic_layout.addRow(self.attach_point_y_label, self.attach_point_y)

        properties_layout.addWidget(basic_group)

        # 激活属性组

        activation_group = QGroupBox("激活属性")

        activation_layout = QFormLayout(activation_group)

        # 激活阈值

        self.signal_threshold_label = QLabel("信号阈值:")

        self.signal_threshold = QDoubleSpinBox()

        self.signal_threshold.setRange(0.0, 1.0)

        self.signal_threshold.setSingleStep(0.05)

        self.signal_threshold.setValue(0.5)

        activation_layout.addRow(self.signal_threshold_label, self.signal_threshold)

        # 激活强度

        self.activation_label = QLabel("激活强度:")

        self.activation = QDoubleSpinBox()

        self.activation.setRange(0.0, 1.0)

        self.activation.setSingleStep(0.05)

        activation_layout.addRow(self.activation_label, self.activation)

        properties_layout.addWidget(activation_group)

        properties_layout.addStretch()

    def _init_advanced_tab(self):

        """初始化高级属性标签"""

        advanced_layout = QVBoxLayout(self.advanced_tab)

        # 高级属性组

        advanced_group = QGroupBox("高级属性")

        advanced_form_layout = QFormLayout(advanced_group)

        # 先天/后天

        self.congenital_label = QLabel("先天组件:")

        self.congenital_check = QCheckBox()

        advanced_form_layout.addRow(self.congenital_label, self.congenital_check)

        # 状态

        self.state_label = QLabel("当前状态:")

        self.state_input = QLineEdit()

        self.state_input.setReadOnly(True)

        advanced_form_layout.addRow(self.state_label, self.state_input)

        advanced_layout.addWidget(advanced_group)

        # 描述文本区域

        self.description_label = QLabel("组件描述:")

        advanced_layout.addWidget(self.description_label)

        self.description_text = QTextEdit()

        self.description_text.setPlaceholderText("组件的详细描述...")

        self.description_text.setMaximumHeight(150)

        advanced_layout.addWidget(self.description_text)

        advanced_layout.addStretch()

    def set_canvas(self, canvas: Any) -> None:

        """设置画布"""

        self.canvas = canvas

        # 更新画布信息

        self.canvas_info.setText(f"画布: {canvas.__class__.__name__}")

        # 加载组件列表

        self._refresh_component_list()

        # 启用按钮

        self._enable_buttons()

    def _refresh_component_list(self) -> None:

        """刷新组件列表"""

        self.component_list.clear()

        if not self.canvas:

            return

        # 遍历所有节点

        for node in self.canvas.nodes:

            # 将每个节点作为组件添加到列表

            list_item = f"{node.type} - {node.id}"

            self.component_list.addItem(list_item)

            # 存储节点对象到 item 的 data 中

            item = self.component_list.item(self.component_list.count() - 1)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, node)

    def _on_component_selected(self, item: QListWidgetItem) -> None:

        """选择组件时的处理"""

        component = item.data(Qt.ItemDataRole.UserRole)

        if component:

            self.current_component = component

            self._load_component_data(component)

    def _load_component_data(self, component: Node) -> None:

        """加载组件数据到编辑界面"""

        # 加载基本属性

        self.id_input.setText(component.id)

        self.type_input.setText(component.type)

        self.name_input.setText(getattr(component, 'name', component.id))

        # 加载位置属性

        location = getattr(component, 'location', 'internal')

        index = self.location_combo.findText(location)

        if index >= 0:

            self.location_combo.setCurrentIndex(index)

        # 加载附着点

        if hasattr(component, 'x') and hasattr(component, 'y'):

            self.attach_point_x.setValue(component.x)

            self.attach_point_y.setValue(component.y)

        # 加载激活属性

        self.signal_threshold.setValue(getattr(component, 'signal_threshold', 0.5))

        self.activation.setValue(getattr(component, 'activation', 0.0))

        # 加载高级属性

        self.congenital_check.setChecked(getattr(component, 'congenital', True))

        self.state_input.setText(getattr(component, 'state', 'idle'))

        # 加载描述

        self.description_text.setText(getattr(component,
    'description',
    f"{component.type} 组件") if hasattr(component,
    'description') else f"{component.type} 组件")

    def _save_component(self):

        """保存组件修改"""

        if not self.current_component:

            QMessageBox.warning(self, "保存失败", "请先选择一个组件进行编辑!")

            return

        if not self.canvas:

            QMessageBox.warning(self, "保存失败", "请先设置画布!")

            return

        # 获取编辑后的数据

        new_id = self.id_input.text()

        new_name = self.name_input.text()

        new_location = self.location_combo.currentText()

        new_attach_x = self.attach_point_x.value()

        new_attach_y = self.attach_point_y.value()

        new_threshold = self.signal_threshold.value()

        new_activation = self.activation.value()

        new_congenital = self.congenital_check.isChecked()

        new_description = self.description_text.toPlainText()

        try:

            # 使用命令模式修改组件属性

            # 修改ID

            if new_id != self.current_component.id:

                command = ModifyNodePropertyCommand(

                    self.current_component, 'id', self.current_component.id, new_id

                )

                self.canvas.command_stack.execute(command)

            # 修改名称

            current_name = getattr(self.current_component, 'name', self.current_component.id)
            if new_name != current_name:

                command = ModifyNodePropertyCommand(

                    self.current_component, 'name', current_name, new_name

                )

                self.canvas.command_stack.execute(command)

            # 修改位置

            if new_location != getattr(self.current_component, 'location', 'internal'):

                command = ModifyNodePropertyCommand(

                    self.current_component, 'location', 

                    getattr(self.current_component, 'location', 'internal'), new_location

                )

                self.canvas.command_stack.execute(command)

            # 修改附着点

            if hasattr(self.current_component, 'position'):

                old_pos = (self.current_component.x, self.current_component.y)

                new_pos = (new_attach_x, new_attach_y)

                if old_pos != new_pos:

                    # 更新位置

                    self.current_component.update_position(new_attach_x, new_attach_y)

            # 修改信号阈值

            if new_threshold != getattr(self.current_component, 'signal_threshold', 0.5):

                command = ModifyNodePropertyCommand(

                    self.current_component, 'signal_threshold', 

                    getattr(self.current_component, 'signal_threshold', 0.5), new_threshold

                )

                self.canvas.command_stack.execute(command)

            # 修改激活强度

            if new_activation != getattr(self.current_component, 'activation', 0.0):

                command = ModifyNodePropertyCommand(

                    self.current_component, 'activation', 

                    getattr(self.current_component, 'activation', 0.0), new_activation

                )

                self.canvas.command_stack.execute(command)

            # 修改先天属性

            if new_congenital != getattr(self.current_component, 'congenital', True):

                command = ModifyNodePropertyCommand(

                    self.current_component, 'congenital', 

                    getattr(self.current_component, 'congenital', True), new_congenital

                )

                self.canvas.command_stack.execute(command)

            # 修改描述

            old_desc = getattr(self.current_component, 'description', '')

            if new_description != old_desc:

                command = ModifyNodePropertyCommand(

                    self.current_component, 'description', old_desc, new_description

                )

                self.canvas.command_stack.execute(command)

            # 发出组件被编辑信号

            self.component_edited.emit()

            QMessageBox.information(self, "保存成功", "组件修改已保存!")

            # 刷新组件列表和画布

            self._refresh_component_list()

            self.canvas.update()

        except Exception as e:

            QMessageBox.critical(self, "保存失败", f"保存过程中发生错误: {str(e)}")

    def _add_component(self) -> None:

        """添加组件"""

        if not self.canvas:

            QMessageBox.warning(self, "添加失败", "请先设置画布!")

            return

        # 创建新组件

        component_id = f"component_{len(self.canvas.nodes) + 1}"

        component = Node(component_id, 300, 200, "sensor")

        # 将组件添加到画布

        command = AddNodeCommand(self.canvas, component, (300, 200))

        self.canvas.command_stack.execute(command)

        # 刷新组件列表

        self._refresh_component_list()

        # 发出组件被添加信号

        self.component_added.emit()

        QMessageBox.information(self, "添加成功", f"组件 {component_id} 已添加!")

    def _delete_component(self) -> None:

        """删除组件"""

        if not self.current_component:

            QMessageBox.warning(self, "删除失败", "请先选择一个组件进行删除!")

            return

        if not self.canvas:

            QMessageBox.warning(self, "删除失败", "请先设置画布!")

            return

        # 确认删除

        reply = QMessageBox.question(

            self, "删除组件", f"确定要删除组件 {self.current_component.id} 吗?",

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if reply == QMessageBox.StandardButton.Yes:

            # 使用命令模式删除组件

            command = DeleteNodeCommand(self.canvas, self.current_component)

            self.canvas.command_stack.execute(command)

            # 刷新组件列表

            self._refresh_component_list()

            # 保存要删除的组件ID

            deleted_component_id = self.current_component.id

            # 发出组件被删除信号

            self.component_deleted.emit()

            # 清空编辑界面

            self._clear_component()

            QMessageBox.information(self, "删除成功", f"组件 {deleted_component_id} 已删除!")

    def _clear_component(self):

        """清空编辑界面"""

        self.id_input.clear()

        self.type_input.clear()

        self.name_input.clear()

        self.location_combo.setCurrentIndex(0)

        self.attach_point_x.setValue(0.0)

        self.attach_point_y.setValue(0.0)

        self.signal_threshold.setValue(0.5)

        self.activation.setValue(0.0)

        self.congenital_check.setChecked(True)

        self.state_input.clear()

        self.description_text.clear()

        self.current_component = None

    def _enable_buttons(self):

        """启用所有按钮"""

        self.add_component_btn.setEnabled(True)

        self.delete_component_btn.setEnabled(True)

        self.refresh_btn.setEnabled(True)

        self.save_btn.setEnabled(True)

    def _disable_buttons(self):

        """禁用所有按钮"""

        self.add_component_btn.setEnabled(False)

        self.delete_component_btn.setEnabled(False)

        self.refresh_btn.setEnabled(False)

        self.save_btn.setEnabled(False)
