from __future__ import annotations

import copy

import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    MAX_RETAINED_RECEIPTS,
    WorldBridgeSharedStateReceiver,
    build_worldbridge_shared_state_envelope,
    build_worldbridge_shared_state_transport_contract,
    copy_worldbridge_shared_state_envelope,
    quarantine_worldbridge_shared_state_transport,
    validate_worldbridge_shared_state_envelope,
    _digest,
)


def _envelope(*, sequence=9, capture_epoch=4, rng_context_snapshot=None):
    return build_worldbridge_shared_state_envelope(
        envelope_id="test-envelope",
        capture_epoch=4,
        sequence=sequence,
        input_events=[{"event_id": "evt-1", "kind": "key_down", "payload": {"key": "A"}}],
        pause_reset_epoch=2,
        clock_provenance={
            "sr": {"domain": "sr", "tick": 10, "delta": 0.05, "time": 0.5, "source": "viewport"},
            "ps": {"domain": "ps", "tick": 8, "delta": 1.0, "time": 8.0, "source": "pond"},
        },
        bridge_identity_links=[{"sr_entity_id": "sr-1", "ps_organism_id": "ps-1"}],
        rng_context_snapshot=rng_context_snapshot,
    )


def test_contract_is_valid_and_quarantine_only():
    contract = build_worldbridge_shared_state_transport_contract()
    assert contract["contract_valid"] is True
    assert contract["quarantine_only"] is True
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False


def test_envelope_round_trip_is_deep_copy_isolated():
    envelope = _envelope()
    assert validate_worldbridge_shared_state_envelope(envelope)["valid"]
    restored = copy_worldbridge_shared_state_envelope(envelope)
    assert restored == envelope
    assert restored is not envelope
    restored["input_events"][0]["payload"]["key"] = "B"
    assert envelope["input_events"][0]["payload"]["key"] == "A"


def test_digest_tampering_is_rejected():
    envelope = _envelope()
    tampered = copy.deepcopy(envelope)
    tampered["sequence"] += 1
    result = validate_worldbridge_shared_state_envelope(tampered)
    assert result["valid"] is False
    assert "envelope_digest_mismatch" in result["errors"]
    with pytest.raises(ValueError, match="invalid shared state envelope"):
        copy_worldbridge_shared_state_envelope(tampered)


def test_input_and_clock_shapes_are_strict():
    with pytest.raises(ValueError):
        build_worldbridge_shared_state_envelope(
            envelope_id="bad", capture_epoch=0, sequence=0,
            input_events=[{"event_id": "x", "kind": "key", "payload": {}, "extra": 1}],
            pause_reset_epoch=0,
            clock_provenance={"sr": {}, "ps": {}}, bridge_identity_links=[],
        )
    with pytest.raises(ValueError):
        build_worldbridge_shared_state_envelope(
            envelope_id="bad", capture_epoch=0, sequence=0, input_events=[], pause_reset_epoch=0,
            clock_provenance={"sr": {"domain": "ps", "tick": 0, "delta": 0, "time": 0, "source": "x"}, "ps": {"domain": "ps", "tick": 0, "delta": 0, "time": 0, "source": "x"}}, bridge_identity_links=[],
        )


def test_quarantine_fallback_is_explicit_and_non_admitting():
    envelope = quarantine_worldbridge_shared_state_transport(
        envelope_id="quarantine", sequence=3, code="rng_missing", stage="capture", message="RNG context unavailable"
    )
    assert validate_worldbridge_shared_state_envelope(envelope)["valid"]
    assert envelope["quarantine"] is True
    assert envelope["failure"]["code"] == "rng_missing"
    assert envelope["input_events"] == []
    assert envelope["replay_admitted"] is False
    assert envelope["lossless"] is False


def test_receiver_preserves_continuity_across_ticks_and_pause_epoch():
    receiver = WorldBridgeSharedStateReceiver()
    first = build_worldbridge_shared_state_envelope(
        envelope_id="tick-1", capture_epoch=1, sequence=0,
        input_events=[], pause_reset_epoch=0,
        clock_provenance={
            "sr": {"domain": "sr", "tick": 1, "delta": 0.05, "time": 0.05, "source": "sr"},
            "ps": {"domain": "ps", "tick": 1, "delta": 0.05, "time": 0.05, "source": "ps"},
        }, bridge_identity_links=[], playing=True, paused=False,
    )
    second = copy.deepcopy(first)
    second["envelope_id"] = "tick-2"
    second["capture_epoch"] = 2
    second["sequence"] = 1
    second["clock_provenance"]["sr"]["tick"] = 2
    second["clock_provenance"]["ps"]["tick"] = 2
    second["clock_provenance"]["sr"]["time"] = 0.1
    second["clock_provenance"]["ps"]["time"] = 0.1
    from core.Lotucosm.runtime.world_bridge_shared_state_transport import _digest
    second["envelope_digest"] = _digest(second)

    receiver.accept(first)
    receiver.accept(second)
    assert receiver.accepted_count == 2
    assert receiver.last_sequence == 1
    assert receiver.last_pause_reset_epoch == 0

    resumed = copy.deepcopy(second)
    resumed["envelope_id"] = "tick-resumed"
    resumed["capture_epoch"] = 3
    resumed["sequence"] = 2
    resumed["lifecycle"]["pause_reset_epoch"] = 1
    resumed["clock_provenance"]["sr"]["tick"] = 3
    resumed["clock_provenance"]["ps"]["tick"] = 3
    resumed["clock_provenance"]["sr"]["time"] = 0.15
    resumed["clock_provenance"]["ps"]["time"] = 0.15
    resumed["envelope_digest"] = _digest(resumed)
    receiver.accept(resumed)
    assert receiver.last_pause_reset_epoch == 1


def test_receiver_rejects_epoch_regression_without_mutating_state():
    receiver = WorldBridgeSharedStateReceiver()
    accepted = _envelope()
    accepted["sequence"] = 0
    accepted["capture_epoch"] = 1
    accepted["lifecycle"]["pause_reset_epoch"] = 1
    from core.Lotucosm.runtime.world_bridge_shared_state_transport import _digest
    accepted["envelope_digest"] = _digest(accepted)
    receiver.accept(accepted)
    regressed = copy.deepcopy(accepted)
    regressed["envelope_id"] = "epoch-one"
    regressed["sequence"] = 1
    regressed["capture_epoch"] = 2
    regressed["lifecycle"]["pause_reset_epoch"] = 2
    regressed["envelope_digest"] = _digest(regressed)
    receiver.accept(regressed)
    before_regression = receiver.state_fingerprint()

    invalid = copy.deepcopy(regressed)
    invalid["envelope_id"] = "epoch-regression"
    invalid["sequence"] = 2
    invalid["capture_epoch"] = 3
    invalid["lifecycle"]["pause_reset_epoch"] = 1
    invalid["envelope_digest"] = _digest(invalid)
    with pytest.raises(ValueError, match="pause_reset_epoch regression"):
        receiver.accept(invalid)
    assert receiver.state_fingerprint() == before_regression


def test_receiver_rejects_rng_snapshot_gap_and_context_switch_without_mutation():
    context_a = create_worldbridge_deterministic_randomness_context("rng-a", 1)
    register_worldbridge_deterministic_random_stream(context_a, "sr", "python_random")
    first = _envelope(sequence=0, capture_epoch=1, rng_context_snapshot=context_a.snapshot())
    receiver = WorldBridgeSharedStateReceiver()
    receiver.accept(first)
    before = receiver.state_fingerprint()

    missing = _envelope(sequence=1, capture_epoch=2)
    with pytest.raises(ValueError, match="RNG snapshot continuity gap"):
        receiver.accept(missing)
    assert receiver.state_fingerprint() == before

    context_b = create_worldbridge_deterministic_randomness_context("rng-b", 1)
    register_worldbridge_deterministic_random_stream(context_b, "sr", "python_random")
    switched = _envelope(sequence=1, capture_epoch=2, rng_context_snapshot=context_b.snapshot())
    with pytest.raises(ValueError, match="RNG context mismatch"):
        receiver.accept(switched)
    assert receiver.state_fingerprint() == before


def test_receiver_retains_only_a_bounded_window_while_counting_all_accepts():
    receiver = WorldBridgeSharedStateReceiver()
    template = _envelope()
    for sequence in range(MAX_RETAINED_RECEIPTS + 17):
        candidate = copy.deepcopy(template)
        candidate["envelope_id"] = f"window-{sequence}"
        candidate["sequence"] = sequence
        candidate["capture_epoch"] = sequence
        candidate["lifecycle"]["pause_reset_epoch"] = 0
        candidate["envelope_digest"] = _digest(candidate)
        receiver.accept(candidate)

    retained = receiver.accepted_envelopes
    assert receiver.accepted_count == MAX_RETAINED_RECEIPTS + 17
    assert len(retained) == MAX_RETAINED_RECEIPTS
    assert retained[0]["sequence"] == 17
    assert retained[-1]["sequence"] == MAX_RETAINED_RECEIPTS + 16
