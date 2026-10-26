"""项目资源浏览器 Dock：工程内资产与场景文件导航。

排错: 见 `builtin/README.md`。
"""

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("ProjectBrowserPlugin")


class ProjectBrowserPlugin(IRuntimePlugin):
    """项目浏览器插件 - 显示和管理项目资源"""
    
    DOCK_ID = "Project"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "ProjectBrowserPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "项目资源浏览器，显示组件库和资源",
            "dependencies": [],
            "provides": ["dock", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "project_browser.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "project_browser.title",
                    "default_title": "项目",
                    "area": "bottom",
                    "default_visible": True,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 50,
                    "refresh_events": ["language_changed"],
                }
            ],
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.dock = None
        self.project_panel = None
        self._event_subscriptions = []

        bindings = (
            ("project_opened", self.on_project_opened),
            ("create_asset", self.on_create_asset),
            ("refresh_project_browser", self.on_refresh_project_browser),
            ("language_changed", self._on_language_changed),
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
        self.project_panel = None
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
                        "project_browser.log.unsubscribe_failed",
                        "⚠️ ProjectBrowser 取消订阅失败: {error}",
                    ).format(error=error)
                )
        self._event_subscriptions.extend(failed)

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
            self._handle_project_reference(project_path)
            return
        if os.path.isdir(asset_path) and os.path.isfile(
            os.path.join(asset_path, "project.json")
        ):
            self._handle_project_reference(asset_path)
            return
        if asset_path.endswith(".pond"):
            logger.info(
                self._t("project_browser.log.open_scene", "🌊 正在打开场景: {path}").format(
                    path=asset_path
                )
            )
            from core.VitaLoom.commands.registry import get_command_registry

            result = get_command_registry().run("scene.open", {"scene_path": asset_path})
            if not result.get("ok"):
                logger.warning("打开场景失败: %s", result.get("error"))
        elif asset_path.endswith((".py", ".json", ".txt")):
            logger.info(self._t("project_browser.log.open_file", "📄 正在打开文件: {path}").format(path=asset_path))
            # 这里可以集成代码编辑器，目前先通过系统关联打开
            import webbrowser
            webbrowser.open(asset_path)
    
    def on_create_asset(self, data: Dict[str, Any]):
        """?????????"""
        asset_type = data.get("type")
        asset_name = data.get("name")
        folder = data.get("folder")

        if not asset_name or not folder:
            return

        try:
            from core.VitaLoom.commands.registry import get_command_registry

            result = get_command_registry().run(
                "asset.create",
                {
                    "project_path": str(getattr(self.context, "current_project_path", "") or ""),
                    "asset_type": str(asset_type or ""),
                    "name": str(asset_name or ""),
                    "folder": str(folder or ""),
                },
            )
            if not result.get("ok"):
                logger.warning("??????: %s", result.get("error"))
                return
            file_path = result.get("result", {}).get("path", "")
            logger.info(self._t("project_browser.log.asset_created", "? ?????: {path}").format(path=file_path))
            if self.project_panel and hasattr(self.project_panel, '_refresh_folder'):
                self.project_panel._refresh_folder()
        except Exception as e:
            logger.warning(self._t("project_browser.log.asset_create_failed", "? ??????: {error}").format(error=e))

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
    

    def _handle_project_reference(self, project_path: str) -> None:
        import os

        current = str(getattr(self.context, "current_project_path", "") or "")
        if current and os.path.normcase(os.path.abspath(current)) == os.path.normcase(
            os.path.abspath(project_path)
        ):
            logger.info(
                self._t(
                    "project_browser.log.project_already_open",
                    "当前项目已打开: {path}",
                ).format(path=project_path)
            )
            return
        logger.warning(
            self._t(
                "project_browser.log.cross_project_blocked",
                "编辑器会话只绑定当前项目；请回到 Hub 打开项目: {path}",
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

    def _on_language_changed(self, _data):
        # Dock shell localization belongs to the current Host Adapter. Keep the
        # concrete ProjectPanel instance and refresh only its content labels.
        panel = self.project_panel
        refresh = getattr(panel, "retranslate_ui", None)
        if callable(refresh):
            refresh()
