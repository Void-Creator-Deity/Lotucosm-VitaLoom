# -*- coding: utf-8 -*-
"""Suite Hub smoke tests for discovery, lock validation, and runtime launching."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class HubSmokeTests(unittest.TestCase):
    def test_default_application_root_is_repository_root(self) -> None:
        from hub.hub_launcher import _app_root
        from hub.hub_paths import application_root

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("VITALOOM_APP_ROOT", None)
            self.assertEqual(application_root(), ROOT)
            self.assertEqual(_app_root(), ROOT)

    def test_suite_root_resolution_accepts_runtime_and_framecore_paths(self) -> None:
        from FrameCore.suite_registry import framecore_root, resolve_application_root
        from core.VitaLoom.core.bundle_paths import resource_root

        runtime = resource_root()
        frame_root = ROOT / "FrameCore"
        self.assertEqual(resolve_application_root(ROOT), ROOT)
        self.assertEqual(resolve_application_root(frame_root), ROOT)
        self.assertEqual(resolve_application_root(runtime), ROOT)
        self.assertEqual(framecore_root(runtime), frame_root)

    def test_hub_chip_status_uses_canonical_admission_code(self) -> None:
        from hub.hub_window import _chip_status

        self.assertEqual(_chip_status("current", "锁定"), "ok")
        self.assertEqual(_chip_status("legacy", "已锁定"), "warning")
        self.assertEqual(_chip_status("unsupported_schema", "已锁定"), "danger")

    def test_display_path_hides_workspace_projects_prefix(self) -> None:
        from hub.hub_window import _display_path

        project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        self.assertEqual(_display_path(str(project), ROOT), str(Path("samples") / "pvaec-细胞演化"))

    def test_project_detail_shows_short_location_with_full_tooltip(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        entry = window._entries[0]
        window._update_detail(entry)
        expected = Path(entry.path).resolve().relative_to(ROOT.resolve())
        if expected.parts[:2] == ("workspace", "projects"):
            expected = Path(*expected.parts[2:])
        self.assertEqual(window._detail_location.text(), str(expected))
        self.assertEqual(window._detail_location.toolTip(), entry.path)
        window.close()
        app.processEvents()

    def test_project_row_exposes_keyboard_focus_state(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QFocusEvent
        from PyQt6.QtWidgets import QApplication
        from hub.hub_window import HubWindow, ProjectRowWidget

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        row = window.list_widget.itemWidget(window.list_widget.item(0))
        self.assertIsInstance(row, ProjectRowWidget)
        assert isinstance(row, ProjectRowWidget)
        self.assertFalse(row.property("focused"))
        row.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
        self.assertTrue(row.property("focused"))
        row.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
        self.assertFalse(row.property("focused"))
        window.close()
        app.processEvents()

    def test_suite_hub_does_not_import_product_runtime_core(self) -> None:
        hub_root = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "hub"
        offenders: list[str] = []
        for path in hub_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if "from core." in text or "import core." in text or "core.VitaLoom" in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_discover_sample_projects(self) -> None:
        from hub.project_list_model import discover_hub_projects

        entries = discover_hub_projects(ROOT)
        names = {entry.name for entry in entries}
        self.assertTrue(names)
        self.assertTrue(any(entry.product_id == "lotucosm-vitaloom" for entry in entries))

    def test_hub_window_construct(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        self.assertGreaterEqual(window.list_widget.count(), 1)
        window.close()
        app.processEvents()

    def test_hub_blocks_project_with_incomplete_lock(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "missing-cap",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {"vitalloom.engine.sr2d": ">=1.0.0"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "project.lock.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "resolved_suite": {
                            "id": "lotucosm.vitaloom.suite",
                            "version": "1.0.0",
                        },
                        "resolved_product": {
                            "id": "lotucosm-vitaloom",
                            "version": "1.0.0",
                        },
                        "resolved_capabilities": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            window = HubWindow(ROOT)
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok) as warning:
                window._open_project(str(project))
            self.assertTrue(warning.called)
            window.close()
            app.processEvents()

    def test_hub_blocks_project_with_unsatisfied_capability_constraint(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "future-cap",
                        "loom_editor_version": "1.0.0",
                        "required_capabilities": {"vitalloom.engine.sr2d": ">=9.0.0"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            window = HubWindow(ROOT)
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok) as warning:
                window._open_project(str(project))
            self.assertTrue(warning.called)
            window.close()
            app.processEvents()

    def test_hub_blocks_project_with_invalid_lock_instead_of_failing_open(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project.json").write_text(
                json.dumps({"name": "invalid-lock", "loom_editor_version": "1.0.0"}),
                encoding="utf-8",
            )
            (project / "project.lock.json").write_text("{broken", encoding="utf-8")
            window = HubWindow(ROOT)
            with patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok) as warning:
                self.assertFalse(window._check_runtime_ready(str(project)))
            self.assertTrue(warning.called)
            window.close()
            app.processEvents()

    def test_start_editor_subprocess_uses_product_runtime_entrypoint(self) -> None:
        from hub.hub_launcher import editor_subprocess_command

        program, args, version = editor_subprocess_command(str(ROOT))
        self.assertTrue(program)
        self.assertIn(str(version.runtime_root / "main.py"), args[0])
        self.assertIn("--editor", args)

    def test_editor_failure_output_preserves_the_real_error_tail(self) -> None:
        from hub.hub_launcher import decode_process_output, failure_output_excerpt

        raw = (
            "startup line\r\n"
            "Traceback (most recent call last):\r\n"
            "RuntimeError: EditorContext runtime capability registry is already bound\r\n"
        ).encode("utf-8")
        output = decode_process_output(raw)
        self.assertIn("already bound", output)
        excerpt = failure_output_excerpt(output, limit=60)
        self.assertIn("already bound", excerpt)
        self.assertLessEqual(len(excerpt), 90)

    def test_editor_launch_log_is_written_to_state_logs(self) -> None:
        from hub import hub_launcher

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(hub_launcher, "_app_root", return_value=Path(tmp)):
                path = hub_launcher.write_editor_launch_log(
                    project_path=str(Path(tmp) / "demo"),
                    exit_code=1,
                    output="Traceback\nRuntimeError: failed",
                )
                self.assertEqual(
                    path,
                    Path(tmp) / "workspace" / "state" / "logs" / "editor-launch.log",
                )
                text = path.read_text(encoding="utf-8")
        self.assertIn("exit_code=1", text)
        self.assertIn("RuntimeError: failed", text)

    def test_refresh_preserves_active_search_filter(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
        from hub.hub_window import HubWindow
        from hub.project_list_model import filter_entries

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        window.search_edit.setText("pvaec")
        window.refresh_projects()
        expected = filter_entries(window._entries, "pvaec")
        self.assertGreater(len(expected), 0)
        self.assertEqual(window.list_widget.count(), len(expected))
        self.assertEqual(
            [window.list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(window.list_widget.count())],
            [entry.path for entry in expected],
        )
        window.close()
        app.processEvents()

    def test_empty_search_result_disables_project_actions(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        window.search_edit.setText("__no_project_can_match_this__")
        self.assertFalse(window._open_btn.isEnabled())
        self.assertFalse(window._reveal_btn.isEnabled())
        self.assertIsNone(window._selected_entry())
        window.close()
        app.processEvents()

    def test_editor_failure_dialog_shows_stderr_and_log_path(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from hub.hub_window import HubWindow

        app = QApplication.instance() or QApplication([])
        window = HubWindow(ROOT)
        window._editor_output = bytearray(
            "Traceback (most recent call last):\nRuntimeError: startup broke\n".encode("utf-8")
        )
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "editor-launch.log"
            with patch("hub.hub_window.write_editor_launch_log", return_value=log_path):
                with patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok) as warning:
                    window._on_editor_process_finished(1, None)
            self.assertTrue(warning.called)
            message = warning.call_args.args[2]
            self.assertIn("RuntimeError: startup broke", message)
            self.assertIn(str(log_path), message)
        window.close()
        app.processEvents()

    def test_editor_subprocess_env_can_import_framecore_and_runtime(self) -> None:
        from FrameCore.product_registry import load_product_registry
        from FrameCore.suite_registry import load_default_suite_manifest
        from hub.hub_launcher import _editor_env

        suite = load_default_suite_manifest(ROOT)
        version = load_product_registry(suite.suite_root).get_default_version(
            "lotucosm-vitaloom"
        )
        self.assertIsNotNone(version)
        env = _editor_env(version)
        paths = env.value("PYTHONPATH").split(os.pathsep)
        self.assertIn(str(ROOT), paths)
        self.assertIn(str(version.runtime_root), paths)


if __name__ == "__main__":
    unittest.main()
