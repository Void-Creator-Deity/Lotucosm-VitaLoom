"""记忆编辑器GUI组件"""

import os
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QLineEdit, QGroupBox,
    QFormLayout, QDoubleSpinBox, QSplitter, QFileDialog,
    QMessageBox, QTabWidget, QListWidgetItem
)

from PyQt6.QtCore import Qt, pyqtSignal

from vitalloom.editor.memory_editor import MemoryEditor
from vitalloom.editor.ui.base_editor_widget import BaseEditorWidget


class MemoryEditorWidget(BaseEditorWidget):
    """记忆编辑器GUI界面"""

    # 自定义信号
    memory_edited = pyqtSignal()  # 记忆被编辑时发出信号
    organism_exported = pyqtSignal()  # 生物体被导出时发出信号

    def __init__(self, organism: Optional[Any] = None):
        """初始化记忆编辑器"""
        super().__init__()

        self.organism: Optional[Any] = organism
        self.memory_editor: Optional[MemoryEditor] = None
        self.current_memory: Optional[Any] = None

        # 初始化界面
        self._init_ui()

        # 如果有生物体，初始化记忆编辑器
        if organism:
            self.set_organism(organism)

    def _init_ui(self):
        """初始化界面"""

        # 主布局
        main_layout = QVBoxLayout(self)

        # 使用基类方法创建标题部分
        self._create_title_section("记忆编辑器", main_layout)

        # 生物体信息
        self.organism_info = QLabel("未选择生物体")
        self.organism_info.setStyleSheet("color: #888888; font-size: 12px;")
        main_layout.addWidget(self.organism_info)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板：记忆列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 记忆列表组
        memory_list_group = QGroupBox("记忆列表")
        memory_list_layout = QVBoxLayout(memory_list_group)

        self.memory_list = QListWidget()
        self.memory_list.itemClicked.connect(self._on_memory_selected)  # type: ignore
        memory_list_layout.addWidget(self.memory_list)

        left_layout.addWidget(memory_list_group)

        # 操作按钮组
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)

        self.export_memory_btn = QPushButton("导出记忆")
        self.export_memory_btn.clicked.connect(self._export_memory)  # type: ignore
        action_layout.addWidget(self.export_memory_btn)

        self.import_memory_btn = QPushButton("导入记忆")
        self.import_memory_btn.clicked.connect(self._import_memory)  # type: ignore
        action_layout.addWidget(self.import_memory_btn)

        self.export_organism_btn = QPushButton("导出生物体模板")
        self.export_organism_btn.clicked.connect(self._export_organism)  # type: ignore
        action_layout.addWidget(self.export_organism_btn)

        self.visualize_btn = QPushButton("可视化记忆网络")
        self.visualize_btn.clicked.connect(self._visualize_memory_network)  # type: ignore
        action_layout.addWidget(self.visualize_btn)

        left_layout.addWidget(action_group)

        splitter.addWidget(left_panel)

        # 右侧面板：记忆编辑
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 标签页
        self.tab_widget = QTabWidget()

        # 记忆编辑标签
        self.edit_tab = QWidget()
        self._init_edit_tab()
        self.tab_widget.addTab(self.edit_tab, "记忆编辑")

        # 记忆可视化标签
        self.visualize_tab = QWidget()
        self._init_visualize_tab()
        self.tab_widget.addTab(self.visualize_tab, "记忆可视化")

        right_layout.addWidget(self.tab_widget)

        splitter.addWidget(right_panel)

        # 设置分割器大小
        splitter.setSizes([300, 500])  # type: ignore

        main_layout.addWidget(splitter)

        # 底部按钮
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self._save_memory)  # type: ignore
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._clear_memory)  # type: ignore
        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(btn_layout)

        # 禁用所有按钮，直到选择生物体
        self._disable_buttons()

    def _init_edit_tab(self):
        """初始化编辑标签"""
        edit_layout = QVBoxLayout(self.edit_tab)

        # 情境信息
        situation_group = QGroupBox("情境信息")
        situation_layout = QFormLayout(situation_group)

        self.situation_label = QLabel("情境名称:")
        self.situation_input = QLineEdit()
        situation_layout.addRow(self.situation_label, self.situation_input)

        edit_layout.addWidget(situation_group)

        # 行动模式
        action_group = QGroupBox("行动模式")
        action_layout = QVBoxLayout(action_group)

        self.action_text = QTextEdit()
        self.action_text.setPlaceholderText("输入行动模式 JSON 数据，例如 {\"cilia_1\": 0.7, \"muscle_1\": 0.3}")
        action_layout.addWidget(QLabel("行动模式 (JSON):"))
        action_layout.addWidget(self.action_text)

        edit_layout.addWidget(action_group)

        # 成功率
        success_group = QGroupBox("成功率")
        success_layout = QHBoxLayout(success_group)

        self.success_rate_label = QLabel("成功率:")
        self.success_rate_input = QDoubleSpinBox()
        self.success_rate_input.setRange(0.0, 1.0)
        self.success_rate_input.setSingleStep(0.05)
        self.success_rate_input.setValue(0.8)

        success_layout.addWidget(self.success_rate_label)
        success_layout.addWidget(self.success_rate_input)
        success_layout.addStretch()

        edit_layout.addWidget(success_group)

        edit_layout.addStretch()

    def _init_visualize_tab(self):
        """初始化可视化标签"""

        visualize_layout = QVBoxLayout(self.visualize_tab)

        self.visualize_text = QTextEdit()
        self.visualize_text.setReadOnly(True)
        self.visualize_text.setPlaceholderText("记忆网络可视化将显示在这里")
        visualize_layout.addWidget(self.visualize_text)

    def set_organism(self, organism: Any):
        """设置生物体"""
        self.organism = organism
        self.memory_editor = MemoryEditor(organism)

        # 更新生物体信息
        self.organism_info.setText(f"生物体: {organism.id if hasattr(organism, 'id') else '未知'}")

        # 加载记忆列表
        self._load_memory_list()

        # 启用按钮
        self._enable_buttons()

    def _load_memory_list(self):
        """加载记忆列表"""

        self.memory_list.clear()

        if not self.memory_editor:
            return

        memories = []
        if self.memory_editor:
            memories = self.memory_editor.list_memories()

        for i, memory in enumerate(memories):
            # 使用情境作为记忆标识
            situation = getattr(memory, 'situation', f"记忆_{i+1}")
            success_rate = getattr(memory, 'success_rate', 0.0)

            # 显示记忆信息
            list_item = f"{situation} - 成功率: {success_rate:.2f}"
            self.memory_list.addItem(list_item)

            # 存储记忆对象到item的data中
            item = self.memory_list.item(i)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, memory)

    def _on_memory_selected(self, item: QListWidgetItem):
        """选择记忆时的处理"""
        memory = item.data(Qt.ItemDataRole.UserRole)

        if memory:
            self.current_memory = memory
            self._load_memory_data(memory)

    def _load_memory_data(self, memory: Any):
        """加载记忆数据到编辑界面"""

        # 加载情境
        situation = getattr(memory, 'situation', '')
        self.situation_input.setText(situation)

        # 加载行动模式
        action_pattern = getattr(memory, 'action_pattern', {})
        import json
        try:
            action_json = json.dumps(action_pattern, indent=2, ensure_ascii=False)
            self.action_text.setText(action_json)
        except Exception:
            self.action_text.setText(str(action_pattern))

        # 加载成功率
        success_rate = getattr(memory, 'success_rate', 0.0)
        self.success_rate_input.setValue(success_rate)

    def _save_memory(self):
        """保存记忆修改"""
        if not self.current_memory:
            QMessageBox.warning(self, "保存失败", "请先选择一个记忆进行编辑")
            return

        # 获取编辑后的数据
        new_situation = self.situation_input.text()
        action_text = self.action_text.toPlainText()
        new_success_rate = self.success_rate_input.value()

        # 解析行动模式
        import json
        try:
            new_action_pattern = json.loads(action_text)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "保存失败", "行动模式必须是有效的 JSON 格式!")
            return

        # 编辑记忆
        try:
            # 使用情境作为记忆ID
            memory_id = getattr(self.current_memory, 'situation', '')
            result = False
            if self.memory_editor:
                result = self.memory_editor.edit_memory(
                    memory_id=memory_id,
                    situation=new_situation,
                    action_pattern=new_action_pattern,
                    success_rate=new_success_rate
                )

            if result:
                QMessageBox.information(self, "保存成功", "记忆修改已保存")
                self._load_memory_list()  # 刷新记忆列表
                self.memory_edited.emit()  # 发出记忆被编辑信号
            else:
                QMessageBox.warning(self, "保存失败", "记忆修改保存失败")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存过程中发生错误: {str(e)}")

    def _export_memory(self):
        """导出记忆"""

        if not self.current_memory:
            QMessageBox.warning(self, "导出失败", "请先选择一个记忆进行导出")
            return

        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(self, "导出记忆", data_dir, "记忆文件 (*.json);;所有文件(*.*)")
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                memory_id = getattr(self.current_memory, 'situation', '')
                result = self.memory_editor.export_memory(memory_id, file_path)

            if result:
                QMessageBox.information(self, "导出成功", f"记忆已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "记忆导出失败")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误: {str(e)}")

    def _import_memory(self):
        """导入记忆"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getOpenFileName(self, "导入记忆", data_dir, "记忆文件 (*.json);;所有文件(*.*)")
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                result = self.memory_editor.import_memory(file_path)

            if result:
                QMessageBox.information(self, "导入成功", "记忆已导入")
                self._load_memory_list()  # 刷新记忆列表
                self.memory_edited.emit()  # 发出记忆被编辑信号
            else:
                QMessageBox.warning(self, "导入失败", "记忆导入失败")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"导入过程中发生错误: {str(e)}")

    def _export_organism(self):
        """导出生物体模板"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(self, "导出生物体模板", data_dir, "生物体模板(*.json);;所有文件(*.*)")
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                result = self.memory_editor.export_organism_template(file_path)

            if result:
                QMessageBox.information(self, "导出成功", f"生物体模板已导出到: {file_path}")
                self.organism_exported.emit()  # 发出生物体被导出信号
            else:
                QMessageBox.warning(self, "导出失败", "生物体模板导出失败")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误: {str(e)}")

    def _visualize_memory_network(self):
        """可视化记忆网络"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(self, "保存记忆网络可视化", data_dir, "文本文件 (*.txt);;所有文件(*.*)")

        try:
            if file_path:
                result = False
                if self.memory_editor:
                    result = self.memory_editor.visualize_memory_network(file_path)

                if result:
                    QMessageBox.information(self, "可视化成功", f"记忆网络已保存到: {file_path}")
                else:
                    QMessageBox.warning(self, "可视化失败", "记忆网络可视化失败")
            else:
                # 在界面上显示可视化结果
                self._display_memory_visualization()
        except Exception as e:
            QMessageBox.critical(self, "可视化失败", f"可视化过程中发生错误: {str(e)}")

    def _display_memory_visualization(self):
        """在界面上显示记忆可视化结果"""

        if not self.memory_editor:
            return

        memories = self.memory_editor.list_memories()

        if not memories:
            self.visualize_text.setText("没有记忆可以可视化")
            return

        # 构建可视化文本
        visualization = "=== 记忆关联网络 ===\n\n"

        for i, memory in enumerate(memories):
            situation = getattr(memory, 'situation', f"记忆_{i+1}")
            action_pattern = getattr(memory, 'action_pattern', {})
            success_rate = getattr(memory, 'success_rate', 0.0)

            visualization += f"记忆 {i+1}: {situation}\n"
            visualization += f"  情境: {situation}\n"
            visualization += f"  行动模式: {str(action_pattern)}\n"
            visualization += f"  成功率: {success_rate:.2f}\n\n"

        self.visualize_text.setText(visualization)

    def _clear_memory(self):
        """清空编辑界面"""
        self.situation_input.clear()
        self.action_text.clear()
        self.success_rate_input.setValue(0.8)
        self.current_memory = None

    def _enable_buttons(self):
        """启用所有按钮"""

        self.export_memory_btn.setEnabled(True)
        self.import_memory_btn.setEnabled(True)
        self.export_organism_btn.setEnabled(True)
        self.visualize_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def _disable_buttons(self):
        """禁用所有按钮"""
        self.export_memory_btn.setEnabled(False)
        self.import_memory_btn.setEnabled(False)
        self.export_organism_btn.setEnabled(False)
        self.visualize_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
