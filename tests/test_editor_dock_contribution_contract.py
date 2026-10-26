# -*- coding: utf-8 -*-
"""Qt-free dock surface facts for the recursive engine plugin Host."""
from __future__ import annotations

import dataclasses
import importlib
import json

import pytest


def _contract_module():
    return importlib.import_module(
        "core.VitaLoom.core.editor_contribution_contract"
    )


def _valid_dock_surface(**overrides):
    item = {
        "id": "inspector.surface",
        "kind": "dock_surface",
        "dock_id": "Inspector",
        "title_key": "inspector.title",
        "default_title": "检视器",
        "area": "right",
        "default_visible": True,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": None,
        "order": 40,
        "refresh_events": ["language_changed"],
    }
    item.update(overrides)
    return item


def test_dock_surface_is_immutable_json_safe_and_host_owned() -> None:
    contract = _contract_module()

    contribution = contract.parse_editor_contributions(
        "Inspector",
        [_valid_dock_surface()],
    )[0]

    assert isinstance(contribution, contract.EditorDockSurfaceContribution)
    assert contribution.owner_plugin_id == "InspectorPlugin"
    assert contribution.kind == "dock_surface"
    assert contribution.dock_id == "Inspector"
    assert contribution.area == "right"
    assert contribution.refresh_events == ("language_changed",)
    with pytest.raises(dataclasses.FrozenInstanceError):
        contribution.area = "left"

    observed = contribution.to_dict()
    assert json.loads(json.dumps(observed, ensure_ascii=False)) == observed
    assert observed["owner_plugin_id"] == "InspectorPlugin"
    assert observed["tabbed_with"] is None


def test_dock_surface_defaults_are_closed_and_deterministic() -> None:
    contract = _contract_module()
    first = _valid_dock_surface(
        id="console.surface",
        dock_id="Console",
        title_key="console.title",
        default_title="控制台",
        area="bottom",
        order=20,
        tabbed_with="Project",
        refresh_events=[],
    )
    second = _valid_dock_surface(order=40)
    for field in ("can_close", "can_float", "can_move"):
        first.pop(field)

    contributions = contract.parse_editor_contributions(
        "InspectorPlugin",
        [second, first],
    )

    assert [item.dock_id for item in contributions] == ["Console", "Inspector"]
    assert contributions[0].can_close is True
    assert contributions[0].can_float is True
    assert contributions[0].can_move is True
    assert contributions[0].tabbed_with == "Project"


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("widget", object(), "contribution_dock_field_unknown"),
        ("factory", lambda: None, "contribution_live_value_forbidden"),
        ("area", "center", "contribution_dock_area_invalid"),
        ("dock_id", "../Inspector", "contribution_dock_id_invalid"),
        ("tabbed_with", "Project/Console", "contribution_dock_tab_invalid"),
        ("refresh_events", ["language changed"], "contribution_event_invalid"),
        ("can_close", 1, "contribution_dock_flag_invalid"),
    ],
)
def test_dock_surface_rejects_live_values_and_nonportable_facts(
    field, value, expected_code
) -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "InspectorPlugin",
            [_valid_dock_surface(**{field: value})],
        )

    assert captured.value.code == expected_code


def test_dock_surface_rejects_forged_owner_unknown_fields_and_duplicate_dock_id() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "InspectorPlugin",
            [_valid_dock_surface(owner_plugin_id="OtherPlugin")],
        )
    assert captured.value.code == "contribution_owner_forbidden"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "InspectorPlugin",
            [_valid_dock_surface(expression="visible == true")],
        )
    assert captured.value.code == "contribution_dock_field_unknown"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "InspectorPlugin",
            [
                _valid_dock_surface(),
                _valid_dock_surface(id="inspector.alias"),
            ],
        )
    assert captured.value.code == "contribution_duplicate_dock_id"


def test_contract_module_remains_qt_free() -> None:
    contract = _contract_module()
    source = open(contract.__file__, encoding="utf-8-sig").read()

    for forbidden in ("PyQt6", "QDockWidget", "QWidget", "LayoutManager"):
        assert forbidden not in source
