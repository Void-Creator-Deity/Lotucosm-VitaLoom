# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    compile_viewport_draw_commands,
)
from core.VitaLoom.viewports.viewport_snapshot import build_viewport_frame_snapshot


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge.py"
)


class WorldBridgeRenderIdentityAuthorityInventoryTests(unittest.TestCase):
    def _circle_for(self, entity: dict[str, object]) -> CircleCommand:
        frame = build_viewport_frame_snapshot([entity], width=160, height=90)
        commands = compile_viewport_draw_commands(frame)
        return next(command for command in commands if isinstance(command, CircleCommand))

    def test_legacy_entity_color_is_not_a_qt_free_viewport_visual_state_input(self) -> None:
        entity = {
            "id": "organism-1",
            "entity_type": "organism",
            "position": (10.0, 20.0),
            "radius": 4.0,
            "visible": True,
            "color": (1, 2, 3),
        }
        frame = build_viewport_frame_snapshot([entity], width=160, height=90)
        snapshot = frame.entities[0]

        self.assertEqual(snapshot.visual_state, {})
        self.assertNotEqual(self._circle_for(entity).fill[:3], (1, 2, 3))

    def test_qt_free_viewport_uses_explicit_visual_state_not_color(self) -> None:
        entity = {
            "id": "organism-2",
            "entity_type": "organism",
            "position": (10.0, 20.0),
            "radius": 4.0,
            "visible": True,
            "color": (1, 2, 3),
            "visual_state": {"fill": (9, 8, 7, 6)},
        }

        self.assertEqual(self._circle_for(entity).fill, (9, 8, 7, 6))

    def test_bridge_and_ledger_keep_render_identity_unmapped(self) -> None:
        audit = build_worldbridge_mapping_audit()
        self.assertEqual(audit["fields"]["render_identity"]["state"], "not_mapped")
        self.assertIn("render_identity", audit["known_losses"])

        tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
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
        self.assertTrue({"color", "visual_state", "sr_visual_state"}.isdisjoint(names))


if __name__ == "__main__":
    unittest.main()
