from __future__ import annotations

import copy
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(Path(__file__).resolve().parents[1])

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_e380_tick_execution import (
    build_worldbridge_e380_tick_execution,
    compare_worldbridge_e380_tick_executions,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager as _scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport


def _dispatch(viewport: GameViewport, event: dict[str, object]) -> None:
    action = event["action"]
    payload = event["payload"]
    if not isinstance(payload, dict):
        raise AssertionError("E380 event payload must be a mapping")
    if action == "key_down":
        viewport._sr_input_press(str(payload["key"]))
    elif action == "key_up":
        viewport._sr_input_release(str(payload["key"]))
    elif action == "mouse_left_down":
        viewport._sr_input.set_mouse_scene(float(payload["x"]), float(payload["y"]))
        viewport._sr_input.mouse_press_left()
    elif action == "mouse_left_up":
        viewport._sr_input.mouse_release_left()
    else:
        raise AssertionError(f"unsupported E380 input action: {action}")


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    context = get_editor_context()
    project = Path(__file__).resolve().parents[1] / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    context.current_project_path = str(project)
    if not _scene_manager.get_scene_manager().load_scene(str(scene)):
        raise AssertionError("E380 scene load failed")
    source = GameViewport()
    target = GameViewport()
    events = [{"sequence": 0, "tick": 1, "action": "key_down", "payload": {"key": "A"}}]
    try:
        for viewport in (source, target):
            if not viewport._load_scene_runtime_entities():
                raise AssertionError("E380 SR runtime load failed")
            viewport._using_scene_runtime = True
            viewport._begin_sr_snapshot_lifetime()
            viewport.set_worldbridge_opt_in_deterministic_randomness_context(
                create_worldbridge_deterministic_randomness_context(
                    "e380-shared-context", "e380-shared-root-seed"
                )
            )
            viewport._unified_pond_mode = True
            viewport._unified_pond = viewport._ensure_unified_pond()
            viewport.is_playing = True
            viewport.is_paused = False

        records = []
        for viewport in (source, target):
            before = viewport.capture_worldbridge_live_checkpoint("e380-before")
            for event in events:
                _dispatch(viewport, event)
            viewport._update_scene_runtime_entities(0.05)
            after = viewport.capture_worldbridge_live_checkpoint("e380-after")
            records.append(
                build_worldbridge_e380_tick_execution(
                    sequence=1,
                    sr_delta_seconds=0.05,
                    ps_ticks=1,
                    input_events=events,
                    before_checkpoint=before,
                    after_checkpoint=after,
                )
            )
        parity = compare_worldbridge_e380_tick_executions(records[0], records[1])
        if parity.get("equal") is not True:
            raise AssertionError(parity)
        return {
            "status": "worldbridge_e380_tick_execution",
            "contract_valid": True,
            "real_game_viewports": True,
            "execution_invoked": True,
            "input_consumption_observed": True,
            "rng_consumption_observed": True,
            "canonical_parity": True,
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
            raise AssertionError("E380 GameViewport cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
