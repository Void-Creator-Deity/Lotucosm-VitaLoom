"""项目插件管理器 Dock：官方能力包、项目 addon 与项目级插件状态。

排错: 见 `builtin/README.md`、`docs/package_architecture.md`。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QSplitter,
    QFrame,
    QMessageBox,
    QToolButton,
    QMenu,
)
from PyQt6.QtGui import QAction

from core.VitaLoom.commands.registry import CommandSpec, command_error, command_ok
from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.capability_publication import publish_capabilities
from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host
from core.VitaLoom.project.project_world_capabilities import (
    get_project_world_configuration_host,
    get_project_world_manifest_validation_host,
    get_project_world_read_model,
)
from core.VitaLoom.ui.base_editor_widget import BaseEditorWidget
from builtin.editor_extensions.package_services import PackageCatalogService, PackageOperationService
from builtin.editor_extensions.package_domain.catalog import (
    collect_update_candidates,
    matches_status_filter,
    merge_package_lists,
    normalize_package,
    parse_dependency_expr,
    parse_version,
    select_target_updates,
    should_block_enable,
    version_gte,
)
from builtin.editor_extensions.package_domain.project_operations import PackageProjectOperations
from core.VitaLoom.core.service_keys import (
    DOWNLOADER,
    PACKAGE_CATALOG,
    PACKAGE_OPERATIONS,
)
from builtin.editor_extensions.plugin_runtime_ops import PluginRuntimeOpsMixin
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PackageManagerPlugin")


class PackageManagerPlugin(IRuntimePlugin, ICommandProvider, PluginRuntimeOpsMixin):
    """当前项目插件管理器：扩展依赖/版本/安装 + 项目级启停。"""

    DOCK_ID = "Package Manager"
    _PLUGIN_ITEM_PREFIX = "plugin:"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PackageManagerPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "当前项目插件管理器（官方能力包、项目 addon、项目引用扩展）",
            "dependencies": ["LocalizationPlugin"],
            "provides": ["dock", "command", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "package_manager.surface",
                    "kind": "dock_surface",
                    "dock_id": self.DOCK_ID,
                    "title_key": "plugin_manager.title",
                    "default_title": "项目插件",
                    "area": "right",
                    "default_visible": False,
                    "can_close": True,
                    "can_float": True,
                    "can_move": True,
                    "tabbed_with": None,
                    "order": 70,
                    "refresh_events": ["language_changed"],
                },
                {
                    "id": "package_manager.reveal",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "tools",
                            "label_key": "menu.tools",
                            "default_label": "工具",
                        }
                    ],
                    "label_key": "plugin_manager.title",
                    "default_label": "项目插件",
                    "command_id": "plugin.package_manager.reveal",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 70,
                },
            ],
            "protected": True,
        }

    def on_load(self, editor_context):
        # A reused plugin instance must release its exact previous activation
        # resources before accepting a new Host context.
        if any(
            (
                getattr(self, "_event_subscriptions", ()),
                getattr(self, "_kernel_signal_connections", ()),
                getattr(self, "_service_publication", None) is not None,
            )
        ):
            self.on_unload()

        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.dock: Optional[QDockWidget] = None
        self.window: Optional[QDialog] = None
        self.package_list: Optional[QListWidget] = None
        self.detail_text: Optional[QTextEdit] = None
        self.search_input: Optional[QLineEdit] = None
        self.tab_bar: Optional[QTabWidget] = None
        self.status_filter: Optional[QComboBox] = None
        self.source_filter: Optional[QComboBox] = None
        self._packages: List[Dict[str, Any]] = []
        self._update_candidates: Dict[str, str] = {}
        self._checked_update_ids: set[str] = set()
        self.queue_select_all_btn: Optional[QPushButton] = None
        self.queue_invert_btn: Optional[QPushButton] = None
        self.queue_clear_btn: Optional[QPushButton] = None
        self.queue_only_checked_cb: Optional[QCheckBox] = None
        self.queue_stats_label: Optional[QLabel] = None
        self.result_text: Optional[QTextEdit] = None
        self._package_count_label: Optional[QLabel] = None
        self._float_open_action: Optional[QAction] = None
        self.open_mode_toggle_cb: Optional[QCheckBox] = None
        self._queue_bar: Optional[QWidget] = None
        self._plugin_runtime_bar: Optional[QWidget] = None
        self._scope_hint: Optional[QLabel] = None
        self._clear_search_btn: Optional[QPushButton] = None
        self._refresh_btn: Optional[QPushButton] = None
        self._enable_btn: Optional[QPushButton] = None
        self._disable_btn: Optional[QPushButton] = None
        self._more_btn: Optional[QToolButton] = None
        self._more_actions: Dict[str, QAction] = {}
        self._reload_btn: Optional[QPushButton] = None
        self._unload_btn: Optional[QPushButton] = None
        self._project_disable_btn: Optional[QPushButton] = None
        self._project_enable_btn: Optional[QPushButton] = None
        self._last_floating_geometry_hex: str = ""
        self._ui_building: bool = False
        self._pending_language_rebuild: bool = False
        self._ui_signals_connected: bool = False
        self.catalog_service: Optional[PackageCatalogService] = None
        self.operation_service: Optional[PackageOperationService] = None
        self._service_publication = None
        self._event_subscriptions: list[tuple[object, str, object]] = []
        self._kernel_signal_connections: list[tuple[object, object]] = []

        try:
            self._subscribe_runtime_events()
            self.catalog_service = PackageCatalogService(self._get_repo_root())
            self.operation_service = PackageOperationService(
                get_project_world_read_model(self.context),
                get_project_world_configuration_host(self.context),
            )
            services = getattr(self.context, "services", None)
            if services is not None:
                self._service_publication = publish_capabilities(
                    services,
                    owner="adapter.package-manager",
                    capabilities={
                        PACKAGE_CATALOG: self.catalog_service,
                        PACKAGE_OPERATIONS: self.operation_service,
                    },
                )
            self._warm_package_cache()
            self._connect_kernel_signals()
        except BaseException as activation_error:
            try:
                self._release_activation_resources()
            except BaseException as rollback_error:
                logger.warning(
                    "PackageManager activation rollback incomplete after %s: %s",
                    activation_error,
                    rollback_error,
                )
            raise

    def _subscribe_runtime_events(self) -> None:
        event_bus = getattr(getattr(self, "context", None), "event_bus", None)
        if event_bus is None:
            return
        bindings = (
            ("language_changed", self._on_language_changed),
            ("project_opened", self._on_project_opened),
            ("project_plugins_synced", self._on_project_plugins_synced),
            ("project_manifest_issues", self._on_project_manifest_issues),
        )
        for event_name, callback in bindings:
            event_bus.subscribe(event_name, callback)
            self._event_subscriptions.append((event_bus, event_name, callback))

    def _connect_kernel_signals(self) -> None:
        kernel = getattr(self, "kernel", None)
        if kernel is None:
            return
        bindings = (
            (getattr(kernel, "plugin_loaded", None), self._on_runtime_plugin_loaded),
            (getattr(kernel, "plugin_unloaded", None), self._on_runtime_plugin_unloaded),
        )
        for signal, callback in bindings:
            if signal is None:
                continue
            signal.connect(callback)
            self._kernel_signal_connections.append((signal, callback))

    def _runtime_selected_plugin_id(self) -> Optional[str]:
        return self._get_selected_plugin_id()

    def _runtime_refresh(self) -> None:
        if self._ensure_ui_refs():
            self._refresh()
            self._on_selection_changed()

    def on_unload(self):
        release_error: BaseException | None = None
        try:
            self._release_activation_resources()
        except BaseException as error:
            release_error = error

        resources_released = not any(
            (
                getattr(self, "_event_subscriptions", ()),
                getattr(self, "_kernel_signal_connections", ()),
                getattr(self, "_service_publication", None) is not None,
            )
        )
        if resources_released:
            dock = getattr(self, "dock", None)
            window = getattr(self, "window", None)
            self.dock = None
            self.window = None
            if dock is not None:
                dock.deleteLater()
            if window is not None:
                window.deleteLater()

        if release_error is not None:
            raise release_error

    def _release_activation_resources(self) -> None:
        first_error: BaseException | None = None
        for release in (
            self._release_kernel_signal_connections,
            self._release_service_publication,
            self._release_event_subscriptions,
        ):
            try:
                release()
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    def _release_event_subscriptions(self) -> None:
        subscriptions = list(getattr(self, "_event_subscriptions", ()))
        self._event_subscriptions = []
        failed: list[tuple[object, str, object]] = []
        first_error: BaseException | None = None
        for event_bus, event_name, callback in reversed(subscriptions):
            try:
                event_bus.unsubscribe(event_name, callback)
            except BaseException as error:
                failed.append((event_bus, event_name, callback))
                if first_error is None:
                    first_error = error
                logger.warning(
                    "PackageManager event unsubscribe failed: event=%s error=%s",
                    event_name,
                    error,
                )
        self._event_subscriptions.extend(reversed(failed))
        if first_error is not None:
            raise first_error

    def _release_kernel_signal_connections(self) -> None:
        connections = list(getattr(self, "_kernel_signal_connections", ()))
        self._kernel_signal_connections = []
        failed: list[tuple[object, object]] = []
        first_error: BaseException | None = None
        for signal, callback in reversed(connections):
            try:
                signal.disconnect(callback)
            except BaseException as error:
                failed.append((signal, callback))
                if first_error is None:
                    first_error = error
                logger.warning(
                    "PackageManager kernel signal disconnect failed: error=%s",
                    error,
                )
        self._kernel_signal_connections.extend(reversed(failed))
        if first_error is not None:
            raise first_error

    def _release_service_publication(self) -> None:
        publication = getattr(self, "_service_publication", None)
        if publication is not None:
            publication.release()
            self._service_publication = None
        if self._service_publication is None:
            self.catalog_service = None
            self.operation_service = None

    def create_dock_widget(self) -> QDockWidget:
        self._ui_building = True
        try:
            self.dock = QDockWidget(self._t("plugin_manager.title", "项目插件"))
            self.dock.setObjectName(self.DOCK_ID)

            content = self._build_main_widget(self.dock)
            self.dock.setWidget(content)
            self.dock.setMinimumSize(720, 520)
        finally:
            self._ui_building = False

        if self._pending_language_rebuild:
            self._pending_language_rebuild = False
            self.retranslate_ui()
            return self.dock

        self._refresh()
        self._on_selection_changed()
        return self.dock


    def get_command_specs(self) -> List[CommandSpec]:
        return [
            CommandSpec(
                id="plugin.package_manager.reveal",
                title="Reveal Package Manager",
                description=(
                    "Reveal the existing Package Manager Dock using the current "
                    "Host visibility and geometry policy."
                ),
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object"},
                handler=self._reveal_command,
                mutates=True,
                undoable=False,
                requires_gui=True,
                capability="vitalloom.editor_essentials",
                owner="PackageManagerPlugin",
            )
        ]

    def _reveal_command(
        self, payload: object, command_context: object
    ) -> Dict[str, Any]:
        del payload, command_context
        try:
            surface = self.show()
        except Exception as error:
            logger.exception("PackageManager reveal command failed")
            return command_error(
                "package_manager_reveal_failed",
                "Package Manager could not be revealed",
                details={"error": str(error)},
            )
        if surface not in {"dock", "dialog"}:
            return command_error(
                "package_manager_reveal_unavailable",
                "Package Manager has no available current-Host surface",
            )
        return command_ok(
            {
                "status": "revealed",
                "surface": surface,
                "dock_id": self.DOCK_ID,
            }
        )

    def _restore_dock_floating_geometry(self):
        if not self.dock or not self._last_floating_geometry_hex:
            return
        try:
            from PyQt6.QtCore import QByteArray
            data = bytes.fromhex(self._last_floating_geometry_hex)
            self.dock.restoreGeometry(QByteArray(data))
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)

    def _capture_dock_floating_geometry(self):
        if not self.dock:
            return
        try:
            if self.dock.isFloating():
                self._last_floating_geometry_hex = bytes(self.dock.saveGeometry()).hex()
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)

    def _sync_hex_from_dock_for_fallback(self):
        """与 LayoutManager 几何缓存对齐：无 LM 或极端回退路径仍可用 saveGeometry hex。"""
        self._capture_dock_floating_geometry()

    def _toggle_dock_floating(self):
        if not self.dock:
            return
        lm = getattr(self.kernel, "layout_manager", None) if self.kernel else None
        if lm and hasattr(lm, "toggle_dock_floating"):
            lm.toggle_dock_floating(self.DOCK_ID)
            self._sync_hex_from_dock_for_fallback()
        else:
            if self.dock.isFloating():
                self._capture_dock_floating_geometry()
                self.dock.setFloating(False)
            else:
                self.dock.setFloating(True)
                self._restore_dock_floating_geometry()
                self.dock.raise_()
                self.dock.activateWindow()
        self._update_float_toggle_btn_text()

    def _update_float_toggle_btn_text(self):
        """浮动切换已移入「更多操作」菜单。"""

    def _update_package_count_label(self, visible: int, total: int) -> None:
        if not self._package_count_label:
            return
        self._package_count_label.setText(
            self._t("package_manager.list_count", "显示 {visible} / 共 {total}").format(
                visible=visible, total=total
            )
        )

    def _render_empty_list_hint(
        self,
        *,
        tab_filter: str,
        status_filter: str,
        keyword: str,
        total_loaded: int,
    ) -> None:
        if not self.detail_text:
            return
        lines: List[str] = [
            self._t("package_manager.empty.title", "当前筛选下没有可显示的包"),
        ]
        if tab_filter == "community":
            lines.append(
                self._t(
                    "package_manager.empty.community",
                    "「社区」仅列出 file/url 外部注册表中的包。"
                    "当前索引 builtin/package_index.json 均为官方 builtin 来源，因此此页通常为空。"
                    "可在 workspace/state/system/package_registries.json 添加社区源。",
                )
            )
        elif tab_filter == "official":
            lines.append(
                self._t(
                    "package_manager.empty.official",
                    "「官方」显示 origin=official 或 category=official 的包。",
                )
            )
        elif tab_filter == "core":
            lines.append(
                self._t(
                    "package_manager.empty.core",
                    "「核心」显示 origin=core 的必装平台包（莲池 + 织机内核）。",
                )
            )
        elif tab_filter == "resources":
            lines.append(
                self._t(
                    "package_manager.empty.resources",
                    "「资源」显示 role=resource 或含 resources[] 的资源包。",
                )
            )
        elif tab_filter == "updates":
            lines.append(
                self._t(
                    "package_manager.empty.updates",
                    "「更新」仅显示 catalog 中存在更高版本的包。",
                )
            )
        elif tab_filter == "plugins":
            lines.append(
                self._t(
                    "package_manager.empty.plugins",
                    "「插件」列出扩展包索引中声明的编辑器插件（约 {total} 个）。"
                    "若为空请改「全部状态」或清除搜索。",
                ).format(total=total_loaded)
            )
        else:
            lines.append(
                self._t(
                    "package_manager.empty.all",
                    "「全部」列出 catalog 中所有包（共 {total} 个）。",
                ).format(total=total_loaded)
            )
        if status_filter == "enabled":
            lines.append(
                self._t(
                    "package_manager.empty.filter_enabled",
                    "状态筛选为「已启用」：仅显示至少有一个项目级启用插件的包；"
                    "无插件的能力包在「全部」页签仍可见。可改为「全部状态」。",
                )
            )
        elif status_filter == "disabled":
            lines.append(
                self._t(
                    "package_manager.empty.filter_disabled",
                    "状态筛选为「已禁用」：仅显示所有插件均在 disabled_plugins 中的包。",
                )
            )
        elif status_filter == "issues":
            lines.append(
                self._t(
                    "package_manager.empty.filter_issues",
                    "状态筛选为「有问题」：仅显示依赖/冲突未满足的包。",
                )
            )
        if keyword:
            lines.append(
                self._t(
                    "package_manager.empty.keyword",
                    "搜索关键词「{kw}」无匹配。",
                ).format(kw=keyword)
            )
        self.detail_text.setPlainText("\n\n".join(lines))

    def _ensure_floating_dock_size(self) -> None:
        """浮动窗口过小时放大，避免按钮与列表区被压扁。"""
        if not self.dock or not self.dock.isFloating():
            return
        min_w, min_h = 720, 520
        geo = self.dock.geometry()
        if geo.width() < min_w or geo.height() < min_h:
            self.dock.resize(max(min_w, geo.width()), max(min_h, geo.height()))

    @staticmethod
    def _widget_alive(widget: Optional[QWidget]) -> bool:
        if widget is None:
            return False
        try:
            import sip

            return not sip.isdeleted(widget)
        except Exception:
            return True

    def _ensure_ui_refs(self) -> bool:
        """列表控件在语言切换重建时可能被销毁，从 dock 内容恢复引用。"""
        if self._widget_alive(self.package_list):
            return True
        root: Optional[QWidget] = None
        if self._widget_alive(self.dock):
            root = self.dock.widget()
        elif self._widget_alive(self.window):
            root = self.window
        if root is None:
            return False
        lst = root.findChild(QListWidget, "packageManagerList")
        detail = root.findChild(QTextEdit, "packageManagerDetail")
        result = root.findChild(QTextEdit, "packageManagerResult")
        if lst is not None:
            self.package_list = lst
        if detail is not None:
            self.detail_text = detail
        if result is not None:
            self.result_text = result
        return self._widget_alive(self.package_list)

    def _connect_ui_signals(self) -> None:
        if self._ui_signals_connected:
            return
        if self.search_input:
            self.search_input.textChanged.connect(self._refresh)
        if self.status_filter:
            self.status_filter.currentIndexChanged.connect(self._refresh)
        if self.source_filter:
            self.source_filter.currentIndexChanged.connect(self._refresh)
        if self.tab_bar:
            self.tab_bar.currentChanged.connect(self._on_tab_changed)
        if self.queue_only_checked_cb:
            self.queue_only_checked_cb.stateChanged.connect(self._refresh)
        if self.package_list:
            self.package_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._ui_signals_connected = True

    def _build_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        统一构建包管理器主界面（独立窗口与 dock 入口共享）。
        注意：这里只负责控件创建与信号绑定；数据刷新由 `_refresh()` 完成。
        """
        self._ui_signals_connected = False
        root = BaseEditorWidget()
        root.setMinimumSize(680, 480)
        if parent is not None:
            root.setParent(parent)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._scope_hint = QLabel(
            self._t(
                "package_manager.scope_hint",
                "管理织机官方/社区扩展与编辑器插件。引擎版本见 Hub 或「核心」标签（只读）。"
                "项目资源请用项目面板导入，不在此安装。",
            )
        )
        self._scope_hint.setWordWrap(True)
        self._scope_hint.setStyleSheet("color: #8899aa; font-size: 11px;")
        layout.addWidget(self._scope_hint)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self._t("package_manager.search_placeholder", "按名称/ID/分类过滤..."))
        search_row.addWidget(self.search_input, 1)
        self._clear_search_btn = QPushButton(self._t("package_manager.search_clear", "清除"))
        self._clear_search_btn.setMaximumWidth(56)
        self._clear_search_btn.clicked.connect(self._clear_search)
        search_row.addWidget(self._clear_search_btn)
        self.status_filter = QComboBox()
        self.status_filter.addItems(
            [
                self._t("package_manager.filter.status.all", "全部状态"),
                self._t("package_manager.filter.status.enabled", "已启用"),
                self._t("package_manager.filter.status.disabled", "已禁用"),
                self._t("package_manager.filter.status.issues", "有问题"),
            ]
        )
        search_row.addWidget(self.status_filter)

        self.source_filter = QComboBox()
        for label, value in (
            (self._t("package_manager.filter.source.all", "全部来源"), "all"),
            (self._t("package_manager.filter.source.builtin", "内置 builtin"), "builtin"),
            (self._t("package_manager.filter.source.file", "本地 file"), "file"),
            (self._t("package_manager.filter.source.url", "远程 url"), "url"),
        ):
            self.source_filter.addItem(label, value)
        search_row.addWidget(self.source_filter)
        layout.addLayout(search_row)

        self.tab_bar = QTabWidget()
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.installed", "全部"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.plugins", "插件"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.core", "核心"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.official", "官方"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.resources", "资源"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.community", "社区"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.updates", "更新"))
        layout.addWidget(self.tab_bar)

        self._queue_bar = QWidget()
        queue_row = QHBoxLayout(self._queue_bar)
        queue_row.setContentsMargins(0, 0, 0, 0)
        self.queue_select_all_btn = QPushButton(self._t("package_manager.queue.select_all", "全选"))
        self.queue_select_all_btn.clicked.connect(self._queue_select_all)
        queue_row.addWidget(self.queue_select_all_btn)
        self.queue_invert_btn = QPushButton(self._t("package_manager.queue.invert", "反选"))
        self.queue_invert_btn.clicked.connect(self._queue_invert_selection)
        queue_row.addWidget(self.queue_invert_btn)
        self.queue_clear_btn = QPushButton(self._t("package_manager.queue.clear", "清空勾选"))
        self.queue_clear_btn.clicked.connect(self._queue_clear_selection)
        queue_row.addWidget(self.queue_clear_btn)
        self.queue_only_checked_cb = QCheckBox(self._t("package_manager.queue.only_checked", "仅显示已勾选"))
        queue_row.addWidget(self.queue_only_checked_cb)
        self.queue_stats_label = QLabel("")
        queue_row.addWidget(self.queue_stats_label)
        queue_row.addStretch(1)
        layout.addWidget(self._queue_bar)

        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(6)
        self._refresh_btn = QPushButton(self._t("package_manager.refresh", "刷新"))
        self._refresh_btn.clicked.connect(self._refresh)
        toolbar_row.addWidget(self._refresh_btn)

        self._enable_btn = QPushButton(self._t("package_manager.enable", "启用"))
        self._enable_btn.clicked.connect(self._enable_selected)
        toolbar_row.addWidget(self._enable_btn)

        self._disable_btn = QPushButton(self._t("package_manager.disable", "禁用"))
        self._disable_btn.clicked.connect(self._disable_selected)
        toolbar_row.addWidget(self._disable_btn)

        self._more_btn = QToolButton()
        self._more_btn.setText(self._t("package_manager.more_actions", "更多操作"))
        self._more_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        more_menu = QMenu(self._more_btn)
        self._more_actions = {}
        self._more_actions["install_selected"] = more_menu.addAction(
            self._t("package_manager.install_selected", "安装选中包"),
            self._install_selected_package,
        )
        self._more_actions["uninstall_selected"] = more_menu.addAction(
            self._t("package_manager.uninstall_selected", "卸载选中包"),
            self._uninstall_selected_package,
        )
        more_menu.addSeparator()
        self._more_actions["update_selected"] = more_menu.addAction(
            self._t("package_manager.update_selected", "更新选中包"),
            self._update_selected_package,
        )
        self._more_actions["update_all"] = more_menu.addAction(
            self._t("package_manager.update_all", "全部更新"),
            self._update_all_packages,
        )
        self._more_actions["rollback_latest"] = more_menu.addAction(
            self._t("package_manager.rollback_latest", "回滚最近更新"),
            self._rollback_latest_update_plan,
        )
        more_menu.addSeparator()
        self._more_actions["open_plugins_tab"] = more_menu.addAction(
            self._t("package_manager.open_plugins_tab", "切换到「插件」列表"),
            self._switch_to_plugins_tab,
        )
        more_menu.addSeparator()
        self._more_actions["toggle_float"] = more_menu.addAction(
            self._t("package_manager.toggle_float", "切换浮动/停靠"),
            self._toggle_dock_floating,
        )
        self._float_open_action = QAction(
            self._t("package_manager.default_float_open", "默认浮动打开"), self._more_btn
        )
        self._float_open_action.setCheckable(True)
        self._float_open_action.setChecked(self._get_package_manager_open_mode() == "floating")
        self._float_open_action.triggered.connect(self._on_float_open_action)
        more_menu.addAction(self._float_open_action)
        self._more_btn.setMenu(more_menu)
        toolbar_row.addWidget(self._more_btn)

        toolbar_row.addStretch(1)
        self._package_count_label = QLabel("")
        toolbar_row.addWidget(self._package_count_label)
        layout.addLayout(toolbar_row)

        self._plugin_runtime_bar = QWidget()
        runtime_row = QHBoxLayout(self._plugin_runtime_bar)
        runtime_row.setContentsMargins(0, 0, 0, 0)
        runtime_row.setSpacing(6)
        self._reload_btn = QPushButton(self._t("plugin_manager.reload", "重载"))
        self._reload_btn.setToolTip(self._t("plugin_manager.reload_tip", "重载选中的插件"))
        self._reload_btn.clicked.connect(self.reload_selected_plugin)
        runtime_row.addWidget(self._reload_btn)
        self._unload_btn = QPushButton(self._t("plugin_manager.unload", "卸载"))
        self._unload_btn.setToolTip(self._t("plugin_manager.unload_tip", "卸载选中的插件"))
        self._unload_btn.clicked.connect(self.unload_selected_plugin)
        runtime_row.addWidget(self._unload_btn)
        self._project_disable_btn = QPushButton(
            self._t("plugin_manager.disable_project", "项目禁用")
        )
        self._project_disable_btn.setToolTip(
            self._t(
                "plugin_manager.disable_project_tip",
                "在当前项目中禁用该插件（持久化）",
            )
        )
        self._project_disable_btn.clicked.connect(self.disable_plugin_in_project)
        runtime_row.addWidget(self._project_disable_btn)
        self._project_enable_btn = QPushButton(
            self._t("plugin_manager.enable_project", "项目启用")
        )
        self._project_enable_btn.setToolTip(
            self._t(
                "plugin_manager.enable_project_tip",
                "在当前项目中启用该插件（持久化）",
            )
        )
        self._project_enable_btn.clicked.connect(self.enable_plugin_in_project)
        runtime_row.addWidget(self._project_enable_btn)
        runtime_row.addStretch(1)
        layout.addWidget(self._plugin_runtime_bar)

        # 与菜单复选同步；不占用工具栏空间
        self.open_mode_toggle_cb = QCheckBox()
        self.open_mode_toggle_cb.setVisible(False)
        self.open_mode_toggle_cb.setChecked(self._get_package_manager_open_mode() == "floating")
        self.open_mode_toggle_cb.stateChanged.connect(self._on_open_mode_toggle_changed)
        layout.addWidget(self.open_mode_toggle_cb)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.package_list = QListWidget()
        self.package_list.setObjectName("packageManagerList")
        self.package_list.setMinimumWidth(240)
        splitter.addWidget(self.package_list)
        splitter.setStretchFactor(0, 2)

        self.detail_text = QTextEdit()
        self.detail_text.setObjectName("packageManagerDetail")
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumWidth(320)
        self.detail_text.setPlaceholderText(self._t("package_manager.placeholder", "选择一个包以查看详情"))
        splitter.addWidget(self.detail_text)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 420])

        layout.addWidget(splitter, 1)

        self.result_text = QTextEdit()
        self.result_text.setObjectName("packageManagerResult")
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(56)
        self.result_text.setPlaceholderText(self._t("package_manager.result.placeholder", "操作结果将显示在这里..."))
        layout.addWidget(self.result_text)

        self._connect_ui_signals()
        self._update_float_toggle_btn_text()
        self._set_queue_buttons_enabled()
        return root

    def show(self):
        # Unity 风格：本质仍是 dock，但默认以浮动窗口形态出现，可随时拖回主 UI。
        if self.dock:
            if not self._ensure_ui_refs():
                logger.warning(
                    "Package Manager Dock content references are unavailable; "
                    "the declarative Host surface will not be re-registered"
                )
                return None
            open_mode = self._get_package_manager_open_mode()
            lm = getattr(self.kernel, "layout_manager", None) if self.kernel else None
            if lm and hasattr(lm, "show_dock_with_mode"):
                lm.show_dock_with_mode(self.DOCK_ID, open_mode == "floating")
                self._sync_hex_from_dock_for_fallback()
                self._ensure_floating_dock_size()
            else:
                if open_mode == "floating":
                    self.dock.setFloating(True)
                    self._restore_dock_floating_geometry()
                    self._ensure_floating_dock_size()
                else:
                    self._capture_dock_floating_geometry()
                    self.dock.setFloating(False)
                self.dock.setVisible(True)
                self.dock.show()
                self.dock.raise_()
            self._refresh()
            self._on_selection_changed()
            self._update_float_toggle_btn_text()
            if self.open_mode_toggle_cb:
                self.open_mode_toggle_cb.setChecked(open_mode == "floating")
            return "dock"

        # 兜底：极端情况下 layout manager 不可用时，仍回退到独立对话框。
        if not self.window:
            parent = self.kernel if isinstance(self.kernel, QWidget) else None
            self.window = QDialog(parent)
            self.window.setWindowTitle(self._t("plugin_manager.title", "项目插件"))
            self.window.resize(1100, 760)
            root = self._build_main_widget(self.window)
            window_layout = QVBoxLayout(self.window)
            window_layout.setContentsMargins(0, 0, 0, 0)
            window_layout.addWidget(root)

        self._refresh()
        self.window.setWindowTitle(self._t("plugin_manager.title", "项目插件"))
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        return "dialog"

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _current_language(self) -> str:
        fn = getattr(self.context, "i18n_get_language", None)
        if callable(fn):
            try:
                return str(fn() or "zh_CN")
            except Exception:
                __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        return "zh_CN"

    def _package_display_name(self, pkg: Dict[str, Any]) -> str:
        pkg_id = str(pkg.get("id", "") or "")
        if self._current_language().startswith("zh"):
            zh = str(pkg.get("display_name_zh", "") or "").strip()
            if zh:
                return zh
        return str(pkg.get("display_name", pkg_id or "Unnamed Package"))

    def _clear_search(self) -> None:
        if self.search_input:
            self.search_input.clear()

    def _switch_to_plugins_tab(self) -> None:
        if self.tab_bar:
            self.tab_bar.setCurrentIndex(1)
        self._refresh()

    def _on_tab_changed(self, idx: int) -> None:
        """社区/更新页与「已启用」筛选易误配为空，自动放宽状态筛选并提示。"""
        if self.tab_bar and idx == 1 and self.status_filter:
            self.status_filter.blockSignals(True)
            self.status_filter.setCurrentIndex(0)
            self.status_filter.blockSignals(False)
        if self.status_filter and idx in (3, 4) and self.status_filter.currentIndex() != 0:
            self.status_filter.blockSignals(True)
            self.status_filter.setCurrentIndex(0)
            self.status_filter.blockSignals(False)
            hint_key = (
                "package_manager.hint.community_reset_filter"
                if idx == 3
                else "package_manager.hint.updates_reset_filter"
            )
            default = (
                "已切换到「社区」：状态筛选已重置为「全部状态」。"
                if idx == 3
                else "已切换到「更新」：状态筛选已重置为「全部状态」。"
            )
            self._append_result(self._t(hint_key, default))
        self._refresh()

    def _restore_list_selection(self, prev_pkg_id: Optional[str]) -> None:
        if not self._ensure_ui_refs() or self.package_list.count() == 0:
            return
        if prev_pkg_id:
            for row in range(self.package_list.count()):
                item = self.package_list.item(row)
                if item and str(item.data(Qt.ItemDataRole.UserRole) or "") == prev_pkg_id:
                    self.package_list.setCurrentRow(row)
                    return
        self.package_list.setCurrentRow(0)

    def _on_float_open_action(self, checked: bool) -> None:
        if self.open_mode_toggle_cb:
            self.open_mode_toggle_cb.blockSignals(True)
            self.open_mode_toggle_cb.setChecked(checked)
            self.open_mode_toggle_cb.blockSignals(False)
        self._on_open_mode_toggle_changed()

    def _get_repo_root(self) -> str:
        from core.VitaLoom.core.bundle_paths import resource_root

        ctx = getattr(self, "context", None)
        if ctx is not None:
            repo = getattr(ctx, "repo_root", None)
            if isinstance(repo, str) and repo.strip():
                return os.path.abspath(repo)
        return str(resource_root())

    def _get_registry_config_path(self) -> str:
        from core.VitaLoom.core.bundle_paths import is_frozen_bundle, system_config_dir

        if is_frozen_bundle():
            return str(system_config_dir() / "package_registries.json")
        repo_root = self._get_repo_root()
        return os.path.join(repo_root, "data", "system", "package_registries.json")

    def _get_policy_config_path(self) -> str:
        from core.VitaLoom.core.bundle_paths import is_frozen_bundle, system_config_dir

        if is_frozen_bundle():
            return str(system_config_dir() / "package_policy.json")
        repo_root = self._get_repo_root()
        return os.path.join(repo_root, "data", "system", "package_policy.json")

    def _get_enable_constraint_mode(self) -> str:
        """包启用约束模式：
        - warn: 发现依赖/冲突问题仅警告，不阻止启用（默认）
        - block: 发现问题则阻止启用
        """
        try:
            path = self._get_policy_config_path()
            if not os.path.exists(path):
                return "warn"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mode = str(data.get("enable_constraint_mode", "warn")).strip().lower()
            return mode if mode in ("warn", "block") else "warn"
        except Exception:
            return "warn"

    def _on_open_mode_toggle_changed(self, _state: int = 0) -> None:
        checked = bool(self.open_mode_toggle_cb and self.open_mode_toggle_cb.isChecked())
        if self._float_open_action and self._float_open_action.isChecked() != checked:
            self._float_open_action.blockSignals(True)
            self._float_open_action.setChecked(checked)
            self._float_open_action.blockSignals(False)
        mode = "floating" if checked else "docked"
        try:
            path = self._get_policy_config_path()
            data: Dict[str, Any] = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
            data["package_manager_open_mode"] = mode
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("保存包管理器打开模式失败: %s", exc)

    def _get_package_manager_open_mode(self) -> str:
        """包管理器打开形态：
        - floating: 默认以浮动 dock 打开（类独立窗口）
        - docked: 默认以停靠形态打开
        """
        try:
            path = self._get_policy_config_path()
            if not os.path.exists(path):
                return "floating"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mode = str(data.get("package_manager_open_mode", "floating")).strip().lower()
            return mode if mode in ("floating", "docked") else "floating"
        except Exception:
            return "floating"

    def _load_registry_config(self) -> List[Dict[str, Any]]:
        try:
            path = self._get_registry_config_path()
            if not os.path.exists(path):
                return [{"name": "builtin", "type": "file", "path": "builtin/package_index.json"}]
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            registries = data.get("registries", [])
            return registries if isinstance(registries, list) else []
        except Exception:
            return [{"name": "builtin", "type": "file", "path": "builtin/package_index.json"}]

    def _load_index_from_file(self, path: str) -> List[Dict[str, Any]]:
        repo_root = self._get_repo_root()
        abs_path = path if os.path.isabs(path) else os.path.join(repo_root, path)
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        packages = data.get("packages", [])
        return packages if isinstance(packages, list) else []

    def _load_index_from_url(self, url: str) -> List[Dict[str, Any]]:
        # 优先使用官方 Downloader 服务（插件层基础设施），避免每个插件各自实现下载逻辑
        services = getattr(self.context, "services", None)
        downloader = services.get(DOWNLOADER) if services and hasattr(services, "get") else None
        if downloader and hasattr(downloader, "fetch_json"):
            data, err = downloader.fetch_json(url, timeout_s=8)
            if err:
                raise RuntimeError(err)
        else:
            # 兜底：无下载服务时仍可工作（不影响内核最小职责）
            import urllib.request

            with urllib.request.urlopen(url, timeout=8) as resp:  # nosec - url comes from user registry config
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
        packages = data.get("packages", [])
        return packages if isinstance(packages, list) else []

    @staticmethod
    def _normalize_package(pkg: Dict[str, Any], source: str) -> Dict[str, Any]:
        return normalize_package(pkg, source)

    @staticmethod
    def merge_package_lists(package_lists: List[List[Dict[str, Any]]], priority_sources: List[str]) -> List[Dict[str, Any]]:
        return merge_package_lists(package_lists, priority_sources)

    @staticmethod
    def _parse_version(version: str) -> tuple[int, int, int]:
        return parse_version(version)

    @classmethod
    def _version_gte(cls, actual: str, expected_min: str) -> bool:
        return version_gte(actual, expected_min)

    @classmethod
    def _parse_dependency_expr(cls, expr: str) -> tuple[str, str, str]:
        return parse_dependency_expr(expr)

    @staticmethod
    def should_block_enable(enable_constraint_mode: str, has_dependency_or_conflict_issue: bool) -> bool:
        return should_block_enable(enable_constraint_mode, has_dependency_or_conflict_issue)

    def _get_package_by_id(self, package_id: str) -> Optional[Dict[str, Any]]:
        for p in self._packages:
            if str(p.get("id", "")) == str(package_id):
                return p
        return None

    def _evaluate_dependency_status(self, pkg: Dict[str, Any]) -> List[str]:
        deps = pkg.get("dependencies", [])
        if not isinstance(deps, list):
            return []

        enabled_ids = self._enabled_package_ids()
        lines: List[str] = []
        for dep_expr in deps:
            dep_text = str(dep_expr)
            dep_id, op, ver = self._parse_dependency_expr(dep_text)
            dep_pkg = self._get_package_by_id(dep_id)
            if dep_pkg is None:
                lines.append(self._t("package_manager.dependency.missing", "MISSING: {dep}").format(dep=dep_text))
                continue
            if dep_id not in enabled_ids:
                lines.append(self._t("package_manager.dependency.disabled", "DISABLED: {dep}").format(dep=dep_text))
                continue

            dep_ver = str(dep_pkg.get("version", "0.0.0"))
            if op == ">=":
                ok = self._version_gte(dep_ver, ver)
                key = "package_manager.dependency.ok" if ok else "package_manager.dependency.incompatible"
                lines.append(self._t(key, "OK: {dep}").format(dep=f"{dep_id}({dep_ver}) requires >= {ver}"))
            else:
                lines.append(self._t("package_manager.dependency.ok", "OK: {dep}").format(dep=f"{dep_id}({dep_ver})"))
        return lines

    def _enabled_package_ids(self) -> set[str]:
        disabled = self._get_project_disabled_plugins()
        disabled_set = set(disabled or [])
        enabled: set[str] = set()
        for pkg in self._packages:
            pkg_id = str(pkg.get("id", ""))
            if not pkg_id:
                continue
            plugins = pkg.get("plugins", [])
            if not isinstance(plugins, list):
                plugins = []
            if any(str(p) not in disabled_set for p in plugins):
                enabled.add(pkg_id)
                continue
            if self._is_implicitly_enabled_package(pkg):
                enabled.add(pkg_id)
        return enabled

    @staticmethod
    def _is_implicitly_enabled_package(pkg: Dict[str, Any]) -> bool:
        """无 plugins 字段的能力包 / 核心包在列表中视为已安装（避免「已启用」筛选为空）。"""
        status = str(pkg.get("status", "")).lower()
        category = str(pkg.get("category", "")).lower()
        plugins = pkg.get("plugins", [])
        if isinstance(plugins, list) and plugins:
            return False
        if status == "planned":
            return False
        if status == "required" or category == "core":
            return True
        if category == "official" and status in ("default", "optional"):
            return True
        return False

    def _evaluate_conflict_status(self, pkg: Dict[str, Any]) -> List[str]:
        conflicts = pkg.get("conflicts", [])
        if not isinstance(conflicts, list):
            return []
        enabled_ids = self._enabled_package_ids()
        lines: List[str] = []
        for cid in conflicts:
            cid_text = str(cid)
            if cid_text in enabled_ids:
                lines.append(self._t("package_manager.conflict.hit", "CONFLICT: {pkg}").format(pkg=cid_text))
            else:
                lines.append(self._t("package_manager.conflict.clear", "CLEAR: {pkg}").format(pkg=cid_text))
        return lines

    def _load_all_packages(self) -> List[Dict[str, Any]]:
        if not self.catalog_service or not self.operation_service:
            return []
        services = getattr(self.context, "services", None)
        downloader = None
        if services and hasattr(services, "get"):
            cand = services.get(DOWNLOADER)
            if cand is not None and hasattr(cand, "fetch_json"):
                downloader = cand
        overrides = self.operation_service.get_version_overrides()
        merged, updates, errors = self.catalog_service.load_all_packages(overrides, downloader=downloader)
        try:
            project_path = self.operation_service.project_world_read_model.current_project_world_path()
            merged = self.catalog_service.annotate_project_lock_status(merged, project_path)
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        self._update_candidates = updates
        if errors:
            msg = self._t(
                "package_manager.registry_partial_failed",
                "部分包源加载失败（已忽略）：\n{errors}",
            ).format(errors="\n".join(errors))
            logger.warning(msg.replace("\n", " | "))
            if self.kernel and isinstance(self.kernel, QWidget):
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "警告"),
                    msg,
                )
        return merged

    @staticmethod
    def _collect_update_candidates(
        loaded_lists: List[List[Dict[str, Any]]],
        merged: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        return collect_update_candidates(loaded_lists, merged)

    def _refresh(self):
        # 在刷新前记录 updates 页签中的勾选状态，便于刷新后保留队列
        prev_pkg_id: Optional[str] = None
        if self.package_list and self.package_list.currentItem():
            prev_pkg_id = str(self.package_list.currentItem().data(Qt.ItemDataRole.UserRole) or "") or None
        tab_filter = self._get_tab_filter()
        if tab_filter == "updates":
            self._checked_update_ids = self._get_checked_update_ids()
        self._packages = self._load_all_packages()
        if not self._ensure_ui_refs():
            return
        self._set_queue_buttons_enabled()
        self.package_list.clear()
        if tab_filter == "plugins":
            self._populate_plugin_list_tab()
            visible = self.package_list.count()
            self._update_package_count_label(visible, len(self._collect_catalog_plugins()))
            if visible == 0:
                self._render_empty_list_hint(
                    tab_filter="plugins",
                    status_filter=self._get_status_filter(),
                    keyword=(self.search_input.text() if self.search_input else "").strip().lower(),
                    total_loaded=len(self._collect_catalog_plugins()),
                )
            else:
                self._restore_list_selection(prev_pkg_id)
            return
        keyword = (self.search_input.text() if self.search_input else "") or ""
        keyword = keyword.strip().lower()

        disabled = self._get_project_disabled_plugins()
        disabled_set = set(disabled or [])
        status_filter = self._get_status_filter()
        source_filter = self._get_source_filter()
        only_checked = bool(self.queue_only_checked_cb and self.queue_only_checked_cb.isChecked() and tab_filter == "updates")

        visible_entries: List[tuple[int, str, str, Dict[str, Any], int, int, bool, str]] = []
        for pkg in self._packages:
            pkg_id = str(pkg.get("id", ""))
            name = self._package_display_name(pkg)
            category = str(pkg.get("category", ""))
            source = str(pkg.get("source", ""))
            version = str(pkg.get("version", ""))
            plugins = pkg.get("plugins", [])
            if not isinstance(plugins, list):
                plugins = []
            enabled_count = sum(1 for p in plugins if str(p) not in disabled_set)
            total_count = len(plugins)
            has_issues = self._package_has_issues(pkg)
            is_enabled = enabled_count > 0 or self._is_implicitly_enabled_package(pkg)

            if not self._matches_tab_filter(pkg, tab_filter):
                continue
            if not self._matches_status_filter(is_enabled, has_issues, status_filter, pkg):
                continue
            if source_filter != "all" and source.lower() != source_filter:
                continue

            if keyword:
                hay = (
                    f"{name}\n{pkg_id}\n{category}\n{source}\n"
                    f"{pkg.get('display_name', '')}\n{pkg.get('display_name_zh', '')}"
                ).lower()
                if keyword not in hay:
                    continue
            if only_checked and pkg_id not in self._checked_update_ids:
                continue
            sort_key = (0 if is_enabled else 1, name.lower(), pkg_id.lower())
            visible_entries.append((sort_key[0], sort_key[1], sort_key[2], pkg, enabled_count, total_count, is_enabled, version))

        visible_entries.sort(key=lambda row: (row[0], row[1], row[2]))
        for _, _, _, pkg, enabled_count, total_count, _is_enabled, version in visible_entries:
            pkg_id = str(pkg.get("id", ""))
            name = self._package_display_name(pkg)
            source = str(pkg.get("source", ""))
            label = self._t("package_manager.list_item", "{name}  ({enabled}/{total})  [{source}]").format(
                name=name, enabled=enabled_count, total=total_count, source=source
            )
            if version:
                label = f"{label}  v{version}"
            latest = self._update_candidates.get(pkg_id, "")
            if latest:
                label = f"{label}  {self._t('package_manager.update.available', '-> latest {version}').format(version=latest)}"
            project_lock_label = self._project_lock_label(pkg)
            if project_lock_label:
                label = f"{label}  [{project_lock_label}]"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, pkg_id)
            if tab_filter == "updates":
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if pkg_id in self._checked_update_ids else Qt.CheckState.Unchecked)
            self.package_list.addItem(item)
        visible = self.package_list.count()
        total_loaded = len(self._packages)
        self._update_package_count_label(visible, total_loaded)
        if visible == 0:
            self._render_empty_list_hint(
                tab_filter=tab_filter,
                status_filter=status_filter,
                keyword=keyword,
                total_loaded=total_loaded,
            )
        else:
            self._restore_list_selection(prev_pkg_id)
        self._update_queue_stats_label()

    def _get_checked_update_ids(self) -> set[str]:
        if not self._ensure_ui_refs():
            return set()
        checked: set[str] = set()
        for i in range(self.package_list.count()):
            item = self.package_list.item(i)
            if not item:
                continue
            pkg_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
            if pkg_id and item.checkState() == Qt.CheckState.Checked:
                checked.add(pkg_id)
        return checked

    def _set_queue_buttons_enabled(self):
        tab = self._get_tab_filter()
        is_updates_tab = tab == "updates"
        is_plugins_tab = tab == "plugins"
        queue_bar = getattr(self, "_queue_bar", None)
        if queue_bar:
            queue_bar.setVisible(is_updates_tab)
        for btn in [self.queue_select_all_btn, self.queue_invert_btn, self.queue_clear_btn, self.queue_only_checked_cb]:
            if btn:
                btn.setEnabled(is_updates_tab and not is_plugins_tab)
        source_filter = getattr(self, "source_filter", None)
        if is_plugins_tab and source_filter:
            source_filter.setEnabled(False)
        elif source_filter:
            source_filter.setEnabled(True)
        runtime_bar = getattr(self, "_plugin_runtime_bar", None)
        if runtime_bar:
            runtime_bar.setVisible(is_plugins_tab)
        self._update_queue_stats_label()

    def _update_queue_stats_label(self):
        if not self.queue_stats_label:
            return
        updates_count = len(self._update_candidates)
        checked_count = len(self._checked_update_ids)
        self.queue_stats_label.setText(
            self._t("package_manager.queue.stats", "队列: {checked}/{updates}").format(
                checked=checked_count, updates=updates_count
            )
        )

    def _queue_select_all(self):
        if self._get_tab_filter() != "updates" or not self.package_list:
            return
        for i in range(self.package_list.count()):
            item = self.package_list.item(i)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self._checked_update_ids = self._get_checked_update_ids()
        self._update_queue_stats_label()

    def _queue_invert_selection(self):
        if self._get_tab_filter() != "updates" or not self.package_list:
            return
        for i in range(self.package_list.count()):
            item = self.package_list.item(i)
            if not item:
                continue
            new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
            item.setCheckState(new_state)
        self._checked_update_ids = self._get_checked_update_ids()
        self._update_queue_stats_label()

    def _queue_clear_selection(self):
        if self._get_tab_filter() != "updates" or not self.package_list:
            return
        for i in range(self.package_list.count()):
            item = self.package_list.item(i)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self._checked_update_ids = set()
        self._update_queue_stats_label()

    def _collect_catalog_plugins(self) -> List[tuple[str, str]]:
        """(plugin_id, package_id) 来自包索引。"""
        rows: List[tuple[str, str]] = []
        seen: set[str] = set()
        for pkg in self._packages:
            pkg_id = str(pkg.get("id", "") or "")
            plugins = pkg.get("plugins", [])
            if not isinstance(plugins, list):
                continue
            for p in plugins:
                pid = str(p)
                if pid and pid not in seen:
                    seen.add(pid)
                    rows.append((pid, pkg_id))
        return sorted(rows, key=lambda x: x[0].lower())

    def _populate_plugin_list_tab(self) -> None:
        if not self._ensure_ui_refs():
            return
        disabled_set = set(self._get_project_disabled_plugins() or [])
        snapshot = self._runtime_plugin_observation()
        loaded = self._runtime_active_plugin_ids(snapshot)
        keyword = (self.search_input.text() if self.search_input else "").strip().lower()
        status_filter = self._get_status_filter()

        for plugin_id, pkg_id in self._collect_catalog_plugins():
            in_memory = loaded is not None and plugin_id in loaded
            project_enabled = plugin_id not in disabled_set
            if status_filter == "enabled" and not (in_memory and project_enabled):
                continue
            if status_filter == "disabled" and project_enabled:
                continue
            pkg = self._get_package_by_id(pkg_id)
            pkg_name = self._package_display_name(pkg) if pkg else pkg_id
            if keyword:
                hay = f"{plugin_id}\n{pkg_id}\n{pkg_name}".lower()
                if keyword not in hay:
                    continue
            if loaded is None:
                mem = self._t("package_manager.plugin.unknown", "\u672a\u77e5")
            elif in_memory:
                mem = self._t("package_manager.plugin.loaded", "已加载")
            else:
                mem = self._t("package_manager.plugin.not_loaded", "未加载")
            proj = self._t("package_manager.plugin.project_on", "项目启用") if project_enabled else self._t(
                "package_manager.plugin.project_off", "项目禁用"
            )
            label = self._t(
                "package_manager.plugin.list_item",
                "{plugin}  ·  {package}  [{mem}] [{proj}]",
            ).format(plugin=plugin_id, package=pkg_name, mem=mem, proj=proj)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, f"{self._PLUGIN_ITEM_PREFIX}{plugin_id}")
            self.package_list.addItem(item)

    def _get_tab_filter(self) -> str:
        if not self.tab_bar:
            return "installed"
        idx = self.tab_bar.currentIndex()
        if idx == 1:
            return "plugins"
        if idx == 2:
            return "core"
        if idx == 3:
            return "official"
        if idx == 4:
            return "resources"
        if idx == 5:
            return "community"
        if idx == 6:
            return "updates"
        return "installed"

    def _get_status_filter(self) -> str:
        if not self.status_filter:
            return "all"
        idx = self.status_filter.currentIndex()
        if idx == 1:
            return "enabled"
        if idx == 2:
            return "disabled"
        if idx == 3:
            return "issues"
        return "all"

    def _get_source_filter(self) -> str:
        if not self.source_filter:
            return "all"
        data = self.source_filter.currentData()
        if data is not None:
            return str(data)
        text = self.source_filter.currentText().strip().lower()
        if text in {"builtin", "file", "url"}:
            return text
        return "all"

    def _matches_tab_filter(self, pkg: Dict[str, Any], tab_filter: str) -> bool:
        pkg_id = str(pkg.get("id", "") or "")
        source = str(pkg.get("source", "")).lower()
        category = str(pkg.get("category", "")).lower()
        origin = str(pkg.get("origin", "") or category or source).lower()
        if tab_filter == "plugins":
            return False
        if tab_filter == "core":
            return origin == "core" or category == "core"
        if tab_filter == "resources":
            role = str(pkg.get("role", "") or "").lower()
            resources = pkg.get("resources", [])
            if role == "resource":
                return True
            if isinstance(resources, list) and len(resources) > 0:
                return True
            return False
        if tab_filter == "official":
            if origin == "core" or category == "core":
                return False
            if origin == "official" or category == "official":
                return True
            if "builtin" in source or source in {"core", "core+builtin", "builtin"}:
                return True
            return False
        if tab_filter == "community":
            return source in {"url", "file"} and category != "official"
        if tab_filter == "updates":
            return pkg_id in self._update_candidates
        return True

    @staticmethod
    def _matches_status_filter(
        is_enabled: bool, has_issues: bool, status_filter: str, pkg: Optional[Dict[str, Any]] = None
    ) -> bool:
        implicitly_enabled = bool(pkg and PackageManagerPlugin._is_implicitly_enabled_package(pkg))
        return matches_status_filter(
            is_enabled, has_issues, status_filter, implicitly_enabled=implicitly_enabled
        )

    def _project_lock_label(self, pkg: Dict[str, Any]) -> str:
        status = str(pkg.get("project_lock_status", "") or "")
        if status == "locked":
            return self._t("package_manager.project_lock.locked", "项目已锁")
        if status == "suggested":
            return self._t("package_manager.project_lock.suggested", "建议锁定")
        if status == "missing":
            return self._t("package_manager.project_lock.missing", "能力缺失")
        if status == "stale":
            return self._t("package_manager.project_lock.stale", "版本不符")
        if status == "unresolved":
            return self._t("package_manager.project_lock.unresolved", "未解析")
        return ""

    @staticmethod
    def _select_target_updates(update_candidates: Dict[str, str], checked_ids: set[str]) -> Dict[str, str]:
        return select_target_updates(update_candidates, checked_ids)

    def _package_has_issues(self, pkg: Dict[str, Any]) -> bool:
        if str(pkg.get("project_lock_status", "") or "") in {"missing", "stale", "unresolved"}:
            return True
        dep_status = self._evaluate_dependency_status(pkg)
        conflict_status = self._evaluate_conflict_status(pkg)
        for line in dep_status + conflict_status:
            upper = line.upper()
            if "MISSING:" in upper or "INCOMPATIBLE:" in upper or "DISABLED:" in upper or "CONFLICT:" in upper:
                return True
        return False

    def _get_selected_list_key(self) -> Optional[str]:
        if not self.package_list:
            return None
        item = self.package_list.currentItem()
        if not item:
            return None
        return str(item.data(Qt.ItemDataRole.UserRole) or "")

    def _get_selected_plugin_id(self) -> Optional[str]:
        key = self._get_selected_list_key()
        if key and key.startswith(self._PLUGIN_ITEM_PREFIX):
            return key[len(self._PLUGIN_ITEM_PREFIX) :]
        return None

    def _get_selected_package(self) -> Optional[Dict[str, Any]]:
        key = self._get_selected_list_key()
        if not key or key.startswith(self._PLUGIN_ITEM_PREFIX):
            return None
        for pkg in self._packages:
            if str(pkg.get("id", "")) == str(key):
                return pkg
        return None

    def _package_for_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        for pkg in self._packages:
            plugins = pkg.get("plugins", [])
            if isinstance(plugins, list) and plugin_id in [str(p) for p in plugins]:
                return pkg
        return None

    def _get_project_disabled_plugins(self) -> Optional[List[str]]:
        if not self.operation_service:
            return None
        return self.operation_service.get_disabled_plugins()

    def _get_project_version_overrides(self) -> Dict[str, str]:
        if not self.operation_service:
            return {}
        return self.operation_service.get_version_overrides()

    def _apply_project_version_overrides(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        overrides = self._get_project_version_overrides()
        if not overrides:
            return packages
        out: List[Dict[str, Any]] = []
        for pkg in packages:
            pkg_id = str(pkg.get("id", "") or "")
            if pkg_id and pkg_id in overrides:
                p = dict(pkg)
                p["version"] = overrides[pkg_id]
                out.append(p)
            else:
                out.append(pkg)
        return out

    def _get_current_project_path(self) -> str:
        try:
            path = get_project_world_read_model(
                self.context
            ).current_project_world_path()
            return str(path or "")
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
            return ""

    def _run_project_plugin_command(
        self,
        command_id: str,
        plugin_id: str,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        project_path = self._get_current_project_path()
        if not project_path:
            return {
                "ok": False,
                "error": {
                    "code": "project_not_open",
                    "message": "No project is open",
                    "details": {},
                },
            }
        payload: Dict[str, Any] = {"project_path": project_path, "plugin_id": str(plugin_id)}
        if extra_payload:
            payload.update(extra_payload)
        from core.VitaLoom.commands.registry import get_command_registry

        return get_command_registry().run(command_id, payload)

    def _handle_project_plugin_command_result(self, result: Dict[str, Any]) -> bool:
        if result.get("ok"):
            return True
        error = result.get("error") if isinstance(result.get("error"), dict) else {}
        code = str(error.get("code", "unknown_error"))
        message = str(error.get("message", code))
        if getattr(self, "result_text", None):
            self._append_result(
                self._t("package_manager.command_failed", "项目插件命令失败：{error}").format(
                    error=message
                )
            )
        if self.kernel:
            QMessageBox.warning(
                self.kernel,
                self._t("dialog.warning.title", "警告"),
                self._t("package_manager.command_failed", "项目插件命令失败：{error}").format(
                    error=message
                ),
            )
        return False

    def _write_project_version_override(self, package_id: str, version: str) -> bool:
        if not self.operation_service:
            return False
        overrides = self.operation_service.get_version_overrides()
        overrides[str(package_id)] = str(version)
        return self.operation_service.write_version_overrides(
            overrides,
            action="update_single",
            metadata={"package_id": str(package_id)},
        )

    def _render_plugin_detail(self, plugin_id: str) -> None:
        if not self.detail_text:
            return
        pkg = self._package_for_plugin(plugin_id)
        pkg_label = self._package_display_name(pkg) if pkg else "—"
        disabled_set = set(self._get_project_disabled_plugins() or [])
        project_on = plugin_id not in disabled_set
        snapshot = self._runtime_plugin_observation()
        loaded_ids = self._runtime_active_plugin_ids(snapshot)
        loaded = loaded_ids is not None and plugin_id in loaded_ids
        memory_label = (
            self._t("package_manager.plugin.unknown", "\u672a\u77e5")
            if loaded_ids is None
            else self._t("package_manager.plugin.loaded", "已加载")
            if loaded
            else self._t("package_manager.plugin.not_loaded", "未加载")
        )
        info_block = ""
        row = self._runtime_plugin_row_from_observation(plugin_id, snapshot)
        if row:
            provides = row.get("provides", [])
            if isinstance(provides, (list, tuple, set, frozenset)):
                provides_text = ", ".join(str(item) for item in provides)
            else:
                provides_text = str(provides or "—")
            info_block = (
                f"\n{self._t('plugin_manager.field.version', '版本')}: {row.get('version', '—')}\n"
                f"{self._t('plugin_manager.field.description', '描述')}: {row.get('description', '—')}\n"
                f"{self._t('plugin_manager.field.provides', '提供能力')}: {provides_text}\n"
            )
        self.detail_text.setPlainText(
            f"{plugin_id}\n"
            f"{self._t('package_manager.plugin.detail_package', '所属扩展包')}: {pkg_label}\n"
            f"{self._t('package_manager.plugin.detail_memory', '内存')}: {memory_label}\n"
            f"{self._t('package_manager.plugin.detail_project', '项目')}: "
            f"{self._t('package_manager.plugin.project_on', '项目启用') if project_on else self._t('package_manager.plugin.project_off', '项目禁用')}\n"
            f"{info_block}\n"
            f"{self._t('package_manager.plugin.detail_hint', '项目禁用后需重启编辑器；资源导入请用「项目」面板 Assets。')}"
        )

    def _on_selection_changed(self):
        if not self.detail_text:
            return
        plugin_id = self._get_selected_plugin_id()
        if plugin_id:
            self._render_plugin_detail(plugin_id)
            return
        pkg = self._get_selected_package()
        if not pkg:
            return
        plugins = pkg.get("plugins", [])
        if not isinstance(plugins, list):
            plugins = []

        disabled = self._get_project_disabled_plugins()
        disabled_set = set(disabled or [])
        enabled_count = sum(1 for p in plugins if str(p) not in disabled_set)
        status = self._t("package_manager.status", "状态：{enabled}/{total} 插件已启用").format(
            enabled=enabled_count, total=len(plugins)
        )

        desc = str(pkg.get("description", ""))
        pkg_id = str(pkg.get("id", ""))
        version = str(pkg.get("version", ""))
        category = str(pkg.get("category", ""))
        source = str(pkg.get("source", ""))
        origin = str(pkg.get("origin", "") or category or source)
        role = str(pkg.get("role", "hybrid") or "hybrid")
        artifact = pkg.get("artifact", {})
        has_signature = False
        if isinstance(artifact, dict):
            has_signature = bool(str(artifact.get("signature", "")).strip())
        signature_text = (
            self._t("package_manager.meta.signature_present", "已提供")
            if has_signature
            else self._t("package_manager.meta.signature_missing", "未提供")
        )
        latest = self._update_candidates.get(pkg_id, version)
        project_lock_label = self._project_lock_label(pkg) or "-"
        project_locked_version = str(pkg.get("project_locked_version", "") or "-")
        project_runtime_lock_status = str(pkg.get("project_runtime_lock_status", "") or "-")
        deps = pkg.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []
        dep_status = self._evaluate_dependency_status(pkg)
        conflicts = pkg.get("conflicts", [])
        if not isinstance(conflicts, list):
            conflicts = []
        conflict_status = self._evaluate_conflict_status(pkg)
        plugin_lines = "\n".join([f"- {p}" for p in plugins])
        provides = pkg.get("provides", [])
        if not isinstance(provides, list):
            provides = []
        provide_lines = "\n".join([f"- {p}" for p in provides if p])
        if plugins:
            capability_block = (
                f"{self._t('package_manager.plugins', '包含插件')}:\n{plugin_lines}"
            )
        elif provides:
            capability_block = (
                "内核能力（非编辑器插件，已编入运行时）:\n"
                f"{provide_lines}"
            )
        else:
            capability_block = (
                f"{self._t('package_manager.plugins', '包含插件')}:\n（无）"
            )
        dep_status_lines = "\n".join([f"- {line}" for line in dep_status]) or "-"
        conflict_status_lines = "\n".join([f"- {line}" for line in conflict_status]) or "-"
        mode = self._get_enable_constraint_mode()
        mode_text = self._t("package_manager.policy.warn", "warn（仅警告）")
        if mode == "block":
            mode_text = self._t("package_manager.policy.block", "block（阻止启用）")

        title = self._package_display_name(pkg)
        en_name = str(pkg.get("display_name", "") or "").strip()
        if self._current_language().startswith("zh") and en_name and en_name != title:
            title = f"{title}\n({en_name})"

        self.detail_text.setPlainText(
            f"{title}\n"
            f"{self._t('package_manager.meta.id', 'ID')}: {pkg_id}\n"
            f"{self._t('package_manager.meta.version', '版本')}: {version}\n"
            f"{self._t('package_manager.meta.latest_version', '最新版本')}: {latest}\n"
            f"{self._t('package_manager.meta.project_lock_status', '项目能力状态')}: {project_lock_label}\n"
            f"{self._t('package_manager.meta.project_locked_version', '项目锁定版本')}: {project_locked_version}\n"
            f"{self._t('package_manager.meta.project_runtime_lock_status', '项目 lock 状态')}: {project_runtime_lock_status}\n"
            f"{self._t('package_manager.meta.category', '分类')}: {category}\n"
            f"{self._t('package_manager.meta.origin', '来源轴 origin')}: {origin}\n"
            f"{self._t('package_manager.meta.role', '角色 role')}: {role}\n"
            f"{self._t('package_manager.meta.source', '来源')}: {source}\n"
            f"{self._t('package_manager.meta.signature', '签名')}: {signature_text}\n"
            f"{self._t('package_manager.meta.signature_policy', '签名规则')}: {self._t('package_manager.meta.signature_policy_value', '仅安装时验证；失败只警告不阻断')}\n"
            f"{self._t('package_manager.meta.update_source', '更新来源')}: {source}\n"
            f"{self._t('package_manager.meta.dependencies', '依赖')}: {', '.join([str(d) for d in deps]) or '-'}\n"
            f"{self._t('package_manager.meta.dependency_status', '依赖状态')}:\n{dep_status_lines}\n"
            f"{self._t('package_manager.meta.conflicts', '冲突包')}: {', '.join([str(c) for c in conflicts]) or '-'}\n"
            f"{self._t('package_manager.meta.conflict_status', '冲突状态')}:\n{conflict_status_lines}\n"
            f"{self._t('package_manager.policy.mode', '约束模式')}: {mode_text}\n"
            f"{status}\n\n"
            f"{desc}\n\n"
            f"{capability_block}"
        )

    def _set_project_plugin_enabled(self, plugin_id: str, enabled: bool) -> bool:
        command_id = "plugin.enable" if enabled else "plugin.disable"
        result = self._run_project_plugin_command(command_id, plugin_id)
        ok = self._handle_project_plugin_command_result(result)
        if ok:
            self._refresh()
            self._on_selection_changed()
        return ok

    def _enable_selected(self):
        plugin_id = self._get_selected_plugin_id()
        if plugin_id:
            if self._set_project_plugin_enabled(plugin_id, True):
                self._append_result(
                    self._t(
                        "package_manager.plugin.enabled",
                        "已在项目中启用插件：{name}（重启后若仍未加载请检查依赖包）",
                    ).format(name=plugin_id)
                )
            return
        pkg = self._get_selected_package()
        if not pkg:
            return
        mode = self._get_enable_constraint_mode()
        deps = pkg.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []
        bad: List[str] = []
        enabled_ids = self._enabled_package_ids()
        for dep_expr in deps:
            dep_text = str(dep_expr)
            dep_id, op, ver = self._parse_dependency_expr(dep_text)
            dep_pkg = self._get_package_by_id(dep_id)
            if dep_pkg is None:
                bad.append(dep_text)
                continue
            if dep_id not in enabled_ids:
                bad.append(dep_text)
                continue
            if op == ">=" and not self._version_gte(str(dep_pkg.get("version", "0.0.0")), ver):
                bad.append(dep_text)
        if bad and self.kernel:
            QMessageBox.warning(
                self.kernel,
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "package_manager.enable_dependency_warning",
                    "依赖存在缺失/不兼容，建议先处理后再启用：\n{details}",
                ).format(details="\n".join(bad)),
            )
        if bad:
            if self.should_block_enable(mode, True):
                return
        conflict_bad: List[str] = []
        conflicts = pkg.get("conflicts", [])
        if not isinstance(conflicts, list):
            conflicts = []
        enabled_ids = self._enabled_package_ids()
        for cid in conflicts:
            cid_text = str(cid)
            if cid_text in enabled_ids:
                conflict_bad.append(cid_text)
        if conflict_bad and self.kernel:
            QMessageBox.warning(
                self.kernel,
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "package_manager.enable_conflict_warning",
                    "检测到冲突包已启用，请先处理冲突后再启用：\n{details}",
                ).format(details="\n".join(conflict_bad)),
            )
        if conflict_bad:
            if self.should_block_enable(mode, True):
                return
        pkg_id = str(pkg.get("id", "")).strip()
        if not pkg_id:
            return
        if self._enable_plugins_for_packages([pkg_id]):
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.enabled_hint", "已写入项目配置。已禁用的插件被重新启用后，需要重启编辑器以重新加载。"),
                )
        self._on_selection_changed()

    def _enable_plugins_for_packages(self, pkg_ids: list[str]) -> bool:
        """Delegate project command ordering to the Qt-free package domain."""
        result = PackageProjectOperations.enable_packages(
            pkg_ids,
            self._run_project_plugin_command,
            command_succeeded=self._handle_project_plugin_command_result,
        )
        return bool(result["changed"])

    def _unload_project_disabled_plugin(self, host: object, plugin_id: str) -> bool:
        """Attempt the one public runtime unload after a persisted project disable."""
        try:
            report = host.unload_plugin(plugin_id)
        except Exception:
            logger.warning(
                "Plugin runtime unload is unavailable after project disable: %s",
                plugin_id,
                exc_info=True,
            )
            return False
        if not isinstance(report, dict) or report.get("status") != "settled":
            logger.warning(
                "Plugin unload did not settle after project disable: %s report=%s",
                plugin_id,
                report,
            )
            return False
        return True

    def _disable_selected(self):
        plugin_id = self._get_selected_plugin_id()
        if plugin_id:
            row = self._runtime_plugin_row(plugin_id)
            if not row:
                logger.warning(
                    "Plugin is absent from the public runtime catalog; project disable denied: %s",
                    plugin_id,
                )
                return
            if row.get("protected"):
                self._append_result(
                    self._t(
                        "package_manager.plugin.protected",
                        "受保护插件不能禁用：{name}",
                    ).format(name=plugin_id)
                )
                return
            host = self._runtime_plugin_host()
            result = self._run_project_plugin_command("plugin.disable", plugin_id)
            if self._handle_project_plugin_command_result(result):
                unload_settled = self._unload_project_disabled_plugin(host, plugin_id)
                feedback_key = (
                    "package_manager.plugin.disabled"
                    if unload_settled
                    else "package_manager.plugin.disabled_runtime_unsettled"
                )
                feedback_default = (
                    "已在项目中禁用插件：{name}"
                    if unload_settled
                    else "已在项目中禁用插件：{name}；当前会话卸载未完成。"
                )
                self._append_result(
                    self._t(feedback_key, feedback_default).format(name=plugin_id)
                )
                self._refresh()
                self._on_selection_changed()
            return
        pkg = self._get_selected_package()
        if not pkg or not self.kernel:
            return
        plugins = pkg.get("plugins", [])
        if not isinstance(plugins, list):
            return

        plugin_ids = [str(plugin_id) for plugin_id in plugins]
        if plugin_ids:
            rows = {
                plugin_id: self._runtime_plugin_row(plugin_id)
                for plugin_id in plugin_ids
            }
            missing_plugin_ids = [
                plugin_id for plugin_id, row in rows.items() if not row
            ]
            if missing_plugin_ids:
                logger.warning(
                    "Package disable denied because plugins are absent from the public runtime catalog: %s",
                    ", ".join(missing_plugin_ids),
                )
                return
            protected = {
                plugin_id for plugin_id, row in rows.items() if row.get("protected")
            }
        else:
            pkg_id = str(pkg.get("id", "")).strip()
            if not pkg_id:
                return
            row = self._runtime_plugin_row(pkg_id)
            if not row:
                logger.warning(
                    "Package disable denied because the package is absent from the public runtime catalog: %s",
                    pkg_id,
                )
                return
            protected = {pkg_id} if row.get("protected") else set()

        host = self._runtime_plugin_host()
        persisted_plugin_ids: list[str] = []
        for plugin_id in plugin_ids:
            if plugin_id in protected:
                continue
            result = self._run_project_plugin_command("plugin.disable", plugin_id)
            if self._handle_project_plugin_command_result(result):
                persisted_plugin_ids.append(plugin_id)
        if not plugin_ids:
            pkg_id = str(pkg.get("id", "")).strip()
            if pkg_id not in protected:
                result = self._run_project_plugin_command("plugin.disable", pkg_id)
                if self._handle_project_plugin_command_result(result):
                    persisted_plugin_ids.append(pkg_id)
        if persisted_plugin_ids:
            unsettled_plugin_ids = [
                plugin_id
                for plugin_id in persisted_plugin_ids
                if not self._unload_project_disabled_plugin(host, plugin_id)
            ]
            if unsettled_plugin_ids:
                self._append_result(
                    self._t(
                        "package_manager.package.disabled_runtime_unsettled",
                        "已写入项目禁用配置，但当前会话卸载未完成：{names}",
                    ).format(names=", ".join(unsettled_plugin_ids))
                )
        self._refresh()
        self._on_selection_changed()
    def _update_selected_package(self):
        pkg = self._get_selected_package()
        if not pkg:
            return
        pkg_id = str(pkg.get("id", "") or "")
        if not pkg_id:
            return
        latest = self._update_candidates.get(pkg_id, "")
        if not latest:
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.no_update_for_selected", "选中包当前已是最新版本。"),
                )
            return
        target_updates = {pkg_id: latest}
        plan = self._confirm_update_plan(target_updates)
        if not plan:
            return
        if self.operation_service:
            ok, _count = self.operation_service.apply_update_plan(plan, action="update_single")
        else:
            ok = self._write_project_version_override(pkg_id, latest)
        if ok:
            self._append_result(self._t("package_manager.result.updated_one", "已更新包：{pkg}").format(pkg=pkg_id))
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t(
                        "package_manager.update_written",
                        "已将 {pkg} 更新到项目版本覆盖：v{version}\n重启后会按新版本策略加载。",
                    ).format(pkg=pkg_id, version=latest),
                )
            self._refresh()
            self._on_selection_changed()

    def _update_all_packages(self):
        target_ids = self._get_checked_update_ids()
        target_updates = self._select_target_updates(self._update_candidates, target_ids)
        if not target_updates:
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.no_updates_available", "当前没有可更新的包。"),
                )
            return
        plan = self._confirm_update_plan(target_updates)
        if not plan:
            return
        if self.operation_service:
            ok, ok_count = self.operation_service.apply_update_plan(plan, action="update_batch")
        else:
            ok = False
            ok_count = 0
        if self.kernel:
            QMessageBox.information(
                self.kernel,
                self._t("dialog.info.title", "提示"),
                self._t(
                    "package_manager.update_queue_written",
                    "已写入 {count} 个包的项目版本覆盖（来自更新队列）。\n重启后会按新版本策略加载。",
                ).format(count=ok_count),
            )
        if ok:
            self._append_result(
                self._t("package_manager.result.updated_batch", "已批量更新 {count} 个包。").format(count=ok_count)
            )
            self._checked_update_ids = set()
            self._update_queue_stats_label()
            self._refresh()
            self._on_selection_changed()

    def _confirm_update_plan(self, target_updates: Dict[str, str]) -> Optional[Dict[str, Any]]:
        if not self.kernel:
            if not self.operation_service:
                return None
            lookup = {str(pkg.get("id", "")): pkg for pkg in self._packages}
            return self.operation_service.create_update_plan(target_updates, lookup)
        if not self.operation_service:
            return None
        lookup = {str(pkg.get("id", "")): pkg for pkg in self._packages}
        plan = self.operation_service.create_update_plan(target_updates, lookup)
        lines: List[str] = []
        for item in plan.get("items", []):
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('id', '')}: v{item.get('current_version', '0.0.0')} -> v{item.get('target_version', '0.0.0')}")
        details = "\n".join(lines) if lines else "-"
        source_counts = plan.get("source_summary", {})
        source_summary = "\n".join([f"- {src}: {count}" for src, count in sorted(source_counts.items())]) or "-"
        content = self._t(
            "package_manager.update_preview_content",
            "将写入以下项目版本覆盖（共 {count} 项）：\n{details}\n\n来源统计：\n{sources}\n\n是否继续？",
        ).format(count=plan.get("count", len(target_updates)), details=details, sources=source_summary)
        while True:
            box = QMessageBox(self.kernel)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(self._t("package_manager.update_preview_title", "更新预览确认"))
            box.setText(content)
            yes_btn = box.addButton(QMessageBox.StandardButton.Yes)
            no_btn = box.addButton(QMessageBox.StandardButton.No)
            export_btn = box.addButton(
                self._t("package_manager.update_preview_export", "导出更新计划"),
                QMessageBox.ButtonRole.ActionRole,
            )
            box.setDefaultButton(no_btn)
            box.exec()
            clicked = box.clickedButton()
            if clicked == yes_btn:
                return plan
            if clicked == export_btn:
                self._export_update_plan(plan)
                continue
            return None

    def _export_update_plan(self, plan: Dict[str, Any]):
        if not self.kernel:
            return
        try:
            if not self.operation_service:
                return
            out_path, err = self.operation_service.export_plan_to_logs(plan)
            if err:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "警告"),
                    self._t("package_manager.update_export_no_project", "当前没有打开项目，无法导出更新计划。"),
                )
                return
            logs_dir = os.path.dirname(str(out_path))
            box = QMessageBox(self.kernel)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle(self._t("dialog.info.title", "提示"))
            box.setText(self._t("package_manager.update_export_ok", "更新计划已导出：\n{path}").format(path=out_path))
            open_btn = box.addButton(
                self._t("package_manager.update_export_open_dir", "打开目录"),
                QMessageBox.ButtonRole.ActionRole,
            )
            ok_btn = box.addButton(QMessageBox.StandardButton.Ok)
            box.setDefaultButton(ok_btn)
            box.exec()
            if box.clickedButton() == open_btn:
                self._open_path_in_explorer(logs_dir)
            self._append_result(self._t("package_manager.result.exported_plan", "已导出更新计划：{path}").format(path=str(out_path)))
        except Exception as e:
            QMessageBox.warning(
                self.kernel,
                self._t("dialog.warning.title", "警告"),
                self._t("package_manager.update_export_failed", "导出更新计划失败：{error}").format(error=str(e)),
            )

    def _open_path_in_explorer(self, path: str):
        try:
            if hasattr(os, "startfile"):
                os.startfile(path)  # type: ignore[attr-defined]
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
                return
            subprocess.Popen(["xdg-open", path])
        except Exception as e:
            if self.kernel:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "警告"),
                    self._t("package_manager.update_export_open_failed", "无法打开目录：{error}").format(error=str(e)),
                )

    def _rollback_latest_update_plan(self):
        if not self.operation_service or not self.kernel:
            return
        ok, result = self.operation_service.rollback_from_latest_export()
        if not ok:
            message = self._t("package_manager.rollback_no_plan", "没有可用的导出更新计划用于回滚。")
            if result not in ("no_plan", "invalid_plan"):
                message = self._t("package_manager.rollback_failed", "回滚失败：{error}").format(error=str(result))
            QMessageBox.warning(self.kernel, self._t("dialog.warning.title", "警告"), message)
            return
        QMessageBox.information(
            self.kernel,
            self._t("dialog.info.title", "提示"),
            self._t("package_manager.rollback_ok", "已按最近更新计划回滚版本覆盖：\n{path}").format(path=result),
        )
        self._append_result(self._t("package_manager.result.rolled_back", "已回滚：{path}").format(path=result))
        self._refresh()
        self._on_selection_changed()

    def _install_selected_package(self):
        pkg = self._get_selected_package()
        if not pkg or not self.operation_service:
            return
        services = getattr(self.context, "services", None)
        downloader = services.get(DOWNLOADER) if services and hasattr(services, "get") else None
        result = PackageProjectOperations.install_package(
            pkg,
            self._packages,
            self._enabled_package_ids(),
            operation_service=self.operation_service,
            run_project_command=self._run_project_plugin_command,
            downloader=downloader,
            mode=self._get_enable_constraint_mode(),
            command_succeeded=self._handle_project_plugin_command_result,
        )
        package_id = str(pkg.get("id", "")).strip()
        operation = result.get("operation", {})
        if operation.get("ok"):
            if not result.get("command_ok"):
                self._append_result(
                    self._t(
                        "package_manager.result.install_record_failed",
                        "Install completed, but the project plugin record failed: {pkg}",
                    ).format(pkg=package_id)
                )
                self._refresh()
                self._on_selection_changed()
                return
            self._append_result(
                self._t("package_manager.result.installed", "Install succeeded: {pkg}").format(
                    pkg=package_id
                )
            )
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "Info"),
                    self._t("package_manager.install_ok", "Install succeeded: {pkg}").format(
                        pkg=package_id
                    ),
                )
        else:
            error = str(operation.get("error", result.get("error", "unknown")))
            self._append_result(
                self._t("package_manager.result.install_failed", "Install failed: {pkg} ({error})").format(
                    pkg=package_id, error=error
                )
            )
            if self.kernel:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "Warning"),
                    self._t("package_manager.install_failed", "Install failed: {pkg}\n{error}").format(
                        pkg=package_id, error=error
                    ),
                )
        self._refresh()
        self._on_selection_changed()

    def _uninstall_selected_package(self):
        pkg = self._get_selected_package()
        if not pkg or not self.operation_service:
            return
        package_id = str(pkg.get("id", "")).strip()
        if not package_id:
            return
        result = PackageProjectOperations.uninstall_package(
            package_id,
            operation_service=self.operation_service,
            run_project_command=self._run_project_plugin_command,
            command_succeeded=self._handle_project_plugin_command_result,
        )
        operation = result.get("operation", {})
        command = result.get("command", {})
        if result.get("ok"):
            self._append_result(
                self._t("package_manager.result.uninstalled", "Uninstall succeeded: {pkg}").format(
                    pkg=package_id
                )
            )
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "Info"),
                    self._t("package_manager.uninstall_ok", "Uninstall succeeded: {pkg}").format(
                        pkg=package_id
                    ),
                )
        else:
            error = command.get("error") or operation.get("error", result.get("error", "unknown"))
            self._append_result(
                self._t("package_manager.result.uninstall_failed", "Uninstall failed: {pkg} ({error})").format(
                    pkg=package_id, error=str(error)
                )
            )
            if self.kernel:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "Warning"),
                    self._t("package_manager.uninstall_failed", "Uninstall failed: {pkg}\n{error}").format(
                        pkg=package_id, error=str(error)
                    ),
                )
        self._refresh()
        self._on_selection_changed()

    def _append_result(self, line: str):
        if not self.result_text:
            return
        old = self.result_text.toPlainText().strip()
        text = f"{old}\n{line}".strip()
        lines = text.splitlines()
        self.result_text.setPlainText("\n".join(lines[-30:]))

    def retranslate_ui(self) -> None:
        """Retranslate retained Package Manager content without replacing its Host-owned shell."""
        scope_hint = getattr(self, "_scope_hint", None)
        if scope_hint:
            scope_hint.setText(
                self._t(
                    "package_manager.scope_hint",
                    "管理织机官方/社区扩展与编辑器插件。引擎版本见 Hub 或「核心」标签（只读）。"
                    "项目资源请用项目面板导入，不在此安装。",
                )
            )

        search_input = getattr(self, "search_input", None)
        if search_input:
            search_input.setPlaceholderText(
                self._t("package_manager.search_placeholder", "按名称/ID/分类过滤...")
            )
        clear_search_btn = getattr(self, "_clear_search_btn", None)
        if clear_search_btn:
            clear_search_btn.setText(
                self._t("package_manager.search_clear", "清除")
            )

        status_filter = getattr(self, "status_filter", None)
        if status_filter:
            for index, (key, default) in enumerate(
                (
                    ("package_manager.filter.status.all", "全部状态"),
                    ("package_manager.filter.status.enabled", "已启用"),
                    ("package_manager.filter.status.disabled", "已禁用"),
                    ("package_manager.filter.status.issues", "有问题"),
                )
            ):
                status_filter.setItemText(index, self._t(key, default))

        source_filter = getattr(self, "source_filter", None)
        if source_filter:
            for index, (key, default) in enumerate(
                (
                    ("package_manager.filter.source.all", "全部来源"),
                    ("package_manager.filter.source.builtin", "内置 builtin"),
                    ("package_manager.filter.source.file", "本地 file"),
                    ("package_manager.filter.source.url", "远程 url"),
                )
            ):
                source_filter.setItemText(index, self._t(key, default))

        tab_bar = getattr(self, "tab_bar", None)
        if tab_bar:
            for index, (key, default) in enumerate(
                (
                    ("package_manager.tab.installed", "全部"),
                    ("package_manager.tab.plugins", "插件"),
                    ("package_manager.tab.core", "核心"),
                    ("package_manager.tab.official", "官方"),
                    ("package_manager.tab.resources", "资源"),
                    ("package_manager.tab.community", "社区"),
                    ("package_manager.tab.updates", "更新"),
                )
            ):
                tab_bar.setTabText(index, self._t(key, default))

        text_targets = (
            ("queue_select_all_btn", "package_manager.queue.select_all", "全选"),
            ("queue_invert_btn", "package_manager.queue.invert", "反选"),
            ("queue_clear_btn", "package_manager.queue.clear", "清空勾选"),
            ("queue_only_checked_cb", "package_manager.queue.only_checked", "仅显示已勾选"),
            ("_refresh_btn", "package_manager.refresh", "刷新"),
            ("_enable_btn", "package_manager.enable", "启用"),
            ("_disable_btn", "package_manager.disable", "禁用"),
            ("_more_btn", "package_manager.more_actions", "更多操作"),
            ("_reload_btn", "plugin_manager.reload", "重载"),
            ("_unload_btn", "plugin_manager.unload", "卸载"),
            ("_project_disable_btn", "plugin_manager.disable_project", "项目禁用"),
            ("_project_enable_btn", "plugin_manager.enable_project", "项目启用"),
        )
        for attr_name, key, default in text_targets:
            target = getattr(self, attr_name, None)
            if target:
                target.setText(self._t(key, default))

        tooltip_targets = (
            ("_reload_btn", "plugin_manager.reload_tip", "重载选中的插件"),
            ("_unload_btn", "plugin_manager.unload_tip", "卸载选中的插件"),
            ("_project_disable_btn", "plugin_manager.disable_project_tip", "在当前项目中禁用该插件（持久化）"),
            ("_project_enable_btn", "plugin_manager.enable_project_tip", "在当前项目中启用该插件（持久化）"),
        )
        for attr_name, key, default in tooltip_targets:
            target = getattr(self, attr_name, None)
            if target:
                target.setToolTip(self._t(key, default))

        action_labels = (
            ("install_selected", "package_manager.install_selected", "安装选中包"),
            ("uninstall_selected", "package_manager.uninstall_selected", "卸载选中包"),
            ("update_selected", "package_manager.update_selected", "更新选中包"),
            ("update_all", "package_manager.update_all", "全部更新"),
            ("rollback_latest", "package_manager.rollback_latest", "回滚最近更新"),
            ("open_plugins_tab", "package_manager.open_plugins_tab", "切换到「插件」列表"),
            ("toggle_float", "package_manager.toggle_float", "切换浮动/停靠"),
        )
        actions = getattr(self, "_more_actions", {})
        for action_name, key, default in action_labels:
            action = actions.get(action_name)
            if action:
                action.setText(self._t(key, default))

        float_open_action = getattr(self, "_float_open_action", None)
        if float_open_action:
            float_open_action.setText(
                self._t("package_manager.default_float_open", "默认浮动打开")
            )

        detail_text = getattr(self, "detail_text", None)
        if detail_text:
            detail_text.setPlaceholderText(
                self._t("package_manager.placeholder", "选择一个包以查看详情")
            )
        result_text = getattr(self, "result_text", None)
        if result_text:
            result_text.setPlaceholderText(
                self._t("package_manager.result.placeholder", "操作结果将显示在这里...")
            )
        window = getattr(self, "window", None)
        if window:
            window.setWindowTitle(self._t("plugin_manager.title", "项目插件"))

        self._update_queue_stats_label()
        self._update_float_toggle_btn_text()
        self._refresh()
        self._on_selection_changed()

    def _on_language_changed(self, _data) -> None:
        if self._ui_building:
            self._pending_language_rebuild = True
            return
        self.retranslate_ui()

    def _warm_package_cache(self) -> None:
        try:
            self._packages = self._load_all_packages()
        except Exception as exc:
            logger.warning("预加载包索引失败: %s", exc)

    def _should_auto_align_manifest(self) -> bool:
        try:
            config = get_project_world_read_model(
                self.context
            ).current_project_world_config()
            if isinstance(config, dict) and "manifest_auto_align" in config:
                return bool(config.get("manifest_auto_align"))
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        return True

    def _show_status_message(self, message: str, timeout_ms: int = 10000) -> None:
        if not self.kernel:
            return
        lm = getattr(self.kernel, "layout_manager", None)
        sb = getattr(lm, "statusbar", None) if lm else None
        if sb is not None:
            sb.showMessage(message, timeout_ms)

    def _on_project_manifest_issues(self, result) -> None:
        """工程 manifest 缺包时自动对齐（默认开启），失败再弹窗确认。"""
        if result is None or not getattr(result, "missing_packages", None):
            return
        missing = list(result.missing_packages)
        if not missing:
            return
        if not self.kernel:
            return

        if self._should_auto_align_manifest():
            if self._align_manifest_packages(missing):
                if hasattr(self.context, "event_bus"):
                    self.context.event_bus.publish("project_manifest_resolved", missing)
                self._show_status_message(
                    self._t(
                        "manifest.auto_aligned",
                        "已自动对齐工程依赖包（{count} 个）。若插件仍未生效，请重启编辑器。",
                    ).format(count=len(missing))
                )
                if self.package_list:
                    self._refresh()
                return

        lines = "\n".join(f"• {pid}" for pid in missing[:12])
        if len(missing) > 12:
            lines += f"\n… +{len(missing) - 12}"
        box = QMessageBox(self.kernel)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(
            self._t("manifest.dialog.title", "工程包未对齐")
        )
        box.setText(
            self._t(
                "manifest.dialog.body",
                "当前工程需要以下官方包，但未启用或缺失：\n{lines}",
            ).format(lines=lines)
        )
        align_btn = box.addButton(
            self._t("manifest.dialog.align", "对齐依赖并刷新"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        box.addButton(
            self._t("manifest.dialog.dismiss", "稍后处理"),
            QMessageBox.ButtonRole.RejectRole,
        )
        box.exec()
        if box.clickedButton() != align_btn:
            return
        if self._align_manifest_packages(missing):
            if hasattr(self.context, "event_bus"):
                self.context.event_bus.publish("project_manifest_resolved", missing)
            QMessageBox.information(
                self.kernel,
                self._t("dialog.info.title", "提示"),
                self._t(
                    "manifest.dialog.aligned",
                    "已更新 disabled_plugins。若仍有警告，请重启编辑器以重载插件。",
                ),
            )
        self._refresh()

    def _align_manifest_packages(self, missing_ids: list[str]) -> bool:
        if not self.operation_service or not missing_ids:
            return False
        self._packages = self._load_all_packages()
        services = getattr(self.context, "services", None)
        downloader = services.get(DOWNLOADER) if services and hasattr(services, "get") else None
        result = PackageProjectOperations.align_manifest_packages(
            missing_ids,
            self._packages,
            get_enabled_ids=self._enabled_package_ids,
            operation_service=self.operation_service,
            run_project_command=self._run_project_plugin_command,
            downloader=downloader,
            mode=self._get_enable_constraint_mode(),
            command_succeeded=self._handle_project_plugin_command_result,
        )
        validation_report: Dict[str, Any] = {}
        try:
            validation_report = get_project_world_manifest_validation_host(
                self.context
            ).refresh_current_project_manifest_validation()
        except Exception:
            __import__("logging").getLogger(__name__).debug(
                "Ignored recoverable exception.", exc_info=True
            )
        raw_remaining = validation_report.get("missing_packages", missing_ids)
        remaining = (
            [str(item) for item in raw_remaining]
            if isinstance(raw_remaining, list)
            else list(missing_ids)
        )
        return bool(result.get("ok") and not remaining)

    def _on_project_opened(self, _data):
        # 项目切换后预热包缓存；完整刷新在 project_plugins_synced 之后
        self._capture_dock_floating_geometry()
        self._warm_package_cache()

    def _on_project_plugins_synced(self, _data) -> None:
        """工程插件按需激活完成后刷新列表（disabled_plugins 与 loaded 状态已就绪）。"""
        self._capture_dock_floating_geometry()
        if self._ensure_ui_refs():
            self._refresh()
        else:
            self._warm_package_cache()
        self._on_selection_changed()
