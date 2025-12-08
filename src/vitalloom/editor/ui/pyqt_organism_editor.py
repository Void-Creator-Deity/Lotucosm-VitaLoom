# -*- coding: utf-8 -*-
"""基于PyQt6的AI生命体编辑器原型"""

import sys
import time
import json
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# PyQt6导入
from PyQt6 import QtWidgets, QtCore, QtGui

# 导入命令模式，用于剪切、复制、粘贴功能
from vitalloom.editor.commands.command import DeleteNodeCommand, AddNodeCommand, CreateConnectionCommand

# 导入节点类，用于粘贴功能
from vitalloom.editor.ui.nodes import Node, ConnectionLine

# 导入编辑器组件
from vitalloom.editor.ui.memory_editor_widget import MemoryEditorWidget
from vitalloom.editor.ui.component_editor_widget import ComponentEditorWidget

# 导入画布类
from typing import Any, Optional
from vitalloom.editor.ui.canvas import OrganismCanvas

# 导入面板类
from vitalloom.editor.ui.panels import PropertyPanel

# 导入项目树类
from vitalloom.editor.ui.tree import ProjectTree

# 导入控制台类
from vitalloom.editor.ui.console import ConsolePanel


class PyQtOrganismEditor(QtWidgets.QMainWindow):
    """AI生命体编辑器主窗口"""

    def __init__(self):
        super().__init__()
        # 类型注释
        self.parent_widget: Any = None
        self.command_stack: list[Any] = []

        self.setWindowTitle("AI生命体编辑器")
        self.setGeometry(100, 100, 1200, 800)

        # 初始化模拟状态
        self.simulation_running = False
        self.simulation = None
        self.simulation_thread = None
        self.current_mode = "edit"  # "edit" or "simulate"

        # 项目状态
        self.project_modified = False
        self.current_project_path = None

        # 剪切板
        self.clipboard: dict = {  # type: ignore
            'nodes': [],
            'connections': [],
            'copy_time': None
        }

        # 初始化编辑器组件
        self.project_tree = None
        self.canvas: Optional[OrganismCanvas] = None
        self.property_panel = None
        self.memory_editor = None
        self.component_editor = None
        self.console_panel = None

        # 初始化界面
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        # 创建中央小部件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建顶部工具栏
        self.create_tool_bar()

        # 创建分割器布局
        self._create_splitter_layout(main_layout)

        # 创建状态栏
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # 创建菜单栏
        self.create_menu_bar()

    def _create_splitter_layout(self, main_layout: QtWidgets.QVBoxLayout):
        """创建分割器布局"""

        # 主水平分割器
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # 左侧项目树
        self.project_tree = ProjectTree()
        main_splitter.addWidget(self.project_tree)

        # 中央垂直分割器
        central_vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_splitter.addWidget(central_vertical_splitter)

        # 中央水平分割器（画布+控制台）
        central_horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        central_vertical_splitter.addWidget(central_horizontal_splitter)

        # 创建画布
        self.canvas: Optional[OrganismCanvas] = OrganismCanvas()
        # 设置画布的父对象引用，便于画布访问主窗口组件
        self.canvas.set_parent(self)
        central_horizontal_splitter.addWidget(self.canvas)

        # 右侧垂直分割器（属性面板+记忆编辑器+组件编辑器）
        right_vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_splitter.addWidget(right_vertical_splitter)

        # 右侧上方：属性面板
        self.property_panel = PropertyPanel()
        right_vertical_splitter.addWidget(self.property_panel)

        # 右侧中间：记忆编辑器
        self.memory_editor = MemoryEditorWidget()
        right_vertical_splitter.addWidget(self.memory_editor)

        # 右侧下方：组件编辑器
        self.component_editor = ComponentEditorWidget(self.canvas)
        right_vertical_splitter.addWidget(self.component_editor)

        # 设置分割器尺寸
        main_splitter.setSizes([220, 700, 300])  # type: ignore  # 项目树、画布区域和右侧面板宽度
        right_vertical_splitter.setSizes([200, 300, 300])  # type: ignore  # 属性面板、记忆编辑器和组件编辑器高度

        # 控制台面板
        self.console_panel = ConsolePanel()
        central_vertical_splitter.addWidget(self.console_panel)

        # 设置画布和控制台高度
        central_vertical_splitter.setSizes([600, 200])  # type: ignore  # 画布和控制台高度

        # 将主分割器添加到中央部件的布局中
        main_layout.addWidget(main_splitter)

        # 连接信号
        self.canvas.updateRequest.connect(self._update_property_panel)  # type: ignore[attr-defined, union-attr]
        self.canvas.projectModified.connect(self._on_project_modified)  # type: ignore[attr-defined, union-attr]
        self.canvas.commandExecuted.connect(self._on_command_executed)  # type: ignore[attr-defined, union-attr]

        # 项目树信号连接
        self.project_tree.organism_created.connect(self._on_organism_created)  # type: ignore
        self.project_tree.organism_deleted.connect(self._on_organism_deleted)  # type: ignore

        # 编辑器信号连接
        self.memory_editor.memory_edited.connect(self._on_memory_edited)  # type: ignore
        self.component_editor.component_edited.connect(self._on_component_edited)  # type: ignore

    def _create_file_menu(self, menu_bar: QtWidgets.QMenuBar):
        """创建文件菜单"""
        file_menu = QtWidgets.QMenu("文件", self)

        new_action = QtGui.QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)  # type: ignore
        file_menu.addAction(new_action)  # type: ignore

        open_action = QtGui.QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)  # type: ignore
        file_menu.addAction(open_action)  # type: ignore

        save_action = QtGui.QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)  # type: ignore
        file_menu.addAction(save_action)  # type: ignore

        save_as_action = QtGui.QAction("另存为", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)  # type: ignore
        file_menu.addAction(save_as_action)  # type: ignore

        file_menu.addSeparator()

        exit_action = QtGui.QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)  # type: ignore
        file_menu.addAction(exit_action)  # type: ignore

        menu_bar.addMenu(file_menu)

    def _create_edit_menu(self, menu_bar: QtWidgets.QMenuBar):
        """创建编辑菜单"""

        edit_menu = QtWidgets.QMenu("编辑", self)

        undo_action = QtGui.QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)  # type: ignore
        edit_menu.addAction(undo_action)  # type: ignore

        redo_action = QtGui.QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)  # type: ignore
        edit_menu.addAction(redo_action)  # type: ignore

        edit_menu.addSeparator()

        cut_action = QtGui.QAction("剪切", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)  # type: ignore
        edit_menu.addAction(cut_action)  # type: ignore

        copy_action = QtGui.QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)  # type: ignore
        edit_menu.addAction(copy_action)  # type: ignore

        paste_action = QtGui.QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)  # type: ignore
        edit_menu.addAction(paste_action)  # type: ignore

        edit_menu.addSeparator()

        delete_action = QtGui.QAction("删除", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)  # type: ignore
        edit_menu.addAction(delete_action)  # type: ignore

        menu_bar.addMenu(edit_menu)

    def _create_tool_menu(self, menu_bar: QtWidgets.QMenuBar):
        """创建工具菜单"""
        tool_menu = QtWidgets.QMenu("工具", self)

        run_simulation_action = QtGui.QAction("运行模拟", self)
        run_simulation_action.setShortcut("F5")
        run_simulation_action.triggered.connect(self.run_simulation)  # type: ignore
        tool_menu.addAction(run_simulation_action)  # type: ignore

        stop_simulation_action = QtGui.QAction("停止模拟", self)
        stop_simulation_action.setShortcut("F6")
        stop_simulation_action.triggered.connect(self.stop_simulation)  # type: ignore
        tool_menu.addAction(stop_simulation_action)  # type: ignore

        tool_menu.addSeparator()

        export_organism_action = QtGui.QAction("导出生物", self)
        export_organism_action.triggered.connect(self.export_organism)  # type: ignore
        tool_menu.addAction(export_organism_action)  # type: ignore

        import_organism_action = QtGui.QAction("导入生物", self)
        import_organism_action.triggered.connect(self.import_organism)  # type: ignore
        tool_menu.addAction(import_organism_action)  # type: ignore

        menu_bar.addMenu(tool_menu)

    def _create_help_menu(self, menu_bar: QtWidgets.QMenuBar):
        """创建帮助菜单"""

        help_menu = QtWidgets.QMenu("帮助", self)

        help_action = QtGui.QAction("使用帮助", self)
        help_action.triggered.connect(self.show_help)  # type: ignore
        help_menu.addAction(help_action)  # type: ignore

        about_action = QtGui.QAction("关于", self)
        about_action.triggered.connect(self.show_about)  # type: ignore
        help_menu.addAction(about_action)  # type: ignore

        menu_bar.addMenu(help_menu)

    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QtWidgets.QMenuBar()

        # 创建各个菜单
        self._create_file_menu(menu_bar)
        self._create_edit_menu(menu_bar)
        self._create_tool_menu(menu_bar)
        self._create_help_menu(menu_bar)

        self.setMenuBar(menu_bar)

    def create_tool_bar(self):
        """创建工具栏"""

        tool_bar = QtWidgets.QToolBar("主工具栏")
        tool_bar.setStyleSheet("""
            QToolBar {
                background-color: #252526;
                color: #ffffff;
                border: none;
                padding: 4px 8px;
                spacing: 8px;
            }
            QToolButton {
                background-color: transparent;
                color: #ffffff;
                padding: 6px 12px;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 13px;
                min-width: 80px;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
                border: 1px solid #606060;
            }
            QToolButton:pressed,
            QToolButton:checked {
                background-color: #0e639c;
                border: 1px solid #1177bb;
            }
            QLabel {
                color: #cccccc;
                margin-right: 8px;
                font-size: 13px;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 120px;
                font-size: 13px;
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
            QComboBox::item {
                background-color: #252526;
                color: #ffffff;
                padding: 8px 12px;
            }
            QComboBox::item:hover {
                background-color: #3c3c3c;
            }
            QComboBox::item:selected {
                background-color: #0e639c;
            }
        """)

        # 新建按钮
        new_button = QtWidgets.QPushButton("新建")
        new_button.clicked.connect(self.new_project)  # type: ignore
        tool_bar.addWidget(new_button)

        # 打开按钮
        open_button = QtWidgets.QPushButton("打开")
        open_button.clicked.connect(self.open_project)  # type: ignore
        tool_bar.addWidget(open_button)

        # 保存按钮
        save_button = QtWidgets.QPushButton("保存")
        save_button.clicked.connect(self.save_project)  # type: ignore
        tool_bar.addWidget(save_button)

        # 分隔线
        tool_bar.addSeparator()

        # 运行模拟按钮
        run_button = QtWidgets.QPushButton("运行模拟")
        run_button.clicked.connect(self.run_simulation)  # type: ignore
        tool_bar.addWidget(run_button)

        # 停止模拟按钮
        stop_button = QtWidgets.QPushButton("停止模拟")
        stop_button.clicked.connect(self.stop_simulation)  # type: ignore
        tool_bar.addWidget(stop_button)

        # 分隔线
        tool_bar.addSeparator()

        # 导出生物按钮
        export_button = QtWidgets.QPushButton("导出生物")
        export_button.clicked.connect(self.export_organism)  # type: ignore
        tool_bar.addWidget(export_button)

        # 导入生物按钮
        import_button = QtWidgets.QPushButton("导入生物")
        import_button.clicked.connect(self.import_organism)  # type: ignore
        tool_bar.addWidget(import_button)

        self.addToolBar(tool_bar)

    def _update_property_panel(self):
        """更新属性面板"""

        if self.canvas and self.property_panel:
            if self.canvas.selected_node:  # type: ignore[attr-defined, union-attr]
                self.property_panel.update_properties(self.canvas.selected_node)  # type: ignore[attr-defined, union-attr]
            elif self.canvas and hasattr(self.canvas, 'selected_nodes') and len(self.canvas.selected_nodes) == 1:  # type: ignore[attr-defined, union-attr]
                if self.canvas and hasattr(self.canvas, 'selected_nodes'):
                    self.property_panel.update_properties(self.canvas.selected_nodes[0])  # type: ignore[attr-defined, union-attr]
            elif self.canvas.hovered_connection:  # type: ignore[attr-defined, union-attr]
                self.property_panel.update_properties(self.canvas.hovered_connection)  # type: ignore[attr-defined, union-attr]
        else:
            if hasattr(self, "property_panel") and self.property_panel is not None:
                if hasattr(self.property_panel, "clear_properties"):
                    self.property_panel.clear_properties()

    def _on_project_modified(self):
        """项目修改处理"""
        self.status_bar.showMessage("项目已修改", 2000)

    def _on_command_executed(self):
        """命令执行处理"""

        self._update_property_panel()

    def _on_organism_created(self, organism_name: str):
        """生物创建处理"""
        self.status_bar.showMessage(f"生物 '{organism_name}' 已创建", 2000)

    def _on_organism_deleted(self, organism_name: str):
        """生物删除处理"""

        self.status_bar.showMessage(f"生物 '{organism_name}' 已删除", 2000)

    def _on_memory_edited(self):
        """记忆编辑处理"""
        self.status_bar.showMessage("记忆已编辑", 2000)
        self._on_project_modified()  # 标记项目为已修改

    def _on_component_edited(self):
        """组件编辑处理"""

        self.status_bar.showMessage("组件已编辑", 2000)
        self._on_project_modified()  # 标记项目为已修改

    def new_project(self):
        """新建项目"""
        # 询问是否保存当前项目
        if self.project_modified:

            reply = QtWidgets.QMessageBox.question(self, "保存项目", "当前项目已修改，是否保存？",
                                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                if not self.save_project():
                    return
            elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return

        # 清空画布
        if self.canvas is not None:
            if self.canvas:
                if hasattr(self.canvas, 'nodes'):  # type: ignore[attr-defined, union-attr]
                    self.canvas.nodes.clear()  # type: ignore[attr-defined, union-attr]
                if hasattr(self.canvas, 'connections'):
                    self.canvas.connections.clear()
                if hasattr(self.canvas, 'selected_nodes'):
                    self.canvas.selected_nodes.clear()  # type: ignore[attr-defined, union-attr]  # type: ignore[attr-defined]

            self.canvas.selected_node = None  # type: ignore[attr-defined, union-attr]
            self.canvas.hovered_node = None
            self.canvas.hovered_connection = None  # type: ignore[union-attr, unknown-member]  # type: ignore[union-attr, unknown-member]  # type: ignore[union-attr, unknown-member]

        # 创建默认节点
        if self.canvas is not None and hasattr(self.canvas, "_create_default_nodes"):
            self.canvas._create_default_nodes()  # type: ignore

        # 更新项目树
        if self.project_tree and self.canvas and hasattr(self.canvas, 'nodes') and hasattr(self.canvas, 'connections') and hasattr(self.project_tree, 'update_tree'):
            self.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[union-attr, arg-type]  # type: ignore[attr-defined, assignment, union-attr]

        # 更新属性面板
        if self.property_panel:
            self.property_panel.clear_properties()

        # 更新状态
        self.current_project_path = None
        self.project_modified = False
        self.setWindowTitle("AI生命体编辑器 - 新建项目")
        self.status_bar.showMessage("新建项目", 2000)

    def open_project(self):

        """打开项目"""

        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 询问是否保存当前项目

        if self.project_modified:

            reply = QtWidgets.QMessageBox.question(self, "保存项目", "当前项目已修改，是否保存？",

                                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)

            if reply == QtWidgets.QMessageBox.StandardButton.Yes:

                if not self.save_project():

                    return False

            elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:

                return False

        # 打开文件对话框，默认路径为data目录
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "打开项目", data_dir, "AI生命体项目 (*.aiorg);;所有文件 (*.*)")

        if not file_path:

            return False

        try:

            # 加载项目文件

            with open(file_path, 'r', encoding='utf-8') as f:

                project_data = json.load(f)

            # 清空画布

            if self.canvas:

                self.canvas.nodes.clear()

                self.canvas.connections.clear()

                self.canvas.selected_nodes.clear()

                self.canvas.selected_node = None  # type: ignore[attr-defined, union-attr]

                self.canvas.hovered_node = None

            self.canvas.hovered_connection = None  # type: ignore[union-attr, unknown-member]

            # 从项目数据中创建节点

            nodes = []

            node_map = {}

            # 创建节点

            for node_data in project_data.get('nodes', []):

                node = Node(

                    node_id=node_data.get('id', f'node_{len(nodes)}'),  # type: ignore[arg-type]  # type: ignore[arg-type]

                    x=node_data.get('x', 300.0),

                    y=node_data.get('y', 200.0),

                    node_type=node_data.get('type', 'sensor')

                )

                # 设置节点半径，使用保存的值

                if 'radius' in node_data:

                    node.radius = node_data['radius']

                nodes.append(node)  # type: ignore[arg-type]  # type: ignore[arg-type]

                node_map[node.id] = node

            # 创建连接

            connections = []

            for connection_data in project_data.get('connections', []):

                start_node = node_map.get(connection_data.get('start_node'))  # type: ignore  # type: ignore[all]  # type: ignore[call-overload, arg-type, unknown-member, type-var, union-attr, assignment, union]  # type: ignore[call-overload, arg-type]

                end_node = node_map.get(connection_data.get('end_node'))  # type: ignore  # type: ignore[all]  # type: ignore[call-overload, arg-type, unknown-member, type-var, union-attr, assignment, union]  # type: ignore[call-overload, arg-type]

                if start_node and end_node:

                    connection = ConnectionLine(start_node, end_node)  # type: ignore[arg-type]  # type: ignore[arg-type]

                    connection.weight = connection_data.get('weight', 1.0)

                    connections.append(connection)  # type: ignore[arg-type]  # type: ignore[arg-type]

            # 更新画布

            self.canvas.nodes = nodes  # type: ignore[union-attr]

            self.canvas.connections = connections  # type: ignore[union-attr]

            # 更新项目树

            if hasattr(self, 'project_tree') and self.canvas:

                if self.project_tree and self.canvas:
                    if self.canvas and hasattr(self.canvas, 'nodes') and hasattr(self.canvas, 'connections') and hasattr(self.project_tree, 'update_tree'):
                        self.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[union-attr, arg-type]  # type: ignore[union-attr, arg-type]

            # 更新属性面板

            if self.property_panel:

                self.property_panel.clear_properties()

            # 更新状态

            self.current_project_path = file_path

            self.project_modified = False

            self.setWindowTitle(f"AI生命体编辑器 - {file_path}")

            self.status_bar.showMessage(f"打开项目: {file_path}", 2000)

            return True

        except (IOError, json.JSONDecodeError, ValueError) as e:

            QtWidgets.QMessageBox.critical(self, "打开项目失败", f"无法打开项目文件: {str(e)}")

            self.status_bar.showMessage("打开项目失败", 2000)

            return False

    def save_project(self):

        """保存项目"""

        if not hasattr(self, 'current_project_path') or not self.current_project_path:

            return self.save_project_as()

        return self._save_project_to_path(self.current_project_path)

    def save_project_as(self):

        """另存为项目"""

        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存项目", data_dir, "AI生命体项目 (*.aiorg);;所有文件 (*.*)")

        if not file_path:

            return False

        # 确保文件扩展名正确

        if not file_path.endswith('.aiorg'):

            file_path += '.aiorg'

        return self._save_project_to_path(file_path)

    def _save_project_to_path(self, file_path: str):

        """保存项目到指定路径"""

        try:

            # 构建项目数据

            project_data: dict[str, Any] = {

                'version': '1.0',

                'nodes': [],

                'connections': []

            }

            # 保存节点

            for node in self.canvas.nodes:  # type: ignore[union-attr]  # type: ignore[union-attr]  # type: ignore[union-attr]

                node_data: dict[str, Any] = {

                    'id': node.id,

                    'x': node.x,

                    'y': node.y,

                    'type': node.type,

                    'radius': node.radius

                }

                project_data['nodes'].append(node_data)  # type: ignore[union-attr, arg-type]

            # 保存连接

            for connection in self.canvas.connections:  # type: ignore[union-attr]  # type: ignore[union-attr]

                connection_data: dict[str, Any] = {

                    'start_node': connection.start_node.id,

                    'end_node': connection.end_node.id,

                    'weight': connection.weight

                }

                project_data['connections'].append(connection_data)  # type: ignore[union-attr, arg-type]

            # 保存文件

            with open(file_path, 'w', encoding='utf-8') as f:

                json.dump(project_data, f, indent=2, ensure_ascii=False)

            # 更新状态

            self.current_project_path = file_path

            self.project_modified = False

            self.setWindowTitle(f"AI生命体编辑器 - {file_path}")

            self.status_bar.showMessage(f"保存项目: {file_path}", 2000)

            return True

        except Exception as e:

            QtWidgets.QMessageBox.critical(self, "保存项目失败", f"无法保存项目文件: {str(e)}")

            self.status_bar.showMessage("保存项目失败", 2000)

            return False

    def run_simulation(self):

        """运行模拟"""

        # 切换到模拟模式

        self.current_mode = "simulate"

        self.simulation_running = True

        # 尝试导入Simulation类

        Simulation = None

        try:
            from lotucosm.simulator.simulation import Simulation
        except ImportError:
            Simulation = None

        if not Simulation:

            QtWidgets.QMessageBox.warning(self, "模拟启动失败", "无法导入模拟模块")

            self.status_bar.showMessage("模拟启动失败", 2000)

            self.simulation_running = False

            self.current_mode = "edit"

            return

        try:

            # 创建模拟对象

            self.simulation = Simulation(self.width(), self.height())
            
            # 清除默认的测试生物体
            self.simulation.organisms.clear()
            
            # 检查编辑器中是否有设计的生物体
            if hasattr(self, 'canvas') and hasattr(self.canvas, 'nodes'):
                organisms = [node for node in self.canvas.nodes if node.type == "organism"]  # type: ignore[union-attr]
                
                if organisms:
                    # 导入Organism类
                    from vitalloom.organisms.organism import Organism
                    from vitalloom.components.sensors import Sensor
                    from vitalloom.components.actuators import Actuator
                    
                    for org_node in organisms:
                        # 创建生物体对象
                        org = Organism(org_node.id, (org_node.x, org_node.y))
                        
                        # 添加传感器和效应器
                        for node in self.canvas.nodes:  # type: ignore[union-attr]
                            if node.type == "sensor":
                                sensor = Sensor(node.id, organism_id=org.id, attach_point=(node.x - org_node.x, node.y - org_node.y))
                                org.add_sensor(sensor)
                            elif node.type == "actuator":
                                actuator = Actuator(node.id, organism_id=org.id, attach_point=(node.x - org_node.x, node.y - org_node.y))
                                org.add_actuator(actuator)
                        
                        # 添加连接
                        for connection in self.canvas.connections:  # type: ignore[union-attr]
                            org.connect_tools(connection.start_node.id, connection.end_node.id, connection.weight)
                        
                        # 添加到模拟中
                        self.simulation.organisms.append(org)
                        self.simulation.selected_organism = org
                        
                    self.status_bar.showMessage(f"成功加载 {len(organisms)} 个设计的生物体", 2000)
                else:
                    self.status_bar.showMessage("画布中没有生物体，使用默认测试生物", 2000)
            else:
                self.status_bar.showMessage("画布不可用，使用默认测试生物", 2000)

            # 创建并启动模拟线程

            class SimulationThread(QtCore.QThread):

                """模拟线程"""

                update_signal = QtCore.pyqtSignal()

                def __init__(self, simulation: Any):

                    """初始化模拟线程"""

                    super().__init__()

                    self.simulation = simulation

                    self.running = True

                def run(self):

                    """运行模拟线程"""

                    while self.running:

                        # 更新模拟

                        self.simulation.update()

                        # 发送更新信号

                        self.update_signal.emit()

                        # 控制模拟速度

                        time.sleep(0.05)  # 20 FPS

                def stop(self):

                    """停止模拟线程"""

                    self.running = False

            self.simulation_thread = SimulationThread(self.simulation)

            # 连接信号

            def update_simulation():

                # 更新画布或其他UI元素

                organism_count = len(self.simulation.organisms) if hasattr(self.simulation, 'organisms') else 0  # type: ignore[union-attr]

                sim_time = getattr(self.simulation, 'time', 0)

                self.status_bar.showMessage(f"模拟运行中 - 生物数量: {organism_count}, 时间: {sim_time}", 1000)

            self.simulation_thread.update_signal.connect(update_simulation)  # type: ignore

            # 启动线程

            self.simulation_thread.start()

            self.status_bar.showMessage("开始模拟", 2000)

        except (ValueError, RuntimeError, ImportError, AttributeError) as e:

            QtWidgets.QMessageBox.warning(self, "模拟启动失败", f"无法启动模拟: {str(e)}")

            self.status_bar.showMessage("模拟启动失败", 2000)

            self.simulation_running = False

            self.current_mode = "edit"

    def stop_simulation(self):

        """停止模拟"""

        # 停止模拟线程

        if hasattr(self, 'simulation_thread') and self.simulation_thread:
            if hasattr(self.simulation_thread, 'isRunning') and self.simulation_thread.isRunning():
                if hasattr(self.simulation_thread, 'stop'):
                    self.simulation_thread.stop()
                if hasattr(self.simulation_thread, 'wait'):
                    self.simulation_thread.wait()

        # 切换回编辑模式

        self.current_mode = "edit"

        self.simulation_running = False

        self.status_bar.showMessage("停止模拟", 2000)

    def export_organism(self):

        """导出生物"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 检查是否有选中的生物

        if not self.canvas.nodes:  # type: ignore[union-attr]

            QtWidgets.QMessageBox.warning(self, "导出生物", "画布中没有生物可以导出！")

            return False

        # 只导出生物体类型的节点

        organisms = [node for node in self.canvas.nodes if node.type == "organism"]  # type: ignore[union-attr]

        if not organisms:

            QtWidgets.QMessageBox.warning(self, "导出生物", "画布中没有生物体类型的节点可以导出！")

            return False

        # 打开文件对话框

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出生物", data_dir, "AI生命体 (*.aiorganism);;所有文件 (*.*)")

        if not file_path:

            return False

        # 确保文件扩展名正确

        if not file_path.endswith('.aiorganism'):

            file_path += '.aiorganism'

        try:

            # 构建生物数据

            organism_data: dict[str, Any] = {

                'version': '1.0',

                'nodes': [],

                'connections': []

            }

            # 保存节点数据

            for node in self.canvas.nodes:  # type: ignore[union-attr]

                node_data: dict[str, Any] = {

                    'id': node.id,

                    'x': node.x,

                    'y': node.y,

                    'type': node.type,

                    'radius': node.radius

                }

                organism_data['nodes'].append(node_data)  # type: ignore[union-attr, arg-type]

            # 保存连接数据

            for connection in self.canvas.connections:  # type: ignore[union-attr]

                connection_data: dict[str, Any] = {

                    'start_node': connection.start_node.id,

                    'end_node': connection.end_node.id,

                    'weight': connection.weight

                }

                organism_data['connections'].append(connection_data)  # type: ignore[union-attr, arg-type]

            # 保存文件

            with open(file_path, 'w', encoding='utf-8') as f:

                json.dump(organism_data, f, indent=2, ensure_ascii=False)

            self.status_bar.showMessage(f"生物已导出到: {file_path}", 2000)

            return True

        except (IOError, PermissionError, json.JSONDecodeError) as e:

            QtWidgets.QMessageBox.critical(self, "导出生物失败", f"无法导出生物: {str(e)}")

            self.status_bar.showMessage("导出生物失败", 2000)

            return False

    def import_organism(self):

        """导入生物"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "导入生物", data_dir, "AI生命体 (*.aiorganism);;所有文件 (*.*)")

        if not file_path:

            return False

        try:

            # 加载生物文件

            with open(file_path, 'r', encoding='utf-8') as f:

                organism_data = json.load(f)

            # 从生物数据中创建节点

            nodes = []

            node_map = {}

            # 创建节点

            for node_data in organism_data.get('nodes', []):

                node = Node(

                    node_id=node_data.get('id', f'node_{len(nodes)}'),  # type: ignore[arg-type]

                    x=node_data.get('x', 300.0),

                    y=node_data.get('y', 200.0),

                    node_type=node_data.get('type', 'sensor')

                )

                # 设置节点半径，使用保存的值

                if 'radius' in node_data:

                    node.radius = node_data['radius']

                nodes.append(node)  # type: ignore[arg-type]

                node_map[node.id] = node

            # 创建连接

            connections = []

            for connection_data in organism_data.get('connections', []):

                start_node = node_map.get(connection_data.get('start_node'))  # type: ignore

                end_node = node_map.get(connection_data.get('end_node'))  # type: ignore

                if start_node and end_node:

                    connection = ConnectionLine(start_node, end_node)  # type: ignore[arg-type]

                    connection.weight = connection_data.get('weight', 1.0)

                    connections.append(connection)  # type: ignore[arg-type]

            # 将导入的节点和连接添加到画布

            self.canvas.nodes.extend(nodes)  # type: ignore[union-attr, arg-type]

            self.canvas.connections.extend(connections)  # type: ignore[union-attr, arg-type]

            # 更新项目树

            if hasattr(self, 'project_tree'):

                self.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[union-attr, arg-type]

            # 更新属性面板

            if self.property_panel:

                self.property_panel.clear_properties()

            # 更新项目状态

            self.project_modified = True

            self._on_project_modified()

            self.status_bar.showMessage(f"生物已导入: {file_path}", 2000)

            return True

        except (IOError, PermissionError, json.JSONDecodeError, FileNotFoundError) as e:

            QtWidgets.QMessageBox.critical(self, "导入生物失败", f"无法导入生物: {str(e)}")

            self.status_bar.showMessage("导入生物失败", 2000)

            return False

    def undo(self):

        """撤销"""

        if self.canvas and hasattr(self.canvas, 'command_stack') and self.canvas.command_stack:
            self.canvas.command_stack.undo()

        self.status_bar.showMessage("撤销", 2000)

    def redo(self):

        """重做"""

        if self.canvas and hasattr(self.canvas, 'command_stack') and self.canvas.command_stack:
            self.canvas.command_stack.redo()

        self.status_bar.showMessage("重做", 2000)

    def cut(self):

        """剪切"""

        # 检查是否有选中的节点

        if self.canvas and hasattr(self.canvas, 'selected_nodes') and not self.canvas.selected_nodes:

            return False

        # 保存选中的节点和连接到剪切板

        self.copy()

        # 删除选中的节点和相关连接

        if self.canvas and hasattr(self.canvas, 'selected_nodes'):
            for node in self.canvas.selected_nodes[:]:  # type: ignore  # type: ignore[all]  # type: ignore[attr-defined, union-attr, unknown-member]  # type: ignore[attr-defined, union-attr]
                # 创建并执行删除命令
                command = DeleteNodeCommand(self.canvas, node)
                if self.canvas and hasattr(self.canvas, 'command_stack') and self.canvas.command_stack:
                    self.canvas.command_stack.execute(command)  # type: ignore[union-attr]  # type: ignore[union-attr]

        # 更新项目树

        if hasattr(self, 'project_tree'):

            self.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[union-attr, arg-type]

        # 更新属性面板

        if self.property_panel:

            self.property_panel.clear_properties()

        # 更新项目状态

        self.project_modified = True

        self._on_project_modified()

        self.status_bar.showMessage("剪切完成", 2000)

        return True

    def copy(self):

        """复制"""

        # 检查是否有选中的节点

        if not self.canvas.selected_nodes:  # type: ignore  # type: ignore[all]  # type: ignore[attr-defined, union-attr, unknown-member]  # type: ignore[attr-defined, union-attr]  # type: ignore[attr-defined]

            return False

        # 保存选中的节点和相关连接到剪切板

        nodes = []
        if self.canvas and hasattr(self.canvas, 'selected_nodes'):
            nodes = self.canvas.selected_nodes[:]  # type: ignore[attr-defined, union-attr]

        # 找到所有与选中节点相关的连接

        connections = [conn for conn in self.canvas.connections  # type: ignore[union-attr] \

                      if conn.start_node in nodes or conn.end_node in nodes]

        # 保存到剪切板

        self.clipboard: dict[str, Any] = {

            'nodes': nodes,

            'connections': connections,

            'copy_time': time.time()

        }

        self.status_bar.showMessage(f"复制了 {len(nodes)} 个节点和 {len(connections)} 个连接", 2000)

        return True

    def paste(self):

        """粘贴"""

        # 检查剪切板是否有内容

        if not self.clipboard.get('nodes', []):  # type: ignore

            return False

        # 计算偏移量，防止粘贴到原位置

        offset_x = 50

        offset_y = 50

        # 创建节点映射，用于重建立连接

        node_map = {}

        # 粘贴节点

        new_nodes = []

        for node in self.clipboard.get('nodes', []):  # type: ignore

            # 创建新节点，添加偏移量

            new_node = Node(

                node_id=f"{node.type}_{len([n for n in self.canvas.nodes if n.type == node.type]) + 1}_{int(time.time()) % 1000}",  # type: ignore[union-attr]
                x=node.x + offset_x,

                y=node.y + offset_y,

                node_type=node.type

            )

            new_nodes.append(new_node)  # type: ignore[arg-type]

            node_map[node] = new_node

            # 创建并执行添加节点命令

            command = AddNodeCommand(self.canvas, new_node, (new_node.x, new_node.y))

            self.canvas.command_stack.execute(command)  # type: ignore[union-attr]

        # 粘贴连接

        for conn in self.clipboard.get('connections', []):  # type: ignore

            # 检查连接的节点是否都已粘贴

            if conn.start_node in node_map and conn.end_node in node_map:

                # 创建新连接

                new_conn = ConnectionLine(node_map[conn.start_node], node_map[conn.end_node])  # type: ignore[arg-type]

                new_conn.weight = conn.weight

                # 创建并执行创建连接命令

                command = CreateConnectionCommand(self.canvas, new_conn)
                self.canvas.command_stack.execute(command)  # type: ignore[union-attr]

        # 更新项目树
        if hasattr(self, 'project_tree'):
            self.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[union-attr, arg-type]

        # 更新属性面板
        if self.property_panel:
            self.property_panel.clear_properties()

        # 更新项目状态
        self.project_modified = True

        self._on_project_modified()

        self.status_bar.showMessage(f"粘贴了 {len(new_nodes)} 个节点", 2000)  # type: ignore[arg-type]

        return True

    def delete_selected(self):

        """删除选中项"""

        # 检查是否有选中的节点

        if not self.canvas.selected_nodes:  # type: ignore

            return False

        # 删除选中的节点和相关连接

        for node in self.canvas.selected_nodes[:]:  # type: ignore

            # 创建并执行删除命令

            command = DeleteNodeCommand(self.canvas, node)

            self.canvas.command_stack.execute(command)  # type: ignore[union-attr]

        # 更新项目树

        if hasattr(self.parent_widget, 'project_tree'):  # type: ignore[attr-defined]

            if hasattr(self, 'parent_widget') and self.parent_widget and hasattr(self.parent_widget, 'project_tree') and hasattr(self.parent_widget.project_tree, 'update_tree') and self.canvas and hasattr(self.canvas, 'nodes') and hasattr(self.canvas, 'connections'):  # type: ignore[attr-defined]
                self.parent_widget.project_tree.update_tree(self.canvas.nodes, self.canvas.connections)  # type: ignore[attr-defined, assignment, union-attr]  # type: ignore[attr-defined]

        # 更新属性面板

        if self.property_panel:

            self.property_panel.clear_properties()

        # 更新项目状态

        self.project_modified = True

        self._on_project_modified()

        if self.canvas and hasattr(self.canvas, 'selected_nodes'):
            self.status_bar.showMessage(f"删除了 {len(self.canvas.selected_nodes)} 个节点", 2000)  # type: ignore[attr-defined, union-attr]

        return True

    def toggle_properties(self):

        """切换属性面板显示"""

        if self.property_panel and hasattr(self.property_panel, 'setVisible') and hasattr(self.property_panel, 'isVisible'):
            self.property_panel.setVisible(not self.property_panel.isVisible())

    def toggle_project_tree(self):

        """切换项目树显示"""

        if self.project_tree and hasattr(self.project_tree, 'setVisible') and hasattr(self.project_tree, 'isVisible'):
            self.project_tree.setVisible(not self.project_tree.isVisible())

    def toggle_console(self):

        """切换控制台显示"""

        if self.console_panel and hasattr(self.console_panel, 'setVisible') and hasattr(self.console_panel, 'isVisible'):
            self.console_panel.setVisible(not self.console_panel.isVisible())

    def show_help(self):

        """显示帮助"""

        # 实现显示帮助逻辑

        self.status_bar.showMessage("显示帮助", 2000)

    def show_about(self):

        """显示关于"""

        # 实现显示关于逻辑

        self.status_bar.showMessage("显示关于", 2000)


def main():
    """主函数"""
    app = QtWidgets.QApplication(sys.argv)
    window = PyQtOrganismEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
