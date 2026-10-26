# -*- coding: utf-8 -*-
"""Offscreen PyQt proof for selected-SR component projection Inspector UI."""
from __future__ import annotations

import inspect
import os
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPlainTextEdit

from core.VitaLoom.docks.inspector import FoldoutGroup, InspectorPanel
from core.VitaLoom.inspector.sr_selected_component_projection import (
    build_sr_selected_component_projection_view_model,
)
from core.VitaLoom.inspector.worldbridge_diagnostics import (
    build_worldbridge_diagnostics_view_model,
)


class _DummyNode:
    def __init__(self, node_id: str = "org_1") -> None:
        self.id = node_id
        self.type = "organism"
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
    widget.hide()
    qapp.processEvents()


def _selected_view_model(*, status: str = "ok", component_count: int | None = 1):
    ok = status == "ok"
    components = []
    coverage = {}
    if ok:
        components = [
            {
                "projection_state": "runtime_snapshot_read_only_projection",
                "maps_live_components": False,
                "source": "sr_attached_runtime_entity",
                "identity_relation": "attached_projection_not_ps_component_equivalence",
                "component_id": "sensor_1",
                "component_type": "sensor",
                "location": "attached",
                "attach_point": [1.0, 2.0],
                "connection_count": 1,
                "inspectable_properties": {"sensing_range": 16.0},
                "component_fields": {},
            }
        ]
        coverage = {"sensor": 1}
    return build_sr_selected_component_projection_view_model(
        {
            "ok": True,
            "result": {
                "schema_version": 1,
                "status": status,
                "reason": None if ok else "component_facts_unavailable",
                "scope": "runtime_snapshot_component_projection",
                "authority": "runtime_snapshot_component_projection",
                "track": "sr_play",
                "read_only": True,
                "projection_state": "runtime_snapshot_read_only_projection",
                "maps_live_components": False,
                "maps_live_runtime_snapshot_facts": ok,
                "identity_relation": "attached_projection_not_ps_component_equivalence",
                "identity": {
                    "track": "sr_play",
                    "runtime_epoch": "sr_epoch_1",
                    "scene_path": "scenes/demo.pond",
                    "entity_id": "org_1",
                },
                "revision": 7,
                "component_count": component_count,
                "coverage": coverage,
                "components": components,
                "do_not_claim": ["ps_component_equivalence"],
            },
            "events": [],
            "warnings": ["runtime snapshot evidence"],
            "error": None,
        }
    )


def _selected_unavailable_view_model():
    return build_sr_selected_component_projection_view_model(
        {
            "ok": False,
            "result": {},
            "events": [],
            "warnings": ["registry warning"],
            "error": {
                "code": "selected_projection_unavailable",
                "message": "projection unavailable",
            },
        }
    )


def _runtime_view_model():
    return build_worldbridge_diagnostics_view_model(
        {
            "ok": True,
            "result": {
                "status": "projection_diagnostics_ready",
                "diagnostic_state": "summary_only",
                "read_only": True,
                "maps_live_components": False,
                "default_ready": False,
                "component_count": 0,
                "coverage": {},
                "safe_projection_fields": [],
                "forbidden_behavior": [],
                "do_not_claim": ["selected_entity_component_state"],
            },
            "events": [],
            "warnings": [],
            "error": None,
        }
    )


def _group(panel: InspectorPanel, name: str) -> FoldoutGroup:
    group = panel.findChild(FoldoutGroup, name)
    assert group is not None
    return group


def _layout_widgets(panel: InspectorPanel) -> list[object]:
    return [
        item.widget()
        for index in range(panel.properties_layout.count())
        if (item := panel.properties_layout.itemAt(index)) is not None
        and item.widget() is not None
    ]


def test_single_selection_appends_distinct_selected_group_and_preserves_runtime_group(
    panel: InspectorPanel,
    qapp: QApplication,
) -> None:
    selected_loader = Mock(return_value=_selected_view_model())
    runtime_loader = Mock(return_value=_runtime_view_model())
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            selected_loader,
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            runtime_loader,
        ),
    ):
        panel.update_properties(_DummyNode())

    selected_loader.assert_called_once_with()
    runtime_loader.assert_called_once_with()
    assert "id" in panel._property_controls
    selected_group = _group(panel, "worldbridgeSrSelectedComponentProjectionGroup")
    runtime_group = _group(panel, "worldbridgeRuntimeDiagnosticsGroup")
    widgets = _layout_widgets(panel)
    assert widgets.index(selected_group) < widgets.index(runtime_group)
    assert selected_group.title() == "WorldBridge Components (Selected SR Runtime Entity)"
    assert selected_group.is_expanded is False
    assert runtime_group.title() == "WorldBridge Diagnostics (Runtime-wide)"

    panel.show()
    selected_group.set_expanded(True)
    qapp.processEvents()
    assert panel.isVisible() is True
    assert selected_group.isVisible() is True
    assert panel.grab().isNull() is False


def test_expanded_selected_group_is_read_only_and_explains_non_equivalence(
    panel: InspectorPanel,
) -> None:
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            return_value=_selected_view_model(),
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            return_value=_runtime_view_model(),
        ),
    ):
        panel.update_properties(_DummyNode())

    group = _group(panel, "worldbridgeSrSelectedComponentProjectionGroup")
    group.set_expanded(True)
    hint = panel.findChild(QLabel, "worldbridgeSrSelectedComponentProjectionHint")
    assert hint is not None
    assert "SR attachment projection" in hint.text()
    assert "not PS Component equivalence" in hint.text()

    assert panel._property_controls["worldbridge_sr_selected.scope"].text() == (
        "selected_sr_runtime_entity"
    )
    assert panel._property_controls["worldbridge_sr_selected.status"].text() == "ok"
    component = panel._property_controls["worldbridge_sr_selected.component.sensor_1"]
    warnings = panel._property_controls["worldbridge_sr_selected.warnings"]
    assert isinstance(component, QPlainTextEdit)
    assert '"component_id": "sensor_1"' in component.toPlainText()
    assert isinstance(warnings, QPlainTextEdit)
    assert "not PS Component equivalence" in warnings.toPlainText()

    widgets = [
        widget
        for key, widget in panel._property_controls.items()
        if key.startswith("worldbridge_sr_selected.")
    ]
    assert widgets
    assert all(
        widget.isReadOnly()
        for widget in widgets
        if isinstance(widget, (QLineEdit, QPlainTextEdit))
    )
    assert all(
        widget.objectName().startswith("worldbridgeSrSelectedComponentProjectionField_")
        for widget in widgets
    )


def test_not_proven_renders_unknown_not_zero(panel: InspectorPanel) -> None:
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            return_value=_selected_view_model(status="not_proven", component_count=None),
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            return_value=_runtime_view_model(),
        ),
    ):
        panel.update_properties(_DummyNode())

    meaning = panel._property_controls[
        "worldbridge_sr_selected.component_count_meaning"
    ].text()
    assert "unknown" in meaning.lower()
    assert "zero" not in meaning.lower()


def test_selected_command_unavailable_keeps_ordinary_properties(panel: InspectorPanel) -> None:
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            return_value=_selected_unavailable_view_model(),
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            return_value=_runtime_view_model(),
        ),
    ):
        panel.update_properties(_DummyNode())

    assert "id" in panel._property_controls
    assert panel._property_controls["worldbridge_sr_selected.availability"].text() == (
        "unavailable"
    )
    assert panel._property_controls["worldbridge_sr_selected.error_code"].text() == (
        "selected_projection_unavailable"
    )


def test_multi_selection_does_not_load_selected_projection(panel: InspectorPanel) -> None:
    selected_loader = Mock(return_value=_selected_view_model())
    runtime_loader = Mock(return_value=_runtime_view_model())
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            selected_loader,
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            runtime_loader,
        ),
    ):
        panel.update_properties([_DummyNode("org_1"), _DummyNode("org_2")])

    selected_loader.assert_not_called()
    runtime_loader.assert_called_once_with()
    assert panel.findChild(
        FoldoutGroup,
        "worldbridgeSrSelectedComponentProjectionGroup",
    ) is None


def test_no_selection_does_not_load_selected_or_runtime_projection(panel: InspectorPanel) -> None:
    selected_loader = Mock(return_value=_selected_view_model())
    runtime_loader = Mock(return_value=_runtime_view_model())
    with (
        patch(
            "core.VitaLoom.docks.inspector.load_sr_selected_component_projection_view_model",
            selected_loader,
        ),
        patch(
            "core.VitaLoom.docks.inspector.load_worldbridge_diagnostics_view_model",
            runtime_loader,
        ),
    ):
        panel.update_properties(None)
        panel.update_properties([])

    selected_loader.assert_not_called()
    runtime_loader.assert_not_called()
    assert _layout_widgets(panel) == []


def test_selected_ui_adapter_source_stays_thin_and_read_only() -> None:
    source = inspect.getsource(
        InspectorPanel._append_sr_selected_component_projection
    )

    assert "load_sr_selected_component_projection_view_model" in source
    assert "get_command_registry" not in source
    assert "bind_inspector_edit" not in source
    assert "runtime_snapshot_component_projection" not in source
    assert "sr_selected_identity_host" not in source
    assert ".pond" not in source
    assert "_on_property_changed" not in source
