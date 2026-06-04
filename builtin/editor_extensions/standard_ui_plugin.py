"""标准菜单/工具栏插件：播放、暂停、停止等编辑器工作流入口。

排错: 见 `builtin/README.md`。
"""

import os

from core.plugin.interfaces import IMenuProvider
from typing import Dict, Any, List
from core.VitaLoom.core.logger import get_logger


logger = get_logger("StandardUIPlugin")


class StandardUIPlugin(IMenuProvider):
    """标准 UI 插件 - 提供基础菜单和工具栏"""
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "StandardUI",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "标准编辑器菜单和工具栏",
            "dependencies": ["Localization"],
            "provides": ["menu"],
            "protected": True,
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = None
        # 尝试获取内核引用
        if hasattr(editor_context, 'kernel'):
            self.kernel = editor_context.kernel
        if hasattr(self.context, "event_bus"):
            self.context.event_bus.subscribe("language_changed", self._on_language_changed)
            self.context.event_bus.subscribe("simulation_transport_state", self._on_transport_state)
            self.context.event_bus.subscribe("project_opened", self._on_project_opened)
        self._dock_guidance_seen: set[str] = set()
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            get_project_manager().recent_projects_changed.connect(
                self._on_recent_projects_changed
            )
        except Exception as e:
            logger.warning("订阅最近项目列表失败: %s", e)
    
    def on_unload(self):
        if hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
                self.context.event_bus.unsubscribe("simulation_transport_state", self._on_transport_state)
                self.context.event_bus.unsubscribe("project_opened", self._on_project_opened)
            except Exception as e:
                logger.warning("取消语言订阅失败: %s", e)
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            get_project_manager().recent_projects_changed.disconnect(
                self._on_recent_projects_changed
            )
        except Exception:
            pass

    def _log_error(self, action: str, error: Exception):
        """统一错误日志输出，便于排查 UI 菜单问题。"""
        logger.exception("%s失败: %s", action, error)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        file_menu = self._t("menu.file", "文件")
        items: List[Dict[str, Any]] = [
            # File 菜单
            {
                "path": f"{file_menu}/{self._t('menu.new_project', '新建项目')}",
                "action": self.new_project,
                "shortcut": "Ctrl+N"
            },
            {
                "path": f"{file_menu}/{self._t('menu.open_project', '打开项目')}",
                "action": self.open_project,
                "shortcut": "Ctrl+O"
            },
        ]
        items.extend(self._recent_project_menu_items(file_menu))
        items.extend([
            {
                "path": f"{file_menu}/{self._t('menu.save_project', '保存项目')}",
                "action": self.save_project,
                "shortcut": "Ctrl+Shift+P"
            },
            {
                "path": f"{self._t('menu.file', '文件')}/{self._t('menu.save_scene', '保存场景')}",
                "action": self.save_scene,
                "shortcut": "Ctrl+S"
            },
            {
                "path": f"{self._t('menu.file', '文件')}/{self._t('menu.save_as', '另存为')}",
                "action": self.save_project_as,
                "shortcut": "Ctrl+Shift+S"
            },
            {
                "path": f"{file_menu}/{self._t('menu.exit', '退出')}",
                "action": self.exit_application,
                "shortcut": "Alt+F4"
            },
        ])
        items.extend([
            # Edit 菜单
            {
                "path": f"{self._t('menu.edit', '编辑')}/{self._t('menu.undo', '撤销')}",
                "action": self.undo,
                "shortcut": "Ctrl+Z"
            },
            {
                "path": f"{self._t('menu.edit', '编辑')}/{self._t('menu.redo', '重做')}",
                "action": self.redo,
                "shortcut": "Ctrl+Y"
            },
            
            # View 菜单
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.scene_view', '场景视图')}",
                "action": self.switch_to_scene_view,
                "shortcut": "F1"
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.game_view', '游戏视图')}",
                "action": self.switch_to_game_view,
                "shortcut": "F2"
            },
            {
                "path": f"{self._t('menu.view', '视图')}/",
                "separator": True
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.layouts', '布局')}/{self._t('menu.save_layout', '保存布局')}",
                "action": self.save_layout,
                "shortcut": None
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.layouts', '布局')}/{self._t('menu.restore_layout', '恢复布局')}",
                "action": self.restore_layout,
                "shortcut": None
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.layouts', '布局')}/{self._t('menu.reset_layout', '重置布局')}",
                "action": self.reset_layout,
                "shortcut": None
            },
            {
                "path": f"{self._t('menu.view', '视图')}/",
                "separator": True
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.view_panels', '面板')}/{self._t('menu.show_simulation_dock', '显示模拟面板')}",
                "action": self.show_simulation_dock,
                "shortcut": "Ctrl+Shift+M",
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.view_panels', '面板')}/{self._t('menu.show_ecology_dock', '显示莲池生态')}",
                "action": self.show_ecology_dock,
                "shortcut": "Ctrl+Shift+E",
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.view_panels', '面板')}/{self._t('menu.toggle_inspector_float', '检视器：切换浮动')}",
                "action": self.toggle_inspector_float,
                "shortcut": None
            },
            {
                "path": f"{self._t('menu.view', '视图')}/{self._t('menu.view_panels', '面板')}/{self._t('menu.toggle_console_float', '控制台：切换浮动')}",
                "action": self.toggle_console_float,
                "shortcut": None
            },
            # Help 菜单
            {
                "path": f"{self._t('menu.help', '帮助')}/{self._t('menu.about', '关于')}",
                "action": self.show_about,
            },
        ])
        return items

    def _recent_project_menu_items(self, file_menu: str) -> List[Dict[str, Any]]:
        """动态「最近打开的项目」子菜单项。"""
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            recents = get_project_manager().get_recent_projects()
        except Exception:
            return []
        if not recents:
            return []
        recent_root = self._t("menu.recent_projects", "最近打开的项目")
        items: List[Dict[str, Any]] = [
            {"path": f"{file_menu}/", "separator": True},
        ]
        for project_path in recents:
            name = os.path.basename(project_path.rstrip("\\/")) or project_path
            items.append(
                {
                    "path": f"{file_menu}/{recent_root}/{name}",
                    "action": lambda _checked=False, p=project_path: self._open_recent_project(p),
                }
            )
        return items

    def _open_recent_project(self, project_path: str) -> None:
        """从最近列表打开项目（统一走 ProjectManager.open_project）。"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from core.VitaLoom.project.project_manager import get_project_manager

            project_json = os.path.join(project_path, "project.json")
            if not os.path.isfile(project_json):
                QMessageBox.warning(
                    self.kernel if self.kernel else None,
                    self._t("dialog.error.title", "错误"),
                    self._t(
                        "dialog.open_project.invalid_dir",
                        "选择的目录不是有效的项目目录（缺少 project.json）",
                    ),
                )
                return
            pm = get_project_manager()
            if not pm.open_project(project_path):
                QMessageBox.critical(
                    self.kernel if self.kernel else None,
                    self._t("dialog.error.title", "错误"),
                    self._t("dialog.open_project.failed", "打开项目失败，请检查项目文件"),
                )
        except Exception as e:
            self._log_error("打开最近项目", e)

    def _on_recent_projects_changed(self, _paths: List[str]) -> None:
        self._refresh_ui_texts()
    
    def _on_transport_state(self, _state):
        self._refresh_ui_texts()

    def _on_project_opened(self, _path) -> None:
        if not self.kernel or not hasattr(self.kernel, "layout_manager"):
            return
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            cfg = get_project_manager().get_current_project_config() or {}
            pres = cfg.get("presentation", {})
            msg = ""
            if isinstance(pres, dict):
                msg = str(pres.get("editor_entry_hint_zh") or pres.get("tagline_zh") or "").strip()
            if msg:
                self.kernel.layout_manager.statusbar.showMessage(msg, 9000)
        except Exception as e:
            logger.debug("项目引导状态栏失败: %s", e)

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        play_label = (
            transport.play_toolbar_label(self._t)
            if transport
            else f"▶ {self._t('toolbar.play', '运行')}"
        )
        return [
            {"text": f"📄 {self._t('toolbar.new', '新建')}", "action": self.new_project},
            {"text": f"💾 {self._t('toolbar.save', '保存')}", "action": self.save_project},
            {"separator": True},
            {"text": play_label, "action": self.play_simulation},
            {"text": f"⏹ {self._t('toolbar.stop', '停止')}", "action": self.stop_simulation},
        ]

    def _refresh_ui_texts(self):
        if not self.kernel or not hasattr(self.kernel, "layout_manager"):
            return
        lm = self.kernel.layout_manager
        if hasattr(lm, "remove_plugin_ui"):
            lm.remove_plugin_ui("StandardUI")
        lm.add_menu_items(self.get_menu_items(), "StandardUI")
        lm.add_toolbar_items(self.get_toolbar_items(), "StandardUI")

    def _on_language_changed(self, _data):
        self._refresh_ui_texts()
    
    # ========== File 菜单操作 ==========
    
    def new_project(self):
        """新建项目"""
        try:
            from core.VitaLoom.project.project_wizard import ProjectWizard
            from core.VitaLoom.project.project_manager import get_project_manager
            
            # 显示项目创建向导
            from PyQt6.QtWidgets import QDialog
            wizard = ProjectWizard(self.kernel if self.kernel else None)
            if wizard.exec() == QDialog.DialogCode.Accepted:
                project_path = wizard.get_created_project_path()
                if project_path:
                    # 自动打开创建的项目
                    project_manager = get_project_manager()
                    if project_manager.open_project(project_path):
                        logger.info("项目创建并打开成功: %s", project_path)
                    else:
                        logger.warning("项目创建成功，但打开失败: %s", project_path)
        except Exception as e:
            self._log_error("创建项目", e)
    
    def open_project(self):
        """打开项目"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            from core.VitaLoom.project.project_manager import get_project_manager
            
            project_manager = get_project_manager()
            
            # 打开文件对话框选择项目
            project_path = QFileDialog.getExistingDirectory(
                self.kernel if self.kernel else None,
                self._t("dialog.open_project.title", "打开项目"),
                project_manager.projects_dir
            )
            
            if project_path:
                # 检查是否是有效项目
                import os
                project_json = os.path.join(project_path, "project.json")
                if not os.path.exists(project_json):
                    QMessageBox.warning(
                        self.kernel if self.kernel else None,
                        self._t("dialog.error.title", "错误"),
                        self._t("dialog.open_project.invalid_dir", "选择的目录不是有效的项目目录（缺少 project.json）")
                    )
                    return
                
                # 打开项目
                if project_manager.open_project(project_path):
                    logger.info("项目打开成功: %s", project_path)
                else:
                    QMessageBox.critical(
                        self.kernel if self.kernel else None,
                        self._t("dialog.error.title", "错误"),
                        self._t("dialog.open_project.failed", "打开项目失败，请检查项目文件")
                    )
        except Exception as e:
            self._log_error("打开项目", e)
    
    def save_scene(self):
        """保存当前场景"""
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            from core.VitaLoom.viewports.scene_viewport import SceneViewport
            from PyQt6.QtWidgets import QMessageBox
            
            sm = get_scene_manager()
            if not sm.get_current_scene_path():
                return
                
            # 获取当前活动的视口并提取数据
            viewport_data = None
            if self.kernel and hasattr(self.kernel, 'layout_manager'):
                lm = self.kernel.layout_manager
                # 遍历所有视口寻找 SceneViewport
                for vp_id, vp_provider in lm.viewport_providers.items():
                    if hasattr(vp_provider, 'viewport') and isinstance(vp_provider.viewport, SceneViewport):
                        # 获取视口序列化数据
                        viewport_data = vp_provider.viewport.get_scene_data()
                        break
            
            # 保存
            if sm.save_scene(data=viewport_data):
                logger.info("场景保存成功: %s", sm.get_current_scene_path())
            else:
                QMessageBox.critical(
                    self.kernel if self.kernel else None,
                    self._t("dialog.error.title", "错误"),
                    self._t("dialog.save_scene.failed", "保存场景失败"),
                )
                
        except Exception as e:
            self._log_error("保存场景", e)

    def save_project(self):
        """保存项目"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from core.VitaLoom.project.project_manager import get_project_manager
            
            project_manager = get_project_manager()
            
            # 检查是否有当前项目
            if not self.context.current_project_path:
                QMessageBox.warning(
                    self.kernel if self.kernel else None,
                    self._t("dialog.warning.title", "警告"),
                    self._t("dialog.no_project", "没有打开的项目，请先创建或打开一个项目")
                )
                return
            
            # 保存项目
            if project_manager.save_project():
                logger.info("项目保存成功: %s", self.context.current_project_path)
            else:
                QMessageBox.critical(
                    self.kernel if self.kernel else None,
                    self._t("dialog.error.title", "错误"),
                    self._t("dialog.save_project.failed", "保存项目失败")
                )
        except Exception as e:
            self._log_error("保存项目", e)
    
    def save_project_as(self):
        """另存为"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            from core.VitaLoom.project.project_manager import get_project_manager
            import shutil
            import os
            
            project_manager = get_project_manager()
            
            # 检查是否有当前项目
            if not self.context.current_project_path:
                QMessageBox.warning(
                    self.kernel if self.kernel else None,
                    self._t("dialog.warning.title", "警告"),
                    self._t("dialog.no_project", "没有打开的项目，请先创建或打开一个项目")
                )
                return
            
            # 选择新路径
            new_path = QFileDialog.getExistingDirectory(
                self.kernel if self.kernel else None,
                self._t("dialog.save_as_project.title", "另存项目为"),
                project_manager.projects_dir
            )
            
            if new_path:
                # 复制项目到新路径
                old_path = self.context.current_project_path
                try:
                    # 如果目标路径已存在，询问是否覆盖
                    if os.path.exists(new_path) and os.listdir(new_path):
                        reply = QMessageBox.question(
                            self.kernel if self.kernel else None,
                            self._t("dialog.confirm.title", "确认"),
                            self._t("dialog.save_as_project.overwrite", "目标目录 '{path}' 已存在且不为空，是否覆盖？").format(path=new_path),
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return
                    
                    # 复制项目文件
                    if os.path.exists(new_path):
                        shutil.rmtree(new_path)
                    shutil.copytree(old_path, new_path)
                    
                    # 更新项目名称（从路径获取）
                    new_name = os.path.basename(new_path)
                    project_json = os.path.join(new_path, "project.json")
                    if os.path.exists(project_json):
                        import json
                        with open(project_json, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                        project_data['name'] = new_name
                        with open(project_json, 'w', encoding='utf-8') as f:
                            json.dump(project_data, f, indent=2, ensure_ascii=False)
                    
                    # 打开新项目
                    if project_manager.open_project(new_path):
                        logger.info("项目另存为成功: %s", new_path)
                    else:
                        QMessageBox.warning(
                            self.kernel if self.kernel else None,
                            self._t("dialog.warning.title", "警告"),
                            self._t("dialog.save_as_project.open_failed", "项目已复制，但打开失败")
                        )
                except Exception as e:
                    self._log_error("另存项目(内部复制)", e)
                    QMessageBox.critical(
                        self.kernel if self.kernel else None,
                        self._t("dialog.error.title", "错误"),
                        self._t("dialog.save_as_project.failed", "另存项目失败: {error}").format(error=str(e))
                    )
        except Exception as e:
            self._log_error("另存项目", e)
    
    def exit_application(self):
        """退出应用"""
        if self.kernel:
            self.kernel.close()
    
    # ========== Edit 菜单操作 ==========
    
    def undo(self):
        """撤销"""
        try:
            # 尝试从当前活动的视口获取命令栈
            if self.kernel and self.kernel.layout_manager:
                current_viewport = self.kernel.layout_manager.get_current_viewport()
                if current_viewport and hasattr(current_viewport, 'command_stack'):
                    if current_viewport.command_stack.can_undo():
                        current_viewport.command_stack.undo()
                        logger.info("撤销成功")
                        if hasattr(current_viewport, 'update'):
                            current_viewport.update()
                    else:
                        logger.warning("没有可撤销的操作")
                else:
                    logger.warning("当前视口不支持撤销功能")
        except Exception as e:
            self._log_error("撤销", e)
    
    def redo(self):
        """重做"""
        try:
            # 尝试从当前活动的视口获取命令栈
            if self.kernel and self.kernel.layout_manager:
                current_viewport = self.kernel.layout_manager.get_current_viewport()
                if current_viewport and hasattr(current_viewport, 'command_stack'):
                    if current_viewport.command_stack.can_redo():
                        current_viewport.command_stack.redo()
                        logger.info("重做成功")
                        if hasattr(current_viewport, 'update'):
                            current_viewport.update()
                    else:
                        logger.warning("没有可重做的操作")
                else:
                    logger.warning("当前视口不支持重做功能")
        except Exception as e:
            self._log_error("重做", e)
    
    # ========== View 菜单操作 ==========
    
    def switch_to_scene_view(self):
        """切换到场景视图"""
        if self.kernel:
            self.kernel.layout_manager.switch_viewport("scene")
    
    def switch_to_game_view(self):
        """切换到游戏视图"""
        if self.kernel:
            self.kernel.layout_manager.switch_viewport("game")
    
    # ========== Layout 管理操作 ==========
    
    def save_layout(self):
        """保存当前布局（参考Unity的布局保存功能）"""
        if self.kernel and self.kernel.layout_manager:
            self.kernel.layout_manager.save_layout()
    
    def restore_layout(self):
        """恢复保存的布局"""
        if self.kernel and self.kernel.layout_manager:
            self.kernel.layout_manager.restore_layout()
    
    def reset_layout(self):
        """重置为默认布局"""
        if self.kernel and self.kernel.layout_manager:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self.kernel,
                self._t("dialog.reset_layout.title", "确认重置布局"),
                self._t("dialog.reset_layout.content", "确定要重置为默认布局吗？当前布局将被覆盖。"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.kernel.layout_manager.reset_layout()

    def toggle_inspector_float(self):
        """检视器在浮动窗口与主窗口停靠区之间切换（几何由 LayoutManager 记忆）。"""
        self._toggle_dock_floating("Inspector")

    def toggle_console_float(self):
        """控制台在浮动窗口与主窗口停靠区之间切换。"""
        self._toggle_dock_floating("Console")

    def show_simulation_dock(self):
        """视图 → 面板 → 显示模拟 Dock。"""
        self._show_dock("SimulationControl")

    def show_ecology_dock(self):
        """视图 → 面板 → 显示莲池生态 Dock。"""
        self._show_dock("EcologyDashboard")

    def _show_dock(self, dock_title: str) -> None:
        if not self.kernel or not getattr(self.kernel, "layout_manager", None):
            return
        lm = self.kernel.layout_manager
        show = getattr(lm, "show_dock", None)
        shown = False
        if callable(show):
            shown = bool(show(dock_title, floating=False))
            if not shown:
                logger.warning("未找到 Dock: %s（插件可能尚未加载）", dock_title)
        else:
            docks = getattr(lm, "docks", None)
            if not docks or dock_title not in docks:
                logger.warning("未找到 Dock: %s", dock_title)
                return
            dock = docks[dock_title]
            dock.setFloating(False)
            dock.setVisible(True)
            dock.show()
            dock.raise_()
            shown = True
        if shown:
            self._maybe_show_dock_guidance(dock_title)

    _DOCK_GUIDANCE_KEYS = {
        "SimulationControl": "standard_ui.dock_hint.simulation",
        "EcologyDashboard": "standard_ui.dock_hint.ecology",
    }

    def _maybe_show_dock_guidance(self, dock_title: str) -> None:
        key = self._DOCK_GUIDANCE_KEYS.get(dock_title)
        if not key or dock_title in self._dock_guidance_seen:
            return
        self._dock_guidance_seen.add(dock_title)
        sb = getattr(getattr(self.kernel, "layout_manager", None), "statusbar", None)
        if sb is None:
            return
        defaults = {
            "standard_ui.dock_hint.simulation": "倍速与高级模拟参数在此；日常播放请用顶部 ▶ / ⏹。",
            "standard_ui.dock_hint.ecology": "▶ 运行后显示种群、代谢与 SR 统计；适合复盘与调参。",
        }
        sb.showMessage(self._t(key, defaults.get(key, "")), 8000)

    def _toggle_dock_floating(self, dock_title: str):
        if not self.kernel or not getattr(self.kernel, "layout_manager", None):
            return
        lm = self.kernel.layout_manager
        docks = getattr(lm, "docks", None)
        if not docks or dock_title not in docks:
            logger.warning("未找到 Dock: %s（插件可能尚未加载）", dock_title)
            return
        toggle = getattr(lm, "toggle_dock_floating", None)
        if callable(toggle):
            toggle(dock_title)
        else:
            dock = docks[dock_title]
            dock.setFloating(not dock.isFloating())
        dock = docks.get(dock_title)
        if dock:
            dock.setVisible(True)
            dock.show()
            dock.raise_()
            if dock.isFloating():
                dock.activateWindow()
    
    # ========== Playback 操作 ==========
    
    def play_simulation(self):
        """工具栏唯一 transport：运行 / 继续 / 暂停。"""
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_toggle()
            return
        logger.info(self._t("standard_ui.play_simulation", "运行模拟"))
        if self.kernel:
            self.kernel.layout_manager.switch_viewport("game")
        self.context.event_bus.publish("simulation_play")

    def pause_simulation(self):
        """菜单/快捷键备用入口。"""
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_pause()
            return
        self.context.event_bus.publish("simulation_pause")

    def stop_simulation(self):
        """停止模拟并回到场景视口。"""
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_stop()
            return
        self.context.event_bus.publish("simulation_stop")
        if self.kernel:
            self.kernel.layout_manager.switch_viewport("scene")
    
    # ========== Help 菜单操作 ==========
    
    def show_about(self):
        """显示关于对话框"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self.kernel if self.kernel else None,
            self._t("about.title", "关于 VitaLoom Engine"),
            self._t(
                "about.content",
                "VitaLoom Engine v1.0.0\n\n基于继承算法的生命模拟引擎\n高度模块化插件架构\n\n© 2026 VitaLoom Team",
            ),
        )
