# -*- coding: utf-8 -*-
"""Opt-in production SR runtime snapshot slice restore contract."""
from __future__ import annotations

import pytest

from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
    SrRuntimeSnapshotRestoreError,
    restore_sr_runtime_snapshot_slice,
)


def _entity(entity_id: str = "e1"):
    class Entity:
        def __init__(self) -> None:
            self.id = entity_id
            self.position = [1.0, 2.0]
            self.velocity = [3.0, 4.0]
            self.radius = 5.0
            self.energy = 6.0
            self.generation = 1
            self.pinned = False
            self.membrane_locked = False
            from core.Lotucosm.sr_entity_visual import SrEntityVisual

            self.sr_visual = SrEntityVisual(flip_x=False, alpha=1.0)

        def set_position(self, value):
            self.position = [float(value[0]), float(value[1])]

        def set_velocity(self, value):
            self.velocity = [float(value[0]), float(value[1])]

        def set_radius(self, value):
            self.radius = float(value)

        def set_energy(self, value):
            self.energy = float(value)

        def set_generation(self, value):
            self.generation = int(value)

    return Entity()


def _snapshot(entity_id: str = "e1", **updates):
    value = {
        "entity_id": entity_id,
        "position": [10.0, 11.0],
        "velocity": [12.0, 13.0],
        "radius": 14.0,
        "energy": 15.0,
        "generation": 4,
        "pinned": True,
        "membrane_locked": True,
        "render_identity": {"flip_x": True, "alpha": 0.5},
    }
    value.update(updates)
    return value


def test_restore_applies_supported_slice_atomically() -> None:
    entity = _entity()
    result = restore_sr_runtime_snapshot_slice([entity], [_snapshot()], scene_time=2.5)

    assert result == 2.5
    assert entity.position == [10.0, 11.0]
    assert entity.velocity == [12.0, 13.0]
    assert entity.radius == 14.0
    assert entity.energy == 15.0
    assert entity.generation == 4
    assert entity.pinned is True
    assert entity.membrane_locked is True
    assert entity.sr_visual.flip_x is True
    assert entity.sr_visual.alpha == 0.5


@pytest.mark.parametrize(
    "bad",
    [
        {"entity_id": "missing", "position": [1.0, 2.0]},
        _snapshot(generation=True),
        _snapshot(position=[float("nan"), 1.0]),
        _snapshot(radius=0.0),
    ],
)
def test_restore_rejects_invalid_or_unknown_snapshot_before_mutation(bad) -> None:
    entity = _entity()
    before = (entity.position[:], entity.velocity[:], entity.radius, entity.energy)

    with pytest.raises(SrRuntimeSnapshotRestoreError):
        restore_sr_runtime_snapshot_slice([entity], [bad], scene_time=2.5)

    assert (entity.position[:], entity.velocity[:], entity.radius, entity.energy) == before


def test_apply_failure_rolls_back_prior_entities() -> None:
    first = _entity("first")
    second = _entity("second")

    def fail(_value):
        raise RuntimeError("setter failure")

    second.set_energy = fail
    with pytest.raises(SrRuntimeSnapshotRestoreError, match="setter failure"):
        restore_sr_runtime_snapshot_slice(
            [first, second],
            [_snapshot("first"), _snapshot("second")],
            scene_time=9.0,
        )

    assert first.position == [1.0, 2.0]
    assert first.energy == 6.0
    assert second.position == [1.0, 2.0]
    assert second.energy == 6.0


def test_restore_does_not_require_or_mutate_scripts_and_topology() -> None:
    entity = _entity()
    entity.scripts = [object()]
    entity.links = [("e1", "e2")]
    restore_sr_runtime_snapshot_slice([entity], [_snapshot()], scene_time=1.0)
    assert len(entity.scripts) == 1
    assert entity.links == [("e1", "e2")]

def test_render_identity_rejects_malformed_payload_before_mutation() -> None:
    entity = _entity()
    before = (entity.sr_visual.flip_x, entity.sr_visual.alpha)

    for bad in (
        {"flip_x": "yes", "alpha": 0.5},
        {"flip_x": True, "alpha": 2.0},
        {"flip_x": True, "alpha": float("nan")},
        {"flip_x": True},
        {"flip_x": True, "alpha": 0.5, "extra": 1},
    ):
        with pytest.raises(SrRuntimeSnapshotRestoreError):
            restore_sr_runtime_snapshot_slice(
                [entity], [_snapshot(render_identity=bad)], scene_time=1.0
            )
        assert (entity.sr_visual.flip_x, entity.sr_visual.alpha) == before


def test_render_identity_apply_failure_rolls_back_prior_entities() -> None:
    first = _entity("first")
    second = _entity("second")

    class _NoVisual:
        pass

    second.sr_visual = None
    first.sr_visual.flip_x = False
    first.sr_visual.alpha = 1.0

    with pytest.raises(SrRuntimeSnapshotRestoreError, match="sr_visual"):
        restore_sr_runtime_snapshot_slice(
            [first, second],
            [_snapshot("first"), _snapshot("second")],
            scene_time=1.0,
        )
    assert (first.sr_visual.flip_x, first.sr_visual.alpha) == (False, 1.0)


def test_snapshot_without_render_identity_leaves_visual_untouched() -> None:
    entity = _entity()
    entity.sr_visual.flip_x = True
    entity.sr_visual.alpha = 0.25
    bad = _snapshot()
    bad.pop("render_identity")

    restore_sr_runtime_snapshot_slice([entity], [bad], scene_time=1.0)

    assert entity.sr_visual.flip_x is True
    assert entity.sr_visual.alpha == 0.25
