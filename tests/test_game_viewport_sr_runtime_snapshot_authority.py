# -*- coding: utf-8 -*-
"""GameViewport Adapter for the Qt-free SR runtime snapshot authority."""
from __future__ import annotations

import os
import copy

import numpy as np
import pytest
from PyQt6.QtWidgets import QApplication

from core.VitaLoom.simulation import simulation_coordinator
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from builtin.entity_types.organism import Organism
from core.Lotucosm.runtime.world_bridge import sync_organism_to_sr_display
from core.Lotucosm.sr_memory_gene_bridge import load_sr_memory_genes_from_props


@pytest.fixture(scope="session", autouse=True)
def _qt_app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def _install_runtime(viewport: GameViewport, *, x: float = 10.0) -> object:
    entity = viewport._SceneRuntimeEntity("same_id", "organism", (x, 20.0), 18.0)
    entity.energy = 75.0
    entity.generation = 3
    entity.scripts = [object()]
    viewport.scene_runtime_entities = [entity]
    viewport._sr_serialized_scene_entity_ids = {"same_id"}
    viewport._sr_runtime_scene_path = "scenes/demo.pond"
    viewport._using_scene_runtime = True
    return entity


def _identity(epoch: str, entity_id: str = "same_id") -> dict[str, str]:
    return {
        "track": "sr_play",
        "runtime_epoch": epoch,
        "scene_path": "scenes/demo.pond",
        "entity_id": entity_id,
    }


def test_runtime_entity_missing_id_uses_caller_owned_identity_source():
    source = DeterministicIdentitySource("e423")
    entity = GameViewport._SceneRuntimeEntity(
        None,
        "organism",
        (1.0, 2.0),
        identity_source=source,
        rng=np.random.default_rng(1),
    )
    assert entity.id == DeterministicIdentitySource("e423").next("entity")
    assert source.snapshot()["counters"] == {"entity": 1}


def test_runtime_entity_missing_id_fails_without_identity_source():
    with pytest.raises(RuntimeError, match="requires identity source"):
        GameViewport._SceneRuntimeEntity(None, "organism", (1.0, 2.0))


def test_worldbridge_projects_real_sr_runtime_entity_through_owner_apis() -> None:
    entity = GameViewport._SceneRuntimeEntity("bridge_owner", "organism", (1.0, 2.0), 8.0)
    organism = Organism("ps_owner", (30.0, 40.0), energy=55.0)
    organism.restore_motion_state(
        position=(30.0, 40.0),
        velocity=(3.0, 4.0),
        acceleration=(0.5, -0.25),
    )
    organism.set_radius(12.0)

    calls: list[str] = []
    for method_name in ("set_position", "set_velocity", "set_acceleration", "set_radius", "set_energy"):
        original = getattr(entity, method_name)

        def tracked(value, *, _original=original, _name=method_name):
            calls.append(_name)
            _original(value)

        setattr(entity, method_name, tracked)

    sync_organism_to_sr_display(organism, entity)

    assert calls == ["set_position", "set_energy", "set_radius", "set_radius", "set_velocity", "set_acceleration"]
    assert entity.position == [30.0, 40.0]
    assert entity.velocity == [3.0, 4.0]
    assert entity.acceleration == [0.5, -0.25]
    assert entity.energy == 55.0
    assert entity.radius == 12.0


def test_viewport_composition_can_use_caller_owned_deterministic_identity() -> None:
    first = GameViewport(identity_source=DeterministicIdentitySource("viewport-e417"))
    second = GameViewport(identity_source=DeterministicIdentitySource("viewport-e417"))
    for viewport in (first, second):
        viewport._sr_runtime_scene_path = "scenes/demo.pond"
        viewport._using_scene_runtime = True
    assert first._begin_sr_snapshot_lifetime() == second._begin_sr_snapshot_lifetime()


def test_adapter_publishes_whitelisted_copy_isolated_snapshots() -> None:
    viewport = GameViewport()
    entity = _install_runtime(viewport)

    epoch = viewport._begin_sr_snapshot_lifetime()
    assert epoch
    first = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))

    assert first["status"] == "ok"
    assert first["snapshot"]["serialized_scene_counterpart"] is True
    assert first["snapshot"]["position"] == [10.0, 20.0]
    assert first["snapshot"]["velocity"] == [float(entity.velocity[0]), float(entity.velocity[1])]
    assert first["snapshot"]["energy"] == 75.0
    assert first["snapshot"]["generation"] == 3
    assert first["snapshot"]["component_facts"] == []
    assert "scripts" not in first["snapshot"]
    assert "color" not in first["snapshot"]
    assert "sr_debug_hud" not in first["snapshot"]

    entity.position[0] = 44.0
    viewport._publish_sr_runtime_snapshots()
    second = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))
    assert second["revision"] == 2
    assert second["snapshot"]["position"] == [44.0, 20.0]


def test_runtime_snapshot_captures_and_restores_memory_genes() -> None:
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    load_sr_memory_genes_from_props(
        entity,
        {"initial_memory_genes": [{"situation": "live", "action_pattern": {"ax": 2}}]},
    )

    epoch = viewport._begin_sr_snapshot_lifetime()
    captured = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))["snapshot"]
    assert captured["memory_genes"][0]["situation"] == "live"

    entity.sr_memory_genes[0].action_pattern["ax"] = 99.0
    viewport.restore_sr_runtime_snapshot_slice(
        [captured], scene_time=viewport._scene_runtime_time
    )

    assert entity.sr_memory_genes[0].action_pattern["ax"] == 2.0
    captured["memory_genes"][0]["action_pattern"]["ax"] = -7.0
    assert entity.sr_memory_genes[0].action_pattern["ax"] == 2.0


def test_render_identity_injection_failure_rolls_back_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Injected mid-restore failure must leave render identity exactly as it was."""
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    epoch = viewport._begin_sr_snapshot_lifetime()
    entity.sr_visual.flip_x = True
    entity.sr_visual.alpha = 0.4
    envelope = viewport.capture_sr_runtime_restore_envelope()

    entity.sr_visual.flip_x = False
    entity.sr_visual.alpha = 1.0

    import core.VitaLoom.simulation.sr_runtime_snapshot_restore as restore_module

    real_apply = restore_module._apply_render_identity
    calls = []

    def apply_then_fail(target, value, entity_id):
        real_apply(target, value, entity_id)
        calls.append(entity_id)
        if len(calls) == 1:
            raise RuntimeError('E537 injected post-render-identity failure')

    monkeypatch.setattr(restore_module, "_apply_render_identity", apply_then_fail)
    with pytest.raises(Exception):
        viewport.restore_sr_runtime_restore_envelope(envelope)

    assert calls == [entity.id, entity.id]
    # The failing write was compensated: the live owner is back at baseline.
    assert entity.sr_visual.flip_x is False
    assert entity.sr_visual.alpha == 1.0

    # Malformed render identity is rejected before any mutation.
    tampered = copy.deepcopy(envelope)
    tampered["snapshots"][0]["render_identity"] = {
        "flip_x": True, "alpha": 3.5,
    }
    tampered.pop("digest")
    from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
        snapshot_restore_digest,
    )

    tampered["digest"] = snapshot_restore_digest(tampered)
    with pytest.raises(Exception):
        viewport.restore_sr_runtime_restore_envelope(tampered)
    assert entity.sr_visual.flip_x is False
    assert entity.sr_visual.alpha == 1.0
    _ = epoch


def test_adapter_marks_runtime_created_entity_without_pond_counterpart() -> None:
    viewport = GameViewport()
    _install_runtime(viewport)
    runtime_created = viewport._SceneRuntimeEntity("evo_organism_00001", "organism", (5.0, 6.0), 22.0)
    viewport.scene_runtime_entities.append(runtime_created)

    epoch = viewport._begin_sr_snapshot_lifetime()
    result = viewport.query_sr_runtime_entity_snapshot(_identity(epoch, "evo_organism_00001"))

    assert result["status"] == "ok"
    assert result["snapshot"]["serialized_scene_counterpart"] is False


def test_discard_ends_lifetime_and_reload_makes_old_epoch_stale() -> None:
    viewport = GameViewport()
    _install_runtime(viewport, x=10.0)
    old_epoch = viewport._begin_sr_snapshot_lifetime()

    viewport._discard_scene_runtime_state()
    assert viewport.query_sr_runtime_entity_snapshot(_identity(old_epoch))["status"] == "not_running"

    _install_runtime(viewport, x=90.0)
    new_epoch = viewport._begin_sr_snapshot_lifetime()
    assert new_epoch != old_epoch
    assert viewport.query_sr_runtime_entity_snapshot(_identity(old_epoch, "missing"))["status"] == "stale"
    current = viewport.query_sr_runtime_entity_snapshot(_identity(new_epoch))
    assert current["status"] == "ok"
    assert current["snapshot"]["position"] == [90.0, 20.0]


def test_empty_runtime_tick_replaces_previous_entity_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    viewport = GameViewport()
    _install_runtime(viewport)
    epoch = viewport._begin_sr_snapshot_lifetime()
    assert viewport.query_sr_runtime_entity_snapshot(_identity(epoch))["status"] == "ok"

    monkeypatch.setattr(viewport, "_maybe_try_sr_extinction_pause", lambda: None)
    monkeypatch.setattr(viewport, "_refresh_sr_hud", lambda _entities: None)
    viewport.scene_runtime_entities = []
    viewport._handle_empty_sr_runtime_tick()

    result = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))
    assert result["status"] == "missing"
    assert result["revision"] == 2


def test_start_and_stop_own_authority_lifetime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    viewport = GameViewport()
    monkeypatch.setattr(simulation_coordinator, "_coordinator", None)
    monkeypatch.setattr(viewport, "_prepare_simulation_backend", lambda: bool(_install_runtime(viewport)))
    monkeypatch.setattr(viewport, "_refresh_unified_pond_mode", lambda *_args, **_kwargs: None)

    viewport._start_simulation()
    epoch = viewport._sr_runtime_epoch
    assert epoch
    assert viewport.query_sr_runtime_entity_snapshot(_identity(epoch))["status"] == "ok"

    viewport._stop_simulation(write_session=False)
    assert viewport._sr_runtime_epoch is None
    assert viewport.query_sr_runtime_entity_snapshot(_identity(epoch))["status"] == "not_running"


def test_resume_reload_rejects_same_id_from_previous_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    viewport = GameViewport()
    monkeypatch.setattr(simulation_coordinator, "_coordinator", None)
    monkeypatch.setattr(viewport, "_refresh_unified_pond_mode", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(viewport, "_prepare_simulation_backend", lambda: bool(_install_runtime(viewport, x=10.0)))
    viewport._start_simulation()
    old_epoch = viewport._sr_runtime_epoch
    assert old_epoch

    viewport.is_paused = True
    monkeypatch.setattr(viewport, "_scene_runtime_needs_reload", lambda: True)
    monkeypatch.setattr(viewport, "_prepare_simulation_backend", lambda: bool(_install_runtime(viewport, x=80.0)))
    viewport._resume_simulation()

    new_epoch = viewport._sr_runtime_epoch
    assert new_epoch and new_epoch != old_epoch
    assert viewport.query_sr_runtime_entity_snapshot(_identity(old_epoch))["status"] == "stale"
    current = viewport.query_sr_runtime_entity_snapshot(_identity(new_epoch))
    assert current["snapshot"]["position"] == [80.0, 20.0]
    viewport._stop_simulation(write_session=False)


def test_sr_snapshot_adapter_projects_only_attached_runtime_entities() -> None:
    viewport = GameViewport()
    organism = _install_runtime(viewport)
    sensor = viewport._SceneRuntimeEntity("sensor_1", "sensor", (15.0, 18.0), 8.0)
    actuator = viewport._SceneRuntimeEntity("actuator_unattached", "actuator", (4.0, 5.0), 8.0)
    sensor.scripts = [object()]
    viewport.scene_runtime_entities.extend([sensor, actuator])
    viewport._sr_membrane_attach = {"sensor_1": (str(organism.id), 5.0, -2.0)}
    viewport._sr_connection_edges = [
        {"start": "same_id", "end": "sensor_1", "type": "hard"},
    ]
    viewport._sr_signal_edges = [
        {"start": "sensor_1", "end": "same_id", "channel": "touch"},
    ]

    epoch = viewport._begin_sr_snapshot_lifetime()
    result = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))

    assert result["status"] == "ok"
    assert result["snapshot"]["component_facts"] == [
        {
            "source": "sr_attached_runtime_entity",
            "identity_relation": "attached_projection_not_ps_component_equivalence",
            "component_id": "sensor_1",
            "component_type": "sensor",
            "location": "attached",
            "attach_point": [5.0, -2.0],
            "connection_count": 2,
            "inspectable_properties": {},
            "component_fields": {},
        }
    ]
    serialized = str(result["snapshot"]["component_facts"])
    assert "scripts" not in serialized
    assert "actuator_unattached" not in serialized

    selected_child = viewport.query_sr_runtime_entity_snapshot(
        _identity(epoch, "sensor_1")
    )
    assert selected_child["status"] == "ok"
    assert "component_facts" not in selected_child["snapshot"]


def test_restore_envelope_round_trip_and_context_rejection() -> None:
    viewport = GameViewport()
    entity = viewport._SceneRuntimeEntity("e1", "organism", (1.0, 2.0), 5.0)
    viewport.scene_runtime_entities = [entity]
    viewport._sr_runtime_scene_path = "scenes/demo.pond"
    viewport._using_scene_runtime = True
    epoch = viewport._begin_sr_snapshot_lifetime()
    assert epoch
    viewport._scene_runtime_time = 4.0

    envelope = viewport.capture_sr_runtime_restore_envelope()
    entity.position = [99.0, 99.0]
    restored = viewport.restore_sr_runtime_restore_envelope(envelope)

    assert restored == 4.0
    assert entity.position == [1.0, 2.0]

    tampered = dict(envelope)
    tampered["scene_time"] = 8.0
    with pytest.raises(ValueError, match="digest"):
        viewport.restore_sr_runtime_restore_envelope(tampered)

    other = GameViewport()
    other.scene_runtime_entities = [other._SceneRuntimeEntity("e1", "organism", (0.0, 0.0), 5.0)]
    other._sr_runtime_scene_path = "scenes/demo.pond"
    other._using_scene_runtime = True
    other._begin_sr_snapshot_lifetime()
    with pytest.raises(RuntimeError, match="epoch"):
        other.restore_sr_runtime_restore_envelope(envelope)


def test_restore_envelope_round_trips_membrane_topology_owner_state() -> None:
    viewport = GameViewport()
    entity = viewport._SceneRuntimeEntity("hub", "organism", (1.0, 2.0), 5.0)
    viewport.scene_runtime_entities = [entity]
    viewport._sr_runtime_scene_path = "scenes/topology.pond"
    viewport._using_scene_runtime = True
    viewport._begin_sr_snapshot_lifetime()
    viewport._sr_structural_edges = [{"start": "hub", "end": "hub_sensor", "channel": "struct"}]
    viewport._sr_connection_edges = copy.deepcopy(viewport._sr_structural_edges)
    viewport._sr_signal_edges = [{"start": "hub_sensor", "end": "hub", "channel": "chemo"}]
    viewport._scene_runtime_edges = [("hub", "hub_sensor")]
    viewport._scene_runtime_neighbor_ids = {"hub": frozenset({"hub_sensor"})}
    viewport._sr_membrane_attach = {"hub_sensor": ("hub", 1.0, 2.0)}
    viewport._sr_membrane_template = {"sensors": [{"suffix": "sensor"}]}
    viewport._sr_spawn_seq = 7

    envelope = viewport.capture_sr_runtime_restore_envelope()
    viewport._sr_structural_edges = []
    viewport._sr_connection_edges = []
    viewport._sr_signal_edges = []
    viewport._scene_runtime_edges = []
    viewport._scene_runtime_neighbor_ids = {}
    viewport._sr_membrane_attach = {}
    viewport._sr_membrane_template = {}
    viewport._sr_spawn_seq = 0

    viewport.restore_sr_runtime_restore_envelope(envelope)

    assert viewport._sr_structural_edges == envelope["topology"]["structural_edges"]
    assert viewport._sr_signal_edges == envelope["topology"]["signal_edges"]
    assert viewport._sr_membrane_attach == envelope["topology"]["membrane_attach"]
    assert viewport._sr_spawn_seq == 7


def test_topology_owner_round_trip_is_a_single_reversible_surface() -> None:
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    viewport._begin_sr_snapshot_lifetime()
    before = viewport.capture_sr_topology_owner_state()

    updated = copy.deepcopy(before)
    updated["spawn_seq"] = before["spawn_seq"] + 5
    updated["membrane_attach"] = {"same_id": ("same_id", 3.0, 4.0)}
    viewport.restore_sr_topology_owner_state(updated)

    assert viewport.capture_sr_topology_owner_state()["spawn_seq"] == before["spawn_seq"] + 5
    assert viewport._scene_runtime_neighbor_ids == {}
    viewport.restore_sr_topology_owner_state(before)
    assert viewport.capture_sr_topology_owner_state() == before
    assert entity.position == [10.0, 20.0]


def test_topology_owner_rejects_incomplete_state_before_writing() -> None:
    viewport = GameViewport()
    _install_runtime(viewport)
    viewport._begin_sr_snapshot_lifetime()
    before = viewport.capture_sr_topology_owner_state()

    with pytest.raises(ValueError, match="fields_invalid"):
        viewport.restore_sr_topology_owner_state({"spawn_seq": 9})
    assert viewport.capture_sr_topology_owner_state() == before


def test_topology_injection_failure_rolls_back_the_whole_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An injected topology write failure must roll the envelope back."""
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    viewport._begin_sr_snapshot_lifetime()
    viewport._sr_structural_edges = [
        {"start": "same_id", "end": "same_id", "channel": "struct"}
    ]
    viewport._sr_signal_edges = [
        {"start": "same_id", "end": "same_id", "channel": "chemo"}
    ]
    viewport._sr_membrane_attach = {"same_id": ("same_id", 1.0, 1.0)}
    viewport._sr_spawn_seq = 4
    entity.set_energy(50.0)
    envelope = viewport.capture_sr_runtime_restore_envelope()

    baseline_topology = viewport.capture_sr_topology_owner_state()
    entity.set_energy(90.0)
    viewport._sr_structural_edges = []
    viewport._sr_signal_edges = []
    viewport._sr_membrane_attach = {}
    viewport._sr_spawn_seq = 99
    pre_restore_topology = viewport.capture_sr_topology_owner_state()

    real_restore = GameViewport.restore_sr_topology_owner_state
    calls: list[int] = []

    def restore_then_fail(target, state):
        real_restore(target, state)
        calls.append(int(state["spawn_seq"]))
        if len(calls) == 1:
            raise RuntimeError('E537 injected post-topology failure')

    monkeypatch.setattr(
        GameViewport, "restore_sr_topology_owner_state", restore_then_fail
    )
    with pytest.raises(Exception, match="injected post-topology failure"):
        viewport.restore_sr_runtime_restore_envelope(envelope)

    # First call applied the checkpoint topology, second call compensated it.
    assert calls == [4, 99]
    assert viewport.capture_sr_topology_owner_state() == pre_restore_topology
    assert viewport.capture_sr_topology_owner_state() != baseline_topology
    assert entity.energy == 90.0


def test_viewport_exposes_only_explicit_sr_local_input_restore() -> None:
    viewport = GameViewport()
    _install_runtime(viewport)
    viewport._begin_sr_snapshot_lifetime()
    viewport._sr_input_press("W")
    viewport._sr_input.set_mouse_scene(3.0, 4.0)
    state = viewport.capture_sr_input_state()
    viewport._sr_input_clear()
    viewport.restore_sr_input_state(state)
    assert viewport.capture_sr_input_state() == state

    viewport._stop_simulation(write_session=False)
    with pytest.raises(RuntimeError, match="active_epoch"):
        viewport.restore_sr_input_state(state)


def test_runtime_snapshot_captures_and_restores_active_visible_state() -> None:
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    entity.active = False
    entity.visible = False

    epoch = viewport._begin_sr_snapshot_lifetime()
    captured = viewport.query_sr_runtime_entity_snapshot(_identity(epoch))["snapshot"]
    assert captured["active"] is False
    assert captured["visible"] is False

    entity.active = True
    entity.visible = True
    viewport.restore_sr_runtime_snapshot_slice(
        [captured], scene_time=viewport._scene_runtime_time
    )
    assert entity.active is False
    assert entity.visible is False


def test_active_visible_injection_failure_rolls_back_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SR lifecycle/visibility writes are compensated on a mid-restore failure."""
    viewport = GameViewport()
    entity = _install_runtime(viewport)
    entity.active = False
    entity.visible = False
    viewport._begin_sr_snapshot_lifetime()
    envelope = viewport.capture_sr_runtime_restore_envelope()

    # Live owner at restore time differs from the captured baseline, so a
    # successful rollback must land on this state rather than the envelope.
    entity.active = True
    entity.visible = True

    import core.VitaLoom.simulation.sr_runtime_snapshot_restore as restore_module

    real_apply = restore_module._apply_render_identity
    seen_at_failure: list[tuple[bool, bool]] = []

    calls: list[tuple[bool, bool]] = []

    def apply_then_fail(target, value, entity_id):
        real_apply(target, value, entity_id)
        calls.append((bool(entity.active), bool(entity.visible)))
        if len(calls) == 1:
            raise RuntimeError("E537 injected post-lifecycle failure")

    monkeypatch.setattr(restore_module, "_apply_render_identity", apply_then_fail)
    with pytest.raises(Exception):
        viewport.restore_sr_runtime_restore_envelope(envelope)

    # On the failing write the envelope lifecycle is live; the compensating
    # rollback re-applies render_identity after lifecycle is already back to
    # the live pre-restore state.
    assert calls == [(False, False), (True, True)]
    assert entity.active is True
    assert entity.visible is True

    # A non-boolean lifecycle value is rejected before any mutation.
    tampered = copy.deepcopy(envelope)
    tampered["snapshots"][0]["active"] = "yes"
    tampered.pop("digest")
    from core.VitaLoom.simulation.sr_runtime_snapshot_restore import snapshot_restore_digest

    tampered["digest"] = snapshot_restore_digest(tampered)
    with pytest.raises(Exception):
        viewport.restore_sr_runtime_restore_envelope(tampered)
    assert entity.active is True
    assert entity.visible is True
