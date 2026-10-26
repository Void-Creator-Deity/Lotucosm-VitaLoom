# -*- coding: utf-8 -*-
"""E43 CellEditor viewport shell, retained localization, and exact events."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _EventBus:
    def __init__(
        self,
        *,
        fail_subscribe_on: str | None = None,
        fail_unsubscribe_once_on: str | None = None,
    ) -> None:
        self.fail_subscribe_on = fail_subscribe_on
        self.fail_unsubscribe_once_on = fail_unsubscribe_once_on
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        if event_name == self.fail_subscribe_on:
            raise RuntimeError(f"subscribe failed: {event_name}")
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        if event_name == self.fail_unsubscribe_once_on:
            self.fail_unsubscribe_once_on = None
            raise RuntimeError(f"unsubscribe failed: {event_name}")
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Viewport:
    instances: list['_Viewport'] = []

    def __init__(self) -> None:
        self.deleted = 0
        self.instances.append(self)

    def deleteLater(self) -> None:
        self.deleted += 1


class _Label:
    def __init__(self, text: str) -> None:
        self._text = text
        self.alignment = None
        self.stylesheet = ""
        self.word_wrap = False

    def setAlignment(self, value) -> None:
        self.alignment = value

    def setStyleSheet(self, value: str) -> None:
        self.stylesheet = value

    def setWordWrap(self, value: bool) -> None:
        self.word_wrap = value

    def setText(self, value: str) -> None:
        self._text = value

    def text(self) -> str:
        return self._text


class _VBoxLayout:
    def __init__(self, viewport: _Viewport) -> None:
        self.viewport = viewport
        self.widgets: list[object] = []

    def addWidget(self, widget: object) -> None:
        self.widgets.append(widget)


class _LayoutManager:
    def __init__(self) -> None:
        self.switch_calls: list[str] = []

    def switch_viewport(self, viewport_id: str) -> None:
        self.switch_calls.append(viewport_id)


def _load_plugin(
    monkeypatch,
    *,
    bus: _EventBus | None = None,
    translations: dict[str, str] | None = None,
):
    import builtin.editor_extensions.cell_editor_plugin as module

    bus = bus or _EventBus()
    translations = translations or {}
    layout_manager = _LayoutManager()
    kernel = SimpleNamespace(layout_manager=layout_manager)
    context = SimpleNamespace(
        event_bus=bus,
        kernel=kernel,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    monkeypatch.setattr(module, "QWidget", _Viewport)
    monkeypatch.setattr(module, "QLabel", _Label)
    monkeypatch.setattr(module, "QVBoxLayout", _VBoxLayout)
    monkeypatch.setattr(
        module,
        "Qt",
        SimpleNamespace(AlignmentFlag=SimpleNamespace(AlignCenter="center")),
    )
    plugin = module.CellEditorPlugin()
    plugin.on_load(context)
    return module, plugin, context, bus, layout_manager, translations


def test_cell_editor_declares_one_qt_free_viewport_shell() -> None:
    from builtin.editor_extensions.cell_editor_plugin import CellEditorPlugin

    info = CellEditorPlugin().get_plugin_info()
    assert info["provides"] == ["viewport", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "cell_editor.surface",
            "kind": "viewport_surface",
            "viewport_id": "cell_editor",
            "name_key": "cell_editor.name",
            "default_name": "细胞编辑",
            "order": 30,
            "refresh_events": ["language_changed"],
        }
    ]


def test_create_is_idempotent_and_plugin_owns_exact_events_once(monkeypatch) -> None:
    _module, plugin, _context, bus, _layout, _translations = _load_plugin(monkeypatch)

    viewport = plugin.create_viewport_widget()
    label = plugin._placeholder_label

    assert plugin.create_viewport_widget() is viewport
    assert plugin._placeholder_label is label
    assert [name for name, _callback in bus.subscribe_calls] == [
        "enter_cell_edit",
        "exit_cell_edit",
        "language_changed",
    ]

    plugin.on_unload()

    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed",
        "exit_cell_edit",
        "enter_cell_edit",
    ]
    assert plugin._event_subscriptions == []
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert viewport.deleted == 0
    assert plugin.viewport is None
    assert plugin._placeholder_label is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 3
    assert viewport.deleted == 0


def test_partial_subscription_failure_rolls_back_and_discards_unprojected_widget(
    monkeypatch,
) -> None:
    bus = _EventBus(fail_subscribe_on="language_changed")
    _module, plugin, _context, _bus, _layout, _translations = _load_plugin(
        monkeypatch, bus=bus
    )

    with pytest.raises(RuntimeError, match="subscribe failed: language_changed"):
        plugin.create_viewport_widget()

    assert [name for name, _callback in bus.subscribe_calls] == [
        "enter_cell_edit",
        "exit_cell_edit",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "exit_cell_edit",
        "enter_cell_edit",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin._event_subscriptions == []
    assert plugin.viewport is None
    assert plugin._placeholder_label is None
    assert _Viewport.instances[-1].deleted == 1


def test_failed_unsubscribe_retains_only_exact_event_for_retry(monkeypatch) -> None:
    bus = _EventBus(fail_unsubscribe_once_on="exit_cell_edit")
    _module, plugin, _context, _bus, _layout, _translations = _load_plugin(
        monkeypatch, bus=bus
    )
    viewport = plugin.create_viewport_widget()
    label = plugin._placeholder_label

    with pytest.raises(RuntimeError, match="unsubscribe failed: exit_cell_edit"):
        plugin.on_unload()

    assert [name for name, _callback in plugin._event_subscriptions] == [
        "exit_cell_edit"
    ]
    assert plugin.viewport is viewport
    assert plugin._placeholder_label is label
    assert viewport.deleted == 0
    assert len(bus.callbacks["exit_cell_edit"]) == 1
    assert bus.callbacks["enter_cell_edit"] == []
    assert bus.callbacks["language_changed"] == []

    plugin.on_unload()

    assert plugin._event_subscriptions == []
    assert plugin.viewport is None
    assert plugin._placeholder_label is None
    assert viewport.deleted == 0
    assert all(not callbacks for callbacks in bus.callbacks.values())


def test_language_refresh_preserves_widget_label_and_active_cell_identity(
    monkeypatch,
) -> None:
    translations: dict[str, str] = {}
    _module, plugin, _context, bus, layout, translations = _load_plugin(
        monkeypatch,
        translations=translations,
    )
    viewport = plugin.create_viewport_widget()
    label = plugin._placeholder_label
    cell = {"data": {"entity_name": "Lotus-7", "type": "sensor"}}

    bus.publish("enter_cell_edit", cell)
    assert plugin.current_cell is cell
    assert layout.switch_calls == ["cell_editor"]
    assert label is not None and "Lotus-7" in label.text()
    assert "sensor" in label.text()

    translations.update(
        {
            "cell_editor.placeholder_active": "Editing {title}{type_hint}",
            "cell_editor.unknown_cell": "Unnamed",
        }
    )
    bus.publish("language_changed")

    assert plugin.viewport is viewport
    assert plugin._placeholder_label is label
    assert plugin.current_cell is cell
    assert label.text() == "Editing Lotus-7 (sensor)"

    bus.publish("exit_cell_edit", None)
    assert plugin.current_cell is None
    assert layout.switch_calls == ["cell_editor", "scene"]

    translations["cell_editor.placeholder"] = "Choose a cell"
    bus.publish("language_changed")
    assert plugin.viewport is viewport
    assert plugin._placeholder_label is label
    assert label.text() == "Choose a cell"


def test_language_content_refresh_does_not_reach_into_host_tabs() -> None:
    source = (
        RUNTIME / "builtin" / "editor_extensions" / "cell_editor_plugin.py"
    ).read_text(encoding="utf-8-sig")

    assert "viewport_tabs" not in source
    assert "setTabText" not in source


