# -*- coding: utf-8
from __future__ import annotations

from types import SimpleNamespace

from core.VitaLoom.simulation.sr_runtime_structure_parity import (
    build_sr_runtime_structure_fingerprint,
    compare_sr_runtime_structure_fingerprints,
    validate_sr_runtime_structure_fingerprint,
)


def _structure(x: float = 1.0):
    parent = SimpleNamespace(
        id="org:a", entity_type="organism", radius=18.0, pinned=False,
        scripts=[SimpleNamespace()],
    )
    child = SimpleNamespace(id="sensor:a", entity_type="sensor", radius=8.0, pinned=False, scripts=[])
    return build_sr_runtime_structure_fingerprint(
        entities=[parent, child],
        scene_path="scene.pond",
        structural_edges=[{"start": "org:a", "end": "sensor:a", "type": "hard"}],
        signal_edges=[{"start": "sensor:a", "end": "org:a", "channel": "chemo", "weight": x}],
        membrane_attach={"sensor:a": ["org:a", 5.0, -2.0]},
        membrane_template={"sensors": ["sensor"]},
    )


def test_structure_fingerprint_is_valid_and_order_independent_for_edges():
    first = _structure()
    second = build_sr_runtime_structure_fingerprint(
        entities=[SimpleNamespace(id="sensor:a", entity_type="sensor", radius=8.0, pinned=False, scripts=[]), SimpleNamespace(id="org:a", entity_type="organism", radius=18.0, pinned=False, scripts=[SimpleNamespace()])],
        scene_path="scene.pond",
        structural_edges=[{"type": "hard", "end": "sensor:a", "start": "org:a"}],
        signal_edges=[{"weight": 1.0, "channel": "chemo", "end": "org:a", "start": "sensor:a"}],
        membrane_attach={"sensor:a": ["org:a", 5.0, -2.0]},
        membrane_template={"sensors": ["sensor"]},
    )
    assert validate_sr_runtime_structure_fingerprint(first)["valid"] is True
    assert compare_sr_runtime_structure_fingerprints(first, second)["equal"] is True


def test_structure_mismatch_is_rejected_before_dynamic_restore():
    result = compare_sr_runtime_structure_fingerprints(_structure(), _structure(2.0))
    assert result["equal"] is False
    assert result["reason"] == "structure_mismatch"
