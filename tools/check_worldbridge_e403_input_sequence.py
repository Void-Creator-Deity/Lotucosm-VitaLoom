from __future__ import annotations

import copy
import json
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence, validate_worldbridge_input_events


def verify() -> dict[str, object]:
    sequence = WorldBridgeInputSequence()
    sequence.append("key_down", {"key": "W"})
    sequence.append("mouse_down", {"button": "left", "scene_xy": [4.0, 5.0]})
    events = sequence.consume()
    baseline = validate_worldbridge_input_events(events)
    duplicate = copy.deepcopy(events)
    duplicate.append(copy.deepcopy(events[0]))
    duplicate_result = validate_worldbridge_input_events(duplicate)
    sequence.lifecycle("pause")
    sequence.append("key_up", {"key": "W"})
    epoch_events = sequence.consume()
    epoch_result = validate_worldbridge_input_events(epoch_events, last_sequence=2, pause_reset_epoch=1)
    result = {
        "status": "worldbridge_e403_input_sequence",
        "contract_valid": baseline["valid"] and duplicate_result["valid"] is False and epoch_result["valid"],
        "canonical_sequence_valid": baseline["valid"],
        "duplicate_or_gap_rejected": duplicate_result["valid"] is False,
        "pause_epoch_advanced": sequence.pause_reset_epoch == 1,
        "post_pause_epoch_valid": epoch_result["valid"],
        "dropped_event_policy": "reject_sequence_gap",
        "shared_queued_input_ordering": True,
        "input_replay_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
