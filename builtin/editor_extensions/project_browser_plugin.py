"""项目资源浏览器 Dock：工程内资产与场景文件导航。

排错: 见 `builtin/README.md`。
"""

from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any
import re

from core.VitaLoom.core.logger import get_logger

logger = get_logger("ProjectBrowserPlugin")


class ProjectBrowserPlugin(IDockProvider):
    """项目浏览器插件 - 显示和管理项目资源"""
    
    DOCK_ID = "Project"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "ProjectBrowser",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "项目资源浏览器，显示组件库和资源",
            "dependencies": [],
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None
        self.project_panel = None
        
        # 订阅项目打开事件，更新项目树
        editor_context.event_bus.subscribe("project_opened", self.on_project_opened)
        # 订阅资产创建事件
        editor_context.event_bus.subscribe("create_asset", self.on_create_asset)
        # 订阅刷新事件
        editor_context.event_bus.subscribe("refresh_project_browser", self.on_refresh_project_browser)
        editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_unload(self):
        # 取消订阅
        if hasattr(self, 'context') and self.context:
            try:
                self.context.event_bus.unsubscribe("project_opened", self.on_project_opened)
                self.context.event_bus.unsubscribe("create_asset", self.on_create_asset)
                self.context.event_bus.unsubscribe("refresh_project_browser", self.on_refresh_project_browser)
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.warning(self._t("project_browser.log.unsubscribe_failed", "⚠️  ProjectBrowser 取消订阅失败: {error}").format(error=e))
        
        if self.dock:
            self.dock.deleteLater()
    
    def on_project_opened(self, data):
        """项目打开时更新项目树"""
        try:
            project_path = data if isinstance(data, str) else data.get("path", "")
            logger.info(self._t("project_browser.log.opened", "📁 项目已打开: {path}").format(path=project_path))
            
            # 如果项目面板已创建，更新项目文件树
            if self.project_panel and hasattr(self.project_panel, 'on_project_opened'):
                self.project_panel.on_project_opened(project_path)
        except Exception as e:
            logger.warning(self._t("project_browser.log.opened_failed", "⚠️  处理项目打开事件失败: {error}").format(error=e))
    
    def on_asset_double_clicked(self, asset_path: str):
        """处理资源双击：工程根 / project.json / 场景 / 文本。"""
        import os

        if asset_path.lower().endswith("project.json"):
            project_path = os.path.dirname(asset_path)
            self._open_project_path(project_path)
            return
        if os.path.isdir(asset_path) and os.path.isfile(
            os.path.join(asset_path, "project.json")
        ):
            self._open_project_path(asset_path)
            return
        if asset_path.endswith(".pond"):
            logger.info(
                self._t("project_browser.log.open_scene", "🌊 正在打开场景: {path}").format(
                    path=asset_path
                )
            )
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            get_scene_manager().load_scene(asset_path)
        elif asset_path.endswith((".py", ".json", ".txt")):
            logger.info(self._t("project_browser.log.open_file", "📄 正在打开文件: {path}").format(path=asset_path))
            # 这里可以集成代码编辑器，目前先通过系统关联打开
            import webbrowser
            webbrowser.open(asset_path)
    
    def on_create_asset(self, data: Dict[str, Any]):
        """处理资产创建事件"""
        asset_type = data.get("type")
        asset_name = data.get("name")
        folder = data.get("folder")
        
        if not asset_name or not folder:
            return
            
        import os
        filename = asset_name
        content = "{}"
        
        if asset_type == "scene":
            if not filename.endswith(".pond"):
                filename += ".pond"
            # 使用 SceneManager 创建场景
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            project_path = self.context.current_project_path
            created_scene_path = get_scene_manager().create_scene(asset_name, project_path)
            if created_scene_path and self.project_panel and hasattr(self.project_panel, '_refresh_folder'):
                self.project_panel._refresh_folder()
            return # create_scene 会刷新
            
        elif asset_type == "entity":
            if not filename.endswith(".json"):
                filename += ".json"
            content = '{\n  "type": "entity",\n  "name": "' + asset_name + '",\n  "entity_type": "blank",\n  "components": [],\n  "scripts": [],\n  "children": []\n}'
            
        elif asset_type == "organism":
            if not filename.endswith(".json"):
                filename += ".json"
            content = '{\n  "type": "entity",\n  "name": "' + asset_name + '",\n  "entity_type": "organism",\n  "components": ["Transform", "Renderer"],\n  "scripts": [],\n  "children": []\n}'

        elif asset_type == "food":
            if not filename.endswith(".json"):
                filename += ".json"
            content = '{\n  "type": "entity",\n  "name": "' + asset_name + '",\n  "entity_type": "food",\n  "components": ["Transform", "Renderer", "Nutrition"],\n  "scripts": [],\n  "children": []\n}'

        elif asset_type == "component":
            if not filename.endswith(".py"):
                filename += ".py"
            class_name = self._to_valid_script_class_name(asset_name)
            content = (
                "from core.Lotucosm.scripts import ScriptBase\n\n"
                f"class {class_name}(ScriptBase):\n"
                f"    \"\"\"{asset_name} 脚本描述\"\"\"\n\n"
                "    def start(self):\n"
                "        \"\"\"初始化时调用一次\"\"\"\n"
                f"        print(f\"{{self.entity.id}}: {asset_name} 脚本已启动\")\n\n"
                "    def update(self, delta_time: float):\n"
                "        \"\"\"每帧更新\"\"\"\n"
                "        pass\n"
            )
            
        if asset_type == "folder":
            folder_path = os.path.join(folder, asset_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                logger.info(self._t("project_browser.log.folder_created", "📁 已创建文件夹: {path}").format(path=folder_path))
                if self.project_panel and hasattr(self.project_panel, '_refresh_folder'):
                    self.project_panel._refresh_folder()
                return
            except Exception as e:
                logger.warning(self._t("project_browser.log.folder_create_failed", "❌ 创建文件夹失败: {error}").format(error=e))
                return

        file_path = os.path.join(folder, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(self._t("project_browser.log.asset_created", "✅ 已创建资产: {path}").format(path=file_path))
            
            # 刷新面板
            if self.project_panel and hasattr(self.project_panel, '_refresh_folder'):
                self.project_panel._refresh_folder()
        except Exception as e:
            logger.warning(self._t("project_browser.log.asset_create_failed", "❌ 创建资产失败: {error}").format(error=e))

    def create_dock_widget(self) -> QDockWidget:
        """创建 Project Dock 窗口"""
        self.dock = QDockWidget(self._t("project_browser.title", "项目"))
        self.dock.setObjectName(self.DOCK_ID)
        
        # 尝试复用现有的 ProjectPanel
        try:
            from core.VitaLoom.docks.library_browser import ProjectPanel
            self.project_panel = ProjectPanel()
            # 连接双击信号
            self.project_panel.asset_double_clicked.connect(self.on_asset_double_clicked)
        except Exception as e:
            logger.warning(self._t("project_browser.log.load_panel_failed", "⚠️  无法加载 ProjectPanel: {error}").format(error=e))
            from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
            widget = QWidget()
            layout = QVBoxLayout(widget)
            label = QLabel(self._t("project_browser.placeholder", "项目\n\n组件库和资源会显示在这里。"))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            self.project_panel = widget
        
        self.dock.setWidget(self.project_panel)
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.BottomDockWidgetArea,
            "default_visible": True,
            "can_close": True
        }
    
    def _open_project_path(self, project_path: str) -> None:
        from core.VitaLoom.project.project_manager import get_project_manager

        pm = get_project_manager()
        if not pm.open_project(project_path):
            logger.warning(
                self._t(
                    "project_browser.log.open_project_failed",
                    "打开项目失败: {path}",
                ).format(path=project_path)
            )

    def on_refresh_project_browser(self, data):
        """刷新项目浏览器"""
        if self.project_panel and hasattr(self.project_panel, '_refresh_folder'):
            self.project_panel._refresh_folder()
            logger.info(self._t("project_browser.log.refreshed", "🔄 项目面板已刷新"))

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _to_valid_script_class_name(self, raw_name: str) -> str:
        sanitized = re.sub(r"[^0-9A-Za-z_]+", "_", raw_name or "")
        sanitized = sanitized.strip("_")
        if not sanitized:
            sanitized = "UserScript"
        if sanitized[0].isdigit():
            sanitized = f"Script_{sanitized}"

        # 统一转成 PascalCase，避免 class_name 含非法风格。
        parts = [p for p in sanitized.split("_") if p]
        if parts:
            sanitized = "".join(p[:1].upper() + p[1:] for p in parts)

        return sanitized

    def _on_language_changed(self, _data):
        if self.dock and self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            if hasattr(lm, "remove_dock"):
                lm.remove_dock(self.DOCK_ID)
            dock = self.create_dock_widget()
            lm.add_dock(dock, self.get_dock_config())