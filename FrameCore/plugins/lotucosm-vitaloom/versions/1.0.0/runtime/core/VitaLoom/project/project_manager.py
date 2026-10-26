# -*- coding: utf-8 -*-
"""项目管理器：`projects/` 下 project.json 生命周期与最近列表。

排错: 见 core/VitaLoom/README.md「项目打不开」
"""

import os
import json
import shutil
from typing import Optional, List, Dict, Any, Mapping
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.core.signal_bus import get_signal_bus
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host


logger = get_logger("ProjectManager")


class ProjectManager(QObject):
    """职责: 单例管理项目路径、配置与 EditorContext.current_project_path。
    时机: 启动向导或「打开项目」；关闭时 `close_project`。
    不变量: `open_project` 成功须加载 project.json 并应用插件策略字段。
    排错: 最近列表空 → workspace/state/system/editor_config.json；路径不存在会被过滤。
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
        
        from core.VitaLoom.core.bundle_paths import (
            application_root,
            projects_root,
            resource_root,
            samples_projects_root,
            system_config_dir,
            user_projects_root,
        )

        app_root = application_root()
        res_root = resource_root()
        self.projects_dir = str(user_projects_root())
        self.samples_projects_dir = str(samples_projects_root())
        self._projects_root = str(projects_root())
        self.templates_dir = str(res_root / "workspace" / "templates" / "ponds")
        os.makedirs(self.templates_dir, exist_ok=True)
        self._system_config_dir = str(system_config_dir())

        self.max_recent_projects = 10
        self._recent_projects: List[str] = []
        self._load_recent_projects()
        self.last_project_open_report: Dict[str, Any] = {
            "status": "not_started",
            "code": "",
            "project_path": "",
            "warnings": [],
            "actions": [],
        }
        self.last_project_flush_report: Dict[str, Any] = {
            "status": "not_started",
            "code": "",
            "project_path": "",
            "actions": [],
        }
        self.last_project_save_report: Dict[str, Any] = {
            "status": "not_started",
            "code": "",
            "project_path": "",
            "actions": [],
        }
        self.last_project_close_report: Dict[str, Any] = {
            "status": "not_started",
            "code": "",
            "project_path": "",
            "actions": [],
        }
    def _read_editor_config(self) -> Dict[str, Any]:
        """读取 workspace/state/system/editor_config.json。"""
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
        if self._is_ephemeral_project_path(project_path):
            return
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

    def flush_current_project(
        self, *, update_active_scene: bool = True
    ) -> Dict[str, Any]:
        """Flush the applied Project World through the concrete PyQt Host Adapter."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )

        project_path = self.current_project_world_path()
        if not project_path:
            report = finalize_project_world_report(
                {
                    "transition": "flush",
                    "status": "noop",
                    "code": "no_current_project_world",
                    "message": "No Project World is currently applied",
                    "project_path": "",
                    "actions": [],
                }
            )
            self.last_project_flush_report = report
            return report
        return self._flush_before_project_switch(
            project_path,
            update_active_scene=update_active_scene,
        )

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
        os.makedirs(self._system_config_dir, exist_ok=True)
        return os.path.join(self._system_config_dir, "editor_config.json")
    
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

    def register_known_project(self, project_path: str) -> bool:
        """Hub「导入项目」：校验 project.json 并加入最近列表。"""
        path = os.path.abspath(project_path)
        if not os.path.isfile(os.path.join(path, "project.json")):
            return False
        if self._is_ephemeral_project_path(path):
            return False
        self._add_to_recent_projects(path)
        return True

    def clone_demo_project(self, demo_folder_name: str, dest_parent: str) -> Optional[str]:
        """Hub：复制 workspace/projects/samples/ 下示范工程到用户指定目录。"""
        try:
            src = os.path.join(self.samples_projects_dir, demo_folder_name)
            if not os.path.isdir(src) or not os.path.isfile(os.path.join(src, "project.json")):
                return None
            dest_parent = os.path.abspath(dest_parent)
            dest = os.path.join(dest_parent, demo_folder_name)
            if os.path.exists(dest):
                return None
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "dist"),
            )
            self._add_to_recent_projects(dest)
            return dest
        except Exception as e:
            logger.exception("复制示范工程失败: %s", e)
            return None
    
    def create_project(self, project_name: str, project_path: Optional[str] = None,
                      template: Optional[str] = None, description: str = "",
                      project_type: str = "sr2d") -> Optional[str]:
        """Create a Project World through the Qt-free authority.

        This PyQt Adapter only selects Host paths, updates recent-project state,
        and emits Host lifecycle signals after successful scaffold creation.
        """
        if project_path is None:
            project_path = os.path.join(self.projects_dir, project_name)

        try:
            from core.VitaLoom.core.bundle_paths import resource_root
            from core.VitaLoom.project.project_world_creation import (
                ProjectWorldCreationError,
                create_project_world,
            )

            created = create_project_world(
                project_name,
                project_path,
                template=template,
                templates_dir=self.templates_dir,
                description=description,
                project_type=project_type or template or "sr2d",
                repo_root=resource_root(),
            )
            created_path = str(created["project_path"])
            lock_error = str(created.get("lock_error", "") or "")
            if lock_error:
                raise ProjectWorldCreationError(
                    "project_lock_creation_failed",
                    lock_error,
                )

            self._add_to_recent_projects(created_path)
            self.project_created.emit(created_path)
            self.signal_bus.emit_project_opened(created_path)
            return created_path
        except ProjectWorldCreationError as exc:
            if exc.code != "project_target_exists":
                logger.error("创建项目失败 [%s]: %s", exc.code, exc)
            return None
        except Exception as exc:
            logger.exception("创建项目失败: %s", exc)
            return None

    def _persist_viewport_scene(self, scene_manager: Any) -> Dict[str, Any]:
        """Persist visible SceneViewport data when the legacy Host exposes one."""

        try:
            kernel = getattr(self.editor_context, "kernel", None)
            if kernel is None or not hasattr(kernel, "layout_manager"):
                return {"available": False, "saved": False}
            from core.VitaLoom.viewports.scene_viewport import SceneViewport

            layout_manager = kernel.layout_manager
            for provider in getattr(layout_manager, "viewport_providers", {}).values():
                viewport = getattr(provider, "viewport", None)
                if isinstance(viewport, SceneViewport):
                    saved = bool(scene_manager.save_scene(data=viewport.get_scene_data()))
                    return {"available": True, "saved": saved}
            return {"available": False, "saved": False}
        except Exception as exc:
            logger.exception("同步并保存场景视口数据失败: %s", exc)
            return {
                "available": True,
                "saved": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }

    def _flush_before_project_switch(
        self, prev_project_path: str, *, update_active_scene: bool = True
    ) -> Dict[str, Any]:
        """Prepare and apply previous-World persistence before destructive switching."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )
        from core.VitaLoom.project.project_world_session import (
            AUTOMATIC_SCENE_FLUSH_HISTORY_BOUNDARY,
            prepare_project_world_flush,
        )
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_manager = get_scene_manager()
        previous_path = os.path.abspath(os.fspath(prev_project_path))
        if not os.path.exists(previous_path) and not scene_manager.is_scene_modified():
            report = finalize_project_world_report(
                {
                    "transition": "flush",
                    "status": "noop",
                    "code": "stale_project_world_unavailable",
                    "message": (
                        "Previous Project World is no longer available and the Host "
                        "has no modified scene state to persist"
                    ),
                    "project_path": previous_path,
                    "scene_path": str(scene_manager.get_current_scene_path() or ""),
                    "scene_persistence_boundary": dict(AUTOMATIC_SCENE_FLUSH_HISTORY_BOUNDARY),
                    "warnings": [
                        {
                            "code": "previous_project_world_unavailable",
                            "message": (
                                "The previously applied Project World was removed outside "
                                "the Host; switching continues because no modified scene "
                                "state would be discarded"
                            ),
                        }
                    ],
                    "actions": [
                        {
                            "action": "persist_host_scene",
                            "status": "skipped_stale_world",
                        }
                    ],
                }
            )
            self.last_project_flush_report = report
            return report

        preparation = prepare_project_world_flush(
            previous_path,
            scene_path=scene_manager.get_current_scene_path(),
            update_active_scene=update_active_scene,
        )
        self.last_project_flush_report = dict(preparation)
        if preparation.get("status") != "ready":
            return dict(preparation)
        return self.apply_project_world_flush(preparation)

    def apply_project_world_flush(
        self, preparation: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Apply prepared persistence facts through SceneManager and the PyQt Host."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )
        from core.VitaLoom.project.project_world_session import (
            commit_project_world_manifest,
        )
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        report: Dict[str, Any] = dict(preparation)
        boundary = preparation.get("scene_persistence_boundary")
        if isinstance(boundary, Mapping):
            report["scene_persistence_boundary"] = dict(boundary)
        report["preparation_report_id"] = str(preparation.get("report_id", "") or "")
        report["actions"] = []
        report["code"] = ""
        scene_persisted = False

        def record(action: str, status: str, **details: Any) -> None:
            row: Dict[str, Any] = {"action": action, "status": status}
            row.update(details)
            report["actions"].append(row)

        def finish(status: str, code: str = "", message: str = "") -> Dict[str, Any]:
            report["status"] = status
            report["code"] = code
            report["message"] = message
            final = finalize_project_world_report(report)
            self.last_project_flush_report = final
            return final

        if preparation.get("status") != "ready":
            return finish(
                "blocked",
                str(preparation.get("code", "project_world_flush_not_ready") or "project_world_flush_not_ready"),
                str(preparation.get("message", "Project World flush is not ready") or ""),
            )

        prepared_project_path = str(preparation.get("project_path", "") or "")
        current_project_path = self.current_project_world_path()
        if (
            not prepared_project_path
            or not current_project_path
            or os.path.normcase(os.path.realpath(os.path.abspath(current_project_path)))
            != os.path.normcase(os.path.realpath(os.path.abspath(prepared_project_path)))
        ):
            record(
                "verify_project_context",
                "failed",
                current_project_path=current_project_path,
                prepared_project_path=prepared_project_path,
            )
            return finish(
                "blocked",
                "project_world_flush_context_changed",
                "The applied Project World changed after flush preparation",
            )

        scene_manager = get_scene_manager()
        scene_path = str(preparation.get("scene_path", "") or "")
        current_scene_path = str(scene_manager.get_current_scene_path() or "")
        if scene_path and (
            not current_scene_path
            or os.path.normcase(os.path.realpath(os.path.abspath(current_scene_path)))
            != os.path.normcase(os.path.realpath(os.path.abspath(scene_path)))
        ):
            record(
                "verify_scene_context",
                "failed",
                current_scene_path=current_scene_path,
                prepared_scene_path=scene_path,
            )
            return finish(
                "blocked",
                "project_world_flush_scene_changed",
                "The active Host scene changed after flush preparation",
            )

        if not scene_path:
            record("persist_host_scene", "skipped_no_scene")
        else:
            viewport_result = self._persist_viewport_scene(scene_manager)
            if bool(viewport_result.get("available", False)):
                if not bool(viewport_result.get("saved", False)):
                    record("persist_host_scene", "failed", source="scene_viewport", **{
                        key: value
                        for key, value in viewport_result.items()
                        if key not in {"available", "saved"}
                    })
                    return finish(
                        "failed",
                        "scene_save_failed",
                        "SceneViewport data could not be persisted",
                    )
                scene_persisted = True
                record("persist_host_scene", "completed", source="scene_viewport")
            elif scene_manager.is_scene_modified():
                if not bool(scene_manager.save_scene()):
                    record("persist_host_scene", "failed", source="scene_manager")
                    return finish(
                        "failed",
                        "scene_save_failed",
                        "SceneManager.save_scene returned False",
                    )
                scene_persisted = True
                record("persist_host_scene", "completed", source="scene_manager")
            else:
                record("persist_host_scene", "skipped_unmodified", source="scene_manager")

        if bool(preparation.get("manifest_update_required", False)):
            manifest_report = commit_project_world_manifest(preparation)
            report["manifest_persistence"] = manifest_report
            if manifest_report.get("status") != "persisted":
                record(
                    "atomic_replace_project_manifest",
                    "failed",
                    persistence_status=manifest_report.get("status", ""),
                    persistence_code=manifest_report.get("code", ""),
                )
                return finish(
                    "partial" if scene_persisted else "failed",
                    str(manifest_report.get("code", "project_manifest_persistence_failed") or "project_manifest_persistence_failed"),
                    str(manifest_report.get("message", "Project World manifest persistence failed") or ""),
                )
            record("atomic_replace_project_manifest", "completed")
            next_project_data = preparation.get("next_project_data")
            if (
                os.path.normcase(self.current_project_world_path())
                == os.path.normcase(str(preparation.get("project_path", "") or ""))
                and isinstance(next_project_data, Mapping)
            ):
                setattr(self.editor_context, "current_project_config", dict(next_project_data))

        status = "flushed" if scene_path or bool(preparation.get("manifest_update_required", False)) else "noop"
        code = "" if status == "flushed" else "no_current_scene"
        message = "Project World flushed" if status == "flushed" else "Project World has no current scene to flush"
        return finish(status, code, message)

    def current_project_world_path(self) -> str:
        """Return the Project World currently applied by this Host Adapter."""

        return str(getattr(self.editor_context, "current_project_path", "") or "")

    def open_project(self, project_path: str) -> bool:
        """Prepare a Project World, then apply it through this PyQt Host Adapter."""

        try:
            from core.VitaLoom.core.bundle_paths import resource_root
            from core.VitaLoom.project.project_world_open import (
                prepare_project_world_open,
            )

            repo_root = getattr(self.editor_context, "project_root", None) or resource_root()
            preparation = prepare_project_world_open(
                project_path,
                previous_project_path=self.current_project_world_path() or None,
                repo_root=repo_root,
            )
            self.last_project_open_report = dict(preparation)
            if preparation.get("status") != "ready":
                logger.error(
                    "Project World open blocked [%s]: %s",
                    preparation.get("code", "project_open_blocked"),
                    preparation.get("message", ""),
                )
                return False

            report = self.apply_project_world_open(preparation)
            return report.get("status") in {"opened", "opened_with_warnings"}
        except Exception as exc:
            report = {
                "status": "failed",
                "code": "project_open_preparation_failed",
                "message": f"{type(exc).__name__}: {exc}",
                "project_path": os.path.abspath(project_path),
                "warnings": [],
                "actions": [],
            }
            self.last_project_open_report = report
            logger.exception("打开项目失败: %s", exc)
            return False

    def apply_project_world_open(
        self, preparation: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Apply prepared Project World facts through the concrete PyQt Host."""

        from core.VitaLoom.project.project_world_open import (
            finalize_project_world_open_report,
        )

        report: Dict[str, Any] = dict(preparation)
        boundary = preparation.get("scene_persistence_boundary")
        if isinstance(boundary, Mapping):
            report["scene_persistence_boundary"] = dict(boundary)
        report["preparation_report_id"] = str(preparation.get("report_id", "") or "")
        report["warnings"] = [
            dict(item) for item in preparation.get("warnings", []) if isinstance(item, Mapping)
        ]
        report["actions"] = []
        report["code"] = ""
        context_applied = False

        def record(action: str, status: str, **details: Any) -> None:
            row: Dict[str, Any] = {"action": action, "status": status}
            row.update(details)
            report["actions"].append(row)

        def finish(status: str, code: str = "", message: str = "") -> Dict[str, Any]:
            report["status"] = status
            report["code"] = code
            report["message"] = message
            final = finalize_project_world_open_report(report)
            self.last_project_open_report = final
            return final

        if preparation.get("status") != "ready":
            return finish(
                "blocked",
                str(preparation.get("code", "project_open_not_ready") or "project_open_not_ready"),
                str(preparation.get("message", "Project World preparation is not ready") or ""),
            )

        project_path = str(preparation.get("project_path", "") or "")
        project_data = preparation.get("project_data", {})
        if not project_path or not isinstance(project_data, Mapping):
            return finish(
                "failed",
                "project_open_preparation_invalid",
                "prepared project_path and project_data are required",
            )

        try:
            flush = preparation.get("flush", {})
            if isinstance(flush, Mapping) and bool(flush.get("required", False)):
                previous = str(flush.get("project_path", "") or "")
                flush_report = self._flush_before_project_switch(
                    previous,
                    update_active_scene=bool(flush.get("update_active_scene", False)),
                )
                report["previous_world_flush"] = flush_report
                report["warnings"].extend(
                    dict(item)
                    for item in flush_report.get("warnings", [])
                    if isinstance(item, Mapping)
                )
                if flush_report.get("status") not in {"flushed", "noop"}:
                    record(
                        "flush_previous_world",
                        "failed",
                        project_path=previous,
                        flush_status=flush_report.get("status", ""),
                        flush_code=flush_report.get("code", ""),
                    )
                    return finish(
                        "failed",
                        "project_previous_world_flush_failed",
                        str(flush_report.get("message", "Previous Project World flush failed") or ""),
                    )
                record(
                    "flush_previous_world",
                    "completed",
                    project_path=previous,
                    update_active_scene=bool(flush.get("update_active_scene", False)),
                    flush_status=flush_report.get("status", ""),
                )

            from core.VitaLoom.scene.scene_manager import get_scene_manager

            scene_manager = get_scene_manager()
            scene_manager.clear_scene()
            self.editor_context.clear_selection()
            record("clear_host_scene", "completed")

            self.editor_context.current_project_path = project_path
            self.editor_context.project_modified = False
            setattr(self.editor_context, "current_project_config", dict(project_data))
            context_applied = True
            self._add_to_recent_projects(project_path)
            record("apply_project_context", "completed")

            active_scene = str(preparation.get("active_scene", "main_scene.pond") or "main_scene.pond")
            scene_path = str(preparation.get("scene_path", "") or "")
            scene_loaded = False
            if bool(preparation.get("scene_exists", False)):
                scene_loaded = bool(scene_manager.load_scene(scene_path))
                if scene_loaded:
                    record("load_active_scene", "completed", scene_path=scene_path)
                    logger.info("场景加载成功: %s", active_scene)
                else:
                    scene_manager.clear_scene()
                    report["warnings"].append(
                        {
                            "code": "active_scene_load_failed",
                            "message": f"SceneManager.load_scene returned False: {scene_path}",
                        }
                    )
                    record("load_active_scene", "failed", scene_path=scene_path)
                    logger.warning("场景加载失败: %s", active_scene)
            else:
                record("load_active_scene", "skipped_missing", scene_path=scene_path)
                logger.warning("场景文件不存在: %s", scene_path)
            report["scene_loaded"] = scene_loaded

            self.project_opened.emit(project_path)
            self.signal_bus.emit_project_opened(project_path)
            self.editor_context.event_bus.publish("project_opened", project_path)
            record("publish_project_opened", "completed")

            self._publish_project_manifest_validation(preparation)

            plugin_lifecycle_report = self._sync_project_plugins(
                dict(project_data), project_path
            )
            report["plugin_lifecycle"] = plugin_lifecycle_report
            plugin_event_payload = {
                "project_path": project_path,
                "lifecycle": plugin_lifecycle_report,
            }
            if plugin_lifecycle_report.get("status") in {
                "settled",
                "skipped_eager_mode",
            }:
                self.editor_context.event_bus.publish(
                    "project_plugins_synced",
                    plugin_event_payload,
                )
                record(
                    "sync_project_plugins",
                    "completed",
                    lifecycle_status=plugin_lifecycle_report.get("status", ""),
                )
            else:
                self.editor_context.event_bus.publish(
                    "project_plugin_lifecycle_failed",
                    plugin_event_payload,
                )
                report["warnings"].append(
                    {
                        "code": "project_plugin_lifecycle_unsettled",
                        "message": str(plugin_lifecycle_report.get("status", "failed")),
                    }
                )
                record(
                    "sync_project_plugins",
                    "failed",
                    lifecycle_status=plugin_lifecycle_report.get("status", ""),
                )

            self._set_last_opened_project(project_path)
            record("persist_recent_world", "completed")
            asset_registry_report = self._refresh_project_asset_registry(project_path)
            report["asset_registry"] = asset_registry_report
            asset_status = str(asset_registry_report.get("status", "") or "")
            if asset_status == "refresh_failed":
                report["warnings"].append(
                    {
                        "code": "asset_registry_refresh_failed",
                        "message": str(asset_registry_report.get("error", "")),
                    }
                )
                record("refresh_asset_registry", "failed", registry_status=asset_status)
            else:
                record("refresh_asset_registry", "completed", registry_status=asset_status)

            self.editor_context.event_bus.publish("refresh_project_browser", project_path)
            record("refresh_project_browser", "completed")

            logger.info("项目打开成功: %s", project_path)
            logger.info("项目名称: %s", project_data.get("name", "Unknown"))
            logger.info("活动场景: %s", active_scene)
            status = "opened_with_warnings" if report["warnings"] else "opened"
            return finish(status, "", "Project World opened")
        except Exception as exc:
            record(
                "host_application_exception",
                "failed",
                error=type(exc).__name__,
                message=str(exc),
            )
            status = "partial" if context_applied or report["actions"] else "failed"
            logger.exception("打开项目失败: %s", exc)
            return finish(
                status,
                "project_host_application_failed",
                f"{type(exc).__name__}: {exc}",
            )

    def _publish_project_manifest_validation(
        self, preparation: Mapping[str, Any]
    ) -> None:
        """Apply JSON-safe manifest evidence to existing PyQt/UI consumers."""

        from core.VitaLoom.project.project_world_open import (
            manifest_validation_result_from_report,
        )

        raw = preparation.get("manifest_validation", {})
        validation_report = raw if isinstance(raw, Mapping) else {}
        result = manifest_validation_result_from_report(validation_report)
        setattr(self.editor_context, "project_manifest_validation", result)
        if hasattr(self.editor_context, "event_bus"):
            self.editor_context.event_bus.publish("project_manifest_issues", result)
        for issue in result.issues:
            logger.warning("工程 manifest [%s]: %s", issue.code, issue.message)
        summary = result.summary_text()
        kernel = getattr(self.editor_context, "kernel", None)
        if kernel and hasattr(kernel, "layout_manager"):
            statusbar = getattr(kernel.layout_manager, "statusbar", None)
            if statusbar is not None and summary:
                statusbar.showMessage(f"工程包/版本检查: {summary}", 12000)

    def refresh_current_project_manifest_validation(self) -> Dict[str, Any]:
        """Revalidate the applied Project World and publish Host/UI evidence."""

        project_path = self.get_current_project_path()
        if not project_path:
            return {
                "status": "unavailable",
                "code": "no_current_project_world",
                "project_path": "",
                "ok": False,
                "missing_packages": [],
                "issues": [],
            }
        try:
            from core.VitaLoom.core.bundle_paths import resource_root
            from core.VitaLoom.project.project_world_open import (
                manifest_validation_result_from_report,
                prepare_project_world_open,
            )

            preparation = prepare_project_world_open(
                project_path,
                previous_project_path=project_path,
                repo_root=resource_root(),
            )
            validation_report = preparation.get("manifest_validation", {})
            if not isinstance(validation_report, Mapping) or not validation_report:
                return {
                    "status": "failed",
                    "code": str(preparation.get("code", "manifest_validation_unavailable")),
                    "project_path": str(project_path),
                    "ok": False,
                    "missing_packages": [],
                    "issues": [],
                }
            self._publish_project_manifest_validation(
                {"manifest_validation": dict(validation_report)}
            )
            result = manifest_validation_result_from_report(validation_report)
            return {
                "status": "validated" if result.ok else "issues",
                "code": "",
                "project_path": str(project_path),
                "ok": bool(result.ok),
                "missing_packages": [str(item) for item in result.missing_packages],
                "issues": [
                    {
                        "level": str(issue.level),
                        "code": str(issue.code),
                        "message": str(issue.message),
                    }
                    for issue in result.issues
                ],
            }
        except Exception as exc:
            logger.warning("刷新工程 manifest 验证失败: %s", exc)
            return {
                "status": "failed",
                "code": "project_world_manifest_validation_failed",
                "project_path": str(project_path),
                "ok": False,
                "missing_packages": [],
                "issues": [
                    {
                        "level": "error",
                        "code": "project_world_manifest_validation_failed",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                ],
            }

    def _refresh_project_asset_registry(self, project_path: str) -> Dict[str, Any]:
        """Refresh project-local asset identity and return truthful evidence."""

        try:
            from core.VitaLoom.project.asset_reference_transaction import recover_asset_reference_mutations
            from core.VitaLoom.project.asset_registry import refresh_project_asset_registry

            recovery = recover_asset_reference_mutations(project_path)
            snapshot = refresh_project_asset_registry(project_path)
            snapshot["asset_transaction_recovery"] = recovery
            setattr(self.editor_context, "project_asset_registry_snapshot", snapshot)
            self.editor_context.event_bus.publish(
                "asset_registry_refreshed",
                {
                    "project_path": project_path,
                    "registry_revision": snapshot["registry_revision"],
                    "generation": snapshot["generation"],
                    "source": "project_open",
                },
            )
            if recovery["recovery_required"]:
                self.editor_context.event_bus.publish(
                    "asset_transaction_recovery_required", recovery
                )
            return {
                "status": "refreshed",
                "project_path": project_path,
                "registry_revision": str(snapshot.get("registry_revision", "") or ""),
                "generation": int(snapshot.get("generation", 0) or 0),
                "recovery_required": bool(recovery.get("recovery_required", False)),
            }
        except Exception as exc:
            diagnostic = {
                "project_path": project_path,
                "status": "refresh_failed",
                "error": type(exc).__name__,
                "message": str(exc),
                "source": "project_open",
            }
            setattr(self.editor_context, "project_asset_registry_snapshot", diagnostic)
            self.editor_context.event_bus.publish(
                "asset_registry_refresh_failed", diagnostic
            )
            logger.warning("Asset Registry refresh after project open failed: %s", exc)
            return diagnostic

    def _sync_project_plugins(
        self, project_data: Dict[str, Any], project_path: str
    ) -> Dict[str, Any]:
        """Discover L4 addons, then execute the L1 Host lifecycle authority plan."""
        ctx = self.editor_context
        host = resolve_plugin_host(ctx)
        repo_root = getattr(ctx, "repo_root", None) or getattr(
            ctx, "project_root", None
        )
        if not repo_root:
            from core.VitaLoom.core.bundle_paths import resource_root

            repo_root = str(resource_root())
        try:
            discovery = host.scan_project_addons(project_path)
            if discovery.get("status") != "ready":
                return {
                    "status": "blocked",
                    "source": "project_open",
                    "discovery": discovery,
                    "diagnostics": list(discovery.get("diagnostics", [])),
                    "completed": {"deactivated": [], "activated": []},
                }
            lifecycle = host.sync_plugins_for_project(
                project_data,
                repo_root=repo_root,
            )
            lifecycle = dict(lifecycle)
            lifecycle["discovery"] = discovery
            lifecycle["source"] = "project_open"
            return lifecycle
        except Exception as exc:
            logger.exception("同步工程插件生命周期失败: %s", exc)
            return {
                "status": "failed",
                "source": "project_open",
                "diagnostics": [
                    {
                        "level": "error",
                        "code": "plugin_lifecycle_adapter_exception",
                        "message": str(exc),
                        "plugin_id": "",
                        "source": project_path,
                    }
                ],
                "completed": {"deactivated": [], "activated": []},
            }
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
    
    def save_project(
        self,
        project_path: Optional[str] = None,
        *,
        modified_at: Optional[str] = None,
    ) -> bool:
        """Atomically save project.json through the Qt-free persistence authority."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )
        from core.VitaLoom.project.project_world_session import (
            commit_project_world_manifest,
            prepare_project_world_save,
        )
        from core.VitaLoom.project.project_write_authority import (
            ProjectWriteInterlockError,
            project_write_interlock,
        )

        selected_path = project_path or self.current_project_world_path()
        if not selected_path:
            report = finalize_project_world_report(
                {
                    "transition": "save",
                    "status": "noop",
                    "code": "no_current_project_world",
                    "message": "No Project World is currently applied",
                    "project_path": "",
                    "actions": [],
                }
            )
            self.last_project_save_report = report
            return False

        preparation = prepare_project_world_save(
            selected_path,
            modified_at=modified_at,
        )
        if preparation.get("status") != "ready":
            self.last_project_save_report = dict(preparation)
            logger.error(
                "保存项目被阻断 [%s]: %s",
                preparation.get("code", "project_save_blocked"),
                preparation.get("message", ""),
            )
            return False

        try:
            with project_write_interlock(
                selected_path,
                authority_action="project_manifest_save",
            ):
                persistence = commit_project_world_manifest(preparation)
        except ProjectWriteInterlockError as exc:
            persistence = {
                "status": "blocked",
                "code": exc.code,
                "message": str(exc),
                "actions": [],
            }
        if persistence.get("status") != "persisted":
            report = finalize_project_world_report(
                {
                    **dict(preparation),
                    "status": "failed",
                    "code": str(persistence.get("code", "project_manifest_persistence_failed") or "project_manifest_persistence_failed"),
                    "message": str(persistence.get("message", "Project World manifest persistence failed") or ""),
                    "preparation_report_id": preparation.get("report_id", ""),
                    "manifest_persistence": persistence,
                    "actions": list(persistence.get("actions", [])),
                }
            )
            self.last_project_save_report = report
            logger.error("保存项目失败 [%s]: %s", report["code"], report["message"])
            return False

        next_project_data = preparation.get("next_project_data", {})
        if isinstance(next_project_data, Mapping):
            setattr(self.editor_context, "current_project_config", dict(next_project_data))
        self.editor_context.project_modified = False
        self.project_saved.emit(str(selected_path))
        self.signal_bus.emit_project_saved(str(selected_path))
        report = finalize_project_world_report(
            {
                **dict(preparation),
                "status": "saved",
                "code": "",
                "message": "Project World saved",
                "preparation_report_id": preparation.get("report_id", ""),
                "manifest_persistence": persistence,
                "actions": list(persistence.get("actions", []))
                + [{"action": "publish_project_saved", "status": "completed"}],
            }
        )
        self.last_project_save_report = report
        return True

    def close_project(self) -> Dict[str, Any]:
        """Prepare and apply Project World close through the legacy PyQt Host."""

        from core.VitaLoom.project.project_world_session import (
            prepare_project_world_close,
        )

        preparation = prepare_project_world_close(self.current_project_world_path() or None)
        self.last_project_close_report = dict(preparation)
        if preparation.get("status") == "noop":
            return dict(preparation)
        if preparation.get("status") != "ready":
            return dict(preparation)
        return self.apply_project_world_close(preparation)

    def apply_project_world_close(
        self, preparation: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Apply flush, L4 teardown, Host clear, and close publication in order."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        report: Dict[str, Any] = dict(preparation)
        boundary = preparation.get("scene_persistence_boundary")
        if isinstance(boundary, Mapping):
            report["scene_persistence_boundary"] = dict(boundary)
        report["preparation_report_id"] = str(preparation.get("report_id", "") or "")
        report["actions"] = []
        report["warnings"] = []
        report["code"] = ""

        def record(action: str, status: str, **details: Any) -> None:
            row: Dict[str, Any] = {"action": action, "status": status}
            row.update(details)
            report["actions"].append(row)

        def finish(status: str, code: str = "", message: str = "") -> Dict[str, Any]:
            report["status"] = status
            report["code"] = code
            report["message"] = message
            final = finalize_project_world_report(report)
            self.last_project_close_report = final
            return final

        if preparation.get("status") != "ready":
            return finish(
                "blocked",
                str(preparation.get("code", "project_world_close_not_ready") or "project_world_close_not_ready"),
                str(preparation.get("message", "Project World close is not ready") or ""),
            )

        project_path = str(preparation.get("project_path", "") or "")
        if not project_path:
            return finish(
                "noop",
                "no_current_project_world",
                "No Project World is currently applied",
            )

        current_project_path = self.current_project_world_path()
        if (
            not current_project_path
            or os.path.normcase(os.path.realpath(os.path.abspath(current_project_path)))
            != os.path.normcase(os.path.realpath(os.path.abspath(project_path)))
        ):
            record(
                "verify_project_context",
                "failed",
                current_project_path=current_project_path,
                prepared_project_path=project_path,
            )
            return finish(
                "blocked",
                "project_world_close_context_changed",
                "The applied Project World changed after close preparation",
            )

        flush_report = self.flush_current_project()
        report["flush"] = flush_report
        if flush_report.get("status") not in {"flushed", "noop"}:
            record(
                "flush_current_world",
                "failed",
                flush_status=flush_report.get("status", ""),
                flush_code=flush_report.get("code", ""),
            )
            return finish(
                "blocked",
                "project_close_flush_failed",
                str(flush_report.get("message", "Project World flush failed") or ""),
            )
        record(
            "flush_current_world",
            "completed",
            flush_status=flush_report.get("status", ""),
        )

        lifecycle_report: Dict[str, Any]
        host = resolve_plugin_host(self.editor_context)
        try:
            discovery = host.scan_project_addons(None)
            lifecycle_report = dict(host.sync_plugins_for_project({}))
            lifecycle_report["discovery"] = discovery
            lifecycle_report["source"] = "project_close"
        except Exception as exc:
            lifecycle_report = {
                "status": "failed",
                "source": "project_close",
                "completed": {"deactivated": [], "activated": []},
                "diagnostics": [
                    {
                        "level": "error",
                        "code": "project_close_plugin_cleanup_failed",
                        "message": str(exc),
                        "plugin_id": "",
                        "source": project_path,
                    }
                ],
            }
            report["plugin_lifecycle"] = lifecycle_report
            record(
                "teardown_project_addons",
                "failed",
                lifecycle_status="failed",
                error=type(exc).__name__,
            )
            if hasattr(self.editor_context, "event_bus"):
                self.editor_context.event_bus.publish(
                    "project_plugin_lifecycle_failed",
                    {"project_path": project_path, "lifecycle": lifecycle_report},
                )
            logger.exception("关闭工程时清理插件生命周期失败: %s", exc)
            return finish(
                "partial",
                "project_addon_teardown_exception",
                f"{type(exc).__name__}: {exc}",
            )

        lifecycle_status = str(lifecycle_report.get("status", "") or "")
        if lifecycle_status not in {"settled", "skipped_eager_mode"}:
            report["plugin_lifecycle"] = lifecycle_report
            record(
                "teardown_project_addons",
                "failed",
                lifecycle_status=lifecycle_status,
            )
            if hasattr(self.editor_context, "event_bus"):
                self.editor_context.event_bus.publish(
                    "project_plugin_lifecycle_failed",
                    {"project_path": project_path, "lifecycle": lifecycle_report},
                )
            return finish(
                "partial",
                "project_addon_teardown_unsettled",
                f"Project addon teardown status: {lifecycle_status or 'unknown'}",
            )
        record(
            "teardown_project_addons",
            "completed",
            lifecycle_status=lifecycle_status,
        )

        report["plugin_lifecycle"] = lifecycle_report
        if hasattr(self.editor_context, "event_bus"):
            self.editor_context.event_bus.publish(
                "project_plugins_synced",
                {"project_path": "", "lifecycle": lifecycle_report},
            )

        try:
            scene_manager = get_scene_manager()
            scene_manager.clear_scene()
            self.editor_context.clear_selection()
            record("clear_host_scene", "completed")

            self.editor_context.current_project_path = None
            self.editor_context.project_modified = False
            setattr(self.editor_context, "current_project_config", None)
            setattr(self.editor_context, "project_manifest_validation", None)
            setattr(self.editor_context, "project_asset_registry_snapshot", None)
            record("clear_project_context", "completed")

            self.project_closed.emit()
            self.signal_bus.emit_project_closed()
            if hasattr(self.editor_context, "event_bus"):
                self.editor_context.event_bus.publish("project_closed", project_path)
            record("publish_project_closed", "completed")
        except Exception as exc:
            record(
                "host_close_exception",
                "failed",
                error=type(exc).__name__,
                message=str(exc),
            )
            logger.exception("Project World Host close failed: %s", exc)
            return finish(
                "partial",
                "project_host_close_failed",
                f"{type(exc).__name__}: {exc}",
            )

        status = "closed_with_warnings" if report["warnings"] else "closed"
        return finish(status, "", "Project World closed")

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
            
            project_settings = project_data.get("settings")
            if not isinstance(project_settings, dict):
                project_settings = {}
            project_settings.update(settings or {})
            return self.update_project_config_fields({"settings": project_settings})
        
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

        project_json_path = None
        lock_path = None
        manifest_before = None
        lock_before = None
        config_before = None
        try:
            project_path = self.editor_context.current_project_path
            if not project_path:
                return False

            project_json_path = Path(project_path) / "project.json"
            if not os.path.exists(project_json_path):
                return False
            lock_path = Path(project_path) / "project.lock.json"
            manifest_before = project_json_path.read_bytes()
            lock_before = lock_path.read_bytes() if lock_path.is_file() else None

            with project_json_path.open("r", encoding="utf-8") as f:
                project_data = json.load(f)
            config_before = dict(project_data)

            project_data.update(fields or {})
            project_data["modified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            project_json_path.write_text(
                json.dumps(project_data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            from core.VitaLoom.core.bundle_paths import resource_root
            from core.VitaLoom.project.project_write_authority import (
                project_write_interlock,
            )
            from core.VitaLoom.suite.project_lock import ensure_project_lock

            with project_write_interlock(
                project_path,
                authority_action="project_manifest_fields_lock_refresh",
            ):
                ensure_project_lock(
                    project_path,
                    repo_root=resource_root(),
                    overwrite=True,
                )

            setattr(self.editor_context, "current_project_config", project_data)
            self.editor_context.project_modified = False
            return True
        except Exception as e:
            if project_json_path is not None and manifest_before is not None:
                try:
                    project_json_path.write_bytes(manifest_before)
                    if lock_path is not None:
                        if lock_before is None:
                            lock_path.unlink(missing_ok=True)
                        else:
                            lock_path.write_bytes(lock_before)
                    if config_before is not None:
                        setattr(self.editor_context, "current_project_config", config_before)
                except OSError as restore_error:
                    logger.error("回滚项目配置和 lock 失败: %s", restore_error)
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

def release_project_manager_instance(expected: object | None = None) -> bool:
    """Release the concrete singleton without implying save/close semantics.

    When ``expected`` is provided it must be the exact retained instance. The
    caller completes Project World session transitions before this lifecycle seam.
    """

    current = ProjectManager._instance
    if current is None:
        return False
    if expected is not None and current is not expected:
        raise RuntimeError(
            "refusing to release a different ProjectManager singleton instance"
        )
    ProjectManager._instance = None
    return True
