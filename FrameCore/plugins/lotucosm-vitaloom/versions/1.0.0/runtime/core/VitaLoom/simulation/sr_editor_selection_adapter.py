# -*- coding: utf-8 -*-
"""Qt-bound Adapter projecting heterogeneous editor selection to JSON facts."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.VitaLoom.tools.selection_tool import Node


def project_editor_selection(
    selected_objects: object,
    scene_path: object,
) -> dict[str, Any]:
    """Project EditorContext selection without exporting wrappers across the Seam."""
    if not isinstance(selected_objects, list):
        return {
            "selection_count": 0,
            "items": [],
            "projection_error": "selection_must_be_list",
        }

    normalized_scene_path = _nonempty_string(scene_path)
    items = [
        _project_item(item, normalized_scene_path)
        for item in selected_objects
    ]
    return {
        "selection_count": len(selected_objects),
        "items": items,
    }


def _project_item(item: object, scene_path: str | None) -> dict[str, str]:
    if isinstance(item, Node):
        entity_id = _nonempty_string(getattr(item, "id", None))
        if scene_path is None or entity_id is None:
            return {
                "kind": "invalid_scene_entity",
                "source": "scene_viewport_node",
                "reason": "missing_scene_or_entity_id",
            }
        return {
            "kind": "scene_entity",
            "scene_path": scene_path,
            "entity_id": entity_id,
            "source": "scene_viewport_node",
        }

    if isinstance(item, Mapping):
        item_type = _nonempty_string(item.get("type"))
        if item_type == "pond":
            return {"kind": "pond", "source": "hierarchy_pond"}
        if item_type == "entity":
            wrapper_id = _nonempty_string(item.get("id"))
            data = item.get("data")
            data_id = _nonempty_string(data.get("id")) if isinstance(data, Mapping) else None
            if wrapper_id is None or data_id is None:
                return {
                    "kind": "invalid_scene_entity",
                    "source": "hierarchy_entity",
                    "reason": "missing_entity_id",
                }
            if wrapper_id != data_id:
                return {
                    "kind": "invalid_scene_entity",
                    "source": "hierarchy_entity",
                    "reason": "inconsistent_entity_id",
                }
            if scene_path is None:
                return {
                    "kind": "invalid_scene_entity",
                    "source": "hierarchy_entity",
                    "reason": "missing_scene_or_entity_id",
                }
            return {
                "kind": "scene_entity",
                "scene_path": scene_path,
                "entity_id": wrapper_id,
                "source": "hierarchy_entity",
            }
        return {"kind": "unsupported", "source": "mapping"}

    return {"kind": "unsupported", "source": type(item).__name__}


def _nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
