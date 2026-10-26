# -*- coding: utf-8 -*-
"""E237 evidence: no source-backed live SR/PS checkpoint, restore, or replay yet."""
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_checkpoint_restore_feasibility import (
    build_worldbridge_checkpoint_restore_feasibility_contract,
    validate_worldbridge_checkpoint_restore_feasibility_contract,
)
from core.Lotucosm.runtime.world_bridge_input_pause_authority import (
    build_worldbridge_input_pause_authority_contract,
)
from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    build_worldbridge_sr_runtime_randomness_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from core.Lotucosm.runtime.world_bridge_e317_live_checkpoint_gap_audit import (
    build_worldbridge_e317_live_checkpoint_gap_audit,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_checkpoint_restore_feasibility.py"
SR_SNAPSHOTS = RUNTIME / "core" / "VitaLoom" / "simulation" / "sr_runtime_snapshot_authority.py"
TRACE_PRODUCER = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_live_trace_producer.py"
POND_SERIALIZER = RUNTIME / "builtin" / "systems" / "pond_serializer.py"
POND = RUNTIME / "core" / "Lotucosm" / "pond.py"


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == name:
                    return member
    raise AssertionError(f"missing function {name}")


def _class_method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise AssertionError(f"missing method {class_name}.{method_name}")


def _has_self_attribute(node: ast.AST, name: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == name
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def test_contract_is_qt_free_and_rejects_checkpoint_restore_replay_overclaims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = build_worldbridge_checkpoint_restore_feasibility_contract()
    assert validate_worldbridge_checkpoint_restore_feasibility_contract(contract)["valid"] is True
    assert contract["decision"]["cross_lane_checkpoint_available"] is False
    assert contract["decision"]["cross_lane_restore_available"] is False
    assert contract["decision"]["replay_preconditions_satisfied"] is False
    assert contract["existing_lane_local_seams"]["ps_pond_serializer"]["restores_root_entity_registration"] is True
    assert all(value is False for value in contract["cross_lane_state_gaps"].values())
    assert all(value is False for value in contract["admissions"].values())

    for path, field in (
        ("decision", "cross_lane_checkpoint_available"),
        ("decision", "cross_lane_restore_available"),
        ("decision", "replay_preconditions_satisfied"),
        ("admissions", "checkpoint_restore"),
        ("admissions", "atomicity"),
        ("admissions", "rollback"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
        ("cross_lane_state_gaps", "sr_rng_state"),
    ):
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        assert validate_worldbridge_checkpoint_restore_feasibility_contract(tampered)["valid"] is False

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_checkpoint_restore", AUTHORITY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_checkpoint_restore_feasibility_contract()["contract_valid"] is True


def test_runtime_status_nests_feasibility_contract_without_enabling_unified_mode() -> None:
    contract = build_worldbridge_checkpoint_restore_feasibility_contract()
    status = build_runtime_worldbridge_status()

    assert status["cross_lane_checkpoint_restore_feasibility_contract"] == contract
    assert "cross_lane_checkpoint_restore_feasibility_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert status["e317_live_checkpoint_gap_audit"] == build_worldbridge_e317_live_checkpoint_gap_audit()
    assert status["e317_live_checkpoint_gap_audit"]["opt_in_live_adapter_admission"]["default_ready"] is False


def test_source_backed_seams_do_not_amount_to_a_cross_lane_restore_protocol() -> None:
    snapshots = ast.parse(SR_SNAPSHOTS.read_text(encoding="utf-8-sig"))
    assert not any(
        isinstance(node, ast.FunctionDef) and "restore" in node.name.lower()
        for node in ast.walk(snapshots)
    )

    trace_text = TRACE_PRODUCER.read_text(encoding="utf-8")
    assert '"atomic_checkpoint": False' in trace_text
    trace_tree = ast.parse(trace_text)
    assert not any(
        isinstance(node, ast.FunctionDef) and "restore" in node.name.lower()
        for node in ast.walk(trace_tree)
    )

    serializer = ast.parse(POND_SERIALIZER.read_text(encoding="utf-8"))
    serialize_pond = _class_method(serializer, "PondSerializer", "serialize_pond")
    assert any(
        isinstance(node, ast.Attribute)
        and node.attr == "time"
        and isinstance(node.value, ast.Name)
        and node.value.id == "pond"
        for node in ast.walk(serialize_pond)
    )
    deserialize_pond = _class_method(serializer, "PondSerializer", "deserialize_pond")
    assert any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "pond_class"
        for node in ast.walk(deserialize_pond)
    )

    pond = ast.parse(POND.read_text(encoding="utf-8"))
    update = _class_method(pond, "Pond", "update")
    calls = {
        ast.unparse(node.func)
        for node in ast.walk(update)
        if isinstance(node, ast.Call)
    }
    assert _has_self_attribute(update, "time") or "self.time += 1" in ast.unparse(update)
    for required in (
        "self.physics_engine.update",
        "self.floating_system.update",
        "self.assembly_system.update",
        "self.resource_manager.update",
    ):
        assert required in calls


def test_existing_input_and_randomness_authorities_still_block_replay_preconditions() -> None:
    randomness = build_worldbridge_sr_runtime_randomness_contract()
    assert randomness["sr_rng_state_checkpointed"] is False
    assert randomness["bridge_rng_state_checkpoint"] is False
    assert randomness["cross_lane_consumption_order_captured"] is False

    input_authority = build_worldbridge_input_pause_authority_contract()
    assert input_authority["admissions"]["checkpoint_input_state"] is False
    assert input_authority["admissions"]["input_replay_admitted"] is False
    assert input_authority["lifecycle"]["shared_pause_reset_authority"] is False
