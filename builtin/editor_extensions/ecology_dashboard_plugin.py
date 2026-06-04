# -*- coding: utf-8 -*-
"""生态统计 Dock 插件：展示 GameViewport SR 运行时快照（非 PS Simulation）。

架构数据流::

    GameViewport tick → SR 统计 API → EcologyDashboardPanel 刷新

排错: 见 `builtin/README.md`（生态面板无数据、未播放）。
"""
from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from core.plugin.interfaces import IDockProvider
from core.VitaLoom.core.logger import get_logger

logger = get_logger("EcologyDashboardPlugin")


class EcologyDashboardPlugin(IDockProvider):
    """SR 生态 Dock：on_load 创建面板，卸载时销毁 widget。"""

    DOCK_ID = "EcologyDashboard"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "EcologyDashboard",
            "version": "1.0.0",
            "author": "Lotucosm",
            "description": "SR 运行时莲池生态统计（中文）",
            "dependencies": [],
            "provides": ["dock"],
        }

    def on_load(self, editor_context: Any) -> None:
        """绑定 editor_context/kernel，延迟到 create_dock_widget 建面板。

        职责: 保存上下文供 EcologyDashboardPanel 拉取 SR 快照。
        时机: PluginLoader 加载 builtin 插件时调用一次。
        不变量: 不订阅模拟事件；数据由面板向 GameViewport 查询。
        排错: Dock 空白 → 查 `EcologyDashboardPanel` 导入异常日志。
        """
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock = None

    def on_unload(self) -> None:
        if self.dock:
            self.dock.deleteLater()

    def create_dock_widget(self) -> QDockWidget:
        """构造右侧 Dock 并嵌入 EcologyDashboardPanel。

        职责: 提供 `DOCK_ID` 对象名供布局恢复。
        时机: 内核首次需要该 Dock 或用户打开面板时。
        不变量: 失败时显示占位 QLabel，不阻断其它插件。
        排错: 「生态面板加载失败」→ 查 `core.VitaLoom.docks.ecology_dashboard` 导入。
        """
        self.dock = QDockWidget("生态统计")
        self.dock.setObjectName(self.DOCK_ID)
        try:
            from core.VitaLoom.docks.ecology_dashboard import EcologyDashboardPanel

            panel = EcologyDashboardPanel(self.context)
        except Exception as exc:
            logger.warning("无法加载 EcologyDashboardPanel: %s", exc)
            from PyQt6.QtWidgets import QLabel

            panel = QLabel("生态面板加载失败")
        self.dock.setWidget(panel)
        return self.dock

    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": False,
            "can_close": True,
        }
