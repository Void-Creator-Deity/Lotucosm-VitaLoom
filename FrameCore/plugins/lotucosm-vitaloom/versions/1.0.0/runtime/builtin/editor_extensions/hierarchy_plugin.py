"""场景层级 Dock 插件：树形展示当前场景实体。

排错: 见 `builtin/README.md`。
"""

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("HierarchyPlugin")


class HierarchyPlugin(IRuntimePlugin):
    """层级面板插件 - 显示场景中的实体层级结构"""
    
    DOCK_ID = "Hierarchy"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "HierarchyPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "场景层级面板，显示所有实体",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "hierarchy.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "hierarchy.title",
                    "default_title": "层级",
                    "area": "left",
                    "default_visible": True,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 30,
                    "refresh_events": ["language_changed"],
                }
            ],
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.dock = None
        self.hierarchy_panel = None
        self._event_subscriptions = []

        bindings = (
            ("scene_loaded", self.on_scene_loaded),
            ("entity_created_in_scene", self.on_entity_created),
            ("entity_created", self.on_entity_created),
            ("entity_deleted", self.on_entity_deleted),
            ("language_changed", self._on_language_changed),
            ("scene_hierarchy_updated", self._on_scene_hierarchy_updated),
        )
        try:
            for event_name, callback in bindings:
                editor_context.event_bus.subscribe(event_name, callback)
                self._event_subscriptions.append(
                    (editor_context.event_bus, event_name, callback)
                )
        except Exception:
            self._release_event_subscriptions()
            raise
    
    def on_unload(self):
        self._release_event_subscriptions()
        dock = self.dock
        self.dock = None
        self.hierarchy_panel = None
        if dock:
            dock.deleteLater()

    def _release_event_subscriptions(self) -> None:
        subscriptions = list(getattr(self, "_event_subscriptions", ()))
        self._event_subscriptions = []
        failed = []
        for event_bus, event_name, callback in subscriptions:
            try:
                event_bus.unsubscribe(event_name, callback)
            except Exception as error:
                failed.append((event_bus, event_name, callback))
                logger.warning(
                    self._t(
                        "hierarchy.log.unsubscribe_failed",
                        "⚠️  Hierarchy 取消订阅失败: {error}",
                    ).format(error=error)
                )
        self._event_subscriptions.extend(failed)
    
    def _on_scene_hierarchy_updated(self, data) -> None:
        if not self.hierarchy_panel or not hasattr(self.hierarchy_panel, "update_tree"):
            return
        if not isinstance(data, dict):
            return
        nodes = data.get("nodes", [])
        connections = data.get("connections", [])
        try:
            self.hierarchy_panel.update_tree(nodes, connections)
        except Exception as exc:
            logger.debug("层级树更新失败: %s", exc)

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
            
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, "_update_hierarchy"):
                self.hierarchy_panel._update_hierarchy()
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
        # Dock title refresh belongs to the current Host Adapter. This callback
        # refreshes only the legacy content bridge owned by this plugin.
        try:
            if self.hierarchy_panel and hasattr(self.hierarchy_panel, "setHeaderLabel"):
                self.hierarchy_panel.setHeaderLabel(
                    self._t("hierarchy.header.scene", "场景")
                )
        except Exception:
            __import__("logging").getLogger(__name__).debug(
                "Ignored recoverable exception.", exc_info=True
            )
