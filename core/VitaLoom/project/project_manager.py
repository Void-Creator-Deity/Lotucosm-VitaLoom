# -*- coding: utf-8 -*-
"""项目管理器：`projects/` 下 project.json 生命周期与最近列表。

排错: 见 core/VitaLoom/README.md「项目打不开」
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus
from core.VitaLoom.core.logger import get_logger


logger = get_logger("ProjectManager")


class ProjectManager(QObject):
    """职责: 单例管理项目路径、配置与 EditorContext.current_project_path。
    时机: 启动向导或「打开项目」；关闭时 `close_project`。
    不变量: `open_project` 成功须加载 project.json 并应用插件策略字段。
    排错: 最近列表空 → data/system/editor_config.json；路径不存在会被过滤。
    """
    
    # 信号
    project_created = pyqtSignal(str)  # 项目路径
    project_opened = pyqtSignal(str)  # 项目路径
    project_saved = pyqtSignal(str)  # 项目路径
    project_closed = pyqtSignal()
    recent_projects_changed = pyqtSignal(list)  # 最近项目列表
    
    _instance: Optional['ProjectManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ProjectManager.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        
        self.editor_context = get_editor_context()
        self.signal_bus = get_signal_bus()
        
        # 项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.projects_dir = os.path.join(project_root, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        
        # 最近项目列表（最多10个）
        self.max_recent_projects = 10
        self._recent_projects: List[str] = []
        self._load_recent_projects()
        
        # 项目模板目录
        self.templates_dir = os.path.join(project_root, "data", "ponds", "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def _read_editor_config(self) -> Dict[str, Any]:
        """读取 data/system/editor_config.json。"""
        config_file = self._get_config_file()
        if not os.path.exists(config_file):
            return {}
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("读取编辑器配置失败: %s", e)
            return {}

    def _write_editor_config(self, config: Dict[str, Any]) -> None:
        config_file = self._get_config_file()
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("保存编辑器配置失败: %s", e)

    @staticmethod
    def _is_ephemeral_project_path(path: str) -> bool:
        """过滤单测/临时目录，避免污染最近项目与启动恢复。"""
        norm = os.path.normcase(os.path.abspath(path))
        markers = (
            os.path.normcase(os.path.join(os.environ.get("TEMP", ""), "")),
            os.path.normcase(os.path.join(os.environ.get("TMP", ""), "")),
            os.path.normcase("/tmp/"),
        )
        for marker in markers:
            if marker and len(marker) > 3 and norm.startswith(marker):
                return True
        parts = {os.path.normcase(p) for p in os.path.normpath(norm).split(os.sep)}
        if "tmp" in parts or "temp" in parts:
            return True
        for part in parts:
            if part.startswith("_pytest"):
                return True
        return False

    def _sanitize_recent_projects(self) -> None:
        cleaned = []
        for p in self._recent_projects:
            if not isinstance(p, str):
                continue
            if not os.path.exists(p):
                continue
            if self._is_ephemeral_project_path(p):
                continue
            if not os.path.isfile(os.path.join(p, "project.json")):
                continue
            cleaned.append(p)
        if cleaned != self._recent_projects:
            self._recent_projects = cleaned
            self._save_recent_projects()

    def _load_recent_projects(self):
        """加载最近项目列表"""
        config = self._read_editor_config()
        self._recent_projects = config.get("recent_projects", [])
        if not isinstance(self._recent_projects, list):
            self._recent_projects = []
        self._sanitize_recent_projects()
        self._sanitize_editor_config()

    def _sanitize_editor_config(self) -> None:
        """剔除无效 last_opened_project 并写回 editor_config.json。"""
        config = self._read_editor_config()
        changed = False
        last = config.get("last_opened_project")
        if isinstance(last, str) and last.strip():
            path = os.path.abspath(last)
            valid = (
                not self._is_ephemeral_project_path(path)
                and os.path.isfile(os.path.join(path, "project.json"))
            )
            if not valid:
                config.pop("last_opened_project", None)
                changed = True
        elif last is not None:
            config.pop("last_opened_project", None)
            changed = True
        if changed:
            config["recent_projects"] = self._recent_projects
            self._write_editor_config(config)
            logger.info("已清理无效的 last_opened_project 配置项")

    def _save_recent_projects(self):
        """保存最近项目列表（保留 last_opened_project）。"""
        config = self._read_editor_config()
        config["recent_projects"] = self._recent_projects
        self._write_editor_config(config)

    def _set_last_opened_project(self, project_path: str) -> None:
        config = self._read_editor_config()
        config["last_opened_project"] = os.path.abspath(project_path)
        config["recent_projects"] = self._recent_projects
        self._write_editor_config(config)

    def get_last_opened_project(self) -> Optional[str]:
        """返回上次成功打开的项目路径；无效则 None。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        path = self._read_editor_config().get("last_opened_project")
        if not isinstance(path, str) or not path:
            return None
        path = os.path.abspath(path)
        if self._is_ephemeral_project_path(path):
            return None
        if os.path.isfile(os.path.join(path, "project.json")):
            return path
        return None

    def flush_current_project(self) -> None:
        """退出或切换前：合并视口、保存场景并写入 active_scene。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        path = self.editor_context.current_project_path
        if path:
            self._flush_before_project_switch(path)

    def open_last_project_on_startup(self) -> bool:
        """启动时恢复上次项目；无记录则尝试最近列表首项。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if os.environ.get("VITALOOM_SKIP_AUTO_OPEN", "0") == "1":
            logger.info("已跳过启动自动打开项目 (VITALOOM_SKIP_AUTO_OPEN)")
            return False
        if self.editor_context.current_project_path:
            return False
        path = self.get_last_opened_project()
        if not path:
            recents = self.get_recent_projects()
            path = recents[0] if recents else None
        if not path:
            return False
        logger.info("启动恢复项目: %s", path)
        return self.open_project(path)
    
    def _get_config_file(self) -> str:
        """获取配置文件路径"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        config_dir = os.path.join(project_root, "data", "system")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "editor_config.json")
    
    def _add_to_recent_projects(self, project_path: str):
        """添加到最近项目列表"""
        if self._is_ephemeral_project_path(project_path):
            return
        # 移除已存在的
        if project_path in self._recent_projects:
            self._recent_projects.remove(project_path)
        
        # 添加到开头
        self._recent_projects.insert(0, project_path)
        
        # 限制数量
        if len(self._recent_projects) > self.max_recent_projects:
            self._recent_projects = self._recent_projects[:self.max_recent_projects]
        
        # 保存
        self._save_recent_projects()
        self.recent_projects_changed.emit(self._recent_projects.copy())
    
    def get_recent_projects(self) -> List[str]:
        """获取最近项目列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._sanitize_recent_projects()
        return self._recent_projects.copy()
    
    def create_project(self, project_name: str, project_path: Optional[str] = None, 
                      template: Optional[str] = None, description: str = "") -> Optional[str]:
        """创建新项目目录与默认 assets/scripts/scenes。

        职责:
            在 projects_dir 下建目录并写入项目元数据 JSON。

        时机:
            项目向导或「新建项目」菜单确认后。

        不变量:
            已存在同名路径时返回 None，不覆盖。

        排错:
            目录创建失败 → 查路径权限与 projects_dir；见 VitaLoom README。
        """
        try:
            # 确定项目路径
            if project_path is None:
                project_path = os.path.join(self.projects_dir, project_name)
            
            # 检查项目是否已存在
            if os.path.exists(project_path):
                return None
            
            # 创建项目目录结构
            os.makedirs(os.path.join(project_path, "assets"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "scripts"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "scenes"), exist_ok=True)
            
            # 创建项目配置文件
            project_data = {
                "name": project_name,
                "description": description,
                "version": "1.0.0",
                "enabled_plugins": [],
                "disabled_plugins": [],
                "active_scene": "main_scene.pond",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "modified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "settings": {
                    "auto_save": True,
                    "auto_save_interval": 300,  # 5分钟
                    "backup_enabled": True,
                    "backup_count": 5
                }
            }
            
            project_json_path = os.path.join(project_path, "project.json")
            with open(project_json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # 如果指定了模板，加载模板
            if template and os.path.exists(os.path.join(self.templates_dir, template)):
                self._load_template(project_path, template)
            else:
                # 创建默认场景
                self._create_default_scene(project_path)
            
            # 添加到最近项目
            self._add_to_recent_projects(project_path)
            
            # 发送信号
            self.project_created.emit(project_path)
            self.signal_bus.emit_project_opened(project_path)
            
            return project_path
        
        except Exception as e:
            logger.exception("创建项目失败: %s", e)
            return None
    
    def _load_template(self, project_path: str, template_name: str):
        """加载项目模板"""
        template_path = os.path.join(self.templates_dir, template_name)
        if os.path.isdir(template_path):
            # 复制模板文件
            import shutil
            for item in os.listdir(template_path):
                src = os.path.join(template_path, item)
                dst = os.path.join(project_path, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
    
    def _create_default_scene(self, project_path: str):
        """创建默认场景"""
        scene_data = {
            "name": "主场景",
            "version": "1.0",
            "pond_config": {
                "name": "默认莲池",
                "size": [1200, 800],
                "initial_components": 50,
                "initial_organisms": 10
            },
            "entities": [],
            "components": [],
            "resources": []
        }
        
        scene_path = os.path.join(project_path, "scenes", "main_scene.pond")
        os.makedirs(os.path.dirname(scene_path), exist_ok=True)
        with open(scene_path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, indent=2, ensure_ascii=False)
    
    def _sync_viewport_into_scene_manager(self) -> None:
        """将 SceneViewport 画布数据合并进 SceneManager（切换项目前保存编辑）。"""
        try:
            kernel = getattr(self.editor_context, "kernel", None)
            if kernel is None or not hasattr(kernel, "layout_manager"):
                return
            from core.VitaLoom.viewports.scene_viewport import SceneViewport
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            lm = kernel.layout_manager
            for provider in getattr(lm, "viewport_providers", {}).values():
                vp = getattr(provider, "viewport", None)
                if isinstance(vp, SceneViewport):
                    get_scene_manager().save_scene(data=vp.get_scene_data())
                    return
        except Exception as e:
            logger.warning("同步场景视口数据失败: %s", e)

    def _write_active_scene_to_project_json(
        self, project_path: str, scene_path: str
    ) -> None:
        """把上次打开的场景相对路径写入指定项目的 project.json。"""
        project_json_path = os.path.join(project_path, "project.json")
        scenes_dir = os.path.join(project_path, "scenes")
        if not os.path.isfile(project_json_path) or not scene_path:
            return
        try:
            abs_scene = os.path.abspath(scene_path)
            abs_scenes = os.path.abspath(scenes_dir)
            if not abs_scene.startswith(abs_scenes):
                return
            rel = os.path.relpath(abs_scene, abs_scenes).replace("\\", "/")
            with open(project_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["active_scene"] = rel
            with open(project_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("写入项目 active_scene 失败: %s", e)

    def _flush_before_project_switch(
        self, prev_project_path: str, *, update_active_scene: bool = True
    ) -> None:
        """离开项目前：合并视口、按需存盘、可选写入 active_scene。"""
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        sm = get_scene_manager()
        scene_path = sm.get_current_scene_path()
        if not scene_path:
            return
        self._sync_viewport_into_scene_manager()
        if sm.is_scene_modified():
            sm.save_scene()
            scene_path = sm.get_current_scene_path() or scene_path
        if update_active_scene:
            self._write_active_scene_to_project_json(prev_project_path, scene_path)

    def open_project(self, project_path: str) -> bool:
        """职责: 加载 project.json、写入 EditorContext、应用插件策略与最近列表。
        时机: 启动向导或项目浏览器打开。
        不变量: 无 project.json 返回 False；成功触发 project_opened 信号。
        排错: 打开后无场景 → active_scene 字段与 SceneManager.load_scene 链。
        """
        try:
            project_path = os.path.abspath(project_path)
            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return False

            from core.VitaLoom.scene.scene_manager import get_scene_manager

            scene_manager = get_scene_manager()
            prev_path = self.editor_context.current_project_path
            prev_abs = (
                os.path.normcase(os.path.abspath(prev_path)) if prev_path else None
            )
            new_abs = os.path.normcase(project_path)
            if prev_path and prev_abs != new_abs:
                self._flush_before_project_switch(prev_path)
            elif prev_path and prev_abs == new_abs:
                # 同项目再次打开：保存 .pond 变更，但不覆盖 project.json 的 active_scene
                self._flush_before_project_switch(
                    project_path, update_active_scene=False
                )

            # 先清空旧场景，驱动视口/层级热更新
            scene_manager.clear_scene()
            self.editor_context.clear_selection()

            # 读取项目配置
            with open(project_json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 更新编辑器上下文
            self.editor_context.current_project_path = project_path
            self.editor_context.project_modified = False
            # 缓存项目配置（供插件/内核读取）
            setattr(self.editor_context, "current_project_config", project_data)
            
            # 添加到最近项目
            self._add_to_recent_projects(project_path)
            
            # 加载该项目上次记录的 active_scene
            active_scene = str(project_data.get("active_scene", "main_scene.pond")).replace("\\", "/")
            scene_path = os.path.join(project_path, "scenes", active_scene)
            
            if os.path.exists(scene_path):
                if scene_manager.load_scene(scene_path):
                    logger.info("场景加载成功: %s", active_scene)
                else:
                    logger.warning("场景加载失败: %s", active_scene)
                    scene_manager.clear_scene()
            else:
                logger.warning("场景文件不存在: %s", scene_path)
                scene_manager.clear_scene()
            
            # 发送信号
            self.project_opened.emit(project_path)
            self.signal_bus.emit_project_opened(project_path)
            
            # 通过事件总线发布项目打开事件（供插件订阅）
            self.editor_context.event_bus.publish("project_opened", project_path)

            # 应用项目级插件策略（Official/User 可被项目禁用；Core 不在这里卸载）
            self._apply_project_plugin_policy(project_data)

            self._set_last_opened_project(project_path)
            self.editor_context.event_bus.publish("refresh_project_browser", project_path)
            
            logger.info("项目打开成功: %s", project_path)
            logger.info("项目名称: %s", project_data.get("name", "Unknown"))
            logger.info("活动场景: %s", active_scene)
            
            return True
        
        except Exception as e:
            logger.exception("打开项目失败: %s", e)
            return False

    def _apply_project_plugin_policy(self, project_data: Dict[str, Any]):
        """根据项目配置应用插件启用/禁用策略（持久化在 project.json）。"""
        try:
            ctx = self.editor_context
            kernel = getattr(ctx, "kernel", None)
            if not kernel or not hasattr(kernel, "plugin_loader"):
                return

            loader = kernel.plugin_loader
            disabled = project_data.get("disabled_plugins", [])
            if not isinstance(disabled, list) or not disabled:
                return

            disabled_set = {str(x) for x in disabled if x is not None}
            for plugin_name in list(getattr(loader, "loaded_plugins", {}).keys()):
                if plugin_name not in disabled_set:
                    continue
                scope = loader.get_plugin_scope(plugin_name) if hasattr(loader, "get_plugin_scope") else "unknown"
                if scope == "core_mod":
                    continue
                if hasattr(loader, "is_plugin_protected") and loader.is_plugin_protected(plugin_name):
                    continue
                loader.unload_plugin(plugin_name)
        except Exception as e:
            logger.warning("应用项目插件策略失败（已忽略）: %s", e)

    def get_current_project_path(self) -> Optional[str]:
        """兼容旧代码：返回当前项目路径。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.editor_context.current_project_path
    
    def save_project(self, project_path: Optional[str] = None) -> bool:
        """保存项目。

        
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
            if project_path is None:
                project_path = self.editor_context.current_project_path
            
            if not project_path:
                return False
            
            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return False
            
            # 读取现有项目配置
            with open(project_json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 更新修改时间
            project_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存项目配置
            with open(project_json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # 更新编辑器上下文
            self.editor_context.project_modified = False
            
            # 发送信号
            self.project_saved.emit(project_path)
            self.signal_bus.emit_project_saved(project_path)
            
            return True
        
        except Exception as e:
            logger.exception("保存项目失败: %s", e)
            return False
    
    def close_project(self):
        """关闭当前项目。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.editor_context.current_project_path = None
        self.editor_context.project_modified = False
        self.project_closed.emit()
        self.signal_bus.emit_project_closed()
    
    def get_project_info(self, project_path: str) -> Optional[Dict[str, Any]]:
        """获取项目信息。

        
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
            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return None
            
            with open(project_json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 添加额外信息
            project_data['path'] = project_path
            project_data['exists'] = True
            
            return project_data
        
        except Exception as e:
            logger.warning("读取项目信息失败: %s (path=%s)", e, project_path)
            return None
    
    def update_project_settings(self, settings: Dict[str, Any]) -> bool:
        """更新项目设置。

        
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
            project_path = self.editor_context.current_project_path
            if not project_path:
                return False
            
            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return False
            
            # 读取项目配置
            with open(project_json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 更新设置
            if 'settings' not in project_data:
                project_data['settings'] = {}
            project_data['settings'].update(settings)
            project_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存
            with open(project_json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.exception("更新项目设置失败: %s", e)
            return False

    def get_current_project_config(self) -> Optional[Dict[str, Any]]:
        """读取当前项目的 project.json（优先返回缓存，失败则回退读取）。

        
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
            cached = getattr(self.editor_context, "current_project_config", None)
            if isinstance(cached, dict) and cached:
                return cached

            project_path = self.editor_context.current_project_path
            if not project_path:
                return None

            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return None

            with open(project_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            setattr(self.editor_context, "current_project_config", data)
            return data
        except Exception as e:
            logger.warning("读取当前项目配置失败: %s", e)
            return None

    def update_project_config_fields(self, fields: Dict[str, Any]) -> bool:
        """更新 project.json 的顶层字段（不是 settings 子树）。

        
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
            project_path = self.editor_context.current_project_path
            if not project_path:
                return False

            project_json_path = os.path.join(project_path, "project.json")
            if not os.path.exists(project_json_path):
                return False

            with open(project_json_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            project_data.update(fields or {})
            project_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(project_json_path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            setattr(self.editor_context, "current_project_config", project_data)
            self.editor_context.project_modified = False
            return True
        except Exception as e:
            logger.warning("更新 project.json 字段失败: %s", e)
            return False
    
    def get_available_templates(self) -> List[str]:
        """获取可用的项目模板列表。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        templates = []
        if os.path.exists(self.templates_dir):
            for item in os.listdir(self.templates_dir):
                template_path = os.path.join(self.templates_dir, item)
                if os.path.isdir(template_path):
                    templates.append(item)
        return templates


def get_project_manager() -> ProjectManager:
    """获取项目管理器单例"""
    return ProjectManager()
