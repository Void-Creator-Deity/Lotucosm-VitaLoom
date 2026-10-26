# -*- coding: utf-8 -*-
"""AI command undo/audit status must be explicit, not implied by metadata."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AiCommandAuditStatusToolTests(unittest.TestCase):
    def test_tool_reports_durable_audit_and_command_facing_undo_path(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "check_ai_command_audit_status.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)

        self.assertEqual(data["schema_version"], 4)
        self.assertEqual(data["status"], "durable_audit_with_representative_undo")
        self.assertTrue(data["command_stack"]["exists"])
        self.assertFalse(data["command_stack"]["registry_integrated"])
        self.assertTrue(data["command_registry_undo_bridge"])
        self.assertTrue(data["command_undo_redo_path"])
        self.assertTrue(data["ui_undo_redo_action_binding"])
        self.assertTrue(data["ui_menu_toolbar_undo_redo_binding"])
        self.assertTrue(data["standard_ui_semantic_history_dispatch"])
        self.assertTrue(data["inspector_semantic_property_route"])
        self.assertTrue(data["inspector_transient_property_route"])
        self.assertTrue(data["memory_editor_registry_route"])
        self.assertTrue(data["inspector_local_command_stack_retired"])
        self.assertTrue(data["viewport_single_node_drag_semantic_route"])
        self.assertTrue(data["viewport_multi_node_drag_semantic_route"])
        self.assertTrue(data["viewport_connection_semantic_route"])
        self.assertTrue(data["viewport_event_node_semantic_route"])
        self.assertTrue(data["viewport_keyboard_semantic_history"])
        self.assertTrue(data["viewport_local_command_stack_retired"])
        self.assertTrue(data["ui_history_scene_refresh"])
        self.assertTrue(data["representative_undo_redo_runtime"])
        self.assertTrue(data["representative_durable_project_undo"])
        self.assertTrue(data["representative_durable_project_redo"])
        self.assertFalse(data["unified_undo_redo_runtime"])
        self.assertTrue(data["durable_audit_history"])

        by_id = {row["id"]: row for row in data["commands"]}
        for command_id in (
            "entity.create",
            "entity.delete",
            "prefab.place",
            "entity.set_property",
            "transform.set",
            "transform.batch_set",
            "connection.create",
            "connection.delete",
            "connection.set_weight",
            "script.set_property",
        ):
            row = by_id[command_id]
            self.assertTrue(row["mutates"])
            self.assertTrue(row["undoable_metadata"])
            self.assertEqual(row["audit_history"], "durable")
            self.assertEqual(row["undo_redo"], "command_path")
            self.assertTrue(row["durable_project_undo"])
            self.assertTrue(row["durable_project_redo"])


if __name__ == "__main__":
    unittest.main()
