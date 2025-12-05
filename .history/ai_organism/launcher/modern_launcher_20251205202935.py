#!/usr/bin/env python3
"""
AI生命体模拟系统 - GUI启动器

融合了三个主要功能：
1. 环境存档管理（选择、新建、编辑）
2. 运行继承算法模拟器
3. 运行AI生命体编辑器

基于PyQt6实现，提供用户界面
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QTextEdit,
    QInputDialog, QMessageBox, QMenu, QFileDialog, QSplitter,
    QFormLayout, QLineEdit, QGroupBox, QToolButton, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction

from ai_organism.environment.archive_manager import EnvironmentArchiveManager

class AIOrganismLauncher(QMainWindow):
    """GUI启动器"""
    
    def __init__(self):
        """初始化启动器"""
        super().__init__()
        self.archive_manager: EnvironmentArchiveManager = EnvironmentArchiveManager()
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("AI生命体模拟系统")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(800, 500)
        
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.setFont(font)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部标题
        title_label = QLabel("AI生命体模拟系统")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        main_layout.addWidget(title_label)
        
        # 主要功能区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(10)
        main_layout.addWidget(splitter)
        
        # 左侧：环境存档列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 环境存档标题
        archive_title = QLabel("环境存档管理")
        archive_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        archive_title.setStyleSheet("color: #3498db; margin-bottom: 10px;")
        left_layout.addWidget(archive_title)
        
        # 存档列表
        self.archive_list = QListWidget()
        self.archive_list.setStyleSheet(
            "QListWidget { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; }"
            "QListWidget::item { padding: 8px; border-radius: 3px; }"
            "QListWidget::item:hover { background-color: #e8f4f8; }"
            "QListWidget::item:selected { background-color: #3498db; color: white; }"
        )
        left_layout.addWidget(self.archive_list)
        
        # 存档列表上下文菜单
        self.archive_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.archive_list.customContextMenuRequested.connect(self.show_archive_context_menu)
        
        # 存档操作按钮组
        archive_buttons = QHBoxLayout()
        
        self.new_archive_btn = QPushButton("新建环境")
        self.new_archive_btn.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; border: none; padding: 8px 15px; border-radius: 5px; } "
            "QPushButton:hover { background-color: #27ae60; }"
        )
        self.new_archive_btn.clicked.connect(self.create_new_environment)
        archive_buttons.addWidget(self.new_archive_btn)
        
        self.edit_archive_btn = QPushButton("编辑环境")
        self.edit_archive_btn.setStyleSheet(
            "QPushButton { background-color: #f39c12; color: white; border: none; padding: 8px 15px; border-radius: 5px; } "
            "QPushButton:hover { background-color: #e67e22; }"
        )
        self.edit_archive_btn.clicked.connect(self.edit_environment)
        archive_buttons.addWidget(self.edit_archive_btn)
        
        self.delete_archive_btn = QPushButton("删除环境")
        self.delete_archive_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 5px; } "
            "QPushButton:hover { background-color: #c0392b; }"
        )
        self.delete_archive_btn.clicked.connect(self.delete_environment)
        archive_buttons.addWidget(self.delete_archive_btn)
        
        left_layout.addLayout(archive_buttons)
        
        # 存档描述
        self.archive_description = QTextEdit()
        self.archive_description.setPlaceholderText("选中环境存档查看描述...")
        self.archive_description.setReadOnly(True)
        self.archive_description.setStyleSheet(
            "border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; background-color: #f8f9fa;"
        )
        self.archive_description.setMaximumHeight(100)
        left_layout.addWidget(self.archive_description)
        
        # 将左侧部件添加到分割器
        splitter.addWidget(left_widget)
        
        # 右侧：功能选择
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 功能标题
        function_title = QLabel("主要功能")
        function_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        function_title.setStyleSheet("color: #3498db; margin-bottom: 20px;")
        right_layout.addWidget(function_title)
        
        # 功能按钮组
        function_buttons_layout = QVBoxLayout()
        function_buttons_layout.setSpacing(15)
        
        # 运行模拟按钮
        self.run_simulation_btn = QPushButton("运行继承算法模拟器")
        self.run_simulation_btn.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; border: none; padding: 15px; border-radius: 8px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #2980b9; }"
            "QPushButton:disabled { background-color: #bdc3c7; color: #ecf0f1; }"
        )
        self.run_simulation_btn.clicked.connect(self.run_tool_simulation)
        self.run_simulation_btn.setFixedHeight(60)
        function_buttons_layout.addWidget(self.run_simulation_btn)
        
        # 运行编辑器按钮
        self.run_editor_btn = QPushButton("运行AI生命体编辑器")
        self.run_editor_btn.setStyleSheet(
            "QPushButton { background-color: #9b59b6; color: white; border: none; padding: 15px; border-radius: 8px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #8e44ad; }"
        )
        self.run_editor_btn.clicked.connect(self.run_organism_editor)
        self.run_editor_btn.setFixedHeight(60)
        function_buttons_layout.addWidget(self.run_editor_btn)
        
        # 退出按钮
        self.exit_btn = QPushButton("退出系统")
        self.exit_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; border: none; padding: 15px; border-radius: 8px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        self.exit_btn.clicked.connect(self.close)
        self.exit_btn.setFixedHeight(60)
        function_buttons_layout.addWidget(self.exit_btn)
        
        # 功能说明
        info_group = QGroupBox("功能说明")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setStyleSheet("background-color: #f8f9fa; border: none; padding: 10px;")
        info_text.setHtml(
            "<ul> <li><strong>环境存档管理</strong>: 选择、新建、编辑和删除环境存档</li> "
            "<li><strong>继承算法模拟器</strong>: 模拟AI生命体通过工具学习和记忆遗传的进化过程</li> "
            "<li><strong>AI生命体编辑器</strong>: 基于PyQt6的可视化编辑器，支持创建和编辑AI生命体的结构和属性</li> </ul>"
        )
        info_text.setMaximumHeight(120)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        
        # 将功能布局添加到右侧布局
        right_layout.addLayout(function_buttons_layout)
        right_layout.addStretch()
        right_layout.addWidget(info_group)
        
        # 将右侧部件添加到分割器
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 500])
        
        # 加载存档列表
        self.load_archives()
        
        # 连接信号
        self.archive_list.itemSelectionChanged.connect(self.on_archive_selected)
    
    def load_archives(self) -> None:
        """加载环境存档列表"""
        self.archive_list.clear()
        
        # 获取存档列表
        archives = self.archive_manager.list_archives()
        
        if not archives:
            # 添加空提示项
            empty_item = QListWidgetItem("暂无环境存档")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setForeground(Qt.GlobalColor.gray)
            self.archive_list.addItem(empty_item)
            self.run_simulation_btn.setEnabled(False)
        else:
            # 添加存档项
            for archive in archives:
                item = QListWidgetItem(f"{archive['name']}")
                item.setData(Qt.ItemDataRole.UserRole, archive)
                self.archive_list.addItem(item)
            self.run_simulation_btn.setEnabled(True)
    
    def on_archive_selected(self) -> None:
        """当选中存档时更新描述"""
        selected_items = self.archive_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            archive_data = item.data(Qt.ItemDataRole.UserRole)
            if archive_data:
                self.archive_description.setPlainText(f"名称: {archive_data['name']}\n\n描述: {archive_data['description']}")
                self.run_simulation_btn.setEnabled(True)
    
    def show_archive_context_menu(self, pos) -> None:
        """显示存档列表上下文菜单"""
        item = self.archive_list.itemAt(pos)
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        menu = QMenu()
        
        # 运行模拟
        run_action = QAction("运行模拟")
        run_action.triggered.connect(self.run_tool_simulation)
        menu.addAction(run_action)
        
        # 编辑存档
        edit_action = QAction("编辑存档")
        edit_action.triggered.connect(self.edit_environment)
        menu.addAction(edit_action)
        
        # 删除存档
        delete_action = QAction("删除存档")
        delete_action.triggered.connect(self.delete_environment)
        delete_action.setIcon(QIcon.fromTheme("edit-delete"))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.archive_list.mapToGlobal(pos))
    
    def create_new_environment(self) -> None:
        """创建新环境存档"""
        # 获取新环境名称
        name, ok = QInputDialog.getText(self, "新建环境", "请输入环境名称:")
        if not ok or not name.strip():
            return
        
        # 获取环境描述
        description, ok = QInputDialog.getMultiLineText(self, "新建环境", "请输入环境描述:")
        if not ok:
            return
        
        try:
            # 创建新环境
            new_env = self.archive_manager.create_new_environment()
            
            # 添加一些默认内容
            new_env.add_food((100, 100))
            new_env.add_food((300, 200))
            new_env.add_food((500, 300))
            new_env.add_light_source((200, 150), 1.0)
            new_env.add_obstacle((400, 250), 30)
            
            # 保存环境
            self.archive_manager.save_environment(new_env, name.strip(), description.strip())
            
            # 重新加载存档列表
            self.load_archives()
            
            QMessageBox.information(self, "成功", f"环境 '{name}' 创建成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建环境失败: {str(e)}")
    
    def edit_environment(self) -> None:
        """编辑环境存档"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个环境存档！")
            return
        
        item = selected_items[0]
        archive_data = item.data(Qt.ItemDataRole.UserRole)
        if not archive_data:
            return
        
        QMessageBox.information(self, "提示", f"环境编辑功能开发中，敬请期待！\n\n当前选中的环境: {archive_data['name']}")
    
    def delete_environment(self) -> None:
        """删除环境存档"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个环境存档！")
            return
        
        item = selected_items[0]
        archive_data = item.data(Qt.ItemDataRole.UserRole)
        if not archive_data:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除环境 '{archive_data['name']}' 吗？\n\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除存档
            success = self.archive_manager.delete_archive(archive_data['file'])
            if success:
                QMessageBox.information(self, "成功", f"环境 '{archive_data['name']}' 删除成功！")
                self.load_archives()
            else:
                QMessageBox.critical(self, "错误", f"删除环境 '{archive_data['name']}' 失败！")
    
    def run_tool_simulation(self) -> None:
        """运行继承算法模拟器"""
        selected_items = self.archive_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个环境存档！")
            return
        
        item = selected_items[0]
        archive_data = item.data(Qt.ItemDataRole.UserRole)
        if not archive_data:
            return
        
        # 获取选中的存档文件名
        archive_file = archive_data['file']
        
        try:
            # 使用subprocess运行模拟器，避免Qt事件循环与pygame事件循环冲突
            import subprocess
            import sys
            
            # 构建命令行参数
            cmd = [
                sys.executable,  # 当前Python解释器
                '-c',  # 执行命令行代码
                'from ai_organism.simulation import inheritance_simulation; inheritance_simulation.main()'
            ]
            
            # 启动子进程，不等待其结束
            subprocess.Popen(cmd, shell=False)
            
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法导入subprocess模块: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动模拟器失败: {str(e)}")
    
    def run_organism_editor(self) -> None:
        """运行AI生命体编辑器"""
        try:
            # 使用subprocess运行编辑器，避免事件循环冲突
            import subprocess
            import sys
            
            # 构建命令行参数
            cmd = [
                sys.executable,  # 当前Python解释器
                '-c',  # 执行命令行代码
                'from ai_organism.editor.ui import pyqt_organism_editor; pyqt_organism_editor.main()'
            ]
            
            # 启动子进程，不等待其结束
            subprocess.Popen(cmd, shell=False)
            
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法导入subprocess模块: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动编辑器失败: {str(e)}")
    
    def closeEvent(self, event) -> None:
        """关闭窗口时的事件处理"""
        reply = QMessageBox.question(
            self, "确认退出", "确定要退出AI生命体模拟系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main() -> None:
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示启动器
    launcher = ModernLauncher()
    launcher.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

