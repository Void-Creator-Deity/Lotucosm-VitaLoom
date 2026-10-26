# -*- coding: utf-8 -*-
"""Qt-free viewport surface facts for the recursive engine plugin Host."""
from __future__ import annotations

import dataclasses
import importlib
import json

import pytest


def _contract_module():
    return importlib.import_module(
        "core.VitaLoom.core.editor_contribution_contract"
    )


def _valid_viewport_surface(**overrides):
    item = {
        "id": "cell_editor.surface",
        "kind": "viewport_surface",
        "viewport_id": "cell_editor",
        "name_key": "cell_editor.name",
        "default_name": "细胞编辑",
        "order": 30,
        "refresh_events": ["language_changed"],
    }
    item.update(overrides)
    return item


def test_viewport_surface_is_immutable_json_safe_and_host_owned() -> None:
    contract = _contract_module()

    contribution = contract.parse_editor_contributions(
        "CellEditor",
        [_valid_viewport_surface()],
    )[0]

    assert isinstance(contribution, contract.EditorViewportSurfaceContribution)
    assert contribution.owner_plugin_id == "CellEditorPlugin"
    assert contribution.kind == "viewport_surface"
    assert contribution.viewport_id == "cell_editor"
    assert contribution.name_key == "cell_editor.name"
    assert contribution.default_name == "细胞编辑"
    assert contribution.order == 30
    assert contribution.refresh_events == ("language_changed",)
    with pytest.raises(dataclasses.FrozenInstanceError):
        contribution.order = 31

    observed = contribution.to_dict()
    assert json.loads(json.dumps(observed, ensure_ascii=False)) == observed
    assert observed == {
        "owner_plugin_id": "CellEditorPlugin",
        "id": "cell_editor.surface",
        "kind": "viewport_surface",
        "viewport_id": "cell_editor",
        "name_key": "cell_editor.name",
        "default_name": "细胞编辑",
        "order": 30,
        "refresh_events": ["language_changed"],
    }


def test_viewport_surface_ordering_and_defaults_are_deterministic() -> None:
    contract = _contract_module()
    first = _valid_viewport_surface(
        id="alpha.surface",
        viewport_id="alpha",
        name_key="alpha.name",
        default_name="Alpha",
        order=10,
    )
    first.pop("refresh_events")
    second = _valid_viewport_surface(order=30)

    contributions = contract.parse_editor_contributions(
        "CellEditorPlugin",
        [second, first],
    )

    assert [item.viewport_id for item in contributions] == ["alpha", "cell_editor"]
    assert contributions[0].refresh_events == ()


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("widget", object(), "contribution_viewport_field_unknown"),
        ("factory", lambda: None, "contribution_live_value_forbidden"),
        ("provider", type("LivePlugin", (), {"get_plugin_info": lambda self: {}})(), "contribution_live_value_forbidden"),
        ("viewport_id", "../cell_editor", "contribution_viewport_id_invalid"),
        ("name_key", "cell editor name", "contribution_viewport_name_key_invalid"),
        ("order", True, "contribution_order_invalid"),
        ("refresh_events", "language_changed", "contribution_event_invalid"),
        ("refresh_events", ["language changed"], "contribution_event_invalid"),
        ("refresh_events", ["language_changed", "language_changed"], "contribution_event_duplicate"),
    ],
)
def test_viewport_surface_rejects_live_values_and_nonportable_facts(
    field, value, expected_code
) -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "CellEditorPlugin",
            [_valid_viewport_surface(**{field: value})],
        )

    assert captured.value.code == expected_code


def test_viewport_surface_rejects_forged_owner_unknown_fields_and_duplicate_ids() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "CellEditorPlugin",
            [_valid_viewport_surface(owner_plugin_id="OtherPlugin")],
        )
    assert captured.value.code == "contribution_owner_forbidden"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "CellEditorPlugin",
            [_valid_viewport_surface(renderer="opengl")],
        )
    assert captured.value.code == "contribution_viewport_field_unknown"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "CellEditorPlugin",
            [
                _valid_viewport_surface(),
                _valid_viewport_surface(id="cell_editor.alias"),
            ],
        )
    assert captured.value.code == "contribution_duplicate_viewport_id"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "CellEditorPlugin",
            [
                _valid_viewport_surface(),
                _valid_viewport_surface(viewport_id="cell_editor_alt"),
            ],
        )
    assert captured.value.code == "contribution_duplicate_id"


def test_existing_contribution_kinds_remain_supported_and_contract_stays_qt_free() -> None:
    contract = _contract_module()

    assert contract.SUPPORTED_EDITOR_CONTRIBUTION_KINDS == frozenset(
        {
            "menu_command",
            "menu_separator",
            "toolbar_command",
            "toolbar_separator",
            "dock_surface",
            "viewport_surface",
            "theme_profile",
        }
    )
    source = open(contract.__file__, encoding="utf-8-sig").read()
    for forbidden in (
        "PyQt6",
        "QDockWidget",
        "QWidget",
        "LayoutManager",
        "create_viewport_widget",
    ):
        assert forbidden not in source
