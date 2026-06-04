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
from .layout_manager import LayoutManager
from ..core.editor_context import get_editor_context
from ..core.logger import get_logger


logger = get_logger("EditorKernel")


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
    
    def __init__(self):
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
        self.setWindowTitle(self._t("app.title", "VitaLoom Engine"))
        self.setGeometry(100, 100, 1600, 900)

        # 初始化管理器
        self.plugin_loader = PluginLoader(self)
        self._startup_log("PluginLoader 创建成功")
        self.event_bus = EventBus()
        self._startup_log("EventBus 创建成功")
        self.editor_context = get_editor_context()
        self._startup_log("EditorContext 获取完成")
        # 中央视口容器（用于切换不同视口）
        # 注意：LayoutManager会创建标签页系统，这里保留central_stack作为兼容
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        self._startup_log("中央视口容器创建成功")
        # 初始化布局管理器（必须在设置中央部件之后）
        self.layout_manager = LayoutManager(self)
        
        # 如果布局管理器创建了标签页系统，替换中央部件
        if self.layout_manager.viewport_tabs:
            self.setCentralWidget(self.layout_manager.viewport_tabs)
        
        self._startup_log("LayoutManager 创建成功")
        try:
            from ..ui.theme_manager import get_theme_manager, ThemeType

            get_theme_manager().apply_theme(ThemeType.DARK)
        except Exception as e:
            logger.debug("应用默认主题失败: %s", e)
        # 连接编辑器上下文到内核
        self.editor_context.kernel = self
        self.editor_context.event_bus = self.event_bus
        from ..simulation.simulation_transport import init_simulation_transport

        init_simulation_transport(self.editor_context)
        self._startup_log("EditorKernel.__init__ 完成")
        logger.info("VitaLoom Engine 内核初始化完成")

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
        """插件与布局就绪后恢复上次打开的项目。"""
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            get_project_manager().open_last_project_on_startup()
        except Exception as e:
            logger.warning("启动自动打开项目失败: %s", e)

    def _flush_project_before_shutdown(self) -> None:
        """退出前落盘当前场景与 active_scene。"""
        try:
            from core.VitaLoom.project.project_manager import get_project_manager

            ctx = self.editor_context
            path = getattr(ctx, "current_project_path", None)
            if path:
                get_project_manager().flush_current_project()
        except Exception as e:
            logger.warning("退出前保存项目状态失败: %s", e)
    
    def get_event_bus(self) -> EventBus:
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
        """职责: 关闭前提示保存脏场景、持久化布局、卸载全部插件。
        时机: 用户关闭主窗口时由 Qt 调用。
        不变量: Cancel 时 `event.ignore()`；Yes 时调用 `SceneManager.save_scene`。
        排错: 未提示保存 → `is_scene_modified`；插件残留 → `unload_plugin` 异常日志。
        """
        # 检查未保存的更改
        from core.VitaLoom.scene.scene_manager import get_scene_manager
        sm = get_scene_manager()
        
        if sm.is_scene_modified():
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                self._t("kernel.dialog.save_changes.title", "保存更改"),
                self._t("kernel.dialog.save_changes.content", "场景已被修改，是否在退出前保存？"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                sm.save_scene()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        # 保存当前布局（参考Unity的布局保存功能）
        if hasattr(self, 'layout_manager'):
            self.layout_manager.save_layout()

        self._flush_project_before_shutdown()
        
        # 卸载所有插件
        plugin_names = list(self.plugin_loader.loaded_plugins.keys())
        for plugin_name in plugin_names:
            try:
                self.plugin_loader.unload_plugin(plugin_name)
            except Exception as e:
                logger.exception("卸载插件失败: plugin=%s error=%s", plugin_name, e)
        
        event.accept()
