# -*- coding: utf-8 -*-
"""Qt-free editor contribution facts for recursive VitaLoom plugin Hosts."""
from __future__ import annotations

import dataclasses
import importlib
import json
import sys
from pathlib import Path

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


def _valid_menu_command(**overrides):
    item = {
        "id": "language.zh_cn",
        "kind": "menu_command",
        "menu_path": [
            {
                "id": "tools",
                "label_key": "menu.tools",
                "default_label": "工具",
            },
            {
                "id": "language",
                "label_key": "menu.language",
                "default_label": "语言",
            },
        ],
        "label_key": "menu.language.zh",
        "default_label": "简体中文",
        "command_id": "editor.language.set",
        "command_payload": {"language": "zh_CN"},
        "order": 10,
    }
    item.update(overrides)
    return item


def _contract_module():
    return importlib.import_module(
        "core.VitaLoom.core.editor_contribution_contract"
    )


def test_menu_command_is_immutable_and_json_safe_plain_data() -> None:
    contract = _contract_module()

    contributions = contract.parse_editor_contributions(
        "LocalizationUIPlugin",
        [_valid_menu_command()],
    )

    assert isinstance(contributions, tuple)
    assert len(contributions) == 1
    contribution = contributions[0]
    assert contribution.owner_plugin_id == "LocalizationUIPlugin"
    assert contribution.id == "language.zh_cn"
    assert contribution.kind == "menu_command"
    assert contribution.menu_path[0].id == "tools"
    assert contribution.command_payload["language"] == "zh_CN"
    with pytest.raises(dataclasses.FrozenInstanceError):
        contribution.order = 20
    with pytest.raises(TypeError):
        contribution.command_payload["language"] = "en_US"

    observed = contribution.to_dict()
    assert json.loads(json.dumps(observed, ensure_ascii=False)) == observed
    assert observed["owner_plugin_id"] == "LocalizationUIPlugin"


def test_owner_is_canonicalized_from_host_argument() -> None:
    contract = _contract_module()

    contribution = contract.parse_editor_contributions(
        "LocalizationUI",
        [_valid_menu_command()],
    )[0]

    assert contribution.owner_plugin_id == "LocalizationUIPlugin"


def test_plugin_cannot_declare_or_forge_owner() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(owner_plugin_id="OtherPlugin")],
        )

    assert captured.value.code == "contribution_owner_forbidden"


def test_contributions_have_deterministic_order() -> None:
    contract = _contract_module()
    later = _valid_menu_command(
        id="language.en_us",
        label_key="menu.language.en",
        default_label="English",
        command_payload={"language": "en_US"},
        order=20,
    )
    same_order_later_id = _valid_menu_command(
        id="language.zh_tw",
        label_key="menu.language.zh_tw",
        default_label="繁體中文",
        command_payload={"language": "zh_TW"},
        order=10,
    )

    contributions = contract.parse_editor_contributions(
        "LocalizationUIPlugin",
        [later, same_order_later_id, _valid_menu_command()],
    )

    assert [item.id for item in contributions] == [
        "language.zh_cn",
        "language.zh_tw",
        "language.en_us",
    ]


def test_live_callback_is_rejected() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(action=lambda: None)],
        )

    assert captured.value.code == "contribution_live_value_forbidden"


def test_non_json_safe_native_object_is_rejected() -> None:
    contract = _contract_module()

    class FakeQWidget:
        pass

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(command_payload={"widget": FakeQWidget()})],
        )

    assert captured.value.code == "contribution_value_not_json_safe"


def test_live_plugin_instance_is_rejected() -> None:
    contract = _contract_module()

    class FakePlugin:
        def get_plugin_info(self):
            return {"name": "FakePlugin"}

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(plugin=FakePlugin())],
        )

    assert captured.value.code == "contribution_live_value_forbidden"


def test_duplicate_contribution_id_is_rejected() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(), _valid_menu_command(order=20)],
        )

    assert captured.value.code == "contribution_duplicate_id"


def test_unsupported_contribution_kind_is_rejected() -> None:
    contract = _contract_module()

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "LocalizationUIPlugin",
            [_valid_menu_command(kind="qt_widget_factory")],
        )

    assert captured.value.code == "contribution_kind_unsupported"


def test_contract_module_import_is_qt_free_and_not_an_alternate_host_or_registry() -> None:
    module_name = "core.VitaLoom.core.editor_contribution_contract"
    before_pyqt = {name for name in sys.modules if name.startswith("PyQt6")}

    module = importlib.import_module(module_name)

    after_pyqt = {name for name in sys.modules if name.startswith("PyQt6")}
    assert after_pyqt == before_pyqt
    source = Path(module.__file__).read_text(encoding="utf-8-sig")
    for forbidden in (
        "from PyQt6",
        "import PyQt6",
        "EditorKernel",
        "LayoutManager",
        "RuntimePluginHost",
        "NestedPluginHost",
        "ProjectScopedPluginHost",
        "class EditorContributionRegistry",
        "class EditorContributionHost",
    ):
        assert forbidden not in source