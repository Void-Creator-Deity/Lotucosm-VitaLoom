"""细胞内部编辑视口：PS 组件图编辑（传感器/执行器/连接）。

当前 QWidget 内容仍是 PyQt legacy content bridge；稳定视口壳层由
``viewport_surface`` contribution 和当前 Host Adapter 投影。
"""
from __future__ import annotations

from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin

logger = get_logger("CellEditorPlugin")


class CellEditorPlugin(IRuntimePlugin):
    """细胞编辑器插件——保留当前占位内容与进入/退出切换语义。"""

    VIEWPORT_ID = "cell_editor"
    _EVENT_BINDINGS = (
        ("enter_cell_edit", "on_enter_cell_edit"),
        ("exit_cell_edit", "on_exit_cell_edit"),
        ("language_changed", "_on_language_changed"),
    )

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "CellEditorPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "细胞内部编辑视口，用于编辑细胞内组件和连接",
            "dependencies": [],
            "provides": ["viewport", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "cell_editor.surface",
                    "kind": "viewport_surface",
                    "viewport_id": self.VIEWPORT_ID,
                    "name_key": "cell_editor.name",
                    "default_name": "细胞编辑",
                    "order": 30,
                    "refresh_events": ["language_changed"],
                }
            ],
        }

    def on_load(self, editor_context) -> None:
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self.viewport: QWidget | None = None
        self._placeholder_label: QLabel | None = None
        self.current_cell: Any = None
        self._event_subscriptions: list[tuple[str, object]] = []

    def on_unload(self) -> None:
        errors = self._release_event_subscriptions()
        if errors:
            raise errors[0]

        # LayoutManager is the concrete viewport removal/deletion authority.
        # Clearing retained references here avoids a second deleteLater call.
        self.current_cell = None
        self.viewport = None
        self._placeholder_label = None

    def create_viewport_widget(self) -> QWidget:
        """Create the retained legacy content bridge exactly once per load."""
        existing = getattr(self, "viewport", None)
        if existing is not None:
            return existing

        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(self._idle_placeholder_text())
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #888;")
        label.setWordWrap(True)
        layout.addWidget(label)

        self.viewport = widget
        self._placeholder_label = label
        try:
            self._acquire_event_subscriptions()
        except BaseException:
            rollback_errors = self._release_event_subscriptions()
            if rollback_errors:
                logger.warning(
                    "CellEditor 激活回滚未完全释放，保留内容供 unload 重试: %s",
                    self._format_errors(rollback_errors),
                )
            else:
                widget.deleteLater()
                self.viewport = None
                self._placeholder_label = None
            raise
        return widget

    def get_viewport_id(self) -> str:
        """Legacy/community Host fallback; declarative Hosts use viewport_surface."""
        return self.VIEWPORT_ID

    def get_viewport_name(self) -> str:
        """Legacy/community Host fallback; declarative Hosts own the shell name."""
        return self._t("cell_editor.name", "细胞编辑")

    def on_viewport_activated(self) -> None:
        logger.debug(
            "🔬 %s",
            self._t("cell_editor.activated", "细胞编辑视口已激活"),
        )

    def on_viewport_deactivated(self) -> None:
        logger.debug(
            "🔬 %s",
            self._t("cell_editor.deactivated", "细胞编辑视口已停用"),
        )

    def on_enter_cell_edit(self, cell_data) -> None:
        self.current_cell = cell_data
        logger.info(
            self._t(
                "cell_editor.entering", "🔬 进入细胞编辑模式：{cell}"
            ).format(cell=cell_data)
        )
        self._refresh_placeholder_for_cell(cell_data)

        kernel = getattr(getattr(self, "context", None), "kernel", None)
        layout_manager = getattr(kernel, "layout_manager", None)
        switch = getattr(layout_manager, "switch_viewport", None)
        if callable(switch):
            switch(self.VIEWPORT_ID)

    def on_exit_cell_edit(self, _data) -> None:
        self.current_cell = None
        self.retranslate_ui()
        logger.info(
            "🔬 %s", self._t("cell_editor.exiting", "退出细胞编辑模式")
        )

        kernel = getattr(getattr(self, "context", None), "kernel", None)
        layout_manager = getattr(kernel, "layout_manager", None)
        switch = getattr(layout_manager, "switch_viewport", None)
        if callable(switch):
            switch("scene")

    def retranslate_ui(self) -> None:
        """Refresh retained content in place; the Host owns the tab label."""
        if self.current_cell is None:
            label = getattr(self, "_placeholder_label", None)
            if label is not None:
                label.setText(self._idle_placeholder_text())
            return
        self._refresh_placeholder_for_cell(self.current_cell)

    def _refresh_placeholder_for_cell(self, cell_data: Any) -> None:
        label = getattr(self, "_placeholder_label", None)
        if label is None:
            return
        name = ""
        entity_type = ""
        if isinstance(cell_data, dict):
            inner = (
                cell_data.get("data")
                if isinstance(cell_data.get("data"), dict)
                else cell_data
            )
            name = str(
                inner.get("entity_name")
                or inner.get("name")
                or inner.get("id")
                or ""
            )
            entity_type = str(
                inner.get("type") or inner.get("entity_type") or ""
            )
        title = name or self._t("cell_editor.unknown_cell", "未命名细胞")
        type_hint = f" ({entity_type})" if entity_type else ""
        label.setText(
            self._t(
                "cell_editor.placeholder_active",
                "细胞编辑视口\n\n当前：{title}{type_hint}\n\n"
                "完整组件图编辑尚未实现；可在层级面板返回场景视图。",
            ).format(title=title, type_hint=type_hint)
        )

    def _idle_placeholder_text(self) -> str:
        return self._t(
            "cell_editor.placeholder",
            "细胞编辑视口\n\n"
            "在层级面板双击一个细胞以编辑其内部结构。\n"
            "你可以在这里添加传感器、执行器和连接。",
        )

    def _acquire_event_subscriptions(self) -> None:
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        if not callable(subscribe):
            raise RuntimeError("event_bus.subscribe is unavailable")
        for event_name, callback_name in self._EVENT_BINDINGS:
            callback = getattr(self, callback_name)
            subscribe(event_name, callback)
            self._event_subscriptions.append((event_name, callback))

    def _release_event_subscriptions(self) -> list[BaseException]:
        errors: list[BaseException] = []
        subscriptions = getattr(self, "_event_subscriptions", [])
        bus = getattr(getattr(self, "context", None), "event_bus", None)
        unsubscribe = getattr(bus, "unsubscribe", None)
        if subscriptions and not callable(unsubscribe):
            return [RuntimeError("event_bus.unsubscribe is unavailable")]

        for index in range(len(subscriptions) - 1, -1, -1):
            event_name, callback = subscriptions[index]
            try:
                unsubscribe(event_name, callback)
            except BaseException as exc:
                errors.append(exc)
            else:
                subscriptions.pop(index)
        return errors

    def _on_language_changed(self, _data=None) -> None:
        self.retranslate_ui()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(getattr(self, "context", None), "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    @staticmethod
    def _format_errors(errors: list[BaseException]) -> str:
        return "; ".join(f"{type(exc).__name__}: {exc}" for exc in errors)
