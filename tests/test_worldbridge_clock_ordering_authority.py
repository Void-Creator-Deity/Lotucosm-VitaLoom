# -*- coding: utf-8 -*-
"""E233 tests for source-backed WorldBridge clock/order non-admission."""
from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (
    SERIAL_HANDOFF_ORDER,
    build_worldbridge_clock_ordering_authority_contract,
    observe_worldbridge_clock_ordering,
    validate_worldbridge_clock_ordering_authority_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"
DRIVER = RUNTIME / "core" / "VitaLoom" / "viewports" / "simulation_driver.py"


def _method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise AssertionError(f"missing {class_name}.{method_name}")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function {name}")


def _attribute_calls(node: ast.AST) -> list[str]:
    return [
        call.func.attr
        for call in sorted(
            ast.walk(node),
            key=lambda item: (getattr(item, "lineno", -1), getattr(item, "col_offset", -1)),
        )
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    ]


def test_contract_admits_only_serial_handoff_not_common_clock_or_atomicity() -> None:
    contract = build_worldbridge_clock_ordering_authority_contract()
    assert validate_worldbridge_clock_ordering_authority_contract(contract) == {"valid": True, "errors": []}
    assert contract["contract_valid"] is True
    assert contract["runtime_mode"] == "dual"
    assert contract["clock_relation"]["shared_clock"] is False
    assert contract["clock_relation"]["time_conversion_admitted"] is False
    assert contract["serial_handoff"]["order"] == list(SERIAL_HANDOFF_ORDER)
    assert contract["serial_handoff"]["atomicity_admitted"] is False
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False


def test_observations_cover_pause_variable_speed_and_missed_handoff_without_conversion() -> None:
    paused = observe_worldbridge_clock_ordering(4.0, paused=True, bridge_handoff_invoked=True)
    slow = observe_worldbridge_clock_ordering(0.01, paused=False, bridge_handoff_invoked=True)
    fast = observe_worldbridge_clock_ordering(3.0, paused=False, bridge_handoff_invoked=True)
    missed = observe_worldbridge_clock_ordering(1.0, paused=False, bridge_handoff_invoked=False)
    assert (paused["sr_delta_seconds"], paused["ps_ticks_advanced"]) == (0.0, 0)
    assert slow["sr_delta_seconds"] == pytest.approx(0.01)
    assert slow["ps_ticks_advanced"] == 1
    assert fast["sr_delta_seconds"] == pytest.approx(0.15)
    assert fast["ps_ticks_advanced"] == 1
    assert (missed["sr_delta_seconds"], missed["ps_ticks_advanced"]) == (0.05, 0)
    assert all(item["time_conversion_admitted"] is False for item in (paused, slow, fast, missed))
    with pytest.raises(ValueError, match="finite"):
        observe_worldbridge_clock_ordering(float("nan"), paused=False, bridge_handoff_invoked=True)


def test_validator_rejects_clock_conversion_ordering_atomic_and_runtime_overclaims() -> None:
    contract = build_worldbridge_clock_ordering_authority_contract()
    cases = {
        "shared_clock_overclaim": ("clock_relation", "shared_clock", True),
        "time_conversion_overclaim": ("clock_relation", "time_conversion_admitted", True),
        "time_conversion_value_overclaim": ("clock_relation", "sr_seconds_per_ps_tick", 0.05),
        "cross_call_ordering_overclaim": ("serial_handoff", "cross_call_ordering_admitted", True),
        "atomicity_overclaim": ("serial_handoff", "atomicity_admitted", True),
        "replay_overclaim": (None, "replay_admitted", True),
        "default_ready_overclaim": (None, "default_ready", True),
    }
    for error, (section, field, value) in cases.items():
        tampered = copy.deepcopy(contract)
        target = tampered if section is None else tampered[section]
        target[field] = value
        result = validate_worldbridge_clock_ordering_authority_contract(tampered)
        assert result["valid"] is False
        assert error in result["errors"]


def test_runtime_status_nests_the_static_clock_order_contract() -> None:
    contract = build_worldbridge_clock_ordering_authority_contract()
    status = build_runtime_worldbridge_status()
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
    assert status["common_clock_cross_lane_ordering_authority_contract"] == contract


def test_real_sources_support_pause_phase_order_and_serial_handoff_only() -> None:
    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    update = _method(viewport, "GameViewport", "_update_simulation")
    update_calls = _attribute_calls(update)
    assert "_update_scene_runtime_entities" in update_calls
    pause_if = next(
        node for node in ast.walk(update)
        if isinstance(node, ast.If) and isinstance(node.test, ast.Attribute) and node.test.attr == "is_paused"
    )
    assert any(isinstance(child, ast.Return) for child in ast.walk(pause_if))

    snapshot = _method(viewport, "GameViewport", "run_snapshot_phase")
    calls = _attribute_calls(snapshot)
    assert calls.index("_refresh_sr_hud") < calls.index("_run_unified_pond_bridge_tick") < calls.index("_publish_sr_runtime_snapshots")

    driver = ast.parse(DRIVER.read_text(encoding="utf-8"))
    tick = _method(driver, "SimulationDriver", "tick")
    phase_calls = _attribute_calls(tick)
    expected = ["prepare_simulation_tick", "run_script_phase", "run_spawn_phase", "run_actuator_phase", "run_fluid_phase", "run_physics_phase", "run_survival_phase", "run_snapshot_phase"]
    assert [name for name in phase_calls if name in expected] == expected


def test_real_sources_keep_one_pond_tick_per_handoff_with_explicit_shared_delta() -> None:
    bridge = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry = _function(bridge, "unified_pond_step")
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_unified_pond_step_impl"
        for node in ast.walk(entry)
    ), "unified_pond_step must delegate to _unified_pond_step_impl"
    step = _function(bridge, "_unified_pond_step_impl")
    update_calls = [
        node for node in ast.walk(step)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_invoke_clocked_pond_update"
    ]
    assert len(update_calls) == 1
    assert len(update_calls[0].args) == 2
    assert all(isinstance(arg, ast.Name) for arg in update_calls[0].args)

    pond = ast.parse(POND.read_text(encoding="utf-8"))
    update = _method(pond, "Pond", "update")
    assert any(
        isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Attribute)
        and node.target.attr == "time"
        and isinstance(node.op, ast.Add)
        and isinstance(node.value, ast.Constant)
        and node.value.value == 1
        for node in ast.walk(update)
    )
    assert any(
        isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Attribute)
        and node.target.attr == "simulation_time"
        and isinstance(node.value, ast.Name)
        for node in ast.walk(update)
    )




