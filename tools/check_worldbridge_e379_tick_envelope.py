from __future__ import annotations

import json
import os
import copy
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

from core.Lotucosm.runtime.world_bridge_e379_tick_envelope import (
    digest_worldbridge_e379_state,
)
from core.Lotucosm.runtime.world_bridge_e379_tick_envelope import (
    build_worldbridge_e379_tick_envelope,
    compare_worldbridge_e379_tick_envelopes,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager as _scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    context = get_editor_context()
    project = Path(__file__).resolve().parents[1] / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    context.current_project_path = str(project)
    if not _scene_manager.get_scene_manager().load_scene(str(scene)):
        raise AssertionError("E379 scene load failed")
    source = GameViewport()
    target = GameViewport()
    try:
        # Each lane gets an independent context with identical root seed.  A
        # shared context would share one mutable stream and make construction
        # order part of the parity result.
        for viewport in (source, target):
            if not viewport._load_scene_runtime_entities():
                raise AssertionError("E379 SR runtime load failed")
            viewport._using_scene_runtime = True
            viewport._begin_sr_snapshot_lifetime()
            viewport.set_worldbridge_opt_in_deterministic_randomness_context(
                create_worldbridge_deterministic_randomness_context(
                    "e379-shared-context", "e379-shared-root-seed"
                )
            )
            viewport._unified_pond_mode = True
            viewport._unified_pond = viewport._ensure_unified_pond()
        source_checkpoint = source.capture_worldbridge_live_checkpoint("e379-source")
        target_checkpoint = target.capture_worldbridge_live_checkpoint("e379-target")
        def parity_state(value):
            def strip_identity(item):
                if isinstance(item, dict):
                        normalized = {
                            key: strip_identity(child)
                            for key, child in item.items()
                            if key not in {
                                "runtime_epoch",
                                "capture_id",
                                "context_id",
                                "digest",
                                "capture_digest",
                                "snapshot_digest",
                                "envelope_digest",
                                "checkpoint_digest",
                                "receipt_digest",
                            }
                        }
                        return normalized
                if isinstance(item, list):
                    return [strip_identity(child) for child in item]
                return copy.deepcopy(item)
            return strip_identity(value)

        def differing_paths(left_value, right_value, path=""):
            if type(left_value) is not type(right_value):
                return [(path, left_value, right_value)]
            if isinstance(left_value, dict):
                result = []
                for key in sorted(set(left_value) | set(right_value)):
                    if key not in left_value or key not in right_value:
                        result.append((f"{path}/{key}", left_value.get(key), right_value.get(key)))
                    else:
                        result.extend(differing_paths(left_value[key], right_value[key], f"{path}/{key}"))
                return result
            if isinstance(left_value, list):
                result = []
                for index in range(max(len(left_value), len(right_value))):
                    if index >= len(left_value) or index >= len(right_value):
                        result.append((f"{path}/{index}", left_value[index] if index < len(left_value) else None, right_value[index] if index < len(right_value) else None))
                    else:
                        result.extend(differing_paths(left_value[index], right_value[index], f"{path}/{index}"))
                return result
            return [] if left_value == right_value else [(path, left_value, right_value)]

        def envelope(checkpoint):
            return build_worldbridge_e379_tick_envelope(
                sequence=1,
                sr_delta_seconds=0.05,
                ps_ticks=1,
                input_events=[{"sequence": 0, "tick": 1, "action": "key_down", "payload": {"key": "A"}}],
                sr_state_digest=digest_worldbridge_e379_state(parity_state(checkpoint["sr_state"])),
                ps_state_digest=digest_worldbridge_e379_state(parity_state(checkpoint["ps_state"])),
                randomness_digest=digest_worldbridge_e379_state(parity_state(checkpoint["randomness_state"])),
            )
        left = envelope(source_checkpoint)
        right = envelope(target_checkpoint)
        parity = compare_worldbridge_e379_tick_envelopes(left, right)
        if parity.get("equal") is not True:
            raise AssertionError({
                **parity,
                "left": {key: left[key] for key in ("sr_state_digest", "ps_state_digest", "randomness_digest")},
                "right": {key: right[key] for key in ("sr_state_digest", "ps_state_digest", "randomness_digest")},
                "sr_differences": differing_paths(parity_state(source_checkpoint["sr_state"]), parity_state(target_checkpoint["sr_state"]))[:12],
                "randomness_differences": differing_paths(parity_state(source_checkpoint["randomness_state"]), parity_state(target_checkpoint["randomness_state"]))[:12],
            })
        return {
            "status": "worldbridge_e379_tick_envelope",
            "contract_valid": True,
            "canonical_parity": True,
            "real_game_viewports": True,
            "input_ordering": True,
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
            raise AssertionError("E379 GameViewport cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
