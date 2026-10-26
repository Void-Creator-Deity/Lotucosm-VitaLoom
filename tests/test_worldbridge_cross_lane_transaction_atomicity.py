# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.Lotucosm.runtime.world_bridge as bridge
from core.Lotucosm.runtime.world_bridge import (
    BRIDGE_ORGANISM_ATTR,
    unified_pond_step,
    unified_pond_step_with_trace,
)
from core.Lotucosm.runtime.world_bridge_transaction_authority import (
    WorldBridgeHandoffFailure,
    build_worldbridge_transaction_failure_isolation_contract,
    validate_worldbridge_transaction_failure_isolation_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
WORLD_BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"
AUTHORITY = RUNTIME / "core/Lotucosm/runtime/world_bridge_transaction_authority.py"


class FakePond:
    def __init__(self, organisms: dict[str, SimpleNamespace], *, fail_update: bool = False) -> None:
        self.organisms = organisms
        self.update_calls = 0
        self.fail_update = fail_update

    def update(self) -> None:
        self.update_calls += 1
        for organism in self.organisms.values():
            organism.position[0] += 10.0
            organism.energy -= 4.0
        if self.fail_update:
            raise RuntimeError("pond exploded after partial mutation")


def _entity(entity_id: str = "sr:a", organism_id: str = "ps:a") -> SimpleNamespace:
    entity = SimpleNamespace(
        id=entity_id,
        entity_type="organism",
        position=[1.0, 2.0],
        velocity=[0.5, 0.25],
        acceleration=[0.0, 0.0],
        radius=4.0,
        size=8.0,
        energy=30.0,
        health=20.0,
        generation=3,
        sr_debug_hud={},
    )
    setattr(entity, BRIDGE_ORGANISM_ATTR, organism_id)
    return entity


def _organism(organism_id: str = "ps:a") -> SimpleNamespace:
    return SimpleNamespace(
        id=organism_id,
        position=[100.0, 200.0],
        velocity=[0.0, 0.0],
        acceleration=[0.0, 0.0],
        radius=4.0,
        size=8.0,
        energy=90.0,
        health=40.0,
        generation=3,
        developmental_stage=2,
    )


def _receipt(error: pytest.ExceptionInfo[WorldBridgeHandoffFailure]) -> dict[str, object]:
    assert isinstance(error.value, WorldBridgeHandoffFailure)
    return error.value.receipt


def test_contract_is_qt_free_and_rejects_transaction_rollback_replay_overclaims(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = build_worldbridge_transaction_failure_isolation_contract()
    assert validate_worldbridge_transaction_failure_isolation_contract(contract)["valid"] is True
    assert contract["failure_semantics"]["partial_mutation_possible_after_live_phase_starts"] is True
    for field in ("cross_lane_transaction", "rollback_performed", "atomic_checkpoint"):
        assert contract["failure_semantics"][field] is False
    for field in ("cross_lane_transaction", "rollback", "atomicity", "checkpoint_restore", "replay_admitted", "default_ready"):
        assert contract["admissions"][field] is False
        tampered = copy.deepcopy(contract)
        tampered["admissions"][field] = True
        assert validate_worldbridge_transaction_failure_isolation_contract(tampered)["valid"] is False

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_transaction_authority", AUTHORITY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_transaction_failure_isolation_contract()["contract_valid"] is True


def test_trace_preflight_failure_mutates_neither_lane() -> None:
    entity = _entity()
    organism = _organism()
    pond = SimpleNamespace(organisms={"ps:a": organism})

    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step_with_trace(pond, [entity], sr_checkpoint={"sim_time": 0.0})

    receipt = _receipt(error)
    assert receipt["phase"] == "preflight"
    assert receipt["partial_mutation_possible"] is False
    assert receipt["phase_started"] == {"sr_to_ps_sync": False, "pond_update": False, "ps_to_sr_reflection": False}
    assert entity.position == [1.0, 2.0]
    assert organism.position == [100.0, 200.0]


def test_plain_handoff_rejects_duplicate_ps_binding_before_sync() -> None:
    first = _entity("sr:a", "ps:a")
    second = _entity("sr:b", "ps:a")
    organism = _organism()
    pond = FakePond({"ps:a": organism})

    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step(pond, [first, second])

    receipt = _receipt(error)
    assert receipt["phase"] == "preflight"
    assert receipt["partial_mutation_possible"] is False
    assert receipt["phase_started"] == {
        "sr_to_ps_sync": False,
        "pond_update": False,
        "ps_to_sr_reflection": False,
    }
    assert pond.update_calls == 0
    assert organism.position == [100.0, 200.0]
    assert first.position == [1.0, 2.0]
    assert second.position == [1.0, 2.0]


def test_plain_handoff_rejects_duplicate_sr_identity_before_sync() -> None:
    first = _entity("sr:a", "ps:a")
    second = _entity("sr:a", "ps:b")
    first_organism = _organism("ps:a")
    second_organism = _organism("ps:b")
    pond = FakePond({"ps:a": first_organism, "ps:b": second_organism})

    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step(pond, [first, second])

    assert _receipt(error)["phase"] == "preflight"
    assert pond.update_calls == 0
    assert first_organism.position == [100.0, 200.0]
    assert second_organism.position == [100.0, 200.0]


def test_trace_handoff_keeps_duplicate_binding_value_error_before_sync() -> None:
    first = _entity("sr:a", "ps:a")
    second = _entity("sr:b", "ps:a")
    organism = _organism()
    pond = FakePond({"ps:a": organism})

    with pytest.raises(ValueError, match="duplicate ps_organism_id"):
        unified_pond_step_with_trace(
            pond, [first, second], sr_checkpoint={"sim_time": 0.0}
        )

    assert pond.update_calls == 0
    assert organism.position == [100.0, 200.0]


@pytest.mark.parametrize("trace_requested", [False, True])
def test_handoff_rejects_binding_drift_before_reflection(trace_requested: bool) -> None:
    entity = _entity()
    original = _organism("ps:a")
    other = _organism("ps:b")
    pond = FakePond({"ps:a": original, "ps:b": other})
    pond.time = 0
    pond.iteration = 0
    update = pond.update

    def change_binding_during_update() -> None:
        update()
        pond.time += 1
        setattr(entity, BRIDGE_ORGANISM_ATTR, "ps:b")

    pond.update = change_binding_during_update
    with pytest.raises(WorldBridgeHandoffFailure) as error:
        if trace_requested:
            unified_pond_step_with_trace(pond, [entity], sr_checkpoint={"sim_time": 0.0})
        else:
            unified_pond_step(pond, [entity])

    receipt = _receipt(error)
    assert receipt["phase"] == "ps_to_sr_reflection"
    assert receipt["phase_started"] == {
        "sr_to_ps_sync": True,
        "pond_update": True,
        "ps_to_sr_reflection": False,
    }
    assert receipt["rollback_performed"] is False
    assert pond.update_calls == 1
    assert entity.position == [1.0, 2.0]
    assert entity.energy == 30.0


@pytest.mark.parametrize("trace_requested", [False, True])
def test_sync_binding_drift_stops_before_pond_update(
    trace_requested: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    entity = _entity()
    organism = _organism()
    pond = FakePond({"ps:a": organism})

    def change_binding(source: SimpleNamespace, target: SimpleNamespace) -> None:
        setattr(source, BRIDGE_ORGANISM_ATTR, "ps:b")

    monkeypatch.setattr(bridge, "sync_sr_entity_to_organism", change_binding)
    with pytest.raises(WorldBridgeHandoffFailure) as error:
        if trace_requested:
            unified_pond_step_with_trace(pond, [entity], sr_checkpoint={"sim_time": 0.0})
        else:
            unified_pond_step(pond, [entity])

    receipt = _receipt(error)
    assert receipt["phase"] == "sr_to_ps_sync"
    assert receipt["phase_started"]["pond_update"] is False
    assert pond.update_calls == 0


@pytest.mark.parametrize("trace_requested", [False, True])
@pytest.mark.parametrize("mutation", ["replace", "remove"])
def test_handoff_rejects_ps_object_identity_change_after_update(
    trace_requested: bool, mutation: str
) -> None:
    entity = _entity()
    original = _organism()
    pond = FakePond({"ps:a": original})
    pond.time = 0
    pond.iteration = 0
    update = pond.update

    def change_ps_identity() -> None:
        update()
        pond.time += 1
        if mutation == "replace":
            pond.organisms["ps:a"] = _organism()
        else:
            del pond.organisms["ps:a"]

    pond.update = change_ps_identity
    if mutation == "remove":
        unified_pond_step(pond, [entity])
    else:
        with pytest.raises(WorldBridgeHandoffFailure) as error:
            if trace_requested:
                unified_pond_step_with_trace(pond, [entity], sr_checkpoint={"sim_time": 0.0})
            else:
                unified_pond_step(pond, [entity])
        receipt = _receipt(error)
        assert receipt["phase"] == ("trace_ps_capture" if trace_requested else "ps_to_sr_reflection")
        assert receipt["phase_started"]["pond_update"] is True
        assert receipt["phase_started"]["ps_to_sr_reflection"] is False
        assert receipt["rollback_performed"] is False
    assert pond.update_calls == 1
    assert entity.position == [1.0, 2.0]
    assert entity.energy == 30.0


def test_plain_unbound_handoff_keeps_missing_organism_map_noop() -> None:
    pond = SimpleNamespace(update=lambda: None)
    entity = SimpleNamespace(id="sr:unbound", position=[1.0, 2.0])

    unified_pond_step(pond, [entity])

    assert entity.position == [1.0, 2.0]


def test_sr_to_ps_failure_is_labelled_and_stops_before_pond_update(monkeypatch: pytest.MonkeyPatch) -> None:
    entity = _entity()
    pond = FakePond({"ps:a": _organism()})

    def fail_sync(_entity: object, _organism: object) -> None:
        raise RuntimeError("sync failed")

    monkeypatch.setattr(bridge, "sync_sr_entity_to_organism", fail_sync)
    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step(pond, [entity])

    receipt = _receipt(error)
    assert receipt["phase"] == "sr_to_ps_sync"
    assert receipt["phase_started"] == {"sr_to_ps_sync": True, "pond_update": False, "ps_to_sr_reflection": False}
    assert receipt["partial_mutation_possible"] is True
    assert receipt["rollback_performed"] is False
    assert pond.update_calls == 0


def test_pond_failure_records_partial_mutation_and_skips_reflection() -> None:
    entity = _entity()
    organism = _organism()
    pond = FakePond({"ps:a": organism}, fail_update=True)

    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step(pond, [entity])

    receipt = _receipt(error)
    assert receipt["phase"] == "pond_update"
    assert receipt["phase_started"] == {"sr_to_ps_sync": True, "pond_update": True, "ps_to_sr_reflection": False}
    assert receipt["partial_mutation_possible"] is True
    assert receipt["cross_lane_transaction"] is False
    assert pond.update_calls == 1
    assert organism.position == [11.0, 2.0]
    assert entity.position == [1.0, 2.0]


def test_reflection_failure_is_labelled_and_cannot_claim_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    entity = _entity()
    organism = _organism()
    pond = FakePond({"ps:a": organism})

    def fail_reflection(source: SimpleNamespace, target: SimpleNamespace) -> None:
        target.position[:] = source.position
        raise RuntimeError("display write failed after partial mutation")

    monkeypatch.setattr(bridge, "sync_organism_to_sr_display", fail_reflection)
    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step(pond, [entity])

    receipt = _receipt(error)
    assert receipt["phase"] == "ps_to_sr_reflection"
    assert receipt["phase_started"] == {"sr_to_ps_sync": True, "pond_update": True, "ps_to_sr_reflection": True}
    assert receipt["rollback_performed"] is False
    assert pond.update_calls == 1
    assert entity.position == [11.0, 2.0]


def test_trace_uses_same_phase_receipt_on_pond_failure_and_does_not_reflect() -> None:
    entity = _entity()
    organism = _organism()
    pond = FakePond({"ps:a": organism}, fail_update=True)

    with pytest.raises(WorldBridgeHandoffFailure) as error:
        unified_pond_step_with_trace(pond, [entity], sr_checkpoint={"sim_time": 0.0})

    receipt = _receipt(error)
    assert receipt["trace_requested"] is True
    assert receipt["phase"] == "pond_update"
    assert receipt["phase_started"] == {"sr_to_ps_sync": True, "pond_update": True, "ps_to_sr_reflection": False}
    assert pond.update_calls == 1
    assert entity.position == [1.0, 2.0]


def test_runtime_status_nests_contract_without_dual_or_default_readiness_admission() -> None:
    contract = build_worldbridge_transaction_failure_isolation_contract()
    status = build_runtime_worldbridge_status()
    assert status["cross_lane_transaction_failure_isolation_contract"] == contract
    assert "cross_lane_transaction_failure_isolation_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False


def test_bridge_source_preflights_before_sync_and_labels_each_live_phase() -> None:
    tree = ast.parse(WORLD_BRIDGE.read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for public_name, implementation_name in (
        ("unified_pond_step", "_unified_pond_step_impl"),
        ("unified_pond_step_with_trace", "_unified_pond_step_with_trace_impl"),
    ):
        wrapper = ast.unparse(functions[public_name])
        source = ast.unparse(functions[implementation_name])
        assert implementation_name in wrapper
        assert "_prepare_unified_pond_handoff" in source
        assert "WorldBridgeHandoffFailure" not in source
        assert "PHASE_SR_TO_PS_SYNC" in source
        assert "PHASE_POND_UPDATE" in source
        assert "PHASE_PS_TO_SR_REFLECTION" in source
    traced = ast.unparse(functions["_unified_pond_step_with_trace_impl"])
    assert "PHASE_TRACE_SR_CAPTURE" in traced
    assert "PHASE_TRACE_PS_CAPTURE" in traced
