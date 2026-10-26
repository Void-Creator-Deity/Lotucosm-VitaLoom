# -*- coding: utf-8 -*-
"""Suite-level Hub window."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from FrameCore.product_registry import load_product_registry
from FrameCore.project_lock import resolve_project_runtime
from hub.hub_installs_dialog import HubInstallsDialog
from hub.hub_launcher import (
    decode_process_output,
    failure_output_excerpt,
    start_editor_subprocess,
    write_editor_launch_log,
)
from hub.hub_paths import projects_root, suite_root
from hub.project_index import register_known_project
from hub.project_list_model import HubProjectEntry, discover_hub_projects, filter_entries

MAX_CAPTURED_OUTPUT_BYTES = 1_000_000


def _chip_status(admission: str, text: str = "") -> str:
    canonical = (admission or "").strip().lower()
    if canonical == "current":
        return "ok"
    if canonical in {"legacy", "missing"}:
        return "warning"
    if canonical in {
        "invalid",
        "unsupported_schema",
        "version_missing",
        "constraint_mismatch",
        "stale",
    }:
        return "danger"
    lowered = (text or "").lower()
    if not text:
        return "neutral"
    if any(token in lowered for token in ("missing", "unresolved", "mismatch", "failed", "缺", "不符")):
        return "danger"
    if any(token in lowered for token in ("unlock", "未", "stale", "warning")):
        return "warning"
    return "ok"


def _project_state(entry: HubProjectEntry) -> tuple[str, str]:
    """Translate lock internals into a user-facing launch state."""
    tone = _chip_status(entry.lock_admission, entry.lock_status)
    if tone == "ok":
        return "可打开", tone
    if entry.lock_admission == "legacy":
        return "可打开 · 旧锁", tone
    if entry.lock_admission == "missing":
        return "可打开 · 未锁定", tone
    if tone == "danger":
        return "需要修复", tone
    return entry.lock_status or "状态未知", tone


def _display_path(path: str, repo_root: str | Path) -> str:
    raw = Path(path).resolve()
    root = Path(repo_root).resolve()
    try:
        relative = raw.relative_to(root)
    except ValueError:
        return str(raw)
    if relative.parts[:2] == ("workspace", "projects"):
        return str(Path(*relative.parts[2:])) or "."
    return str(relative)


def _set_chip_state(label: QLabel, text: str, tone: str) -> None:
    label.setText(text)
    label.setProperty("status", tone)
    label.style().unpolish(label)
    label.style().polish(label)


class ProjectRowWidget(QFrame):
    """Project summary card: what it is, whether it can open."""

    def __init__(self, entry: HubProjectEntry, parent=None):
        super().__init__(parent)
        self.setObjectName("projectRow")
        self.setProperty("selected", False)
        self.setProperty("focused", False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(entry.path)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(7)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)
        title = QLabel(entry.name)
        title.setObjectName("projectTitle")
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        top.addWidget(title, stretch=1)

        state_text, tone = _project_state(entry)
        self.state_label = QLabel(state_text)
        self.state_label.setObjectName("rowStatus")
        self.state_label.setProperty("status", tone)
        top.addWidget(self.state_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        description = QLabel(entry.description or "暂无项目说明")
        description.setObjectName("projectDescription")
        description.setWordWrap(True)
        description.setMaximumHeight(36)
        layout.addWidget(description)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def focusInEvent(self, event: QFocusEvent) -> None:
        self.setProperty("focused", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.setProperty("focused", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().focusOutEvent(event)


class EmptyStateWidget(QWidget):
    def __init__(self, title: str, hint: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 36, 24, 36)
        layout.setSpacing(8)
        layout.addStretch()
        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        hint_label = QLabel(hint)
        hint_label.setObjectName("emptyHint")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        layout.addStretch()


class HubWindow(QWidget):
    """Project control surface for the Lotucosm-VitaLoom Suite."""

    project_open_requested = pyqtSignal(str)

    def __init__(self, repo_root: str | Path, parent=None):
        super().__init__(parent)
        self.repo_root = str(Path(repo_root).resolve())
        self._entries: list[HubProjectEntry] = []
        self._editor_version = self._load_editor_version()
        self._include_external_recent = False
        self._editor_process = None
        self._editor_project_path = ""
        self._editor_output = bytearray()
        self._hub_action_buttons: list[QPushButton] = []
        self._entry_by_path: dict[str, HubProjectEntry] = {}
        self._search_query = ""
        self.setWindowTitle("VitaLoom · 项目")
        self.setMinimumSize(960, 620)
        self.resize(1120, 720)
        self._build_ui()
        self.refresh_projects()

    def _load_editor_version(self) -> str:
        try:
            registry = load_product_registry(suite_root())
            version = registry.get_default_version("lotucosm-vitaloom")
            return version.version if version is not None else "1.0.0"
        except Exception:
            return "1.0.0"

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(204)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 24, 16, 18)
        side.setSpacing(0)

        product_name = QLabel("VitaLoom")
        product_name.setObjectName("vitaloomSidebarTitle")
        side.addWidget(product_name)
        product_subtitle = QLabel("生命织机")
        product_subtitle.setObjectName("vitaloomHint")
        side.addWidget(product_subtitle)
        side.addSpacing(28)

        section = QLabel("浏览")
        section.setObjectName("sidebarSection")
        side.addWidget(section)
        side.addSpacing(8)

        projects_button = QPushButton("项目")
        projects_button.setObjectName("navActive")
        projects_button.setCheckable(True)
        projects_button.setChecked(True)
        projects_button.setCursor(Qt.CursorShape.PointingHandCursor)
        side.addWidget(projects_button)
        side.addSpacing(4)

        installs_button = QPushButton("运行时与能力")
        installs_button.setObjectName("navSecondary")
        installs_button.setCursor(Qt.CursorShape.PointingHandCursor)
        installs_button.clicked.connect(self._show_installs)  # type: ignore[arg-type]
        side.addWidget(installs_button)
        side.addStretch()

        footer = QFrame()
        footer.setObjectName("sidebarFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 11, 12, 11)
        footer_layout.setSpacing(3)
        runtime_key = QLabel("默认运行时")
        runtime_key.setObjectName("sidebarFooterKey")
        footer_layout.addWidget(runtime_key)
        runtime_value = QLabel(f"VitaLoom {self._editor_version}")
        runtime_value.setObjectName("sidebarVersion")
        footer_layout.addWidget(runtime_value)
        side.addWidget(footer)
        root.addWidget(sidebar)

        main_surface = QWidget()
        main_surface.setObjectName("mainSurface")
        main = QVBoxLayout(main_surface)
        main.setContentsMargins(32, 28, 32, 24)
        main.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(24)
        title_column = QVBoxLayout()
        title_column.setSpacing(4)
        heading = QLabel("项目")
        heading.setObjectName("vitaloomPageTitle")
        title_column.addWidget(heading)
        subtitle = QLabel("选择项目并打开编辑器。")
        subtitle.setObjectName("vitaloomHint")
        title_column.addWidget(subtitle)
        header.addLayout(title_column, stretch=1)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索项目")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(260)
        self.search_edit.setMaximumWidth(340)
        self.search_edit.textChanged.connect(self._on_search_changed)  # type: ignore[arg-type]
        header.addWidget(self.search_edit, alignment=Qt.AlignmentFlag.AlignBottom)
        main.addLayout(header)
        main.addSpacing(24)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)

        self._open_btn = QPushButton("打开项目")
        self._open_btn.setObjectName("primary")
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self._on_open_selected)  # type: ignore[arg-type]
        actions.addWidget(self._open_btn)

        self._import_btn = QPushButton("导入项目")
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.clicked.connect(self._on_import)  # type: ignore[arg-type]
        actions.addWidget(self._import_btn)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.refresh_projects)  # type: ignore[arg-type]
        actions.addWidget(self._refresh_btn)

        self._more_btn = QToolButton()
        self._more_btn.setText("更多")
        self._more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._more_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        more_menu = QMenu(self._more_btn)
        self._external_recent_action = more_menu.addAction("显示外部最近项目")
        self._external_recent_action.setCheckable(True)
        self._external_recent_action.toggled.connect(self._on_toggle_external_recent)  # type: ignore[arg-type]
        self._more_btn.setMenu(more_menu)
        actions.addWidget(self._more_btn)
        actions.addStretch()

        self._status_label = QLabel("")
        self._status_label.setObjectName("vitaloomStatus")
        actions.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._hub_action_buttons = [
            self._open_btn,
            self._import_btn,
            self._refresh_btn,
            self._more_btn,
        ]
        main.addLayout(actions)
        main.addSpacing(20)

        list_heading = QHBoxLayout()
        list_heading.setContentsMargins(0, 0, 0, 0)
        list_title = QLabel("全部项目")
        list_title.setObjectName("listTitle")
        list_heading.addWidget(list_title)
        self._project_count_chip = QLabel("")
        self._project_count_chip.setObjectName("projectCount")
        list_heading.addWidget(self._project_count_chip)
        list_heading.addStretch()
        main.addLayout(list_heading)
        main.addSpacing(10)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setSpacing(2)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)  # type: ignore[arg-type]
        self.list_widget.currentItemChanged.connect(self._sync_project_row_selection)  # type: ignore[arg-type]
        content.addWidget(self.list_widget, stretch=1)

        self._detail_panel = QFrame()
        self._detail_panel.setObjectName("projectDetailPanel")
        self._detail_panel.setFixedWidth(304)
        detail = QVBoxLayout(self._detail_panel)
        detail.setContentsMargins(20, 20, 20, 18)
        detail.setSpacing(0)

        detail_caption = QLabel("项目详情")
        detail_caption.setObjectName("detailCaption")
        detail.addWidget(detail_caption)
        detail.addSpacing(14)

        self._detail_title = QLabel("选择一个项目")
        self._detail_title.setObjectName("detailTitle")
        self._detail_title.setWordWrap(True)
        detail.addWidget(self._detail_title)
        detail.addSpacing(8)

        self._detail_status = QLabel("")
        self._detail_status.setObjectName("detailStatus")
        self._detail_status.setProperty("status", "neutral")
        detail.addWidget(self._detail_status, alignment=Qt.AlignmentFlag.AlignLeft)
        detail.addSpacing(14)

        self._detail_desc = QLabel("")
        self._detail_desc.setObjectName("detailDesc")
        self._detail_desc.setWordWrap(True)
        detail.addWidget(self._detail_desc)
        detail.addSpacing(18)

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        detail.addWidget(divider)
        detail.addSpacing(16)

        self._detail_runtime = QLabel("-")
        self._detail_location = QLabel("-")
        self._detail_modified = QLabel("-")
        for key, value in (
            ("运行时", self._detail_runtime),
            ("位置", self._detail_location),
            ("最近修改", self._detail_modified),
        ):
            key_label = QLabel(key)
            key_label.setObjectName("detailKey")
            detail.addWidget(key_label)
            detail.addSpacing(4)
            value.setObjectName("detailValue")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            detail.addWidget(value)
            detail.addSpacing(14)

        detail.addStretch()
        self._reveal_btn = QPushButton("打开项目文件夹")
        self._reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reveal_btn.clicked.connect(self._on_reveal_selected)  # type: ignore[arg-type]
        self._hub_action_buttons.append(self._reveal_btn)
        detail.addWidget(self._reveal_btn)

        content.addWidget(self._detail_panel)
        main.addLayout(content, stretch=1)
        root.addWidget(main_surface, stretch=1)
        self._update_detail(None)

    def refresh_projects(self) -> None:
        self._status_label.setText("正在扫描项目…")
        self._entries = discover_hub_projects(
            self.repo_root,
            include_external_recent=self._include_external_recent,
        )
        filtered = filter_entries(self._entries, self._search_query)
        empty_text = "没有匹配的项目" if self._search_query.strip() else ""
        self._populate_list(filtered, empty_text)
        self._status_label.setText("")

    def _populate_list(self, entries: list[HubProjectEntry], empty_text: str = "") -> None:
        self.list_widget.clear()
        self._entry_by_path = {entry.path: entry for entry in entries}
        count_text = f"{len(entries)} 个" if entries else "0 个"
        self._project_count_chip.setText(count_text)
        if not entries:
            title = empty_text or "还没有项目"
            hint = (
                "换个关键词试试。"
                if self._search_query
                else "导入一个项目，或把项目放入项目库。"
            )
            item = QListWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setSizeHint(QSize(0, 170))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, EmptyStateWidget(title, hint, self.list_widget))
            self._update_detail(None)
            self._open_btn.setEnabled(False)
            self._reveal_btn.setEnabled(False)
            return
        for entry in entries:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            self.list_widget.addItem(item)
            row = ProjectRowWidget(entry, self.list_widget)
            item.setSizeHint(QSize(0, max(78, row.sizeHint().height())))
            self.list_widget.setItemWidget(item, row)
        self.list_widget.setCurrentRow(0)
        self._sync_project_row_selection()

    def _sync_project_row_selection(self, *_args) -> None:
        current = self.list_widget.currentItem()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, ProjectRowWidget):
                widget.set_selected(item is current)
        entry = self._selected_entry()
        self._update_detail(entry)
        self._open_btn.setEnabled(entry is not None and self._editor_process is None)
        self._reveal_btn.setEnabled(entry is not None)

    def _selected_entry(self) -> HubProjectEntry | None:
        path = self._selected_path()
        if not path:
            return None
        return self._entry_by_path.get(path)

    def _update_detail(self, entry: HubProjectEntry | None) -> None:
        has_entry = entry is not None
        self._reveal_btn.setEnabled(has_entry)
        if entry is None:
            self._detail_title.setText("选择一个项目")
            _set_chip_state(self._detail_status, "未选择", "neutral")
            self._detail_desc.setText("从左侧选择项目后，这里会显示运行时和位置。")
            self._detail_runtime.setText("-")
            self._detail_location.setText("-")
            self._detail_modified.setText("-")
            return
        state_text, tone = _project_state(entry)
        version = entry.product_version or entry.loom_editor_version or "未解析"
        self._detail_title.setText(entry.name)
        _set_chip_state(self._detail_status, state_text, tone)
        self._detail_desc.setText(entry.description or "暂无项目说明。")
        self._detail_runtime.setText(f"VitaLoom {version}")
        self._detail_location.setText(_display_path(entry.path, self.repo_root))
        self._detail_location.setToolTip(entry.path)
        self._detail_modified.setText(entry.modified_at or "未记录")

    def _selected_path(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        path = item.data(Qt.ItemDataRole.UserRole)
        return str(path) if path else None

    def _on_toggle_external_recent(self, checked: bool) -> None:
        self._include_external_recent = checked
        self.refresh_projects()

    def _set_hub_busy(self, busy: bool, message: str = "") -> None:
        for button in self._hub_action_buttons:
            button.setEnabled(not busy)
        self.search_edit.setEnabled(not busy)
        self.list_widget.setEnabled(not busy)
        if not busy:
            has_selection = self._selected_entry() is not None
            self._open_btn.setEnabled(has_selection and self._editor_process is None)
            self._reveal_btn.setEnabled(has_selection)
        self._status_label.setText(message)

    def _on_search_changed(self, text: str) -> None:
        self._search_query = text
        self._populate_list(filter_entries(self._entries, text), "没有匹配的项目")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._open_project(str(path))

    def _on_open_selected(self) -> None:
        path = self._selected_path()
        if not path:
            QMessageBox.information(self, "打开项目", "请先选择一个项目。")
            return
        self._open_project(path)

    def _on_reveal_selected(self) -> None:
        path = self._selected_path()
        if not path:
            return
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception as exc:
            QMessageBox.warning(self, "打开文件夹失败", str(exc))

    def _show_installs(self) -> None:
        HubInstallsDialog(self.repo_root, self._editor_version, self).exec()

    def _check_runtime_ready(self, project_path: str) -> bool:
        try:
            resolved = resolve_project_runtime(project_path, repo_root=self.repo_root)
            if resolved.has_blocking_issues:
                QMessageBox.warning(
                    self,
                    "项目暂时无法打开",
                    resolved.blocking_issue_summary or resolved.lock_status_text,
                )
                return False
        except Exception as exc:
            QMessageBox.warning(self, "项目暂时无法打开", str(exc))
            return False
        return True

    def _open_project(self, project_path: str) -> None:
        if self._editor_process is not None:
            QMessageBox.information(self, "编辑器", "编辑器已在运行，请先关闭当前窗口。")
            return
        if not os.path.isfile(os.path.join(project_path, "project.json")):
            QMessageBox.warning(self, "项目无效", "项目目录中缺少 project.json。")
            return
        if not self._check_runtime_ready(project_path):
            return
        abspath = os.path.abspath(project_path)
        register_known_project(abspath)
        self.project_open_requested.emit(abspath)
        try:
            proc = start_editor_subprocess(abspath, parent=self)
        except RuntimeError as exc:
            QMessageBox.critical(self, "无法启动编辑器", str(exc))
            return
        self._editor_process = proc
        self._editor_project_path = abspath
        self._editor_output = bytearray()
        proc.readyReadStandardOutput.connect(self._on_editor_ready_read)  # type: ignore[arg-type]
        proc.finished.connect(self._on_editor_process_finished)  # type: ignore[arg-type]
        self._set_hub_busy(True, f"正在打开「{Path(abspath).name}」…")

    def _on_editor_ready_read(self) -> None:
        if self._editor_process is None:
            return
        chunk = bytes(self._editor_process.readAllStandardOutput())
        if not chunk:
            return
        self._editor_output.extend(chunk)
        if len(self._editor_output) > MAX_CAPTURED_OUTPUT_BYTES:
            del self._editor_output[:-MAX_CAPTURED_OUTPUT_BYTES]

    def _on_editor_process_finished(self, exit_code: int, _status) -> None:
        proc = self._editor_process
        if proc is not None:
            self._editor_output.extend(bytes(proc.readAllStandardOutput()))
        output = decode_process_output(bytes(self._editor_output))
        project_path = self._editor_project_path
        self._editor_process = None
        self._editor_project_path = ""
        self._editor_output = bytearray()
        self._set_hub_busy(False)
        self.refresh_projects()
        if exit_code == 0:
            self._status_label.setText("编辑器已关闭")
            return
        excerpt = failure_output_excerpt(output)
        try:
            log_path = write_editor_launch_log(
                project_path=project_path,
                exit_code=int(exit_code),
                output=output,
            )
        except OSError as exc:
            log_text = f"日志写入失败：{exc}"
        else:
            log_text = str(log_path)
        message = f"编辑器未能正常启动（退出码 {exit_code}）。"
        if excerpt:
            message += f"\n\n错误信息：\n{excerpt}"
        else:
            message += "\n\n没有收到错误输出。请检查项目文件是否完整后重试。"
        message += f"\n\n完整日志：\n{log_text}"
        self._status_label.setText("编辑器启动失败，详情见提示或日志")
        QMessageBox.warning(self, "编辑器启动失败", message)

    def _on_import(self) -> None:
        default_dir = str(projects_root() / "user")
        path = QFileDialog.getExistingDirectory(self, "导入项目", default_dir)
        if not path:
            return
        if not os.path.isfile(os.path.join(path, "project.json")):
            QMessageBox.warning(self, "导入失败", "所选目录中缺少 project.json。")
            return
        register_known_project(path)
        self.refresh_projects()
