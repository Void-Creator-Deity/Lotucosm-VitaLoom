# -*- coding: utf-8 -*-
"""Inspector Dock：选中节点/连线的属性表单与撤销命令。

架构数据流::

    selection_changed → InspectorPanel → Modify*Command → CommandStack

排错: 见 core/VitaLoom/README.md「Inspector」
"""

import os
import json
from typing import Any, List, Optional, Dict, Callable

from core.VitaLoom.scene import script_property_edit as spe
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QScrollArea, QColorDialog, QSlider, QPlainTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor

# 导入命令模式
from core.VitaLoom.commands.command import (
    Command,
    CommandStack,
    ModifyNodePropertyCommand,
    ModifyConnectionPropertyCommand,
)

# 导入编辑器上下文和信号总线
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus
from core.VitaLoom.core.logger import get_logger


logger = get_logger("InspectorPanel")


class FoldoutGroup(QGroupBox):
    """职责: Unity 风格可折叠属性分组容器。"""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        """FoldoutGroup.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__(title, parent)
        self._expanded = True
        self._setup_style()
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggled)  # type: ignore
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                color: #d4d4d4;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QGroupBox::indicator {
                width: 12px;
                height: 12px;
            }
        """)
    
    def _on_toggled(self, checked: bool):
        """折叠/展开处理"""
        self._expanded = checked
        # 隐藏/显示内容
        layout = self.layout()
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(checked)
    
    @property
    def is_expanded(self) -> bool:
        """是否展开。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        return self._expanded
    
    def set_expanded(self, expanded: bool):
        """设置展开状态。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.setChecked(expanded)


class InspectorPanel(QWidget):
    """职责: 根据选中对象动态生成属性编辑器并提交 Modify 命令。
    时机: Inspector 插件 Dock on_load；订阅 selection 与 scene 信号。
    不变量: 属性修改须走 CommandStack 以支持撤销；脚本属性委托 script_property_edit。
    排错: 不刷新 → signal_bus selection；改值不可撤销 → 是否 execute 命令。
    """

    # 自定义信号
    projectModified = pyqtSignal()
    commandExecuted = pyqtSignal()

    def __init__(self):
        """InspectorPanel.__init__。

        
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
        
        self.setMinimumWidth(280)
        self.setStyleSheet("background-color: #2d2d2d;")
        self.setAcceptDrops(True)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # 标题
        self.title_label = QLabel(self._t("inspector.title", "检视器"))
        self.title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #404040;")
        main_layout.addWidget(line)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
        """)
        
        # 属性容器
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(4, 4, 4, 4)
        self.properties_layout.setSpacing(4)
        self.properties_layout.addStretch()
        
        scroll_area.setWidget(self.properties_container)
        main_layout.addWidget(scroll_area)

        # 状态信息
        self.status_label = QLabel(self._t("inspector.status.no_selection", "未选择对象"))
        self.status_label.setStyleSheet("color: #888888; font-size: 11px; padding: 4px;")
        main_layout.addWidget(self.status_label)

        # 当前选中的对象
        self._selected_objects: List[Any] = []
        
        # 属性控件映射
        self._property_controls: Dict[str, Any] = {}
        self._property_groups: Dict[str, FoldoutGroup] = {}
        
        # 命令栈
        self.command_stack = CommandStack()
        
        # 连接编辑器上下文信号
        self.editor_context.selection_changed.connect(self._on_selection_changed)
        if hasattr(self.editor_context, "event_bus"):
            self.editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
            self.editor_context.event_bus.subscribe("project_opened", self._on_project_opened)
        
        self._clear_properties()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    class _PropertyWriteCommand(Command):
        """通用属性写回命令，支持对象属性与字典字段。"""

        def __init__(self, target: Any, apply_fn: Callable[[Any], None], rollback_fn: Callable[[Any], None], desc: str):
            """_PropertyWriteCommand.__init__。

            
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
            self.target = target
            self._apply_fn = apply_fn
            self._rollback_fn = rollback_fn
            self.description = desc

        def execute(self) -> None:
            """_PropertyWriteCommand.execute。

            
                职责:
                    执行本函数声明的对外行为（见实现）。
            
                时机:
                    由调用方在对应生命周期内调用。
            
                不变量:
                    不破坏模块顶 docstring 与同级契约。
            
                排错:
                    异常时见本文件模块说明与子树 README 排错表。
            """
            self._apply_fn(self.target)

        def undo(self) -> None:
            """_PropertyWriteCommand.undo。

            
                职责:
                    执行本函数声明的对外行为（见实现）。
            
                时机:
                    由调用方在对应生命周期内调用。
            
                不变量:
                    不破坏模块顶 docstring 与同级契约。
            
                排错:
                    异常时见本文件模块说明与子树 README 排错表。
            """
            self._rollback_fn(self.target)

    def _on_selection_changed(self, objects: List[Any]):
        """选中对象变化处理"""
        if objects:
            self.update_properties(objects[0] if len(objects) == 1 else objects)
        else:
            self._clear_properties()

    def _on_project_opened(self, _data):
        """换项目时清空检视器，避免仍显示上一项目的实体属性。"""
        self._selected_objects = []
        self._clear_properties()

    def _on_language_changed(self, _data):
        self.title_label.setText(self._t("inspector.title", "检视器"))
        if not self._selected_objects:
            self.status_label.setText(self._t("inspector.status.no_selection", "未选择对象"))

    def _clear_properties(self):
        """清空属性面板"""
        # 清除所有属性组
        while self.properties_layout.count() > 1:  # 保留stretch
            item = self.properties_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        self._property_controls.clear()
        self._property_groups.clear()
        self._selected_objects.clear()
        self.status_label.setText(self._t("inspector.status.no_selection", "未选择对象"))

    def clear_properties(self):
        """清空属性面板内容（公共方法）。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._clear_properties()

    def update_properties(self, selected_object: Any):
        """更新属性面板内容。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self._clear_properties()
        
        if not selected_object:
            return
        
        # 处理多对象选择
        if isinstance(selected_object, list):
            if len(selected_object) == 0:
                return
            elif len(selected_object) == 1:
                selected_object = selected_object[0]
            else:
                self._update_multi_selection(selected_object)
                return
        
        self._selected_objects = [selected_object]
        
        # 更新状态标签
        obj_type = getattr(selected_object, 'type', selected_object.__class__.__name__)
        obj_id = getattr(selected_object, 'id', self._t("inspector.unknown", "未知"))
        self.status_label.setText(f"{obj_type}: {obj_id}")
        
        # 根据对象类型显示属性（完全参考Unity的Inspector）
        # 检查是否是字典（从Hierarchy传来的实体数据）
        if isinstance(selected_object, dict):
            obj_type = selected_object.get('type')
            if obj_type == 'entity':
                # 实体：显示脚本和属性
                self._add_entity_inspector(selected_object)
            elif obj_type == 'pond':
                # Pond：显示Pond属性
                self._add_pond_inspector(selected_object)
            else:
                self._add_node_properties(selected_object)
        elif hasattr(selected_object, "id"):
            # 检查是否是实体对象（EntityBase的子类）
            from core.Lotucosm.entity import EntityBase
            if isinstance(selected_object, EntityBase):
                # 实体属性（不仅仅是节点）
                self._add_entity_properties(selected_object)
            else:
                # 节点属性
                self._add_node_properties(selected_object)
        elif hasattr(selected_object, "start_node") and hasattr(selected_object, "end_node"):
            # 连接线属性
            self._add_connection_properties(selected_object)
        elif hasattr(selected_object, "components"):
            # 组件容器（如Organism）
            self._add_entity_properties(selected_object)

    def _update_multi_selection(self, objects: List[Any]):
        """更新多对象选择"""
        self._selected_objects = objects
        self.status_label.setText(
            self._t("inspector.status.multi_selected", "已选择 {count} 个对象").format(count=len(objects))
        )
        
        # 创建通用属性组
        general_group = self._get_or_create_group(self._t("inspector.group.general", "通用"))
        
        # 显示"Mixed Values"提示
        mixed_label = QLabel(self._t("inspector.multi_select_hint", "多个对象已选中 - 某些属性可能显示为混合值"))
        mixed_label.setStyleSheet("color: #888888; font-style: italic; padding: 8px;")
        general_group.layout().addWidget(mixed_label)
        
        # 只显示所有对象共有的属性
        common_props = self._get_common_properties(objects)
        for prop_name, prop_value in common_props.items():
            self._add_property_field(general_group, prop_name, prop_value, objects)

    def _get_common_properties(self, objects: List[Any]) -> Dict[str, Any]:
        """获取所有对象的共同属性"""
        if not objects:
            return {}
        
        # 获取第一个对象的所有属性
        first_obj = objects[0]
        common_props = {}
        
        # 检查所有对象是否都有这些属性
        for attr in ['id', 'type', 'x', 'y']:
            if all(hasattr(obj, attr) for obj in objects):
                values = [getattr(obj, attr) for obj in objects]
                # 如果所有值相同，使用该值；否则标记为混合
                if len(set(values)) == 1:
                    common_props[attr] = values[0]
                else:
                    common_props[attr] = self._t("inspector.mixed_values", "混合值")
        
        return common_props

    def _add_node_properties(self, node: Any):
        """添加节点属性"""
        # 通用属性组
        general_group = self._get_or_create_group(self._t("inspector.group.general", "通用"))
        self._add_property_field(
            general_group,
            self._t("inspector.field.id", "ID"),
            getattr(node, "id", "-"),
            [node],
            readonly=True,
        )
        self._add_property_field(
            general_group,
            self._t("inspector.field.type", "类型"),
            getattr(node, "type", "-"),
            [node],
            readonly=True,
        )
        
        # Transform组
        transform_group = self._get_or_create_group(self._t("inspector.group.transform", "变换"))
        if hasattr(node, 'x') and hasattr(node, 'y'):
            self._add_property_field(transform_group, self._t("inspector.field.x", "X"), node.x, [node], prop_type=float)
            self._add_property_field(transform_group, self._t("inspector.field.y", "Y"), node.y, [node], prop_type=float)
        
        # Size组
        if hasattr(node, 'radius'):
            size_group = self._get_or_create_group(self._t("inspector.group.size", "尺寸"))
            self._add_property_field(
                size_group,
                self._t("inspector.field.radius", "半径"),
                node.radius,
                [node],
                prop_type=int,
                min_val=10,
                max_val=100,
            )
            
        # 脚本组（嵌套 dict 展开；可选 SR_INSPECTOR_SCHEMA 分组）
        if hasattr(node, 'scripts') and node.scripts:
            scripts_dir = self._project_scripts_directory()
            for script_data in node.scripts:
                script_name = script_data.get('name', self._t("inspector.unknown_script", "未知脚本"))
                script_group = self._get_or_create_group(script_name)
                script_props = script_data.get('properties', {}) or {}
                norm = spe.normalize_script_properties_dict(script_props)
                for row in spe.inspector_rows_for_script(script_name, norm, scripts_dir):
                    disp = (
                        row["label"]
                        if row["group"] == script_name
                        else f'{row["group"]} › {row["label"]}'
                    )
                    extra: Dict[str, Any] = {}
                    if row["prop_type"] == float:
                        extra["min_val"] = row.get("min_val") if row.get("min_val") is not None else -1e9
                        extra["max_val"] = row.get("max_val") if row.get("max_val") is not None else 1e9
                        extra["step"] = row.get("step") if row.get("step") is not None else 0.01
                    self._add_property_field(
                        script_group,
                        disp,
                        row["value"],
                        [node],
                        prop_name=spe.inspector_key_for_script_field(script_name, row["path"]),
                        prop_type=row["prop_type"],
                        **extra,
                    )
        else:
            # 如果没有脚本，显示提示
            no_scripts_group = self._get_or_create_group(self._t("inspector.group.scripts", "脚本"))
            no_scripts_label = QLabel(self._t("inspector.no_scripts", "没有附加脚本"))
            no_scripts_label.setStyleSheet("color: #888888; font-style: italic; padding: 8px;")
            no_scripts_group.layout().addWidget(no_scripts_label)

        # 添加 Add Component 按钮
        self._add_component_button(node)

    def _add_entity_inspector(self, entity_data: Dict):
        """添加实体Inspector（完全参考Unity，显示脚本和属性）"""
        entity_info = entity_data.get('data', entity_data)
        entity_id = entity_info.get('id', self._t("inspector.unknown", "未知"))
        entity_name = entity_info.get('name', entity_id)
        
        # 更新状态标签
        self.status_label.setText(self._t("inspector.status.entity", "实体: {name}").format(name=entity_name))
        
        # Transform组（Unity风格）
        transform_group = self._get_or_create_group(self._t("inspector.group.transform", "变换"))
        position = entity_info.get('position', [0, 0])
        self._add_property_field(transform_group, self._t("inspector.field.position_x", "位置 X"), position[0] if len(position) > 0 else 0, [entity_data], prop_name="position_x", prop_type=float)
        self._add_property_field(transform_group, self._t("inspector.field.position_y", "位置 Y"), position[1] if len(position) > 1 else 0, [entity_data], prop_name="position_y", prop_type=float)
        
        # 脚本列表
        scripts = entity_info.get('scripts', [])
        # 尝试从运行时实体获取脚本 (如果是实际对象)
        if hasattr(entity_info, 'scripts'):
            for script in getattr(entity_info, 'scripts'):
                self._add_script_to_inspector(script)
        elif scripts:
            for script_data in scripts:
                script_name = script_data.get('name', self._t("inspector.unknown_script", "未知脚本"))
                script_group = self._get_or_create_group(script_name)
                
                # 显示脚本的属性
                script_props = script_data.get('properties', {}) or {}
                norm = spe.normalize_script_properties_dict(script_props)
                scripts_dir = self._project_scripts_directory()
                for row in spe.inspector_rows_for_script(script_name, norm, scripts_dir):
                    disp = (
                        row["label"]
                        if row["group"] == script_name
                        else f'{row["group"]} › {row["label"]}'
                    )
                    extra: Dict[str, Any] = {}
                    if row["prop_type"] == float:
                        extra["min_val"] = row.get("min_val") if row.get("min_val") is not None else -1e9
                        extra["max_val"] = row.get("max_val") if row.get("max_val") is not None else 1e9
                        extra["step"] = row.get("step") if row.get("step") is not None else 0.01
                    self._add_property_field(
                        script_group,
                        disp,
                        row["value"],
                        [entity_data],
                        prop_name=spe.inspector_key_for_script_field(script_name, row["path"]),
                        prop_type=row["prop_type"],
                        **extra,
                    )
        else:
            # 如果没有脚本，显示提示
            no_scripts_group = self._get_or_create_group(self._t("inspector.group.scripts", "脚本"))
            from PyQt6.QtWidgets import QLabel
            no_scripts_label = QLabel(self._t("inspector.no_scripts_hint", "没有附加脚本\n\n点击“添加组件”添加脚本"))
            no_scripts_label.setStyleSheet("color: #888888; font-style: italic; padding: 8px;")
            no_scripts_group.layout().addWidget(no_scripts_label)
        
        # 添加并显示 Add Component 按钮
        self._add_component_button(entity_data)

    def _add_script_to_inspector(self, script: Any):
        """将单个脚本实例添加到 Inspector 显示"""
        script_name = script.component_type if hasattr(script, 'component_type') else script.__class__.__name__
        script_group = self._get_or_create_group(script_name)
        
        if hasattr(script, 'get_inspectable_properties'):
            props = script.get_inspectable_properties()
            for prop_name, prop_info in props.items():
                val = prop_info['value']
                p_type = prop_info['type']
                attrs = prop_info['attributes']
                self._add_property_field(
                    script_group, prop_name, val, [script], 
                    prop_name=prop_name, prop_type=p_type,
                    min_val=attrs.get('min'), max_val=attrs.get('max'),
                    step=attrs.get('step'), readonly=attrs.get('readonly', False)
                )
        else:
            # 备选：显示所有不是以 _ 开头的属性
            for attr in dir(script):
                if not attr.startswith('_') and not callable(getattr(script, attr)):
                    val = getattr(script, attr)
                    if isinstance(val, (int, float, bool, str)):
                        self._add_property_field(script_group, attr, val, [script], prop_name=attr, prop_type=type(val))

    def _add_component_button(self, target: Any):
        """添加 'Add Component' 按钮"""
        add_component_group = self._get_or_create_group(self._t("inspector.add_component.group", "添加组件"))
        from PyQt6.QtWidgets import QPushButton
        add_script_btn = QPushButton(self._t("inspector.add_component.button", "添加组件"))
        add_script_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        add_script_btn.clicked.connect(lambda: self._show_add_script_dialog(target))  # type: ignore
        add_component_group.layout().addWidget(add_script_btn)


    def _scene_snapshot_for_pond(self, pond_data: Dict) -> Optional[Dict]:
        """当前内存场景或磁盘 .pond 的快照，用于展示 pond_config 等。"""
        path = pond_data.get("path")
        if not path:
            return None
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            sm = get_scene_manager()
            cur = sm.get_current_scene_path()
            if cur and os.path.normpath(cur) == os.path.normpath(path):
                return sm.get_scene_data()
            if isinstance(path, str) and path.endswith(".pond") and os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as exc:
            logger.warning("读取莲池场景快照失败: %s", exc)
        return None

    def _add_pond_inspector(self, pond_data: Dict):
        """添加Pond Inspector（名称可编辑；其余优先只读展示场景/pond_config）。"""
        pond_name = pond_data.get('name', self._t("inspector.unknown", "未知"))
        self.status_label.setText(self._t("inspector.status.pond", "池塘: {name}").format(name=pond_name))

        snapshot = self._scene_snapshot_for_pond(pond_data)

        # Pond属性组
        pond_group = self._get_or_create_group(self._t("inspector.group.pond_settings", "池塘设置"))
        self._add_property_field(
            pond_group,
            self._t("inspector.field.name", "名称"),
            pond_name,
            [pond_data],
            prop_name="name",
            prop_type=str,
        )

        meta_group = self._get_or_create_group(self._t("inspector.group.scene_meta", "场景信息"))
        pth = pond_data.get("path")
        if pth:
            self._add_property_field(
                meta_group,
                self._t("inspector.field.scene_path", "场景路径"),
                str(pth),
                [pond_data],
                readonly=True,
            )
        if snapshot:
            ver = snapshot.get("version")
            if ver is not None and ver != "":
                self._add_property_field(
                    meta_group,
                    self._t("inspector.field.version", "版本"),
                    str(ver),
                    [snapshot],
                    readonly=True,
                )
            modified = snapshot.get("modified_at")
            if modified:
                self._add_property_field(
                    meta_group,
                    self._t("inspector.field.modified_at", "修改时间"),
                    str(modified),
                    [snapshot],
                    readonly=True,
                )

        pond_cfg = (snapshot or {}).get("pond_config") or {}
        if pond_cfg:
            cfg_group = self._get_or_create_group(self._t("inspector.group.pond_config", "莲池配置"))
            cn = pond_cfg.get("name")
            if cn:
                self._add_property_field(
                    cfg_group,
                    self._t("inspector.field.pond_config_name", "配置名称"),
                    str(cn),
                    [pond_cfg],
                    readonly=True,
                )
            sz = pond_cfg.get("size")
            if isinstance(sz, (list, tuple)) and len(sz) >= 2:
                self._add_property_field(
                    cfg_group,
                    self._t("inspector.field.pond_width", "宽度"),
                    float(sz[0]),
                    [pond_cfg],
                    readonly=True,
                )
                self._add_property_field(
                    cfg_group,
                    self._t("inspector.field.pond_height", "高度"),
                    float(sz[1]),
                    [pond_cfg],
                    readonly=True,
                )
            for key, label_key, default_label in (
                ("initial_components", "inspector.field.initial_components", "初始组件数"),
                ("initial_organisms", "inspector.field.initial_organisms", "初始生物体数"),
            ):
                if key in pond_cfg:
                    self._add_property_field(
                        cfg_group,
                        self._t(label_key, default_label),
                        int(pond_cfg[key]),
                        [pond_cfg],
                        readonly=True,
                    )
    
    def _add_entity_properties(self, entity: Any):
        """添加实体属性（参考Unity的Inspector，支持编辑实体）"""
        # 通用属性组
        general_group = self._get_or_create_group(self._t("inspector.group.general", "通用"))
        self._add_property_field(
            general_group,
            self._t("inspector.field.id", "ID"),
            getattr(entity, "id", "-"),
            [entity],
            readonly=True,
        )
        self._add_property_field(
            general_group,
            self._t("inspector.field.type", "类型"),
            getattr(entity, "entity_type", getattr(entity, "type", "-")),
            [entity],
            readonly=True,
        )
        
        # Transform组
        transform_group = self._get_or_create_group(self._t("inspector.group.transform", "变换"))
        if hasattr(entity, 'position'):
            pos = entity.position
            self._add_property_field(
                transform_group,
                self._t("inspector.field.x", "X"),
                float(pos[0]),
                [entity],
                prop_name="position_x",
                prop_type=float,
            )
            self._add_property_field(
                transform_group,
                self._t("inspector.field.y", "Y"),
                float(pos[1]),
                [entity],
                prop_name="position_y",
                prop_type=float,
            )
        
        # 显示所有附加脚本
        if hasattr(entity, 'scripts'):
            for script in entity.scripts:
                self._add_script_to_inspector(script)
        
        # 添加 Add Component 按钮
        self._add_component_button(entity)

        # 传统的组件列表 (用于向后兼容)
        if hasattr(entity, 'components') and isinstance(entity.components, dict) and not hasattr(entity, 'scripts'):
            components_group = self._get_or_create_group(self._t("inspector.group.components_legacy", "组件（旧版）"))
            for comp_id, component in entity.components.items():
                comp_name = getattr(component, 'type', type(component).__name__)
                self._add_property_field(
                    components_group,
                    self._t("inspector.field.component", "组件: {name}").format(name=comp_name),
                    comp_id,
                    [entity],
                    readonly=True,
                )
    
    def _add_connection_properties(self, connection: Any):
        """添加连接属性"""
        # 通用属性组
        general_group = self._get_or_create_group(self._t("inspector.group.general", "通用"))
        self._add_property_field(
            general_group,
            self._t("inspector.field.source_node", "源节点"),
            getattr(connection.start_node, "id", "-"),
            [connection],
            readonly=True,
        )
        self._add_property_field(
            general_group,
            self._t("inspector.field.target_node", "目标节点"),
            getattr(connection.end_node, "id", "-"),
            [connection],
            readonly=True,
        )
        
        # Connection组
        connection_group = self._get_or_create_group(self._t("inspector.group.connection", "连接"))
        if hasattr(connection, 'weight'):
            self._add_property_field(
                connection_group,
                self._t("inspector.field.weight", "权重"),
                connection.weight,
                [connection],
                prop_type=float,
                min_val=-5.0,
                max_val=5.0,
                step=0.1,
            )
    
    def _show_add_component_dialog(self, entity: Any):
        """显示添加组件对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("inspector.add_component.dialog_title", "添加组件"))
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        # 组件类型选择
        type_label = QLabel(self._t("inspector.add_component.component_type", "组件类型:"))
        type_combo = QComboBox()
        
        # 从Project面板获取组件列表
        try:
            if hasattr(self.editor_context, 'kernel'):
                kernel = self.editor_context.kernel
                if kernel and hasattr(kernel, 'layout_manager'):
                    # 尝试从Project面板获取组件列表
                    project_dock = kernel.layout_manager.docks.get("Project")
                    if project_dock and hasattr(project_dock, 'widget'):
                        project_panel = project_dock.widget()
                        if hasattr(project_panel, '_component_categories'):
                            for category, components in project_panel._component_categories.items():
                                for comp in components:
                                    comp_name = comp.get('name', self._t("inspector.unknown", "未知"))
                                    type_combo.addItem(f"[{category}] {comp_name}", comp)
        except Exception as e:
            logger.warning("加载组件列表失败: %s", e)
        
        layout.addWidget(type_label)
        layout.addWidget(type_combo)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)  # type: ignore
        buttons.rejected.connect(dialog.reject)  # type: ignore
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_index = type_combo.currentIndex()
            comp_data = type_combo.itemData(selected_index)
            if comp_data:
                # 由 SceneViewportPlugin.on_add_component 写入场景实体（与添加脚本同一管线）
                logger.info("添加组件到实体: %s", comp_data.get("name", self._t("inspector.unknown", "未知")))
                self.editor_context.event_bus.publish("add_component_to_entity", {
                    'entity': entity,
                    'component_type': comp_data.get('name'),
                    'component_data': comp_data
                })
    
    def _show_add_script_dialog(self, entity_data: Dict):
        """显示添加脚本对话框（Unity风格）"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("inspector.add_component.dialog_title", "添加组件"))
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 脚本类型选择
        type_label = QLabel(self._t("inspector.add_component.script_label", "脚本:"))
        type_combo = QComboBox()
        type_combo.setEditable(True)  # 允许搜索
        
        # 从项目资源加载脚本列表
        try:
            if hasattr(self.editor_context, 'kernel'):
                kernel = self.editor_context.kernel
                if kernel and hasattr(kernel, 'layout_manager'):
                    # 尝试从Project面板获取脚本列表
                    project_dock = kernel.layout_manager.docks.get("Project")
                    if project_dock and hasattr(project_dock, 'widget'):
                        project_panel = project_dock.widget()
                        # 从项目路径加载脚本
                        if hasattr(project_panel, 'current_project_path') and project_panel.current_project_path:
                            project_path = project_panel.current_project_path
                            # 递归搜索项目目录下所有的 .py 文件
                            for root, dirs, files in os.walk(project_path):
                                # 跳过隐藏目录
                                dirs[:] = [d for d in dirs if not d.startswith('.')]
                                for file in files:
                                    if file.endswith(".py") and file != "project.json":
                                        script_name = file[:-3]
                                        full_path = os.path.join(root, file)
                                        # 计算相对路径以便显示
                                        rel_path = os.path.relpath(full_path, project_path)
                                        type_combo.addItem(f"{script_name} ({rel_path})", {'name': script_name, 'path': full_path})
        except Exception as e:
            logger.warning("加载脚本列表失败: %s", e)
        
        # 添加默认脚本类型
        default_scripts = [
            self._t("inspector.default_script.transform", "Transform"),
            self._t("inspector.default_script.rigidbody", "Rigidbody"),
            self._t("inspector.default_script.collider", "Collider"),
            self._t("inspector.default_script.renderer", "Renderer"),
            self._t("inspector.default_script.sensor", "SensorScript"),
            self._t("inspector.default_script.actuator", "ActuatorScript"),
            self._t("inspector.default_script.brain", "BrainScript"),
        ]
        for script_name in default_scripts:
            if type_combo.findText(script_name) == -1:
                type_combo.addItem(script_name, {'name': script_name, 'path': None})
        
        layout.addWidget(type_label)
        layout.addWidget(type_combo)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)  # type: ignore
        buttons.rejected.connect(dialog.reject)  # type: ignore
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_index = type_combo.currentIndex()
            script_data = type_combo.itemData(selected_index)
            
            # 如果没有选中预设，但输入了文字，则作为新脚本（可能未创建文件）
            if not script_data and type_combo.currentText():
                script_name = type_combo.currentText()
                script_data = {'name': script_name, 'path': None}
                
            if script_data:
                # 通过事件总线发送添加脚本事件
                self.editor_context.event_bus.publish("add_script_to_entity", {
                    'entity': entity_data,
                    'script': script_data
                })
                logger.info("添加脚本到实体: %s", script_data.get("name", self._t("inspector.unknown", "未知")))

    def dragEnterEvent(self, event):
        """处理拖入事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # 只要有一个是 .py 或者是图片（未来支持图片拖入作为 SpriteRenderer）
            if any(url.toLocalFile().lower().endswith(('.py', '.png', '.jpg', '.jpeg')) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event):
        """处理删除事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if not os.path.exists(file_path):
                continue
                
            if file_path.lower().endswith('.py'):
                script_name = os.path.basename(file_path)[:-3]
                script_data = {'name': script_name, 'path': file_path}
                
                # 为所有选中的对象添加脚本
                for obj in self._selected_objects:
                    self.editor_context.event_bus.publish("add_script_to_entity", {
                        'entity': obj,
                        'script': script_data
                    })
                logger.info("拖入脚本并应用到选定实体: %s", script_name)
            
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif')):
                abs_path = os.path.normpath(os.path.abspath(file_path))
                proj = getattr(self.editor_context, "current_project_path", None)
                store_path = abs_path
                if proj:
                    try:
                        store_path = os.path.relpath(abs_path, proj).replace("\\", "/")
                    except ValueError:
                        store_path = abs_path
                for obj in self._selected_objects:
                    self.editor_context.event_bus.publish(
                        "set_entity_sprite_path",
                        {"entity": obj, "sprite_path": store_path},
                    )
                logger.info("拖入图片并设置 sprite_path: %s", store_path)

    def _is_mixed_property_value(self, value: Any) -> bool:
        """脚本等嵌套 dict 不能放入 set 做 `in` 检测（不可哈希），须用相等比较。"""
        if value == "Mixed Values":
            return True
        try:
            return value == self._t("inspector.mixed_values", "混合值")
        except Exception:
            return False

    def _format_inspector_json(self, value: Any) -> str:
        """场景脚本里 dict/list 用缩进 JSON 展示，避免单行 `{'a': ...}` 难以阅读。"""
        try:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        except (TypeError, ValueError):
            return str(value)

    def _project_scripts_directory(self) -> Optional[str]:
        proj = getattr(self.editor_context, "current_project_path", None)
        if not proj:
            return None
        return os.path.join(proj, "scripts")

    def _get_or_create_group(self, group_name: str) -> FoldoutGroup:
        """获取或创建属性组"""
        if group_name not in self._property_groups:
            group = FoldoutGroup(group_name)
            group.setLayout(QFormLayout())
            self._property_groups[group_name] = group
            self.properties_layout.insertWidget(self.properties_layout.count() - 1, group)
        return self._property_groups[group_name]

    def _add_property_field(
        self,
        group: FoldoutGroup,
        label: str,
        value: Any,
        objects: List[Any],
        prop_name: Optional[str] = None,
        prop_type: type = str,
        readonly: bool = False,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        step: Optional[float] = None
    ):
        """添加属性字段"""
        if prop_name is None:
            prop_name = label.lower().replace(' ', '_')
        
        layout = group.layout()
        if not isinstance(layout, QFormLayout):
            return

        # dict / list：用只读 JSON 块展示（.pond 本质为 JSON；与 Unity 检视器「序列化对象」类似但先只读）
        if isinstance(value, (dict, list)) and not self._is_mixed_property_value(value):
            jtxt = self._format_inspector_json(value)
            widget = QPlainTextEdit(jtxt)
            widget.setReadOnly(True)
            widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            lines = max(4, min(18, jtxt.count("\n") + 1))
            widget.setFixedHeight(14 * lines + 24)
            widget.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 6px;
                    color: #c8c8c8;
                    font-family: Consolas, 'Cascadia Mono', monospace;
                    font-size: 11px;
                }
            """)
            row_title = f"{label}"
            hint = self._t(
                "inspector.field.json_readonly_hint",
                "（结构化 JSON，只读；请在场景文件或后续专用编辑器中修改）",
            )
            layout.addRow(row_title, widget)
            hint_lab = QLabel(hint)
            hint_lab.setStyleSheet("color: #888888; font-size: 10px;")
            hint_lab.setWordWrap(True)
            layout.addRow(hint_lab)
            self._property_controls[prop_name] = widget
            return
        
        # 根据类型创建控件
        if readonly or prop_type == str:
            # 只读文本或字符串
            widget = QLineEdit(str(value))
            widget.setReadOnly(readonly)
            widget.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 4px;
                    color: #d4d4d4;
                }
                QLineEdit:read-only {
                    background-color: #2d2d2d;
                    color: #888888;
                }
            """)
            if not readonly:
                widget.editingFinished.connect(  # type: ignore
                    lambda p=prop_name, w=widget, objs=objects: self._on_text_property_changed(p, w, objs)
                )
        elif prop_type == int:
            # 整数
            widget = QSpinBox()
            if min_val is not None:
                widget.setMinimum(int(min_val))
            if max_val is not None:
                widget.setMaximum(int(max_val))
            widget.setValue(int(value) if value != "Mixed Values" else 0)
            widget.setStyleSheet("""
                QSpinBox {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 4px;
                    color: #d4d4d4;
                }
            """)
            if not readonly:
                widget.valueChanged.connect(lambda v: self._on_property_changed(prop_name, v, objects))  # type: ignore
        elif prop_type == float:
            # 浮点数
            widget = QDoubleSpinBox()
            if min_val is not None:
                widget.setMinimum(min_val)
            if max_val is not None:
                widget.setMaximum(max_val)
            if step is not None:
                widget.setSingleStep(step)
            widget.setValue(float(value) if value != "Mixed Values" else 0.0)
            widget.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 4px;
                    color: #d4d4d4;
                }
            """)
            if not readonly:
                widget.valueChanged.connect(lambda v: self._on_property_changed(prop_name, v, objects))  # type: ignore
        elif prop_type == bool:
            # 布尔值
            widget = QCheckBox()
            widget.setChecked(bool(value) if value != "Mixed Values" else False)
            widget.setStyleSheet("""
                QCheckBox {
                    color: #d4d4d4;
                }
            """)
            if not readonly:
                widget.toggled.connect(lambda v: self._on_property_changed(prop_name, v, objects))  # type: ignore
        else:
            # 默认文本
            widget = QLineEdit(str(value))
            widget.setReadOnly(readonly)
        
        # 如果值是混合值，特殊处理（勿用 value in {…}：value 为 dict 时会触发不可哈希 TypeError）
        if self._is_mixed_property_value(value):
            if hasattr(widget, 'setSpecialValueText'):
                widget.setSpecialValueText(self._t("inspector.mixed_short", "混合"))
            elif hasattr(widget, 'setPlaceholderText'):
                widget.setPlaceholderText(self._t("inspector.mixed_values", "混合值"))
        
        layout.addRow(f"{label}:", widget)
        self._property_controls[prop_name] = widget

    def _on_text_property_changed(self, prop_name: str, widget: QLineEdit, objects: List[Any]):
        """处理字符串字段提交，避免 textChanged 产生高频写回。"""
        self._on_property_changed(prop_name, widget.text(), objects)

    def _sync_scene_entity_data(self, obj: Any, prop_name: str, new_value: Any):
        """将 Inspector 修改同步到 SceneManager 的 entities 数据。"""
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            entity_id = spe.entity_id_from_inspector_obj(obj)
            if not entity_id:
                return

            if prop_name.startswith("script_"):
                spe.apply_entity_script_property_to_scene(entity_id, prop_name, new_value)
                return

            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if not scene_data:
                return

            entities = scene_data.get("entities", [])
            for entity in entities:
                if entity.get("id") != entity_id:
                    continue

                if prop_name == "position_x":
                    pos = entity.get("position", [0, 0])
                    if not isinstance(pos, list):
                        pos = list(pos) if isinstance(pos, (tuple, list)) else [0, 0]
                    while len(pos) < 2:
                        pos.append(0)
                    pos[0] = float(new_value)
                    entity["position"] = pos
                elif prop_name == "position_y":
                    pos = entity.get("position", [0, 0])
                    if not isinstance(pos, list):
                        pos = list(pos) if isinstance(pos, (tuple, list)) else [0, 0]
                    while len(pos) < 2:
                        pos.append(0)
                    pos[1] = float(new_value)
                    entity["position"] = pos
                else:
                    entity[prop_name] = new_value
                break

            sm.update_scene_data({"entities": entities})
        except Exception as e:
            logger.warning("同步场景实体数据失败: %s", e)

    def _build_property_command(self, obj: Any, prop_name: str, new_value: Any) -> Optional[Command]:
        """根据对象与字段构建可撤销命令。"""
        # 连接线沿用原有命令
        if hasattr(obj, "start_node") and hasattr(obj, "end_node") and hasattr(obj, prop_name):
            old_value = getattr(obj, prop_name)
            return ModifyConnectionPropertyCommand(obj, prop_name, old_value, new_value)

        # Node 的 x/y 直接沿用原有命令
        if hasattr(obj, prop_name) and prop_name in {"x", "y", "radius", "name"}:
            old_value = getattr(obj, prop_name)
            return ModifyNodePropertyCommand(obj, prop_name, old_value, new_value)

        # position_x / position_y 适配到 position 或 x/y
        if prop_name in {"position_x", "position_y"}:
            axis = 0 if prop_name == "position_x" else 1

            if hasattr(obj, "position"):
                old_pos = list(getattr(obj, "position"))
                new_pos = old_pos.copy()
                while len(new_pos) < 2:
                    new_pos.append(0.0)
                new_pos[axis] = float(new_value)
                desc = self._t("inspector.command.modify_position_axis", "修改 position[{axis}]").format(axis=axis)
                return self._PropertyWriteCommand(
                    obj,
                    lambda target: setattr(target, "position", tuple(new_pos) if isinstance(getattr(target, "position"), tuple) else new_pos),
                    lambda target: setattr(target, "position", tuple(old_pos) if isinstance(getattr(target, "position"), tuple) else old_pos),
                    desc,
                )

            if hasattr(obj, "x") and hasattr(obj, "y"):
                attr_name = "x" if axis == 0 else "y"
                old_value = getattr(obj, attr_name)
                return ModifyNodePropertyCommand(obj, attr_name, old_value, float(new_value))

            if isinstance(obj, dict):
                old_pos = list(obj.get("position", [0.0, 0.0]))
                while len(old_pos) < 2:
                    old_pos.append(0.0)
                new_pos = old_pos.copy()
                new_pos[axis] = float(new_value)
                return self._PropertyWriteCommand(
                    obj,
                    lambda target: target.__setitem__("position", new_pos),
                    lambda target: target.__setitem__("position", old_pos),
                    self._t("inspector.command.modify_dict_position_axis", "修改字典 position[{axis}]").format(axis=axis),
                )

        # 脚本字段 script_<脚本名>_<点分路径>：写回 scripts[].properties（场景节点与实体字典）
        if prop_name.startswith("script_"):
            holder = spe.scripts_holder(obj)
            if holder is None:
                holder = obj
            names = spe.script_names_from_holder(holder)
            parsed = spe.parse_script_inspector_key(prop_name, names)
            if parsed:
                script_name, dotted_path = parsed
                old_scalar = None
                scripts_list = getattr(holder, "scripts", None)
                if scripts_list is None and isinstance(holder, dict):
                    scripts_list = holder.get("scripts")
                if isinstance(scripts_list, list):
                    for sd in scripts_list:
                        if isinstance(sd, dict) and sd.get("name") == script_name:
                            props = sd.setdefault("properties", {})
                            if isinstance(props, dict):
                                old_scalar = spe.nested_get(props, dotted_path)
                            break
                coerced = spe.coerce_script_property_update(old_scalar, new_value)
                snap = spe.snapshot_scripts(holder)
                sn, dp, cv = script_name, dotted_path, coerced

                def _touch_canvas(target: Any) -> None:
                    if hasattr(target, "canvas") and hasattr(target.canvas, "update_visualization"):
                        target.canvas.update_visualization()

                def apply_fn(target: Any) -> None:
                    h = spe.scripts_holder(target)
                    if h is None:
                        h = target
                    spe.apply_script_property_to_holder(h, sn, dp, cv)
                    _touch_canvas(target)

                def rollback_fn(target: Any) -> None:
                    h = spe.scripts_holder(target)
                    if h is None:
                        h = target
                    spe.restore_scripts(h, snap)
                    _touch_canvas(target)

                return self._PropertyWriteCommand(
                    obj,
                    apply_fn,
                    rollback_fn,
                    self._t("inspector.command.modify_script_field", "修改脚本字段 {field}").format(
                        field=prop_name
                    ),
                )

        # 通用对象属性
        if hasattr(obj, prop_name):
            old_value = getattr(obj, prop_name)
            return ModifyNodePropertyCommand(obj, prop_name, old_value, new_value)

        # 通用字典字段
        if isinstance(obj, dict):
            old_value = obj.get(prop_name)
            return self._PropertyWriteCommand(
                obj,
                lambda target: target.__setitem__(prop_name, new_value),
                lambda target: target.__setitem__(prop_name, old_value),
                self._t("inspector.command.modify_dict_field", "修改字典字段 {field}").format(field=prop_name),
            )

        return None

    def _on_property_changed(self, prop_name: str, new_value: Any, objects: List[Any]):
        """属性变化处理"""
        if not objects:
            return

        changed = False
        for obj in objects:
            command = self._build_property_command(obj, prop_name, new_value)
            if command is not None:
                self.command_stack.execute(command)
                changed = True
                self._sync_scene_entity_data(obj, prop_name, new_value)

        if not changed:
            return

        # 通知项目已修改
        self.projectModified.emit()
        self.commandExecuted.emit()
        self.signal_bus.emit_object_modified(objects[0] if objects else None, {prop_name: new_value})


# 为了向后兼容，保留PropertyPanel作为别名
PropertyPanel = InspectorPanel
