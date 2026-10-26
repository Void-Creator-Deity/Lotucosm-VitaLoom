# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from PyQt6.QtWidgets import QApplication


class AssetRegistryProjectOpenAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_project_open_refreshes_project_local_registry_after_context_is_set(self) -> None:
        from core.VitaLoom.core.editor_context import get_editor_context
        from core.VitaLoom.kernel.event_bus import EventBus
        from core.VitaLoom.project.project_manager import ProjectManager

        context = get_editor_context()
        context._ensure_qobject_initialized()
        context.event_bus = EventBus()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "open-project"
            (project / "assets").mkdir(parents=True)
            (project / "scenes").mkdir()
            (project / "assets" / "hero.png").write_bytes(b"hero")
            (project / "project.json").write_text(
                json.dumps({"name": "open-project", "active_scene": "main.pond"}),
                encoding="utf-8",
            )
            (project / "scenes" / "main.pond").write_text("{}", encoding="utf-8")

            self.assertTrue(ProjectManager().open_project(str(project)))
            snapshot = getattr(context, "project_asset_registry_snapshot")
            self.assertEqual(snapshot["project_path"], str(project.resolve()))
            self.assertTrue((project / ".vitaloom" / "asset_registry.json").is_file())
            self.assertTrue(any(row["path"] == "assets/hero.png" for row in snapshot["asset_projection"]))


    def test_project_open_reports_incomplete_transaction_journal_without_mutating_it(self) -> None:
        from core.VitaLoom.core.editor_context import get_editor_context
        from core.VitaLoom.kernel.event_bus import EventBus
        from core.VitaLoom.project.project_manager import ProjectManager

        context = get_editor_context()
        context._ensure_qobject_initialized()
        context.event_bus = EventBus()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "open-recovery-project"
            (project / "assets").mkdir(parents=True)
            (project / "scenes").mkdir()
            (project / ".vitaloom" / "asset_transactions").mkdir(parents=True)
            (project / "assets" / "hero.png").write_bytes(b"hero")
            (project / "project.json").write_text(json.dumps({"name": "open", "active_scene": "main.pond"}), encoding="utf-8")
            (project / "scenes" / "main.pond").write_text("{}", encoding="utf-8")
            journal = project / ".vitaloom" / "asset_transactions" / "incomplete.json"
            journal.write_text(json.dumps({"schema_version": 1, "state": "prepared"}), encoding="utf-8")
            journal_before = journal.read_bytes()

            self.assertTrue(ProjectManager().open_project(str(project)))
            snapshot = getattr(context, "project_asset_registry_snapshot")
            recovery = snapshot["asset_transaction_recovery"]
            self.assertTrue(recovery["recovery_required"])
            self.assertIn(".vitaloom/asset_transactions/incomplete.json", recovery["pending_journals"])
            self.assertEqual(recovery["transactions"][0]["classification"], "malformed")
            self.assertEqual(journal.read_bytes(), journal_before)


if __name__ == "__main__":
    unittest.main()
