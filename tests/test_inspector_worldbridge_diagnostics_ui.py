# -*- coding: utf-8 -*-
"""Real PyQt6 proof for command-backed WorldBridge Inspector diagnostics."""
from __future__ import annotations

import inspect
import os
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPlainTextEdit

from core.VitaLoom.docks.inspector import FoldoutGroup, InspectorPanel
from core.VitaLoom.inspector.worldbridge_diagnostics import (
    build_worldbridge_diagnostics_view_model,
)


class _DummyNode:
    def __init__(self, node_id: str = "node_1") -> None:
        self.id = node_id
        self.type = "node"
        self.x = 1.0
        self.y = 2.0
        self.scripts = []

    def update_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp: QApplication):
    widget = InspectorPanel()
    yield widget
    # InspectorPanel subscribes to process-wide Qt singletons. Keep teardown
    # non-destructive so this focused UI proof cannot invalidate those shared
    # QObject wrappers for test modules that run later in the same process.
    widget.hide()
    qapp.processEvents()


def _available_view_model(*, component_count: int = 0, warnings: list[str] | None = None):
    return build_worldbridge_diagnostics_view_model(
        {
            "ok": True,
            "result": {
                "status": "projection_diagnostics_ready",
                "diagnostic_state": "summary_only",
                "read_only": True,
                "maps_live_components": False,
                "default_ready": False,
                "component_count": component_count,
                "coverage": {"membrane": component_count},
                "safe_projection_fields": ["component_id", "component_type"],
                "forbidden_behavior": ["update", "mutate"],
                "do_not_claim": ["selected_entity_component_state"],
            },
            "events": [],
            "warnings": warnings or [],
            "error": None,
        }
    )


def _unavailable_view_model():
    return build_worldbridge_diagnostics_view_model(
        {
            "ok": False,
            "result": {},
            "events": [],
            "warnings": ["registry warning"],
            "error": {
                "code": "diagnostics_unavailable",
                "message": "projection evidence unavailable",
            },
        }
    )


def _diagnostics_group(panel: InspectorPanel) -> FoldoutGroup:
    group = panel.findChild(FoldoutGroup, "worldbridgeRuntimeDiagnosticsGroup")
    assert group is not None
    return group


def _layout_widgets(panel: InspectorPanel) -> list[object]:
    return [
        item.widget()
        for index in range(panel.properties_layout.count())
        if (item := panel.properties_layout.itemAt(index)) is not None
        and item.widget() is not None
    ]


def test_single_selection_appends_one_collapsed_runtime_group_after_normal_properties(
    panel: InspectorPanel,
    qapp: QApplication,
) -> None:
    loader = Mock(return_value=_available_view_model(component_count=0))
    with patch(
        "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
        loader,
    ):
        panel.update_properties(_DummyNode())

    loader.assert_called_once_with()
    assert "id" in panel._property_controls
    group = _diagnostics_group(panel)
    assert _layout_widgets(panel)[-1] is group
    assert group.title() == "WorldBridge Diagnostics (Runtime-wide)"
    assert group.objectName() == "worldbridgeRuntimeDiagnosticsGroup"
    assert group.is_expanded is False
    assert group.isChecked() is False

    panel.show()
    group.set_expanded(True)
    qapp.processEvents()
    assert panel.isVisible() is True
    assert group.isVisible() is True
    assert panel.grab().isNull() is False


def test_expanded_group_is_read_only_and_preserves_runtime_scope_authority_and_warnings(
    panel: InspectorPanel,
) -> None:
    loader = Mock(
        return_value=_available_view_model(
            component_count=0,
            warnings=["runtime evidence is summary-only"],
        )
    )
    with patch(
        "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
        loader,
    ):
        panel.update_properties(_DummyNode())

    group = _diagnostics_group(panel)
    group.set_expanded(True)

    hint = panel.findChild(
        QLabel,
        "worldbridgeRuntimeDiagnosticsHint",
    )
    assert hint is not None
    assert "Runtime-wide projection evidence" in hint.text()
    assert "not selected-entity component state" in hint.text()

    scope = panel._property_controls["worldbridge_diagnostics.scope"]
    authority = panel._property_controls["worldbridge_diagnostics.authority_command"]
    count_meaning = panel._property_controls[
        "worldbridge_diagnostics.component_count_meaning"
    ]
    warnings = panel._property_controls["worldbridge_diagnostics.warnings"]

    assert scope.text() == "runtime"
    assert authority.text() == "runtime.worldbridge.component_projection_diagnostics"
    assert count_meaning.text() == "No components in current runtime projection evidence."
    assert "selected entity has no components" not in count_meaning.text().lower()
    assert isinstance(warnings, QPlainTextEdit)
    assert "runtime evidence is summary-only" in warnings.toPlainText()

    diagnostic_widgets = [
        widget
        for key, widget in panel._property_controls.items()
        if key.startswith("worldbridge_diagnostics.")
    ]
    assert diagnostic_widgets
    assert all(
        widget.isReadOnly()
        for widget in diagnostic_widgets
        if isinstance(widget, (QLineEdit, QPlainTextEdit))
    )
    assert all(
        widget.objectName().startswith("worldbridgeRuntimeDiagnosticsField_")
        for widget in diagnostic_widgets
    )


def test_command_unavailable_keeps_ordinary_properties_and_renders_error(
    panel: InspectorPanel,
) -> None:
    with patch(
        "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
        return_value=_unavailable_view_model(),
    ):
        panel.update_properties(_DummyNode())

    assert "id" in panel._property_controls
    assert panel._property_controls["worldbridge_diagnostics.availability"].text() == "unavailable"
    assert (
        panel._property_controls["worldbridge_diagnostics.error_code"].text()
        == "diagnostics_unavailable"
    )
    assert (
        panel._property_controls["worldbridge_diagnostics.error_message"].text()
        == "projection evidence unavailable"
    )
    assert "registry warning" in panel._property_controls[
        "worldbridge_diagnostics.warnings"
    ].toPlainText()


def test_multi_selection_appends_diagnostics_once_after_common_properties(
    panel: InspectorPanel,
) -> None:
    loader = Mock(return_value=_available_view_model(component_count=2))
    with patch(
        "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
        loader,
    ):
        panel.update_properties([_DummyNode("node_1"), _DummyNode("node_2")])

    loader.assert_called_once_with()
    assert _layout_widgets(panel)[-1] is _diagnostics_group(panel)
    assert "worldbridge_diagnostics.component_count" in panel._property_controls


def test_no_selection_remains_empty_and_does_not_load_diagnostics(
    panel: InspectorPanel,
) -> None:
    loader = Mock(return_value=_available_view_model())
    with patch(
        "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
        loader,
    ):
        panel.update_properties(None)
        panel.update_properties([])

    loader.assert_not_called()
    assert panel.findChild(FoldoutGroup, "worldbridgeRuntimeDiagnosticsGroup") is None
    assert _layout_widgets(panel) == []


def test_ui_adapter_source_does_not_open_forbidden_semantics_paths() -> None:
    source = inspect.getsource(InspectorPanel._append_worldbridge_runtime_diagnostics)

    assert "load_worldbridge_diagnostics_view_model" in source
    assert "get_command_registry" not in source
    assert "bind_inspector_edit" not in source
    assert "world_bridge_component_projection" not in source
    assert ".pond" not in source
    assert "_on_property_changed" not in source
