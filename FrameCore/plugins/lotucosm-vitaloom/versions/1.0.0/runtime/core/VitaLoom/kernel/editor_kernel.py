"""编辑器内核：空白主窗口 + 插件/Dock/视口挂载点。

架构数据流::

    main.py → EditorKernel → PluginLoader → LayoutManager.restore_layout
                    ↓
              EditorContext.kernel / event_bus

排错: 见 core/VitaLoom/README.md「启动」「插件」
"""

import json
import os
import time
from typing import List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from .plugin_loader import PluginLoader
from .event_bus import EventBus
from core.VitaLoom.core.runtime_event_bus import (
    RuntimeEventBus,
    require_runtime_event_bus,
)
from .layout_manager import LayoutManager
from ..core.editor_context import get_editor_context
from ..core.logger import get_logger


logger = get_logger("EditorKernel")


class EditorKernelInitializationRollbackError(RuntimeError):
    """Initialization failed and its owned Project World teardown did not settle."""

    def __init__(self, initialization_error: Exception) -> None:
        super().__init__(
            "Editor Kernel initialization failed and Project World rollback did "
            f"not settle: {initialization_error}"
        )


class EditorKernel(QMainWindow):
    """职责: 极简 QMainWindow 宿主，持有 PluginLoader、EventBus、LayoutManager。
    时机: `main.py` 构造后调用 `load_plugins` / `load_plugins_layered`；关闭时 `closeEvent` 保存布局并卸载插件。
    不变量: `editor_context.kernel` 与 `event_bus` 在 `__init__` 末绑定；中央部件可被 `viewport_tabs` 替换。
    排错: 空白界面 → PluginLoader；布局错乱 → LayoutManager；退出未保存 → SceneManager.is_scene_modified。
    """
    
    # 信号
    plugin_loaded = pyqtSignal(str)  # 插件加载完成
    plugin_unloaded = pyqtSignal(str)  # 插件卸载

    STARTUP_DEBUG = os.environ.get("VITALOOM_DEBUG_STARTUP", "0") == "1"

    @classmethod
    def _startup_log(cls, message: str, **data):
        if not cls.STARTUP_DEBUG:
            return
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        log_dir = os.path.join(project_root, ".cursor")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "debug.log")
        payload = {
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    
    def __init__(
        self,
        capability_registry: object | None = None,
        event_bus: object | None = None,
    ):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self._startup_log("EditorKernel.__init__ 开始")
        super().__init__()
        self._startup_log("QMainWindow.__init__ 完成")
        self.editor_context = get_editor_context(capability_registry)
        self.setWindowTitle(self._t("app.title", "VitaLoom Engine"))
        self.setGeometry(100, 100, 1600, 900)

        # 初始化管理器
        self.plugin_loader = PluginLoader(self)
        self._startup_log("PluginLoader 创建成功")
        self.event_bus: RuntimeEventBus = (
            EventBus()
            if event_bus is None
            else require_runtime_event_bus(event_bus)
        )
        self._startup_log("EventBus 创建成功")
        self._plugin_host_capability_lease = None
        self._startup_log("EditorContext 获取完成")
        # 中央视口容器（用于切换不同视口）
        # 注意：LayoutManager会创建标签页系统，这里保留central_stack作为兼容
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        self._startup_log("中央视口容器创建成功")
        # 初始化布局管理器（必须在设置中央部件之后）
        self.layout_manager = LayoutManager(self)
        
        # 如果布局管理器创建了标签页系统，替换中央部件
        if self.layout_manager.viewport_tabs is not None:
            self.setCentralWidget(self.layout_manager.viewport_tabs)
        
        self._startup_log("LayoutManager 创建成功")
        self._register_core_command_actions()
        try:
            from ..ui.theme_manager import get_theme_manager, ThemeType

            get_theme_manager().apply_theme(ThemeType.DARK)
        except Exception as e:
            logger.debug("应用默认主题失败: %s", e)
        # 连接编辑器上下文到内核
        self.editor_context.kernel = self
        self.editor_context.event_bus = self.event_bus
        self._project_world_host_lease = None
        self.project_world_capabilities: dict[str, object] = {}
        try:
            from core.VitaLoom.core.capability_publication import publish_capabilities
            from core.VitaLoom.core.service_keys import (
                PLUGIN_HOST_CONTROL_OBSERVATION,
            )
            from core.VitaLoom.project.project_world_host_composition import (
                acquire_project_world_host,
            )
            from core.VitaLoom.project.project_world_capabilities import (
                register_project_world_host_capabilities,
            )

            self._plugin_host_capability_lease = publish_capabilities(
                self.editor_context.services,
                owner="editor-kernel.plugin-host",
                capabilities={
                    PLUGIN_HOST_CONTROL_OBSERVATION: (
                        self.plugin_loader.nested_plugin_host
                    )
                },
            )
            self._project_world_host_lease = acquire_project_world_host(
                "editor-kernel"
            )
            self.project_world_session_host = self._project_world_host_lease.host
            self.project_world_capabilities = register_project_world_host_capabilities(
                self.editor_context.services, self.project_world_session_host
            )
            from core.VitaLoom.core.bundle_paths import application_root, resource_root

            self.editor_context.repo_root = str(resource_root())
            self.editor_context.application_root = str(application_root())
            from ..simulation.simulation_transport import init_simulation_transport
            from ..simulation.simulation_coordinator import init_simulation_coordinator

            init_simulation_transport(self.editor_context)
            init_simulation_coordinator(self.editor_context)
            self._startup_log("EditorKernel.__init__ complete")
            logger.info("VitaLoom Engine kernel initialized")
            self._startup_project_path: str | None = None
        except Exception as initialization_error:
            if not self._release_project_world_host_lease():
                raise EditorKernelInitializationRollbackError(
                    initialization_error
                ) from initialization_error
            raise

    def _release_project_world_host_lease(self) -> bool:
        """Unpublish exact capabilities, then release this composition lease."""

        plugin_host_lease = getattr(self, "_plugin_host_capability_lease", None)
        if plugin_host_lease is not None:
            try:
                plugin_host_lease.release()
                self._plugin_host_capability_lease = None
            except Exception as exc:
                logger.exception("Failed to unregister plugin Host capability: %s", exc)
                return False

        capabilities = getattr(self, "project_world_capabilities", {})
        if capabilities:
            try:
                from core.VitaLoom.project.project_world_capabilities import (
                    unregister_project_world_host_capabilities,
                )

                unregister_project_world_host_capabilities(
                    self.editor_context.services, capabilities
                )
                self.project_world_capabilities = {}
            except Exception as exc:
                logger.exception(
                    "Failed to unregister Project World capabilities: %s", exc
                )
                return False

        lease = getattr(self, "_project_world_host_lease", None)
        if lease is None:
            return True
        try:
            released = lease.release()
        except Exception as exc:
            logger.exception("Failed to release Project World Host lease: %s", exc)
            return False
        if released or lease.released:
            self._project_world_host_lease = None
        return bool(released or lease.released)

    def _register_core_command_actions(self) -> None:
        from core.VitaLoom.ui.command_actions import register_editor_command_actions

        register_editor_command_actions(
            context=self,
            layout_manager=getattr(self, "layout_manager", None),
        )

    def set_startup_project(self, project_path: str | None) -> None:
        """Hub 或 CLI 指定打开的工程；优先于 last_opened 自动恢复。"""
        if project_path:
            self._startup_project_path = os.path.abspath(project_path)
        else:
            self._startup_project_path = None

    def _t(self, key: str, default: str = "") -> str:
        try:
            ctx = get_editor_context()
            tr_fn = getattr(ctx, "i18n_tr", None)
            if callable(tr_fn):
                return tr_fn(key, default)
        except Exception as e:
            logger.debug("i18n 翻译回退: key=%s error=%s", key, e)
        return default or key
    
    def load_plugins(self, plugin_dirs: List[str]):
        """职责: 扫描目录加载全部 `*_plugin.py` 并在 Dock 就绪后恢复布局。
        时机: 启动阶段由 `main.py` 调用一次。
        不变量: 插件加载与布局恢复分离，布局在 QTimer 500ms 后执行。
        排错: Dock 缺失 → PluginLoader 日志；布局 → `layout_manager.restore_layout`。
        """
        self.plugin_loader.load_from_directories(plugin_dirs)
        self._schedule_post_plugin_init()

    def load_plugins_layered(self, layered_dirs: dict[str, List[str]]):
        """职责: 按 core_mod / official_mod / user_mod 分层扫描插件目录。
        时机: 推荐启动路径（`main.py` 传入分层目录表）。
        不变量: 同 scope 内仍走依赖解析与 `_finalize_loading` 顺序。
        排错: 官方插件未加载 → 检查 scope 键名与目录是否存在。
        """
        self.plugin_loader.load_from_layered_directories(layered_dirs)
        self._schedule_post_plugin_init()

    def refresh_editor_contributions(self) -> None:
        """Refresh Host-copied Editor contributions through the current UI Adapter."""
        self.plugin_loader.legacy_editor_plugin_adapter.refresh_editor_contributions()

    def _schedule_post_plugin_init(self, delay_ms: int = 500) -> None:
        """插件加载后延迟恢复布局并尝试打开上次项目。"""
        from PyQt6.QtCore import QTimer

        def _restore_or_apply_default():
            restored = self.layout_manager.restore_layout()
            if not restored:
                self.layout_manager.apply_default_workspace_layout()
            self._try_open_last_project_on_startup()

        QTimer.singleShot(delay_ms, _restore_or_apply_default)

    def _try_open_last_project_on_startup(self) -> None:
        """Restore a Project World through the configured Host capability."""

        try:
            host = self.project_world_session_host
            pending = getattr(self, "_startup_project_path", None)
            if pending and os.path.isfile(os.path.join(pending, "project.json")):
                logger.info("Hub/CLI 指定打开项目: %s", pending)
                host.open_project(pending)
                self._startup_project_path = None
                return
            host.open_last_project_on_startup()
        except Exception as exc:
            logger.warning("启动自动打开项目失败: %s", exc)

    def _flush_project_before_shutdown(self) -> dict[str, object]:
        """Flush through the explicit Project World session Host capability."""

        from core.VitaLoom.project.project_world_report import (
            finalize_project_world_report,
        )

        try:
            report = self.project_world_session_host.flush_current_project()
            if not isinstance(report, dict):
                raise TypeError("Project World session Host returned a non-report value")
            if report.get("status") not in {"flushed", "noop"}:
                logger.warning(
                    "退出前保存项目状态未完成 [%s]: %s",
                    report.get("code", "project_world_flush_failed"),
                    report.get("message", ""),
                )
            return report
        except Exception as exc:
            logger.warning("退出前保存项目状态失败: %s", exc)
            return finalize_project_world_report(
                {
                    "transition": "flush",
                    "status": "failed",
                    "code": "project_world_session_host_exception",
                    "message": f"{type(exc).__name__}: {exc}",
                    "actions": [],
                }
            )

    def get_event_bus(self) -> RuntimeEventBus:
        """获取事件总线。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.event_bus
    
    def get_context(self):
        """获取编辑器上下文。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.editor_context
    
    def closeEvent(self, event):
        """Prompt for dirty-scene intent, then flush and tear down the legacy Host."""

        from PyQt6.QtWidgets import QMessageBox
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_manager = get_scene_manager()
        flush_before_close = True
        if scene_manager.is_scene_modified():
            reply = QMessageBox.question(
                self,
                self._t("kernel.dialog.save_changes.title", "保存更改"),
                self._t(
                    "kernel.dialog.save_changes.content",
                    "场景已被修改，是否在退出前保存？",
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.No:
                flush_before_close = False

        if flush_before_close:
            report = self._flush_project_before_shutdown()
            if report.get("status") not in {"flushed", "noop"}:
                QMessageBox.critical(
                    self,
                    self._t("dialog.error.title", "错误"),
                    self._t(
                        "dialog.save_project.failed",
                        "保存项目失败，编辑器将保持打开。",
                    ),
                )
                event.ignore()
                return

        if hasattr(self, "layout_manager"):
            self.layout_manager.save_layout()
            cleanup_viewports = getattr(
                self.layout_manager,
                "dispose_viewport_runtime_capabilities",
                None,
            )
            cleanup = cleanup_viewports() if callable(cleanup_viewports) else {"failed": ()}
            if cleanup.get("failed"):
                QMessageBox.critical(
                    self,
                    self._t("dialog.error.title", "Error"),
                    "Viewport runtime capability cleanup failed; the editor will remain open.",
                )
                event.ignore()
                return

        try:
            shutdown_report = self.plugin_loader.shutdown_plugins()
        except Exception as exc:
            logger.exception("Nested plugin Host shutdown failed: %s", exc)
            QMessageBox.critical(
                self,
                self._t("dialog.error.title", "Error"),
                "Plugin Host shutdown failed; the editor will remain open.",
            )
            event.ignore()
            return
        if shutdown_report.get("status") not in {"settled", "noop"}:
            logger.error(
                "Nested plugin Host shutdown did not settle: %s",
                shutdown_report,
            )
            QMessageBox.critical(
                self,
                self._t("dialog.error.title", "Error"),
                "Plugin Host shutdown did not settle; the editor will remain open.",
            )
            event.ignore()
            return

        if not EditorKernel._release_project_world_host_lease(self):
            QMessageBox.critical(
                self,
                self._t("dialog.error.title", "Error"),
                "Project World Host release failed; the editor will remain open.",
            )
            event.ignore()
            return

        event.accept()
