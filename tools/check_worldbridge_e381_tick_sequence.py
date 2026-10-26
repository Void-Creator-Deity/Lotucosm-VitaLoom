from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(Path(__file__).resolve().parents[1])

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import create_worldbridge_deterministic_randomness_context
from core.Lotucosm.runtime.world_bridge_e380_tick_execution import build_worldbridge_e380_tick_execution
from core.Lotucosm.runtime.world_bridge_e380_tick_execution import canonicalize_e380_checkpoint
from core.Lotucosm.runtime.world_bridge_e381_tick_sequence import (
    build_worldbridge_e381_tick_sequence,
    compare_worldbridge_e381_tick_sequences,
)
from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import verify_fresh_ps_restore_parity
from core.Lotucosm.runtime.world_bridge_fresh_sr_restore import verify_fresh_sr_restore_parity
from core.Lotucosm.runtime.world_bridge_e504_fresh_dual_lane_witness import (
    build_worldbridge_e504_fresh_dual_lane_witness,
    validate_worldbridge_e504_fresh_dual_lane_witness,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager as _scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport


def _dispatch(viewport: GameViewport, event: dict[str, object]) -> None:
    payload = event["payload"]
    if event["action"] == "key_down":
        viewport._sr_input_press(str(payload["key"]))
    elif event["action"] == "key_up":
        viewport._sr_input_release(str(payload["key"]))
    elif event["action"] == "mouse_left_down":
        viewport._sr_input.set_mouse_scene(float(payload["x"]), float(payload["y"]))
        viewport._sr_input.mouse_press_left()
    elif event["action"] == "mouse_left_up":
        viewport._sr_input.mouse_release_left()
    else:
        raise AssertionError(f"unsupported E381 action: {event['action']}")


def _configure_lifecycle(viewport: GameViewport) -> None:
    viewport._sr_combat_lineage = {}
    viewport._sr_war_respawn_queue = [{
        "at_time": 0.0,
        "lineage_id": "e381-lineage",
        "position": (360.0, 280.0),
        "radius": 20.0,
        "energy": 80.0,
        "generation": 1,
        "death_count": 0,
        "scripts": [],
    }]


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    context = get_editor_context()
    project = Path(__file__).resolve().parents[1] / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    context.current_project_path = str(project)
    if not _scene_manager.get_scene_manager().load_scene(str(scene)):
        raise AssertionError("E381 scene load failed")
    source, target = GameViewport(), GameViewport()
    events_by_tick = {
        1: [{"sequence": 0, "tick": 1, "action": "key_down", "payload": {"key": "A"}}],
        2: [{"sequence": 0, "tick": 2, "action": "key_up", "payload": {"key": "A"}}],
        3: [
            {"sequence": 0, "tick": 3, "action": "mouse_left_down", "payload": {"x": 120.0, "y": 140.0}},
            {"sequence": 1, "tick": 3, "action": "mouse_left_up", "payload": {}},
        ],
    }
    lane_records: list[list[dict[str, object]]] = [[], []]
    lane_after_checkpoints: list[list[dict[str, object]]] = [[], []]
    lane_projections: list[list[tuple[object, object]]] = [[], []]
    lifecycle_counts: list[list[tuple[int, int]]] = [[], []]
    try:
        for viewport in (source, target):
            if not viewport._load_scene_runtime_entities():
                raise AssertionError("E381 SR runtime load failed")
            viewport._using_scene_runtime = True
            viewport._begin_sr_snapshot_lifetime()
            viewport.set_worldbridge_opt_in_deterministic_randomness_context(
                create_worldbridge_deterministic_randomness_context("e381-shared-context", "e381-shared-root-seed")
            )
            viewport._unified_pond_mode = True
            viewport._unified_pond = viewport._ensure_unified_pond()
            viewport.is_playing = True
            viewport.is_paused = False
            _configure_lifecycle(viewport)

        for lane_index, viewport in enumerate((source, target)):
            for tick in (1, 2, 3):
                if tick == 2:
                    organism = next(
                        entity for entity in viewport.scene_runtime_entities
                        if str(getattr(entity, "entity_type", "")) == "organism"
                    )
                    organism.set_energy(0.0)
                before_count = len(viewport.scene_runtime_entities)
                before = viewport.capture_worldbridge_live_checkpoint(f"e381-{lane_index}-before-{tick}")
                for event in events_by_tick[tick]:
                    _dispatch(viewport, event)
                viewport._update_scene_runtime_entities(0.05)
                after_count = len(viewport.scene_runtime_entities)
                after = viewport.capture_worldbridge_live_checkpoint(f"e381-{lane_index}-after-{tick}")
                lane_after_checkpoints[lane_index].append(after)
                lifecycle_counts[lane_index].append((before_count, after_count))
                lane_projections[lane_index].append((canonicalize_e380_checkpoint(before), canonicalize_e380_checkpoint(after)))
                lane_records[lane_index].append(build_worldbridge_e380_tick_execution(
                    sequence=tick,
                    sr_delta_seconds=0.05,
                    ps_ticks=1,
                    input_events=events_by_tick[tick],
                    before_checkpoint=before,
                    after_checkpoint=after,
                ))
        if lifecycle_counts[0] != lifecycle_counts[1]:
            raise AssertionError({"reason": "lifecycle_count_mismatch", "counts": lifecycle_counts})
        spawn_observed = lifecycle_counts[0][0][1] > lifecycle_counts[0][0][0]
        despawn_observed = lifecycle_counts[0][1][1] < lifecycle_counts[0][1][0]
        left = build_worldbridge_e381_tick_sequence(lane_records[0], dynamic_spawn_observed=spawn_observed, dynamic_despawn_observed=despawn_observed)
        right = build_worldbridge_e381_tick_sequence(lane_records[1], dynamic_spawn_observed=spawn_observed, dynamic_despawn_observed=despawn_observed)
        parity = compare_worldbridge_e381_tick_sequences(left, right)
        if parity.get("equal") is not True or not spawn_observed or not despawn_observed:
            differences = []
            def diff(left_value, right_value, path=""):
                if isinstance(left_value, Mapping) and isinstance(right_value, Mapping):
                    result = []
                    for key in sorted(set(left_value) | set(right_value), key=str):
                        if key not in left_value or key not in right_value:
                            result.append((f"{path}/{key}", left_value.get(key), right_value.get(key)))
                        else:
                            result.extend(diff(left_value[key], right_value[key], f"{path}/{key}"))
                    return result
                if isinstance(left_value, (list, tuple)) and isinstance(right_value, (list, tuple)):
                    result = []
                    for index in range(max(len(left_value), len(right_value))):
                        if index >= len(left_value) or index >= len(right_value):
                            result.append((f"{path}/{index}", left_value[index] if index < len(left_value) else None, right_value[index] if index < len(right_value) else None))
                        else:
                            result.extend(diff(left_value[index], right_value[index], f"{path}/{index}"))
                    return result
                if type(left_value) is not type(right_value):
                    return [(path, left_value, right_value)]
                if isinstance(left_value, dict):
                    result = []
                    for key in sorted(set(left_value) | set(right_value)):
                        if key not in left_value or key not in right_value:
                            result.append((f"{path}/{key}", left_value.get(key), right_value.get(key)))
                        else:
                            result.extend(diff(left_value[key], right_value[key], f"{path}/{key}"))
                    return result
                if isinstance(left_value, list):
                    result = []
                    for index in range(max(len(left_value), len(right_value))):
                        if index >= len(left_value) or index >= len(right_value):
                            result.append((f"{path}/{index}", left_value[index] if index < len(left_value) else None, right_value[index] if index < len(right_value) else None))
                        else:
                            result.extend(diff(left_value[index], right_value[index], f"{path}/{index}"))
                    return result
                return [] if left_value == right_value else [(path, left_value, right_value)]
            for index, (left_record, right_record) in enumerate(zip(lane_records[0], lane_records[1]), 1):
                differences.append({
                    "tick": index,
                    "left": left_record,
                    "right": right_record,
                    "state_differences": diff(lane_projections[0][index - 1], lane_projections[1][index - 1])[:20],
                })
            raise AssertionError({"parity": parity, "lifecycle_counts": lifecycle_counts, "records": differences})
        fresh_sr = verify_fresh_sr_restore_parity(source, target)
        fresh_ps = verify_fresh_ps_restore_parity(source._unified_pond)
        if not all((fresh_sr["fresh_instance"], fresh_sr["dynamic_slice_restored"], fresh_sr["dynamic_state_equal"], fresh_ps["fresh_instance_created"], fresh_ps["canonical_state_equal"])):
            raise AssertionError({"fresh_sr": fresh_sr, "fresh_ps": fresh_ps})
        e504_witness = build_worldbridge_e504_fresh_dual_lane_witness(
            source_checkpoint=lane_after_checkpoints[0][-1],
            fresh_checkpoint=lane_after_checkpoints[1][-1],
            fresh_sr_restore=fresh_sr,
            fresh_ps_restore=fresh_ps,
            source_next_rng_snapshot=source._worldbridge_opt_in_deterministic_randomness_context.snapshot(),
            fresh_next_rng_snapshot=target._worldbridge_opt_in_deterministic_randomness_context.snapshot(),
        )
        if validate_worldbridge_e504_fresh_dual_lane_witness(e504_witness) != {"valid": True, "errors": []}:
            raise AssertionError("E504 fresh dual-lane witness did not validate")
        return {
            "status": "worldbridge_e381_tick_sequence",
            "contract_valid": True,
            "real_game_viewports": True,
            "tick_count": 3,
            "continuous_execution_observed": True,
            "input_boundaries_observed": True,
            "dynamic_spawn_observed": True,
            "dynamic_despawn_observed": True,
            "canonical_parity": True,
            "component_digests": dict(left["component_digests"]),
            "fresh_sr_restore": True,
            "fresh_ps_restore": True,
            "fresh_dual_lane_parity": e504_witness["fresh_dual_lane_parity"],
            "e504_fresh_dual_lane_witness": e504_witness,
            "shared_clock_admitted": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    finally:
        source.deleteLater()
        target.deleteLater()
        QCoreApplication.sendPostedEvents(source, QEvent.Type.DeferredDelete)
        QCoreApplication.sendPostedEvents(target, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not (sip.isdeleted(source) and sip.isdeleted(target)):
            raise AssertionError("E381 GameViewport cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
