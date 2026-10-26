from __future__ import annotations

import copy
import random
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
    register_worldbridge_deterministic_random_stream,
)
from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
    _digest,
    validate_worldbridge_shared_state_envelope,
)
from core.VitaLoom.core.editor_context import EditorMode
from core.VitaLoom.viewports.game_viewport import GameViewport


class _SnapshotAuthority:
    def __init__(self) -> None:
        self.revision = 1

    def query(self, _identity: object) -> dict[str, int]:
        return {"revision": self.revision}


class _ViewportDouble(SimpleNamespace):
    def query_sr_runtime_entity_snapshot(self, identity: object) -> dict[str, int]:
        return self._sr_runtime_snapshot_authority.query(identity)


def _viewport() -> _ViewportDouble:
    viewport = _ViewportDouble()
    viewport._worldbridge_input_sequence = WorldBridgeInputSequence()
    viewport._worldbridge_input_events_last_tick = []
    viewport._worldbridge_shared_state_sequence = 0
    viewport._worldbridge_last_shared_state_envelope = None
    viewport._worldbridge_shared_state_receiver = None
    viewport._worldbridge_last_shared_state_receipt = None
    viewport._sr_runtime_epoch = "sr-test-epoch"
    viewport._sr_runtime_scene_path = "scene.pond"
    viewport._sr_runtime_snapshot_authority = _SnapshotAuthority()
    viewport._unified_pond = SimpleNamespace(time=1, simulation_time=0.05)
    viewport.scene_runtime_entities = [
        SimpleNamespace(
            id="sr-organism-1",
            _world_bridge_organism_id="ps-organism-1",
        )
    ]
    viewport._scene_runtime_time = 0.05
    viewport.is_playing = True
    viewport.is_paused = False
    viewport._sr_input = SimpleNamespace(clear=lambda: None)
    viewport.capture_sr_input_state = lambda: {}
    viewport.restore_sr_input_state = lambda _state: None
    return viewport


def test_pause_mode_keeps_playing_session_alive() -> None:
    viewport = _viewport()
    pauses: list[bool] = []
    stops: list[bool] = []
    viewport._pause_simulation = lambda: pauses.append(True)
    viewport._stop_simulation = lambda: stops.append(True)

    GameViewport._on_mode_changed(viewport, EditorMode.PAUSE)

    assert pauses == [True]
    assert stops == []


def test_edit_mode_still_stops_playing_session() -> None:
    viewport = _viewport()
    stops: list[bool] = []
    viewport._stop_simulation = lambda: stops.append(True)

    GameViewport._on_mode_changed(viewport, EditorMode.EDIT)

    assert stops == [True]


def test_viewport_binds_input_clocks_bridge_identity_and_opt_in_rng_snapshot() -> None:
    viewport = _viewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    GameViewport.capture_worldbridge_input_events(viewport)

    context = create_worldbridge_deterministic_randomness_context(
        "viewport-envelope-test", 123
    )
    register_worldbridge_deterministic_random_stream(
        context, "sr.runtime", "python_random", stream=random.Random(123)
    )
    viewport._worldbridge_opt_in_deterministic_randomness_context = context

    envelope = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    assert validate_worldbridge_shared_state_envelope(envelope) == {
        "valid": True,
        "errors": [],
    }
    assert envelope["sequence"] == 0
    assert envelope["input_events"] == [
        {
            "event_id": "input-1",
            "kind": "key_down",
            "payload": {
                "canonical_sequence": 1,
                "pause_reset_epoch": 0,
                "event_digest": viewport._worldbridge_input_events_last_tick[0]["event_digest"],
                "data": {"key": "W"},
            },
        }
    ]
    assert envelope["lifecycle"]["pause_reset_epoch"] == 0
    assert envelope["clock_provenance"]["sr"]["tick"] == 1
    assert envelope["clock_provenance"]["ps"]["tick"] == 1
    assert envelope["bridge_identity_links"] == [
        {
            "sr_entity_id": "sr-organism-1",
            "ps_organism_id": "ps-organism-1",
            "relation": "observation_link",
        }
    ]
    assert envelope["rng_context_snapshot"]["stream_count"] == 1

    accepted = GameViewport.consume_worldbridge_shared_state_envelope(viewport, envelope)
    assert accepted == envelope
    assert accepted is not envelope
    accepted["input_events"][0]["payload"]["data"]["key"] = "mutated"
    assert (
        viewport._worldbridge_last_shared_state_envelope["input_events"][0]["payload"]["data"]["key"]
        == "W"
    )


def test_viewport_receiver_accepts_consecutive_ticks_and_input_reset_epoch() -> None:
    viewport = _viewport()
    first = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    GameViewport.consume_worldbridge_shared_state_envelope(viewport, first)

    viewport._worldbridge_input_sequence.append("key_down", {"key": "A"})
    GameViewport._sr_input_clear(viewport)
    assert GameViewport.capture_worldbridge_input_events(viewport) == []

    viewport._sr_runtime_snapshot_authority.revision = 2
    viewport._unified_pond.time = 2
    viewport._unified_pond.simulation_time = 0.1
    viewport._scene_runtime_time = 0.1
    second = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    accepted = GameViewport.consume_worldbridge_shared_state_envelope(viewport, second)

    assert accepted["sequence"] == 1
    assert accepted["lifecycle"]["pause_reset_epoch"] == 1
    assert accepted["input_events"] == []
    assert viewport._worldbridge_shared_state_receiver.accepted_count == 2
    assert viewport._worldbridge_shared_state_receiver.last_pause_reset_epoch == 1


def test_viewport_receiver_rejection_does_not_advance_receiver_or_receipt() -> None:
    viewport = _viewport()
    first = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    GameViewport.consume_worldbridge_shared_state_envelope(viewport, first)
    receiver = viewport._worldbridge_shared_state_receiver
    before = receiver.state_fingerprint()
    prior_receipt = copy.deepcopy(viewport._worldbridge_last_shared_state_receipt)

    invalid = copy.deepcopy(first)
    invalid["sequence"] = 1
    with pytest.raises(ValueError, match="invalid shared state envelope"):
        GameViewport.consume_worldbridge_shared_state_envelope(viewport, invalid)

    assert receiver.state_fingerprint() == before
    assert viewport._worldbridge_last_shared_state_receipt == prior_receipt


def test_viewport_receiver_rejects_canonical_input_sequence_gap() -> None:
    viewport = _viewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    GameViewport.capture_worldbridge_input_events(viewport)
    first = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    GameViewport.consume_worldbridge_shared_state_envelope(viewport, first)

    viewport._worldbridge_input_sequence.append("key_down", {"key": "A"})
    GameViewport.capture_worldbridge_input_events(viewport)
    viewport._worldbridge_shared_state_sequence = 1
    second = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    second["input_events"][0]["payload"]["canonical_sequence"] = 9
    second["envelope_digest"] = _digest(second)
    receiver = viewport._worldbridge_shared_state_receiver
    before = receiver.state_fingerprint()

    with pytest.raises(ValueError, match="canonical input sequence continuity failure"):
        GameViewport.consume_worldbridge_shared_state_envelope(viewport, second)
    assert receiver.state_fingerprint() == before


def test_transport_reset_is_a_new_lifetime_and_does_not_reuse_receiver_cursor() -> None:
    viewport = _viewport()
    first = GameViewport.capture_worldbridge_shared_state_envelope(viewport, 0.05)
    GameViewport.consume_worldbridge_shared_state_envelope(viewport, first)
    old_receiver = viewport._worldbridge_shared_state_receiver
    assert old_receiver.last_sequence == 0

    GameViewport._reset_worldbridge_shared_state_transport(viewport)

    assert viewport._worldbridge_shared_state_sequence == 0
    assert viewport._worldbridge_shared_state_receiver is None
    assert viewport._worldbridge_last_shared_state_envelope is None
    assert viewport._worldbridge_last_shared_state_receipt is None

    next_lifetime = GameViewport.capture_worldbridge_shared_state_envelope(
        viewport, 0.05, lifecycle_action="start"
    )
    accepted = GameViewport.consume_worldbridge_shared_state_envelope(
        viewport, next_lifetime
    )

    assert accepted["sequence"] == 0
    assert viewport._worldbridge_shared_state_receiver is not old_receiver
    assert viewport._worldbridge_shared_state_receiver.last_sequence == 0
    assert viewport._worldbridge_shared_state_receiver.accepted_count == 1


def test_pause_resume_clears_pending_input_and_advances_epoch_without_old_cursor() -> None:
    viewport = _viewport()
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    GameViewport.capture_worldbridge_input_events(viewport)
    before_pause_epoch = viewport._worldbridge_input_sequence.pause_reset_epoch

    GameViewport._sr_input_clear(viewport)

    assert viewport._worldbridge_input_sequence.pause_reset_epoch == before_pause_epoch + 1
    assert GameViewport.capture_worldbridge_input_events(viewport) == []

    resumed_event = viewport._worldbridge_input_sequence.append(
        "key_down", {"key": "A"}
    )
    resumed_events = GameViewport.capture_worldbridge_input_events(viewport)
    assert [event["sequence"] for event in resumed_events] == [resumed_event["sequence"]]
    assert resumed_events[0]["pause_reset_epoch"] == before_pause_epoch + 1

    envelope = GameViewport.capture_worldbridge_shared_state_envelope(
        viewport, 0.05, lifecycle_action="resume"
    )
    assert envelope["lifecycle"]["pause_reset_epoch"] == before_pause_epoch + 1
    assert envelope["input_events"][0]["payload"]["canonical_sequence"] == resumed_event[
        "sequence"
    ]


def test_explicit_lifecycle_action_clears_ps_handoff_batch() -> None:
    cleared: list[list[dict[str, object]]] = []
    viewport = _viewport()
    viewport._unified_pond.apply_worldbridge_input_events = (
        lambda events: cleared.append(copy.deepcopy(events))
    )
    viewport._worldbridge_input_sequence.append("key_down", {"key": "W"})
    GameViewport.capture_worldbridge_input_events(viewport)
    viewport._unified_pond.apply_worldbridge_input_events(
        viewport._worldbridge_input_events_last_tick
    )
    before = viewport._worldbridge_input_sequence.pause_reset_epoch

    GameViewport._sr_input_clear(viewport, lifecycle_action="pause")

    assert viewport._worldbridge_input_sequence.pause_reset_epoch == before + 1
    assert viewport._worldbridge_input_events_last_tick == []
    assert cleared[-1] == []


def test_transport_reset_invalidates_checkpoint_cursor_for_new_viewport_lifetime() -> None:
    from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
        create_game_viewport_live_checkpoint_adapters,
    )

    viewport = _viewport()
    viewport._using_scene_runtime = True
    viewport._unified_pond_mode = True
    adapter = create_game_viewport_live_checkpoint_adapters(viewport)
    checkpoint_input = adapter.capture_input()
    GameViewport._reset_worldbridge_shared_state_transport(viewport)
    viewport._sr_runtime_epoch = "new-sr-epoch"
    with pytest.raises(RuntimeError, match="shared transport checkpoint epoch mismatch"):
        adapter.restore_input(checkpoint_input)
