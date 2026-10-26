from __future__ import annotations

from types import SimpleNamespace

from core.Lotucosm.runtime.world_bridge_fresh_sr_restore import (
    build_worldbridge_fresh_sr_restore_contract,
    verify_fresh_sr_restore_parity,
)


class _Runtime:
    def __init__(self, *, weight: float = 1.0):
        self._sr_runtime_scene_path = "sample.pond"
        self._sr_structural_edges = [{"start": "org:a", "end": "sensor:a", "type": "hard"}]
        self._sr_signal_edges = [{"start": "sensor:a", "end": "org:a", "channel": "chemo", "weight": weight}]
        self._sr_membrane_attach = {"sensor:a": ("org:a", 4.0, -2.0)}
        self._sr_membrane_template = {"sensors": ["sensor"]}
        self.scene_runtime_entities = [
            SimpleNamespace(id="org:a", entity_type="organism", radius=18.0, pinned=False, scripts=[]),
            SimpleNamespace(id="sensor:a", entity_type="sensor", radius=8.0, pinned=False, scripts=[]),
        ]
        self._state = {"scene_time": 3.0, "snapshots": [
            {"entity_id": "org:a", "position": [5.0, 6.0], "velocity": [1.0, 0.0], "radius": 18.0, "energy": 70.0, "generation": 2, "pinned": False, "membrane_locked": False},
            {"entity_id": "sensor:a", "position": [9.0, 4.0], "velocity": [0.0, 0.0], "radius": 8.0, "energy": 10.0, "generation": 0, "pinned": False, "membrane_locked": False},
        ]}

    def capture_sr_runtime_restore_envelope(self):
        return dict(self._state)

    def restore_sr_runtime_snapshot_slice(self, snapshots, *, scene_time=None):
        self._state = {"scene_time": scene_time, "snapshots": snapshots}
        return scene_time


def test_fresh_sr_restore_requires_structure_and_restores_dynamic_slice():
    result = verify_fresh_sr_restore_parity(_Runtime(), _Runtime())
    assert result["fresh_instance"] is True
    assert result["structure"]["equal"] is True
    assert result["dynamic_slice_restored"] is True
    assert result["dynamic_state_equal"] is True
    assert result["cross_lane_parity"] is True
    assert result["default_ready"] is False


def test_fresh_sr_restore_rejects_topology_drift_before_mutation():
    source = _Runtime()
    fresh = _Runtime(weight=2.0)
    before = fresh.capture_sr_runtime_restore_envelope()
    result = verify_fresh_sr_restore_parity(source, fresh)
    assert result["dynamic_slice_restored"] is False
    assert result["errors"] == ["sr_structure_mismatch"]
    assert fresh.capture_sr_runtime_restore_envelope() == before


def test_contract_keeps_full_replay_and_default_readiness_closed():
    contract = build_worldbridge_fresh_sr_restore_contract()
    assert contract["contract_valid"] is True
    assert contract["structure_fingerprint_required"] is True
    assert contract["cross_lane_parity"] is False
    assert contract["default_ready"] is False
