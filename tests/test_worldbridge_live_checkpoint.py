# -*- coding: utf-8
from __future__ import annotations

import copy
from collections import OrderedDict

import pytest

from core.Lotucosm.runtime import world_bridge_live_checkpoint as checkpoint_module
from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
    LiveCheckpointAdapters,
    WorldBridgeLiveCheckpointCoordinator,
    WorldBridgeLiveCheckpointError,
    WorldBridgeOwnerBindingDrift,
    validate_worldbridge_live_checkpoint,
)


class FakeLiveState:
    def __init__(self) -> None:
        self.state = {
            "sr": {"time": 1.0, "entities": ["sr:a"]},
            "ps": {"time": 2, "organisms": ["ps:a"]},
            "bridge": [{"sr_entity_id": "sr:a", "ps_organism_id": "ps:a"}],
            "input": {"cursor": 3},
            "randomness": {"context": "local", "cursor": 4},
            "lifecycle": {"playing": True, "paused": False, "epoch": 1},
        }
        self.fail_phase: str | None = None
        self.always_fail_phase: str | None = None
        self.phase_calls: dict[str, int] = {}

    def adapters(self) -> LiveCheckpointAdapters:
        def capture(name: str):
            return lambda: copy.deepcopy(self.state[name])

        def restore(name: str):
            def apply(value):
                self.phase_calls[name] = self.phase_calls.get(name, 0) + 1
                if self.always_fail_phase == name and self.phase_calls[name] > 1:
                    raise RuntimeError(f"persistently failed {name}")
                if self.fail_phase == name:
                    self.fail_phase = None
                    raise RuntimeError(f"failed {name}")
                self.state[name] = copy.deepcopy(value)
            return apply

        return LiveCheckpointAdapters(
            capture_sr=capture("sr"), restore_sr=restore("sr"),
            capture_ps=capture("ps"), restore_ps=restore("ps"),
            capture_bridge=capture("bridge"), restore_bridge=restore("bridge"),
            capture_input=capture("input"), restore_input=restore("input"),
            capture_randomness=capture("randomness"), restore_randomness=restore("randomness"),
            capture_lifecycle=capture("lifecycle"), restore_lifecycle=restore("lifecycle"),
        )


def test_capture_is_digest_sealed_and_copy_isolated() -> None:
    live = FakeLiveState()
    coordinator = WorldBridgeLiveCheckpointCoordinator(live.adapters())
    checkpoint = coordinator.capture(checkpoint_id="cp-1", sequence=0)
    assert validate_worldbridge_live_checkpoint(checkpoint) == {"valid": True, "errors": []}
    checkpoint["sr_state"]["entities"].append("mutated")
    assert live.state["sr"]["entities"] == ["sr:a"]


def test_restore_uses_fixed_order_and_updates_all_live_owners() -> None:
    live = FakeLiveState()
    coordinator = WorldBridgeLiveCheckpointCoordinator(live.adapters())
    checkpoint = coordinator.capture(checkpoint_id="cp-1", sequence=0)
    live.state["sr"] = {"time": 99.0, "entities": []}
    live.state["ps"] = {"time": 99, "organisms": []}
    result = coordinator.restore(checkpoint)
    assert result["restored"] is True
    assert result["restore_order"] == ["lifecycle", "input", "randomness", "ps", "sr", "bridge"]
    assert live.state["sr"] == checkpoint["sr_state"]
    assert live.state["ps"] == checkpoint["ps_state"]


def test_restore_failure_compensates_already_applied_phases() -> None:
    live = FakeLiveState()
    coordinator = WorldBridgeLiveCheckpointCoordinator(live.adapters())
    checkpoint = coordinator.capture(checkpoint_id="cp-1", sequence=0)
    before = copy.deepcopy(live.state)
    checkpoint["lifecycle"] = {"playing": False, "paused": True, "epoch": 2}
    checkpoint["digest"] = ""
    from core.Lotucosm.runtime.world_bridge_live_checkpoint import _digest
    checkpoint["digest"] = _digest(checkpoint)
    live.fail_phase = "ps"
    with pytest.raises(WorldBridgeLiveCheckpointError) as error:
        coordinator.restore(checkpoint)
    assert error.value.report["phase"] == "ps"
    assert error.value.report["compensation_complete"] is True
    assert live.state == before


def test_tampered_checkpoint_rejected_before_capture_or_mutation() -> None:
    live = FakeLiveState()
    coordinator = WorldBridgeLiveCheckpointCoordinator(live.adapters())
    checkpoint = coordinator.capture(checkpoint_id="cp-1", sequence=0)
    checkpoint["sequence"] = 4
    before = copy.deepcopy(live.state)
    with pytest.raises(ValueError):
        coordinator.restore(checkpoint)
    assert live.state == before


def test_restore_reports_incomplete_compensation_without_claiming_success() -> None:
    live = FakeLiveState()
    coordinator = WorldBridgeLiveCheckpointCoordinator(live.adapters())
    checkpoint = coordinator.capture(checkpoint_id="cp-1", sequence=0)
    live.fail_phase = "ps"
    live.always_fail_phase = "lifecycle"
    with pytest.raises(WorldBridgeLiveCheckpointError) as error:
        coordinator.restore(checkpoint)
    report = error.value.report
    assert report["phase"] == "ps"
    assert report["compensation_complete"] is False
    assert "lifecycle" in report["compensation_errors"]


def test_restore_rejects_owner_drift_before_any_adapter_mutation() -> None:
    live = FakeLiveState()
    owner = object()

    def current_owner_binding():
        return {"owner": id(live_owner[0])}

    def validate_owner_binding(expected):
        errors = [] if expected == current_owner_binding() else ["owner_root_changed:ps_pond"]
        return {"valid": not errors, "errors": errors}

    def capture_lifecycle():
        return {
            **copy.deepcopy(live.state["lifecycle"]),
            "process_owner_binding": current_owner_binding(),
        }

    live_owner = [owner]
    adapters = live.adapters()
    from dataclasses import replace

    coordinator = WorldBridgeLiveCheckpointCoordinator(
        replace(
            adapters,
            capture_lifecycle=capture_lifecycle,
            capture_owner_binding=current_owner_binding,
            validate_owner_binding=validate_owner_binding,
        )
    )
    checkpoint = coordinator.capture(checkpoint_id="owner-bound", sequence=0)
    before = copy.deepcopy(live.state)
    live_owner[0] = object()

    with pytest.raises(WorldBridgeOwnerBindingDrift, match="owner_root_changed:ps_pond"):
        coordinator.restore(checkpoint)

    assert live.state == before
    assert live.phase_calls == {}


def test_process_owner_binding_registry_is_bounded_and_evicted_checkpoints_fail_closed(
    monkeypatch,
) -> None:
    owner_bindings_before = copy.deepcopy(checkpoint_module._PROCESS_OWNER_BINDINGS)
    checkpoints_before = copy.deepcopy(checkpoint_module._PROCESS_OWNER_CHECKPOINTS)
    owner_limit_before = checkpoint_module._MAX_PROCESS_OWNER_BINDINGS
    checkpoint_limit_before = checkpoint_module._MAX_PROCESS_OWNER_CHECKPOINTS
    monkeypatch.setattr(checkpoint_module, "_MAX_PROCESS_OWNER_BINDINGS", 2)
    monkeypatch.setattr(checkpoint_module, "_MAX_PROCESS_OWNER_CHECKPOINTS", 2)

    checkpoints = []
    binding = {"test_owner": "bounded-registry"}
    try:
        for index in range(3):
            checkpoint = {
                "checkpoint_id": f"registry-{index}",
                "sequence": index,
                "lifecycle": {},
                "digest": "",
            }
            checkpoint_module._register_process_owner_binding(checkpoint, binding)
            checkpoints.append(checkpoint)

        assert len(checkpoint_module._PROCESS_OWNER_BINDINGS) <= 2
        assert len(checkpoint_module._PROCESS_OWNER_CHECKPOINTS) <= 2
        assert checkpoint_module._resolve_process_owner_binding(checkpoints[0]) is None
        assert checkpoint_module._resolve_process_owner_binding(checkpoints[-1]) == binding
    finally:
        with checkpoint_module._PROCESS_OWNER_BINDINGS_LOCK:
            checkpoint_module._PROCESS_OWNER_BINDINGS = OrderedDict(owner_bindings_before)
            checkpoint_module._PROCESS_OWNER_CHECKPOINTS = OrderedDict(checkpoints_before)
        monkeypatch.setattr(
            checkpoint_module,
            "_MAX_PROCESS_OWNER_BINDINGS",
            owner_limit_before,
        )
        monkeypatch.setattr(
            checkpoint_module,
            "_MAX_PROCESS_OWNER_CHECKPOINTS",
            checkpoint_limit_before,
        )
