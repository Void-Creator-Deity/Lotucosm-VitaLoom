# -*- coding: utf-8 -*-
"""MCP adapter remains a thin wrapper over the command registry."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.VitaLoom.commands import mcp_adapter


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


class McpCommandAdapterTests(unittest.TestCase):
    def test_list_and_describe_commands(self) -> None:
        commands = mcp_adapter.list_commands()["commands"]
        ids = {row["id"] for row in commands}
        self.assertIn("project.state", ids)
        self.assertIn("project.create", ids)
        self.assertIn("entity.set_property", ids)
        self.assertIn("transform.set", ids)
        self.assertIn("script.set_property", ids)
        self.assertIn("asset.apply_to_scene", ids)
        self.assertIn("asset.scan", ids)
        self.assertIn("asset.export_closure", ids)
        self.assertIn("asset.rename", ids)
        self.assertIn("asset.delete", ids)
        self.assertIn("asset.retirement.analyze", ids)
        self.assertIn("asset.transaction.undo", ids)
        self.assertIn("asset.transaction.redo", ids)
        self.assertIn("asset.transaction.inspect", ids)
        self.assertIn("asset.transaction.recovery.list", ids)
        self.assertIn("asset.transaction.recovery.resolve", ids)
        self.assertIn("asset.transaction.prune.plan", ids)
        self.assertIn("asset.transaction.prune.apply", ids)
        self.assertIn("plugin.list", ids)
        self.assertIn("plugin.enable", ids)
        self.assertIn("export.player.prepare", ids)
        self.assertIn("runtime.replay.status", ids)
        self.assertIn("runtime.worldbridge.status", ids)
        self.assertIn("runtime.worldbridge.mapping_audit", ids)
        self.assertIn("runtime.worldbridge.component_decision", ids)
        self.assertIn("runtime.worldbridge.component_projection", ids)
        self.assertIn("runtime.worldbridge.component_projection_diagnostics", ids)
        self.assertEqual(
            mcp_adapter.describe_command("project.state")["id"],
            "project.state",
        )
        retirement = mcp_adapter.describe_command("asset.retirement.analyze")
        self.assertFalse(retirement["mutates"])
        self.assertEqual(retirement["input_schema"]["required"], ["project_path", "source_path"])

    def test_runtime_replay_status_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.replay.status", {})
        helper = mcp_adapter.get_runtime_replay_status()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["unified_pond_enabled"])

    def test_runtime_worldbridge_status_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.worldbridge.status", {})
        helper = mcp_adapter.get_runtime_worldbridge_status()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["default_ready"])

    def test_runtime_worldbridge_mapping_audit_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.worldbridge.mapping_audit", {})
        helper = mcp_adapter.get_runtime_worldbridge_mapping_audit()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["lossless"])

    def test_runtime_worldbridge_component_decision_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.worldbridge.component_decision", {})
        helper = mcp_adapter.get_runtime_worldbridge_component_decision()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["maps_live_components"])

    def test_runtime_worldbridge_component_projection_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.worldbridge.component_projection", {})
        helper = mcp_adapter.get_runtime_worldbridge_component_projection()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["maps_live_components"])

    def test_runtime_worldbridge_component_projection_diagnostics_helper_uses_registry_command(self) -> None:
        direct = mcp_adapter.run_command("runtime.worldbridge.component_projection_diagnostics", {})
        helper = mcp_adapter.get_runtime_worldbridge_component_projection_diagnostics()

        self.assertEqual(self._normalize_replay_status(helper), self._normalize_replay_status(direct))
        self.assertTrue(helper["result"]["read_only"])
        self.assertFalse(helper["result"]["maps_live_components"])

    def test_get_project_state_uses_command_shape(self) -> None:
        project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        result = mcp_adapter.get_project_state(str(project))
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["name"], "PVAEC · 细胞演化")

    def test_project_open_reports_missing_gui_host_with_preparation_evidence(self) -> None:
        project = Path(tempfile.mkdtemp(prefix="mcp_project_open_", dir=str(WORKSPACE)))
        try:
            (project / "scenes").mkdir()
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "MCP Project Open",
                        "active_scene": "main.pond",
                        "manifest_validation_mode": "warn",
                    }
                ),
                encoding="utf-8",
            )
            (project / "scenes" / "main.pond").write_text(
                json.dumps({"name": "main", "entities": [], "connections": []}),
                encoding="utf-8",
            )

            result = mcp_adapter.run_command(
                "project.open", {"project_path": str(project)}
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "project_host_adapter_unavailable")
            preparation = result["error"]["details"]["preparation"]
            self.assertEqual(preparation["status"], "ready")
            self.assertEqual(preparation["project_path"], str(project.resolve()))
            self.assertTrue(preparation["report_id"])
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_run_command_rejects_outside_workspace(self) -> None:
        result = mcp_adapter.run_command("project.state", {"project_path": str(ROOT.parent)})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "path_outside_workspace")

    def test_get_scene_snapshot_and_validate_share_command_shape(self) -> None:
        scene = (
            ROOT
            / "workspace"
            / "projects"
            / "samples"
            / "织机教程-迷你Roguelike"
            / "scenes"
            / "dungeon_01.pond"
        )
        snapshot = mcp_adapter.get_scene_snapshot(scene_path=str(scene))
        self.assertTrue(snapshot["ok"])
        validation = mcp_adapter.run_command("scene.validate", {"scene_path": str(scene)})
        self.assertTrue(validation["ok"])
        self.assertIn("dependency_edges", validation["result"])

    def test_asset_export_closure_uses_registry(self) -> None:
        samples = ROOT / "workspace" / "projects" / "samples"
        project = next(path for path in samples.iterdir() if "Roguelike" in path.name)
        closure = mcp_adapter.run_command("asset.export_closure", {"project_path": str(project)})
        self.assertTrue(closure["ok"], closure)
        self.assertGreater(closure["result"]["file_count"], 0)
        self.assertIn("enabled_plugins", closure["result"])

    def test_create_entity_matches_cli_scene_edit_output(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="mcp_cli_scene_edit_", dir=str(WORKSPACE)))
        try:
            cli_scene = self._make_scene_project(root / "cli_project")
            mcp_scene = self._make_scene_project(root / "mcp_project")
            entity = {
                "id": "mcp_cli_crate",
                "name": "MCP CLI Crate",
                "type": "game_prop",
                "position": [12.0, 34.0],
                "radius": 7.0,
                "scripts": [],
                "sr_visual": {"sprite": "crate"},
            }

            cli_proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "main.py",
                    "command",
                    "run",
                    "entity.create",
                    "--json",
                    json.dumps(
                        {"scene_path": str(cli_scene), "entity": entity},
                        ensure_ascii=False,
                    ),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            self.assertEqual(cli_proc.returncode, 0, cli_proc.stdout + cli_proc.stderr)
            cli_result = json.loads(cli_proc.stdout)

            mcp_result = mcp_adapter.create_entity(str(mcp_scene), entity)

            self.assertEqual(
                self._normalize_command_result(cli_result),
                self._normalize_command_result(mcp_result),
            )
            self.assertEqual(
                self._normalize_scene_data(cli_scene),
                self._normalize_scene_data(mcp_scene),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_set_transform_matches_cli_scene_edit_output(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="mcp_cli_transform_", dir=str(WORKSPACE)))
        try:
            cli_scene = self._make_scene_project(root / "cli_project")
            mcp_scene = self._make_scene_project(root / "mcp_project")
            self._write_transform_fixture(cli_scene)
            self._write_transform_fixture(mcp_scene)
            payload = {
                "scene_path": str(cli_scene),
                "entity_id": "hero",
                "position": [7.5, 8.25],
                "rotation": 15.0,
                "scale": [1.5, 1.25],
            }

            cli_proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "main.py",
                    "command",
                    "run",
                    "transform.set",
                    "--json",
                    json.dumps(payload, ensure_ascii=False),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            self.assertEqual(cli_proc.returncode, 0, cli_proc.stdout + cli_proc.stderr)
            cli_result = json.loads(cli_proc.stdout)

            mcp_result = mcp_adapter.set_transform(
                str(mcp_scene),
                "hero",
                position=[7.5, 8.25],
                rotation=15.0,
                scale=[1.5, 1.25],
            )

            self.assertEqual(
                self._normalize_command_result(cli_result),
                self._normalize_command_result(mcp_result),
            )
            self.assertEqual(
                self._normalize_scene_data(cli_scene),
                self._normalize_scene_data(mcp_scene),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_set_script_property_matches_cli_scene_edit_output(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="mcp_cli_script_", dir=str(WORKSPACE)))
        try:
            cli_scene = self._make_scene_project(root / "cli_project")
            mcp_scene = self._make_scene_project(root / "mcp_project")
            self._write_script_fixture(cli_scene)
            self._write_script_fixture(mcp_scene)
            payload = {
                "scene_path": str(cli_scene),
                "entity_id": "hero",
                "script": "brain",
                "property_path": "mind.level",
                "value": 4,
            }

            cli_proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "main.py",
                    "command",
                    "run",
                    "script.set_property",
                    "--json",
                    json.dumps(payload, ensure_ascii=False),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            self.assertEqual(cli_proc.returncode, 0, cli_proc.stdout + cli_proc.stderr)
            cli_result = json.loads(cli_proc.stdout)

            mcp_result = mcp_adapter.set_script_property(
                str(mcp_scene),
                "hero",
                "brain",
                "mind.level",
                4,
            )

            self.assertEqual(
                self._normalize_command_result(cli_result),
                self._normalize_command_result(mcp_result),
            )
            self.assertEqual(
                self._normalize_scene_data(cli_scene),
                self._normalize_scene_data(mcp_scene),
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def _make_scene_project(self, project: Path) -> Path:
        scene = project / "scenes" / "main.pond"
        scene.parent.mkdir(parents=True)
        (project / "project.json").write_text(
            json.dumps(
                {
                    "name": project.name,
                    "active_scene": "main.pond",
                    "suite_id": "lotucosm.vitaloom.suite",
                    "product_id": "lotucosm-vitaloom",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        scene.write_text(
            json.dumps(
                {"name": "Main", "entities": [], "components": []},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return scene

    def _write_transform_fixture(self, scene: Path) -> None:
        scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {
                            "id": "hero",
                            "name": "Hero",
                            "type": "game_actor",
                            "position": [1.0, 2.0],
                            "rotation": 0.0,
                            "scale": [1.0, 1.0],
                            "scripts": [],
                        }
                    ],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _write_script_fixture(self, scene: Path) -> None:
        scene.write_text(
            json.dumps(
                {
                    "name": "Main",
                    "entities": [
                        {
                            "id": "hero",
                            "name": "Hero",
                            "type": "game_actor",
                            "position": [1.0, 2.0],
                            "scripts": [
                                {
                                    "name": "brain",
                                    "type": "Brain",
                                    "properties": {"mind": {"level": 1}},
                                }
                            ],
                        }
                    ],
                    "components": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _normalize_command_result(self, result: dict) -> dict:
        cleaned = dict(result)
        cleaned["result"] = dict(cleaned.get("result") or {})
        cleaned["result"]["scene_path"] = "<scene>"
        if "audit_id" in cleaned["result"]:
            cleaned["result"]["audit_id"] = "<audit>"
        if "audit_path" in cleaned["result"]:
            cleaned["result"]["audit_path"] = "<audit_path>"
        return cleaned

    def _normalize_scene_data(self, scene: Path) -> dict:
        data = json.loads(scene.read_text(encoding="utf-8"))
        data.pop("modified_at", None)
        return data

    def _normalize_replay_status(self, result: dict) -> dict:
        cleaned = dict(result)
        cleaned["result"] = dict(cleaned.get("result") or {})
        return cleaned


if __name__ == "__main__":
    unittest.main()
