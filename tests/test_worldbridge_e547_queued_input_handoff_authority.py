# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (
    issue_worldbridge_frame_clock_decision,
)
from core.Lotucosm.runtime.world_bridge_e546_shared_clock_delta_authority import (
    build_worldbridge_e546_shared_clock_delta_authority,
)
from core.Lotucosm.runtime.world_bridge_e547_queued_input_handoff_authority import (
    CLOSED_ADMISSION_FIELDS,
    build_worldbridge_e547_queued_input_handoff_authority,
    validate_worldbridge_e547_queued_input_handoff_authority,
)
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    build_worldbridge_shared_state_envelope,
)
from core.Lotucosm.runtime.world_bridge_tick_authority import (
    WorldBridgeTickAuthority,
    validate_worldbridge_tick_receipt,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


OWNER = "game_viewport_clock"
EPOCH = "epoch-e547"


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


def _reseal_receipt(receipt: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(receipt)
    sealed["receipt_digest"] = ""
    sealed["receipt_digest"] = _digest(sealed)
    return sealed


def _reseal_envelope(envelope: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(envelope)
    sealed["envelope_digest"] = ""
    sealed["envelope_digest"] = _digest(sealed)
    return sealed


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _clock_witness(receipt: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e546_shared_clock_delta_authority(
        completed_tick_receipt=receipt,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
    )


def _transport_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
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
    events: list[dict[str, object]],
    receipt: dict[str, object],
) -> dict[str, object]:
    delta = receipt["delta_time"]
    return build_worldbridge_shared_state_envelope(
        envelope_id="e547-shared-1",
        capture_epoch=1,
        sequence=0,
        input_events=_transport_events(events),
        pause_reset_epoch=receipt["pause_reset_epoch"],
        clock_provenance={
            "sr": {
                "domain": "sr",
                "tick": receipt["tick_sequence"],
                "delta": delta,
                "time": float(receipt["tick_sequence"]),
                "source": "viewport_snapshot",
            },
            "ps": {
                "domain": "ps",
                "tick": receipt["tick_sequence"],
                "delta": delta,
                "time": float(receipt["tick_sequence"]),
                "source": "pond_update",
            },
        },
        bridge_identity_links=[],
    )


def _fixture(
    *, with_event: bool = True, event_count: int | None = None
) -> dict[str, object]:
    authority = WorldBridgeTickAuthority()
    count = (1 if with_event else 0) if event_count is None else event_count
    for index in range(count):
        authority.input_sequence.append(
            "key_down" if index % 2 == 0 else "key_up",
            {"key": "W"},
        )
    decision = issue_worldbridge_frame_clock_decision(
        1.0,
        paused=False,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
        decision_sequence=1,
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
    receipt = authority.complete_tick()
    events = copy.deepcopy(context["input_events"])
    snapshot = authority.input_sequence.snapshot()
    envelope = _envelope(events, receipt)
    clock = _clock_witness(receipt)
    return {
        "authority": authority,
        "decision": decision,
        "receipt": receipt,
        "events": events,
        "snapshot": snapshot,
        "envelope": envelope,
        "clock": clock,
        "ps_events": copy.deepcopy(events),
    }


def _build(fixture: dict[str, object], **overrides) -> dict[str, object]:
    values = {
        "completed_tick_receipt": fixture["receipt"],
        "shared_clock_delta_witness": fixture["clock"],
        "canonical_input_events": fixture["events"],
        "input_sequence_snapshot": fixture["snapshot"],
        "shared_state_envelope": fixture["envelope"],
        "ps_received_input_events": fixture["ps_events"],
    }
    values.update(overrides)
    return build_worldbridge_e547_queued_input_handoff_authority(**values)


def _assert_rejected(fixture: dict[str, object], reason: str, **overrides) -> None:
    with pytest.raises(ValueError) as raised:
        _build(fixture, **overrides)
    assert reason in str(raised.value)


def test_e547_valid_batch_is_detached_sealed_and_closed():
    fixture = _fixture()
    witness = _build(fixture)

    assert validate_worldbridge_e547_queued_input_handoff_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert witness["canonical_input_events"] == fixture["events"]
    assert witness["canonical_input_events"] is not fixture["events"]
    assert witness["ps_received_input_events"] == fixture["events"]
    assert witness["shared_state_envelope"] == fixture["envelope"]
    assert witness["input_sequence_snapshot"] == fixture["snapshot"]
    assert witness["event_count"] == 1
    assert witness["first_input_sequence"] == witness["last_input_sequence"] == 1
    assert witness["batch_contiguous"] is True
    assert witness["receipt_batch_bound"] is True
    assert witness["envelope_batch_bound"] is True
    assert witness["sr_pending_empty_after_tick"] is True
    assert witness["canonical_event_ids_consumed"] is True
    assert witness["ps_received_batch_identical"] is True
    assert witness["same_tick_delta_observed"] is True
    assert witness["read_only"] is True
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert len(witness["witness_digest"]) == 64
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)

    witness["canonical_input_events"][0]["payload"]["key"] = "A"
    assert fixture["events"][0]["payload"]["key"] == "W"


def test_e547_empty_tick_batch_is_valid_without_fabricating_events():
    fixture = _fixture(with_event=False)
    witness = _build(fixture)

    assert witness["event_count"] == 0
    assert witness["first_input_sequence"] is None
    assert witness["last_input_sequence"] is None
    assert witness["batch_contiguous"] is True
    assert witness["ps_received_batch_identical"] is True
    assert validate_worldbridge_e547_queued_input_handoff_authority(witness)[
        "valid"
    ] is True


def test_e547_default_admission_has_no_queued_input_evidence():
    admission = build_worldbridge_tick_replay_admission()

    assert admission["queued_input_handoff_evidence"] == {
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


def test_e547_valid_evidence_is_aggregated_without_opening_admission():
    fixture = _fixture()
    witness = _build(fixture)
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        queued_input_handoff_witness=witness
    )

    assert admission["queued_input_handoff_evidence"] == {
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


def test_e547_invalid_evidence_is_rejected_by_admission():
    fixture = _fixture()
    witness = _build(fixture)
    witness["witness_digest"] = "0" * 64
    admission = build_worldbridge_tick_replay_admission(
        queued_input_handoff_witness=witness
    )
    evidence = admission["queued_input_handoff_evidence"]

    assert evidence["evidence_available"] is True
    assert evidence["validated"] is False
    assert "witness_digest_mismatch" in evidence["errors"]
    assert evidence["grants_admission"] is False
    assert admission["default_ready"] is False


def test_e547_runtime_status_passes_evidence_without_opening_admission():
    fixture = _fixture()
    witness = _build(fixture)
    status = build_runtime_worldbridge_status(
        queued_input_handoff_witness=witness
    )
    admission = status["tick_replay_admission"]
    evidence = admission["queued_input_handoff_evidence"]

    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["grants_admission"] is False
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e547_rejects_receipt_count_mismatch_after_reseal():
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["receipt"])
    receipt["input_event_count"] = 2
    receipt = _reseal_receipt(receipt)
    assert validate_worldbridge_tick_receipt(receipt) == {
        "valid": True,
        "errors": [],
    }

    _assert_rejected(
        fixture,
        "receipt_input_event_count_mismatch",
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
    )


def test_e547_rejects_receipt_digest_mismatch_after_reseal():
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["receipt"])
    receipt["input_digest"] = "0" * 64
    receipt = _reseal_receipt(receipt)
    assert validate_worldbridge_tick_receipt(receipt) == {
        "valid": True,
        "errors": [],
    }

    _assert_rejected(
        fixture,
        "receipt_input_digest_mismatch",
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
    )


def test_e547_rejects_tampered_canonical_event_digest():
    fixture = _fixture()
    events = copy.deepcopy(fixture["events"])
    events[0]["payload"]["key"] = "A"

    _assert_rejected(
        fixture,
        "canonical_input_event_0_digest_invalid",
        canonical_input_events=events,
        ps_received_input_events=events,
    )


def test_e547_rejects_reordered_canonical_batch():
    fixture = _fixture()
    authority = WorldBridgeTickAuthority()
    authority.input_sequence.append("key_down", {"key": "W"})
    authority.input_sequence.append("key_up", {"key": "W"})
    decision = issue_worldbridge_frame_clock_decision(
        1.0,
        paused=False,
        owner_token=OWNER,
        runtime_epoch=EPOCH,
        decision_sequence=1,
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
    receipt = authority.complete_tick()
    events = copy.deepcopy(context["input_events"])
    reordered = [copy.deepcopy(events[1]), copy.deepcopy(events[0])]

    _assert_rejected(
        fixture,
        "canonical_input_event_1_sequence_invalid",
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
        canonical_input_events=reordered,
        input_sequence_snapshot=authority.input_sequence.snapshot(),
        shared_state_envelope=_envelope(reordered, receipt),
        ps_received_input_events=reordered,
    )


def test_e547_rejects_envelope_reorder_even_after_reseal():
    fixture = _fixture(event_count=2)
    envelope = copy.deepcopy(fixture["envelope"])
    envelope["input_events"].reverse()
    envelope = _reseal_envelope(envelope)

    _assert_rejected(
        fixture,
        "envelope_input_batch_mismatch",
        shared_state_envelope=envelope,
    )


def test_e547_rejects_ps_received_batch_mismatch():
    fixture = _fixture()
    ps_events = copy.deepcopy(fixture["events"])
    ps_events[0]["event_id"] = "input-other"

    _assert_rejected(
        fixture,
        "ps_received_batch_mismatch",
        ps_received_input_events=ps_events,
    )


def test_e547_rejects_pending_duplicate_after_tick():
    fixture = _fixture()
    snapshot = copy.deepcopy(fixture["snapshot"])
    snapshot["pending"] = [copy.deepcopy(fixture["events"][0])]

    _assert_rejected(
        fixture,
        "input_sequence_pending_not_empty",
        input_sequence_snapshot=snapshot,
    )


def test_e547_rejects_missing_consumed_event_id_in_cursor():
    fixture = _fixture()
    snapshot = copy.deepcopy(fixture["snapshot"])
    snapshot["seen_event_ids"] = []

    _assert_rejected(
        fixture,
        "input_sequence_seen_ids_missing",
        input_sequence_snapshot=snapshot,
    )


def test_e547_rejects_input_epoch_mismatch_after_reseal():
    fixture = _fixture()
    receipt = copy.deepcopy(fixture["receipt"])
    receipt["pause_reset_epoch"] = 1
    receipt = _reseal_receipt(receipt)

    _assert_rejected(
        fixture,
        "input_sequence_epoch_mismatch",
        completed_tick_receipt=receipt,
        shared_clock_delta_witness=_clock_witness(receipt),
    )


def test_e547_rejects_envelope_lifecycle_epoch_mismatch_after_reseal():
    fixture = _fixture()
    envelope = copy.deepcopy(fixture["envelope"])
    envelope["lifecycle"]["pause_reset_epoch"] = 1
    envelope = _reseal_envelope(envelope)

    _assert_rejected(
        fixture,
        "envelope_pause_reset_epoch_mismatch",
        shared_state_envelope=envelope,
    )


def test_e547_rejects_lane_delta_mismatch_after_reseal():
    fixture = _fixture()
    envelope = copy.deepcopy(fixture["envelope"])
    envelope["clock_provenance"]["ps"]["delta"] = 1.0
    envelope = _reseal_envelope(envelope)

    _assert_rejected(
        fixture,
        "envelope_lane_delta_mismatch",
        shared_state_envelope=envelope,
    )


def test_e547_rejects_clock_witness_for_different_receipt():
    fixture = _fixture()
    other = _fixture(with_event=False)
    _assert_rejected(
        fixture,
        "clock_witness_receipt_mismatch",
        shared_clock_delta_witness=other["clock"],
    )


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e547_rejects_each_admission_overclaim_after_reseal(field: str):
    witness = _build(_fixture())
    witness[field] = True
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e547_queued_input_handoff_authority(candidate)
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e547_rejects_extra_keys_with_valid_reseal():
    witness = _build(_fixture())
    candidate = _reseal_witness({**witness, "unexpected_evidence": True})

    validation = validate_worldbridge_e547_queued_input_handoff_authority(candidate)
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e547_rejects_invalid_embedded_clock_witness_after_witness_reseal():
    witness = _build(_fixture())
    witness["shared_clock_delta_witness"]["decision_digest"] = "0" * 64
    candidate = _reseal_witness(witness)

    validation = validate_worldbridge_e547_queued_input_handoff_authority(candidate)
    assert validation["valid"] is False
    assert any("clock_" in error for error in validation["errors"])
