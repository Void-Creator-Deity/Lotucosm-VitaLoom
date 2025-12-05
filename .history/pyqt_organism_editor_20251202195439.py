"""基于PyQt6的AI生命体编辑器原型"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QPen, QBrush
import sys


class OrganismCanvas(QWidget):
    """生物可视化编辑画布"""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1e1e1e;")
        self.objects = []
        self.selected_objects = []
        self.dragging = False
        self.drag_start = QPoint()
        self.drag_object = None
    
    def paintEvent(self, event):
        """绘制画布内容"""
        painter = QPainter(self)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制中心生物
        center_x, center_y = self.width() // 2, self.height() // 2
        
        # 绘制生物主体
        painter.setBrush(QBrush(QColor(100, 150, 200)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawEllipse(center_x - 30, center_y - 30, 60, 60)
        
        # 绘制示例传感器
        # 触觉传感器（绿色）
        painter.setBrush(QBrush(QColor(0, 255, 0)))
        painter.drawEllipse(center_x - 50, center_y, 20, 20)
        
        # 光感传感器（黄色）
        painter.setBrush(QBrush(QColor(255, 255, 0)))
        painter.drawEllipse(center_x + 30, center_y - 40, 20, 20)
        
        # 绘制示例效应器
        # 肌肉效应器（红色）
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawRect(center_x - 40, center_y + 20, 20, 20)
        
        # 纤毛效应器（青色）
        painter.setBrush(QBrush(QColor(0, 255, 255)))
        painter.drawRect(center_x + 20, center_y + 20, 20, 20)
        
        # 绘制连接
        painter.setPen(QPen(QColor(100, 100, 255), 2))
        painter.drawLine(center_x - 30, center_y, center_x - 50, center_y + 10)
        painter.drawLine(center_x, center_y - 30, center_x + 30, center_y - 40)
        painter.drawLine(center_x - 30, center_y + 30, center_x - 40, center_y + 30)
        painter.drawLine(center_x + 30, center_y + 30, center_x + 20, center_y + 30)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = event.pos()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.drag_object = None
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if self.dragging and self.drag_object:
            # 处理拖拽逻辑
            pass


class PropertyPanel(QWidget):
    """属性编辑面板"""
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(250)
        self.setStyleSheet("background-color: #2d2d2d;")
        
        self.layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("属性编辑")
        title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        self.layout.addWidget(title)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #404040;")
        self.layout.addWidget(line)
        
        # 对象类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["生物", "传感器", "效应器", "连接", "记忆基因"])
        self.type_combo.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.layout.addWidget(QLabel("对象类型:"))
        self.layout.addWidget(self.type_combo)
        
        # 名称输入
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("对象名称")
        self.name_edit.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.layout.addWidget(QLabel("名称:"))
        self.layout.addWidget(self.name_edit)
        
        # 数值属性示例
        self.form_layout = QFormLayout()
        
        # X坐标
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-1000, 1000)
        self.x_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.form_layout.addRow("X坐标:", self.x_spin)
        
        # Y坐标
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-1000, 1000)
        self.y_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.form_layout.addRow("Y坐标:", self.y_spin)
        
        # 强度
        self.strength_spin = QDoubleSpinBox()
        self.strength_spin.setRange(0.0, 1.0)
        self.strength_spin.setSingleStep(0.1)
        self.strength_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.form_layout.addRow("强度:", self.strength_spin)
        
        # 权重
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(-1.0, 1.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
        self.form_layout.addRow("权重:", self.weight_spin)
        
        self.layout.addLayout(self.form_layout)
        
        # 空控件填充剩余空间
        self.layout.addStretch()
    
    def update_properties(self, selected_object):
        """更新属性面板内容"""
        # 根据选中对象更新属性
        pass


class ProjectTree(QWidget):
    """项目树面板"""
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(200)
        self.setStyleSheet("background-color: #252526;")
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("项目")
        title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #404040;")
        layout.addWidget(line)
        
        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("生物项目")
        self.tree.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        # 添加示例项目
        project_item = QTreeWidgetItem(self.tree, ["AI生命体项目"])
        
        # 添加生物
        organism_item = QTreeWidgetItem(project_item, ["生物列表"])
        QTreeWidgetItem(organism_item, ["生物1"])
        QTreeWidgetItem(organism_item, ["生物2"])
        
        # 添加模板
        template_item = QTreeWidgetItem(project_item, ["模板库"])
        QTreeWidgetItem(template_item, ["基础生物"])
        QTreeWidgetItem(template_item, ["传感器丰富生物"])
        QTreeWidgetItem(template_item, ["效应器丰富生物"])
        
        # 添加环境
        environment_item = QTreeWidgetItem(project_item, ["环境"])
        QTreeWidgetItem(environment_item, ["默认环境"])
        
        self.tree.expandAll()
        layout.addWidget(self.tree)


class ConsolePanel(QWidget):
    """控制台输出面板"""
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(150)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("控制台")
        title.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #1e1e1e; color: #4ec9b0;")
        layout.addWidget(self.text_edit)
    
    def add_output(self, text):
        """添加输出文本"""
        self.text_edit.append(text)


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
        
        # 创建左侧面板（项目树）
        self.project_tree = ProjectTree()
        self.horizontal_splitter.addWidget(self.project_tree)
        
        # 创建中央编辑区
        self.central_tab = QTabWidget()
        self.central_tab.setStyleSheet("background-color: #252526;")
        
        # 添加编辑画布
        self.canvas = OrganismCanvas()
        self.central_tab.addTab(self.canvas, "生物编辑")
        
        # 添加记忆编辑
        self.memory_edit = QTextEdit()
        self.memory_edit.setPlaceholderText("记忆基因编辑")
        self.memory_edit.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.central_tab.addTab(self.memory_edit, "记忆编辑")
        
        # 添加连接编辑
        self.connection_edit = QTextEdit()
        self.connection_edit.setPlaceholderText("连接编辑")
        self.connection_edit.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.central_tab.addTab(self.connection_edit, "连接编辑")
        
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
        self.status_bar.setStyleSheet("background-color: #252526; color: #ffffff;")
        self.setStatusBar(self.status_bar)
        
        # 初始化状态栏
        self.status_bar.showMessage("就绪")
        self.status_bar.addPermanentWidget(QLabel("模式: 查看"))
        
        # 初始化控制台
        self.console.add_output("AI生命体编辑器已启动")
        self.console.add_output("欢迎使用PyQt6版编辑器")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        menu_bar.setStyleSheet("background-color: #252526; color: #ffffff;")
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        file_menu.addAction("新建", self.new_project, "Ctrl+N")
        file_menu.addAction("打开", self.open_project, "Ctrl+O")
        file_menu.addAction("保存", self.save_project, "Ctrl+S")
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close, "Ctrl+Q")
        menu_bar.addMenu(file_menu)
        
        # 编辑菜单
        edit_menu = QMenu("编辑", self)
        edit_menu.addAction("撤销", self.undo, "Ctrl+Z")
        edit_menu.addAction("重做", self.redo, "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("复制", self.copy, "Ctrl+C")
        edit_menu.addAction("粘贴", self.paste, "Ctrl+V")
        edit_menu.addAction("删除", self.delete, "Del")
        menu_bar.addMenu(edit_menu)
        
        # 视图菜单
        view_menu = QMenu("视图", self)
        view_menu.addAction("显示项目树", self.toggle_project_tree, "Ctrl+1")
        view_menu.addAction("显示属性面板", self.toggle_property_panel, "Ctrl+2")
        view_menu.addAction("显示控制台", self.toggle_console, "Ctrl+3")
        menu_bar.addMenu(view_menu)
        
        # 工具菜单
        tool_menu = QMenu("工具", self)
        tool_menu.addAction("运行模拟", self.run_simulation, "F5")
        tool_menu.addAction("停止模拟", self.stop_simulation, "F6")
        tool_menu.addSeparator()
        tool_menu.addAction("导出生物", self.export_organism)
        tool_menu.addAction("导入生物", self.import_organism)
        menu_bar.addMenu(tool_menu)
        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        help_menu.addAction("使用帮助", self.show_help)
        help_menu.addAction("关于", self.show_about)
        menu_bar.addMenu(help_menu)
        
        self.setMenuBar(menu_bar)
    
    def create_tool_bar(self):
        """创建工具栏"""
        tool_bar = QToolBar("主工具栏")
        tool_bar.setStyleSheet("background-color: #252526; color: #ffffff;")
        
        # 添加工具栏按钮
        tool_bar.addAction("新建", self.new_project, "Ctrl+N")
        tool_bar.addAction("打开", self.open_project, "Ctrl+O")
        tool_bar.addAction("保存", self.save_project, "Ctrl+S")
        tool_bar.addSeparator()
        tool_bar.addAction("撤销", self.undo, "Ctrl+Z")
        tool_bar.addAction("重做", self.redo, "Ctrl+Y")
        tool_bar.addSeparator()
        tool_bar.addAction("运行", self.run_simulation, "F5")
        tool_bar.addAction("停止", self.stop_simulation, "F6")
        tool_bar.addSeparator()
        
        # 添加模式选择
        mode_combo = QComboBox()
        mode_combo.addItems(["查看", "添加传感器", "添加效应器", "连接"])
        mode_combo.setStyleSheet("background-color: #3c3c3c; color: #ffffff;")
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
