"""场景编辑视口插件：静态场景布置（非 SR 游戏播放视口）。

排错: 播放/模拟见 `game_viewport_plugin`；见 `builtin/README.md`。
"""

from core.plugin.interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("SceneViewportPlugin")


class SceneViewportPlugin(IViewportProvider):
    """场景视口插件 - 场景级编辑视口"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "SceneViewport",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "场景编辑视口，用于编辑场景中的对象",
            "dependencies": [],
            "provides": ["viewport"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.viewport = None
        
        # 订阅项目打开和场景加载事件
        editor_context.event_bus.subscribe("project_opened", self.on_project_opened)
        editor_context.event_bus.subscribe("scene_loaded", self.on_scene_loaded)
        # 订阅创建实体事件
        editor_context.event_bus.subscribe("create_entity", self.on_create_entity)
        # 订阅删除实体事件
        editor_context.event_bus.subscribe("delete_entity", self.on_delete_entity)
        # 订阅添加脚本事件
        editor_context.event_bus.subscribe("add_script_to_entity", self.on_add_script)
        editor_context.event_bus.subscribe("add_component_to_entity", self.on_add_component)
        editor_context.event_bus.subscribe("set_entity_sprite_path", self.on_set_entity_sprite_path)
        editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_project_opened(self, data):
        """项目打开时强制刷新画布（与 scene_loaded 双保险）。"""
        try:
            project_path = data if isinstance(data, str) else data.get("path", "")
            logger.info(self._t("scene_viewport.log.project_opened", "📐 项目已打开: {path}").format(path=project_path))
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            path = get_scene_manager().get_current_scene_path() or ""
            self.on_scene_loaded(path)
        except Exception as e:
            logger.warning(self._t("scene_viewport.log.project_opened_failed", "⚠️  处理项目打开事件失败: {error}").format(error=e))
    
    def on_scene_loaded(self, data):
        """场景加载时处理（path 为空时清空画布）。"""
        try:
            scene_path = data if isinstance(data, str) else data.get("path", "")
            logger.info(self._t("scene_viewport.log.scene_loaded", "📐 场景已加载: {path}").format(path=scene_path))
            
            if not self.viewport or not hasattr(self.viewport, "load_scene_data"):
                return
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            scene_manager = get_scene_manager()
            scene_data = scene_manager.get_scene_data()
            if scene_data:
                self.viewport.load_scene_data(scene_data)
                logger.info(self._t("scene_viewport.log.scene_data_loaded", "✅ 场景数据已加载到视口"))
            else:
                self.viewport.load_scene_data({"entities": [], "connections": []})
                self.viewport.update()
                logger.info(self._t("scene_viewport.log.scene_cleared", "✅ 场景视口已清空"))
        except Exception as e:
            logger.exception(
                self._t("scene_viewport.log.scene_loaded_failed", "⚠️  处理场景加载事件失败: {error}").format(error=e)
            )
    
    def on_create_entity(self, data):
        """创建实体事件处理"""
        try:
            if not self.viewport:
                return
            
            # 获取实体信息
            entity_name = data.get("entity_name", data.get("entity_type", "Entity"))
            entity_type = data.get("entity_type", "organism")
            position = data.get("position", [0, 0])
            sprite_path = data.get("sprite_path", "")  # 新增：获取图片路径
            
            # 如果viewport是SceneViewport，调用创建节点方法
            if hasattr(self.viewport, 'create_entity_node'):
                self.viewport.create_entity_node(entity_name, entity_type, position, sprite_path)
            elif hasattr(self.viewport, 'nodes'):
                # 使用Node类创建节点
                from core.VitaLoom.viewports.scene_viewport import Node
                pos_x = float(position[0]) if len(position) > 0 else 0.0
                pos_y = float(position[1]) if len(position) > 1 else 0.0
                
                # 生成唯一ID
                import uuid
                entity_id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
                
                node = Node(entity_id, pos_x, pos_y, entity_type)
                
                # 如果是sprite类型，设置图片路径
                if entity_type == "sprite" and sprite_path:
                    node.sprite_path = sprite_path
                    node.name = entity_name
                    node.radius = 40  # sprite稍微大一点
                
                self.viewport.nodes.append(node)
                self.viewport.update()
                
                # 通知Hierarchy面板同步
                self.context.event_bus.publish("entity_created_in_scene", {
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "node_data": node.to_dict()
                })
                
                logger.info(
                    self._t("scene_viewport.log.entity_created", "✅ 已创建实体: {name} ({id})").format(
                        name=entity_name, id=entity_id
                    )
                )
        except Exception as e:
            logger.exception(
                self._t("scene_viewport.log.entity_create_failed", "⚠️  创建实体失败: {error}").format(error=e)
            )

    def on_delete_entity(self, data):
        """删除实体事件处理"""
        try:
            if not self.viewport:
                return
            
            entity_data = data.get("entity")
            if not entity_data:
                return
                
            entity_id = entity_data.get("id")
            if not entity_id:
                return
            
            # 在视口中寻删除对应节点
            if hasattr(self.viewport, 'nodes'):
                nodes_to_remove = [n for n in self.viewport.nodes if n.id == entity_id]
                for node in nodes_to_remove:
                    # 使用视口的删除逻辑（如果有）
                    if hasattr(self.viewport, '_delete_node_by_instance'):
                        self.viewport._delete_node_by_instance(node)
                    else:
                        # 备选：直接从列表删除并清理连接
                        self.viewport.nodes.remove(node)
                        if hasattr(self.viewport, 'connections'):
                            self.viewport.connections = [c for c in self.viewport.connections 
                                                       if c.start_node != node and c.end_node != node]
                
                self.viewport.update()
                logger.info(self._t("scene_viewport.log.entity_removed", "🗑️  已移除实体: {id}").format(id=entity_id))
                
                # 更新场景管理器数据
                from core.VitaLoom.scene.scene_manager import get_scene_manager
                sm = get_scene_manager()
                scene_data = sm.get_scene_data()
                if scene_data and "entities" in scene_data:
                    scene_data["entities"] = [e for e in scene_data["entities"] if e.get("id") != entity_id]
                    sm.update_scene_data(scene_data)
        except Exception as e:
            logger.warning(self._t("scene_viewport.log.entity_delete_failed", "⚠️  删除实体失败: {error}").format(error=e))

    def on_add_script(self, data: Dict[str, Any]):
        """处理添加脚本事件"""
        try:
            if not self.viewport:
                return
            
            entity_info = data.get("entity")
            script_data = data.get("script")
            
            if not entity_info or not script_data:
                return
                
            entity_id = None
            if isinstance(entity_info, dict):
                entity_id = entity_info.get("id")
                if entity_id is None and entity_info.get("type") == "entity":
                    inner = entity_info.get("data") or {}
                    entity_id = inner.get("id")
            else:
                entity_id = getattr(entity_info, "id", None)
            if not entity_id:
                return

            # 在视口中寻找对应节点
            found_node = None
            if hasattr(self.viewport, 'nodes'):
                for node in self.viewport.nodes:
                    if node.id == entity_id:
                        found_node = node
                        break
            
            if found_node:
                # 检查是否已存在同名脚本
                script_name = script_data.get("name")
                if not any(s.get("name") == script_name for s in found_node.scripts):
                    found_node.scripts.append(script_data)
                    # 同步场景数据
                    from core.VitaLoom.scene.scene_manager import get_scene_manager
                    sm = get_scene_manager()
                    scene_data = sm.get_scene_data()
                    if scene_data and "entities" in scene_data:
                        for entity in scene_data["entities"]:
                            if entity.get("id") == entity_id:
                                scripts = entity.get("scripts", [])
                                if not any(s.get("name") == script_name for s in scripts):
                                    scripts.append(script_data)
                                entity["scripts"] = scripts
                                break
                        sm.update_scene_data({"entities": scene_data["entities"]})

                    logger.info(
                        self._t("scene_viewport.log.script_added", "✅ 已添加脚本 {script} 到节点 {id}").format(
                            script=script_name, id=entity_id
                        )
                    )
                    # 同步上下文选中并刷新检视器
                    self.context.set_selection([found_node])
                else:
                    logger.warning(
                        self._t("scene_viewport.log.script_exists", "⚠️  节点 {id} 已存在脚本 {script}").format(
                            id=entity_id, script=script_name
                        )
                    )
                    
        except Exception as e:
            logger.exception(
                self._t("scene_viewport.log.add_script_failed", "⚠️  添加脚本失败: {error}").format(error=e)
            )


    def on_set_entity_sprite_path(self, data: Dict[str, Any]):
        """拖入或设置实体贴图路径，同步节点与场景 JSON。"""
        try:
            if not self.viewport:
                return
            entity_info = data.get("entity")
            sprite_path = data.get("sprite_path")
            if not entity_info or not sprite_path:
                return

            entity_id = None
            if isinstance(entity_info, dict):
                entity_id = entity_info.get("id")
                if entity_id is None and entity_info.get("type") == "entity":
                    inner = entity_info.get("data") or {}
                    entity_id = inner.get("id")
            else:
                entity_id = getattr(entity_info, "id", None)
            if not entity_id:
                return

            from core.VitaLoom.scene.scene_manager import get_scene_manager

            sm = get_scene_manager()
            found_node = None
            if hasattr(self.viewport, "nodes"):
                for node in self.viewport.nodes:
                    if node.id == entity_id:
                        found_node = node
                        if hasattr(node, "set_sprite_path"):
                            node.set_sprite_path(str(sprite_path))
                        else:
                            node.sprite_path = str(sprite_path)
                            node._cached_pixmap = None  # type: ignore[attr-defined]
                        break

            scene_data = sm.get_scene_data()
            if scene_data and "entities" in scene_data:
                for entity in scene_data["entities"]:
                    if entity.get("id") == entity_id:
                        entity["sprite_path"] = str(sprite_path)
                        break
                sm.update_scene_data({"entities": scene_data["entities"]})

            if hasattr(self.viewport, "update"):
                self.viewport.update()

            logger.info(
                self._t(
                    "scene_viewport.log.sprite_set",
                    "已设置实体 {id} 贴图: {path}",
                ).format(id=entity_id, path=sprite_path)
            )
            if found_node is not None:
                self.context.set_selection([found_node])
            else:
                self.context.set_selection([entity_info])
        except Exception as e:
            logger.warning(self._t("scene_viewport.log.sprite_set_failed", "设置贴图失败: {error}").format(error=e))


    def on_add_component(self, data: Dict[str, Any]):
        """处理添加组件事件（与脚本结构兼容，先写入 scripts 列表）。"""
        try:
            entity_info = data.get("entity")
            component_type = data.get("component_type")
            component_data = data.get("component_data", {})
            if not entity_info or not component_type:
                return

            script_payload = {
                "name": component_type,
                "type": component_type,
                "properties": component_data.get("properties", {}),
            }

            self.on_add_script({
                "entity": entity_info,
                "script": script_payload,
            })
        except Exception as e:
            logger.exception(
                self._t("scene_viewport.log.add_component_failed", "⚠️  添加组件失败: {error}").format(error=e)
            )

    def on_unload(self):
        # 取消订阅
        if hasattr(self, 'context') and self.context:
            try:
                self.context.event_bus.unsubscribe("project_opened", self.on_project_opened)
                self.context.event_bus.unsubscribe("scene_loaded", self.on_scene_loaded)
                self.context.event_bus.unsubscribe("create_entity", self.on_create_entity)
                self.context.event_bus.unsubscribe("delete_entity", self.on_delete_entity)
                self.context.event_bus.unsubscribe("add_script_to_entity", self.on_add_script)
                self.context.event_bus.unsubscribe("add_component_to_entity", self.on_add_component)
                self.context.event_bus.unsubscribe("set_entity_sprite_path", self.on_set_entity_sprite_path)
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.warning(self._t("scene_viewport.log.unsubscribe_failed", "⚠️  SceneViewport 取消订阅失败: {error}").format(error=e))
        
        if self.viewport:
            self.viewport.deleteLater()
    
    def create_viewport_widget(self) -> QWidget:
        """创建场景视口部件"""
        # 尝试复用现有的 SceneViewport
        try:
            from core.VitaLoom.viewports.scene_viewport import SceneViewport
            self.viewport = SceneViewport()
            logger.info(self._t("scene_viewport.log.created", "✅ 场景视口创建成功"))
        except Exception as e:
            logger.exception(
                self._t("scene_viewport.log.load_failed", "⚠️  无法加载 SceneViewport: {error}").format(error=e)
            )
            # 如果导入失败，创建一个简单的占位符
            try:
                from PyQt6.QtWidgets import QLabel, QVBoxLayout
                from PyQt6.QtCore import Qt as QtCore
                widget = QWidget()
                layout = QVBoxLayout(widget)
                label = QLabel(self._t("scene_viewport.placeholder", "场景视口\n\n场景编辑视图将显示在这里。"))
                label.setAlignment(QtCore.AlignmentFlag.AlignCenter)
                label.setStyleSheet("font-size: 14px; color: #888;")
                layout.addWidget(label)
                self.viewport = widget
                logger.info(self._t("scene_viewport.log.placeholder_created", "✅ 已创建场景视口占位符"))
            except Exception as e2:
                logger.warning(self._t("scene_viewport.log.placeholder_failed", "❌ 创建占位符失败: {error}").format(error=e2))
                # 最后的备选方案
                self.viewport = QWidget()
        
        return self.viewport
    
    def get_viewport_id(self) -> str:
        return "scene"
    
    def get_viewport_name(self) -> str:
        return self._t("scene_viewport.name", "场景")
    
    def on_viewport_activated(self):
        """场景视口被激活"""
        logger.debug("📐 %s", self._t('scene_viewport.activated', '场景视口已激活'))
    
    def on_viewport_deactivated(self):
        """场景视口被停用"""
        logger.debug("📐 %s", self._t('scene_viewport.deactivated', '场景视口已停用'))

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        # 刷新标签页名称（LayoutManager 在 add_viewport 时会缓存 tab text）
        if self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            try:
                if getattr(lm, "viewport_tabs", None) and self.viewport:
                    tabs = lm.viewport_tabs
                    idx = tabs.indexOf(self.viewport)
                    if idx >= 0:
                        tabs.setTabText(idx, self.get_viewport_name())
            except Exception:
                pass
