# -*- coding: utf-8 -*-
"""场景编辑视口：节点图、连线、命令栈与 .pond 数据双向同步。

架构数据流::

    load_scene_data ← SceneManager → paintEvent / semantic command history

排错: 见 core/VitaLoom/README.md「场景重载」「撤销」
"""

import os
import re
from typing import List, Optional, Any, Dict
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPaintEvent, QMouseEvent, QWheelEvent, QContextMenuEvent, QKeyEvent
)
from PyQt6.QtWidgets import QWidget, QMenu, QToolBar, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

# 导入节点和连接线类
from core.VitaLoom.tools.selection_tool import Node, ConnectionLine

# 导入命令模式

# 导入编辑器上下文
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus, SignalType
from core.VitaLoom.core.logger import get_logger


logger = get_logger("SceneViewport")


class SceneViewport(QWidget):
    """职责: 编辑模式下的 2D 节点画布（平移/缩放/框选/连线）。
    时机: 由声明式 `viewport_surface` 经 Adapter 投影到 LayoutManager；场景加载后 `load_scene_data`。
    不变量: 修改经 semantic command history；`get_scene_data` 与 SceneManager.save 字段契约一致。
    排错: 空白画布 → scene_loaded 回调；撤销无效 → semantic history 是否 execute。
    """

    # 自定义信号
    updateRequest = pyqtSignal()
    projectModified = pyqtSignal()
    commandExecuted = pyqtSignal()

    def __init__(self):
        """SceneViewport.__init__。

        
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
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # 获取编辑器上下文和信号总线
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        # 父窗口引用
        self.parent_widget: Optional[Any] = None

        # 节点和连接线
        self.nodes: List[Node] = []
        self.connections: List[ConnectionLine] = []

        # 交互状态
        self.selected_node: Optional[Node] = None
        self.selected_nodes: List[Node] = []
        self.hovered_node: Optional[Node] = None
        self.hovered_connection: Optional[ConnectionLine] = None
        self.dragging = False
        self.drag_start = QPoint()
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self._multi_drag_start_positions: Dict[str, tuple[float, float]] = {}
        self.connecting = False
        self.connect_start_node: Optional[Node] = None
        self.connect_temp_pos = QPoint()
        
        # 相机控制状态（参考 Unity/Godot）
        self.panning = False  # 平移状态
        self.pan_start = QPoint()  # 平移起始点
        self.box_selecting = False  # 框选状态
        self.box_select_start = QPoint()  # 框选起始点
        self.box_select_end = QPoint()  # 框选结束点
        
        # 视图状态
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.pan_offset = QPointF(0, 0)
        self.show_grid = True
        self.snap_to_grid = False
        self.grid_size = 20
        self.show_gizmos = True  # 显示操作手柄
        self.show_viewport_info = True  # 显示视口信息

        # 命令栈

        # 顶部工具栏 + 画布区域（stretch 以下为场景绘制区）
        self._toolbar_container = QWidget(self)
        tb_layout = QHBoxLayout(self._toolbar_container)
        tb_layout.setContentsMargins(4, 4, 4, 4)
        self._populate_scene_toolbar(tb_layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._toolbar_container)
        outer.addStretch(1)

        # 连接编辑器上下文信号
        self.editor_context.selection_changed.connect(self._on_context_selection_changed)  # type: ignore
        
        # 不要在这里订阅事件，交由 SceneViewportPlugin 统一管理
        # 这可以避免双重创建或双重加载的问题
        
        # 如果没有场景数据，不要自动创建默认节点（用户要求空白）
        # if not self.nodes:
        #     self._create_default_nodes()
        #     self.update()
        
        # 启用拖拽支持
        self.setAcceptDrops(True)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    @staticmethod
    def _scene_entity_id_from_path(file_name: str) -> str:
        stem = os.path.splitext(os.path.basename(file_name))[0]
        entity_id = re.sub(r"[^0-9A-Za-z_]+", "_", stem).strip("_").lower()
        if not entity_id:
            entity_id = "asset"
        if entity_id[0].isdigit():
            entity_id = f"asset_{entity_id}"
        return entity_id

    @staticmethod
    def _run_scene_placement_command(command_id: str, payload: Dict[str, Any], *, registry: Any = None) -> bool:
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run(command_id, dict(payload))
        if not result.get("ok"):
            logger.warning("场景放置命令失败 %s: %s", command_id, result.get("error"))
            return False
        return True

    @staticmethod
    def _run_scene_entity_create_command(payload: Dict[str, Any], *, registry: Any = None) -> bool:
        return SceneViewport._run_scene_placement_command("entity.create", payload, registry=registry)

    def _apply_scene_prefab_placement(
        self,
        scene_path: str,
        prefab_path: str,
        file_name: str,
        position: List[float],
    ) -> bool:
        """Place one prefab through scene authority and rehydrate only after success.

        A rejected scene-owned placement is terminal at this UI-host boundary: it
        must not publish a legacy create event or attempt a local fallback.
        """
        placed = self._run_scene_placement_command(
            "prefab.place",
            {
                "scene_path": scene_path,
                "prefab_path": prefab_path,
                "entity_id": self._scene_entity_id_from_path(file_name),
                "position": list(position),
            },
        )
        if not placed:
            return False
        self._refresh_scene_after_command(scene_path)
        return True

    def _apply_scene_asset_placement(
        self,
        scene_path: str,
        asset_path: str,
        file_name: str,
        position: List[float],
    ) -> bool:
        """Apply one asset through scene authority and rehydrate only after success.

        A rejected current-scene asset placement is terminal here. Legacy EventBus
        creation remains reserved for the explicitly non-scene/ownerless routes.
        """
        placed = self._run_scene_placement_command(
            "asset.apply_to_scene",
            {
                "scene_path": scene_path,
                "asset_path": asset_path,
                "entity_id": self._scene_entity_id_from_path(file_name),
                "name": file_name,
                "entity_type": "asset",
                "position": list(position),
            },
        )
        if not placed:
            return False
        self._refresh_scene_after_command(scene_path)
        return True

    @staticmethod
    def _run_scene_entity_delete_command(
        payload: Dict[str, Any], *, registry: Any = None
    ) -> dict[str, Any]:
        """Run one durable entity deletion through the Qt-free command authority."""
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run("entity.delete", dict(payload))
        if not result.get("ok"):
            logger.warning("Scene entity delete command failed: %s", result.get("error"))
        return result

    @staticmethod
    def _run_scene_transform_command(payload: Dict[str, Any], *, registry: Any = None) -> dict[str, Any]:
        """Run one durable node-transform mutation through the Qt-free command authority."""
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run("transform.set", dict(payload))
        if not result.get("ok"):
            logger.warning("Scene node transform command failed: %s", result.get("error"))
        return result

    @staticmethod
    def _run_scene_batch_transform_command(payload: Dict[str, Any], *, registry: Any = None) -> dict[str, Any]:
        """Run an atomic multi-node transform through the Qt-free command authority."""
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run("transform.batch_set", dict(payload))
        if not result.get("ok"):
            logger.warning("Scene multi-node transform command failed: %s", result.get("error"))
        return result

    @staticmethod
    def _run_scene_connection_command(
        command_id: str,
        payload: Dict[str, Any],
        *,
        registry: Any = None,
    ) -> dict[str, Any]:
        """Run a JSON-only connection mutation through the runtime command authority."""
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run(command_id, dict(payload))
        if not result.get("ok"):
            logger.warning("Scene connection command failed %s: %s", command_id, result.get("error"))
        return result

    def _own_connection(self, connection: ConnectionLine) -> ConnectionLine:
        """Bind a nonserialized owner witness used only by Inspector semantic routing."""
        connection._vitaloom_owner_viewport = self
        return connection

    def _commit_connection_via_command(
        self,
        command_id: str,
        connection: ConnectionLine,
        *,
        connection_index: Optional[int] = None,
    ) -> bool:
        """Persist one viewport connection and rehydrate from canonical `.pond` on success."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_path = get_scene_manager().get_current_scene_path()
        if not scene_path:
            return False
        payload: Dict[str, Any] = {
            "scene_path": scene_path,
            "connection": connection.to_dict(),
        }
        if connection_index is not None:
            payload["connection_index"] = connection_index
        result = self._run_scene_connection_command(command_id, payload)
        if not result.get("ok"):
            return False
        result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
        self._refresh_scene_after_command(str(result_data.get("scene_path") or scene_path))
        return True

    @staticmethod
    def _run_asset_import_command(payload: Dict[str, Any], *, registry: Any = None) -> dict[str, Any]:
        """Import an external file through the shared asset mutation Authority."""
        if registry is None:
            from core.VitaLoom.commands.registry import get_command_registry

            registry = get_command_registry()
        result = registry.run("asset.import", dict(payload))
        if not result.get("ok"):
            logger.warning("Asset import command failed: %s", result.get("error"))
        return result

    def _refresh_scene_after_command(self, scene_path: str) -> None:
        try:
            from core.VitaLoom.commands.registry import get_command_registry

            result = get_command_registry().run("scene.open", {"scene_path": scene_path})
            if not result.get("ok"):
                logger.warning("命令放置后刷新场景失败: %s", result.get("error"))
        except Exception as exc:
            logger.warning("命令放置后刷新场景失败: %s", exc)


    def _select_rehydrated_nodes(self, node_ids: List[str]) -> List[Node]:
        """Select canonical node instances after ``scene.open`` has rebuilt the viewport."""
        requested = {str(node_id).strip() for node_id in node_ids if str(node_id).strip()}
        selected = [node for node in self.nodes if str(getattr(node, "id", "")) in requested]
        self.selected_nodes = selected
        self.selected_node = selected[0] if selected else None
        if selected:
            self.editor_context.set_selection(selected)
        else:
            self.editor_context.clear_selection()
        return selected

    def _commit_single_node_drag_via_command(
        self,
        node: Node,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> bool:
        """Commit one completed node drag through canonical `.pond` command history.

        Mouse movement remains a transient preview. The release either becomes one
        `transform.set` record or restores the preview to its original coordinate;
        it never writes the same project mutation to the legacy semantic command history.
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_path = get_scene_manager().get_current_scene_path()
        node_id = str(getattr(node, "id", "")).strip()
        if not scene_path or not node_id:
            node.update_position(start_x, start_y)
            return False

        result = self._run_scene_transform_command(
            {
                "scene_path": scene_path,
                "entity_id": node_id,
                "position": [float(end_x), float(end_y)],
            }
        )
        if not result.get("ok"):
            node.update_position(start_x, start_y)
            self.update()
            self.updateRequest.emit()
            return False

        result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
        canonical_scene_path = str(result_data.get("scene_path") or scene_path)
        self._refresh_scene_after_command(canonical_scene_path)
        return True

    def _restore_multi_drag_preview(self, start_positions: Dict[str, tuple[float, float]]) -> None:
        for node in self.selected_nodes:
            node_id = str(getattr(node, "id", "")).strip()
            start_position = start_positions.get(node_id)
            if start_position is not None:
                node.update_position(*start_position)

    def _commit_multi_node_drag_via_command(self, start_positions: Dict[str, tuple[float, float]]) -> bool:
        """Commit one completed multi-node drag as a single atomic semantic mutation."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_path = get_scene_manager().get_current_scene_path()
        transforms: List[Dict[str, Any]] = []
        for node in self.selected_nodes:
            node_id = str(getattr(node, "id", "")).strip()
            start_position = start_positions.get(node_id)
            if not scene_path or not node_id or start_position is None:
                self._restore_multi_drag_preview(start_positions)
                return False
            end_position = [float(node.x), float(node.y)]
            if end_position != [float(start_position[0]), float(start_position[1])]:
                transforms.append({"entity_id": node_id, "position": end_position})
        if not transforms:
            return False

        result = self._run_scene_batch_transform_command(
            {"scene_path": scene_path, "transforms": transforms}
        )
        if not result.get("ok"):
            self._restore_multi_drag_preview(start_positions)
            self.update()
            self.updateRequest.emit()
            return False

        result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
        self._refresh_scene_after_command(str(result_data.get("scene_path") or scene_path))
        return True

    def _run_global_scene_history_command(self, command_id: str) -> bool:
        """Use the global semantic history and rehydrate this viewport from `.pond`."""
        try:
            from core.VitaLoom.commands.registry import get_command_registry

            result = get_command_registry().run(command_id, {})
        except Exception as exc:
            logger.warning("Global scene history command failed %s: %s", command_id, exc)
            return False
        if not result.get("ok"):
            logger.warning("Global scene history command failed %s: %s", command_id, result.get("error"))
            return False

        result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
        scene_path = result_data.get("scene_path")
        if scene_path:
            self._refresh_scene_after_command(str(scene_path))
        return True

    def _create_entity_via_command_or_event(
        self,
        entity_name: str,
        entity_type: str,
        position: List[float],
        *,
        sprite_path: str = "",
        scripts: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        import uuid

        payload = {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "position": position,
        }
        if sprite_path:
            payload["sprite_path"] = sprite_path
        if scripts:
            payload["scripts"] = scripts

        scene_path = get_scene_manager().get_current_scene_path()
        if not scene_path:
            self.editor_context.event_bus.publish("create_entity", payload)
            return True

        entity = {
            "id": f"{self._scene_entity_id_from_path(entity_name or entity_type)}_{uuid.uuid4().hex[:8]}",
            "name": entity_name,
            "type": entity_type,
            "position": position,
            "radius": 16.0,
            "scripts": list(scripts or []),
        }
        if sprite_path:
            entity["sprite_path"] = sprite_path
            entity["sr_visual"] = {"sprite_path": sprite_path}

        placed = self._run_scene_entity_create_command(
            {"scene_path": scene_path, "entity": entity}
        )
        if not placed:
            return False
        self._refresh_scene_after_command(scene_path)
        return True

    def _chrome_top(self) -> int:
        """顶部工具栏占用高度（用于坐标映射与裁剪）。"""
        if hasattr(self, "_toolbar_container") and self._toolbar_container is not None:
            h = self._toolbar_container.height()
            if h > 0:
                return h
            return max(self._toolbar_container.sizeHint().height(), 28)
        return 0

    def _populate_scene_toolbar(self, toolbar_layout: QHBoxLayout) -> None:
        """填充场景视口顶部工具栏。"""
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(lambda: self.set_zoom(self.zoom_level * 1.2))  # type: ignore
        toolbar_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(lambda: self.set_zoom(self.zoom_level * 0.8))  # type: ignore
        toolbar_layout.addWidget(zoom_out_btn)

        zoom_reset_btn = QPushButton(self._t("scene_viewport.toolbar.reset_zoom", "重置"))
        zoom_reset_btn.setMaximumWidth(50)
        zoom_reset_btn.clicked.connect(lambda: self.set_zoom(1.0))  # type: ignore
        toolbar_layout.addWidget(zoom_reset_btn)

        toolbar_layout.addStretch()

        grid_btn = QPushButton(self._t("scene_viewport.toolbar.grid", "网格"))
        grid_btn.setCheckable(True)
        grid_btn.setChecked(True)
        grid_btn.toggled.connect(self._toggle_grid)  # type: ignore
        toolbar_layout.addWidget(grid_btn)

        snap_btn = QPushButton(self._t("scene_viewport.toolbar.snap", "吸附"))
        snap_btn.setCheckable(True)
        snap_btn.toggled.connect(self._toggle_snap)  # type: ignore
        toolbar_layout.addWidget(snap_btn)

    def set_zoom(self, zoom: float):
        """设置缩放级别。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, zoom))
        self.update()

    def _toggle_grid(self, checked: bool):
        """切换网格显示"""
        self.show_grid = checked
        self.update()

    def _toggle_snap(self, checked: bool):
        """切换吸附到网格"""
        self.snap_to_grid = checked

    def _on_context_selection_changed(self, objects: List[Any]):
        """编辑器上下文选中对象变化处理"""
        # 更新画布选择
        self.selected_nodes = [obj for obj in objects if isinstance(obj, Node)]
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
        else:
            self.selected_node = None
        self.update()

    def set_parent(self, parent: Optional[Any]):
        """设置父窗口引用。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.parent_widget = parent

    def _create_default_nodes(self):
        """创建默认节点（确保编辑器首次启动不空白）"""
        # 清空现有节点
        self.nodes.clear()
        self.connections.clear()
        
        # 获取视口中心位置
        center_x, center_y = 400, 300

        # 创建生物体节点（细胞膜）- 作为根节点
        organism = Node("organism_1", center_x, center_y, "organism")
        if hasattr(organism, 'radius'):
            organism.radius = 50
        self.nodes.append(organism)

        # 创建中枢管理器节点
        central_brain = Node("central_1", center_x, center_y, "central_brain")
        if hasattr(central_brain, 'radius'):
            central_brain.radius = 30
        self.nodes.append(central_brain)

        # 创建传感器节点
        sensor1 = Node("sensor_1", center_x - 120, center_y - 60, "sensor")
        if hasattr(sensor1, 'radius'):
            sensor1.radius = 20
        sensor2 = Node("sensor_2", center_x + 120, center_y - 60, "sensor")
        if hasattr(sensor2, 'radius'):
            sensor2.radius = 20
        self.nodes.extend([sensor1, sensor2])

        # 创建效应器节点
        actuator1 = Node("actuator_1", center_x - 120, center_y + 60, "actuator")
        if hasattr(actuator1, 'radius'):
            actuator1.radius = 20
        actuator2 = Node("actuator_2", center_x + 120, center_y + 60, "actuator")
        if hasattr(actuator2, 'radius'):
            actuator2.radius = 20
        self.nodes.extend([actuator1, actuator2])
        
        # 创建一些连接
        try:
            connection1 = self._own_connection(ConnectionLine(central_brain, sensor1))
            connection2 = self._own_connection(ConnectionLine(central_brain, sensor2))
            connection3 = self._own_connection(ConnectionLine(central_brain, actuator1))
            connection4 = self._own_connection(ConnectionLine(central_brain, actuator2))
            self.connections.extend([connection1, connection2, connection3, connection4])
        except Exception as e:
            logger.exception("创建默认连接失败: %s", e)
        
        logger.info("已创建默认节点（编辑器首次启动）")

        # 创建连接线
        self.connections.append(self._own_connection(ConnectionLine(sensor1, central_brain)))
        self.connections.append(self._own_connection(ConnectionLine(sensor2, central_brain)))
        self.connections.append(self._own_connection(ConnectionLine(central_brain, actuator1)))
        self.connections.append(self._own_connection(ConnectionLine(central_brain, actuator2)))

    # === 绘制: 网格、节点、连线、框选 ==========================================
    def paintEvent(self, event: Optional[QPaintEvent]):
        """绘制画布内容。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        chrome = self._chrome_top()

        # 检查是否有场景加载
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        sm = get_scene_manager()
        current_scene = sm.get_current_scene_path()

        if not current_scene:
            # 绘制未打开场景的提示信息
            self._draw_background(painter)
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.setFont(self.font())
            hint_rect = self.rect().adjusted(0, chrome, 0, 0) if chrome > 0 else self.rect()
            painter.drawText(
                hint_rect,
                Qt.AlignmentFlag.AlignCenter,
                self._t(
                    "scene_viewport.hint.open_scene",
                    "未打开场景\n\n请在项目面板中双击 .pond 文件打开",
                ),
            )
            return

        # 世界坐标：先下移画布区，再平移/缩放，与 _screen_to_world 一致
        painter.save()
        painter.translate(0, chrome)
        painter.setClipRect(0, 0, self.width(), max(1, self.height() - chrome))
        painter.translate(self.pan_offset)
        painter.scale(self.zoom_level, self.zoom_level)

        # 绘制背景
        self._draw_background(painter)

        # 绘制网格
        if self.show_grid:
            self._draw_grid(painter)

        # 绘制连接线
        for connection in self.connections:
            if connection == self.hovered_connection:
                # 高亮悬停的连接线
                glow_pen = QPen(QColor(255, 255, 0, 100), connection.width + 6)
                painter.setPen(glow_pen)
                painter.drawLine(
                    QPointF(float(connection.start_node.x), float(connection.start_node.y)),
                    QPointF(float(connection.end_node.x), float(connection.end_node.y))
                )
            connection.draw(painter)

        # 绘制临时连接线
        if self.connecting and self.connect_start_node:
            pen = QPen(QColor(255, 255, 255, 150), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            world_pos = self._screen_to_world(self.connect_temp_pos)
            painter.drawLine(
                QPointF(float(self.connect_start_node.x), float(self.connect_start_node.y)),
                world_pos
            )

        # 绘制框选矩形
        if self.box_selecting:
            self._draw_box_selection(painter)
        
        # 绘制节点
        for node in self.nodes:
            is_selected = node in self.selected_nodes
            is_hovered = node == self.hovered_node

            if is_selected:
                # 绘制选中效果
                glow_brush = QBrush(QColor(255, 255, 255, 80))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                rect = QRectF(
                    node.x - node.radius - 10,
                    node.y - node.radius - 10,
                    node.radius * 2 + 20,
                    node.radius * 2 + 20
                )
                painter.drawEllipse(rect)

                # 绘制选中边框
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                rect = QRectF(
                    node.x - node.radius - 5,
                    node.y - node.radius - 5,
                    node.radius * 2 + 10,
                    node.radius * 2 + 10
                )
                painter.drawEllipse(rect)
            elif is_hovered:
                # 绘制悬停效果
                glow_brush = QBrush(QColor(255, 255, 255, 50))
                painter.setBrush(glow_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                rect = QRectF(
                    node.x - node.radius - 8,
                    node.y - node.radius - 8,
                    node.radius * 2 + 16,
                    node.radius * 2 + 16
                )
                painter.drawEllipse(rect)

            # 绘制节点
            node.draw(painter)

        # 为生物体节点绘制细胞膜效果
        for node in self.nodes:
            if node.type == "organism":
                membrane_radius = int(node.radius * 3)
                center_x, center_y = int(node.x), int(node.y)

                # 绘制细胞膜外环
                outer_rect = QRect(center_x - membrane_radius - 2, center_y - membrane_radius - 2,
                                  membrane_radius * 2 + 4, membrane_radius * 2 + 4)
                outer_gradient = QLinearGradient(outer_rect.topLeft().x(), outer_rect.topLeft().y(),
                                               outer_rect.bottomRight().x(), outer_rect.bottomRight().y())
                outer_gradient.setColorAt(0, QColor(100, 150, 255, 50))
                outer_gradient.setColorAt(1, QColor(100, 150, 255, 0))
                painter.setBrush(QBrush(outer_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(outer_rect)

                # 绘制细胞膜主体
                membrane_pen = QPen()
                membrane_gradient = QLinearGradient(center_x - membrane_radius, center_y - membrane_radius,
                                                 center_x + membrane_radius, center_y + membrane_radius)
                membrane_gradient.setColorAt(0, QColor(100, 150, 255, 255))
                membrane_gradient.setColorAt(1, QColor(50, 100, 200, 255))
                membrane_pen.setBrush(membrane_gradient)
                membrane_pen.setWidth(3)
                membrane_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(membrane_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                # 确保所有参数都是 int 类型
                x1 = int(center_x - membrane_radius)
                y1 = int(center_y - membrane_radius)
                w1 = int(membrane_radius * 2)
                h1 = int(membrane_radius * 2)
                painter.drawEllipse(x1, y1, w1, h1)

                # 绘制细胞膜内环
                inner_pen = QPen(QColor(150, 200, 255, 150), 1)
                painter.setPen(inner_pen)
                x2 = int(center_x - membrane_radius + 4)
                y2 = int(center_y - membrane_radius + 4)
                w2 = int((membrane_radius - 4) * 2)
                h2 = int((membrane_radius - 4) * 2)
                painter.drawEllipse(x2, y2, w2, h2)
        
        painter.restore()

        # 绘制视口信息（参考 Unity/Godot）
        if self.show_viewport_info:
            self._draw_viewport_info(painter)

    def _draw_box_selection(self, painter: QPainter):
        """绘制框选矩形（屏幕坐标，不改变外部 painter 变换栈）"""
        painter.save()
        painter.resetTransform()

        rect = QRectF(
            min(self.box_select_start.x(), self.box_select_end.x()),
            min(self.box_select_start.y(), self.box_select_end.y()),
            abs(self.box_select_end.x() - self.box_select_start.x()),
            abs(self.box_select_end.y() - self.box_select_start.y())
        )

        fill_brush = QBrush(QColor(100, 150, 255, 30))
        painter.setBrush(fill_brush)
        painter.setPen(QPen(QColor(100, 150, 255, 200), 2, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

        painter.restore()
    
    def _draw_viewport_info(self, painter: QPainter):
        """绘制视口信息（坐标、缩放级别等）"""
        # 恢复变换以绘制屏幕坐标
        painter.resetTransform()
        
        try:
            # 获取鼠标位置对应的世界坐标
            from PyQt6.QtWidgets import QApplication
            mouse_pos = self.mapFromGlobal(QApplication.cursor().pos())
            if self.rect().contains(mouse_pos):
                world_pos = self._screen_to_world(mouse_pos)
                
                # 绘制信息文本
                info_text = f"缩放: {self.zoom_level:.2f}x | 坐标: ({world_pos.x():.1f}, {world_pos.y():.1f})"
                if self.selected_nodes:
                    info_text += f" | 选中: {len(self.selected_nodes)}"
                
                # 背景
                font_metrics = painter.fontMetrics()
                text_rect = font_metrics.boundingRect(info_text)
                text_rect.adjust(-4, -2, 4, 2)
                text_rect.moveBottomLeft(QPoint(10, self.height() - 10))
                
                bg_brush = QBrush(QColor(0, 0, 0, 180))
                painter.setBrush(bg_brush)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(text_rect)
                
                # 文本
                painter.setPen(QPen(QColor(255, 255, 255, 255)))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, info_text)
        except:
            # 如果获取鼠标位置失败，只显示缩放级别
            info_text = f"缩放: {self.zoom_level:.2f}x"
            if self.selected_nodes:
                info_text += f" | 选中: {len(self.selected_nodes)}"
            
            font_metrics = painter.fontMetrics()
            text_rect = font_metrics.boundingRect(info_text)
            text_rect.adjust(-4, -2, 4, 2)
            text_rect.moveBottomLeft(QPoint(10, self.height() - 10))
            
            bg_brush = QBrush(QColor(0, 0, 0, 180))
            painter.setBrush(bg_brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(text_rect)
            
            painter.setPen(QPen(QColor(255, 255, 255, 255)))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, info_text)
        
    def _finish_box_selection(self):
        """完成框选操作"""
        if not self.box_selecting:
            return
        
        # 计算框选区域（世界坐标）
        world_start = self._screen_to_world(self.box_select_start)
        world_end = self._screen_to_world(self.box_select_end)
        
        box_rect = QRectF(
            min(world_start.x(), world_end.x()),
            min(world_start.y(), world_end.y()),
            abs(world_end.x() - world_start.x()),
            abs(world_end.y() - world_start.y())
        )
        
        # 选择框内的所有节点
        selected = []
        for node in self.nodes:
            node_rect = QRectF(
                node.x - node.radius,
                node.y - node.radius,
                node.radius * 2,
                node.radius * 2
            )
            if box_rect.intersects(node_rect):
                selected.append(node)
        
        # 更新选择（框选默认替换选择，除非按住 Ctrl/Shift）
        from PyQt6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl: 添加到选择
            for node in selected:
                if node not in self.selected_nodes:
                    self.selected_nodes.append(node)
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Shift: 添加到选择
            for node in selected:
                if node not in self.selected_nodes:
                    self.selected_nodes.append(node)
        else:
            # 替换选择
            self.selected_nodes = selected
        
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
            self.editor_context.set_selection(self.selected_nodes)
        else:
            self.selected_node = None
            self.editor_context.clear_selection()
        
        self.update()
        self.updateRequest.emit()

    def _draw_background(self, painter: QPainter):
        """绘制背景"""
        painter.setBrush(QBrush(QColor(25, 25, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())

    def _draw_grid(self, painter: QPainter):
        """绘制网格（改进的网格渲染，参考 Unity/Godot）"""
        # 根据缩放级别自适应网格大小
        effective_grid_size = self.grid_size
        grid_alpha = 255
        
        # 如果缩放级别太小，显示更粗的网格
        if self.zoom_level < 0.5:
            effective_grid_size = self.grid_size * 4
            grid_alpha = 200
        elif self.zoom_level < 1.0:
            effective_grid_size = self.grid_size * 2
            grid_alpha = 220
        else:
            effective_grid_size = self.grid_size
            grid_alpha = 255
        
        # 主网格颜色（较暗）
        main_grid_color = QColor(60, 60, 70, grid_alpha)
        main_pen = QPen(main_grid_color, 0.5)
        painter.setPen(main_pen)

        # 计算可见区域
        visible_rect = self._get_visible_rect()
        start_x = int((visible_rect.left() // effective_grid_size) * effective_grid_size)
        end_x = int((visible_rect.right() // effective_grid_size) * effective_grid_size)
        start_y = int((visible_rect.top() // effective_grid_size) * effective_grid_size)
        end_y = int((visible_rect.bottom() // effective_grid_size) * effective_grid_size)

        # 绘制主网格线
        for x in range(start_x, end_x + effective_grid_size, effective_grid_size):
            painter.drawLine(x, start_y, x, end_y)

        for y in range(start_y, end_y + effective_grid_size, effective_grid_size):
            painter.drawLine(start_x, y, end_x, y)
        
        # 如果缩放级别足够大，绘制子网格（更细的线）
        if self.zoom_level >= 1.0 and effective_grid_size >= self.grid_size * 2:
            sub_grid_color = QColor(50, 50, 55, int(grid_alpha * 0.5))
            sub_pen = QPen(sub_grid_color, 0.3)
            painter.setPen(sub_pen)
            
            sub_grid_size = self.grid_size
            for x in range(start_x, end_x + sub_grid_size, sub_grid_size):
                if x % effective_grid_size != 0:  # 跳过主网格线
                    painter.drawLine(x, start_y, x, end_y)
            
            for y in range(start_y, end_y + sub_grid_size, sub_grid_size):
                if y % effective_grid_size != 0:  # 跳过主网格线
                    painter.drawLine(start_x, y, end_x, y)
        
        # 绘制中心十字线（参考 Unity）
        center_color = QColor(100, 100, 120, 150)
        center_pen = QPen(center_color, 1.0)
        painter.setPen(center_pen)
        painter.drawLine(0, start_y, 0, end_y)  # 垂直中心线
        painter.drawLine(start_x, 0, end_x, 0)  # 水平中心线

    def _get_visible_rect(self) -> QRectF:
        """获取可见区域（世界坐标）"""
        # 将屏幕坐标转换为世界坐标
        top_left = self._screen_to_world(QPoint(0, 0))
        bottom_right = self._screen_to_world(QPoint(self.width(), self.height()))
        return QRectF(top_left, bottom_right)

    def _screen_to_world(self, screen_pos: QPoint) -> QPointF:
        """屏幕坐标转世界坐标（扣除顶部工具栏）"""
        ey = screen_pos.y() - self._chrome_top()
        world_x = (screen_pos.x() - self.pan_offset.x()) / self.zoom_level
        world_y = (ey - self.pan_offset.y()) / self.zoom_level
        return QPointF(world_x, world_y)

    def _world_to_screen(self, world_pos: QPointF) -> QPoint:
        """世界坐标转屏幕坐标（含顶部工具栏偏移）"""
        screen_x = int(world_pos.x() * self.zoom_level + self.pan_offset.x())
        screen_y = int(world_pos.y() * self.zoom_level + self.pan_offset.y()) + self._chrome_top()
        return QPoint(screen_x, screen_y)

    # === 交互: 鼠标、滚轮、拖放 ==================================================
    def mousePressEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标按下事件（参考 Unity/Godot 的交互方式）。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击了节点
            clicked_node = None
            world_pos = self._screen_to_world(event.pos())
            
            for node in reversed(self.nodes):
                if node.contains(world_pos):
                    clicked_node = node
                    break

            if clicked_node:
                # 处理多选
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    if clicked_node in self.selected_nodes:
                        self.selected_nodes.remove(clicked_node)
                        if self.selected_node == clicked_node:
                            self.selected_node = None
                    else:
                        self.selected_nodes.append(clicked_node)
                        self.selected_node = clicked_node
                elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                    if self.selected_node:
                        # 范围选择
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(clicked_node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                        self.selected_node = clicked_node
                    else:
                        self.selected_nodes = [clicked_node]
                        self.selected_node = clicked_node
                else:
                    self.selected_nodes = [clicked_node]
                    self.selected_node = clicked_node

                # 更新编辑器上下文
                self.editor_context.set_selection(self.selected_nodes)
                
                self.dragging = True
                self.drag_start = event.pos()
                self._drag_start_x = clicked_node.x
                self._drag_start_y = clicked_node.y
                self._multi_drag_start_positions = {
                    str(node.id): (float(node.x), float(node.y))
                    for node in self.selected_nodes
                    if str(getattr(node, "id", "")).strip()
                }
            else:
                # 点击空白处，开始框选或取消选择
                modifiers = event.modifiers()
                if not (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                    # 开始框选
                    self.box_selecting = True
                    self.box_select_start = event.pos()
                    self.box_select_end = event.pos()
                    
                    # 如果没有按住 Ctrl/Shift，取消选择
                    self.selected_nodes.clear()
                    self.selected_node = None
                    self.editor_context.clear_selection()

            self.update()
            self.updateRequest.emit()

        elif event.button() == Qt.MouseButton.MiddleButton:
            # 鼠标中键开始平移（Unity/Godot 标准）
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
        elif event.button() == Qt.MouseButton.RightButton:
            world_pos = self._screen_to_world(event.pos())

            # 右键优先处理连接线删除
            for connection_index, connection in enumerate(self.connections):
                if connection.contains(world_pos):
                    if self._commit_connection_via_command(
                        "connection.delete",
                        connection,
                        connection_index=connection_index,
                    ):
                        self.projectModified.emit()
                        self.commandExecuted.emit()
                    self.update()
                    return

            # 再处理节点选择
            clicked_node = None
            for node in reversed(self.nodes):
                if node.contains(world_pos):
                    clicked_node = node
                    break

            if clicked_node:
                # 处理多选
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    if clicked_node in self.selected_nodes:
                        self.selected_nodes.remove(clicked_node)
                        if self.selected_node == clicked_node:
                            self.selected_node = None
                    else:
                        self.selected_nodes.append(clicked_node)
                        self.selected_node = clicked_node
                elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                    if self.selected_node:
                        # 范围选择
                        current_index = self.nodes.index(self.selected_node)
                        clicked_index = self.nodes.index(clicked_node)
                        start = min(current_index, clicked_index)
                        end = max(current_index, clicked_index)
                        self.selected_nodes = self.nodes[start:end+1]
                        self.selected_node = clicked_node
                    else:
                        self.selected_nodes = [clicked_node]
                        self.selected_node = clicked_node
                else:
                    self.selected_nodes = [clicked_node]
                    self.selected_node = clicked_node

                # 更新编辑器上下文
                self.editor_context.set_selection(self.selected_nodes)
                
                self.dragging = True
                self.drag_start = event.pos()
                self._drag_start_x = clicked_node.x
                self._drag_start_y = clicked_node.y
                self._multi_drag_start_positions = {
                    str(node.id): (float(node.x), float(node.y))
                    for node in self.selected_nodes
                    if str(getattr(node, "id", "")).strip()
                }
            else:
                # 点击空白处，取消选择
                if not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
                    self.selected_nodes.clear()
                    self.selected_node = None
                    self.editor_context.clear_selection()

            self.update()
            self.updateRequest.emit()

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标释放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # 处理框选完成
            if self.box_selecting:
                self.box_selecting = False
                # 执行框选逻辑
                self._finish_box_selection()
                self.update()
            
            if self.dragging:
                self.dragging = False
                if self.selected_node:
                    new_x = self.selected_node.x
                    new_y = self.selected_node.y
                    dx = new_x - self._drag_start_x
                    dy = new_y - self._drag_start_y

                    if dx != 0 or dy != 0:
                        if len(self.selected_nodes) > 1:
                            committed = self._commit_multi_node_drag_via_command(
                                dict(self._multi_drag_start_positions)
                            )
                        else:
                            committed = self._commit_single_node_drag_via_command(
                                self.selected_node,
                                self._drag_start_x,
                                self._drag_start_y,
                                new_x,
                                new_y,
                            )

                        if committed:
                            self.projectModified.emit()
                            self.commandExecuted.emit()
                self._multi_drag_start_positions.clear()

            # 处理连接完成
            if self.connecting and self.connect_start_node:
                world_pos = self._screen_to_world(event.pos())
                for node in self.nodes:
                    if node.contains(world_pos) and node != self.connect_start_node:
                        if self.connect_start_node.type != "organism" and node.type != "organism":
                            new_connection = self._own_connection(ConnectionLine(self.connect_start_node, node))
                            if self._commit_connection_via_command("connection.create", new_connection):
                                self.projectModified.emit()
                                self.commandExecuted.emit()
                            break

                self.connecting = False
                self.connect_start_node = None
                self.update()
                self.updateRequest.emit()
        
        elif event.button() == Qt.MouseButton.MiddleButton:
            # 鼠标中键结束平移
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: Optional[QMouseEvent]):
        """处理鼠标移动事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return
        if event is None:
            return

        # 处理平移（鼠标中键或右键）
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_offset += QPointF(delta.x(), delta.y())
            self.pan_start = event.pos()
            self.update()
            return

        # 处理框选
        if self.box_selecting:
            self.box_select_end = event.pos()
            self.update()
            return

        world_pos = self._screen_to_world(event.pos())
        self._update_hover_states(world_pos)

        if self.dragging and self.selected_node:
            dx = (event.pos().x() - self.drag_start.x()) / self.zoom_level
            dy = (event.pos().y() - self.drag_start.y()) / self.zoom_level

            if len(self.selected_nodes) > 1:
                for node in self.selected_nodes:
                    start_position = self._multi_drag_start_positions.get(str(getattr(node, "id", "")).strip())
                    if start_position is None:
                        continue
                    new_x = start_position[0] + dx
                    new_y = start_position[1] + dy
                    # 应用吸附
                    if self.snap_to_grid:
                        new_x = round(new_x / self.grid_size) * self.grid_size
                        new_y = round(new_y / self.grid_size) * self.grid_size
                    node.update_position(new_x, new_y)
            else:
                new_x = self.selected_node.x + dx
                new_y = self.selected_node.y + dy
                # 应用吸附
                if self.snap_to_grid:
                    new_x = round(new_x / self.grid_size) * self.grid_size
                    new_y = round(new_y / self.grid_size) * self.grid_size
                self.selected_node.update_position(new_x, new_y)

            if len(self.selected_nodes) <= 1:
                self.drag_start = event.pos()
            self.update()

        if self.connecting:
            self.connect_temp_pos = event.pos()
            self.update()

    def _update_hover_states(self, pos: QPointF):
        """更新悬停状态"""
        self.hovered_node = None
        for node in self.nodes:
            if node.contains(pos):
                self.hovered_node = node
                break

        self.hovered_connection = None
        for connection in self.connections:
            if connection.contains(pos):
                self.hovered_connection = connection
                break

        self.update()

    def wheelEvent(self, event: Optional[QWheelEvent]):
        """处理鼠标滚轮缩放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        if not get_scene_manager().get_current_scene_path():
            return
        if event is None:
            return

        # 获取鼠标位置（屏幕坐标）
        mouse_pos = event.position().toPoint()
        
        # 获取鼠标位置对应的世界坐标
        world_pos_before = self._screen_to_world(mouse_pos)
        
        # 计算缩放因子
        delta = event.angleDelta().y()
        zoom_speed = 0.1  # 缩放速度
        zoom_factor = 1.0 + (delta / 1200.0) * zoom_speed
        zoom_factor = max(0.9, min(1.1, zoom_factor))  # 限制单次缩放范围
        
        # 应用缩放
        new_zoom = self.zoom_level * zoom_factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # 计算缩放后的偏移，使鼠标位置对应的世界坐标保持不变
        if new_zoom != self.zoom_level:
            chrome = self._chrome_top()
            ey = mouse_pos.y() - chrome
            self.pan_offset = QPointF(
                mouse_pos.x() - world_pos_before.x() * new_zoom,
                ey - world_pos_before.y() * new_zoom,
            )
            self.zoom_level = new_zoom
            self.update()

    def contextMenuEvent(self, event: Optional[QContextMenuEvent]):
        """上下文菜单事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event is None:
            return

        menu = QMenu(self)
        world_pos = self._screen_to_world(event.pos())
        pos_list = [world_pos.x(), world_pos.y()]

        def add_create_action(label: str, entity_name: str, entity_type: str, *, scripts: Optional[List[Dict[str, Any]]] = None) -> None:
            menu.addAction(
                label,
                lambda name=entity_name, typ=entity_type, script_list=scripts: self._create_entity_via_command_or_event(
                    name,
                    typ,
                    pos_list,
                    scripts=script_list,
                ),
            )

        # 创建基本实体菜单
        add_create_action(
            self._t("scene_viewport.menu.create_empty_entity", "创建空实体"),
            self._t("scene_viewport.entity_name.empty", "Empty Entity"),
            "empty",
        )
        add_create_action(
            self._t("scene_viewport.menu.create_organism", "创建生物体"),
            self._t("scene_viewport.entity_name.organism", "Organism"),
            "organism",
        )
        
        submenu = menu.addMenu(self._t("scene_viewport.menu.biological_components", "生物组件"))
        submenu.addAction(
            self._t("scene_viewport.menu.create_sensor", "创建传感器"),
            lambda: self._create_entity_via_command_or_event(
                self._t("scene_viewport.entity_name.sensor", "Sensor"), "sensor", pos_list
            ),
        )
        submenu.addAction(
            self._t("scene_viewport.menu.create_actuator", "创建效应器"),
            lambda: self._create_entity_via_command_or_event(
                self._t("scene_viewport.entity_name.actuator", "Actuator"), "actuator", pos_list
            ),
        )
        submenu.addAction(
            self._t("scene_viewport.menu.create_central_brain", "创建中枢管理器"),
            lambda: self._create_entity_via_command_or_event(
                self._t("scene_viewport.entity_name.central_brain", "Central Brain"), "central_brain", pos_list
            ),
        )

        menu.addSeparator()
        official_cell_script = [
            {
                "name": "OfficialCellBehavior",
                "path": os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "..",
                        "..",
                        "builtin",
                        "templates",
                        "official_cell_behavior.py",
                    )
                ),
            }
        ]
        add_create_action(
            self._t("scene_viewport.menu.create_official_cell", "创建官方细胞模板"),
            self._t("scene_viewport.entity_name.official_cell", "Official Cell"),
            "organism",
            scripts=official_cell_script,
        )

        menu.addSeparator()

        if self.selected_node:
            connect_action = menu.addAction(self._t("scene_viewport.menu.start_connection", "开始连接"))
            connect_action.triggered.connect(self._start_connection)

            delete_action = menu.addAction(self._t("scene_viewport.menu.delete_entity", "删除实体"))
            delete_action.triggered.connect(self._delete_node)

        menu.exec(event.globalPos())

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
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-vitaloom-asset"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """处理拖放事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        scene_path = get_scene_manager().get_current_scene_path()
        if not scene_path:
            # 没有当前场景时，只允许拖入 .pond 文件来打开场景。
            if not event.mimeData().hasUrls():
                return
            elif not any(url.toLocalFile().lower().endswith('.pond') for url in event.mimeData().urls()):
                return

        world_pos = self._screen_to_world(event.position().toPoint())
        pos_list = [world_pos.x(), world_pos.y()]

        if event.mimeData().hasUrls():
            # 处理文件拖入
            for url in event.mimeData().urls():
                import os
                file_path = url.toLocalFile()
                file_name = os.path.basename(file_path)
                
                # 根据文件类型创建实体
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    logger.info("拖入图片: %s", file_name)
                    
                    # 检查是否是外部文件（不在项目目录内）
                    project_path = self.editor_context.current_project_path
                    
                    if project_path:
                        # External drops must enter through the same import/Registry seam.
                        try:
                            inside_project = os.path.commonpath(
                                [os.path.abspath(file_path), os.path.abspath(project_path)]
                            ) == os.path.abspath(project_path)
                        except ValueError:
                            inside_project = False
                        if not inside_project:
                            assets_dir = os.path.join(project_path, "assets")
                            target_path = os.path.join(assets_dir, file_name)
                            counter = 1
                            name_without_ext, ext = os.path.splitext(file_name)
                            while os.path.exists(target_path):
                                target_path = os.path.join(assets_dir, f"{name_without_ext}_{counter}{ext}")
                                counter += 1
                            try:
                                imported = self._run_asset_import_command(
                                    {
                                        "project_path": project_path,
                                        "source_path": file_path,
                                        "target_folder": "assets",
                                        "name": os.path.basename(target_path),
                                    }
                                )
                            except Exception as exc:
                                logger.warning("External asset import command failed: %s", exc)
                                continue
                            if not imported.get("ok"):
                                logger.warning("External asset import command failed: %s", imported.get("error"))
                                continue
                            file_path = str(imported.get("result", {}).get("path") or target_path)
                            logger.info("Imported external asset through command: %s", os.path.relpath(file_path, project_path))
                            self.editor_context.event_bus.publish("refresh_project_browser", {})
                    
                    placed = self._run_scene_placement_command(
                        "asset.apply_to_scene",
                        {
                            "scene_path": scene_path,
                            "asset_path": file_path,
                            "entity_id": self._scene_entity_id_from_path(file_name),
                            "name": file_name,
                            "entity_type": "sprite",
                            "position": pos_list,
                        },
                    )
                    if placed:
                        self._refresh_scene_after_command(scene_path)
                    else:
                        self.editor_context.event_bus.publish("create_entity", {
                        "entity_name": file_name, 
                        "entity_type": "sprite", 
                        "position": pos_list, 
                        "sprite_path": file_path
                        })
                elif file_path.lower().endswith('.pond'):
                    # 检查是否按住 Alt 或 Shift，如果是，则作为预制体放入；否则询问是否切换场景
                    # 简化逻辑：如果是从项目中的场景文件夹拖入，通常是想打开场景
                    msg = f"检测到场景文件: {file_name}\n\n你想打开这个场景，还是将其作为预制体放入当前场景？"
                    from PyQt6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(self, "场景操作", msg, 
                                               QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel)
                    
                    if reply == QMessageBox.StandardButton.Open:
                        from core.VitaLoom.commands.registry import get_command_registry

                        result = get_command_registry().run("scene.open", {"scene_path": file_path})
                        if not result.get("ok"):
                            logger.warning("拖拽打开场景失败: %s", result.get("error"))
                    elif reply == QMessageBox.StandardButton.Apply:
                        logger.info("Applying dropped prefab: %s", file_name)
                        self._apply_scene_prefab_placement(
                            scene_path,
                            file_path,
                            file_name,
                            pos_list,
                        )
                else:
                    self._apply_scene_asset_placement(
                        scene_path,
                        file_path,
                        file_name,
                        pos_list,
                    )
            
            event.acceptProposedAction()

    def _add_node(self, pos: QPointF, node_type: str) -> bool:
        """Create one node through Runtime history, then select its canonical rehydrated instance."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_path = get_scene_manager().get_current_scene_path()
        if not scene_path:
            logger.warning("Cannot create node without a current scene")
            return False

        existing_ids = {str(getattr(node, "id", "")).strip() for node in self.nodes}
        suffix = 1
        while f"{node_type}_{suffix}" in existing_ids:
            suffix += 1
        node_id = f"{node_type}_{suffix}"
        new_x = float(pos.x())
        new_y = float(pos.y())

        if self.snap_to_grid:
            new_x = round(new_x / self.grid_size) * self.grid_size
            new_y = round(new_y / self.grid_size) * self.grid_size

        if node_type != "organism":
            organism_node = next((node for node in self.nodes if node.type == "organism"), None)
            if organism_node:
                membrane_radius = organism_node.radius * 3
                distance = ((new_x - organism_node.x) ** 2 + (new_y - organism_node.y) ** 2) ** 0.5
                if distance > membrane_radius:
                    dx_dir = new_x - organism_node.x
                    dy_dir = new_y - organism_node.y
                    if distance > 0:
                        dx_dir /= distance
                        dy_dir /= distance
                    new_x = float(organism_node.x + dx_dir * membrane_radius)
                    new_y = float(organism_node.y + dy_dir * membrane_radius)

        draft_node = Node(node_id, float(new_x), float(new_y), node_type)
        if not self._run_scene_entity_create_command(
            {"scene_path": scene_path, "entity": draft_node.to_dict()}
        ):
            return False

        self._refresh_scene_after_command(scene_path)
        selected = self._select_rehydrated_nodes([node_id])
        if not selected:
            logger.warning("Created node %s was not available after canonical scene rehydrate", node_id)
            return False
        new_node = selected[0]

        if self.parent_widget and hasattr(self.parent_widget, "project_tree"):
            project_tree = getattr(self.parent_widget, "project_tree")
            if hasattr(project_tree, "update_tree"):
                project_tree.update_tree(self.nodes, self.connections)

        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()
        self.signal_bus.emit_object_created(new_node, {"type": node_type})
        return True

    def _delete_node(self) -> bool:
        """Delete selected nodes through Runtime history without duplicate local mutations."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        deleted_nodes = list(self.selected_nodes)
        scene_path = get_scene_manager().get_current_scene_path()
        if not deleted_nodes or not scene_path:
            return False

        successful: List[tuple[Node, str]] = []
        for node in deleted_nodes:
            node_id = str(getattr(node, "id", "")).strip()
            if not node_id:
                continue
            result = self._run_scene_entity_delete_command(
                {"scene_path": scene_path, "entity_id": node_id}
            )
            if not result.get("ok"):
                continue
            result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
            self._refresh_scene_after_command(str(result_data.get("scene_path") or scene_path))
            successful.append((node, node_id))

        if not successful:
            return False

        self._select_rehydrated_nodes([])
        for node, node_id in successful:
            self.signal_bus.emit_object_deleted(node)
            self.editor_context.event_bus.publish("entity_deleted", {"id": node_id})

        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()
        logger.info("Deleted %s scene entities through Runtime commands", len(successful))
        return True

    def _delete_node_by_instance(self, node: Node) -> bool:
        """Delete one node by instance through Runtime history and canonical rehydration."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        node_id = str(getattr(node, "id", "")).strip()
        scene_path = get_scene_manager().get_current_scene_path()
        if not node_id or not scene_path:
            return False

        remaining_selection_ids = [
            str(getattr(selected, "id", "")).strip()
            for selected in self.selected_nodes
            if selected is not node and str(getattr(selected, "id", "")).strip() != node_id
        ]
        result = self._run_scene_entity_delete_command(
            {"scene_path": scene_path, "entity_id": node_id}
        )
        if not result.get("ok"):
            return False

        result_data = result.get("result") if isinstance(result.get("result"), dict) else {}
        self._refresh_scene_after_command(str(result_data.get("scene_path") or scene_path))
        self._select_rehydrated_nodes(remaining_selection_ids)
        self.signal_bus.emit_object_deleted(node)
        self.editor_context.event_bus.publish("entity_deleted", {"id": node_id})
        self.update()
        self.updateRequest.emit()
        self.projectModified.emit()
        self.commandExecuted.emit()
        return True

    def _run_viewport_keyboard_history_command(self, command_id: str) -> bool:
        """Route focused Ctrl+Z/Ctrl+Y to Qt-free global semantic history."""
        return self._run_global_scene_history_command(command_id)

    def keyPressEvent(self, event):
        """处理键盘事件。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self._delete_node()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._run_viewport_keyboard_history_command("command.undo")
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._run_viewport_keyboard_history_command("command.redo")
        else:
            super().keyPressEvent(event)

    def _start_connection(self):
        """开始连接节点"""
        if self.selected_node:
            self.connecting = True
            self.connect_start_node = self.selected_node
            self.connect_temp_pos = self._world_to_screen(QPointF(self.selected_node.x, self.selected_node.y))
            self.update()
    
    # === 场景数据: 与 SceneManager 同步 ==========================================
    def load_scene_data(self, scene_data: Dict[str, Any]):
        """职责: 从 `.pond` JSON 重建 nodes/connections 并清空命令栈。
        时机: scene_loaded 事件或项目打开后。
        不变量: 空 entities 时保留默认演示节点逻辑见 `_create_default_nodes`。
        排错: 加载后空白 → scene_data 键名 nodes/connections 是否与导出一致。
        """
        try:
            # 清空现有节点和连接
            self.nodes.clear()
            self.connections.clear()
            self.selected_node = None
            self.selected_nodes.clear()
            
            # 加载实体（节点）
            entities = scene_data.get("entities", [])
            if entities:
                for entity_data in entities:
                    try:
                        entity_id = entity_data.get("id", "")
                        entity_type = entity_data.get("type", "organism")
                        position = entity_data.get("position", [0, 0])
                        
                        # 处理位置数据（可能是列表、元组或字典）
                        if isinstance(position, (list, tuple)):
                            pos_x = float(position[0]) if len(position) > 0 else 0.0
                            pos_y = float(position[1]) if len(position) > 1 else 0.0
                        elif isinstance(position, dict):
                            pos_x = float(position.get("x", 0.0))
                            pos_y = float(position.get("y", 0.0))
                        else:
                            pos_x = 0.0
                            pos_y = 0.0
                        
                        # 创建节点
                        node = Node(entity_id, pos_x, pos_y, entity_type)
                        
                        # 恢复名称和脚本
                        if "name" in entity_data:
                            node.name = entity_data["name"]
                        if "scripts" in entity_data:
                            node.scripts = entity_data["scripts"]
                        if "sprite_path" in entity_data:
                            node.sprite_path = entity_data["sprite_path"]
                        if "radius" in entity_data:
                            node.radius = entity_data["radius"]
                        if entity_data.get("pinned") is True:
                            node.pinned = True
                        raw_vis = entity_data.get("sr_visual")
                        if isinstance(raw_vis, dict):
                            node.sr_visual = dict(raw_vis)
                        else:
                            try:
                                from core.VitaLoom.core.editor_context import get_editor_context
                                from core.Lotucosm.sr_game_defaults import (
                                    default_sr_visual_for_entity,
                                    infer_engine_game_project,
                                )

                                project_path = getattr(get_editor_context(), "current_project_path", None)
                                if infer_engine_game_project(project_path):
                                    vis = default_sr_visual_for_entity(entity_id, entity_type)
                                    if vis.sprite:
                                        node.sr_visual = {"sprite": vis.sprite}
                                        if vis.alpha < 0.999:
                                            node.sr_visual["alpha"] = vis.alpha
                            except Exception:
                                __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
                            
                        self.nodes.append(node)
                    except Exception as e:
                        logger.warning("加载实体失败: %s", e)
                        continue
            
            # 如果没有实体，保持空白（用户要求）
            # if not self.nodes:
            #     print("📝 场景中没有实体，创建默认节点")
            #     self._create_default_nodes()
            
            # 加载连接（需要根据场景数据格式调整）
            # 尝试多种可能的连接数据格式
            connections_data = scene_data.get("connections", [])
            if not connections_data:
                # 也可能在 components 中
                components = scene_data.get("components", [])
                for comp in components:
                    if isinstance(comp, dict) and "connections" in comp:
                        connections_data.extend(comp["connections"])
            
            for conn_data in connections_data:
                try:
                    # 支持多种连接数据格式
                    if isinstance(conn_data, dict):
                        start_id = conn_data.get("start", conn_data.get("start_id", conn_data.get("from", "")))
                        end_id = conn_data.get("end", conn_data.get("end_id", conn_data.get("to", "")))
                    elif isinstance(conn_data, (list, tuple)) and len(conn_data) >= 2:
                        start_id = str(conn_data[0])
                        end_id = str(conn_data[1])
                    else:
                        continue
                    
                    # 查找对应的节点
                    start_node = next((n for n in self.nodes if n.id == start_id), None)
                    end_node = next((n for n in self.nodes if n.id == end_id), None)
                    
                    if start_node and end_node:
                        connection = ConnectionLine(start_node, end_node)
                        weight = conn_data.get("weight", 1.0)
                        if isinstance(weight, (int, float)) and not isinstance(weight, bool):
                            connection.weight = float(weight)
                        self.connections.append(self._own_connection(connection))
                except Exception as e:
                    logger.warning("加载连接失败: %s", e)
                    continue
            
            # 恢复视口平移/缩放（上次保存于 .pond viewport_state）
            vp_state = scene_data.get("viewport_state")
            if isinstance(vp_state, dict):
                pan = vp_state.get("pan_offset")
                if isinstance(pan, (list, tuple)) and len(pan) >= 2:
                    self.pan_offset = QPointF(float(pan[0]), float(pan[1]))
                zoom = vp_state.get("zoom_level")
                if zoom is not None:
                    try:
                        self.zoom_level = max(0.1, min(4.0, float(zoom)))
                    except (TypeError, ValueError):
                        pass

            # 更新显示
            self.update()
            self.updateRequest.emit()
            
            logger.info("场景数据已加载到视口: %s 个节点, %s 个连接", len(self.nodes), len(self.connections))
            
        except Exception as e:
            logger.exception("加载场景数据失败: %s", e)
            if not self.nodes:
                self._create_default_nodes()
                self.update()

    def get_scene_data(self) -> Dict[str, Any]:
        """职责: 序列化当前画布为 SceneManager 可保存的 dict 片段。
        时机: 保存场景前由插件或 SceneManager 拉取。
        不变量: 与 load_scene_data 字段对称（nodes、connections、resources）。
        排错: 保存丢失编辑 → 是否调用本方法合并进 save_scene(data=...)。
        """
        from core.Lotucosm.sr_game_defaults import default_sr_visual_for_entity, infer_engine_game_project
        from core.Lotucosm.sr_game_scene import normalize_game_scene_data
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        sm = get_scene_manager()
        base_data = sm.get_scene_data() or {}

        try:
            from core.VitaLoom.core.editor_context import get_editor_context

            project_path = getattr(get_editor_context(), "current_project_path", None)
        except Exception:
            project_path = None

        if infer_engine_game_project(project_path):
            for node in self.nodes:
                if not isinstance(node.sr_visual, dict) or not node.sr_visual.get("sprite"):
                    vis = default_sr_visual_for_entity(node.id, node.type)
                    if vis.sprite:
                        node.sr_visual = {"sprite": vis.sprite}
                        if vis.alpha < 0.999:
                            node.sr_visual["alpha"] = vis.alpha

        base_data["entities"] = [node.to_dict() for node in self.nodes]
        base_data["connections"] = [conn.to_dict() for conn in self.connections]

        base_data["viewport_state"] = {
            "pan_offset": [self.pan_offset.x(), self.pan_offset.y()],
            "zoom_level": self.zoom_level,
        }

        return normalize_game_scene_data(base_data, project_path)

    def _on_create_entity_event(self, data: Dict[str, Any]):
        """创建实体事件处理"""
        try:
            entity_name = data.get("entity_name", data.get("entity_type", "Entity"))
            entity_type = data.get("entity_type", "organism")
            position = data.get("position", [0, 0])
            sprite_path = data.get("sprite_path", "")
            scripts = data.get("scripts", [])
            
            self.create_entity_node(entity_name, entity_type, position, sprite_path, scripts=scripts)
        except Exception as e:
            logger.exception("处理创建实体事件失败: %s", e)
    
    def _on_scene_loaded_event(self, data):
        """场景加载事件处理"""
        try:
            # 重新加载当前场景数据到视口
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            sm = get_scene_manager()
            scene_data = sm.get_scene_data()
            if scene_data:
                self.load_scene_data(scene_data)
        except Exception as e:
            logger.exception("处理场景加载事件失败: %s", e)
    
    def create_entity_node(
        self,
        entity_name: str,
        entity_type: str,
        position: List[float],
        sprite_path: str = "",
        scripts: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Create an event-requested entity through Runtime history and canonical rehydration."""
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        import uuid

        scene_path = get_scene_manager().get_current_scene_path()
        if not scene_path:
            logger.warning("Cannot create event entity without a current scene")
            return False
        try:
            entity_id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
            pos_x = float(position[0]) if len(position) > 0 else 0.0
            pos_y = float(position[1]) if len(position) > 1 else 0.0
            draft_node = Node(entity_id, pos_x, pos_y, entity_type)
            draft_node.name = entity_name
            draft_node.scripts = list(scripts or [])
            if entity_type == "sprite" and sprite_path:
                draft_node.sprite_path = sprite_path
                draft_node.radius = 40.0

            if not self._run_scene_entity_create_command(
                {"scene_path": scene_path, "entity": draft_node.to_dict()}
            ):
                return False

            self._refresh_scene_after_command(scene_path)
            selected = self._select_rehydrated_nodes([entity_id])
            if not selected:
                logger.warning("Created event entity %s was not available after canonical rehydrate", entity_id)
                return False

            self.editor_context.event_bus.publish(
                "entity_created",
                {
                    "id": entity_id,
                    "name": entity_name,
                    "type": entity_type,
                    "position": [pos_x, pos_y],
                    "sprite_path": sprite_path,
                    "scripts": list(scripts or []),
                },
            )
            self.update()
            self.updateRequest.emit()
            self.projectModified.emit()
            self.commandExecuted.emit()
            logger.info("Created scene entity through Runtime command: %s (%s)", entity_name, entity_id)
            return True
        except Exception as exc:
            logger.exception("Failed to create event entity node: %s", exc)
            return False


# 为了向后兼容，保留OrganismCanvas作为别名
OrganismCanvas = SceneViewport

