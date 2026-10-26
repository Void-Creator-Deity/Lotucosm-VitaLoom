from __future__ import annotations

import copy
from types import SimpleNamespace

import numpy as np
import pytest

import core.Lotucosm.runtime.world_bridge as world_bridge
from builtin.entity_types.organism import Organism
from builtin.systems.physics_engine import PhysicsEngine
from builtin.systems.pond_serializer import PondSerializer
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR
from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
    LiveCheckpointAdapters,
    WorldBridgeLiveCheckpointCoordinator,
    worldbridge_live_checkpoint_state_digest,
)
from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    classify_worldbridge_handoff_failure,
    classify_worldbridge_verified_transaction_failure,
)
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    WorldBridgeHandoffFailure,
)


class RuntimeEntity:
    def __init__(self) -> None:
        self.id = "sr:a"
        self.entity_type = "organism"
        self.position = np.array([10.0, 20.0])
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])
        self.energy = 80.0
        self.health = 60.0
        self.size = 12.0
        self.radius = 6.0
        self.active = True
        self.sr_debug_hud = {"baseline": True}
        setattr(self, BRIDGE_ORGANISM_ATTR, "ps:a")


def _plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return copy.deepcopy(value)


def _fixture():
    pond = Pond(
        name="handoff-transaction",
        initial_organisms=0,
        initial_components=0,
        randomness_rng=np.random.default_rng(811),
    )
    organism = Organism(
        "ps:a",
        (10.0, 20.0),
        energy=80.0,
        health=60.0,
        size=12.0,
    )
    pond.add_organism(organism)
    pond.physics_engine = PhysicsEngine(world_size=pond.size)
    pond._refresh_physics_targets()
    entity = RuntimeEntity()
    cursor = {"value": 0}
    lifecycle = {"playing": True, "epoch": "epoch-1"}

    def capture_sr():
        return _plain(vars(entity))

    def restore_sr(state):
        for name in tuple(vars(entity)):
            if name not in state:
                delattr(entity, name)
        for name, value in state.items():
            current = getattr(entity, name, None)
            if isinstance(current, np.ndarray):
                current[...] = value
            else:
                setattr(entity, name, copy.deepcopy(value))

    def capture_ps():
        payload = PondSerializer(save_format="json").serialize_pond(pond)
        payload.pop("timestamp", None)
        return payload

    def capture_bridge():
        return [{"sr_entity_id": entity.id, "ps_organism_id": getattr(entity, BRIDGE_ORGANISM_ATTR)}]

    def restore_bridge(links):
        if links != capture_bridge():
            raise RuntimeError("unexpected test bridge identity change")

    adapters = LiveCheckpointAdapters(
        capture_sr=capture_sr,
        restore_sr=restore_sr,
        capture_ps=capture_ps,
        restore_ps=lambda state: pond.restore_serialized_state_in_place(copy.deepcopy(dict(state))),
        capture_bridge=capture_bridge,
        restore_bridge=restore_bridge,
        capture_input=lambda: copy.deepcopy(cursor),
        restore_input=lambda state: cursor.update(copy.deepcopy(dict(state))),
        capture_randomness=lambda: copy.deepcopy(pond.randomness_rng.bit_generator.state),
        restore_randomness=lambda state: setattr(
            pond.randomness_rng.bit_generator, "state", copy.deepcopy(state)
        ),
        capture_lifecycle=lambda: copy.deepcopy(lifecycle),
        restore_lifecycle=lambda state: (lifecycle.clear(), lifecycle.update(copy.deepcopy(dict(state)))),
        capture_live_ps=pond.capture_worldbridge_live_transaction_state,
        restore_live_ps=pond.restore_worldbridge_live_transaction_state,
    )
    return pond, organism, entity, cursor, lifecycle, WorldBridgeLiveCheckpointCoordinator(adapters)


@pytest.mark.parametrize("phase", ["sr_to_ps_sync", "pond_update", "ps_to_sr_reflection"])
def test_opt_in_handoff_restores_every_owner_after_partial_phase_failure(
    phase: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    pond, organism, entity, cursor, lifecycle, coordinator = _fixture()
    before_checkpoint = coordinator.capture(checkpoint_id="before", sequence=0)
    before_digest = worldbridge_live_checkpoint_state_digest(before_checkpoint)
    before_live_ps_digest = pond.capture_worldbridge_live_transaction_state().digest
    original_organism = organism
    original_pond_organisms = pond.organisms
    original_physics_targets = pond.physics_engine._targets

    if phase == "sr_to_ps_sync":
        original_sync = world_bridge.sync_sr_entity_to_organism

        def fail_after_sync(source, target):
            original_sync(source, target)
            target.energy = 2.0
            raise RuntimeError("injected post-sync failure")

        monkeypatch.setattr(world_bridge, "sync_sr_entity_to_organism", fail_after_sync)
    elif phase == "pond_update":
        original_update = Pond.update

        def fail_after_update(target, delta_time=1.0):
            original_update(target, delta_time)
            pond._worldbridge_input_events_last_tick.append({"injected": True})
            raise RuntimeError("injected post-update failure")

        monkeypatch.setattr(Pond, "update", fail_after_update)
    else:
        original_reflection = world_bridge.sync_organism_to_sr_display

        def fail_after_reflection(source, target):
            original_reflection(source, target)
            target.energy = -123.0
            raise RuntimeError("injected post-reflection failure")

        monkeypatch.setattr(world_bridge, "sync_organism_to_sr_display", fail_after_reflection)

    with pytest.raises(WorldBridgeHandoffFailure) as raised:
        event = WorldBridgeInputSequence().append("key_down", {"key": "x"})
        world_bridge.unified_pond_step(
            pond,
            [entity],
            input_events=[event],
            transaction_coordinator=coordinator,
        )

    receipt = raised.value.receipt
    rollback = receipt["transaction_rollback"]
    assert receipt["phase"] == phase
    assert receipt["rollback_performed"] is True
    assert receipt["cross_lane_transaction"] is True
    assert receipt["post_failure_state_restored"] is True
    assert receipt["atomic_checkpoint"] is False
    assert rollback["rollback_complete"] is True
    assert rollback.get("rollback_error") is None
    assert rollback["restore_report"]["transaction_verified"] is True
    assert rollback["restore_report"]["target_state_digest"] == before_digest
    assert rollback["captured_live_ps_state_digest"] == before_live_ps_digest

    after_checkpoint = coordinator.capture(checkpoint_id="after", sequence=0)
    assert worldbridge_live_checkpoint_state_digest(after_checkpoint) == before_digest
    assert pond.capture_worldbridge_live_transaction_state().digest == before_live_ps_digest
    assert pond.organisms is original_pond_organisms
    assert pond.organisms["ps:a"] is original_organism
    assert pond.physics_engine._targets is original_physics_targets
    assert pond.physics_engine._targets == [original_organism]
    assert getattr(entity, BRIDGE_ORGANISM_ATTR) == "ps:a"
    assert entity.energy == 80.0
    assert organism.energy == 80.0
    assert pond.time == 0
    assert cursor == {"value": 0}
    assert lifecycle == {"playing": True, "epoch": "epoch-1"}


def test_transactional_handoff_fails_closed_before_mutation_for_opaque_pond_owner() -> None:
    pond, organism, entity, _, _, coordinator = _fixture()

    class OpaqueOwner:
        __slots__ = ("value",)

        def __init__(self) -> None:
            self.value = object()

    pond.unsupported_owner = OpaqueOwner()
    before_position = organism.position.copy()
    before_energy = organism.energy

    with pytest.raises(WorldBridgeHandoffFailure) as raised:
        world_bridge.unified_pond_step(
            pond, [entity], transaction_coordinator=coordinator
        )

    assert raised.value.receipt["phase"] == "preflight"
    assert raised.value.receipt["partial_mutation_possible"] is False
    assert "transaction_rollback" not in raised.value.receipt
    assert np.array_equal(organism.position, before_position)
    assert organism.energy == before_energy
    assert pond.time == 0


def test_verified_transaction_classifier_rejects_tampered_rollback_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pond, _, entity, _, _, coordinator = _fixture()
    original_sync = world_bridge.sync_sr_entity_to_organism

    def fail_after_sync(source, target):
        original_sync(source, target)
        target.energy = 2.0
        raise RuntimeError("injected post-sync failure")

    monkeypatch.setattr(world_bridge, "sync_sr_entity_to_organism", fail_after_sync)
    with pytest.raises(WorldBridgeHandoffFailure) as raised:
        world_bridge.unified_pond_step(
            pond, [entity], transaction_coordinator=coordinator
        )

    receipt = raised.value.receipt
    classify_worldbridge_verified_transaction_failure(receipt)

    tampered = copy.deepcopy(receipt)
    tampered["transaction_rollback"]["restore_report"]["target_state_digest"] = "tampered"
    with pytest.raises(ValueError, match="state digest evidence is inconsistent"):
        classify_worldbridge_verified_transaction_failure(tampered)

    tampered = copy.deepcopy(receipt)
    tampered["transaction_rollback"]["captured_live_ps_state_digest"] = "tampered"
    with pytest.raises(ValueError, match="live PS digest evidence is inconsistent"):
        classify_worldbridge_verified_transaction_failure(tampered)

    tampered = copy.deepcopy(receipt)
    tampered["transaction_rollback"]["restore_report"]["transaction_verified"] = False
    with pytest.raises(ValueError, match="fresh digest verification is missing"):
        classify_worldbridge_verified_transaction_failure(tampered)


def test_unified_failure_classifier_keeps_verified_and_legacy_paths_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pond, _, entity, _, _, coordinator = _fixture()
    original_sync = world_bridge.sync_sr_entity_to_organism

    def fail_after_sync(source, target):
        original_sync(source, target)
        target.energy = 2.0
        raise RuntimeError("injected post-sync failure")

    monkeypatch.setattr(world_bridge, "sync_sr_entity_to_organism", fail_after_sync)
    with pytest.raises(WorldBridgeHandoffFailure) as raised:
        world_bridge.unified_pond_step(
            pond, [entity], transaction_coordinator=coordinator
        )

    verified = classify_worldbridge_handoff_failure(raised.value.receipt)
    assert verified["handoff_suspended"] is False
    assert (
        verified["decision"]["status"]
        == "worldbridge_verified_transaction_failure_containment"
    )
    assert (
        verified["decision"]["admissions"]["future_opt_in_handoff_suspension"]
        is False
    )

    legacy_receipt = {
        "schema_version": 1,
        "status": "worldbridge_cross_lane_transaction_failure_isolation_authority",
        "phase": "pond_update",
        "failure_isolated": True,
        "partial_mutation_possible": True,
        "rollback_performed": False,
        "cross_lane_transaction": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
    }
    legacy = classify_worldbridge_handoff_failure(legacy_receipt)
    assert legacy["handoff_suspended"] is True
    assert (
        legacy["decision"]["host_action"]
        == "suspend_future_opt_in_handoffs_for_current_runtime"
    )

    tampered = copy.deepcopy(raised.value.receipt)
    tampered["transaction_rollback"]["restore_report"]["transaction_verified"] = False
    with pytest.raises(ValueError, match="fresh digest verification is missing"):
        classify_worldbridge_handoff_failure(tampered)
