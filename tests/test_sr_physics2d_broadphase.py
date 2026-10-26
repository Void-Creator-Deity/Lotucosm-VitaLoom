# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

from tools.benchmark_engine import _make_sr2d_entities

from core.Lotucosm.sr_physics2d import Physics2DMode, SrPhysics2DConfig, SrPhysics2DWorld
from core.Lotucosm.sr_physics2d.pvaec_contacts import build_pvaec_contact_pairs
from tests.fixtures.sr2d_parity_cases import assert_snapshots_close, snapshot


def _entity(
    entity_id: str,
    kind: str,
    x: float,
    y: float,
    *,
    radius: float = 18.0,
    vx: float = 0.0,
    vy: float = 0.0,
    pinned: bool = False,
    membrane_locked: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=entity_id,
        entity_type=kind,
        position=[x, y],
        velocity=[vx, vy],
        radius=radius,
        pinned=pinned,
        membrane_locked=membrane_locked,
    )


def _pair_ids(pairs: object) -> list[tuple[str, str]]:
    return [(str(a.id), str(b.id)) for a, b in pairs]


def test_spatial_hash_broadphase_filters_far_pairs_but_keeps_bruteforce_order() -> None:
    entities = [
        _entity("dyn_a", "organism", 10.0, 10.0, radius=10.0),
        _entity("dyn_b", "central_brain", 25.0, 10.0, radius=10.0),
        _entity("dyn_far", "organism", 400.0, 400.0, radius=10.0),
        _entity("static_near", "nutrient", 30.0, 10.0, radius=8.0, pinned=True),
        _entity("static_far", "environment_well", 500.0, 500.0, radius=8.0, pinned=True),
        _entity("pinned_dynamic", "organism", 12.0, 10.0, radius=10.0, pinned=True),
    ]

    brute = _pair_ids(build_pvaec_contact_pairs(entities, broadphase="bruteforce"))
    spatial = _pair_ids(build_pvaec_contact_pairs(entities, broadphase="spatial_hash"))

    assert brute == [
        ("dyn_a", "dyn_b"),
        ("dyn_a", "dyn_far"),
        ("dyn_a", "static_near"),
        ("dyn_a", "static_far"),
        ("dyn_b", "dyn_far"),
        ("dyn_b", "static_near"),
        ("dyn_b", "static_far"),
        ("dyn_far", "static_near"),
        ("dyn_far", "static_far"),
    ]
    assert spatial == [
        ("dyn_a", "dyn_b"),
        ("dyn_a", "static_near"),
        ("dyn_b", "static_near"),
    ]


def test_dense_spatial_hash_candidate_order_matches_bruteforce() -> None:
    entities = [
        _entity("a", "organism", 40.0, 40.0, radius=18.0),
        _entity("b", "central_brain", 50.0, 40.0, radius=18.0),
        _entity("c", "organism", 58.0, 45.0, radius=18.0),
        _entity("s", "nutrient", 52.0, 44.0, radius=14.0, pinned=True),
    ]

    brute = _pair_ids(build_pvaec_contact_pairs(entities, broadphase="bruteforce"))
    spatial = _pair_ids(build_pvaec_contact_pairs(entities, broadphase="spatial_hash"))

    assert spatial == brute


def test_spatial_hash_and_bruteforce_resolve_to_same_snapshot_on_controlled_case() -> None:
    base_entities = [
        _entity("a", "organism", 48.0, 52.0, radius=18.0, vx=20.0, vy=-5.0),
        _entity("b", "central_brain", 62.0, 52.0, radius=18.0, vx=-8.0, vy=4.0),
        _entity("s", "nutrient", 65.0, 52.0, radius=14.0, pinned=True),
        _entity("far", "organism", 220.0, 180.0, radius=18.0, vx=2.0, vy=1.0),
    ]
    brute_entities = [
        _entity(e.id, e.entity_type, e.position[0], e.position[1], radius=e.radius, vx=e.velocity[0], vy=e.velocity[1], pinned=e.pinned)
        for e in base_entities
    ]
    spatial_entities = [
        _entity(e.id, e.entity_type, e.position[0], e.position[1], radius=e.radius, vx=e.velocity[0], vy=e.velocity[1], pinned=e.pinned)
        for e in base_entities
    ]

    SrPhysics2DWorld(SrPhysics2DConfig(contact_iterations=4, pvaec_broadphase="bruteforce")).step(
        brute_entities,
        1.0 / 60.0,
        320.0,
        240.0,
        mode=Physics2DMode.PVAEC,
    )
    SrPhysics2DWorld(SrPhysics2DConfig(contact_iterations=4, pvaec_broadphase="spatial_hash")).step(
        spatial_entities,
        1.0 / 60.0,
        320.0,
        240.0,
        mode=Physics2DMode.PVAEC,
    )

    assert_snapshots_close(snapshot(spatial_entities), snapshot(brute_entities))


def test_config_parses_pvaec_broadphase_mode() -> None:
    cfg = SrPhysics2DConfig.from_scene_data(
        {"sr_physics2d": {"pvaec_broadphase": "bruteforce"}}
    )

    assert cfg.pvaec_broadphase == "bruteforce"


def test_dense_spatial_hash_matches_bruteforce_across_multiple_steps() -> None:
    import copy

    base_entities = _make_sr2d_entities("dense")
    brute_entities = copy.deepcopy(base_entities)
    spatial_entities = copy.deepcopy(base_entities)
    brute_world = SrPhysics2DWorld(
        SrPhysics2DConfig(contact_iterations=2, pvaec_broadphase="bruteforce")
    )
    spatial_world = SrPhysics2DWorld(
        SrPhysics2DConfig(contact_iterations=2, pvaec_broadphase="spatial_hash")
    )

    for _ in range(30):
        brute_world.step(
            brute_entities,
            1.0 / 60.0,
            640.0,
            480.0,
            mode=Physics2DMode.PVAEC,
        )
        spatial_world.step(
            spatial_entities,
            1.0 / 60.0,
            640.0,
            480.0,
            mode=Physics2DMode.PVAEC,
        )

    assert_snapshots_close(snapshot(spatial_entities), snapshot(brute_entities))
