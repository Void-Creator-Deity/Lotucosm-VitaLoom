"""包管理器 Dock：Unity 风格包 = 插件组 + manifest 元数据。

排错: 见 `builtin/README.md`、`docs/package_operation_lifecycle.md`。
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
)

from core.plugin.interfaces import IDockProvider, IMenuProvider
from core.VitaLoom.project.project_manager import get_project_manager
from core.VitaLoom.ui.base_editor_widget import BaseEditorWidget
from builtin.editor_extensions.package_services import (
    PackageCatalogService,
    PackageOperationService,
    parse_dependency_expr,
    parse_version,
    version_gte,
)


class PackageManagerPlugin(IDockProvider, IMenuProvider):
    """包管理 Dock + 菜单：安装/卸载/解析依赖；生命周期同 IDockProvider。"""

    DOCK_ID = "Package Manager"

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PackageManager",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "Unity 风格包管理器（按项目启用/禁用一组官方插件）",
            "dependencies": ["Localization"],
            "provides": ["dock", "menu"],
            "protected": True,
        }

    def on_load(self, editor_context):
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
        self.float_toggle_btn: Optional[QPushButton] = None
        self.open_mode_toggle_cb: Optional[QCheckBox] = None
        self._last_floating_geometry_hex: str = ""
        self.catalog_service: Optional[PackageCatalogService] = None
        self.operation_service: Optional[PackageOperationService] = None

        if hasattr(self.context, "event_bus"):
            self.context.event_bus.subscribe("language_changed", self._on_language_changed)
            self.context.event_bus.subscribe("project_opened", self._on_project_opened)
        self.catalog_service = PackageCatalogService(self._get_repo_root())
        self.operation_service = PackageOperationService(get_project_manager())
        services = getattr(self.context, "services", None)
        if services and hasattr(services, "register"):
            services.register("package.catalog", self.catalog_service)
            services.register("package.operations", self.operation_service)

    def on_unload(self):
        if hasattr(self, "context") and self.context and hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception:
                pass
            try:
                self.context.event_bus.unsubscribe("project_opened", self._on_project_opened)
            except Exception:
                pass
        if self.dock:
            self.dock.deleteLater()
        if self.window:
            self.window.deleteLater()
        services = getattr(self.context, "services", None)
        if services and hasattr(services, "unregister"):
            services.unregister("package.catalog")
            services.unregister("package.operations")

    def create_dock_widget(self) -> QDockWidget:
        self.dock = QDockWidget(self._t("package_manager.title", "包管理器"))
        self.dock.setObjectName(self.DOCK_ID)

        content = self._build_main_widget(self.dock)
        self.dock.setWidget(content)
        self._refresh()
        self._on_selection_changed()
        return self.dock

    def get_dock_config(self) -> Dict[str, Any]:
        return {
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": False,
            "can_close": True,
            # 不默认 tabify 到其它面板；show() 会让它以 floating dock 的形态出现。
            "tabbed_with": None,
        }

    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": f"{self._t('menu.tools', '工具')}/{self._t('package_manager.title', '包管理器')}",
                "action": self.show,
            }
        ]

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        return []

    def _restore_dock_floating_geometry(self):
        if not self.dock or not self._last_floating_geometry_hex:
            return
        try:
            from PyQt6.QtCore import QByteArray
            data = bytes.fromhex(self._last_floating_geometry_hex)
            self.dock.restoreGeometry(QByteArray(data))
        except Exception:
            pass

    def _capture_dock_floating_geometry(self):
        if not self.dock:
            return
        try:
            if self.dock.isFloating():
                self._last_floating_geometry_hex = bytes(self.dock.saveGeometry()).hex()
        except Exception:
            pass

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
        if not self.float_toggle_btn or not self.dock:
            return
        if self.dock.isFloating():
            self.float_toggle_btn.setText(self._t('package_manager.dock_to_main', '停靠到主界面'))
        else:
            self.float_toggle_btn.setText(self._t('package_manager.float_window', '浮动窗口'))

    def _build_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        统一构建包管理器主界面（独立窗口与 dock 入口共享）。
        注意：这里只负责控件创建与信号绑定；数据刷新由 `_refresh()` 完成。
        """
        root = BaseEditorWidget()
        if parent is not None:
            root.setParent(parent)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QLabel(self._t("package_manager.title", "包管理器"))
        layout.addWidget(header)

        search_row = QHBoxLayout()
        search_label = QLabel(self._t("package_manager.search", "搜索"))
        search_row.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self._t("package_manager.search_placeholder", "按名称/ID/分类过滤..."))
        self.search_input.textChanged.connect(self._refresh)
        search_row.addWidget(self.search_input, 1)
        self.status_filter = QComboBox()
        self.status_filter.addItems(
            [
                self._t("package_manager.filter.status.all", "全部状态"),
                self._t("package_manager.filter.status.enabled", "已启用"),
                self._t("package_manager.filter.status.disabled", "已禁用"),
                self._t("package_manager.filter.status.issues", "有问题"),
            ]
        )
        self.status_filter.currentIndexChanged.connect(self._refresh)
        search_row.addWidget(self.status_filter)

        self.source_filter = QComboBox()
        self.source_filter.addItems(
            [
                self._t("package_manager.filter.source.all", "全部来源"),
                "builtin",
                "file",
                "url",
            ]
        )
        self.source_filter.currentIndexChanged.connect(self._refresh)
        search_row.addWidget(self.source_filter)
        layout.addLayout(search_row)

        self.tab_bar = QTabWidget()
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.installed", "Installed"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.official", "Official"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.community", "Community"))
        self.tab_bar.addTab(QWidget(), self._t("package_manager.tab.updates", "Updates"))
        self.tab_bar.currentChanged.connect(lambda _idx: self._refresh())
        layout.addWidget(self.tab_bar)

        queue_row = QHBoxLayout()
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
        self.queue_only_checked_cb.stateChanged.connect(self._refresh)
        queue_row.addWidget(self.queue_only_checked_cb)
        self.queue_stats_label = QLabel("")
        queue_row.addWidget(self.queue_stats_label)
        queue_row.addStretch(1)
        layout.addLayout(queue_row)

        top_row = QHBoxLayout()
        refresh_btn = QPushButton(f"🔃 {self._t('package_manager.refresh', '刷新')}")
        refresh_btn.clicked.connect(self._refresh)
        top_row.addWidget(refresh_btn)

        enable_btn = QPushButton(f"✅ {self._t('package_manager.enable', '项目启用')}")
        enable_btn.clicked.connect(self._enable_selected)
        top_row.addWidget(enable_btn)

        disable_btn = QPushButton(f"🚫 {self._t('package_manager.disable', '项目禁用')}")
        disable_btn.clicked.connect(self._disable_selected)
        top_row.addWidget(disable_btn)

        install_btn = QPushButton(f"📦 {self._t('package_manager.install_selected', '安装选中包')}")
        install_btn.clicked.connect(self._install_selected_package)
        top_row.addWidget(install_btn)

        uninstall_btn = QPushButton(f"🧹 {self._t('package_manager.uninstall_selected', '卸载选中包')}")
        uninstall_btn.clicked.connect(self._uninstall_selected_package)
        top_row.addWidget(uninstall_btn)

        update_btn = QPushButton(f"⬆️ {self._t('package_manager.update_selected', '更新选中包')}")
        update_btn.clicked.connect(self._update_selected_package)
        top_row.addWidget(update_btn)

        update_all_btn = QPushButton(f"🚀 {self._t('package_manager.update_all', '全部更新')}")
        update_all_btn.clicked.connect(self._update_all_packages)
        top_row.addWidget(update_all_btn)

        rollback_btn = QPushButton(f"↩️ {self._t('package_manager.rollback_latest', '回滚最近更新')}")
        rollback_btn.clicked.connect(self._rollback_latest_update_plan)
        top_row.addWidget(rollback_btn)

        self.float_toggle_btn = QPushButton()
        self.float_toggle_btn.clicked.connect(self._toggle_dock_floating)
        top_row.addWidget(self.float_toggle_btn)

        self.open_mode_toggle_cb = QCheckBox(self._t("package_manager.default_float_open", "默认浮动打开"))
        self.open_mode_toggle_cb.setChecked(self._get_package_manager_open_mode() == "floating")
        self.open_mode_toggle_cb.stateChanged.connect(self._on_open_mode_toggle_changed)
        top_row.addWidget(self.open_mode_toggle_cb)

        top_row.addStretch(1)
        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.package_list = QListWidget()
        self.package_list.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.package_list)
        splitter.setStretchFactor(0, 1)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText(self._t("package_manager.placeholder", "选择一个包以查看详情"))
        splitter.addWidget(self.detail_text)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(120)
        self.result_text.setPlaceholderText(self._t("package_manager.result.placeholder", "操作结果将显示在这里..."))
        layout.addWidget(self.result_text)

        return root

    def show(self):
        # Unity 风格：本质仍是 dock，但默认以浮动窗口形态出现，可随时拖回主 UI。
        if not self.dock and self.kernel and hasattr(self.kernel, "layout_manager"):
            dock = self.create_dock_widget()
            self.kernel.layout_manager.add_dock(dock, self.get_dock_config())

        if self.dock:
            open_mode = self._get_package_manager_open_mode()
            lm = getattr(self.kernel, "layout_manager", None) if self.kernel else None
            if lm and hasattr(lm, "show_dock_with_mode"):
                lm.show_dock_with_mode(self.DOCK_ID, open_mode == "floating")
                self._sync_hex_from_dock_for_fallback()
            else:
                if open_mode == "floating":
                    self.dock.setFloating(True)
                    self._restore_dock_floating_geometry()
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
            return

        # 兜底：极端情况下 layout manager 不可用时，仍回退到独立对话框。
        if not self.window:
            parent = self.kernel if isinstance(self.kernel, QWidget) else None
            self.window = QDialog(parent)
            self.window.setWindowTitle(self._t("package_manager.title", "包管理器"))
            self.window.resize(1100, 760)
            root = self._build_main_widget(self.window)
            window_layout = QVBoxLayout(self.window)
            window_layout.setContentsMargins(0, 0, 0, 0)
            window_layout.addWidget(root)

        self._refresh()
        self.window.setWindowTitle(self._t("package_manager.title", "包管理器"))
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _get_repo_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _get_registry_config_path(self) -> str:
        repo_root = self._get_repo_root()
        return os.path.join(repo_root, "data", "system", "package_registries.json")

    def _get_policy_config_path(self) -> str:
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
        mode = "floating" if self.open_mode_toggle_cb.isChecked() else "docked"
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
        downloader = services.get("downloader") if services and hasattr(services, "get") else None
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
        if not isinstance(pkg, dict):
            return {}
        normalized = dict(pkg)
        normalized.setdefault("id", "")
        normalized.setdefault("display_name", normalized.get("id", ""))
        normalized.setdefault("version", "")
        normalized.setdefault("category", "")
        normalized.setdefault("description", "")
        normalized.setdefault("dependencies", [])
        normalized.setdefault("conflicts", [])
        normalized.setdefault("plugins", [])
        normalized.setdefault("source", source)
        return normalized

    @staticmethod
    def merge_package_lists(package_lists: List[List[Dict[str, Any]]], priority_sources: List[str]) -> List[Dict[str, Any]]:
        """按包 id 去重合并，优先使用 priority_sources 更靠前的来源。"""
        priority = {name: idx for idx, name in enumerate(priority_sources)}
        merged: Dict[str, Dict[str, Any]] = {}
        for pkg_list in package_lists:
            for pkg in pkg_list:
                if not isinstance(pkg, dict):
                    continue
                pkg_id = str(pkg.get("id", "") or "")
                if not pkg_id:
                    continue
                src = str(pkg.get("source", "unknown"))
                if pkg_id not in merged:
                    merged[pkg_id] = pkg
                    continue
                old = merged[pkg_id]
                old_src = str(old.get("source", "unknown"))
                if priority.get(src, 10_000) < priority.get(old_src, 10_000):
                    merged[pkg_id] = pkg
        # stable order: by display_name then id
        return sorted(merged.values(), key=lambda p: (str(p.get("display_name", "")), str(p.get("id", ""))))

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
        return bool(has_dependency_or_conflict_issue) and str(enable_constraint_mode).lower() == "block"

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
        return enabled

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
        downloader = services.get("downloader") if services and hasattr(services, "get") else None
        overrides = self.operation_service.get_version_overrides()
        merged, updates, errors = self.catalog_service.load_all_packages(overrides, downloader=downloader)
        self._update_candidates = updates
        if errors and self.kernel:
            # 仅提示一次，不阻断 UI
            QMessageBox.warning(
                self.kernel,
                self._t("dialog.warning.title", "警告"),
                self._t("package_manager.registry_partial_failed", "部分包源加载失败（已忽略）：\n{errors}").format(errors="\n".join(errors)),
            )
        return merged

    @classmethod
    def _collect_update_candidates(
        cls,
        loaded_lists: List[List[Dict[str, Any]]],
        merged: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        highest: Dict[str, str] = {}
        for pkg_list in loaded_lists:
            for pkg in pkg_list:
                pkg_id = str(pkg.get("id", "") or "")
                if not pkg_id:
                    continue
                ver = str(pkg.get("version", "") or "0.0.0")
                old = highest.get(pkg_id)
                if old is None or cls._version_gte(ver, old):
                    highest[pkg_id] = ver
        updates: Dict[str, str] = {}
        for pkg in merged:
            pkg_id = str(pkg.get("id", "") or "")
            if not pkg_id:
                continue
            current = str(pkg.get("version", "") or "0.0.0")
            latest = highest.get(pkg_id, current)
            if cls._version_gte(latest, current) and cls._parse_version(latest) != cls._parse_version(current):
                updates[pkg_id] = latest
        return updates

    def _refresh(self):
        # 在刷新前记录 updates 页签中的勾选状态，便于刷新后保留队列
        if self._get_tab_filter() == "updates":
            self._checked_update_ids = self._get_checked_update_ids()
        self._packages = self._load_all_packages()
        if not self.package_list:
            return
        self._set_queue_buttons_enabled()
        self.package_list.clear()
        keyword = (self.search_input.text() if self.search_input else "") or ""
        keyword = keyword.strip().lower()

        disabled = self._get_project_disabled_plugins()
        disabled_set = set(disabled or [])
        tab_filter = self._get_tab_filter()
        status_filter = self._get_status_filter()
        source_filter = self._get_source_filter()
        only_checked = bool(self.queue_only_checked_cb and self.queue_only_checked_cb.isChecked() and tab_filter == "updates")

        for pkg in self._packages:
            pkg_id = str(pkg.get("id", ""))
            name = str(pkg.get("display_name", pkg_id or "Unnamed Package"))
            category = str(pkg.get("category", ""))
            source = str(pkg.get("source", ""))
            version = str(pkg.get("version", ""))
            plugins = pkg.get("plugins", [])
            if not isinstance(plugins, list):
                plugins = []
            enabled_count = sum(1 for p in plugins if str(p) not in disabled_set)
            total_count = len(plugins)
            has_issues = self._package_has_issues(pkg)
            is_enabled = enabled_count > 0

            if not self._matches_tab_filter(pkg, tab_filter):
                continue
            if not self._matches_status_filter(is_enabled, has_issues, status_filter):
                continue
            if source_filter != "all" and source.lower() != source_filter:
                continue

            if keyword:
                hay = f"{name}\n{pkg_id}\n{category}\n{source}".lower()
                if keyword not in hay:
                    continue
            if only_checked and pkg_id not in self._checked_update_ids:
                continue
            label = self._t("package_manager.list_item", "{name}  ({enabled}/{total})  [{source}]").format(
                name=name, enabled=enabled_count, total=total_count, source=source
            )
            if version:
                label = f"{label}  v{version}"
            latest = self._update_candidates.get(pkg_id, "")
            if latest:
                label = f"{label}  {self._t('package_manager.update.available', '-> latest {version}').format(version=latest)}"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, pkg_id)
            if tab_filter == "updates":
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if pkg_id in self._checked_update_ids else Qt.CheckState.Unchecked)
            self.package_list.addItem(item)
        self._update_queue_stats_label()

    def _get_checked_update_ids(self) -> set[str]:
        if not self.package_list:
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
        is_updates_tab = self._get_tab_filter() == "updates"
        for btn in [self.queue_select_all_btn, self.queue_invert_btn, self.queue_clear_btn, self.queue_only_checked_cb]:
            if btn:
                btn.setEnabled(is_updates_tab)
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

    def _get_tab_filter(self) -> str:
        if not self.tab_bar:
            return "installed"
        idx = self.tab_bar.currentIndex()
        if idx == 1:
            return "official"
        if idx == 2:
            return "community"
        if idx == 3:
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
        text = self.source_filter.currentText().strip().lower()
        if text in {"builtin", "file", "url"}:
            return text
        return "all"

    def _matches_tab_filter(self, pkg: Dict[str, Any], tab_filter: str) -> bool:
        pkg_id = str(pkg.get("id", "") or "")
        source = str(pkg.get("source", "")).lower()
        category = str(pkg.get("category", "")).lower()
        if tab_filter == "official":
            return source == "builtin" or category == "official"
        if tab_filter == "community":
            return source in {"url", "file"} and category != "official"
        if tab_filter == "updates":
            return pkg_id in self._update_candidates
        return True

    @staticmethod
    def _matches_status_filter(is_enabled: bool, has_issues: bool, status_filter: str) -> bool:
        if status_filter == "enabled":
            return is_enabled
        if status_filter == "disabled":
            return not is_enabled
        if status_filter == "issues":
            return has_issues
        return True

    @staticmethod
    def _select_target_updates(update_candidates: Dict[str, str], checked_ids: set[str]) -> Dict[str, str]:
        if not checked_ids:
            return dict(update_candidates)
        return {k: v for k, v in update_candidates.items() if k in checked_ids}

    def _package_has_issues(self, pkg: Dict[str, Any]) -> bool:
        dep_status = self._evaluate_dependency_status(pkg)
        conflict_status = self._evaluate_conflict_status(pkg)
        for line in dep_status + conflict_status:
            upper = line.upper()
            if "MISSING:" in upper or "INCOMPATIBLE:" in upper or "DISABLED:" in upper or "CONFLICT:" in upper:
                return True
        return False

    def _get_selected_package(self) -> Optional[Dict[str, Any]]:
        if not self.package_list:
            return None
        item = self.package_list.currentItem()
        if not item:
            return None
        pkg_id = item.data(Qt.ItemDataRole.UserRole)
        for pkg in self._packages:
            if str(pkg.get("id", "")) == str(pkg_id):
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

    def _write_project_disabled_plugins(self, disabled_plugins: List[str]) -> bool:
        if not self.operation_service:
            return False
        return self.operation_service.write_disabled_plugins(disabled_plugins)

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

    def _on_selection_changed(self):
        pkg = self._get_selected_package()
        if not pkg or not self.detail_text:
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
        deps = pkg.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []
        dep_status = self._evaluate_dependency_status(pkg)
        conflicts = pkg.get("conflicts", [])
        if not isinstance(conflicts, list):
            conflicts = []
        conflict_status = self._evaluate_conflict_status(pkg)
        plugin_lines = "\n".join([f"- {p}" for p in plugins])
        dep_status_lines = "\n".join([f"- {line}" for line in dep_status]) or "-"
        conflict_status_lines = "\n".join([f"- {line}" for line in conflict_status]) or "-"
        mode = self._get_enable_constraint_mode()
        mode_text = self._t("package_manager.policy.warn", "warn（仅警告）")
        if mode == "block":
            mode_text = self._t("package_manager.policy.block", "block（阻止启用）")

        self.detail_text.setPlainText(
            f"{pkg.get('display_name', pkg.get('id', ''))}\n"
            f"{self._t('package_manager.meta.id', 'ID')}: {pkg_id}\n"
            f"{self._t('package_manager.meta.version', '版本')}: {version}\n"
            f"{self._t('package_manager.meta.latest_version', '最新版本')}: {latest}\n"
            f"{self._t('package_manager.meta.category', '分类')}: {category}\n"
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
            f"{self._t('package_manager.plugins', '包含插件')}:\n{plugin_lines}"
        )

    def _enable_selected(self):
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
        plugins = pkg.get("plugins", [])
        if not isinstance(plugins, list):
            return
        disabled = self._get_project_disabled_plugins()
        if disabled is None:
            return
        disabled_set = set(disabled)
        for p in plugins:
            disabled_set.discard(str(p))
        if self._write_project_disabled_plugins(sorted(disabled_set)):
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.enabled_hint", "已写入项目配置。已禁用的插件被重新启用后，需要重启编辑器以重新加载。"),
                )
        self._on_selection_changed()

    def _disable_selected(self):
        pkg = self._get_selected_package()
        if not pkg or not self.kernel:
            return
        plugins = pkg.get("plugins", [])
        if not isinstance(plugins, list):
            return
        disabled = self._get_project_disabled_plugins()
        if disabled is None:
            return
        disabled_set = set(disabled)
        loader = getattr(self.kernel, "plugin_loader", None)
        protected: set[str] = set()
        if loader and hasattr(loader, "is_plugin_protected"):
            for p in plugins:
                if loader.is_plugin_protected(str(p)):
                    protected.add(str(p))

        for p in plugins:
            if str(p) in protected:
                continue
            disabled_set.add(str(p))
        if self._write_project_disabled_plugins(sorted(disabled_set)):
            # 立即卸载已加载的插件（会话生效）
            if loader:
                for p in plugins:
                    if str(p) in protected:
                        continue
                    try:
                        loader.unload_plugin(str(p))
                    except Exception:
                        pass
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
        package_id = str(pkg.get("id", "")).strip()
        if not package_id:
            return
        services = getattr(self.context, "services", None)
        downloader = services.get("downloader") if services and hasattr(services, "get") else None
        enabled_ids = self._enabled_package_ids()
        mode = self._get_enable_constraint_mode()
        result = self.operation_service.install_package(
            package_id,
            self._packages,
            enabled_ids,
            downloader=downloader,
            mode=mode,
        )
        if result.get("ok"):
            self._append_result(self._t("package_manager.result.installed", "安装成功：{pkg}").format(pkg=package_id))
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.install_ok", "安装成功：{pkg}").format(pkg=package_id),
                )
        else:
            self._append_result(
                self._t("package_manager.result.install_failed", "安装失败：{pkg} ({error})").format(
                    pkg=package_id, error=str(result.get("error", "unknown"))
                )
            )
            if self.kernel:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "警告"),
                    self._t("package_manager.install_failed", "安装失败：{pkg}\n{error}").format(
                        pkg=package_id, error=str(result.get("error", "unknown"))
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
        result = self.operation_service.uninstall_package(package_id)
        if result.get("ok"):
            self._append_result(self._t("package_manager.result.uninstalled", "卸载成功：{pkg}").format(pkg=package_id))
            if self.kernel:
                QMessageBox.information(
                    self.kernel,
                    self._t("dialog.info.title", "提示"),
                    self._t("package_manager.uninstall_ok", "卸载成功：{pkg}").format(pkg=package_id),
                )
        else:
            self._append_result(
                self._t("package_manager.result.uninstall_failed", "卸载失败：{pkg} ({error})").format(
                    pkg=package_id, error=str(result.get("error", "unknown"))
                )
            )
            if self.kernel:
                QMessageBox.warning(
                    self.kernel,
                    self._t("dialog.warning.title", "警告"),
                    self._t("package_manager.uninstall_failed", "卸载失败：{pkg}\n{error}").format(
                        pkg=package_id, error=str(result.get("error", "unknown"))
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

    def _on_language_changed(self, _data):
        dock_was_visible = bool(self.dock and self.dock.isVisible())
        dock_was_floating = bool(self.dock and self.dock.isFloating())

        if self.window:
            # 语言切换时重建独立窗口，确保文本完整刷新
            was_visible = self.window.isVisible()
            self.window.deleteLater()
            self.window = None
            self.package_list = None
            self.detail_text = None
            self.search_input = None
            self.tab_bar = None
            self.status_filter = None
            self.source_filter = None
            self.queue_select_all_btn = None
            self.queue_invert_btn = None
            self.queue_clear_btn = None
            self.queue_only_checked_cb = None
            self.queue_stats_label = None
            self.result_text = None
            self.open_mode_toggle_cb = None
            if was_visible:
                self.show()
        # 重建 dock 入口文本
        if self.dock and self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            if hasattr(lm, remove_dock):
                lm.remove_dock(self.DOCK_ID)
            dock = self.create_dock_widget()
            lm.add_dock(dock, self.get_dock_config())
            if dock_was_floating and self.dock:
                self.dock.setFloating(True)
                self._restore_dock_floating_geometry()
            if dock_was_visible:
                self.dock.setVisible(True)
                self.dock.show()
                self.dock.raise_()


    def _on_project_opened(self, _data):
        # 项目切换后，详情状态需要刷新
        self._capture_dock_floating_geometry()
        self._on_selection_changed()

