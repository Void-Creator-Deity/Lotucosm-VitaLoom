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

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6 import sip
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    restore_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
from core.Lotucosm.runtime.world_bridge_e504_fresh_dual_lane_witness import (
    build_worldbridge_e504_fresh_dual_lane_witness,
    validate_worldbridge_e504_fresh_dual_lane_witness,
)
from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import (
    capture_canonical_ps_state,
    restore_ps_state_to_fresh_pond,
)
from core.VitaLoom.simulation.sr_runtime_structure_parity import (
    build_sr_runtime_structure_fingerprint,
    compare_sr_runtime_structure_fingerprints,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport


def _new_viewport(project: Path, scene: Path, root_seed: str) -> GameViewport:
    get_editor_context().current_project_path = str(project)
    if not scene_manager.get_scene_manager().load_scene(str(scene)):
        raise AssertionError("E505 scene load failed")
    viewport = GameViewport()
    if not viewport._load_scene_runtime_entities():
        raise AssertionError("E505 SR runtime load failed")
    viewport._using_scene_runtime = True
    viewport._begin_sr_snapshot_lifetime()
    viewport._unified_pond_mode = True
    viewport._ensure_unified_pond()
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(
        create_worldbridge_deterministic_randomness_context(
            "e505-fresh-host-context", root_seed
        )
    )
    viewport.is_playing = True
    viewport.is_paused = False
    return viewport


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    source = _new_viewport(project, scene, "e505-root-seed")
    fresh = None
    try:
        source._update_scene_runtime_entities(0.05)
        source_checkpoint = source.capture_worldbridge_live_checkpoint("e505-source")
        source_rng = copy.deepcopy(source_checkpoint["randomness_state"]["deterministic_context"])
        source_input = copy.deepcopy(source_checkpoint["input_state"])
        source_sr = copy.deepcopy(source_checkpoint["sr_state"]["runtime_restore_envelope"])
        source_ps = copy.deepcopy(source_checkpoint["ps_state"])
        source_ps_canonical = capture_canonical_ps_state(source._unified_pond)
        source_structure = build_sr_runtime_structure_fingerprint(
            entities=source.scene_runtime_entities,
            scene_path=source._sr_runtime_scene_path,
            structural_edges=source._sr_structural_edges,
            signal_edges=source._sr_signal_edges,
            membrane_attach=source._sr_membrane_attach,
            membrane_template=source._sr_membrane_template,
        )
        source._update_scene_runtime_entities(0.05)
        source_next_rng = source._worldbridge_opt_in_deterministic_randomness_context.snapshot()

        # Creating a second host changes the global editor selection and can
        # stop the first host; all source-owned capture must precede that edge.
        fresh = _new_viewport(project, scene, "e505-root-seed")

        # Fresh host owns a distinct epoch; only the portable state slices are
        # applied. The source epoch is never copied into the fresh host.
        fresh._update_scene_runtime_entities(0.05)
        fresh_structure = build_sr_runtime_structure_fingerprint(
            entities=fresh.scene_runtime_entities,
            scene_path=fresh._sr_runtime_scene_path,
            structural_edges=fresh._sr_structural_edges,
            signal_edges=fresh._sr_signal_edges,
            membrane_attach=fresh._sr_membrane_attach,
            membrane_template=fresh._sr_membrane_template,
        )
        structure = compare_sr_runtime_structure_fingerprints(source_structure, fresh_structure)
        fresh.restore_sr_runtime_snapshot_slice(
            copy.deepcopy(source_sr["snapshots"]), scene_time=source_sr["scene_time"]
        )
        fresh_dynamic = fresh.capture_sr_runtime_restore_envelope()
        canonical = lambda value: json.dumps(
            {"scene_time": value.get("scene_time"), "snapshots": value.get("snapshots")},
            ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        dynamic_equal = canonical(fresh_dynamic) == canonical(source_sr)
        fresh_sr = {
            "schema_version": 1,
            "status": "worldbridge_fresh_sr_restore_parity",
            "fresh_instance": True,
            "structure": structure,
            "dynamic_slice_restored": structure.get("equal") is True,
            "dynamic_state_equal": dynamic_equal,
            "cross_lane_parity": structure.get("equal") is True and dynamic_equal,
            "errors": [] if structure.get("equal") is True and dynamic_equal else [
                "sr_structure_mismatch" if structure.get("equal") is not True else "dynamic_state_mismatch"
            ],
            "default_ready": False,
            "replay_admitted": False,
            "lossless": False,
        }
        fresh._unified_pond.restore_serialized_state_in_place(copy.deepcopy(source_ps))
        restore_worldbridge_deterministic_randomness_context(
            fresh._worldbridge_opt_in_deterministic_randomness_context, source_rng
        )
        # The checkpoint input envelope contains host-local lane state plus
        # portable canonical input state and source-owned transport metadata.
        # Restore only the lane-local fields and canonical cursor here. The
        # fresh host must establish its own transport epoch below.
        canonical_sequence = source_input.pop("canonical_sequence", None)
        source_input.pop("shared_transport", None)
        source_input.pop("ps_handoff_input_events", None)
        if canonical_sequence is None:
            raise AssertionError("E505 canonical input sequence missing")
        WorldBridgeInputSequence.validate_snapshot(canonical_sequence)
        fresh.restore_sr_input_state(source_input)
        fresh._worldbridge_input_sequence.restore_snapshot(canonical_sequence)
        fresh_checkpoint = fresh.capture_worldbridge_live_checkpoint("e505-fresh")
        fresh_transport = fresh_checkpoint["input_state"]["shared_transport"]
        if fresh_transport["runtime_epoch"] != str(fresh._sr_runtime_epoch):
            raise AssertionError("E505 fresh transport epoch was not rebound")
        if fresh_transport["runtime_epoch"] == source_checkpoint["input_state"]["shared_transport"]["runtime_epoch"]:
            raise AssertionError("E505 fresh transport reused source epoch")
        fresh_ps = {
            "fresh_instance_created": fresh._unified_pond is not source._unified_pond,
            "canonical_state_equal": capture_canonical_ps_state(fresh._unified_pond)
            == source_ps_canonical,
        }
        fresh._update_scene_runtime_entities(0.05)
        fresh_next_rng = fresh._worldbridge_opt_in_deterministic_randomness_context.snapshot()
        witness = build_worldbridge_e504_fresh_dual_lane_witness(
            source_checkpoint=source_checkpoint,
            fresh_checkpoint=fresh_checkpoint,
            fresh_sr_restore=fresh_sr,
            fresh_ps_restore=fresh_ps,
            source_next_rng_snapshot=source_next_rng,
            fresh_next_rng_snapshot=fresh_next_rng,
        )
        if validate_worldbridge_e504_fresh_dual_lane_witness(witness) != {"valid": True, "errors": []}:
            raise AssertionError("E505 composite witness invalid")
        return {
            "status": "worldbridge_e505_fresh_host_reconstruction",
            "contract_valid": True,
            "fresh_host_created": True,
            "distinct_runtime_epochs": source._sr_runtime_epoch != fresh._sr_runtime_epoch,
            "fresh_dual_lane_parity": witness["fresh_dual_lane_parity"],
            "source_next_tick_executed": True,
            "fresh_next_tick_executed": True,
            "live_restore_admitted": False,
            "atomic_checkpoint": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
            "witness": witness,
            "source_checkpoint": copy.deepcopy(source_checkpoint),
            "fresh_checkpoint": copy.deepcopy(fresh_checkpoint),
            "source_structure": copy.deepcopy(source_structure),
            "source_next_rng_snapshot": copy.deepcopy(source_next_rng),
            "fresh_next_rng_snapshot": copy.deepcopy(fresh_next_rng),
        }
    finally:
        for viewport in (source, fresh):
            if viewport is None:
                continue
            viewport.deleteLater()
            QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not (sip.isdeleted(source) and sip.isdeleted(fresh)):
            raise AssertionError("E505 fresh host cleanup incomplete")


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
