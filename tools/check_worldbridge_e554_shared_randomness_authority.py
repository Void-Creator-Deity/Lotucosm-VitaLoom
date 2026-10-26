#!/usr/bin/env python3
"""Verify E554 shared randomness evidence on a real GameViewport."""
from __future__ import annotations

import copy
import hashlib
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

from core.Lotucosm.runtime.world_bridge_e502_rng_draw_order_witness import (
    build_worldbridge_e502_rng_draw_order_witness,
)
from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
    validate_worldbridge_e538_shared_contract,
)
from core.Lotucosm.runtime.world_bridge_e546_shared_clock_delta_authority import (
    build_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    build_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_e548_rng_draw_order_authority import (
    build_worldbridge_e548_rng_draw_order_authority,
    validate_worldbridge_e548_rng_draw_order_authority,
)
from core.Lotucosm.runtime.world_bridge_e554_shared_randomness_authority import (
    PROOF_FIELDS,
    build_worldbridge_e554_shared_randomness_authority,
    validate_worldbridge_e554_shared_randomness_authority,
)
from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_admission_evidence,
    build_native_entropy_boundary_receipt,
    validate_native_admission_evidence,
    validate_native_entropy_boundary_receipt,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import RNG_PHASE_ORDER
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.Lotucosm.sr_physics2d import is_native_sr2d_available
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_sr2d_native_admission import verify as verify_native_admission
from tools.check_worldbridge_e548_rng_draw_order_authority import (
    _new_trusted_viewport,
    _require,
    _trusted_sample_project,
)


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


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _verify_project(project: Path, app: QApplication) -> dict[str, object]:
    scene = project / "scenes" / "challenge_scene.pond"
    viewport = _new_trusted_viewport(
        project,
        scene,
        context_id="e554-shared-randomness-context",
        root_seed="e554-shared-randomness-root-seed",
    )
    try:
        viewport._update_simulation()
        previous_receipt = viewport._worldbridge_last_tick_receipt
        _require(isinstance(previous_receipt, dict), "E554 previous receipt missing")

        organism = next(
            entity
            for entity in viewport.scene_runtime_entities
            if entity.entity_type == "organism"
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
        ps_events = copy.deepcopy(
            viewport._unified_pond.worldbridge_input_events_last_tick
        )
        context = viewport._worldbridge_opt_in_deterministic_randomness_context
        observations = copy.deepcopy(viewport._worldbridge_e502_rng_observations)
        snapshot = context.snapshot()
        _require(isinstance(receipt, dict), "E554 receipt missing")
        _require(isinstance(envelope, dict), "E554 envelope missing")
        _require(
            [item["phase"] for item in observations] == list(RNG_PHASE_ORDER),
            "E554 RNG phase order mismatch",
        )

        clock = build_worldbridge_e546_shared_clock_delta_authority(
            completed_tick_receipt=receipt,
            previous_completed_tick_receipt=previous_receipt,
            owner_token=str(viewport._worldbridge_clock_owner_token),
            runtime_epoch=str(viewport._sr_runtime_epoch),
        )
        queued = build_worldbridge_e547_queued_input_handoff_authority(
            completed_tick_receipt=receipt,
            shared_clock_delta_witness=clock,
            canonical_input_events=events,
            input_sequence_snapshot=(
                viewport._worldbridge_tick_authority.input_sequence.snapshot()
            ),
            shared_state_envelope=envelope,
            ps_received_input_events=ps_events,
        )
        draw = build_worldbridge_e502_rng_draw_order_witness(
            [envelope],
            observations,
        )
        draw_witness = build_worldbridge_e548_rng_draw_order_authority(
            completed_tick_receipt=receipt,
            queued_input_handoff_witness=queued,
            rng_draw_order_witness=draw,
            rng_context_snapshot=snapshot,
        )
        _require(
            validate_worldbridge_e548_rng_draw_order_authority(draw_witness)
            == {"valid": True, "errors": []},
            "E554 embedded E548 witness invalid",
        )

        checkpoint = viewport.capture_worldbridge_live_checkpoint(
            "e554-shared-randomness"
        )
        script_evidence = checkpoint["lifecycle"]["script_evidence"]
        checkpoint_native_receipt = checkpoint["randomness_state"][
            "native_boundary_receipt"
        ]
        _require(
            validate_native_entropy_boundary_receipt(
                checkpoint_native_receipt
            )
            == {"valid": True, "errors": []},
            "E554 checkpoint native receipt invalid",
        )
        physics = viewport._sr_physics_world
        _require(physics is not None, "E554 physics backend missing")
        native_capability = physics.backend_capability()
        requested_backend = str(viewport._sr2d_backend_request)
        native_admission_evidence = None
        if is_native_sr2d_available():
            native_admission_evidence = build_native_admission_evidence(
                verify_native_admission(repeats=1)
            )
            _require(
                validate_native_admission_evidence(
                    native_admission_evidence
                )
                == {"valid": True, "errors": []},
                "E554 native admission evidence invalid",
            )
            _require(
                native_admission_evidence["native_admitted"] is True,
                "E554 native admission was not proven",
            )
        native_receipt = build_native_entropy_boundary_receipt(
            native_admission_evidence=native_admission_evidence,
        )

        witness = build_worldbridge_e554_shared_randomness_authority(
            rng_draw_order_witness=draw_witness,
            script_evidence=script_evidence,
            native_boundary_receipt=native_receipt,
            native_backend_capability=native_capability,
            native_admission_evidence=native_admission_evidence,
            requested_native_backend=requested_backend,
            project_path=str(project),
        )
        _require(
            validate_worldbridge_e554_shared_randomness_authority(witness)
            == {"valid": True, "errors": []},
            "E554 witness invalid",
        )
        _require(
            all(witness[field] is True for field in PROOF_FIELDS),
            "E554 did not prove every randomness boundary",
        )
        _require(witness["grants_admission"] is False, "E554 granted admission")

        baseline = build_worldbridge_tick_replay_admission()
        admission = build_worldbridge_tick_replay_admission(
            shared_randomness_authority_witness=witness
        )
        evidence = admission["shared_randomness_authority_evidence"]
        _require(evidence["validated"] is True, "admission rejected E554")
        _require(evidence["witness_digest"] == witness["witness_digest"], "E554 digest drift")
        _require(
            "shared_random_seed_contract_missing"
            not in admission["remaining_admission_blockers"],
            "E554 did not remove the randomness blocker",
        )
        _require(
            len(admission["remaining_admission_blockers"])
            == len(baseline["remaining_admission_blockers"]) - 1,
            "E554 removed more than the randomness blocker",
        )
        _require(admission["tick_merge_admitted"] is False, "tick merge opened")
        _require(
            admission["full_unified_replay_admitted"] is False,
            "full replay opened",
        )
        _require(admission["default_ready"] is False, "default readiness opened")

        contract = build_worldbridge_e538_shared_contracts(
            shared_randomness_authority_witness=witness
        )
        _require(
            validate_worldbridge_e538_shared_contract(contract)
            == {"valid": True, "errors": []},
            "E554 E538 contract invalid",
        )
        status = build_runtime_worldbridge_status(
            project,
            shared_randomness_authority_witness=witness,
        )
        status_evidence = status["tick_replay_admission"][
            "shared_randomness_authority_evidence"
        ]
        _require(status_evidence["validated"] is True, "status rejected E554")

        tampered = copy.deepcopy(witness)
        tampered["script_evidence"]["owner_registry_digest"] = "0" * 64
        tampered = _reseal_witness(tampered)
        tampered_validation = (
            validate_worldbridge_e554_shared_randomness_authority(tampered)
        )
        _require(tampered_validation["valid"] is False, "tampered E554 accepted")
        _require(
            "dynamic_script_owner_binding_mismatch"
            in tampered_validation["errors"],
            "tampered script owner was not diagnosed",
        )

        return {
            "schema_version": 1,
            "status": "worldbridge_e554_shared_randomness_authority",
            "real_game_viewport": True,
            "read_only": True,
            "tick_sequence": receipt["tick_sequence"],
            "rng_context_id": witness["rng_context_id"],
            "shared_root_seed_digest": witness["shared_root_seed_digest"],
            "stream_registration": witness["stream_registration"],
            "dynamic_script_count": len(script_evidence["audits"]),
            "native_closure_mode": witness["native_closure_mode"],
            "native_runtime_adapter_available": witness[
                "native_runtime_adapter_available"
            ],
            "native_admission_digest": (
                None
                if witness["native_admission_evidence"] is None
                else witness["native_admission_evidence"]["digest"]
            ),
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "witness": witness,
            "tampered_script_owner_rejected": True,
            "tampered_errors": tampered_validation["errors"],
            "remaining_admission_blockers": admission[
                "remaining_admission_blockers"
            ],
            "shared_random_seed_contract": contract["admissions"][
                "shared_random_seed_contract"
            ],
            "cross_lane_rng_draw_order_admitted": contract["admissions"][
                "cross_lane_rng_draw_order_admitted"
            ],
            "tick_merge_admitted": admission["tick_merge_admitted"],
            "full_unified_replay_admitted": admission[
                "full_unified_replay_admitted"
            ],
            "default_ready": admission["default_ready"],
            "contract_valid": True,
            "errors": [],
            "ok": True,
        }
    finally:
        viewport.deleteLater()
        QCoreApplication.sendPostedEvents(viewport, QEvent.Type.DeferredDelete)
        app.processEvents()
        if not sip.isdeleted(viewport):
            raise AssertionError("E554 viewport cleanup incomplete")


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
