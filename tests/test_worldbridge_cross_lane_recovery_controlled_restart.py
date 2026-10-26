# -*- coding: utf-8 -*-
"""E238 evidence: quarantine failed live handoffs; fresh host starts are not restore."""
from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR
from core.Lotucosm.runtime.world_bridge_recovery_authority import (
    build_worldbridge_recovery_compensation_controlled_restart_contract,
    classify_worldbridge_handoff_failure_containment,
    validate_worldbridge_recovery_compensation_controlled_restart_contract,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from core.VitaLoom.viewports.game_viewport import GameViewport


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
AUTHORITY = RUNTIME / "core" / "Lotucosm" / "runtime" / "world_bridge_recovery_authority.py"
VIEWPORT = RUNTIME / "core" / "VitaLoom" / "viewports" / "game_viewport.py"


def _viewport() -> GameViewport:
    assert APP is not None
    return GameViewport()


def _function_or_method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise AssertionError(f"missing {class_name}.{method_name}")


def _receipt(*, phase: str = "pond_update", partial_mutation_possible: bool = True) -> dict[str, object]:
    return {
        "phase": phase,
        "failure_isolated": True,
        "rollback_performed": False,
        "cross_lane_transaction": False,
        "atomic_checkpoint": False,
        "partial_mutation_possible": partial_mutation_possible,
    }


def _entity() -> SimpleNamespace:
    entity = SimpleNamespace(
        id="sr:recovery",
        entity_type="organism",
        position=[1.0, 2.0],
        velocity=[0.0, 0.0],
        acceleration=[0.0, 0.0],
        radius=4.0,
        size=8.0,
        energy=30.0,
        health=20.0,
        generation=1,
        sr_debug_hud={},
    )
    setattr(entity, BRIDGE_ORGANISM_ATTR, "ps:recovery")
    return entity


def _organism() -> SimpleNamespace:
    return SimpleNamespace(
        id="ps:recovery",
        position=[1.0, 2.0],
        velocity=[0.0, 0.0],
        acceleration=[0.0, 0.0],
        radius=4.0,
        size=8.0,
        energy=30.0,
        health=20.0,
        generation=1,
        developmental_stage=0,
    )


def test_contract_is_qt_free_and_rejects_recovery_overclaims(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = build_worldbridge_recovery_compensation_controlled_restart_contract()
    assert validate_worldbridge_recovery_compensation_controlled_restart_contract(contract)["valid"] is True
    assert contract["failure_response"]["automatic_restart"] is False
    assert contract["failure_response"]["automatic_retry"] is False
    assert contract["fresh_restart_boundary"]["discard_current_sr_runtime_instance"] is True
    assert contract["fresh_restart_boundary"]["discard_current_ps_pond_instance"] is True

    for path, field in (
        ("compensation", "cross_lane_rollback"),
        ("compensation", "inverse_mutation_compensation"),
        ("compensation", "in_place_sr_ps_restore"),
        ("compensation", "atomic_recovery"),
        ("admissions", "cross_lane_rollback"),
        ("admissions", "in_place_restore"),
        ("admissions", "replay_admitted"),
        ("admissions", "default_ready"),
    ):
        tampered = copy.deepcopy(contract)
        tampered[path][field] = True
        assert validate_worldbridge_recovery_compensation_controlled_restart_contract(tampered)["valid"] is False

    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_worldbridge_recovery_authority", AUTHORITY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_worldbridge_recovery_compensation_controlled_restart_contract()["contract_valid"] is True


def test_classifier_requires_non_transaction_failure_receipt_and_only_recommends_quarantine() -> None:
    decision = classify_worldbridge_handoff_failure_containment(_receipt())
    assert decision["host_action"] == "suspend_future_opt_in_handoffs_for_current_runtime"
    assert decision["sr_host_tick_may_continue"] is True
    assert decision["compensation_performed"] is False
    assert decision["controlled_fresh_restart"]["restores_failed_runtime_state"] is False
    assert decision["controlled_fresh_restart"]["replays_failed_handoff"] is False

    for field, invalid in (
        ("rollback_performed", True),
        ("cross_lane_transaction", True),
        ("atomic_checkpoint", True),
        ("failure_isolated", False),
    ):
        receipt = _receipt()
        receipt[field] = invalid
        with pytest.raises(ValueError):
            classify_worldbridge_handoff_failure_containment(receipt)


def test_viewport_quarantines_after_labelled_failure_and_does_not_retry_same_pond() -> None:
    class FailingPond:
        def __init__(self) -> None:
            self.organisms = {"ps:recovery": _organism()}
            self.update_calls = 0

        def update(self) -> None:
            self.update_calls += 1
            self.organisms["ps:recovery"].energy -= 1.0
            raise RuntimeError("planned partial Pond mutation")

    viewport = _viewport()
    viewport._unified_pond_mode = True
    viewport._worldbridge_handoff_suspended = False
    viewport.scene_runtime_entities = [_entity()]
    pond = FailingPond()
    viewport._ensure_unified_pond = lambda: pond

    assert viewport._run_unified_pond_bridge_tick(0.05) is None
    assert pond.update_calls == 1
    assert viewport._worldbridge_handoff_suspended is True
    assert viewport._worldbridge_last_handoff_failure["phase"] == "pond_update"
    decision = viewport._worldbridge_last_recovery_decision
    assert decision["host_action"] == "suspend_future_opt_in_handoffs_for_current_runtime"
    assert decision["compensation_performed"] is False

    assert viewport._run_unified_pond_bridge_tick(0.05) is None
    assert pond.update_calls == 1


def test_discard_lifecycle_releases_quarantine_only_after_dropping_current_pond() -> None:
    viewport = _viewport()
    old_pond = object()
    viewport._unified_pond = old_pond
    viewport._worldbridge_handoff_suspended = True
    viewport._discard_scene_runtime_state()

    assert viewport._unified_pond is None
    assert viewport._worldbridge_handoff_suspended is False
    assert viewport._worldbridge_last_handoff_failure is None


def test_runtime_status_and_viewport_source_preserve_quarantine_not_restore_boundary() -> None:
    contract = build_worldbridge_recovery_compensation_controlled_restart_contract()
    status = build_runtime_worldbridge_status()
    assert status["cross_lane_recovery_compensation_controlled_restart_contract"] == contract
    assert "cross_lane_recovery_compensation_controlled_restart_module" in status["pilot_modules"]
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False

    tree = ast.parse(VIEWPORT.read_text(encoding="utf-8"))
    bridge_tick = "\n".join(
        ast.unparse(
            _function_or_method(tree, "GameViewport", method_name)
        )
        for method_name in (
            "_run_unified_pond_bridge_tick",
            "_run_unified_pond_bridge_tick_locked",
        )
    )
    assert "_worldbridge_handoff_suspended" in bridge_tick
    assert "classify_worldbridge_handoff_failure(receipt)" in bridge_tick
    assert "classify_worldbridge_verified_transaction_failure" not in bridge_tick
    assert "classify_worldbridge_handoff_failure_containment" not in bridge_tick
    assert bridge_tick.index("_worldbridge_handoff_suspended") < bridge_tick.index("_ensure_unified_pond")
    assert "rollback" not in bridge_tick.lower()

    for method_name in ("_discard_scene_runtime_state", "_stop_simulation"):
        source = ast.unparse(_function_or_method(tree, "GameViewport", method_name))
        assert "self._unified_pond = None" in source
        assert "self._worldbridge_handoff_suspended = False" in source
