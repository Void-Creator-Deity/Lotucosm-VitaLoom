# -*- coding: utf-8 -*-
"""项目创建向导对话框，调用 ProjectManager.create_project。

排错: 见 README「项目打不开」。
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from core.VitaLoom.project.project_manager import get_project_manager
from core.VitaLoom.core.editor_context import get_editor_context


class ProjectWizard(QDialog):
    """职责: 收集项目名/路径/模板并创建 projects 目录结构。"""
    """项目向导对话框"""
    
    def __init__(self, parent=None):
        """ProjectWizard.__init__。

        
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
        self.editor_context = get_editor_context()
        self.setWindowTitle(self._t("project_wizard.title", "新建项目"))
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self.project_manager = get_project_manager()
        self.created_project_path: Optional[str] = None
        
        self._init_ui()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 项目名称
        name_layout = QHBoxLayout()
        name_label = QLabel(self._t("project_wizard.field.name", "项目名称:"))
        name_label.setMinimumWidth(100)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self._t("project_wizard.placeholder.name", "输入项目名称"))
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 项目路径
        path_layout = QHBoxLayout()
        path_label = QLabel(self._t("project_wizard.field.path", "项目路径:"))
        path_label.setMinimumWidth(100)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self._t("project_wizard.placeholder.path", "选择项目保存路径"))
        browse_btn = QPushButton(self._t("project_wizard.action.browse", "浏览..."))
        browse_btn.clicked.connect(self._browse_path)  # type: ignore
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # 项目模板
        template_layout = QHBoxLayout()
        template_label = QLabel(self._t("project_wizard.field.template", "项目模板:"))
        template_label.setMinimumWidth(100)
        self.template_combo = QComboBox()
        self.template_combo.addItem(self._t("project_wizard.template.blank", "空白项目"), None)
        templates = self.project_manager.get_available_templates()
        for template in templates:
            self.template_combo.addItem(template, template)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)
        
        # 项目描述
        desc_label = QLabel(self._t("project_wizard.field.description", "项目描述:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setPlaceholderText(self._t("project_wizard.placeholder.description", "输入项目描述（可选）"))
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_btn = QPushButton(self._t("project_wizard.action.cancel", "取消"))
        cancel_btn.clicked.connect(self.reject)  # type: ignore
        create_btn = QPushButton(self._t("project_wizard.action.create", "创建"))
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._create_project)  # type: ignore
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _browse_path(self):
        """浏览项目路径"""
        path = QFileDialog.getExistingDirectory(
            self,
            self._t("project_wizard.dialog.choose_path.title", "选择项目保存路径"),
            self.project_manager.projects_dir,
        )
        if path:
            self.path_edit.setText(path)
    
    def _create_project(self):
        """创建项目"""
        project_name = self.name_edit.text().strip()
        if not project_name:
            QMessageBox.warning(
                self,
                self._t("dialog.error.title", "错误"),
                self._t("project_wizard.error.no_name", "请输入项目名称"),
            )
            return
        
        project_path = self.path_edit.text().strip()
        if not project_path:
            # 使用默认路径
            project_path = None
        
        template_data = self.template_combo.currentData()
        template = template_data if template_data else None
        
        description = self.desc_edit.toPlainText().strip()
        
        # 创建项目
        created_path = self.project_manager.create_project(
            project_name, project_path, template, description
        )
        
        if created_path:
            self.created_project_path = created_path
            QMessageBox.information(
                self,
                self._t("dialog.success.title", "成功"),
                self._t("project_wizard.success.created", "项目 '{name}' 创建成功！").format(name=project_name),
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                self._t("dialog.error.title", "错误"),
                self._t("project_wizard.error.create_failed", "项目创建失败，请检查项目名称和路径"),
            )
    
    def get_created_project_path(self) -> Optional[str]:
        """获取创建的项目路径。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.created_project_path
