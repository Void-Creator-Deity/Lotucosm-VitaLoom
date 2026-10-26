# -*- coding: utf-8 -*-
"""GUI-side selection projection Adapter for selected SR identity."""
from __future__ import annotations

import os

import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.simulation.sr_editor_selection_adapter import (
    project_editor_selection,
)
from core.VitaLoom.tools.selection_tool import Node


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def test_scene_viewport_node_projects_to_json_scene_entity() -> None:
    node = Node("entity_1", 10.0, 20.0, "organism")

    result = project_editor_selection([node], "scenes/demo.pond")

    assert result == {
        "selection_count": 1,
        "items": [
            {
                "kind": "scene_entity",
                "scene_path": "scenes/demo.pond",
                "entity_id": "entity_1",
                "source": "scene_viewport_node",
            }
        ],
    }


def test_hierarchy_entity_wrapper_projects_only_consistent_id() -> None:
    entity = {"id": "entity_1", "type": "organism", "scripts": [object()]}
    wrapper = {"type": "entity", "id": "entity_1", "data": entity}

    result = project_editor_selection([wrapper], "scenes/demo.pond")

    assert result["items"] == [
        {
            "kind": "scene_entity",
            "scene_path": "scenes/demo.pond",
            "entity_id": "entity_1",
            "source": "hierarchy_entity",
        }
    ]


def test_adapter_does_not_guess_pond_string_or_arbitrary_objects() -> None:
    class IdLike:
        id = "entity_1"

    result = project_editor_selection(
        [
            {"type": "pond", "path": "scenes/demo.pond"},
            "entity_1",
            IdLike(),
        ],
        "scenes/demo.pond",
    )

    assert result["selection_count"] == 3
    assert [item["kind"] for item in result["items"]] == [
        "pond",
        "unsupported",
        "unsupported",
    ]
    assert "object" not in result["items"][2]


def test_malformed_hierarchy_entity_is_explicitly_invalid() -> None:
    result = project_editor_selection(
        [
            {"type": "entity", "id": "entity_1", "data": {"id": "different"}},
        ],
        "scenes/demo.pond",
    )

    assert result["items"] == [
        {
            "kind": "invalid_scene_entity",
            "source": "hierarchy_entity",
            "reason": "inconsistent_entity_id",
        }
    ]


def test_projection_is_json_only_and_requires_scene_path() -> None:
    node = Node("entity_1", 0.0, 0.0)
    assert project_editor_selection([node], "")["items"][0]["kind"] == "invalid_scene_entity"

    result = project_editor_selection([node], "scenes/demo.pond")
    import json

    json.dumps(result, ensure_ascii=False, allow_nan=False)
