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
from core.Lotucosm.runtime.world_bridge_e549_pause_reset_lifecycle_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e549_pause_reset_lifecycle_authority,
    validate_worldbridge_e549_pause_reset_lifecycle_authority,
)
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    WorldBridgeSharedStateReceiver,
    build_worldbridge_shared_state_envelope,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    RNG_PHASE_ORDER,
    WorldBridgeTickAuthority,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


OWNER = "game_viewport_clock"
EPOCH = "epoch-e549"


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


def _reseal_receipt(receipt: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(receipt)
    sealed["receipt_digest"] = ""
    sealed["receipt_digest"] = _digest(sealed)
    return sealed


def _authority() -> tuple[WorldBridgeTickAuthority, object]:
    context = create_worldbridge_deterministic_randomness_context(
        "e549-context", "e549-root"
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
    return authority, context


def _complete_tick(
    authority: WorldBridgeTickAuthority,
    *,
    decision_sequence: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    decision = issue_worldbridge_frame_clock_decision(
        1.0,
        paused=False,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
        decision_sequence=decision_sequence,
        bridge_handoff_requested=True,
    )
    context = authority.begin_tick(
        decision["sr_delta_seconds"],
        clock_decision=decision,
        clock_owner_token=OWNER,
        clock_runtime_epoch=EPOCH,
    )
    authority.record_clock_consumer("sr")
    authority.record_clock_consumer("ps")
    counts = {"sr.runtime": 1, "ps.pond": 1}
    for phase in RNG_PHASE_ORDER:
        authority.record_rng_phase(phase, draw_counts=counts)
    return authority.complete_tick(), copy.deepcopy(context["input_events"])


def _canonical_input(events: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "event_id": event["event_id"],
            "kind": event["kind"],
            "payload": {
                "canonical_sequence": event["sequence"],
                "pause_reset_epoch": event["pause_reset_epoch"],
                "event_digest": event["event_digest"],
                "data": event["payload"],
            },
        }
        for event in events
    ]


def _envelope(
    *,
    sequence: int,
    capture_epoch: int,
    pause_epoch: int,
    action: str,
    playing: bool,
    paused: bool,
    input_events: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return build_worldbridge_shared_state_envelope(
        envelope_id=f"e549-{sequence}",
        capture_epoch=capture_epoch,
        sequence=sequence,
        input_events=input_events or [],
        pause_reset_epoch=pause_epoch,
        clock_provenance={
            "sr": {
                "domain": "sr",
                "tick": capture_epoch,
                "delta": 0.05,
                "time": capture_epoch * 0.05,
                "source": "sr_runtime",
            },
            "ps": {
                "domain": "ps",
                "tick": capture_epoch,
                "delta": 0.05,
                "time": capture_epoch * 0.05,
                "source": "pond_update",
            },
        },
        bridge_identity_links=[],
        lifecycle_action=action,
        playing=playing,
        paused=paused,
    )


def _fixture() -> dict[str, object]:
    authority, _ = _authority()
    pause_receipt, pause_input_events = _complete_tick(
        authority, decision_sequence=1
    )
    assert pause_input_events == []

    authority.input_sequence.append("key_down", {"key": "W"})
    authority.input_sequence.append("key_up", {"key": "W"})
    before_pause = authority.input_sequence.snapshot()
    pre_pause_ids = [event["event_id"] for event in before_pause["pending"]]
    authority.reset(lifecycle_action="pause")
    after_pause = authority.input_sequence.snapshot()

    receiver = WorldBridgeSharedStateReceiver()
    receiver.accept(
        _envelope(
            sequence=0,
            capture_epoch=1,
            pause_epoch=0,
            action="tick",
            playing=True,
            paused=False,
        )
    )
    pause_envelope = _envelope(
        sequence=1,
        capture_epoch=2,
        pause_epoch=after_pause["pause_reset_epoch"],
        action="pause",
        playing=True,
        paused=True,
    )
    receiver.accept(pause_envelope)
    pause_transition = {
        "action": "pause",
        "before": before_pause,
        "after": after_pause,
        "receipt_before": pause_receipt,
        "receipt_after": None,
        "envelope": pause_envelope,
        "receiver_after": receiver.continuity_snapshot(),
        "discarded_event_ids": pre_pause_ids,
    }

    authority.input_sequence.append("key_down", {"key": "D"})
    before_resume = authority.input_sequence.snapshot()
    paused_ids = [event["event_id"] for event in before_resume["pending"]]
    authority.reset(lifecycle_action="resume")
    after_resume = authority.input_sequence.snapshot()
    resume_envelope = _envelope(
        sequence=2,
        capture_epoch=3,
        pause_epoch=after_resume["pause_reset_epoch"],
        action="resume",
        playing=True,
        paused=False,
    )
    receiver.accept(resume_envelope)
    resume_transition = {
        "action": "resume",
        "before": before_resume,
        "after": after_resume,
        "receipt_before": None,
        "receipt_after": None,
        "envelope": resume_envelope,
        "receiver_after": receiver.continuity_snapshot(),
        "discarded_event_ids": paused_ids,
    }

    stale_envelope = _envelope(
        sequence=3,
        capture_epoch=4,
        pause_epoch=after_pause["pause_reset_epoch"],
        action="pause",
        playing=True,
        paused=True,
    )
    receiver_before_stale = receiver.continuity_snapshot()
    stale_error = ""
    try:
        receiver.accept(stale_envelope)
    except ValueError as exc:
        stale_error = str(exc)
    receiver_after_stale = receiver.continuity_snapshot()
    stale_attempt = {
        "envelope": stale_envelope,
        "receiver_before": receiver_before_stale,
        "receiver_after": receiver_after_stale,
        "error": stale_error,
    }

    authority.input_sequence.append("key_down", {"key": "D"})
    authority.input_sequence.append("key_up", {"key": "D"})
    post_receipt, post_events = _complete_tick(authority, decision_sequence=2)
    post_envelope = _envelope(
        sequence=3,
        capture_epoch=4,
        pause_epoch=post_receipt["pause_reset_epoch"],
        action="tick",
        playing=True,
        paused=False,
        input_events=_canonical_input(post_events),
    )
    receiver.accept(post_envelope)
    post_tick = {
        "receipt": post_receipt,
        "input_events": post_events,
        "envelope": post_envelope,
        "receiver_after": receiver.continuity_snapshot(),
        "sequence_snapshot": authority.input_sequence.snapshot(),
    }
    return {
        "pause_transition": pause_transition,
        "resume_transition": resume_transition,
        "stale_transport_attempt": stale_attempt,
        "post_resume_tick": post_tick,
    }


def _build(fixture: dict[str, object] | None = None) -> dict[str, object]:
    return build_worldbridge_e549_pause_reset_lifecycle_authority(
        **(fixture or _fixture())
    )


def _assert_rejected(fixture: dict[str, object], error: str) -> None:
    with pytest.raises(ValueError, match=error):
        _build(fixture)


def test_e549_builds_and_validates_real_lifecycle_fixture() -> None:
    witness = _build()

    assert validate_worldbridge_e549_pause_reset_lifecycle_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"


def test_e549_rejects_pause_epoch_not_advanced() -> None:
    fixture = _fixture()
    fixture["pause_transition"]["after"]["pause_reset_epoch"] = 0
    _assert_rejected(fixture, "pause_epoch_not_advanced")


def test_e549_rejects_pending_not_cleared_on_resume() -> None:
    fixture = _fixture()
    fixture["resume_transition"]["after"]["pending"] = copy.deepcopy(
        fixture["resume_transition"]["before"]["pending"]
    )
    _assert_rejected(fixture, "resume_pending_not_cleared")


def test_e549_rejects_pre_pause_event_reused_after_resume() -> None:
    fixture = _fixture()
    fixture["post_resume_tick"]["input_events"][0]["event_id"] = fixture[
        "pause_transition"
    ]["discarded_event_ids"][0]
    _assert_rejected(fixture, "post_tick_input_invalid")


def test_e549_rejects_non_atomic_stale_epoch_failure() -> None:
    fixture = _fixture()
    fixture["stale_transport_attempt"]["receiver_after"]["last_sequence"] = 99
    _assert_rejected(fixture, "stale_rejection_mutated_receiver")


def test_e549_rejects_stale_rejection_for_wrong_reason() -> None:
    fixture = _fixture()
    fixture["stale_transport_attempt"]["error"] = "sequence continuity failure"
    _assert_rejected(fixture, "stale_epoch_not_rejected")


def test_e549_rejects_post_tick_input_digest_mismatch() -> None:
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["post_resume_tick"]["receipt"])
    receipt["input_digest"] = "0" * 64
    fixture["post_resume_tick"]["receipt"] = _reseal_receipt(receipt)
    _assert_rejected(fixture, "post_tick_input_receipt_mismatch")


def test_e549_rejects_post_tick_epoch_mismatch() -> None:
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["post_resume_tick"]["receipt"])
    receipt["pause_reset_epoch"] = 0
    fixture["post_resume_tick"]["receipt"] = _reseal_receipt(receipt)
    _assert_rejected(fixture, "post_tick_epoch_mismatch")


def test_e549_rejects_extra_keys_after_reseal() -> None:
    witness = _build()
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e549_rejects_proof_flag_tamper_after_reseal() -> None:
    witness = _build()
    witness["stale_rejection_atomic"] = False
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        candidate
    )
    assert validation["valid"] is False
    assert "stale_rejection_atomic_mismatch" in validation["errors"]
    assert "stale_rejection_atomic_not_true" in validation["errors"]


def test_e549_rejects_digest_tamper() -> None:
    witness = _build()
    witness["witness_digest"] = "0" * 64

    validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        witness
    )
    assert validation["valid"] is False
    assert "witness_digest_mismatch" in validation["errors"]


def test_e549_admission_evidence_is_validated_without_opening_authority() -> None:
    witness = _build()
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        pause_reset_lifecycle_witness=witness
    )

    evidence = admission["pause_reset_lifecycle_evidence"]
    assert evidence["validated"] is True
    assert evidence["grants_admission"] is False
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert admission["remaining_admission_blockers"] == baseline[
        "remaining_admission_blockers"
    ]
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e549_runtime_status_retains_read_only_evidence() -> None:
    witness = _build()
    status = build_runtime_worldbridge_status(
        pause_reset_lifecycle_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "pause_reset_lifecycle_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["admission_effect"] == "none"
    assert status["tick_replay_admission"]["default_ready"] is False


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e549_rejects_each_closed_admission_overclaim(field: str) -> None:
    witness = _build()
    witness[field] = True
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e549_pause_reset_lifecycle_authority(
        candidate
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]
