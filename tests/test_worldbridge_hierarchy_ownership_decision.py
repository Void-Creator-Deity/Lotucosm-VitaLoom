# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import numpy as np

from builtin.entity_types.organism import Organism
from builtin.systems.pond_serializer import PondSerializer
from core.Lotucosm.entity import EntityBase
from core.Lotucosm.pond import Pond
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge.py"
)


class _UpdateProbe:
    def __init__(self) -> None:
        self.calls = 0

    def update(self, delta_time: float) -> None:
        self.calls += 1


class WorldBridgeHierarchyOwnershipDecisionTests(unittest.TestCase):
    def test_parent_child_relation_changes_world_position_and_recursive_update(self) -> None:
        parent = EntityBase("parent", position=(10.0, 20.0))
        child = EntityBase("child", position=(3.0, 4.0))
        probe = _UpdateProbe()
        child.add_script(probe)

        parent.add_child(child)
        parent.update(1.0)

        self.assertIs(child.parent, parent)
        self.assertEqual(parent.children, [child])
        np.testing.assert_allclose(child.world_position, (13.0, 24.0))
        self.assertEqual(probe.calls, 1)

    def test_pond_root_membership_and_snapshot_do_not_represent_the_child_graph(self) -> None:
        pond = Pond(initial_organisms=0, initial_components=0)
        parent = Organism("parent", (10.0, 20.0))
        child = Organism("child", (3.0, 4.0))
        self.assertTrue(pond.add_organism(parent))
        self.assertTrue(pond.add_organism(child))

        parent.add_child(child)
        self.assertEqual(pond.root_entities, [parent, child])

        snapshot = PondSerializer().serialize_pond(pond)
        records = {record["id"]: record for record in snapshot["organisms"]}
        self.assertEqual(set(records), {"parent", "child"})
        for record in records.values():
            self.assertNotIn("parent", record)
            self.assertNotIn("children", record)

        pond.update()
        self.assertEqual(parent.age, 4)
        self.assertEqual(child.age, 8)

    def test_ledger_and_bridge_retain_no_hierarchy_mapping_route(self) -> None:
        audit = build_worldbridge_mapping_audit()
        self.assertEqual(audit["fields"]["hierarchy"], {"state": "not_mapped", "direction": "none"})
        self.assertIn("hierarchy", audit["known_losses"])

        tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
        forbidden = {
            "parent", "children", "add_child", "remove_child", "world_position", "root_entities",
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


if __name__ == "__main__":
    unittest.main()

