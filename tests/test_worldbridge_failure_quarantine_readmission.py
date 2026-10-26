# -*- coding: utf-8 -*-
"""E239 evidence: quarantine guards every known opt-in WorldBridge writer."""
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
    OPT_IN_BRIDGE_ENTRY_POINTS,
    build_worldbridge_failure_quarantine_readmission_contract,
    classify_worldbridge_opt_in_bridge_admission,
    validate_worldbridge_failure_quarantine_readmission_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from core.VitaLoom.viewports.game_viewport import GameViewport


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_quarantine_readmission_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise AssertionError(f"missing {class_name}.{method_name}")


def _viewport() -> GameViewport:
    assert APP is not None
    return GameViewport()


def test_authority_is_qt_free_and_rejects_same_runtime_retry_or_recovery_overclaims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = build_worldbridge_failure_quarantine_readmission_contract()
    assert validate_worldbridge_failure_quarantine_readmission_contract(contract)["valid"] is True
    assert contract["guarded_entry_points"] == sorted(OPT_IN_BRIDGE_ENTRY_POINTS)
    assert contract["quarantine"]["same_runtime_re_admission"] is False
    assert contract["fresh_instance_re_admission_boundary"]["reuses_partially_mutated_pond"] is False

    for path, field in (
        ("quarantine", "same_runtime_re_admission"),
        ("quarantine", "automatic_re_admission"),
        ("fresh_instance_re_admission_boundary", "reuses_partially_mutated_pond"),
        ("fresh_instance_re_admission_boundary", "restores_failed_runtime_state"),
        ("fresh_instance_re_admission_boundary", "replays_failed_handoff"),
        ("admissions", "same_runtime_safe_retry"),
        ("admissions", "automatic_quarantine_clear"),
        ("admissions", "cross_lane_rollback"),
        ("admissions", "in_place_restore"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
    ):
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        assert validate_worldbridge_failure_quarantine_readmission_contract(tampered)["valid"] is False

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_e239_authority", AUTHORITY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_failure_quarantine_readmission_contract()["contract_valid"] is True


def test_classification_denies_all_known_writers_before_pond_construction_when_quarantined() -> None:
    for entry in sorted(OPT_IN_BRIDGE_ENTRY_POINTS):
        decision = classify_worldbridge_opt_in_bridge_admission(
            entry,
            unified_pond_mode=True,
            handoff_suspended=True,
            current_pond_present=True,
        )
        assert decision["admitted"] is False
        assert decision["may_construct_or_reuse_pond"] is False
        assert decision["may_call_sr_ps_bridge_mutator"] is False
        assert decision["requires_fresh_runtime_lifecycle_before_re_admission"] is True
        assert decision["restores_failed_runtime_state"] is False
        assert decision["replays_failed_handoff"] is False

    fresh = classify_worldbridge_opt_in_bridge_admission(
        "tick_handoff",
        unified_pond_mode=True,
        handoff_suspended=False,
        current_pond_present=False,
    )
    assert fresh["admitted"] is True
    assert fresh["host_action"] == "admit_opt_in_bridge_writer_for_current_unquarantined_runtime"

    with pytest.raises(ValueError):
        classify_worldbridge_opt_in_bridge_admission(
            "unknown_writer",
            unified_pond_mode=True,
            handoff_suspended=False,
            current_pond_present=False,
        )


def test_scene_prebridge_does_not_construct_or_reuse_pond_while_current_runtime_is_quarantined() -> None:
    viewport = _viewport()
    viewport._unified_pond_mode = True
    viewport._worldbridge_handoff_suspended = True
    viewport._unified_pond = object()
    viewport.scene_runtime_entities = []

    def forbidden_pond() -> object:
        raise AssertionError("quarantined scene prebridge tried to construct or reuse Pond")

    viewport._ensure_unified_pond = forbidden_pond
    viewport._ensure_unified_bridge_for_scene()

    decision = viewport._worldbridge_last_quarantine_admission
    assert decision is not None
    assert decision["entry_point"] == "scene_prebridge"
    assert decision["admitted"] is False
    assert decision["may_construct_or_reuse_pond"] is False


def test_fresh_discard_keeps_historical_receipt_but_only_re_admits_new_runtime_instances() -> None:
    viewport = _viewport()
    prior_receipt = {"phase": "pond_update", "partial_mutation_possible": True}
    old_pond = object()
    viewport._unified_pond = old_pond
    viewport._worldbridge_handoff_suspended = True
    viewport._worldbridge_last_handoff_failure = prior_receipt
    viewport._discard_scene_runtime_state()

    assert viewport._unified_pond is None
    assert viewport._worldbridge_handoff_suspended is False
    assert viewport._worldbridge_last_handoff_failure == prior_receipt

    # A normal fresh lifecycle may opt in again; this is not reuse of old Pond.
    viewport._unified_pond_mode = True
    decision = viewport._worldbridge_opt_in_bridge_entry_admitted("tick_handoff")
    assert decision is True
    assert viewport._worldbridge_last_quarantine_admission["current_pond_present"] is False
    assert viewport._worldbridge_last_quarantine_admission["restores_failed_runtime_state"] is False


def test_viewport_source_guards_every_known_writer_and_status_preserves_dual_defaults() -> None:
    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    checks = (
        ("_ensure_unified_bridge_for_scene", "scene_prebridge", "ensure_bridged_organisms"),
        ("_process_organism_with_membrane_spawn", "spawn_bridge", "bridge_spawned_organism"),
        ("_run_unified_pond_bridge_tick", "tick_handoff", "_ensure_unified_pond"),
    )
    for method_name, entry_name, mutator in checks:
        source = ast.unparse(_method(tree, "GameViewport", method_name))
        if method_name == "_run_unified_pond_bridge_tick":
            source += "\n" + ast.unparse(
                _method(
                    tree,
                    "GameViewport",
                    "_run_unified_pond_bridge_tick_locked",
                )
            )
        assert entry_name in source
        assert source.index(entry_name) < source.index(mutator)

    for method_name in ("_discard_scene_runtime_state", "_stop_simulation"):
        source = ast.unparse(_method(tree, "GameViewport", method_name))
        assert source.index("self._unified_pond = None") < source.index("self._worldbridge_handoff_suspended = False")

    status = build_runtime_worldbridge_status()
    contract = build_worldbridge_failure_quarantine_readmission_contract()
    assert status["failure_quarantine_opt_in_handoff_readmission_contract"] == contract
    assert "failure_quarantine_opt_in_handoff_readmission_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
