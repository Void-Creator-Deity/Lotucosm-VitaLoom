# -*- coding: utf-8 -*-
"""项目资源库 Dock：assets 目录浏览与拖放到 SceneViewport。

排错: 拖放无效 → MIME 类型与 DragDropManager 契约。
"""

import os
from pathlib import Path as FsPath
from typing import Any, Optional, List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QLineEdit, QSplitter, QPushButton,
    QMenu, QFileIconProvider, QListView, QTreeView, QSlider,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QDir, QModelIndex, QMimeData, QUrl, QSize, QFileInfo
from PyQt6.QtGui import QAction, QIcon, QFileSystemModel, QDrag, QColor

from core.VitaLoom.ui.base_editor_widget import BaseEditorWidget
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus, SignalType
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ProjectPanel")

PACKAGES_HUB_PATH = "__PACKAGES_HUB__"

# 与常见引擎约定一致：资源 / 场景 / 脚本（磁盘名小写）
_ASSET_FOLDER_ORDER = {"assets": 0, "scenes": 1, "scripts": 2}
_STANDARD_PROJECT_SUBDIRS = frozenset({"assets", "scenes", "scripts"})


def _folder_sort_key(name: str) -> tuple:
    return (_ASSET_FOLDER_ORDER.get(name.lower(), 99), name.lower())


def _path_is_under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(root)]) == os.path.abspath(root)
    except ValueError:
        return False


class DraggableListWidget(QListWidget):
    """职责: 资源列表项拖放源，payload 供 SceneViewport.dropEvent 解析。"""
    """支持拖拽文件的列表控件"""
    def startDrag(self, supportedActions):
        """DraggableListWidget.startDrag。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        item = self.currentItem()
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        # 将文件路径转换为 URL，这样 Inspector 就能识别并接收
        if os.path.exists(file_path):
            mime_data.setUrls([QUrl.fromLocalFile(file_path)])
            drag.setMimeData(mime_data)
            
            pm = item.icon().pixmap(32, 32)
            if not pm.isNull():
                drag.setPixmap(pm)
            drag.exec(supportedActions)


class ProjectPanel(BaseEditorWidget):
    """职责: Unity 式 Project 面板，列出当前项目资源并支持拖放创建实体。"""
    """Project 面板 — 对齐 Unity Project / UE Content Browser / Godot 文件系统的浏览习惯。

    约定：
    - 树根显示「项目名称」（来自 project.json），对应打开的工程根、Godot 的 res:// 项目部分，
      避免根节点写「Assets」与磁盘上 ``assets/`` 文件夹语义混淆。
    - ``assets/``、``scenes/``、``scripts/`` 在树上使用友好显示名（磁盘路径不变）。
    - 完整路径放在 Tooltip；右侧列表上方显示面包屑。
    """

    # 自定义信号
    asset_selected = pyqtSignal(str)  # 资源被选中
    asset_double_clicked = pyqtSignal(str)  # 资源被双击

    def __init__(self, canvas: Optional[Any] = None):
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
        
        # 获取编辑器上下文和信号总线
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        self.canvas: Optional[Any] = canvas
        self.current_project_path: Optional[str] = None
        self._repo_root_cached: Optional[str] = None
        self._file_icon_provider = QFileIconProvider()

        # 预设组件分类 (用于 Add Component 菜单)
        self._component_categories = {
            "Sensors": [
                {"name": "LightSensor", "description": "检测光强"},
                {"name": "CollisionSensor", "description": "检测碰撞"},
                {"name": "EnergySensor", "description": "检测能量轨迹"}
            ],
            "Actuators": [
                {"name": "Motor", "description": "控制移动"},
                {"name": "Rotator", "description": "控制旋转"}
            ],
            "Physics": [
                {"name": "Rigidbody", "description": "物理刚体"},
                {"name": "BoxCollider", "description": "矩形碰撞体"},
                {"name": "CircleCollider", "description": "圆形碰撞体"}
            ]
        }
        
        # 初始化界面
        self._init_ui()
        
        # 订阅项目打开事件
        self.editor_context.event_bus.subscribe("project_opened", self.on_project_opened)
        
        # 如果没有项目，显示默认内容
        if not self.current_project_path:
            self.folder_tree.clear()
            self.asset_list.clear()
            placeholder = QListWidgetItem(
                self._t(
                    "project_panel.placeholder.no_project",
                    "没有打开的项目\n\n请在 'File' 菜单中创建或打开项目",
                )
            )
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.asset_list.addItem(placeholder)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _asset_type_label(self, asset_type: str) -> str:
        mapping = {
            "folder": self._t("project_panel.asset_type.folder", "文件夹"),
            "scene": self._t("project_panel.asset_type.scene", "场景"),
            "entity": self._t("project_panel.asset_type.entity", "空实体"),
            "organism": self._t("project_panel.asset_type.organism", "生物体"),
            "food": self._t("project_panel.asset_type.food", "食物"),
            "component": self._t("project_panel.asset_type.script", "脚本"),
        }
        return mapping.get(asset_type, asset_type)

    def _repo_root(self) -> str:
        if self._repo_root_cached:
            return self._repo_root_cached
        here = FsPath(__file__).resolve()
        self._repo_root_cached = str(here.parents[3])
        return self._repo_root_cached

    def _is_readonly_browser_path(self, path: Optional[str]) -> bool:
        if not path or path == PACKAGES_HUB_PATH:
            return True
        root = self._repo_root()
        b = os.path.join(root, 'builtin')
        pl = os.path.join(root, 'plugins')
        if _path_is_under(path, b):
            return True
        if os.path.isdir(pl) and _path_is_under(path, pl):
            return True
        return False

    def _find_tree_item_for_path(self, target: str) -> Optional[QTreeWidgetItem]:
        nt = os.path.normcase(os.path.normpath(target))

        def walk(it: QTreeWidgetItem) -> Optional[QTreeWidgetItem]:
            d = it.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(d, str) and d and d != PACKAGES_HUB_PATH:
                if os.path.normcase(os.path.normpath(d)) == nt:
                    return it
            for i in range(it.childCount()):
                f = walk(it.child(i))
                if f:
                    return f
            return None

        for i in range(self.folder_tree.topLevelItemCount()):
            f = walk(self.folder_tree.topLevelItem(i))
            if f:
                return f
        return None

    def _item_caption(self, item_path: str, item_name: str) -> str:
        if os.path.isdir(item_path):
            return self._folder_display_label(item_name)
        if item_name.lower() == 'project.json':
            return self._t('project_panel.file.project_config_short', 'project.json')
        return item_name

    def _use_grid_captions(self) -> bool:
        return self.asset_list.viewMode() == QListWidget.ViewMode.IconMode

    def _make_list_item(self, item_path: str, item_name: str) -> QListWidgetItem:
        txt = self._item_caption(item_path, item_name) if self._use_grid_captions() else self._list_row_label(item_path, item_name)
        it = QListWidgetItem(txt)
        it.setData(Qt.ItemDataRole.UserRole, item_path)
        it.setToolTip(item_path)
        prov = self._file_icon_provider
        if os.path.isdir(item_path):
            it.setIcon(prov.icon(QFileIconProvider.IconType.Folder))
        else:
            it.setIcon(prov.icon(QFileInfo(item_path)))
        return it

    def _on_icon_size_changed(self, value: int) -> None:
        s = max(32, int(value))
        self.asset_list.setIconSize(QSize(s, s))
        self.asset_list.setGridSize(QSize(s + 24, s + 36))

    def _refresh_asset_list_preserving_selection(self) -> None:
        sel = self.folder_tree.selectedItems()
        if sel:
            pd = sel[0].data(0, Qt.ItemDataRole.UserRole)
            if pd:
                self._update_asset_list(pd)

    def _project_display_name(self) -> str:
        """树根显示名：优先 project.json 的 name。"""
        cfg = getattr(self.editor_context, "current_project_config", None)
        if isinstance(cfg, dict):
            name = cfg.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        if self.current_project_path:
            base = os.path.basename(self.current_project_path.rstrip("/\\"))
            return base or self.current_project_path
        return self._t("project_panel.tree.assets_root", "Assets")

    def _folder_display_label(self, dirname: str) -> str:
        """标准子目录友好名（磁盘文件夹名不变）。"""
        low = dirname.lower()
        if low == "assets":
            return self._t("project_panel.folder.assets", "美术与资源")
        if low == "scenes":
            return self._t("project_panel.folder.scenes", "场景")
        if low == "scripts":
            return self._t("project_panel.folder.scripts", "脚本")
        return dirname

    def _list_row_label(self, item_path: str, item_name: str) -> str:
        """列表行展示：文件夹用友好名 + 原文件名小号提示。"""
        if os.path.isdir(item_path):
            friendly = self._folder_display_label(item_name)
            low = item_name.lower()
            if low in _STANDARD_PROJECT_SUBDIRS and friendly != item_name:
                return f"📁 {friendly}   ({item_name})"
            return f"📁 {friendly}"
        if item_name.lower() == "project.json":
            return f"📋 {self._t('project_panel.file.project_config', 'project.json（工程配置）')}"
        if item_path.endswith(".pond"):
            return f"🌊 {item_name}"
        if item_path.endswith(".aiorganism"):
            return f"🧬 {item_name}"
        if item_path.endswith(".json"):
            return f"📄 {item_name}"
        if item_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            return f"🖼️  {item_name}"
        if item_path.endswith(".py"):
            return f"🐍  {item_name}"
        return item_name

    def _set_breadcrumb(self, folder_path: str) -> None:
        # Unity-style: Assets / Packages breadcrumb
        if not hasattr(self, "_breadcrumb"):
            return
        if not folder_path:
            self._breadcrumb.setText("")
            return
        sep = self._t("project_panel.breadcrumb.sep", " > ")
        assets_label = self._t("project_panel.tree.assets_root", "Assets")
        pkg_label = self._t("project_panel.tree.packages_root", "Packages")
        engine_label = self._t("project_panel.tree.package_builtin", "Engine")
        plugins_label = self._t("project_panel.tree.package_plugins", "Community plugins")

        if folder_path == PACKAGES_HUB_PATH:
            self._breadcrumb.setText(pkg_label)
            return

        fp = os.path.normpath(folder_path)
        proj = self.current_project_path
        repo = self._repo_root()
        builtin_root = os.path.join(repo, "builtin")
        plugins_root = os.path.join(repo, "plugins")

        if proj:
            pj = os.path.normpath(proj)
            try:
                if os.path.normcase(fp) == os.path.normcase(pj):
                    self._breadcrumb.setText(assets_label)
                    return
                rel = os.path.relpath(fp, pj)
                if rel not in (".", ""):
                    parts = [x for x in rel.split(os.sep) if x]
                    self._breadcrumb.setText(
                        sep.join([assets_label] + [self._folder_display_label(x) for x in parts])
                    )
                    return
            except ValueError:
                pass

        if _path_is_under(fp, builtin_root):
            rel = os.path.relpath(fp, builtin_root)
            parts = [x for x in rel.split(os.sep) if x] if rel not in (".", "") else []
            self._breadcrumb.setText(sep.join([pkg_label, engine_label] + parts))
            return

        if os.path.isdir(plugins_root) and _path_is_under(fp, plugins_root):
            rel = os.path.relpath(fp, plugins_root)
            parts = [x for x in rel.split(os.sep) if x] if rel not in (".", "") else []
            self._breadcrumb.setText(sep.join([pkg_label, plugins_label] + parts))
            return

        self._breadcrumb.setText(fp)

    def _init_ui(self):
        """Unity Project: grid default, icon slider."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(4, 4, 4, 4)
        toolbar_layout.setSpacing(4)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self._t("project_panel.search_placeholder", "搜索资源..."))
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                color: #d4d4d4;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0e639c;
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)  # type: ignore
        toolbar_layout.addWidget(self.search_box)

        self.list_view_btn = QPushButton(self._t("project_panel.view.list", "列表"))
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setChecked(False)
        self.list_view_btn.setMaximumWidth(50)
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode("list"))  # type: ignore
        toolbar_layout.addWidget(self.list_view_btn)

        self.grid_view_btn = QPushButton(self._t("project_panel.view.grid", "网格"))
        self.grid_view_btn.setCheckable(True)
        self.grid_view_btn.setChecked(True)
        self.grid_view_btn.setMaximumWidth(50)
        self.grid_view_btn.clicked.connect(lambda: self._set_view_mode("grid"))  # type: ignore
        toolbar_layout.addWidget(self.grid_view_btn)

        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel(self._t("project_panel.header.project_tree", "项目"))
        self.folder_tree.setMaximumWidth(280)
        self.folder_tree.setMinimumWidth(160)
        self.folder_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
                border-right: 1px solid #404040;
            }
            QTreeWidget::item {
                height: 22px;
                padding: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background-color: #264f78;
                color: #ffffff;
            }
            QTreeWidget::branch {
                background-color: #252526;
            }
        """)
        self.folder_tree.itemSelectionChanged.connect(self._on_folder_selected)  # type: ignore
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self._show_folder_context_menu)  # type: ignore
        self.main_splitter.addWidget(self.folder_tree)

        self._breadcrumb = QLabel("")
        self._breadcrumb.setStyleSheet(
            "color:#bbbbbb; background-color:#2d2d30; padding:6px 10px; font-size:11px; "
            "border-bottom:1px solid #3f3f46;"
        )
        self._breadcrumb.setWordWrap(True)
        self._breadcrumb.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.asset_list = DraggableListWidget()
        self.asset_list.setDragEnabled(True)
        self.asset_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.asset_list.setUniformItemSizes(False)
        self.asset_list.setWrapping(True)
        self.asset_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.asset_list.setMovement(QListWidget.Movement.Static)
        self.asset_list.setSpacing(8)
        self.asset_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #264f78;
                color: #ffffff;
            }
        """)
        self.asset_list.itemDoubleClicked.connect(self._on_asset_double_clicked)  # type: ignore
        self.asset_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self._show_asset_context_menu)  # type: ignore

        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(8, 4, 8, 4)
        slider_row.setSpacing(8)
        iz = QLabel(self._t("project_panel.icon_size", "图标"))
        iz.setStyleSheet("color:#aaaaaa;font-size:11px;")
        self._icon_slider = QSlider(Qt.Orientation.Horizontal)
        self._icon_slider.setRange(48, 128)
        self._icon_slider.setValue(80)
        self._icon_slider.setMaximumWidth(220)
        self._icon_slider.valueChanged.connect(self._on_icon_size_changed)  # type: ignore
        slider_row.addWidget(iz)
        slider_row.addWidget(self._icon_slider)
        slider_row.addStretch()
        slider_wrap = QWidget()
        slider_wrap.setLayout(slider_row)
        slider_wrap.setStyleSheet("background-color:#2d2d30;border-top:1px solid #3f3f46;")

        right_stack = QWidget()
        right_layout = QVBoxLayout(right_stack)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._breadcrumb)
        right_layout.addWidget(self.asset_list)
        right_layout.addWidget(slider_wrap)
        self.main_splitter.addWidget(right_stack)

        self.main_splitter.setSizes([220, 620])  # type: ignore

        main_layout.addWidget(self.main_splitter)
        self._on_icon_size_changed(self._icon_slider.value())

    def _show_default_content(self):
        """显示默认内容（当没有项目时）"""
        self.folder_tree.clear()
        self.asset_list.clear()
        if hasattr(self, "_breadcrumb"):
            self._breadcrumb.setText("")
        placeholder = QListWidgetItem(
            self._t(
                "project_panel.placeholder.no_project",
                "没有打开的项目\n\n请在 'File' 菜单中创建或打开项目",
            )
        )
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_list.addItem(placeholder)

    def on_project_opened(self, data):
        """项目打开时更新项目树。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        try:
            project_path = data if isinstance(data, str) else data.get("path", "")
            if project_path and os.path.exists(project_path):
                self.current_project_path = project_path
                self._update_project_tree(project_path)
                logger.info("项目文件树已更新: %s", project_path)
        except Exception as e:
            logger.exception("更新项目文件树失败: %s", e)

    def _update_project_tree(self, project_path: str):
        # Unity: top-level Assets + Packages
        self.folder_tree.clear()

        if not os.path.exists(project_path):
            self._show_default_content()
            return

        assets_item = QTreeWidgetItem(self.folder_tree)
        assets_item.setText(0, self._t("project_panel.tree.assets_root", "Assets"))
        assets_item.setToolTip(
            0,
            self._t(
                "project_panel.tree.assets_project_tooltip",
                "User project (like Unity Assets).\n{path}",
            ).format(path=project_path),
        )
        assets_item.setData(0, Qt.ItemDataRole.UserRole, project_path)
        assets_item.setExpanded(True)
        self._add_directory_to_tree(assets_item, project_path)

        pkg_parent = QTreeWidgetItem(self.folder_tree)
        pkg_parent.setText(0, self._t("project_panel.tree.packages_root", "Packages"))
        pkg_parent.setToolTip(
            0, self._t("project_panel.tree.packages_tooltip", "Engine packages (read-only)")
        )
        pkg_parent.setData(0, Qt.ItemDataRole.UserRole, PACKAGES_HUB_PATH)
        pkg_parent.setExpanded(False)

        repo = self._repo_root()
        builtin_path = os.path.join(repo, "builtin")
        if os.path.isdir(builtin_path):
            bi = QTreeWidgetItem(pkg_parent)
            bi.setText(0, self._t("project_panel.tree.package_builtin", "Engine"))
            bi.setToolTip(0, builtin_path)
            bi.setData(0, Qt.ItemDataRole.UserRole, builtin_path)
            bi.setExpanded(False)
            self._add_directory_to_tree(bi, builtin_path)

        plugins_path = os.path.join(repo, "plugins")
        if os.path.isdir(plugins_path):
            pi = QTreeWidgetItem(pkg_parent)
            pi.setText(0, self._t("project_panel.tree.package_plugins", "Community plugins"))
            pi.setToolTip(0, plugins_path)
            pi.setData(0, Qt.ItemDataRole.UserRole, plugins_path)
            pi.setExpanded(False)
            self._add_directory_to_tree(pi, plugins_path)

        self.folder_tree.setCurrentItem(assets_item)
        self._update_asset_list(project_path)

    def _add_directory_to_tree(self, parent_item: QTreeWidgetItem, dir_path: str):
        """递归添加目录到树"""
        try:
            if not os.path.isdir(dir_path):
                return
            
            # 获取目录内容（只取文件夹）
            items = sorted(
                [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))],
                key=_folder_sort_key,
            )
            
            for item_name in items:
                item_path = os.path.join(dir_path, item_name)
                
                # 跳过隐藏文件夹
                if item_name.startswith('.'):
                    continue
                
                tree_item = QTreeWidgetItem(parent_item)
                label = self._folder_display_label(item_name)
                low = item_name.lower()
                if low in _STANDARD_PROJECT_SUBDIRS and label != item_name:
                    tree_item.setText(0, f"{label}   ({item_name})")
                else:
                    tree_item.setText(0, label)
                tree_item.setToolTip(0, item_path)
                tree_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                
                # 递归添加子目录
                self._add_directory_to_tree(tree_item, item_path)
                tree_item.setExpanded(False)  # 默认折叠
        except Exception as e:
            logger.warning("添加目录到树失败: %s", e)

    def _update_asset_list(self, folder_path: str):
        self.asset_list.clear()
        self._set_breadcrumb(folder_path)

        if folder_path == PACKAGES_HUB_PATH:
            repo = self._repo_root()
            builtin_path = os.path.join(repo, "builtin")
            plugins_path = os.path.join(repo, "plugins")
            for cap, pth in (
                (self._t("project_panel.tree.package_builtin", "Engine"), builtin_path),
                (self._t("project_panel.tree.package_plugins", "Community plugins"), plugins_path),
            ):
                if os.path.isdir(pth):
                    it = QListWidgetItem(cap)
                    it.setData(Qt.ItemDataRole.UserRole, pth)
                    it.setIcon(self._file_icon_provider.icon(QFileIconProvider.IconType.Folder))
                    it.setToolTip(pth)
                    self.asset_list.addItem(it)
            hint = QListWidgetItem(
                self._t("project_panel.packages_hub_hint", "Double-click Engine or Community to browse (read-only).")
            )
            hint.setFlags(Qt.ItemFlag.NoItemFlags)
            hint.setForeground(QColor(140, 140, 140))
            self.asset_list.addItem(hint)
            return

        if not os.path.exists(folder_path):
            return

        try:
            items = sorted(
                os.listdir(folder_path),
                key=lambda x: (not os.path.isdir(os.path.join(folder_path, x)), x.lower()),
            )
            for item_name in items:
                item_path = os.path.join(folder_path, item_name)
                if item_name.startswith("."):
                    continue
                self.asset_list.addItem(self._make_list_item(item_path, item_name))
        except Exception as ex:
            logger.warning("更新资源列表失败: %s", ex)

    def _on_folder_selected(self):
        """文件夹选择变化处理"""
        selected_items = self.folder_tree.selectedItems()
        if selected_items:
            folder_path = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if folder_path:
                self._update_asset_list(folder_path)

    def _on_search_changed(self, text: str):
        """搜索文本变化处理"""
        query = text.strip().lower()

        # 空搜索时显示全部
        if not query:
            for i in range(self.asset_list.count()):
                item = self.asset_list.item(i)
                item.setHidden(False)
            return

        # 基于资源文件名过滤（优先使用真实路径，避免 emoji 前缀干扰）
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            raw_path = item.data(Qt.ItemDataRole.UserRole)
            display_text = item.text()

            if isinstance(raw_path, str) and raw_path:
                match_text = os.path.basename(raw_path).lower()
            else:
                match_text = display_text.lower()

            item.setHidden(query not in match_text)

    def _on_asset_double_clicked(self, item: QListWidgetItem):
        asset_path = item.data(Qt.ItemDataRole.UserRole)
        if not asset_path:
            return
        if isinstance(asset_path, str) and asset_path.lower().endswith("project.json"):
            self.asset_double_clicked.emit(asset_path)
            logger.info("打开工程配置: %s", asset_path)
            return
        if os.path.isdir(asset_path):
            project_json = os.path.join(asset_path, "project.json")
            if os.path.isfile(project_json):
                current = self.current_project_path or ""
                if os.path.normcase(os.path.abspath(asset_path)) != os.path.normcase(
                    os.path.abspath(current) if current else ""
                ):
                    self.asset_double_clicked.emit(asset_path)
                    logger.info("打开项目目录: %s", asset_path)
                    return
            tree_item = self._find_tree_item_for_path(asset_path)
            if tree_item:
                self.folder_tree.setCurrentItem(tree_item)
                tree_item.setExpanded(True)
                self.folder_tree.scrollToItem(tree_item)
                self._update_asset_list(asset_path)
            return
        self.asset_double_clicked.emit(asset_path)
        logger.info("打开资源: %s", asset_path)

    def _set_active_scene(self, scene_path: str) -> None:
        """将 .pond 设为 project.json 的 active_scene 并加载（不切换工程）。"""
        if not scene_path or not scene_path.endswith(".pond"):
            return
        if not self.current_project_path:
            return
        try:
            scenes_dir = os.path.join(self.current_project_path, "scenes")
            rel = os.path.relpath(scene_path, scenes_dir).replace("\\", "/")
            from core.VitaLoom.project.project_manager import get_project_manager
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            get_project_manager().update_project_config_fields({"active_scene": rel})
            get_scene_manager().load_scene(scene_path)
            logger.info("已设为主场景: %s", rel)
        except Exception as e:
            logger.exception("设为主场景失败: %s", e)

    def _set_view_mode(self, mode: str):
        if mode == "list":
            self.asset_list.setViewMode(QListWidget.ViewMode.ListMode)
            self.list_view_btn.setChecked(True)
            self.grid_view_btn.setChecked(False)
        elif mode == "grid":
            self.asset_list.setViewMode(QListWidget.ViewMode.IconMode)
            self.list_view_btn.setChecked(False)
            self.grid_view_btn.setChecked(True)
        self._refresh_asset_list_preserving_selection()

    def _show_folder_context_menu(self, pos: QPoint):
        item = self.folder_tree.itemAt(pos)
        menu = QMenu(self)

        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            readonly = isinstance(path, str) and self._is_readonly_browser_path(path)
            hub = path == PACKAGES_HUB_PATH

            if not readonly and not hub:
                create_folder_action = QAction(self._t("project_panel.menu.create_folder", "创建文件夹"), self)
                create_folder_action.triggered.connect(lambda: self._create_asset("folder"))  # type: ignore
                menu.addAction(create_folder_action)

                menu.addSeparator()

                create_scene_action = QAction(self._t("project_panel.menu.create_scene", "创建/场景 (.pond)"), self)
                create_scene_action.triggered.connect(lambda: self._create_asset("scene"))  # type: ignore
                menu.addAction(create_scene_action)

                create_entity_action = QAction(self._t("project_panel.menu.create_entity", "创建/空实体 (.json)"), self)
                create_entity_action.triggered.connect(lambda: self._create_asset("entity"))  # type: ignore
                menu.addAction(create_entity_action)

                create_organism_action = QAction(self._t("project_panel.menu.create_organism", "创建/生物体 (.json)"), self)
                create_organism_action.triggered.connect(lambda: self._create_asset("organism"))  # type: ignore
                menu.addAction(create_organism_action)

                create_food_action = QAction(self._t("project_panel.menu.create_food", "创建/食物 (.json)"), self)
                create_food_action.triggered.connect(lambda: self._create_asset("food"))  # type: ignore
                menu.addAction(create_food_action)

                create_component_action = QAction(self._t("project_panel.menu.create_script", "创建/脚本 (.py)"), self)
                create_component_action.triggered.connect(lambda: self._create_asset("component"))  # type: ignore
                menu.addAction(create_component_action)

                menu.addSeparator()

                import_action = QAction(self._t("project_panel.menu.import", "导入资源..."), self)
                import_action.triggered.connect(self._import_asset)  # type: ignore
                menu.addAction(import_action)

                menu.addSeparator()

            refresh_action = QAction(self._t("project_panel.menu.refresh", "刷新"), self)
            refresh_action.triggered.connect(self._refresh_folder)  # type: ignore
            menu.addAction(refresh_action)
        else:
            refresh_action = QAction(self._t("project_panel.menu.refresh", "刷新"), self)
            refresh_action.triggered.connect(self._refresh_folder)  # type: ignore
            menu.addAction(refresh_action)

        menu.exec(self.folder_tree.mapToGlobal(pos))  # type: ignore

    def _show_asset_context_menu(self, pos: QPoint):
        item = self.asset_list.itemAt(pos)
        menu = QMenu(self)

        if item:
            asset_path = item.data(Qt.ItemDataRole.UserRole)
            if asset_path:
                open_action = QAction(self._t("project_panel.menu.open", "打开"), self)
                open_action.triggered.connect(lambda: self._on_asset_double_clicked(item))  # type: ignore
                menu.addAction(open_action)

                if isinstance(asset_path, str) and asset_path.endswith(".pond"):
                    set_active_action = QAction(self._t("project_panel.menu.set_active_scene", "设为主场景"), self)
                    set_active_action.triggered.connect(
                        lambda: self._set_active_scene(asset_path)
                    )  # type: ignore
                    menu.addAction(set_active_action)

                if not self._is_readonly_browser_path(asset_path):
                    menu.addSeparator()
                    delete_action = QAction(self._t("project_panel.menu.delete", "删除"), self)
                    delete_action.triggered.connect(lambda: self._delete_asset(asset_path))  # type: ignore
                    menu.addAction(delete_action)
        else:
            folder = self._get_current_folder_path()
            if folder:
                create_folder_action = QAction(self._t("project_panel.menu.create_folder", "创建文件夹"), self)
                create_folder_action.triggered.connect(lambda: self._create_asset("folder"))  # type: ignore
                menu.addAction(create_folder_action)

                menu.addSeparator()

                create_scene_action = QAction(self._t("project_panel.menu.create_scene", "创建/场景 (.pond)"), self)
                create_scene_action.triggered.connect(lambda: self._create_asset("scene"))  # type: ignore
                menu.addAction(create_scene_action)

                menu.addSeparator()

                import_action = QAction(self._t("project_panel.menu.import", "导入资源..."), self)
                import_action.triggered.connect(self._import_asset)  # type: ignore
                menu.addAction(import_action)

        menu.exec(self.asset_list.mapToGlobal(pos))  # type: ignore

    def _import_asset(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        target_folder = self._get_current_folder_path()
        if not target_folder:
            QMessageBox.information(
                self,
                self._t("project_panel.readonly.title", "提示"),
                self._t(
                    "project_panel.import_need_assets_folder",
                    "请先选择左侧 Assets 下的文件夹再导入。",
                ),
            )
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._t("project_panel.dialog.import.title", "导入资源"),
            "",
            self._t(
                "project_panel.dialog.import.filter",
                "所有文件 (*.*);;图片 (*.png *.jpg *.jpeg *.bmp);;场景 (*.pond);;脚本 (*.py)",
            ),
        )

        if files:
            import shutil

            for file_path in files:
                try:
                    target_path = os.path.join(target_folder, os.path.basename(file_path))
                    if file_path != target_path:
                        shutil.copy2(file_path, target_path)
                    logger.info("已导入资源: %s", target_path)
                except Exception as e:
                    logger.exception("导入资源失败: %s", e)

            self._refresh_folder()

    def _create_asset(self, asset_type: str):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox

        folder = self._get_current_folder_path()
        if not folder:
            QMessageBox.information(
                self,
                self._t("project_panel.readonly.title", "提示"),
                self._t(
                    "project_panel.create_need_assets_folder",
                    "请在 Assets 下选择目标文件夹后再创建。（Packages 内只读）",
                ),
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            self._t("project_panel.dialog.create_asset.title", "创建 {type}").format(type=self._asset_type_label(asset_type))
        )
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        name_label = QLabel(self._t("project_panel.field.name", "名称:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText(
            self._t("project_panel.placeholder.asset_name", "输入 {type} 名称...").format(type=self._asset_type_label(asset_type))
        )
        layout.addWidget(name_label)
        layout.addWidget(name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)  # type: ignore
        buttons.rejected.connect(dialog.reject)  # type: ignore
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset_name = name_input.text().strip()
            if asset_name:
                self.editor_context.event_bus.publish(
                    "create_asset",
                    {"type": asset_type, "name": asset_name, "folder": folder},
                )
                logger.info("创建资源: %s (%s)", asset_name, asset_type)

    def _get_current_folder_path(self) -> Optional[str]:
        selected_items = self.folder_tree.selectedItems()
        if not selected_items:
            return self.current_project_path
        p = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
        if p == PACKAGES_HUB_PATH:
            return None
        if not p:
            return None
        if self._is_readonly_browser_path(p):
            return None
        return p

    def _refresh_folder(self):
        """刷新文件夹"""
        if self.current_project_path:
            self._update_project_tree(self.current_project_path)

    def _delete_asset(self, asset_path: str):
        """删除资源"""
        from PyQt6.QtWidgets import QMessageBox

        if self._is_readonly_browser_path(asset_path):
            QMessageBox.information(
                self,
                self._t("project_panel.readonly.title", "提示"),
                self._t("project_panel.readonly.no_delete", "Packages / 引擎目录为只读，不能删除。"),
            )
            return

        usage_info = self._check_asset_usage(asset_path)
        if usage_info:
            msg = self._t(
                "project_panel.dialog.delete.in_use.prefix",
                "资源 '{name}' 正在当前场景中被以下实体使用：\n\n",
            ).format(name=os.path.basename(asset_path))
            msg += "\n".join([f"- {name} ({id})" for id, name in usage_info])
            msg += self._t(
                "project_panel.dialog.delete.in_use.suffix",
                "\n\n确定要删除吗？这可能会导致场景显示异常。",
            )
            
            reply = QMessageBox.warning(
                self,
                self._t("project_panel.dialog.delete.in_use.title", "资源正在使用中"),
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                self._t("project_panel.dialog.delete.confirm.title", "确认删除"),
                self._t("project_panel.dialog.delete.confirm.content", "确定要删除 '{name}' 吗？").format(
                    name=os.path.basename(asset_path)
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(asset_path):
                    os.remove(asset_path)
                elif os.path.isdir(asset_path):
                    import shutil
                    shutil.rmtree(asset_path)
                logger.info("已删除资源: %s", asset_path)
                self._refresh_folder()
                
                # 通知其它组件资源已删除
                self.editor_context.event_bus.publish("asset_deleted", {"path": asset_path})
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self._t("dialog.error.title", "错误"),
                    self._t("project_panel.dialog.delete.failed", "删除失败: {error}").format(error=e),
                )

    def _check_asset_usage(self, asset_path: str) -> List[tuple]:
        """检查资源在当前场景中的使用情况"""
        usage = []
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if not scene_data:
                return usage
            
            entities = scene_data.get("entities", [])
            abs_asset_path = os.path.abspath(asset_path).replace("\\", "/")
            
            for entity in entities:
                # 检查 sprite_path
                sprite_path = entity.get("sprite_path")
                if sprite_path:
                    abs_sprite_path = os.path.abspath(sprite_path).replace("\\", "/")
                    if abs_sprite_path == abs_asset_path:
                        usage.append((entity.get("id"), entity.get("name", self._t("project_panel.unnamed", "未命名"))))
                        continue
                
                # 检查 prefab_path
                prefab_path = entity.get("prefab_path")
                if prefab_path:
                    abs_prefab_path = os.path.abspath(prefab_path).replace("\\", "/")
                    if abs_prefab_path == abs_asset_path:
                        usage.append((entity.get("id"), entity.get("name", self._t("project_panel.unnamed", "未命名"))))
                        continue
        except Exception as e:
            logger.warning("检查资源使用情况失败: %s", e)
            
        return usage


# 为了向后兼容，保留ComponentEditorWidget作为别名
ComponentEditorWidget = ProjectPanel
