from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

from core.Lotucosm.runtime.world_bridge_fresh_sr_restore import (
    verify_fresh_sr_restore_parity,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager as _scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport


def verify_real_game_viewport_fresh_sr_restore() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    context = get_editor_context()
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    context.current_project_path = str(project)
    manager = _scene_manager.get_scene_manager()
    if not manager.load_scene(str(scene)):
        raise AssertionError(f"could not load scene: {scene}")

    source = GameViewport()
    fresh = GameViewport()
    try:
        for viewport in (source, fresh):
            if not viewport._load_scene_runtime_entities():
                raise AssertionError("real GameViewport scene runtime was not loaded")
            viewport._using_scene_runtime = True
            viewport._begin_sr_snapshot_lifetime()
        result = verify_fresh_sr_restore_parity(source, fresh)
        if not result["fresh_instance"] or not result["structure"]["equal"]:
            raise AssertionError(result)
        if not result["dynamic_slice_restored"] or not result["dynamic_state_equal"]:
            raise AssertionError(result)
        return {
            "status": "worldbridge_e378_real_game_viewport_fresh_sr",
            "contract_valid": True,
            "real_game_viewports": True,
            "scene_loaded": True,
            "script_entropy_receipts_compared": (
                list(source._sr_script_entropy_receipts)
                == list(fresh._sr_script_entropy_receipts)
            ),
            "structure_parity": result["structure"]["equal"],
            "dynamic_state_equal": result["dynamic_state_equal"],
            "cleanup_complete": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    finally:
        source.deleteLater()
        fresh.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        cleanup = bool(sip.isdeleted(source) and sip.isdeleted(fresh))
        if not cleanup:
            raise AssertionError("real GameViewport cleanup was incomplete")


if __name__ == "__main__":
    result = verify_real_game_viewport_fresh_sr_restore()
    result["cleanup_complete"] = True
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] and result["cleanup_complete"] else 1)
