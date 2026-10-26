from __future__ import annotations

import json
from types import SimpleNamespace

from _runtime_bootstrap import install_runtime_paths
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_fresh_sr_restore import verify_fresh_sr_restore_parity


class _Runtime:
    def __init__(self):
        self._sr_runtime_scene_path = "e377.pond"
        self._sr_structural_edges = [{"start": "org:e377", "end": "sensor:e377", "type": "hard"}]
        self._sr_signal_edges = [{"start": "sensor:e377", "end": "org:e377", "channel": "chemo", "weight": 1.0}]
        self._sr_membrane_attach = {"sensor:e377": ("org:e377", 2.0, 1.0)}
        self._sr_membrane_template = {"sensors": ["sensor"]}
        self.scene_runtime_entities = [
            SimpleNamespace(id="org:e377", entity_type="organism", radius=18.0, pinned=False, scripts=[]),
            SimpleNamespace(id="sensor:e377", entity_type="sensor", radius=8.0, pinned=False, scripts=[]),
        ]
        self._state = {"scene_time": 2.0, "snapshots": [
            {"entity_id": "org:e377", "position": [1.0, 2.0], "velocity": [0.0, 0.0], "radius": 18.0, "energy": 75.0, "generation": 1, "pinned": False, "membrane_locked": False},
            {"entity_id": "sensor:e377", "position": [3.0, 2.0], "velocity": [0.0, 0.0], "radius": 8.0, "energy": 10.0, "generation": 0, "pinned": False, "membrane_locked": False},
        ]}

    def capture_sr_runtime_restore_envelope(self):
        return dict(self._state)

    def restore_sr_runtime_snapshot_slice(self, snapshots, *, scene_time=None):
        self._state = {"scene_time": scene_time, "snapshots": snapshots}
        return scene_time


def verify() -> dict[str, object]:
    result = verify_fresh_sr_restore_parity(_Runtime(), _Runtime())
    if not all(result[key] is True for key in ("fresh_instance", "dynamic_slice_restored", "dynamic_state_equal")):
        raise AssertionError(result)
    return {
        "status": "worldbridge_fresh_sr_restore",
        "contract_valid": True,
        "structure_parity": result["structure"]["equal"],
        "dynamic_state_equal": result["dynamic_state_equal"],
        "cross_lane_parity": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
