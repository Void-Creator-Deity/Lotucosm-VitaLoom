from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from builtin.entity_types.organism import Organism
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.memory import MemoryGene
from core.Lotucosm.runtime.world_bridge_field_mapper import (
    WorldBridgeFieldBatchError,
    WorldBridgeFieldMapper,
)
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR


def test_sr_to_ps_batch_compensates_prior_fields_and_partially_written_setter() -> None:
    entity = EntityBase(
        "sr-batch",
        position=(12.0, 13.0),
        velocity=(4.0, 5.0),
        acceleration=(6.0, 7.0),
    )
    entity.energy = 23.0
    entity.health = 34.0
    entity.active = False
    entity.sr_memory_genes = [MemoryGene("source", {"ax": 2.0}, 0.7)]

    organism = Organism("ps-batch", (1.0, 2.0))
    organism.restore_motion_state(
        position=(8.0, 9.0),
        velocity=(-1.0, -2.0),
        acceleration=(-3.0, -4.0),
    )
    organism.set_energy(81.0)
    organism.set_health(72.0)
    organism.active = True
    original_gene = MemoryGene("original", {"ay": 3.0}, 0.6)
    organism.replace_memory_genes([original_gene])

    calls = 0

    def write_then_fail_once(value: float) -> None:
        nonlocal calls
        organism.health = value
        if calls == 0:
            calls += 1
            raise RuntimeError("health setter failed after mutation")

    organism.set_health = write_then_fail_once

    try:
        WorldBridgeFieldMapper().sync_sr_to_ps(entity, organism)
    except WorldBridgeFieldBatchError as exc:
        error = exc
    else:
        raise AssertionError("the injected owner setter failure must escape the mapper")

    assert error.failed_field == "health"
    assert error.direction == "sr_to_ps"
    assert error.phase == "apply"
    assert error.mutation_started is True
    assert error.rollback_attempted is True
    assert error.rollback_complete is True
    assert error.rollback_errors == ()
    assert organism.position.tolist() == [8.0, 9.0]
    assert organism.velocity.tolist() == [-1.0, -2.0]
    assert organism.acceleration.tolist() == [-3.0, -4.0]
    assert organism.energy == 81.0
    assert organism.health == 72.0
    assert organism.active is True
    assert organism.memory_genes == [original_gene]
    assert organism.memory_genes[0] is original_gene


def test_field_batch_reports_incomplete_compensation_by_field() -> None:
    entity = EntityBase("sr-incomplete", position=(4.0, 5.0))
    entity.energy = 20.0
    entity.health = 30.0
    organism = Organism("ps-incomplete", (1.0, 2.0))
    organism.set_energy(80.0)
    organism.set_health(70.0)
    calls = 0

    def fail_apply_and_compensation(value: float) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            organism.health = value
            raise RuntimeError("apply failed after write")
        raise RuntimeError("compensation rejected")

    organism.set_health = fail_apply_and_compensation

    try:
        WorldBridgeFieldMapper().sync_sr_to_ps(entity, organism)
    except WorldBridgeFieldBatchError as exc:
        error = exc
    else:
        raise AssertionError("the injected owner setter failure must escape the mapper")

    assert error.failed_field == "health"
    assert error.rollback_complete is False
    assert error.rollback_attempted is True
    assert any(item.startswith("health: RuntimeError: compensation rejected") for item in error.rollback_errors)
    assert organism.health == 30.0


def test_capture_failure_rejects_before_any_owner_field_is_applied() -> None:
    entity = EntityBase("sr-capture-failure", position=(9.0, 10.0))
    entity.energy = 22.0
    entity.health = 33.0
    organism = Organism("ps-capture-failure", (1.0, 2.0))
    organism.energy = None
    original_position = organism.position.copy()

    try:
        WorldBridgeFieldMapper().sync_sr_to_ps(entity, organism)
    except WorldBridgeFieldBatchError as exc:
        error = exc
    else:
        raise AssertionError("an un-restorable destination snapshot must fail closed")

    assert error.phase == "capture"
    assert error.failed_field == "energy"
    assert error.mutation_started is False
    assert error.rollback_attempted is False
    assert organism.position.tolist() == original_position.tolist()
    assert organism.energy is None


def test_game_viewport_owner_api_failure_is_compensated_and_reported() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None
    viewport = GameViewport()
    viewport._unified_pond_mode = True
    entity = viewport._SceneRuntimeEntity("hub-batch", "organism", (2.0, 3.0), 12.0)
    viewport.scene_runtime_entities = [entity]
    viewport._ensure_unified_bridge_for_scene()
    pond = viewport._unified_pond
    organism_id = getattr(entity, BRIDGE_ORGANISM_ATTR)
    organism = pond.organisms[str(organism_id)]
    original_position = tuple(float(value) for value in entity.position)

    def update_owner_state() -> None:
        organism.set_position((40.0, 50.0))

    pond.update = update_owner_state
    original_set_position = entity.set_position
    fail_once = True

    def write_then_fail(position: tuple[float, float]) -> None:
        nonlocal fail_once
        original_set_position(position)
        if fail_once:
            fail_once = False
            raise RuntimeError("viewport position setter failed after write")

    entity.set_position = write_then_fail

    assert viewport._run_unified_pond_bridge_tick(0.05) is None
    assert tuple(float(value) for value in entity.position) == original_position
    assert not hasattr(entity, "sr_memory_genes")
    receipt = viewport._worldbridge_last_handoff_failure
    assert receipt["phase"] == "ps_to_sr_reflection"
    assert receipt["cause_type"] == "WorldBridgeFieldBatchError"
    assert receipt["partial_mutation_possible"] is True
    assert receipt["rollback_performed"] is False
    batch = receipt["field_batch_failure"]
    assert batch == {
        "direction": "ps_to_sr",
        "failed_field": "position",
        "phase": "apply",
        "mutation_started": True,
        "rollback_attempted": True,
        "rollback_complete": True,
        "rollback_errors": [],
    }

