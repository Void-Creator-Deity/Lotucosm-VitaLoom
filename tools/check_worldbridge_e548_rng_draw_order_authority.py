# -*- coding: utf-8 -*-
"""Verify E548 single-tick ordered RNG draws on a real viewport."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
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

from core.Lotucosm.runtime.world_bridge_e502_rng_draw_order_witness import (
    build_worldbridge_e502_rng_draw_order_witness,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.Lotucosm.runtime.world_bridge_e546_shared_clock_delta_authority import (
    build_worldbridge_e546_shared_clock_delta_authority,
    validate_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    build_worldbridge_e547_queued_input_handoff_authority,
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_e548_rng_draw_order_authority import (
    PROOF_FIELDS,
    build_worldbridge_e548_rng_draw_order_authority,
    validate_worldbridge_e548_rng_draw_order_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    RNG_PHASE_ORDER,
    validate_worldbridge_tick_receipt,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from core.VitaLoom.scene import get_scene_manager
from core.VitaLoom.suite.project_lock import ensure_project_lock
from core.VitaLoom.viewports.game_viewport import GameViewport


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reseal_context_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(snapshot)
    sealed["snapshot_digest"] = ""
    sealed["snapshot_digest"] = _digest(sealed)
    return sealed


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


@contextmanager
def _trusted_sample_project(root: Path):
    source = root / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    with tempfile.TemporaryDirectory(prefix="vitaloom-e548-") as temp_root:
        project = Path(temp_root) / source.name
        shutil.copytree(source, project)
        scene_path = project / "scenes" / "challenge_scene.pond"
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        script_names = sorted(
            {
                str(script["name"])
                for entity in scene_data.get("entities", [])
                for script in entity.get("scripts", [])
                if isinstance(script, dict) and str(script.get("name") or "").strip()
            }
        )
        grants = []
        for name in script_names:
            script_path = project / "scripts" / f"{name}.py"
            _require(script_path.is_file(), f"E548 trusted script missing: {name}")
            grants.append(
                {
                    "path": script_path.relative_to(project).as_posix(),
                    "sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
                }
            )
        manifest_path = project / "project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["script_trust"] = {"sha256_allowlist": grants}
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        ensure_project_lock(project, repo_root=root, overwrite=True)
        yield project


def _new_trusted_viewport(
    project: Path,
    scene: Path,
    *,
    context_id: str,
    root_seed: str,
) -> GameViewport:
    scene_manager = get_scene_manager()
    scene_manager.clear_scene(notify=False)
    viewport = GameViewport()
    viewport.editor_context.current_project_path = str(project)
    _require(scene_manager.load_scene(str(scene)), "E548 trusted scene load failed")
    viewport._using_scene_runtime = True
    viewport._sr_runtime_scene_path = str(scene)
    _require(
        isinstance(viewport._begin_sr_snapshot_lifetime(), str),
        "E548 SR runtime epoch missing",
    )
    _require(
        viewport._load_scene_runtime_entities(),
        "E548 trusted SR runtime load failed",
    )
    _require(
        not viewport._sr_script_failure_receipts,
        "E548 trusted script load produced failures",
    )
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(
        create_worldbridge_deterministic_randomness_context(context_id, root_seed)
    )
    viewport._unified_pond_mode = True
    viewport._ensure_unified_pond()
    viewport.is_playing = True
    viewport.is_paused = False
    return viewport


def _verify_project(project: Path, app: QApplication) -> dict[str, object]:
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_trusted_viewport(
        project,
        scene,
        context_id="e548-rng-order-context",
        root_seed="e548-rng-order-root-seed",
    )
    try:
        viewport._update_simulation()
        previous_receipt = viewport._worldbridge_last_tick_receipt
        _require(isinstance(previous_receipt, dict), "E548 previous receipt missing")

        organism = next(
            entity
            for entity in viewport.scene_runtime_entities
            if entity.entity_type == "organism"
        )
        _require(bool(organism.scripts), "E548 organism script missing")
        _require(
            hasattr(organism.scripts[0], "_repro_cooldown"),
            "E548 reproduction script missing",
        )
        organism.set_energy(1000.0)
        organism.scripts[0]._repro_acc = organism.scripts[0]._repro_cooldown
        viewport._unified_pond.time = 99
        viewport._sr_input_press("W")
        viewport._sr_input_release("W")
        viewport._update_simulation()
        receipt = viewport._worldbridge_last_tick_receipt
        envelope = viewport._worldbridge_last_shared_state_envelope
        events = copy.deepcopy(viewport._worldbridge_input_events_last_tick)
        ps_events = viewport._unified_pond.worldbridge_input_events_last_tick
        context = viewport._worldbridge_opt_in_deterministic_randomness_context
        observations = copy.deepcopy(viewport._worldbridge_e502_rng_observations)
        snapshot = context.snapshot()

        _require(isinstance(receipt, dict), "E548 current receipt missing")
        _require(
            validate_worldbridge_tick_receipt(receipt)
            == {"valid": True, "errors": []},
            "E548 receipt invalid",
        )
        _require(isinstance(envelope, dict), "E548 envelope missing")
        _require(
            len(observations) == len(RNG_PHASE_ORDER),
            "E548 real RNG observation count mismatch",
        )
        _require(
            [item["phase"] for item in observations] == list(RNG_PHASE_ORDER),
            "E548 real RNG phase order mismatch",
        )
        _require(
            receipt["rng_phase_count"] == len(RNG_PHASE_ORDER),
            "E548 receipt RNG phase count mismatch",
        )
        _require(
            receipt["rng_start_digest"] == observations[0]["snapshot_digest"],
            "E548 start snapshot mismatch",
        )
        _require(
            receipt["rng_end_digest"] == snapshot["snapshot_digest"],
            "E548 end snapshot mismatch",
        )

        clock = build_worldbridge_e546_shared_clock_delta_authority(
            completed_tick_receipt=receipt,
            previous_completed_tick_receipt=previous_receipt,
            owner_token=str(viewport._worldbridge_clock_owner_token),
            runtime_epoch=str(viewport._sr_runtime_epoch),
        )
        _require(
            validate_worldbridge_e546_shared_clock_delta_authority(clock)
            == {"valid": True, "errors": []},
            "E548 clock evidence invalid",
        )
        queued = build_worldbridge_e547_queued_input_handoff_authority(
            completed_tick_receipt=receipt,
            shared_clock_delta_witness=clock,
            canonical_input_events=events,
            input_sequence_snapshot=viewport._worldbridge_tick_authority.input_sequence.snapshot(),
            shared_state_envelope=envelope,
            ps_received_input_events=ps_events,
        )
        _require(
            validate_worldbridge_e547_queued_input_handoff_authority(queued)
            == {"valid": True, "errors": []},
            "E548 queued-input evidence invalid",
        )
        draw = build_worldbridge_e502_rng_draw_order_witness(
            [envelope], observations
        )
        witness = build_worldbridge_e548_rng_draw_order_authority(
            completed_tick_receipt=receipt,
            queued_input_handoff_witness=queued,
            rng_draw_order_witness=draw,
            rng_context_snapshot=snapshot,
        )
        _require(
            validate_worldbridge_e548_rng_draw_order_authority(witness)
            == {"valid": True, "errors": []},
            "E548 witness invalid",
        )
        _require(
            all(witness[field] is True for field in PROOF_FIELDS),
            "E548 did not prove every RNG boundary",
        )
        _require(witness["phase_draw_counts"][1]["sr.runtime"] > witness["phase_draw_counts"][0]["sr.runtime"], "E548 SR draw not observed")
        _require(witness["phase_draw_counts"][3]["ps.pond"] > witness["phase_draw_counts"][2]["ps.pond"], "E548 PS draw not observed")
        _require(witness["grants_admission"] is False, "E548 granted admission")
        _require(witness["admission_effect"] == "none", "E548 changed effect")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            rng_draw_order_witness=witness
        )
        evidence = admission["rng_draw_order_evidence"]
        _require(evidence["validated"] is True, "admission rejected E548")
        _require(evidence["grants_admission"] is False, "E548 granted evidence")
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")
        _require(
            admission["remaining_admission_blockers"]
            == baseline["remaining_admission_blockers"],
            "E548 changed blockers",
        )

        status = build_runtime_worldbridge_status(
            project,
            rng_draw_order_witness=witness,
        )
        status_admission = status["tick_replay_admission"]
        status_evidence = status_admission["rng_draw_order_evidence"]
        _require(status_evidence["validated"] is True, "status dropped E548")
        _require(
            status_evidence["witness_digest"] == witness["witness_digest"],
            "status changed E548 digest",
        )
        _require(status_admission["default_ready"] is False, "status opened readiness")

        tampered = copy.deepcopy(witness)
        tampered_snapshot = tampered["rng_context_snapshot"]
        tampered_snapshot["streams"][1]["state"]["state"]["state"] += 1
        tampered["rng_context_snapshot"] = _reseal_context_snapshot(
            tampered_snapshot
        )
        tampered = _reseal_witness(tampered)
        tampered_validation = validate_worldbridge_e548_rng_draw_order_authority(
            tampered
        )
        _require(tampered_validation["valid"] is False, "tampered RNG context accepted")
        _require(
            "draw_end_snapshot_mismatch" in tampered_validation["errors"],
            "tampered RNG context was not diagnosed",
        )
        _require(
            context.snapshot()["snapshot_digest"] == snapshot["snapshot_digest"],
            "tamper check mutated the live RNG context",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e548_rng_draw_order_authority",
            "real_game_viewport": True,
            "read_only": True,
            "tick_sequence": receipt["tick_sequence"],
            "decision_digest": receipt["clock_decision"]["decision_digest"],
            "rng_context_id": witness["rng_context_id"],
            "rng_start_digest": witness["rng_start_digest"],
            "rng_end_digest": witness["rng_end_digest"],
            "phase_order": witness["phase_order"],
            "registration_order": witness["registration_order"],
            "phase_draw_counts": witness["phase_draw_counts"],
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "admission_evidence": evidence,
            "runtime_status_evidence_validated": status_evidence["validated"],
            "tampered_rng_context_rejected": True,
            "tampered_errors": tampered_validation["errors"],
            "shared_random_seed_contract": False,
            "cross_lane_rng_draw_order_admitted": False,
            "rng_checkpoint_admitted": False,
            "rng_replay_admitted": False,
            "tick_merge_admitted": admission["tick_merge_admitted"],
            "full_unified_replay_admitted": admission[
                "full_unified_replay_admitted"
            ],
            "default_ready": admission["default_ready"],
            "remaining_admission_blockers": admission[
                "remaining_admission_blockers"
            ],
            "grants_admission": False,
            "admission_effect": "none",
            "contract_valid": True,
            "errors": [],
            "ok": True,
        }
    finally:
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E548 viewport cleanup incomplete")


def verify() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    with _trusted_sample_project(ROOT) as project:
        return _verify_project(project, app)


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
