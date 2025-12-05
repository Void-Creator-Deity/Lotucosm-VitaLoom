"""基于PyQt6的AI生命体编辑器原型"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
import sys

# 导入节点和连接线类
from .nodes import Node, ConnectionLine

# 导入画布类
from .canvas import OrganismCanvas

# 导入面板类
from .panels import PropertyPanel

# 导入项目树类
from .tree import ProjectTree

# 导入控制台类
from .console import ConsolePanel

# 导入命令模式
from ai_organism.editor.command import CommandStack


class PyQtOrganismEditor(QMainWindow):
    """AI生命体编辑器主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI生命体编辑器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化模拟状态
        self.simulation_running = False
        self.simulation_process = None
        
        # 初始化界面
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 创建中央小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建顶部工具栏
        self.create_tool_bar()
        
        # 创建分割器布局
        self._create_splitter_layout()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建菜单栏
        self.create_menu_bar()
        
    def _create_splitter_layout(self):
        """创建分割器布局"""
        # 主水平分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧项目树
        self.project_tree = ProjectTree()
        main_splitter.addWidget(self.project_tree)
        
        # 中央垂直分割器
        central_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(central_vertical_splitter)
        
        # 右侧属性面板
        self.property_panel = PropertyPanel()
        main_splitter.addWidget(self.property_panel)
        
        # 设置分割器尺寸
        main_splitter.setSizes([220, 700, 250])  # 项目树、画布区域和属性面板宽度
        
        # 中央水平分割器（画布+控制台）
        central_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_vertical_splitter.addWidget(central_horizontal_splitter)
        
        # 创建画布
        self.canvas = OrganismCanvas()
        central_horizontal_splitter.addWidget(self.canvas)
        
        # 控制台面板
        self.console_panel = ConsolePanel()
        central_vertical_splitter.addWidget(self.console_panel)
        central_vertical_splitter.setSizes([600, 200])  # 画布和控制台高度
        
        # 将主分割器添加到中央部件的布局中
        self.centralWidget().layout().addWidget(main_splitter)
        
        # 连接信号
        self.canvas.updateRequest.connect(self._update_property_panel)
        self.canvas.projectModified.connect(self._on_project_modified)
        self.canvas.commandExecuted.connect(self._on_command_executed)
        
        # 项目树信号连接
        self.project_tree.organism_created.connect(self._on_organism_created)
        self.project_tree.organism_deleted.connect(self._on_organism_deleted)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        
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
        
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
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
        
        cut_action = QAction("剪切", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        menu_bar.addMenu(edit_menu)
        
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
        new_button = QPushButton("新建")
        new_button.clicked.connect(self.new_project)
        tool_bar.addWidget(new_button)
        
        # 打开按钮
        open_button = QPushButton("打开")
        open_button.clicked.connect(self.open_project)
        tool_bar.addWidget(open_button)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_project)
        tool_bar.addWidget(save_button)
        
        # 分隔线
        tool_bar.addSeparator()
        
        # 运行模拟按钮
        run_button = QPushButton("运行模拟")
        run_button.clicked.connect(self.run_simulation)
        tool_bar.addWidget(run_button)
        
        # 停止模拟按钮
        stop_button = QPushButton("停止模拟")
        stop_button.clicked.connect(self.stop_simulation)
        tool_bar.addWidget(stop_button)
        
        # 分隔线
        tool_bar.addSeparator()
        
        # 导出生物按钮
        export_button = QPushButton("导出生物")
        export_button.clicked.connect(self.export_organism)
        tool_bar.addWidget(export_button)
        
        # 导入生物按钮
        import_button = QPushButton("导入生物")
        import_button.clicked.connect(self.import_organism)
        tool_bar.addWidget(import_button)
        
        self.addToolBar(tool_bar)
    
    def _update_property_panel(self):
        """更新属性面板"""
        if self.canvas.selected_node:
            self.property_panel.update_properties(self.canvas.selected_node)
        elif len(self.canvas.selected_nodes) == 1:
            self.property_panel.update_properties(self.canvas.selected_nodes[0])
        elif self.canvas.hovered_connection:
            self.property_panel.update_properties(self.canvas.hovered_connection)
        else:
            self.property_panel._clear_properties()
    
    def _on_project_modified(self):
        """项目修改处理"""
        self.status_bar.showMessage("项目已修改", 2000)
    
    def _on_command_executed(self):
        """命令执行处理"""
        self._update_property_panel()
    
    def _on_organism_created(self, organism_name):
        """生物创建处理"""
        self.status_bar.showMessage(f"生物 '{organism_name}' 已创建", 2000)
    
    def _on_organism_deleted(self, organism_name):
        """生物删除处理"""
        self.status_bar.showMessage(f"生物 '{organism_name}' 已删除", 2000)
    
    def new_project(self):
        """新建项目"""
        # 实现新建项目逻辑
        self.status_bar.showMessage("新建项目", 2000)
    
    def open_project(self):
        """打开项目"""
        # 实现打开项目逻辑
        self.status_bar.showMessage("打开项目", 2000)
    
    def save_project(self):
        """保存项目"""
        # 实现保存项目逻辑
        self.status_bar.showMessage("保存项目", 2000)
    
    def save_project_as(self):
        """另存为项目"""
        # 实现另存为项目逻辑
        self.status_bar.showMessage("另存为项目", 2000)
    
    def run_simulation(self):
        """运行模拟"""
        # 实现运行模拟逻辑
        self.status_bar.showMessage("运行模拟", 2000)
    
    def stop_simulation(self):
        """停止模拟"""
        # 实现停止模拟逻辑
        self.status_bar.showMessage("停止模拟", 2000)
    
    def export_organism(self):
        """导出生物"""
        # 实现导出生物逻辑
        self.status_bar.showMessage("导出生物", 2000)
    
    def import_organism(self):
        """导入生物"""
        # 实现导入生物逻辑
        self.status_bar.showMessage("导入生物", 2000)
    
    def undo(self):
        """撤销"""
        self.canvas.command_stack.undo()
        self.status_bar.showMessage("撤销", 2000)
    
    def redo(self):
        """重做"""
        self.canvas.command_stack.redo()
        self.status_bar.showMessage("重做", 2000)
    
    def cut(self):
        """剪切"""
        # 实现剪切逻辑
        self.status_bar.showMessage("剪切", 2000)
    
    def copy(self):
        """复制"""
        # 实现复制逻辑
        self.status_bar.showMessage("复制", 2000)
    
    def paste(self):
        """粘贴"""
        # 实现粘贴逻辑
        self.status_bar.showMessage("粘贴", 2000)
    
    def delete_selected(self):
        """删除选中项"""
        # 实现删除逻辑
        self.status_bar.showMessage("删除选中项", 2000)
    
    def toggle_properties(self):
        """切换属性面板显示"""
        self.property_panel.setVisible(not self.property_panel.isVisible())
    
    def toggle_project_tree(self):
        """切换项目树显示"""
        self.project_tree.setVisible(not self.project_tree.isVisible())
    
    def toggle_console(self):
        """切换控制台显示"""
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
    app = QApplication(sys.argv)
    window = PyQtOrganismEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()