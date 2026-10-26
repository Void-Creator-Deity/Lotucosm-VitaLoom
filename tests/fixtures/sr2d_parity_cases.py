# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable

from core.Lotucosm.sr_physics2d import Physics2DMode, SrPhysics2DConfig


@dataclass(frozen=True)
class Sr2DParityCase:
    name: str
    entities: tuple[SimpleNamespace, ...]
    dt: float = 1.0 / 60.0
    width: float = 320.0
    height: float = 240.0
    mode: Physics2DMode = Physics2DMode.PVAEC
    springs: tuple[Any, ...] = ()
    config: SrPhysics2DConfig = SrPhysics2DConfig(contact_iterations=4)


def entity(
    kind: str,
    x: float,
    y: float,
    *,
    vx: float = 18.0,
    vy: float = -5.0,
    radius: float | None = None,
    pinned: bool = False,
    membrane_locked: bool = False,
    entity_id: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=entity_id or f"{kind}_{x}_{y}",
        entity_type=kind,
        position=[x, y],
        velocity=[0.0, 0.0] if pinned or membrane_locked else [vx, vy],
        radius=radius if radius is not None else (14.0 if kind == "nutrient" else 18.0),
        pinned=pinned,
        membrane_locked=membrane_locked,
    )


SR2D_PARITY_CASES: tuple[Sr2DParityCase, ...] = (
    Sr2DParityCase(
        name="dynamic_dynamic_overlap",
        entities=(
            entity("organism", 48.0, 52.0, vx=21.0, vy=-7.0),
            entity("central_brain", 62.0, 52.0, vx=-8.0, vy=4.0),
        ),
    ),
    Sr2DParityCase(
        name="spatial_hash_dynamic_overlap",
        entities=(
            entity("organism", 48.0, 52.0, vx=21.0, vy=-7.0),
            entity("central_brain", 62.0, 52.0, vx=-8.0, vy=4.0),
            entity("nutrient", 78.0, 52.0, pinned=True),
        ),
        config=SrPhysics2DConfig(
            contact_iterations=4,
            pvaec_broadphase="spatial_hash",
        ),
    ),
    Sr2DParityCase(
        name="canonicalized_spatial_hash",
        entities=(
            entity("organism", 48.0, 52.0, vx=21.0, vy=-7.0),
            entity("central_brain", 62.0, 52.0, vx=-8.0, vy=4.0),
        ),
        config=SrPhysics2DConfig(
            contact_iterations=4,
            pvaec_broadphase=" SPATIAL_HASH ",
        ),
    ),
    Sr2DParityCase(
        name="dense_spatial_hash_multi_iteration",
        entities=(
            entity("organism", 48.0, 52.0, vx=21.0, vy=-7.0),
            entity("central_brain", 60.0, 52.0, vx=-8.0, vy=4.0),
            entity("organism", 68.0, 58.0, vx=-3.0, vy=-6.0),
            entity("nutrient", 76.0, 54.0, pinned=True),
        ),
        config=SrPhysics2DConfig(
            contact_iterations=6,
            pvaec_broadphase="spatial_hash",
        ),
    ),
    Sr2DParityCase(
        name="unclamped_contact_coefficients",
        entities=(
            entity("organism", 48.0, 52.0, vx=30.0, vy=12.0),
            entity("central_brain", 62.0, 52.0, vx=-14.0, vy=-8.0),
        ),
        config=SrPhysics2DConfig(
            restitution=1.25,
            friction=-0.4,
            contact_slop=-0.5,
            contact_correction=1.2,
            contact_iterations=3,
        ),
    ),
    Sr2DParityCase(
        name="non_contact_kinematic_entity",
        entities=(entity("game_actor", 50.0, 50.0, vx=30.0, vy=-10.0),),
        config=SrPhysics2DConfig(contact_iterations=2),
    ),
    Sr2DParityCase(
        name="dynamic_static_overlap",
        entities=(
            entity("organism", 48.0, 52.0, vx=12.0, vy=-4.0),
            entity("nutrient", 62.0, 52.0, pinned=True),
        ),
    ),
    Sr2DParityCase(
        name="pinned_is_static",
        entities=(
            entity("organism", 48.0, 52.0, pinned=True),
            entity("nutrient", 62.0, 52.0, pinned=True),
        ),
    ),
    Sr2DParityCase(
        name="membrane_locked_is_static",
        entities=(
            entity("organism", 48.0, 52.0, membrane_locked=True),
            entity("central_brain", 62.0, 52.0, vx=-8.0, vy=4.0),
        ),
    ),
    Sr2DParityCase(
        name="boundary_bounce",
        entities=(entity("organism", 11.0, 11.0, vx=-90.0, vy=-60.0, radius=12.0),),
        width=120.0,
        height=100.0,
        config=SrPhysics2DConfig(boundary_bounce=0.8, contact_iterations=2),
    ),
    Sr2DParityCase(
        name="max_speed_clamp",
        entities=(entity("organism", 50.0, 50.0, vx=900.0, vy=300.0),),
        config=SrPhysics2DConfig(max_speed=120.0, contact_iterations=2),
    ),
    Sr2DParityCase(
        name="zero_dt",
        entities=(entity("organism", 50.0, 50.0, vx=30.0, vy=-10.0),),
        dt=0.0,
    ),
    Sr2DParityCase(
        name="empty_entities",
        entities=(),
    ),
)


def clone_entities(case: Sr2DParityCase) -> list[SimpleNamespace]:
    return [copy.deepcopy(entity) for entity in case.entities]


def snapshot(entities: Iterable[SimpleNamespace]) -> list[tuple[float, float, float, float]]:
    return [
        (
            round(float(e.position[0]), 6),
            round(float(e.position[1]), 6),
            round(float(e.velocity[0]), 6),
            round(float(e.velocity[1]), 6),
        )
        for e in entities
    ]


def assert_snapshots_close(
    actual: list[tuple[float, float, float, float]],
    expected: list[tuple[float, float, float, float]],
    *,
    abs_tol: float = 1e-4,
) -> None:
    assert len(actual) == len(expected)
    for actual_row, expected_row in zip(actual, expected):
        for actual_value, expected_value in zip(actual_row, expected_row):
            assert math.isclose(actual_value, expected_value, abs_tol=abs_tol)
