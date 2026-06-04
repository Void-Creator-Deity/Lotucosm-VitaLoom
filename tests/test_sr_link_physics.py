# -*- coding: utf-8 -*-
"""SR 连接物理：硬骨架 / 软信号 / 弹簧 / 独立扩散。"""

from __future__ import annotations

import math
from types import SimpleNamespace

from core.Lotucosm.sr_link_physics import (
    build_spring_links,
    infer_link_kind,
    partition_link_edges,
    step_spring_network,
)
from core.Lotucosm.sr_membrane_topology import build_membrane_attachments, parse_weighted_edges


def _ent(eid: str, etype: str, x: float, y: float):
    return SimpleNamespace(
        id=eid,
        entity_type=etype,
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=12.0,
        membrane_locked=False,
        pinned=False,
    )


def test_infer_link_kind_defaults():
    id_to_type = {
        "hub": "organism",
        "s1": "sensor",
        "a1": "actuator",
    }
    assert infer_link_kind({"start": "hub", "end": "s1"}, id_to_type) == "hard"
    assert infer_link_kind({"start": "s1", "end": "a1"}, id_to_type) == "soft"
    assert (
        infer_link_kind({"start": "s1", "end": "a1", "link_kind": "independent"}, id_to_type)
        == "independent"
    )


def test_hard_only_builds_membrane_attach():
    hub = _ent("hub", "organism", 100.0, 100.0)
    sensor = _ent("s1", "sensor", 140.0, 100.0)
    actuator = _ent("a1", "actuator", 100.0, 140.0)
    entities = [hub, sensor, actuator]
    edges = parse_weighted_edges(
        [
            {"start": "hub", "end": "s1", "link_kind": "hard"},
            {"start": "hub", "end": "a1", "link_kind": "hard"},
        ]
    )
    attach = build_membrane_attachments(entities, edges)
    assert "s1" in attach and "a1" in attach
    assert sensor.membrane_locked is True
    assert actuator.membrane_locked is True


def test_soft_organism_sensor_no_rigid_attach():
    hub = _ent("hub", "organism", 100.0, 100.0)
    sensor = _ent("s1", "sensor", 150.0, 100.0)
    entities = [hub, sensor]
    hard, soft_sig, soft_mech = partition_link_edges(
        [{"start": "hub", "end": "s1", "link_kind": "soft"}],
        {"hub": "organism", "s1": "sensor"},
    )
    assert hard == []
    assert soft_mech  # organism↔sensor soft 默认带弹簧
    attach = build_membrane_attachments(entities, hard)
    assert attach == {}
    assert sensor.membrane_locked is False
    springs = build_spring_links(entities, soft_mech)
    assert len(springs) == 1
    assert math.isclose(springs[0].rest_length, 50.0, rel_tol=1e-3)


def test_soft_signal_not_in_attach():
    s1 = _ent("s1", "sensor", 10.0, 10.0)
    a1 = _ent("a1", "actuator", 40.0, 40.0)
    hard, soft_sig, soft_mech = partition_link_edges(
        [{"start": "s1", "end": "a1", "link_kind": "soft", "channel": "chemo", "weight": 1.2}],
        {"s1": "sensor", "a1": "actuator"},
    )
    assert soft_sig and not soft_mech
    attach = build_membrane_attachments([s1, a1], hard)
    assert attach == {}


def test_spring_network_moves_soft_child():
    hub = _ent("hub", "organism", 0.0, 0.0)
    hub.pinned = True
    sensor = _ent("s1", "sensor", 80.0, 0.0)
    hard, _, soft_mech = partition_link_edges(
        [
            {
                "start": "hub",
                "end": "s1",
                "link_kind": "soft",
                "stiffness": 200.0,
                "damping": 5.0,
                "rest_length": 40.0,
            }
        ],
        {"hub": "organism", "s1": "sensor"},
    )
    springs = build_spring_links([hub, sensor], soft_mech)
    for _ in range(60):
        step_spring_network([hub, sensor], springs, 0.016)
        sensor.position[0] += sensor.velocity[0] * 0.016
        sensor.position[1] += sensor.velocity[1] * 0.016
    assert sensor.position[0] < 75.0
