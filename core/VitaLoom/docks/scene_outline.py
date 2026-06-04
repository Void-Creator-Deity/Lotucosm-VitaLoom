# -*- coding: utf-8 -*-
"""Hierarchy Dock：场景实体树、选区同步与结构编辑。

排错: 选区不同步 → SignalBus object_selected 与 SceneViewport 双向绑定。
"""

from typing import Any, List, Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction

# 导入编辑器上下文和信号总线
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus, SignalType
from core.VitaLoom.core.logger import get_logger
import os

logger = get_logger("HierarchyPanel")


class HierarchyPanel(QWidget):
    """职责: Unity 式层级树，反映 SceneViewport 节点并驱动 Inspector。
    时机: Hierarchy 插件 Dock on_load。
    不变量: 选区变更须同步 SignalBus 与 SceneViewport。
    排错: 树为空 → 当前 scene 是否 load_scene；子实体层级见 entities 嵌套。
    """
    # 显示结构示例：项目根 → Pond → Entity → Child Entity
    _STRUCTURE_HINT = """
    - 项目根
      - Pond 1
        - Entity 1
          - Child Entity 1.1
          - Child Entity 1.2
        - Entity 2
      - Pond 2
        - Entity 3
    """

    # 对象选中信号
    object_selected = pyqtSignal(object)  # 选中的对象
    pond_selected = pyqtSignal(object)  # 选中的Pond

    def __init__(self):
        """HierarchyPanel.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__()
        
        # 获取编辑器上下文和信号总线
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        self.setMinimumWidth(200)
        self.setStyleSheet("background-color: #252526;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self._t("hierarchy_panel.search_placeholder", "搜索..."))
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
        self.search_box.textChanged.connect(self._on_search_text_changed)  # type: ignore
        self._layout.addWidget(self.search_box)

        # 树控件
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel(self._t("hierarchy_panel.header", "层级"))
        self.tree_widget.setRootIsDecorated(True)
        self.tree_widget.setAlternatingRowColors(False)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree_widget.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tree_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        # 设置样式（Unity风格）
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: none;
                outline: none;
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
                background-color: transparent;
            }
        """)

        self._layout.addWidget(self.tree_widget)

        # 连接信号
        self.tree_widget.itemClicked.connect(self._on_item_clicked)  # type: ignore
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)  # type: ignore
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)  # type: ignore
        
        # 连接编辑器上下文信号
        self.editor_context.selection_changed.connect(self._on_context_selection_changed)
        
        # 连接信号总线信号
        self.signal_bus.object_modified.connect(self._on_object_modified)
        
        # 订阅项目打开事件
        self.editor_context.event_bus.subscribe("project_opened", self._on_project_opened)
        self.editor_context.event_bus.subscribe("pond_created", self._on_pond_created)
        self.editor_context.event_bus.subscribe("entity_created", self._on_entity_created)
        self.editor_context.event_bus.subscribe("entity_deleted", self._on_entity_deleted)
        self.editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
        
        # 项目路径
        self._project_path: Optional[str] = None
        
        # 搜索过滤
        self._search_filter = ""

    def _on_project_opened(self, data):
        """项目打开时更新Hierarchy"""
        try:
            project_path = data if isinstance(data, str) else data.get("path", "")
            if project_path:
                self._project_path = project_path
                self._update_hierarchy()
        except Exception as e:
            logger.exception(self._t("hierarchy_panel.log.update_failed", "层级更新失败: {error}").format(error=e))

    def _on_pond_created(self, data):
        """Pond创建事件处理"""
        self._update_hierarchy()

    def _on_entity_created(self, data):
        """实体创建事件处理"""
        self._update_hierarchy()

    def _on_entity_deleted(self, data):
        """实体删除事件处理"""
        self._update_hierarchy()

    def _on_object_modified(self, obj: Any, modified_attrs: Dict[str, Any]):
        """对象修改事件处理"""
        # 如果名称发生变化，更新Hierarchy中的显示
        if 'name' in modified_attrs or 'id' in modified_attrs:
            obj_id = getattr(obj, 'id', None) if not isinstance(obj, dict) else obj.get('id')
            if obj_id:
                item = self._find_item_by_id(obj_id)
                if item:
                    new_name = modified_attrs.get('name', modified_attrs.get('id', item.text(0)))
                    item.setText(0, str(new_name))

    def _update_hierarchy(self):
        """更新Hierarchy树（显示所有Pond和实体）"""
        # 清空树
        self.tree_widget.clear()
        
        if not self._project_path:
            return
        
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            current_scene_data = sm.get_scene_data()
            current_scene_path = sm.get_current_scene_path()

            # 如果有当前在编辑的场景，优先显示它
            if current_scene_data and current_scene_path:
                pond_name = current_scene_data.get("name", self._t("hierarchy_panel.current_scene", "当前场景"))
                pond_item = self._create_tree_item(
                    self.tree_widget.invisibleRootItem(),
                    pond_name,
                    {'type': 'pond', 'path': current_scene_path, 'name': pond_name}
                )
                pond_item.setExpanded(True)
                
                # 直接从内存数据加载实体
                self._build_entities_from_data(pond_item, current_scene_data)
                return

            # 如果没有当前场景，扫描目录 (回退逻辑)
            scenes_dir = os.path.join(self._project_path, "scenes")
            if os.path.exists(scenes_dir):
                # 遍历所有.pond文件
                for file in os.listdir(scenes_dir):
                    if file.endswith(".pond"):
                        pond_path = os.path.join(scenes_dir, file)
                        pond_name = file[:-5]
                        
                        pond_item = self._create_tree_item(
                            self.tree_widget.invisibleRootItem(),
                            pond_name,
                            {'type': 'pond', 'path': pond_path, 'name': pond_name}
                        )
                        pond_item.setExpanded(True)
                        self._load_pond_entities(pond_item, pond_path)
        except Exception as e:
            logger.exception(self._t("hierarchy_panel.log.update_failed", "层级更新失败: {error}").format(error=e))

    def _build_entities_from_data(self, pond_item: QTreeWidgetItem, pond_data: Dict):
        """从内存数据构建实体树项"""
        entities = pond_data.get("entities", [])
        
        # 建立实体映射
        entity_map: Dict[str, Dict] = {}
        root_entities: List[Dict] = []
        
        for entity_data in entities:
            entity_id = entity_data.get("id", "")
            entity_map[entity_id] = entity_data
            entity_data['_children'] = []
        
        for entity_data in entities:
            parent_id = entity_data.get("parent_id")
            if parent_id and parent_id in entity_map:
                entity_map[parent_id]['_children'].append(entity_data)
            else:
                root_entities.append(entity_data)
        
        for entity_data in root_entities:
            self._create_entity_tree_item(pond_item, entity_data, entity_map)

    def _load_pond_entities(self, pond_item: QTreeWidgetItem, pond_path: str):
        """加载Pond中的实体（支持层级结构）"""
        try:
            import json
            with open(pond_path, 'r', encoding='utf-8') as f:
                pond_data = json.load(f)
            
            # 获取实体列表
            entities = pond_data.get("entities", [])
            
            # 构建实体层级结构
            entity_map: Dict[str, Dict] = {}
            root_entities: List[Dict] = []
            
            # 第一遍：建立实体映射
            for entity_data in entities:
                entity_id = entity_data.get("id", "")
                entity_map[entity_id] = entity_data
                entity_data['_children'] = []
            
            # 第二遍：建立父子关系
            for entity_data in entities:
                parent_id = entity_data.get("parent_id")
                if parent_id and parent_id in entity_map:
                    entity_map[parent_id]['_children'].append(entity_data)
                else:
                    root_entities.append(entity_data)
            
            # 第三遍：递归创建树项
            for entity_data in root_entities:
                self._create_entity_tree_item(pond_item, entity_data, entity_map)
        except Exception as e:
            logger.exception(self._t("hierarchy_panel.log.load_pond_failed", "加载池塘实体失败: {error}").format(error=e))

    def _create_entity_tree_item(self, parent_item: QTreeWidgetItem, entity_data: Dict, entity_map: Dict):
        """递归创建实体树项（支持子实体）"""
        entity_id = entity_data.get("id", "")
        entity_name = entity_data.get("name", entity_id)
        entity_type = entity_data.get("type", "entity")
        
        # 创建实体树项
        entity_item = self._create_tree_item(
            parent_item,
            entity_name,
            {'type': 'entity', 'data': entity_data, 'id': entity_id}
        )
        
        # 如果有子实体，递归创建
        children = entity_data.get('_children', [])
        for child_data in children:
            self._create_entity_tree_item(entity_item, child_data, entity_map)

    def _on_search_text_changed(self, text: str):
        """搜索文本变化处理"""
        self._search_filter = text.lower()
        self._update_tree_visibility()

    def _update_tree_visibility(self):
        """根据搜索过滤更新树可见性"""
        root = self.tree_widget.invisibleRootItem()
        self._filter_tree_item(root, self._search_filter)

    def _filter_tree_item(self, item: QTreeWidgetItem, filter_text: str):
        """递归过滤树项"""
        if not filter_text:
            item.setHidden(False)
            for i in range(item.childCount()):
                self._filter_tree_item(item.child(i), filter_text)
            return
        
        # 检查当前项是否匹配
        text = item.text(0).lower()
        matches = filter_text in text
        
        # 检查子项是否匹配
        child_matches = False
        for i in range(item.childCount()):
            child = item.child(i)
            if self._filter_tree_item(child, filter_text):
                child_matches = True
        
        # 如果当前项或子项匹配，显示
        if matches or child_matches:
            item.setHidden(False)
            item.setExpanded(True)
            return True
        else:
            item.setHidden(True)
            return False

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """树项被点击时的处理"""
        obj_data = item.data(0, Qt.ItemDataRole.UserRole)
        if obj_data:
            obj_type = obj_data.get('type')
            
            # 更新编辑器上下文选中对象
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Ctrl+点击：切换选择
                if self.editor_context.is_selected(obj_data):
                    self.editor_context.remove_selection(obj_data)
                else:
                    self.editor_context.add_selection(obj_data)
            else:
                # 普通点击：单选
                self.editor_context.set_selection([obj_data])
            
            # 根据类型发送不同信号
            if obj_type == 'pond':
                self.pond_selected.emit(obj_data)
                pond_path = obj_data.get('path')
                
                # 如果点击的是 pond，且不是当前场景，则加载它
                from core.VitaLoom.scene.scene_manager import get_scene_manager
                sm = get_scene_manager()
                if pond_path and pond_path != sm.get_current_scene_path():
                    sm.load_scene(pond_path)
                    
                # 通知其他组件
                self.editor_context.event_bus.publish("pond_selected", obj_data)
            elif obj_type == 'entity':
                self.object_selected.emit(obj_data)
                self.signal_bus.emit_object_selected(obj_data)

    def _on_selection_changed(self):
        """树选择变化处理"""
        selected_items = self.tree_widget.selectedItems()
        selected_objects = []
        for item in selected_items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                selected_objects.append(data)
                
        if selected_objects:
            self.editor_context.set_selection(selected_objects)

    def _on_context_selection_changed(self, objects: List[Any]):
        """编辑器上下文选中对象变化处理"""
        # 更新树选择，避免循环
        self.tree_widget.blockSignals(True)
        self.tree_widget.clearSelection()
        
        # 在树中查找对应的项目
        for obj in objects:
            obj_id = obj.get('id') if isinstance(obj, dict) else (getattr(obj, 'id', None))
            if obj_id:
                item = self._find_item_by_id(obj_id)
                if item:
                    item.setSelected(True)
        self.tree_widget.blockSignals(False)

    def _find_item_by_id(self, target_id: str) -> Optional[QTreeWidgetItem]:
        """通过ID查找树项"""
        root = self.tree_widget.invisibleRootItem()
        stack = [root.child(i) for i in range(root.childCount())]
        while stack:
            item = stack.pop()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                item_id = data.get('id') if isinstance(data, dict) else getattr(data, 'id', None)
                if item_id == target_id:
                    return item
            for i in range(item.childCount()):
                stack.append(item.child(i))
        return None

    def _show_context_menu(self, pos: QPoint):
        """显示上下文菜单（Unity风格）"""
        item = self.tree_widget.itemAt(pos)
        menu = QMenu(self)
        
        obj_data = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        
        # 创建菜单项
        if obj_data and obj_data.get('type') == 'pond':
            # Pond右键菜单
            create_entity_action = QAction(self._t("hierarchy_panel.menu.create_entity", "创建实体"), self)
            create_entity_action.triggered.connect(lambda: self._create_entity_in_pond(obj_data))  # type: ignore
            menu.addAction(create_entity_action)
        elif obj_data and obj_data.get('type') == 'entity':
            # 实体右键菜单
            create_child_action = QAction(self._t("hierarchy_panel.menu.create_child_entity", "创建子实体"), self)
            create_child_action.triggered.connect(lambda: self._create_child_entity(obj_data))  # type: ignore
            menu.addAction(create_child_action)
            
            menu.addSeparator()
            
            add_script_action = QAction(self._t("hierarchy_panel.menu.add_script", "添加脚本"), self)
            add_script_action.triggered.connect(lambda: self._add_script_to_entity(obj_data))  # type: ignore
            menu.addAction(add_script_action)
            
            menu.addSeparator()
            
            duplicate_action = QAction(self._t("hierarchy_panel.menu.duplicate", "复制"), self)
            duplicate_action.triggered.connect(lambda: self._duplicate_entity(obj_data))  # type: ignore
            menu.addAction(duplicate_action)
            
            delete_action = QAction(self._t("hierarchy_panel.menu.delete", "删除"), self)
            delete_action.triggered.connect(lambda: self._delete_entity(obj_data))  # type: ignore
            menu.addAction(delete_action)
        else:
            # 空白区域右键菜单
            create_pond_action = QAction(self._t("hierarchy_panel.menu.create_pond", "创建池塘"), self)
            create_pond_action.triggered.connect(self._create_pond)  # type: ignore
            menu.addAction(create_pond_action)
        
        global_pos = self.tree_widget.mapToGlobal(pos)
        menu.exec(global_pos)  # type: ignore

    def _create_pond(self):
        """创建新Pond"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("hierarchy_panel.dialog.create_pond.title", "创建池塘"))
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        name_label = QLabel(self._t("hierarchy_panel.dialog.create_pond.name_label", "池塘名称:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText(self._t("hierarchy_panel.dialog.create_pond.name_placeholder", "输入池塘名称..."))
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)  # type: ignore
        buttons.rejected.connect(dialog.reject)  # type: ignore
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pond_name = name_input.text().strip()
            if pond_name:
                self.editor_context.event_bus.publish("create_pond", {
                    'name': pond_name,
                    'project_path': self._project_path
                })

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        self.search_box.setPlaceholderText(self._t("hierarchy_panel.search_placeholder", "搜索..."))
        self.tree_widget.setHeaderLabel(self._t("hierarchy_panel.header", "层级"))

    def _create_entity_in_pond(self, pond_data: Dict):
        """在Pond中创建实体"""
        self.editor_context.event_bus.publish("create_entity", {
            'pond': pond_data,
            'parent_id': None
        })

    def _create_child_entity(self, parent_entity_data: Dict):
        """创建子实体"""
        self.editor_context.event_bus.publish("create_entity", {
            'pond': None,  # 从父实体获取Pond
            'parent_id': parent_entity_data.get('id')
        })

    def _add_script_to_entity(self, entity_data: Dict):
        """给实体添加脚本"""
        self.editor_context.event_bus.publish("add_script_to_entity", {
            'entity': entity_data
        })

    def _duplicate_entity(self, entity_data: Dict):
        """复制实体"""
        self.editor_context.event_bus.publish("duplicate_entity", {
            'entity': entity_data
        })

    def _delete_entity(self, entity_data: Dict):
        """删除实体"""
        self.editor_context.event_bus.publish("delete_entity", {
            'entity': entity_data
        })

    def _create_tree_item(self, parent: QTreeWidgetItem, text: str, obj_data: Any = None) -> QTreeWidgetItem:
        """创建树项"""
        item = QTreeWidgetItem(parent)
        item.setText(0, text)
        if obj_data:
            item.setData(0, Qt.ItemDataRole.UserRole, obj_data)
        return item


# 为了向后兼容，保留ProjectTree作为别名
ProjectTree = HierarchyPanel
