# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import os
import unittest
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from core.Lotucosm.entity import EntityBase
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge.py"
)
VIEWPORT = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/VitaLoom/viewports/game_viewport.py"
)


class _ScriptProbe:
    def __init__(self) -> None:
        self.attached = 0
        self.updated = 0

    def on_attach(self, entity: EntityBase) -> None:
        self.attached += 1

    def update(self, delta_time: float) -> None:
        self.updated += 1


class _LifecycleProbe:
    """Script probe recording attach/detach calls for rollback assertions."""

    def __init__(self, name: str = "probe", fail_on_attach: bool = False) -> None:
        self.name = name
        self.fail_on_attach = fail_on_attach
        self.attached = 0
        self.detached = 0

    def on_attach(self, entity: object) -> None:
        self.attached += 1
        if self.fail_on_attach:
            raise RuntimeError(f"injected attach failure: {self.name}")

    def on_detach(self, entity: object) -> None:
        self.detached += 1


class ScriptReplacementRollbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def _assert_atomic_replace(self, entity) -> None:
        old_a = _LifecycleProbe("old-a")
        old_b = _LifecycleProbe("old-b")
        entity.replace_scripts([old_a, old_b])
        self.assertEqual(entity.scripts, [old_a, old_b])

        new_ok = _LifecycleProbe("new-ok")
        new_bad = _LifecycleProbe("new-bad", fail_on_attach=True)
        with self.assertRaises(RuntimeError):
            entity.replace_scripts([new_ok, new_bad])

        # Old owner set is untouched by a failed replacement.
        self.assertEqual(entity.scripts, [old_a, old_b])
        self.assertEqual((old_a.detached, old_b.detached), (0, 0))
        # Newly attached scripts are detached in reverse order.
        self.assertEqual(new_ok.detached, 1)
        self.assertEqual(new_bad.detached, 0)

        # A successful replacement attaches new scripts and detaches old ones.
        replacement = _LifecycleProbe("replacement")
        entity.replace_scripts([replacement])
        self.assertEqual(entity.scripts, [replacement])
        self.assertEqual(replacement.attached, 1)
        self.assertEqual((old_a.detached, old_b.detached), (1, 1))

    def test_ps_entity_replace_scripts_is_atomic_on_attach_failure(self) -> None:
        self._assert_atomic_replace(EntityBase("ps-script-rollback"))

    def test_sr_runtime_entity_replace_scripts_is_atomic_on_attach_failure(self) -> None:
        entity = GameViewport._SceneRuntimeEntity(
            "sr-script-rollback", "organism", (1.0, 2.0), 8.0
        )
        self._assert_atomic_replace(entity)


class WorldBridgeScriptBindingOwnershipDecisionTests(unittest.TestCase):
    def test_entity_scripts_are_live_lifecycle_objects_not_inert_data(self) -> None:
        entity = EntityBase("script-owner")
        script = _ScriptProbe()

        entity.add_script(script)
        entity.update(1.0)

        self.assertEqual(script.attached, 1)
        self.assertEqual(script.updated, 1)

    def test_ledger_keeps_executable_scripts_unmapped(self) -> None:
        audit = build_worldbridge_mapping_audit()
        self.assertEqual(audit["fields"]["scripts"]["state"], "not_mapped")
        self.assertIn("scripts", audit["known_losses"])
        self.assertFalse(audit["component_projection"]["maps_live_components"])

    def test_bridge_has_no_script_or_component_execution_route(self) -> None:
        tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
        forbidden = {
            "scripts", "add_script", "components", "add_component",
            "sense", "process_signal", "auto_ingest", "get_force_vector",
        }
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"getattr", "hasattr", "setattr"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                names.add(node.args[1].value)
        self.assertTrue(forbidden.isdisjoint(names))

    def test_dynamic_script_module_identity_does_not_use_process_hash(self) -> None:
        source = VIEWPORT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hash"
        ]
        self.assertFalse(calls)
        self.assertIn("hashlib.sha256", source)
        self.assertIn("canonical_script_path", source)
        self.assertIn("vitaloom_user_script_{script_identity}", source)


if __name__ == "__main__":
    unittest.main()
