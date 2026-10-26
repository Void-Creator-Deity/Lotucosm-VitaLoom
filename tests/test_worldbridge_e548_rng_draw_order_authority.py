# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import hashlib
import json
import random

import numpy as np
import pytest

from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (
    issue_worldbridge_frame_clock_decision,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_e502_rng_draw_order_witness import (
    build_worldbridge_e502_rng_draw_order_witness,
    capture_worldbridge_e502_rng_phase_boundary,
    validate_worldbridge_e502_rng_draw_order_witness,
)
from core.Lotucosm.runtime.world_bridge_e546_shared_clock_delta_authority import (
    build_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    build_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_e548_rng_draw_order_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e548_rng_draw_order_authority,
    validate_worldbridge_e548_rng_draw_order_authority,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    RNG_PHASE_ORDER,
    WorldBridgeTickAuthority,
    validate_worldbridge_tick_receipt,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

from test_worldbridge_e547_queued_input_handoff_authority import (
    _envelope,
    _reseal_receipt,
    _reseal_witness,
)


OWNER = "game_viewport_clock"
EPOCH = "epoch-e548"


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


def _clock_witness(receipt: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e546_shared_clock_delta_authority(
        completed_tick_receipt=receipt,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
    )


def _reseal_rng_phase(record: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(record)
    sealed["record_digest"] = ""
    sealed["record_digest"] = _digest(
        {
            key: value
            for key, value in sealed.items()
            if key != "record_digest"
        }
    )
    return sealed


def _reseal_context_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(snapshot)
    sealed["snapshot_digest"] = ""
    sealed["snapshot_digest"] = _digest(sealed)
    return sealed


def _reseal_draw_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _fixture(
    *,
    consume_sr: bool = True,
    consume_ps: bool = True,
    context_id: str = "e548-test",
) -> dict[str, object]:
    context = create_worldbridge_deterministic_randomness_context(
        context_id, "e548-root-seed"
    )
    register_worldbridge_deterministic_random_stream(
        context,
        "sr.runtime",
        "python_random",
        stream=random.Random(17),
    )
    register_worldbridge_deterministic_random_stream(
        context,
        "ps.pond",
        "numpy_pcg64_generator",
        stream=np.random.Generator(np.random.PCG64(29)),
    )
    authority = WorldBridgeTickAuthority()
    authority.bind_randomness_context(context)
    decision = issue_worldbridge_frame_clock_decision(
        1.0,
        paused=False,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
        decision_sequence=1,
        bridge_handoff_requested=True,
    )
    authority.begin_tick(
        decision["sr_delta_seconds"],
        clock_decision=decision,
        clock_owner_token=OWNER,
        clock_runtime_epoch=EPOCH,
    )
    authority.record_clock_consumer("sr")
    authority.record_clock_consumer("ps")
    observations = []
    counts = {"sr.runtime": 0, "ps.pond": 0}
    for order, phase in enumerate(RNG_PHASE_ORDER):
        if consume_sr and phase == "sr.complete":
            context.get_stream("sr.runtime").random()
            counts["sr.runtime"] += 1
        if consume_ps and phase == "ps.complete":
            context.get_stream("ps.pond").random()
            counts["ps.pond"] += 1
        authority.record_rng_phase(phase, draw_counts=counts)
        observations.append(
            capture_worldbridge_e502_rng_phase_boundary(
                context,
                phase,
                order,
                draw_counts=counts,
            )
        )
    receipt = authority.complete_tick()
    snapshot = context.snapshot()
    envelope = _envelope([], receipt)
    clock = _clock_witness(receipt)
    queued = build_worldbridge_e547_queued_input_handoff_authority(
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=clock,
        canonical_input_events=[],
        input_sequence_snapshot=authority.input_sequence.snapshot(),
        shared_state_envelope=envelope,
        ps_received_input_events=[],
    )
    draw = build_worldbridge_e502_rng_draw_order_witness(
        [envelope], observations
    )
    return {
        "context": context,
        "authority": authority,
        "receipt": receipt,
        "snapshot": snapshot,
        "envelope": envelope,
        "clock": clock,
        "queued": queued,
        "draw": draw,
    }


def _build(fixture: dict[str, object], **overrides) -> dict[str, object]:
    values = {
        "completed_tick_receipt": fixture["receipt"],
        "queued_input_handoff_witness": fixture["queued"],
        "rng_draw_order_witness": fixture["draw"],
        "rng_context_snapshot": fixture["snapshot"],
    }
    values.update(overrides)
    return build_worldbridge_e548_rng_draw_order_authority(**values)


def _assert_rejected(fixture: dict[str, object], reason: str, **overrides) -> None:
    with pytest.raises(ValueError) as raised:
        _build(fixture, **overrides)
    assert reason in str(raised.value)


def test_e548_valid_single_tick_rng_order_is_detached_and_closed():
    fixture = _fixture()
    witness = _build(fixture)

    assert validate_worldbridge_e548_rng_draw_order_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert witness["phase_order"] == list(RNG_PHASE_ORDER)
    assert witness["registration_order"] == ["sr.runtime", "ps.pond"]
    assert witness["phase_draw_counts"] == [
        {"sr.runtime": 0, "ps.pond": 0},
        {"sr.runtime": 1, "ps.pond": 0},
        {"sr.runtime": 1, "ps.pond": 0},
        {"sr.runtime": 1, "ps.pond": 1},
    ]
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["rng_context_id"] == fixture["receipt"]["rng_context_id"]
    assert witness["rng_start_digest"] == fixture["receipt"]["rng_start_digest"]
    assert witness["rng_end_digest"] == fixture["receipt"]["rng_end_digest"]
    assert witness["read_only"] is True
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)

    witness["rng_draw_order_witness"]["observations"][0]["phase"] = "ps.start"
    assert fixture["draw"]["observations"][0]["phase"] == "sr.start"


def test_e548_rejects_missing_sr_draw_observation():
    fixture = _fixture(consume_sr=False)
    _assert_rejected(fixture, "sr_draw_observed_not_observed")


def test_e548_rejects_missing_ps_draw_observation():
    fixture = _fixture(consume_ps=False)
    _assert_rejected(fixture, "ps_draw_observed_not_observed")


def test_e548_default_admission_has_no_rng_evidence():
    admission = build_worldbridge_tick_replay_admission()

    assert admission["rng_draw_order_evidence"] == {
        "evidence_available": False,
        "validated": False,
        "errors": [],
        "witness_digest": None,
        "grants_admission": False,
        "admission_effect": "none",
    }
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e548_valid_evidence_is_aggregated_without_opening_admission():
    fixture = _fixture()
    witness = _build(fixture)
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        rng_draw_order_witness=witness
    )

    assert admission["rng_draw_order_evidence"] == {
        "evidence_available": True,
        "validated": True,
        "errors": [],
        "witness_digest": witness["witness_digest"],
        "grants_admission": False,
        "admission_effect": "none",
    }
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False
    assert admission["remaining_admission_blockers"] == baseline[
        "remaining_admission_blockers"
    ]
    assert admission["do_not_claim"] == baseline["do_not_claim"]


def test_e548_invalid_evidence_is_rejected_by_admission():
    witness = _build(_fixture())
    witness["witness_digest"] = "0" * 64
    admission = build_worldbridge_tick_replay_admission(
        rng_draw_order_witness=witness
    )
    evidence = admission["rng_draw_order_evidence"]

    assert evidence["evidence_available"] is True
    assert evidence["validated"] is False
    assert "witness_digest_mismatch" in evidence["errors"]
    assert evidence["grants_admission"] is False
    assert admission["default_ready"] is False


def test_e548_runtime_status_passes_evidence_without_opening_admission():
    witness = _build(_fixture())
    status = build_runtime_worldbridge_status(rng_draw_order_witness=witness)
    admission = status["tick_replay_admission"]
    evidence = admission["rng_draw_order_evidence"]

    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["grants_admission"] is False
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e548_rejects_wrong_phase_order_in_draw_witness():
    fixture = _fixture()
    draw = copy.deepcopy(fixture["draw"])
    draw["observations"][2], draw["observations"][3] = (
        draw["observations"][3],
        draw["observations"][2],
    )
    draw = _reseal_draw_witness(draw)

    _assert_rejected(fixture, "draw_observation_phase_order_invalid", rng_draw_order_witness=draw)


def test_e548_rejects_envelope_binding_mismatch_after_reseal():
    fixture = _fixture()
    draw = copy.deepcopy(fixture["draw"])
    draw["envelope_digests"] = ["0" * 64]
    draw = _reseal_draw_witness(draw)

    _assert_rejected(
        fixture,
        "draw_envelope_binding_mismatch",
        rng_draw_order_witness=draw,
    )


def test_e548_rejects_receipt_phase_draw_count_mismatch_after_reseal():
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["receipt"])
    receipt["rng_phases"][1]["draw_counts"]["sr.runtime"] = 0
    receipt["rng_phases"][1] = _reseal_rng_phase(receipt["rng_phases"][1])
    receipt = _reseal_receipt(receipt)
    queued = build_worldbridge_e547_queued_input_handoff_authority(
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
        canonical_input_events=[],
        input_sequence_snapshot=fixture["authority"].input_sequence.snapshot(),
        shared_state_envelope=fixture["envelope"],
        ps_received_input_events=[],
    )

    _assert_rejected(
        fixture,
        "receipt_rng_phase_mismatch",
        completed_tick_receipt=receipt,
        queued_input_handoff_witness=queued,
    )


def test_e548_rejects_start_snapshot_drift_after_reseal():
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["receipt"])
    receipt["rng_start_digest"] = "0" * 64
    receipt = _reseal_receipt(receipt)
    queued = build_worldbridge_e547_queued_input_handoff_authority(
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
        canonical_input_events=[],
        input_sequence_snapshot=fixture["authority"].input_sequence.snapshot(),
        shared_state_envelope=fixture["envelope"],
        ps_received_input_events=[],
    )

    _assert_rejected(
        fixture,
        "draw_start_snapshot_mismatch",
        completed_tick_receipt=receipt,
        queued_input_handoff_witness=queued,
    )


def test_e548_rejects_end_context_snapshot_drift_after_reseal():
    fixture = _fixture()
    snapshot = copy.deepcopy(fixture["snapshot"])
    snapshot["streams"][1]["state"]["state"]["state"] += 1
    snapshot = _reseal_context_snapshot(snapshot)

    _assert_rejected(
        fixture,
        "draw_end_snapshot_mismatch",
        rng_context_snapshot=snapshot,
    )


def test_e548_rejects_context_id_drift_after_reseal():
    fixture = _fixture()
    snapshot = copy.deepcopy(fixture["snapshot"])
    snapshot["context_id"] = "e548-other"
    snapshot = _reseal_context_snapshot(snapshot)

    _assert_rejected(
        fixture,
        "snapshot_context_id_mismatch",
        rng_context_snapshot=snapshot,
    )


def test_e548_rejects_queued_witness_for_different_receipt():
    fixture = _fixture()
    other = _fixture(context_id="e548-other")
    _assert_rejected(
        fixture,
        "queued_witness_receipt_mismatch",
        queued_input_handoff_witness=other["queued"],
    )


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e548_rejects_each_admission_overclaim_after_reseal(field: str):
    witness = _build(_fixture())
    witness[field] = True
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e548_rng_draw_order_authority(candidate)
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e548_rejects_extra_keys_with_valid_reseal():
    witness = _build(_fixture())
    candidate = _reseal_witness({**witness, "unexpected_evidence": True})

    validation = validate_worldbridge_e548_rng_draw_order_authority(candidate)
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e548_rejects_embedded_draw_proof_flag_tamper_after_reseal():
    witness = _build(_fixture())
    witness["sr_before_ps"] = False
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e548_rng_draw_order_authority(candidate)
    assert validation["valid"] is False
    assert "sr_before_ps_not_true" in validation["errors"]
    assert "sr_before_ps_mismatch" in validation["errors"]
