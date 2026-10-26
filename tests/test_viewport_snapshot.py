# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportCameraSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
    build_viewport_entity_snapshot,
    build_viewport_frame_snapshot,
)


class _Entity:
    def __init__(self) -> None:
        self.id = "sensor_1"
        self.entity_type = "sensor"
        self.position = [12, "34.5"]
        self.velocity = (1, -2.5)
        self.radius = "9.25"
        self.selected = True
        self.visible = False
        self.pinned = True
        self.membrane_locked = True
        self.visual_state = {"energy": 0.8, "tags": ["warm", "active"]}


def test_entity_snapshot_copies_primitives_without_live_entity_reference() -> None:
    entity = _Entity()

    snapshot = build_viewport_entity_snapshot(entity)
    entity.position[0] = 999
    entity.visual_state["energy"] = 0.1
    entity.visual_state["tags"].append("mutated")

    assert is_dataclass(snapshot)
    assert isinstance(snapshot, ViewportEntitySnapshot)
    assert snapshot.id == "sensor_1"
    assert snapshot.entity_type == "sensor"
    assert snapshot.position == (12.0, 34.5)
    assert snapshot.velocity == (1.0, -2.5)
    assert snapshot.radius == 9.25
    assert snapshot.selected is True
    assert snapshot.visible is False
    assert snapshot.pinned is True
    assert snapshot.membrane_locked is True
    assert snapshot.visual_state == {"energy": 0.8, "tags": ("warm", "active")}
    assert entity not in snapshot.__dict__.values()


def test_entity_snapshot_uses_stable_defaults_for_missing_optional_fields() -> None:
    snapshot = build_viewport_entity_snapshot(object())

    assert snapshot.id == ""
    assert snapshot.entity_type == ""
    assert snapshot.position == (0.0, 0.0)
    assert snapshot.velocity == (0.0, 0.0)
    assert snapshot.radius == 18.0
    assert snapshot.selected is False
    assert snapshot.visible is True
    assert snapshot.pinned is False
    assert snapshot.membrane_locked is False
    assert snapshot.visual_state == {}


def test_frame_snapshot_freezes_entities_edges_camera_and_metadata() -> None:
    entity = _Entity()
    edge = {"source": "sensor_1", "target": "hub_1", "kind": "soft", "weight": "0.5"}
    metadata = {"scene": "demo", "nested": {"fps": 60}}

    frame = build_viewport_frame_snapshot(
        [entity],
        width="800",
        height=600,
        scene_time="1.25",
        camera={"position": [3, 4], "zoom": "1.5", "rotation": "0.25"},
        edges=[edge],
        metadata=metadata,
    )
    entity.position[1] = -100
    edge["source"] = "mutated"
    metadata["nested"]["fps"] = 1

    assert isinstance(frame, ViewportFrameSnapshot)
    assert frame.width == 800
    assert frame.height == 600
    assert frame.scene_time == 1.25
    assert frame.entities[0].position == (12.0, 34.5)
    assert frame.edges[0].source_id == "sensor_1"
    assert frame.edges[0].target_id == "hub_1"
    assert frame.edges[0].kind == "soft"
    assert frame.edges[0].weight == 0.5
    assert isinstance(frame.camera, ViewportCameraSnapshot)
    assert frame.camera.position == (3.0, 4.0)
    assert frame.camera.zoom == 1.5
    assert frame.camera.rotation == 0.25
    assert frame.metadata == {"scene": "demo", "nested": {"fps": 60}}


def test_snapshot_dataclasses_are_immutable() -> None:
    snapshot = build_viewport_entity_snapshot(_Entity())

    with pytest.raises(FrozenInstanceError):
        snapshot.radius = 10.0
