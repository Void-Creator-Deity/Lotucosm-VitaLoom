"""记忆基因编辑 Dock：MemoryGene 列表与属性表单。

排错: 与 Lotucosm memory 模块字段不一致时见 commands 中 Memory*Command。
"""

import os
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QLineEdit, QGroupBox,
    QFormLayout, QDoubleSpinBox, QSplitter, QFileDialog,
    QMessageBox, QTabWidget, QListWidgetItem
)

from PyQt6.QtCore import Qt, pyqtSignal

from core.VitaLoom.memory_editor import MemoryEditor
from core.VitaLoom.ui.base_editor_widget import BaseEditorWidget


class MemoryEditorWidget(BaseEditorWidget):
    """职责: 编辑选中实体的记忆条目并走 CommandStack 撤销。"""
    """记忆编辑器GUI界面"""

    # 自定义信号
    memory_edited = pyqtSignal()  # 记忆被编辑时发出信号
    organism_exported = pyqtSignal()  # 生物体被导出时发出信号

    def __init__(self, organism: Optional[Any] = None):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        super().__init__()

        self.organism: Optional[Any] = organism
        self.memory_editor: Optional[MemoryEditor] = None
        self.current_memory: Optional[Any] = None

        # 初始化界面
        self._init_ui()

        # 如果有生物体，初始化记忆编辑器
        if organism:
            self.set_organism(organism)

    def _t(self, key: str, default: str = "") -> str:
        # BaseEditorWidget 可能未提供统一 i18n，这里直接从 editor_context 取
        ctx = getattr(self, "editor_context", None)
        if ctx is None:
            try:
                from core.VitaLoom.core.editor_context import get_editor_context
                ctx = get_editor_context()
            except Exception:
                ctx = None
        tr_fn = getattr(ctx, "i18n_tr", None) if ctx is not None else None
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _init_ui(self):
        """初始化界面"""

        # 主布局
        main_layout = QVBoxLayout(self)

        # 使用基类方法创建标题部分
        self._create_title_section(self._t("memory_editor.title", "记忆编辑器"), main_layout)

        # 生物体信息
        self.organism_info = QLabel(self._t("memory_editor.no_organism", "未选择生物体"))
        self.organism_info.setStyleSheet("color: #888888; font-size: 12px;")
        main_layout.addWidget(self.organism_info)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板：记忆列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 记忆列表组
        memory_list_group = QGroupBox(self._t("memory_editor.group.memory_list", "记忆列表"))
        memory_list_layout = QVBoxLayout(memory_list_group)

        self.memory_list = QListWidget()
        self.memory_list.itemClicked.connect(self._on_memory_selected)  # type: ignore
        memory_list_layout.addWidget(self.memory_list)

        left_layout.addWidget(memory_list_group)

        # 操作按钮组
        action_group = QGroupBox(self._t("memory_editor.group.actions", "操作"))
        action_layout = QVBoxLayout(action_group)

        self.export_memory_btn = QPushButton(self._t("memory_editor.action.export_memory", "导出记忆"))
        self.export_memory_btn.clicked.connect(self._export_memory)  # type: ignore
        action_layout.addWidget(self.export_memory_btn)

        self.import_memory_btn = QPushButton(self._t("memory_editor.action.import_memory", "导入记忆"))
        self.import_memory_btn.clicked.connect(self._import_memory)  # type: ignore
        action_layout.addWidget(self.import_memory_btn)

        self.export_organism_btn = QPushButton(self._t("memory_editor.action.export_organism", "导出生物体模板"))
        self.export_organism_btn.clicked.connect(self._export_organism)  # type: ignore
        action_layout.addWidget(self.export_organism_btn)

        self.visualize_btn = QPushButton(self._t("memory_editor.action.visualize", "可视化记忆网络"))
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
        self.tab_widget.addTab(self.edit_tab, self._t("memory_editor.tab.edit", "记忆编辑"))

        # 记忆可视化标签
        self.visualize_tab = QWidget()
        self._init_visualize_tab()
        self.tab_widget.addTab(self.visualize_tab, self._t("memory_editor.tab.visualize", "记忆可视化"))

        right_layout.addWidget(self.tab_widget)

        splitter.addWidget(right_panel)

        # 设置分割器大小
        splitter.setSizes([300, 500])  # type: ignore

        main_layout.addWidget(splitter)

        # 底部按钮
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton(self._t("memory_editor.action.save", "保存修改"))
        self.save_btn.clicked.connect(self._save_memory)  # type: ignore
        btn_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton(self._t("memory_editor.action.clear", "清空"))
        self.clear_btn.clicked.connect(self._clear_memory)  # type: ignore
        btn_layout.addWidget(self.clear_btn)

        main_layout.addLayout(btn_layout)

        # 禁用所有按钮，直到选择生物体
        self._disable_buttons()

    def _init_edit_tab(self):
        """初始化编辑标签"""
        edit_layout = QVBoxLayout(self.edit_tab)

        # 情境信息
        situation_group = QGroupBox(self._t("memory_editor.group.situation", "情境信息"))
        situation_layout = QFormLayout(situation_group)

        self.situation_label = QLabel(self._t("memory_editor.field.situation", "情境名称:"))
        self.situation_input = QLineEdit()
        situation_layout.addRow(self.situation_label, self.situation_input)

        edit_layout.addWidget(situation_group)

        # 行动模式
        action_group = QGroupBox(self._t("memory_editor.group.action_pattern", "行动模式"))
        action_layout = QVBoxLayout(action_group)

        self.action_text = QTextEdit()
        self.action_text.setPlaceholderText(self._t(
            "memory_editor.placeholder.action_json",
            "输入行动模式 JSON 数据，例如 {\"cilia_1\": 0.7, \"muscle_1\": 0.3}",
        ))
        action_layout.addWidget(QLabel(self._t("memory_editor.field.action_json", "行动模式 (JSON):")))
        action_layout.addWidget(self.action_text)

        edit_layout.addWidget(action_group)

        # 成功率
        success_group = QGroupBox(self._t("memory_editor.group.success_rate", "成功率"))
        success_layout = QHBoxLayout(success_group)

        self.success_rate_label = QLabel(self._t("memory_editor.field.success_rate", "成功率:"))
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
        self.visualize_text.setPlaceholderText(self._t("memory_editor.placeholder.visualize", "记忆网络可视化将显示在这里"))
        visualize_layout.addWidget(self.visualize_text)

    def set_organism(self, organism: Any):
        """设置生物体。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.organism = organism
        self.memory_editor = MemoryEditor(organism)

        # 更新生物体信息
        self.organism_info.setText(
            self._t("memory_editor.organism_info", "生物体: {id}").format(
                id=(organism.id if hasattr(organism, "id") else self._t("inspector.unknown", "未知"))
            )
        )

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
            list_item = self._t(
                "memory_editor.list.item",
                "{situation} - 成功率: {success_rate:.2f}",
            ).format(situation=situation, success_rate=success_rate)
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
            QMessageBox.warning(
                self,
                self._t("memory_editor.dialog.save_failed.title", "保存失败"),
                self._t("memory_editor.dialog.save_failed.no_selection", "请先选择一个记忆进行编辑"),
            )
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
            QMessageBox.warning(
                self,
                self._t("memory_editor.dialog.save_failed.title", "保存失败"),
                self._t("memory_editor.dialog.save_failed.invalid_json", "行动模式必须是有效的 JSON 格式!"),
            )
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
                QMessageBox.information(
                    self,
                    self._t("memory_editor.dialog.save_ok.title", "保存成功"),
                    self._t("memory_editor.dialog.save_ok.content", "记忆修改已保存"),
                )
                self._load_memory_list()  # 刷新记忆列表
                self.memory_edited.emit()  # 发出记忆被编辑信号
            else:
                QMessageBox.warning(
                    self,
                    self._t("memory_editor.dialog.save_failed.title", "保存失败"),
                    self._t("memory_editor.dialog.save_failed.content", "记忆修改保存失败"),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("memory_editor.dialog.save_failed.title", "保存失败"),
                self._t("memory_editor.dialog.save_failed.error", "保存过程中发生错误: {error}").format(error=str(e)),
            )

    def _export_memory(self):
        """导出记忆"""

        if not self.current_memory:
            QMessageBox.warning(
                self,
                self._t("memory_editor.dialog.export_failed.title", "导出失败"),
                self._t("memory_editor.dialog.export_failed.no_selection", "请先选择一个记忆进行导出"),
            )
            return

        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("memory_editor.dialog.export_memory.title", "导出记忆"),
            data_dir,
            self._t("memory_editor.dialog.export_memory.filter", "记忆文件 (*.json);;所有文件(*.*)"),
        )
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                memory_id = getattr(self.current_memory, 'situation', '')
                result = self.memory_editor.export_memory(memory_id, file_path)

            if result:
                QMessageBox.information(
                    self,
                    self._t("memory_editor.dialog.export_ok.title", "导出成功"),
                    self._t("memory_editor.dialog.export_ok.content", "记忆已导出到: {path}").format(path=file_path),
                )
            else:
                QMessageBox.warning(
                    self,
                    self._t("memory_editor.dialog.export_failed.title", "导出失败"),
                    self._t("memory_editor.dialog.export_failed.content", "记忆导出失败"),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("memory_editor.dialog.export_failed.title", "导出失败"),
                self._t("memory_editor.dialog.export_failed.error", "导出过程中发生错误: {error}").format(error=str(e)),
            )

    def _import_memory(self):
        """导入记忆"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("memory_editor.dialog.import_memory.title", "导入记忆"),
            data_dir,
            self._t("memory_editor.dialog.import_memory.filter", "记忆文件 (*.json);;所有文件(*.*)"),
        )
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                result = self.memory_editor.import_memory(file_path)

            if result:
                QMessageBox.information(
                    self,
                    self._t("memory_editor.dialog.import_ok.title", "导入成功"),
                    self._t("memory_editor.dialog.import_ok.content", "记忆已导入"),
                )
                self._load_memory_list()  # 刷新记忆列表
                self.memory_edited.emit()  # 发出记忆被编辑信号
            else:
                QMessageBox.warning(
                    self,
                    self._t("memory_editor.dialog.import_failed.title", "导入失败"),
                    self._t("memory_editor.dialog.import_failed.content", "记忆导入失败"),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("memory_editor.dialog.import_failed.title", "导入失败"),
                self._t("memory_editor.dialog.import_failed.error", "导入过程中发生错误: {error}").format(error=str(e)),
            )

    def _export_organism(self):
        """导出生物体模板"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("memory_editor.dialog.export_organism.title", "导出生物体模板"),
            data_dir,
            self._t("memory_editor.dialog.export_organism.filter", "生物体模板(*.json);;所有文件(*.*)"),
        )
        if not file_path:
            return

        try:
            result = False
            if self.memory_editor:
                result = self.memory_editor.export_organism_template(file_path)

            if result:
                QMessageBox.information(
                    self,
                    self._t("memory_editor.dialog.export_ok.title", "导出成功"),
                    self._t("memory_editor.dialog.export_organism.ok", "生物体模板已导出到: {path}").format(path=file_path),
                )
                self.organism_exported.emit()  # 发出生物体被导出信号
            else:
                QMessageBox.warning(
                    self,
                    self._t("memory_editor.dialog.export_failed.title", "导出失败"),
                    self._t("memory_editor.dialog.export_organism.failed", "生物体模板导出失败"),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("memory_editor.dialog.export_failed.title", "导出失败"),
                self._t("memory_editor.dialog.export_failed.error", "导出过程中发生错误: {error}").format(error=str(e)),
            )

    def _visualize_memory_network(self):
        """可视化记忆网络"""
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 打开文件对话框，默认路径为data目录
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("memory_editor.dialog.visualize_save.title", "保存记忆网络可视化"),
            data_dir,
            self._t("memory_editor.dialog.visualize_save.filter", "文本文件 (*.txt);;所有文件(*.*)"),
        )

        try:
            if file_path:
                result = False
                if self.memory_editor:
                    result = self.memory_editor.visualize_memory_network(file_path)

                if result:
                    QMessageBox.information(
                        self,
                        self._t("memory_editor.dialog.visualize_ok.title", "可视化成功"),
                        self._t("memory_editor.dialog.visualize_ok.content", "记忆网络已保存到: {path}").format(path=file_path),
                    )
                else:
                    QMessageBox.warning(
                        self,
                        self._t("memory_editor.dialog.visualize_failed.title", "可视化失败"),
                        self._t("memory_editor.dialog.visualize_failed.content", "记忆网络可视化失败"),
                    )
            else:
                # 在界面上显示可视化结果
                self._display_memory_visualization()
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("memory_editor.dialog.visualize_failed.title", "可视化失败"),
                self._t("memory_editor.dialog.visualize_failed.error", "可视化过程中发生错误: {error}").format(error=str(e)),
            )

    def _display_memory_visualization(self):
        """在界面上显示记忆可视化结果"""

        if not self.memory_editor:
            return

        memories = self.memory_editor.list_memories()

        if not memories:
            self.visualize_text.setText(self._t("memory_editor.visualize.empty", "没有记忆可以可视化"))
            return

        # 构建可视化文本
        visualization = self._t("memory_editor.visualize.header", "=== 记忆关联网络 ===\n\n")

        for i, memory in enumerate(memories):
            situation = getattr(memory, 'situation', f"记忆_{i+1}")
            action_pattern = getattr(memory, 'action_pattern', {})
            success_rate = getattr(memory, 'success_rate', 0.0)

            visualization += self._t(
                "memory_editor.visualize.item_title",
                "记忆 {index}: {situation}\n",
            ).format(index=i + 1, situation=situation)
            visualization += self._t(
                "memory_editor.visualize.situation_line",
                "  情境: {situation}\n",
            ).format(situation=situation)
            visualization += self._t(
                "memory_editor.visualize.action_pattern_line",
                "  行动模式: {pattern}\n",
            ).format(pattern=str(action_pattern))
            visualization += self._t(
                "memory_editor.visualize.success_rate_line",
                "  成功率: {success_rate:.2f}\n\n",
            ).format(success_rate=success_rate)

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
