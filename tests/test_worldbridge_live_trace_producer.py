# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge import (
    BRIDGE_ORGANISM_ATTR,
    unified_pond_step_with_trace,
)
from core.Lotucosm.runtime.world_bridge_live_trace_producer import (
    CAPTURE_ORDER,
    build_worldbridge_live_trace_producer_contract,
    collect_worldbridge_live_entity_links,
    validate_worldbridge_live_dual_lane_trace,
)
from core.Lotucosm.runtime.world_bridge_live_trace_comparability import (
    evaluate_worldbridge_live_trace_fields,
    validate_worldbridge_live_trace_field_evaluation,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
PRODUCER = RUNTIME / "core/Lotucosm/runtime/world_bridge_live_trace_producer.py"
WORLD_BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"


class FakePond:
    def __init__(self, organisms: dict[str, SimpleNamespace]) -> None:
        self.organisms = organisms
        self.time = 0
        self.iteration = 2
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1
        self.time += 1
        for organism in self.organisms.values():
            organism.position[0] += 2.0
            organism.energy -= 3.0


def _entity(entity_id: str, organism_id: str) -> SimpleNamespace:
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


def _organism(organism_id: str) -> SimpleNamespace:
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


def _run_once() -> tuple[dict[str, object], SimpleNamespace, FakePond, dict[str, object]]:
    entity = _entity("sr:a", "ps:a")
    pond = FakePond({"ps:a": _organism("ps:a")})
    observation: dict[str, object] = {
        "sim_time": 1.25,
        "population": 1,
        "nested": {"value": 7},
    }
    payload = unified_pond_step_with_trace(
        pond,
        [entity],
        sr_checkpoint=observation,
        delta_time=0.05,
    )
    return payload, entity, pond, observation


def test_live_step_produces_deterministic_ordered_non_atomic_trace() -> None:
    first, first_entity, first_pond, _ = _run_once()
    second, _, _, _ = _run_once()

    assert first == second
    assert validate_worldbridge_live_dual_lane_trace(first)["valid"] is True
    assert first["capture_order"] == list(CAPTURE_ORDER)
    assert first["atomic_checkpoint"] is False
    assert first["atomicity"] == "ordered_non_atomic_dual_lane_capture"
    assert first["observed_sr_delta"] == 0.05
    assert first["sr_delta_consumed_by_pond"] is False
    assert first_pond.update_calls == 1

    trace = first["trace"]
    assert trace["lanes"]["sr"]["checkpoint"]["bridged_entities"][0]["position"] == [1.0, 2.0]
    assert trace["lanes"]["ps"]["checkpoint"]["bridged_organisms"][0]["position"] == [3.0, 2.0]
    assert first_entity.position == [3.0, 2.0]
    assert first_entity.energy == 27.0
    assert first_entity.sr_debug_hud["bridge_sync"] == 1


def test_live_trace_preserves_sr2d_backend_capability_evidence() -> None:
    entity = _entity("sr:backend", "ps:backend")
    pond = FakePond({"ps:backend": _organism("ps:backend")})
    payload = unified_pond_step_with_trace(
        pond,
        [entity],
        sr_checkpoint={
            "sim_time": 0.0,
            "physics_backend": {
                "schema_version": 1,
                "backend_id": "cpp",
                "abi_contract": "sr2d_pvaec_circles_v1",
            },
        },
    )
    backend = payload["trace"]["lanes"]["sr"]["checkpoint"]["physics_backend"]
    assert backend["backend_id"] == "cpp"
    assert backend["abi_contract"] == "sr2d_pvaec_circles_v1"


def test_live_trace_records_ps_removal_without_reflecting_missing_target() -> None:
    entity = _entity("sr:removed", "ps:removed")
    pond = FakePond({"ps:removed": _organism("ps:removed")})
    update = pond.update

    def remove_after_update() -> None:
        update()
        del pond.organisms["ps:removed"]

    pond.update = remove_after_update
    payload = unified_pond_step_with_trace(
        pond, [entity], sr_checkpoint={"sim_time": 0.0}, delta_time=0.05
    )

    checkpoint = payload["trace"]["lanes"]["ps"]["checkpoint"]
    assert checkpoint["population"] == 0
    assert checkpoint["bridged_organisms"] == []
    assert checkpoint["retired_bridge_links"] == [{
        "sr_entity_id": "sr:removed",
        "ps_organism_id": "ps:removed",
        "reason": "missing_after_pond_update",
    }]
    assert validate_worldbridge_live_dual_lane_trace(payload)["valid"] is True
    evaluation = evaluate_worldbridge_live_trace_fields(payload)
    assert validate_worldbridge_live_trace_field_evaluation(evaluation)["valid"] is True
    assert evaluation["pair_results"][0]["comparable_status"] == "not_observed"
    assert entity.position == [1.0, 2.0]


def test_live_trace_is_copy_isolated_and_preserves_no_claims() -> None:
    payload, _, _, observation = _run_once()
    observation["nested"]["value"] = 99  # type: ignore[index]

    assert payload["trace"]["lanes"]["sr"]["checkpoint"]["nested"]["value"] == 7
    assert payload["shared_clock"] is False
    assert payload["lossless"] is False
    assert payload["replay_admitted"] is False
    assert payload["default_ready"] is False
    assert payload["trace"]["declared_mapping_losses"] == [
        "hierarchy",
        "membrane_component_graph",
        "memory_genes",
        "render_identity",
        "scripts",
    ]


def test_missing_or_duplicate_live_pairs_reject_before_pond_update() -> None:
    missing = _entity("sr:a", "ps:missing")
    missing_pond = FakePond({})
    with pytest.raises(ValueError, match="missing ps_organism_id"):
        unified_pond_step_with_trace(
            missing_pond,
            [missing],
            sr_checkpoint={"sim_time": 0.0},
        )
    assert missing_pond.update_calls == 0

    first = _entity("sr:a", "ps:a")
    second = _entity("sr:b", "ps:a")
    duplicate_pond = FakePond({"ps:a": _organism("ps:a")})
    with pytest.raises(ValueError, match="duplicate ps_organism_id"):
        collect_worldbridge_live_entity_links([first, second], duplicate_pond)
    assert duplicate_pond.update_calls == 0


def test_live_trace_validator_rejects_atomicity_and_digest_tampering() -> None:
    payload, _, _, _ = _run_once()
    tampered = copy.deepcopy(payload)
    tampered["atomic_checkpoint"] = True
    result = validate_worldbridge_live_dual_lane_trace(tampered)
    assert result["valid"] is False
    assert "atomic_checkpoint_not_admitted" in result["errors"]
    assert "producer_digest_mismatch" in result["errors"]


def test_live_trace_validator_rejects_capture_source_and_pair_set_tampering() -> None:
    payload, _, _, _ = _run_once()
    tampered = copy.deepcopy(payload)
    tampered["trace"]["lanes"]["sr"]["checkpoint"]["capture_source"] = "after_bridge"
    tampered["trace"]["lanes"]["ps"]["checkpoint"]["bridged_organisms"] = []
    result = validate_worldbridge_live_dual_lane_trace(tampered)
    assert result["valid"] is False
    assert "sr_capture_source_mismatch" in result["errors"]
    assert "ps_checkpoint_link_set_mismatch" in result["errors"]
    assert "producer_digest_mismatch" in result["errors"]


def test_producer_contract_is_nested_in_runtime_status_without_admission() -> None:
    contract = build_worldbridge_live_trace_producer_contract()
    assert contract["contract_valid"] is True
    assert contract["atomic_checkpoint"] is False
    assert contract["tick_merge_admitted"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False

    status = build_runtime_worldbridge_status()
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["live_dual_lane_trace_producer_contract"] == contract


def test_live_trace_wrapper_source_has_mechanical_capture_order() -> None:
    tree = ast.parse(WORLD_BRIDGE.read_text(encoding="utf-8"))
    entry = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "unified_pond_step_with_trace"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_unified_pond_step_with_trace_impl"
        for node in ast.walk(entry)
    ), "unified_pond_step_with_trace must delegate to _unified_pond_step_with_trace_impl"
    function = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_unified_pond_step_with_trace_impl"
    )
    call_lines: dict[str, int] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            call_lines[node.func.id] = min(call_lines.get(node.func.id, node.lineno), node.lineno)
    assert call_lines["capture_worldbridge_sr_checkpoint"] < call_lines["sync_sr_entity_to_organism"]
    assert call_lines["sync_sr_entity_to_organism"] < call_lines["_invoke_clocked_pond_update"]
    assert call_lines["_invoke_clocked_pond_update"] < call_lines["capture_worldbridge_ps_checkpoint"]
    assert call_lines["capture_worldbridge_ps_checkpoint"] < call_lines["sync_organism_to_sr_display"]
    assert call_lines["sync_organism_to_sr_display"] < call_lines["build_worldbridge_live_dual_lane_trace"]


def test_producer_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_live_trace_producer", PRODUCER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_live_trace_producer_contract()["contract_valid"] is True
