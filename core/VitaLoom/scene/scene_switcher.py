# -*- coding: utf-8 -*-
"""场景切换 UI：列表选择与 SceneManager.load_scene 联动。

排错: 见 README「场景重载」。
"""

import os
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.VitaLoom.scene.scene_manager import get_scene_manager
from core.VitaLoom.core.editor_context import get_editor_context


class SceneSwitcher(QWidget):
    """职责: 展示项目内 .pond 列表并触发加载。
    时机: 嵌入标准 UI 或项目工作流插件。
    不变量: 依赖 ProjectManager 当前路径。
    排错: 列表空 → get_scenes_in_project 路径。
    """
    """场景切换器 - 场景切换UI组件"""
    
    scene_changed = pyqtSignal(str)  # 场景路径
    
    def __init__(self, parent=None):
        """SceneSwitcher.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__(parent)
        self.scene_manager = get_scene_manager()
        self.editor_context = get_editor_context()
        
        self._init_ui()
        self._connect_signals()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 场景标签
        label = QLabel(self._t("scene_switcher.label.scene", "场景:"))
        layout.addWidget(label)
        
        # 场景下拉框
        self.scene_combo = QComboBox()
        self.scene_combo.setMinimumWidth(200)
        self.scene_combo.currentTextChanged.connect(self._on_scene_selected)  # type: ignore
        layout.addWidget(self.scene_combo)
        
        # 新建场景按钮
        new_btn = QPushButton("+")
        new_btn.setMaximumWidth(30)
        new_btn.setToolTip(self._t("scene_switcher.action.new_scene", "新建场景"))
        new_btn.clicked.connect(self._create_new_scene)  # type: ignore
        layout.addWidget(new_btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _connect_signals(self):
        """连接信号"""
        self.scene_manager.scene_changed.connect(self._refresh_scene_list)  # type: ignore
        self.scene_manager.scene_loaded.connect(self._refresh_scene_list)  # type: ignore
        self.editor_context.project_changed.connect(self._refresh_scene_list)  # type: ignore
        self.editor_context.event_bus.subscribe("project_opened", self._on_project_opened_bus)

    def _on_project_opened_bus(self, data) -> None:
        """event_bus 项目打开：刷新下拉并选中 active_scene。"""
        self._refresh_scene_list()
    
    def _refresh_scene_list(self):
        """刷新场景列表"""
        self.scene_combo.clear()
        
        project_path = self.editor_context.current_project_path
        if not project_path:
            return
        
        scenes = self.scene_manager.get_scenes_in_project(project_path)
        for scene_path in scenes:
            scene_info = self.scene_manager.get_scene_info(scene_path)
            if scene_info:
                scene_name = scene_info.get('name', os.path.basename(scene_path))
                self.scene_combo.addItem(scene_name, scene_path)
        
        # 设置当前场景
        current_scene = self.scene_manager.get_current_scene_path()
        if current_scene:
            index = self.scene_combo.findData(current_scene)
            if index >= 0:
                self.scene_combo.setCurrentIndex(index)
    
    def _on_scene_selected(self, text: str):
        """场景选择处理"""
        scene_path = self.scene_combo.currentData()
        if scene_path:
            self.scene_manager.load_scene(scene_path)
            self.scene_changed.emit(scene_path)
    
    def _create_new_scene(self):
        """创建新场景"""
        from core.VitaLoom.scene.scene_wizard import SceneWizard
        
        wizard = SceneWizard(self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            scene_path = wizard.get_created_scene_path()
            if scene_path:
                self._refresh_scene_list()
                # 切换到新场景
                index = self.scene_combo.findData(scene_path)
                if index >= 0:
                    self.scene_combo.setCurrentIndex(index)


class SceneWizard(QDialog):
    """职责: 新建 .pond 对话框，调用 SceneManager.create_scene。"""
    """场景创建向导"""
    
    def __init__(self, parent=None):
        """SceneWizard.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        super().__init__(parent)
        self.scene_manager = get_scene_manager()
        self.editor_context = get_editor_context()
        self.setWindowTitle(self._t("scene_wizard.title", "新建场景"))
        self.setMinimumWidth(400)
        self.setModal(True)
        self.created_scene_path: Optional[str] = None
        
        self._init_ui()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
    
    def _init_ui(self):
        """初始化UI"""
        from PyQt6.QtWidgets import QFormLayout, QLineEdit
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        
        # 场景名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self._t("scene_wizard.placeholder.name", "输入场景名称"))
        form_layout.addRow(self._t("scene_wizard.field.name", "场景名称:"), self.name_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._create_scene)  # type: ignore
        button_box.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _create_scene(self):
        """创建场景"""
        scene_name = self.name_edit.text().strip()
        if not scene_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                self._t("dialog.error.title", "错误"),
                self._t("scene_wizard.error.no_name", "请输入场景名称"),
            )
            return
        
        project_path = self.editor_context.current_project_path
        if not project_path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                self._t("dialog.error.title", "错误"),
                self._t("scene_wizard.error.no_project", "请先打开或创建项目"),
            )
            return
        
        scene_path = self.scene_manager.create_scene(scene_name, project_path)
        if scene_path:
            self.created_scene_path = scene_path
            self.accept()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                self._t("dialog.error.title", "错误"),
                self._t("scene_wizard.error.create_failed", "场景创建失败，场景可能已存在"),
            )
    
    def get_created_scene_path(self) -> Optional[str]:
        """获取创建的场景路径。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.created_scene_path
