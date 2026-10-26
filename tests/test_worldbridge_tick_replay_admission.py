# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
VIEWPORT = RUNTIME / "core/VitaLoom/viewports/game_viewport.py"
BRIDGE = RUNTIME / "core/Lotucosm/runtime/world_bridge.py"
POND = RUNTIME / "core/Lotucosm/pond.py"


def _method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    return member
    raise AssertionError(f"Missing {class_name}.{method_name}")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Missing function {name}")


class WorldBridgeTickReplayAdmissionTests(unittest.TestCase):
    def test_inventory_retains_dual_non_admitted_contract(self) -> None:
        evidence = build_worldbridge_tick_replay_admission()
        self.assertTrue(evidence["read_only"])
        self.assertEqual(evidence["runtime_mode"], "dual")
        self.assertFalse(evidence["tick_merge_admitted"])
        self.assertFalse(evidence["full_unified_replay_admitted"])
        self.assertFalse(evidence["default_ready"])
        self.assertEqual(
            evidence["sr_lane"]["phase_order"],
            ["script", "spawn", "actuator", "fluid", "physics", "survival", "snapshot"],
        )
        self.assertFalse(evidence["ps_lane"]["clock"]["bridge_delta_consumed_by_pond"])
        self.assertFalse(evidence["persistence_and_replay"]["shared_checkpoint_contract"])
        self.assertIn("sr_ps_tick_merge", evidence["do_not_claim"])
        self.assertIn("full_unified_runtime_replay", evidence["do_not_claim"])

    def test_sr_bridge_handoff_runs_only_after_sr_snapshot_phase_work(self) -> None:
        snapshot = _method(ast.parse(VIEWPORT.read_text(encoding="utf-8")), "GameViewport", "run_snapshot_phase")
        calls = [
            node.func.attr
            for node in ast.walk(snapshot)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        self.assertIn("_refresh_sr_hud", calls)
        self.assertIn("_run_unified_pond_bridge_tick", calls)
        self.assertIn("_publish_sr_runtime_snapshots", calls)
        self.assertLess(calls.index("_refresh_sr_hud"), calls.index("_run_unified_pond_bridge_tick"))
        self.assertLess(calls.index("_run_unified_pond_bridge_tick"), calls.index("_publish_sr_runtime_snapshots"))

    def test_bridge_supplies_shared_delta_to_pond_update(self) -> None:
        bridge_tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
        entry = _function(bridge_tree, "unified_pond_step")
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_unified_pond_step_impl"
                for node in ast.walk(entry)
            ),
            "unified_pond_step must delegate to _unified_pond_step_impl",
        )
        bridge_step = _function(bridge_tree, "_unified_pond_step_impl")
        update_calls = [
            node for node in ast.walk(bridge_step)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_invoke_clocked_pond_update"
        ]
        self.assertEqual(len(update_calls), 1)
        self.assertEqual(len(update_calls[0].args), 2)
        self.assertIsInstance(update_calls[0].args[1], ast.Name)
        self.assertEqual(update_calls[0].keywords, [])

    def test_pond_owns_a_distinct_fixed_step_clock(self) -> None:
        update = _method(ast.parse(POND.read_text(encoding="utf-8")), "Pond", "update")
        increments_time = any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Attribute)
            and node.target.attr == "time"
            and isinstance(node.op, ast.Add)
            and isinstance(node.value, ast.Constant)
            and node.value.value == 1
            for node in ast.walk(update)
        )
        root_updates = [
            node for node in ast.walk(update)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "update"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == 1.0
        ]
        self.assertTrue(increments_time)
        self.assertEqual(len(root_updates), 0)
        self.assertTrue(any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Attribute)
            and node.target.attr == "simulation_time"
            for node in ast.walk(update)
        ))


if __name__ == "__main__":
    unittest.main()
