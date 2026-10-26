# -*- coding: utf-8 -*-
"""Qt-free command toolbar contribution contract for the recursive engine Host."""
from __future__ import annotations

import dataclasses
import importlib
import json

import pytest


def _contract_module():
    return importlib.import_module(
        "core.VitaLoom.core.editor_contribution_contract"
    )


def _valid_toolbar_command(**overrides):
    item = {
        "id": "simulation.toggle",
        "kind": "toolbar_command",
        "label_key": "toolbar.play",
        "default_label": "运行",
        "command_id": "simulation.toggle",
        "command_payload": {},
        "icon": "media-playback-start",
        "group": "simulation",
        "order": 20,
        "state": {
            "command_id": "simulation.transport.status",
            "result_field": "phase",
            "label_variants": {
                "stopped": {
                    "label_key": "toolbar.play",
                    "default_label": "运行",
                },
                "playing": {
                    "label_key": "toolbar.pause",
                    "default_label": "暂停",
                },
                "paused": {
                    "label_key": "toolbar.resume",
                    "default_label": "继续",
                },
            },
            "refresh_events": ["simulation_transport_state"],
        },
    }
    item.update(overrides)
    return item


def test_toolbar_command_is_immutable_json_safe_and_host_owned() -> None:
    contract = _contract_module()

    contribution = contract.parse_editor_contributions(
        "StandardUI",
        [_valid_toolbar_command()],
    )[0]

    assert isinstance(contribution, contract.EditorToolbarCommandContribution)
    assert contribution.owner_plugin_id == "StandardUIPlugin"
    assert contribution.kind == "toolbar_command"
    assert contribution.icon == "media-playback-start"
    assert contribution.group == "simulation"
    assert contribution.state is not None
    assert contribution.state.command_id == "simulation.transport.status"
    assert contribution.state.result_field == "phase"
    assert contribution.state.refresh_events == ("simulation_transport_state",)
    assert contribution.state.label_variants["playing"].label_key == "toolbar.pause"
    with pytest.raises(dataclasses.FrozenInstanceError):
        contribution.order = 30
    with pytest.raises(TypeError):
        contribution.state.label_variants["playing"] = object()

    observed = contribution.to_dict()
    assert json.loads(json.dumps(observed, ensure_ascii=False)) == observed
    assert observed["owner_plugin_id"] == "StandardUIPlugin"


def test_static_toolbar_command_can_omit_state() -> None:
    contract = _contract_module()
    raw = _valid_toolbar_command(
        id="simulation.stop",
        label_key="toolbar.stop",
        default_label="停止",
        command_id="simulation.stop",
        icon="media-playback-stop",
        order=30,
    )
    raw.pop("state")

    contribution = contract.parse_editor_contributions(
        "StandardUIPlugin",
        [raw],
    )[0]

    assert contribution.state is None
    assert contribution.to_dict().get("state") is None


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("action", lambda: None, "contribution_live_value_forbidden"),
        ("icon", object(), "contribution_value_not_json_safe"),
        ("icon", "../native/icon", "contribution_icon_invalid"),
        ("group", "simulation/widgets", "contribution_group_invalid"),
    ],
)
def test_toolbar_rejects_callbacks_native_icons_and_nonportable_tokens(
    field, value, expected_code
) -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "StandardUIPlugin",
            [_valid_toolbar_command(**{field: value})],
        )

    assert captured.value.code == expected_code


def test_toolbar_state_rejects_arbitrary_callable_and_unknown_fields() -> None:
    contract = _contract_module()
    state = _valid_toolbar_command()["state"]

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "StandardUIPlugin",
            [
                _valid_toolbar_command(
                    state={**state, "resolver": lambda: "playing"}
                )
            ],
        )
    assert captured.value.code == "contribution_live_value_forbidden"

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "StandardUIPlugin",
            [_valid_toolbar_command(state={**state, "expression": "phase == 1"})],
        )
    assert captured.value.code == "contribution_toolbar_state_field_unknown"


@pytest.mark.parametrize(
    "state_override",
    [
        {"result_field": "phase.deep"},
        {"label_variants": {}},
        {"refresh_events": []},
        {"refresh_events": ["simulation transport state"]},
        {
            "label_variants": {
                "playing": {"label_key": "toolbar.pause"},
            }
        },
    ],
)
def test_toolbar_dynamic_label_mapping_fails_closed_on_invalid_shape(
    state_override,
) -> None:
    contract = _contract_module()
    state = _valid_toolbar_command()["state"]

    with pytest.raises(contract.EditorContributionContractError):
        contract.parse_editor_contributions(
            "StandardUIPlugin",
            [_valid_toolbar_command(state={**state, **state_override})],
        )


def test_mixed_menu_and_toolbar_contributions_keep_deterministic_order() -> None:
    contract = _contract_module()
    menu = {
        "id": "language.zh_cn",
        "kind": "menu_command",
        "menu_path": [
            {
                "id": "tools",
                "label_key": "menu.tools",
                "default_label": "工具",
            }
        ],
        "label_key": "menu.language.zh",
        "default_label": "简体中文",
        "command_id": "editor.language.set",
        "command_payload": {"language": "zh_CN"},
        "order": 10,
    }

    contributions = contract.parse_editor_contributions(
        "StandardUIPlugin",
        [_valid_toolbar_command(order=20), menu],
    )

    assert [item.id for item in contributions] == [
        "language.zh_cn",
        "simulation.toggle",
    ]
