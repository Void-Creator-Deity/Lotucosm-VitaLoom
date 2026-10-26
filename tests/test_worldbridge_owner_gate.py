from __future__ import annotations

import copy
import threading
import time

from core.Lotucosm.runtime.world_bridge_owner_gate import (
    WorldBridgeOwnerGate,
    validate_worldbridge_owner_gate_snapshot,
)
from core.VitaLoom.viewports.game_viewport import GameViewport


def test_owner_gate_snapshot_is_valid_while_held() -> None:
    gate = WorldBridgeOwnerGate()

    with gate.hold("capture_live_checkpoint"):
        snapshot = gate.snapshot()

    assert validate_worldbridge_owner_gate_snapshot(snapshot) == {
        "valid": True,
        "errors": [],
    }
    assert snapshot["locked"] is True
    assert snapshot["current_operation"] == "capture_live_checkpoint"
    assert snapshot["depth"] == 1
    assert snapshot["owner_thread_id"] == snapshot["current_thread_id"]
    assert gate.snapshot()["locked"] is False


def test_owner_gate_is_reentrant_and_records_depth() -> None:
    gate = WorldBridgeOwnerGate()

    with gate.hold("scene_runtime_tick"):
        with gate.hold("bridge_handoff"):
            snapshot = gate.snapshot()

    assert snapshot["depth"] == 2
    assert snapshot["max_depth"] == 2
    assert snapshot["current_operation"] == "bridge_handoff"
    assert gate.snapshot()["locked"] is False


def test_owner_gate_blocks_competing_thread_until_release() -> None:
    gate = WorldBridgeOwnerGate()
    worker_entered = threading.Event()
    release_holder = threading.Event()
    thread = threading.Thread(target=lambda: _hold_worker(gate, worker_entered))

    with gate.hold("capture_live_checkpoint"):
        thread.start()
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if gate.snapshot()["blocked_attempts"] >= 1:
                break
            time.sleep(0.005)
        assert gate.snapshot()["blocked_attempts"] >= 1
        assert worker_entered.is_set() is False
        release_holder.set()

    thread.join(timeout=2.0)
    assert thread.is_alive() is False
    assert worker_entered.is_set() is True
    assert gate.snapshot()["locked"] is False


def _hold_worker(gate: WorldBridgeOwnerGate, entered: threading.Event) -> None:
    with gate.hold("worker_tick"):
        entered.set()


def test_owner_gate_validator_rejects_tampering() -> None:
    gate = WorldBridgeOwnerGate()
    with gate.hold("capture_live_checkpoint"):
        snapshot = gate.snapshot()
    tampered = copy.deepcopy(snapshot)
    tampered["locked"] = False
    tampered["depth"] = 0

    validation = validate_worldbridge_owner_gate_snapshot(tampered)
    assert validation["valid"] is False
    assert "unlocked_state_inconsistent" in validation["errors"]


def test_viewport_checkpoint_capture_runs_under_shared_gate() -> None:
    viewport = GameViewport.__new__(GameViewport)
    observed = {}

    def capture_locked(checkpoint_id=None):
        observed.update(viewport.worldbridge_owner_gate_snapshot())
        return {"checkpoint_id": checkpoint_id}

    viewport._capture_worldbridge_live_checkpoint_locked = capture_locked

    result = GameViewport.capture_worldbridge_live_checkpoint(
        viewport, "gate-test"
    )

    assert result == {"checkpoint_id": "gate-test"}
    assert observed["locked"] is True
    assert observed["depth"] == 1
    assert observed["current_operation"] == "capture_live_checkpoint"
    assert viewport.worldbridge_owner_gate_snapshot()["locked"] is False
