"""
游戏视口插件：注册 SR 场景运行时视口并转发 simulation_* 事件。

架构数据流::

    simulation_play → on_play → GameViewport._start_simulation

SR 边界: 主世界播放、膜拓扑、chemo 趋食均在本视口内；非 `builtin.systems.simulation.Simulation`。

排错: 见 `builtin/README.md`（占位符、播放无反应）。
"""

from core.plugin.interfaces import IViewportProvider
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from typing import Dict, Any

from core.VitaLoom.core.logger import get_logger

logger = get_logger("GameViewportPlugin")


class GameViewportPlugin(IViewportProvider):
    """SR 游戏视口插件：加载时订阅 play/pause/stop，卸载时退订并销毁 widget。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "GameViewport",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "游戏运行视口，用于运行和观察模拟",
            "dependencies": [],
            "provides": ["viewport"],
        }

    def on_load(self, editor_context):
        """保存上下文并订阅 simulation_play/pause/stop 与 language_changed。"""
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.viewport = None

        editor_context.event_bus.subscribe("simulation_play", self.on_play)
        editor_context.event_bus.subscribe("simulation_pause", self.on_pause)
        editor_context.event_bus.subscribe("simulation_stop", self.on_stop)
        editor_context.event_bus.subscribe("language_changed", self._on_language_changed)

    def on_unload(self):
        if hasattr(self, "context") and self.context:
            try:
                self.context.event_bus.unsubscribe("simulation_play", self.on_play)
                self.context.event_bus.unsubscribe("simulation_pause", self.on_pause)
                self.context.event_bus.unsubscribe("simulation_stop", self.on_stop)
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception as e:
                logger.warning("GameViewport 取消订阅失败: %s", e)

        if self.viewport:
            self.viewport.deleteLater()

    def create_viewport_widget(self) -> QWidget:
        """实例化 `GameViewport` 或降级为占位 QLabel。

        职责: 返回视口根 widget 供 ViewportManager 嵌入。
        时机: 编辑器布局创建「游戏」视口时。
        不变量: 成功时 `self.viewport` 为 GameViewport 实例方可 `on_play`。
        排错: 日志「无法加载 GameViewport」→ 查 import 与 PyQt/pygame 依赖。
        """
        try:
            from core.VitaLoom.viewports.game_viewport import GameViewport

            self.viewport = GameViewport()
            logger.info("GameViewport 创建成功")
        except Exception as e:
            logger.exception("无法加载 GameViewport: %s", e)
            try:
                from PyQt6.QtWidgets import QLabel, QVBoxLayout
                from PyQt6.QtCore import Qt as QtCore

                widget = QWidget()
                layout = QVBoxLayout(widget)
                label = QLabel(
                    self._t(
                        "game_viewport.placeholder",
                        "游戏视口\n\n点击“运行”后模拟将在这里执行。",
                    )
                )
                label.setAlignment(QtCore.AlignmentFlag.AlignCenter)
                label.setStyleSheet("font-size: 14px; color: #888;")
                layout.addWidget(label)
                self.viewport = widget
                logger.info("已创建 GameViewport 占位符")
            except Exception as e2:
                logger.warning("创建占位符失败: %s", e2)
                self.viewport = QWidget()

        return self.viewport

    def get_viewport_id(self) -> str:
        return "game"

    def get_viewport_name(self) -> str:
        return self._t("game_viewport.name", "游戏")

    def on_viewport_activated(self):
        logger.debug("🎮 %s", self._t("game_viewport.activated", "游戏视口已激活"))

    def on_viewport_deactivated(self):
        logger.debug("🎮 %s", self._t("game_viewport.deactivated", "游戏视口已停用"))

    def _is_real_game_viewport(self) -> bool:
        if not self.viewport:
            return False
        try:
            from core.VitaLoom.viewports.game_viewport import GameViewport

            return isinstance(self.viewport, GameViewport)
        except Exception as e:
            logger.warning("GameViewport 类型检查失败: %s", e)
            return False

    def on_play(self, data):
        """响应 simulation_play，调用真实视口的 `_start_simulation`。

        职责: 校验实例类型后启动 SR 场景运行时。
        时机: 工具栏播放或快捷键触发 event_bus。
        不变量: 占位 widget 时仅打 warning，不抛异常。
        排错: 「缺少 _start_simulation」→ GameViewport 版本与插件不匹配。
        """
        try:
            if not self.viewport:
                logger.warning("GameViewport 未初始化")
                return

            if not self._is_real_game_viewport():
                logger.warning("当前视口不是 GameViewport 实例，无法启动模拟")
                return

            if hasattr(self.viewport, "_start_simulation"):
                self.viewport._start_simulation()
                logger.info("▶ %s", self._t("game_viewport.simulation.starting", "正在启动模拟..."))
            else:
                logger.warning("GameViewport 缺少 _start_simulation 方法")
        except Exception as e:
            logger.exception("启动模拟失败: %s", e)

    def on_pause(self, data):
        try:
            if not self.viewport:
                logger.warning("GameViewport 未初始化")
                return

            if not self._is_real_game_viewport():
                logger.warning("当前视口不是 GameViewport 实例，无法暂停模拟")
                return

            if hasattr(self.viewport, "_pause_simulation"):
                self.viewport._pause_simulation()
                logger.info("⏸ %s", self._t("game_viewport.simulation.pausing", "正在暂停模拟..."))
            else:
                logger.warning("GameViewport 缺少 _pause_simulation 方法")
        except Exception as e:
            logger.exception("暂停模拟失败: %s", e)

    def on_stop(self, data):
        try:
            if not self.viewport:
                logger.warning("GameViewport 未初始化")
                return

            if not self._is_real_game_viewport():
                logger.warning("当前视口不是 GameViewport 实例，无法停止模拟")
                return

            if hasattr(self.viewport, "_stop_simulation"):
                self.viewport._stop_simulation()
                logger.info("⏹ %s", self._t("game_viewport.simulation.stopping", "正在停止模拟..."))
            else:
                logger.warning("GameViewport 缺少 _stop_simulation 方法")
        except Exception as e:
            logger.exception("停止模拟失败: %s", e)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
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
