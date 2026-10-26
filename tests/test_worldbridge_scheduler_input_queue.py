from __future__ import annotations

import pytest

from core.Lotucosm.runtime.world_bridge_input_sequence import (
    WorldBridgeInputBackpressureError,
    WorldBridgeInputSequence,
    validate_worldbridge_scheduler_input_queue_snapshot,
)


def _queue(max_pending: int = 2) -> WorldBridgeInputSequence:
    return WorldBridgeInputSequence(
        scheduler_owner_id="test.input_scheduler",
        max_pending=max_pending,
        overflow_policy="reject_newest",
    )


def test_scheduler_queue_snapshot_declares_owner_schema_and_policy() -> None:
    queue = _queue()
    snapshot = queue.scheduler_snapshot()

    assert validate_worldbridge_scheduler_input_queue_snapshot(snapshot) == {
        "valid": True,
        "errors": [],
    }
    assert snapshot["scheduler_owner_id"] == "test.input_scheduler"
    assert snapshot["canonical_event_schema"] == "worldbridge_input_sequence"
    assert snapshot["dispatch_phase"] == "sr_snapshot"
    assert snapshot["routing_policy"] == "sr_snapshot_then_ps_handoff"
    assert snapshot["max_pending"] == 2
    assert snapshot["overflow_policy"] == "reject_newest"


def test_scheduler_queue_backpressure_rejects_newest_atomically() -> None:
    queue = _queue()
    first = queue.append("key_down", {"key": "W"})
    second = queue.append("key_up", {"key": "W"})
    before = queue.snapshot()

    with pytest.raises(WorldBridgeInputBackpressureError) as raised:
        queue.append("key_down", {"key": "A"})

    after = queue.snapshot()
    receipt = raised.value.receipt
    assert before == after
    assert receipt["overflow_policy"] == "reject_newest"
    assert receipt["pending_count"] == 2
    assert receipt["max_pending"] == 2
    assert receipt["next_sequence_unchanged"] == 3
    assert [event["event_id"] for event in after["pending"]] == [
        first["event_id"],
        second["event_id"],
    ]
    snapshot = queue.scheduler_snapshot()
    assert snapshot["rejected_count"] == 1
    assert len(snapshot["backpressure_receipts"]) == 1


def test_scheduler_queue_dispatch_receipt_records_sr_phase() -> None:
    queue = _queue()
    queue.append("key_down", {"key": "W"})
    queue.append("key_up", {"key": "W"})

    events = queue.consume()
    snapshot = queue.scheduler_snapshot()

    assert [event["sequence"] for event in events] == [1, 2]
    assert snapshot["pending_count"] == 0
    assert snapshot["dispatch_count"] == 1
    receipt = snapshot["dispatch_receipts"][-1]
    assert receipt["dispatch_phase"] == "sr_snapshot"
    assert receipt["routing_policy"] == "sr_snapshot_then_ps_handoff"
    assert receipt["event_ids"] == ["input-1", "input-2"]
    assert receipt["first_sequence"] == 1
    assert receipt["last_sequence"] == 2


def test_scheduler_queue_lifecycle_drop_receipt_is_explicit() -> None:
    queue = _queue()
    queue.append("key_down", {"key": "W"})
    queue.append("key_up", {"key": "W"})

    queue.lifecycle("pause")
    snapshot = queue.scheduler_snapshot()

    assert snapshot["pending_count"] == 0
    assert snapshot["pause_reset_epoch"] == 1
    assert snapshot["dropped_count"] == 2
    assert snapshot["last_drop_reason"] == "lifecycle:pause"
    receipt = snapshot["drop_receipts"][-1]
    assert receipt["dropped_event_ids"] == ["input-1", "input-2"]
    assert receipt["dropped_count"] == 2


def test_scheduler_queue_policy_change_requires_empty_queue() -> None:
    queue = _queue()
    queue.configure_policy(max_pending=8)
    assert queue.scheduler_snapshot()["max_pending"] == 8

    queue.append("key_down", {"key": "W"})
    with pytest.raises(ValueError, match="pending events"):
        queue.configure_policy(max_pending=1)


def test_scheduler_queue_validator_rejects_policy_and_receipt_tampering() -> None:
    queue = _queue()
    snapshot = queue.scheduler_snapshot()
    snapshot["overflow_policy"] = "silent_drop"
    snapshot["dispatch_receipts"] = [{"status": "wrong"}]

    validation = validate_worldbridge_scheduler_input_queue_snapshot(snapshot)
    assert validation["valid"] is False
    assert "overflow_policy_invalid" in validation["errors"]
    assert "dispatch_receipts_entry_invalid" in validation["errors"]
