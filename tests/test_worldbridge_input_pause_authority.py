# -*- coding: utf-8 -*-
"""E234 source-backed WorldBridge input/lifecycle non-admission tests."""
from __future__ import annotations

import ast
import copy
import inspect
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_input_pause_authority import (
    build_worldbridge_input_pause_authority_contract,
    observe_worldbridge_sr_input_lifecycle,
    validate_worldbridge_input_pause_authority_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"
INPUT_STATE = RUNTIME / "core" / "VitaLoom" / "viewports" / "sr_input_state.py"
BRIDGE = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge.py"
DRIVER = RUNTIME / "core" / "VitaLoom" / "viewports" / "simulation_driver.py"
GAME_TICK = RUNTIME / "core" / "Lotucosm" / "scene_runtime" / "game_tick.py"


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


def _contains_self_call(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "self"
        and call.func.attr == name
        for call in ast.walk(node)
    )


def test_contract_admits_only_sr_local_input_and_lifecycle_buffer_discards() -> None:
    contract = build_worldbridge_input_pause_authority_contract()
    assert validate_worldbridge_input_pause_authority_contract(contract) == {"valid": True, "errors": []}
    assert contract["contract_valid"] is True
    assert contract["runtime_mode"] == "dual"
    assert contract["sr_input"]["script_phase_precedes_opt_in_bridge_handoff"] is True
    assert contract["ps_input"] == {
        "pond_update_input_argument": False,
        "shared_queue": False,
        "shared_event_log": False,
        "ps_received_sr_input": False,
    }
    assert all(value is True for key, value in contract["lifecycle"].items() if key.endswith("clears_sr_input"))
    assert contract["lifecycle"]["shared_pause_reset_authority"] is False
    assert all(value is False for value in contract["admissions"].values())


def test_observation_covers_inactive_paused_sr_only_bridge_and_lifecycle_without_queue() -> None:
    inactive = observe_worldbridge_sr_input_lifecycle(
        playing=False, paused=False, bridge_handoff_invoked=True
    )
    paused = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=True, bridge_handoff_invoked=True
    )
    sr_only = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=False, bridge_handoff_invoked=False
    )
    bridge = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=False, bridge_handoff_invoked=True
    )
    resumed = observe_worldbridge_sr_input_lifecycle(
        playing=True, paused=True, bridge_handoff_invoked=True, lifecycle_action="resume"
    )
    for observation in (inactive, paused, sr_only, bridge, resumed):
        assert observation["ps_received_input"] is False
        assert observation["shared_queue"] is False
        assert observation["shared_event_log"] is False
        assert observation["cross_lane_input_ordering"] is False
        assert observation["input_replay_admitted"] is False
        assert observation["checkpoint_input_state"] is False
        assert observation["shared_pause_reset_authority"] is False
        assert observation["atomicity_admitted"] is False
        assert observation["default_ready"] is False
    assert inactive["sr_snapshot_admitted"] is False
    assert paused["sr_snapshot_admitted"] is False
    assert sr_only["sr_snapshot_admitted"] is True and sr_only["bridge_handoff_admitted"] is False
    assert bridge["sr_snapshot_admitted"] is True and bridge["bridge_handoff_admitted"] is True
    assert bridge["ps_tick_may_advance"] is True
    assert resumed["sr_input_buffer_discarded"] is True
    assert resumed["sr_snapshot_admitted"] is False
    with pytest.raises(TypeError, match="playing"):
        observe_worldbridge_sr_input_lifecycle(
            playing=1, paused=False, bridge_handoff_invoked=False
        )
    with pytest.raises(ValueError, match="lifecycle_action"):
        observe_worldbridge_sr_input_lifecycle(
            playing=True, paused=False, bridge_handoff_invoked=False, lifecycle_action="reset"
        )


def test_validator_rejects_queue_replay_pause_atomicity_and_readiness_overclaims() -> None:
    contract = build_worldbridge_input_pause_authority_contract()
    cases = {
        "shared_queue": ("ps_input", "shared_queue", True, "shared_queue_overclaim"),
        "event_log": ("ps_input", "shared_event_log", True, "shared_event_log_overclaim"),
        "input_routing": ("ps_input", "ps_received_sr_input", True, "ps_input_routing_overclaim"),
        "shared_order": ("admissions", "shared_queued_input_ordering", True, "shared_queued_input_ordering_overclaim"),
        "cross_lane_order": ("admissions", "cross_lane_input_ordering", True, "cross_lane_input_ordering_overclaim"),
        "replay": ("admissions", "input_replay_admitted", True, "input_replay_overclaim"),
        "checkpoint": ("admissions", "checkpoint_input_state", True, "checkpoint_input_state_overclaim"),
        "pause_reset": ("lifecycle", "shared_pause_reset_authority", True, "shared_pause_reset_authority_overclaim"),
        "atomicity": ("admissions", "atomicity_admitted", True, "atomicity_overclaim"),
        "default_ready": ("admissions", "default_ready", True, "default_ready_overclaim"),
    }
    for _name, (section, field, value, error) in cases.items():
        tampered = copy.deepcopy(contract)
        tampered[section][field] = value
        result = validate_worldbridge_input_pause_authority_contract(tampered)
        assert result["valid"] is False
        assert error in result["errors"]


def test_runtime_status_nests_input_pause_contract_without_default_wiring() -> None:
    contract = build_worldbridge_input_pause_authority_contract()
    status = build_runtime_worldbridge_status()
    assert status["runtime_mode"] == "dual"
    assert status["default_ready"] is False
    assert status["shared_queued_input_pause_reset_authority_contract"] == contract


def test_real_sources_keep_sr_snapshot_edge_semantics_and_pause_gate() -> None:
    input_tree = ast.parse(INPUT_STATE.read_text(encoding="utf-8"))
    snapshot = _method(input_tree, "SrInputState", "snapshot")
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        for node in ast.walk(snapshot)
    )
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Attribute) and target.attr == "_mouse_left_clicked" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and node.value.value is False
        for node in ast.walk(snapshot)
    )

    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    input_snapshot = _method(viewport, "GameViewport", "_sr_input_snapshot")
    conditions = [node for node in ast.walk(input_snapshot) if isinstance(node, ast.If)]
    assert any(
        isinstance(node.test, ast.BoolOp)
        and isinstance(node.test.op, ast.And)
        and any(isinstance(value, ast.Attribute) and value.attr == "is_playing" for value in node.test.values)
        and any(
            isinstance(value, ast.UnaryOp)
            and isinstance(value.op, ast.Not)
            and isinstance(value.operand, ast.Attribute)
            and value.operand.attr == "is_paused"
            for value in node.test.values
        )
        for node in conditions
    )
    assert any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "empty_snapshot"
        for node in ast.walk(input_snapshot)
    )


def test_real_sources_keep_input_before_script_then_opt_in_bridge_and_no_pond_input() -> None:
    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    prepare = _method(viewport, "GameViewport", "prepare_simulation_tick")
    snapshot_calls = _attribute_calls(prepare)
    assert "_sr_input_snapshot" in snapshot_calls
    assert any(
        isinstance(node, ast.Dict)
        and any(isinstance(key, ast.Constant) and key.value == "input_snap" for key in node.keys)
        for node in ast.walk(prepare)
    )

    driver = ast.parse(DRIVER.read_text(encoding="utf-8"))
    tick = _method(driver, "SimulationDriver", "tick")
    calls = _attribute_calls(tick)
    assert calls.index("prepare_simulation_tick") < calls.index("run_script_phase") < calls.index("run_snapshot_phase")

    snapshot_phase = _method(viewport, "GameViewport", "run_snapshot_phase")
    snapshot_calls = _attribute_calls(snapshot_phase)
    assert snapshot_calls.index("_run_unified_pond_bridge_tick") < snapshot_calls.index("_publish_sr_runtime_snapshots")
    assert snapshot_calls.index("capture_worldbridge_shared_state_envelope") < snapshot_calls.index(
        "consume_worldbridge_shared_state_envelope"
    )

    game_tree = ast.parse(GAME_TICK.read_text(encoding="utf-8"))
    game_tick = _function(game_tree, "step_game_runtime")
    game_calls = _attribute_calls(game_tick)
    assert game_calls.index("_sr_input_snapshot") < game_calls.index("_run_script_tick_batch")
    assert "_run_unified_pond_bridge_tick" not in game_calls

    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    entry = _function(bridge_tree, "unified_pond_step")
    assert "input" not in {argument.arg for argument in entry.args.args + entry.args.kwonlyargs}
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_unified_pond_step_impl"
        for node in ast.walk(entry)
    ), "unified_pond_step must delegate to _unified_pond_step_impl"
    step = _function(bridge_tree, "_unified_pond_step_impl")
    update_calls = [
        node for node in ast.walk(step)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_invoke_clocked_pond_update"
    ]
    assert len(update_calls) == 1
    assert len(update_calls[0].args) == 2
    assert all(isinstance(argument, ast.Name) for argument in update_calls[0].args)
    assert update_calls[0].keywords == []


def test_real_sources_clear_input_for_lifecycles_and_isolate_bridge_exception() -> None:
    viewport = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    for method_name in (
        "_start_simulation",
        "_pause_simulation",
        "_resume_simulation",
        "_stop_simulation",
        "_discard_scene_runtime_state",
    ):
        assert _contains_self_call(_method(viewport, "GameViewport", method_name), "_sr_input_clear"), method_name

    assert _contains_self_call(
        _method(viewport, "GameViewport", "_start_simulation"),
        "_reset_worldbridge_shared_state_transport",
    )
    assert _contains_self_call(
        _method(viewport, "GameViewport", "_stop_simulation"),
        "_reset_worldbridge_shared_state_transport",
    )
    assert _contains_self_call(
        _method(viewport, "GameViewport", "_discard_scene_runtime_state"),
        "_reset_worldbridge_shared_state_transport",
    )

    bridge_tick = _method(
        viewport,
        "GameViewport",
        "_run_unified_pond_bridge_tick_locked",
    )
    assert any(isinstance(node, ast.Try) for node in ast.walk(bridge_tick))
    assert any(
        isinstance(node, ast.ExceptHandler)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "debug"
            for call in ast.walk(node)
        )
        for node in ast.walk(bridge_tick)
    )
    bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    step = _function(bridge_tree, "_unified_pond_step_impl")
    assert not any(
        isinstance(node, ast.Name) and "queue" in node.id.lower()
        for node in ast.walk(step)
    )

