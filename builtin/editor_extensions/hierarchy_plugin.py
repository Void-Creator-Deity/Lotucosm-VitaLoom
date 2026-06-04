"""场景层级 Dock 插件：树形展示当前场景实体。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("HierarchyPlugin")


class HierarchyPlugin(IDockProvider):
    """层级面板插件 - 显示场景中的实体层级结构"""
    
    DOCK_ID = "Hierarchy"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Hierarchy",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "场景层级面板，显示所有实体",
            "dependencies": [],
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self.hierarchy_panel = None
        
        # 订阅场景加载事件
        editor_context.event_bus.subscribe("scene_loaded", self.on_scene_loaded)
        # 订阅场景中实体创建事件，实时同步
        editor_context.event_bus.subscribe("entity_created_in_scene", self.on_entity_created)
        # 兼容 SceneViewport 直接发布的 entity_created 事件
        editor_context.event_bus.subscribe("entity_created", self.on_entity_created)
        editor_context.event_bus.subscribe("entity_deleted", self.on_entity_deleted)
        editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_unload(self):
        # 取消订阅
        if hasattr(self, 'context') and self.context:
            try:
                self.context.event_bus.unsubscribe("scene_loaded", self.on_scene_loaded)
                self.context.event_bus.unsubscribe("entity_created_in_scene", self.on_entity_created)
                self.context.event_bus.unsubscribe("entity_created", self.on_entity_created)
                self.context.event_bus.unsubscribe("entity_deleted", self.on_entity_deleted)
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.warning(self._t("hierarchy.log.unsubscribe_failed", "⚠️  Hierarchy 取消订阅失败: {error}").format(error=e))
        
        if self.dock:
            self.dock.deleteLater()
    
    def on_scene_loaded(self, data):
        """场景加载时更新层次树"""
        try:
            scene_path = data if isinstance(data, str) else data.get("path", "")
            if not scene_path:
                if self.hierarchy_panel and hasattr(self.hierarchy_panel, "_update_hierarchy"):
                    self.hierarchy_panel._update_hierarchy()
                elif self.hierarchy_panel and hasattr(self.hierarchy_panel, "tree_widget"):
                    self.hierarchy_panel.tree_widget.clear()
                return
            logger.info(self._t("hierarchy.log.scene_loaded", "📐 场景已加载: {path}").format(path=scene_path))
            
            # 如果层次面板已创建，更新树
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, 'update_tree'):
                # 从场景管理器获取场景数据
                try:
                    from core.VitaLoom.scene.scene_manager import get_scene_manager
                    from core.VitaLoom.viewports.scene_viewport import SceneViewport
                    from core.VitaLoom.kernel.layout_manager import LayoutManager
                    
                    scene_manager = get_scene_manager()
                    scene_data = scene_manager.get_scene_data()
                    
                    # 尝试从场景视口获取节点和连接
                    if self.context and hasattr(self.context, 'kernel'):
                        kernel = self.context.kernel
                        if kernel and hasattr(kernel, 'layout_manager'):
                            layout_manager: LayoutManager = kernel.layout_manager
                            current_viewport_id = layout_manager.get_current_viewport()
                            if current_viewport_id == "scene":
                                viewport_provider = layout_manager.viewport_providers.get(current_viewport_id)
                                if viewport_provider and hasattr(viewport_provider, 'viewport'):
                                    viewport = viewport_provider.viewport
                                    if isinstance(viewport, SceneViewport):
                                        # 获取节点和连接
                                        nodes = viewport.nodes if hasattr(viewport, 'nodes') else []
                                        connections = viewport.connections if hasattr(viewport, 'connections') else []
                                        # 更新层次树
                                        self.hierarchy_panel.update_tree(nodes, connections)
                                        logger.info(
                                            self._t(
                                                "hierarchy.log.tree_updated",
                                                "✅ 层级树已更新: {nodes} 个节点, {connections} 个连接",
                                            ).format(nodes=len(nodes), connections=len(connections))
                                        )
                except Exception as e:
                    logger.exception(
                        self._t("hierarchy.log.update_tree_failed", "⚠️  更新层级树失败: {error}").format(error=e)
                    )
        except Exception as e:
            logger.exception(
                self._t("hierarchy.log.scene_loaded_failed", "⚠️  处理场景加载事件失败: {error}").format(error=e)
            )
    
    def create_dock_widget(self) -> QDockWidget:
        """创建 Hierarchy Dock 窗口"""
        self.dock = QDockWidget(self._t("hierarchy.title", "层级"))
        self.dock.setObjectName(self.DOCK_ID)
        
        # 尝试复用现有的 HierarchyPanel
        try:
            from core.VitaLoom.docks.scene_outline import HierarchyPanel
            self.hierarchy_panel = HierarchyPanel()
            
            # 连接双击事件以支持进入细胞编辑模式
            self.hierarchy_panel.tree_widget.itemDoubleClicked.connect(
                self.on_item_double_clicked
            )
        except Exception as e:
            logger.warning(self._t("hierarchy.log.load_panel_failed", "⚠️  无法加载 HierarchyPanel: {error}").format(error=e))
            # 如果导入失败，创建一个简单的树形控件
            from PyQt6.QtWidgets import QTreeWidget
            self.hierarchy_panel = QTreeWidget()
            self.hierarchy_panel.setHeaderLabel(self._t("hierarchy.header.scene", "场景"))
        
        self.dock.setWidget(self.hierarchy_panel)
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.LeftDockWidgetArea,
            "default_visible": True,
            "can_close": True
        }
    
    def on_item_double_clicked(self, item, column):
        """双击项目时的处理"""
        # 检查是否为细胞实体，如果是则发布进入细胞编辑事件
        obj_data = item.data(0, Qt.ItemDataRole.UserRole)
        if obj_data and isinstance(obj_data, dict):
            if obj_data.get('type') == 'entity' and obj_data.get('data', {}).get('type') == 'cell':
                logger.info("🔬 进入细胞编辑模式: %s", item.text(0))
                self.context.event_bus.publish("enter_cell_edit", obj_data)
    
    def on_entity_created(self, data):
        """实体在场景中创建时同步到Hierarchy"""
        try:
            if not isinstance(data, dict):
                return
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, 'add_entity_to_tree'):
                # 直接添加实体到树
                self.hierarchy_panel.add_entity_to_tree(data)
                logger.info(
                    self._t("hierarchy.log.entity_synced", "🔄 已同步新实体: {name}").format(
                        name=data.get("entity_name")
                    )
                )
            elif self.hierarchy_panel and hasattr(self.hierarchy_panel, 'update_tree'):
                # 如果没有add_entity_to_tree方法，刷新整个树
                self.on_scene_loaded({"path": "current"})
        except Exception as e:
            logger.warning(self._t("hierarchy.log.sync_entity_failed", "⚠️ 同步实体失败: {error}").format(error=e))

    def on_entity_deleted(self, data):
        """实体删除时直接刷新树，保证与场景一致。"""
        try:
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, "update_tree"):
                self.on_scene_loaded({"path": "current"})
        except Exception as e:
            logger.warning(self._t("hierarchy.log.entity_deleted_failed", "⚠️ 处理实体删除失败: {error}").format(error=e))

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        if self.dock:
            self.dock.setWindowTitle(self._t("hierarchy.title", "层级"))
        # 若是降级 QTreeWidget，更新表头
        try:
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, "setHeaderLabel"):
                self.hierarchy_panel.setHeaderLabel(self._t("hierarchy.header.scene", "场景"))
        except Exception:
            pass
        # 尽量不重建 Dock：内部 key 必须稳定
        if self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            if hasattr(lm, "docks") and self.DOCK_ID in getattr(lm, "docks", {}):
                lm.docks[self.DOCK_ID] = self.dock
