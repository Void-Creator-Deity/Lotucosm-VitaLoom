# -*- coding: utf-8 -*-
"""Root main.py command adapter should delegate into product runtime."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class AiCommandCliTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", "main.py", "command", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_command_list_outputs_json(self) -> None:
        proc = self._run("list")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        ids = {row["id"] for row in data["commands"]}
        self.assertIn("project.state", ids)
        self.assertIn("project.create", ids)
        self.assertIn("project.set_active_scene", ids)
        self.assertIn("project.set_ps_experiment_preset", ids)
        self.assertIn("project.set_evolution_defaults", ids)
        self.assertIn("scene.summary", ids)
        self.assertIn("entity.create", ids)
        self.assertIn("transform.set", ids)
        self.assertIn("script.set_property", ids)
        self.assertIn("asset.rename", ids)
        self.assertIn("asset.delete", ids)
        self.assertIn("asset.retirement.analyze", ids)
        self.assertIn("asset.referenced.replace", ids)
        self.assertIn("asset.transaction.undo", ids)
        self.assertIn("asset.transaction.redo", ids)
        self.assertIn("asset.transaction.inspect", ids)
        self.assertIn("asset.transaction.recovery.list", ids)
        self.assertIn("asset.transaction.recovery.resolve", ids)
        self.assertIn("asset.transaction.prune.plan", ids)
        self.assertIn("asset.transaction.prune.apply", ids)
        self.assertIn("prefab.place", ids)
        self.assertIn("asset.create", ids)
        self.assertIn("asset.import", ids)
        self.assertIn("asset.validate", ids)
        self.assertIn("asset.dependencies", ids)
        self.assertIn("asset.export_closure", ids)
        self.assertIn("asset.apply_to_scene", ids)
        self.assertIn("plugin.list", ids)
        self.assertIn("plugin.enable", ids)
        self.assertIn("plugin.disable", ids)
        self.assertIn("plugin.install", ids)
        self.assertIn("plugin.uninstall", ids)
        self.assertIn("export.player.prepare", ids)
        self.assertIn("runtime.replay.status", ids)
        self.assertIn("runtime.worldbridge.status", ids)
        self.assertIn("runtime.worldbridge.mapping_audit", ids)
        self.assertIn("runtime.worldbridge.component_decision", ids)
        self.assertIn("runtime.worldbridge.component_projection", ids)
        self.assertIn("runtime.worldbridge.component_projection_diagnostics", ids)

    def test_describe_retirement_analysis_is_read_only_with_optional_replacement(self) -> None:
        proc = self._run("describe", "asset.retirement.analyze")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["id"], "asset.retirement.analyze")
        self.assertFalse(data["mutates"])
        self.assertEqual(data["input_schema"]["required"], ["project_path", "source_path"])
        self.assertIn("replacement_path", data["input_schema"]["properties"])

    def test_describe_referenced_replacement_is_guarded_and_mutating(self) -> None:
        proc = self._run("describe", "asset.referenced.replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["id"], "asset.referenced.replace")
        self.assertTrue(data["mutates"])
        self.assertTrue(data["undoable"])
        self.assertEqual(data["input_schema"]["required"], ["project_path", "source_path", "replacement_path"])

    def test_describe_project_state(self) -> None:
        proc = self._run("describe", "project.state")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["id"], "project.state")
        self.assertFalse(data["mutates"])

    def test_run_runtime_replay_status_reports_readonly_evidence(self) -> None:
        proc = self._run("run", "runtime.replay.status", "--json", "{}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["result"]["read_only"])
        self.assertFalse(data["result"]["unified_pond_enabled"])
        self.assertIn("ps_replay", data["result"]["lanes"]["defined"])

    def test_run_runtime_worldbridge_status_reports_gate(self) -> None:
        proc = self._run("run", "runtime.worldbridge.status", "--json", "{}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["result"]["read_only"])
        self.assertFalse(data["result"]["default_ready"])
        self.assertFalse(data["result"]["unified_pond_enabled"])

    def test_run_runtime_worldbridge_mapping_audit_reports_losses(self) -> None:
        proc = self._run("run", "runtime.worldbridge.mapping_audit", "--json", "{}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertTrue(data["result"]["read_only"])
        self.assertFalse(data["result"]["lossless"])
        self.assertEqual(
            data["result"]["fields"]["membrane_component_graph"]["state"],
            "not_mapped",
        )

    def test_run_runtime_worldbridge_component_decision_reports_forbidden_behavior(self) -> None:
        proc = self._run("run", "runtime.worldbridge.component_decision", "--json", "{}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertFalse(data["result"]["maps_live_components"])
        self.assertIn("auto_ingest", data["result"]["forbidden_behavior"])

    def test_run_runtime_worldbridge_component_projection_reports_readonly_state(self) -> None:
        proc = self._run("run", "runtime.worldbridge.component_projection", "--json", "{}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["projection_state"], "read_only_projection")
        self.assertFalse(data["result"]["maps_live_components"])
        self.assertFalse(data["result"]["default_ready"])

    def test_run_runtime_worldbridge_component_projection_diagnostics_reports_summary(self) -> None:
        proc = self._run(
            "run",
            "runtime.worldbridge.component_projection_diagnostics",
            "--json",
            "{}",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(
            data["result"]["diagnostic_state"],
            "read_only_projection_diagnostics",
        )
        self.assertFalse(data["result"]["maps_live_components"])
        self.assertNotIn("components", data["result"])

    def test_run_project_state_for_sample(self) -> None:
        project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        proc = self._run(
            "run",
            "project.state",
            "--json",
            json.dumps({"project_path": str(project)}, ensure_ascii=False),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["name"], "PVAEC · 细胞演化")

    def test_project_open_reports_missing_gui_host_without_importing_one(self) -> None:
        project = Path(tempfile.mkdtemp(prefix="cli_project_open_", dir=str(ROOT / "workspace")))
        try:
            (project / "scenes").mkdir()
            (project / "project.json").write_text(
                json.dumps(
                    {
                        "name": "CLI Project Open",
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
            proc = self._run(
                "run",
                "project.open",
                "--json",
                json.dumps({"project_path": str(project)}, ensure_ascii=False),
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"]["code"], "project_host_adapter_unavailable")
            preparation = data["error"]["details"]["preparation"]
            self.assertEqual(preparation["status"], "ready")
            self.assertEqual(preparation["project_path"], str(project.resolve()))
            self.assertTrue(preparation["report_id"])
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_run_rejects_outside_workspace_path(self) -> None:
        proc = self._run(
            "run",
            "project.state",
            "--json",
            json.dumps({"project_path": str(ROOT.parent)}, ensure_ascii=False),
        )
        self.assertNotEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "path_outside_workspace")

    def test_cli_runs_scene_validate_for_sample(self) -> None:
        scene = (
            ROOT
            / "workspace"
            / "projects"
            / "samples"
            / "织机教程-迷你Roguelike"
            / "scenes"
            / "dungeon_01.pond"
        )
        proc = self._run(
            "run",
            "scene.validate",
            "--json",
            json.dumps({"scene_path": str(scene)}, ensure_ascii=False),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["duplicate_entity_ids"], [])

    def test_json_file_accepts_utf8_bom(self) -> None:
        project = ROOT / "workspace" / "projects" / "samples" / "织机教程-迷你Roguelike"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", suffix=".json", delete=False) as tmp:
            json.dump({"project_path": str(project)}, tmp, ensure_ascii=False)
            payload_path = Path(tmp.name)
        try:
            proc = self._run("run", "asset.scan", "--json-file", str(payload_path))
        finally:
            payload_path.unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertGreater(data["result"]["asset_count"], 0)

    def test_project_create_uses_project_manager_contract(self) -> None:
        name = f"cmd_create_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        shutil.rmtree(project, ignore_errors=True)
        try:
            proc = self._run(
                "run",
                "project.create",
                "--json",
                json.dumps(
                    {
                        "name": name,
                        "description": "Created through command registry",
                        "project_path": str(project),
                    },
                    ensure_ascii=False,
                ),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads(proc.stdout)
            self.assertTrue(data["ok"])
            self.assertEqual(Path(data["result"]["project_path"]), project)
            self.assertTrue((project / "project.json").is_file())
            self.assertTrue((project / "project.lock.json").is_file())
            self.assertTrue((project / "scenes" / "main_scene.pond").is_file())
            self.assertEqual(data["result"]["active_scene"], "main_scene.pond")
            self.assertTrue(data["result"]["project_lock_exists"])
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_project_create_project_type_controls_default_plugins(self) -> None:
        cases = {
            "blank": {"vitalloom.core.platform", "vitalloom.editor_essentials"},
            "pvaec": {
                "vitalloom.core.platform",
                "vitalloom.editor_essentials",
                "vitalloom.lotuspond.runtime",
                "vitalloom.engine.sr2d",
                "vitalloom.pvaec.simulation",
            },
            "roguelike": {
                "vitalloom.core.platform",
                "vitalloom.editor_essentials",
                "vitalloom.lotuspond.runtime",
                "vitalloom.engine.sr2d",
            },
        }
        created: list[Path] = []
        try:
            for project_type, expected in cases.items():
                name = f"cmd_{project_type}_{uuid.uuid4().hex[:6]}"
                project = ROOT / "workspace" / "projects" / "user" / name
                created.append(project)
                proc = self._run(
                    "run",
                    "project.create",
                    "--json",
                    json.dumps(
                        {
                            "name": name,
                            "project_path": str(project),
                            "project_type": project_type,
                        },
                        ensure_ascii=False,
                    ),
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                data = json.loads(proc.stdout)
                self.assertTrue(data["ok"])
                self.assertEqual(data["result"]["project_type"], project_type)
                required = set(data["result"]["required_capabilities"].keys())
                self.assertEqual(required, expected)
                if project_type == "roguelike":
                    self.assertNotIn("vitalloom.pvaec.simulation", required)
        finally:
            for project in created:
                shutil.rmtree(project, ignore_errors=True)

    def test_project_plugin_commands_update_project_state_and_lock(self) -> None:
        name = f"cmd_plugins_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        shutil.rmtree(project, ignore_errors=True)
        try:
            create = self._run(
                "run",
                "project.create",
                "--json",
                json.dumps({"name": name, "project_path": str(project), "project_type": "blank"}, ensure_ascii=False),
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)

            listing = self._run("run", "plugin.list", "--json", json.dumps({"project_path": str(project)}))
            self.assertEqual(listing.returncode, 0, listing.stdout + listing.stderr)
            rows = json.loads(listing.stdout)["result"]["plugins"]
            by_id = {row["id"]: row for row in rows}
            self.assertFalse(by_id["vitalloom.engine.sr2d"]["project_enabled"])

            enable = self._run(
                "run",
                "plugin.enable",
                "--json",
                json.dumps({"project_path": str(project), "plugin_id": "vitalloom.engine.sr2d"}),
            )
            self.assertEqual(enable.returncode, 0, enable.stdout + enable.stderr)
            self.assertTrue(json.loads(enable.stdout)["ok"])
            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIn("vitalloom.engine.sr2d", meta["required_capabilities"])
            self.assertNotIn("vitalloom.engine.sr2d", meta.get("disabled_plugins", []))
            lock = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
            self.assertIn("vitalloom.engine.sr2d", lock["resolved_capabilities"])

            disable = self._run(
                "run",
                "plugin.disable",
                "--json",
                json.dumps({"project_path": str(project), "plugin_id": "vitalloom.engine.sr2d"}),
            )
            self.assertEqual(disable.returncode, 0, disable.stdout + disable.stderr)
            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIn("vitalloom.engine.sr2d", meta.get("disabled_plugins", []))
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_project_plugin_command_accepts_contained_editor_plugin_id(self) -> None:
        name = f"cmd_contained_plugin_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        shutil.rmtree(project, ignore_errors=True)
        try:
            create = self._run(
                "run",
                "project.create",
                "--json",
                json.dumps({"name": name, "project_path": str(project), "project_type": "pvaec"}, ensure_ascii=False),
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)

            disable = self._run(
                "run",
                "plugin.disable",
                "--json",
                json.dumps({"project_path": str(project), "plugin_id": "PsExperimentPlugin"}),
            )
            self.assertEqual(disable.returncode, 0, disable.stdout + disable.stderr)
            result = json.loads(disable.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["target_kind"], "contained_plugin")
            self.assertEqual(result["result"]["package_id"], "vitalloom.pvaec.simulation")
            self.assertEqual(result["result"]["affected_plugins"], ["PsExperimentPlugin"])

            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIn("PsExperimentPlugin", meta.get("disabled_plugins", []))
            self.assertIn("vitalloom.pvaec.simulation", meta.get("required_capabilities", {}))
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_workspace_extension_is_source_not_global_enable(self) -> None:
        name = f"cmd_ext_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        ext = ROOT / "workspace" / "extensions" / "user" / f"fixture_ext_{uuid.uuid4().hex[:6]}"
        shutil.rmtree(project, ignore_errors=True)
        shutil.rmtree(ext, ignore_errors=True)
        try:
            ext.mkdir(parents=True)
            create = self._run(
                "run",
                "project.create",
                "--json",
                json.dumps({"name": name, "project_path": str(project), "project_type": "blank"}, ensure_ascii=False),
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            listing = self._run("run", "plugin.list", "--json", json.dumps({"project_path": str(project)}))
            self.assertEqual(listing.returncode, 0, listing.stdout + listing.stderr)
            rows = json.loads(listing.stdout)["result"]["plugins"]
            ext_rows = [row for row in rows if row["id"] == ext.name]
            self.assertEqual(len(ext_rows), 1)
            self.assertEqual(ext_rows[0]["source_kind"], "workspace_extension_source")
            self.assertFalse(ext_rows[0]["project_enabled"])

            install = self._run(
                "run",
                "plugin.install",
                "--json",
                json.dumps(
                    {
                        "project_path": str(project),
                        "plugin_id": ext.name,
                        "source": "workspace_user",
                        "path": str(ext),
                        "version": "0.1.0",
                    }
                ),
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIn(ext.name, meta["package_state"]["installed"])
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(ext, ignore_errors=True)

    def test_project_plugin_uninstall_removes_project_state_and_lock(self) -> None:
        name = f"cmd_uninstall_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        ext = ROOT / "workspace" / "extensions" / "user" / f"fixture_uninstall_{uuid.uuid4().hex[:6]}"
        shutil.rmtree(project, ignore_errors=True)
        shutil.rmtree(ext, ignore_errors=True)
        try:
            ext.mkdir(parents=True)
            create = self._run(
                "run",
                "project.create",
                "--json",
                json.dumps({"name": name, "project_path": str(project), "project_type": "blank"}, ensure_ascii=False),
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)

            plugin_id = ext.name
            install = self._run(
                "run",
                "plugin.install",
                "--json",
                json.dumps(
                    {
                        "project_path": str(project),
                        "plugin_id": plugin_id,
                        "source": "workspace_user",
                        "path": str(ext),
                        "version": "0.1.0",
                    },
                    ensure_ascii=False,
                ),
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIn(plugin_id, meta["package_state"]["installed"])
            self.assertIn(plugin_id, meta["required_capabilities"])
            lock_before = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
            self.assertIn(plugin_id, lock_before["resolved_capabilities"])

            uninstall = self._run(
                "run",
                "plugin.uninstall",
                "--json",
                json.dumps({"project_path": str(project), "plugin_id": plugin_id}, ensure_ascii=False),
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)
            result = json.loads(uninstall.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["result"]["plugin_id"], plugin_id)
            self.assertTrue(result["result"]["lock_refreshed"])

            meta = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertNotIn(plugin_id, meta["package_state"]["installed"])
            self.assertNotIn(plugin_id, meta["required_capabilities"])
            self.assertNotIn(plugin_id, meta.get("disabled_plugins", []))
            actions = [row["action"] for row in meta["package_state"]["history"]]
            self.assertIn("uninstall", actions)
            lock_after = json.loads((project / "project.lock.json").read_text(encoding="utf-8"))
            self.assertNotIn(plugin_id, lock_after["resolved_capabilities"])
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(ext, ignore_errors=True)

    def test_plugin_mutation_rolls_back_when_lock_refresh_fails(self) -> None:
        from core.VitaLoom.commands import runtime_commands

        name = f"cmd_lock_rollback_{uuid.uuid4().hex[:8]}"
        project = ROOT / "workspace" / "projects" / "user" / name
        shutil.rmtree(project, ignore_errors=True)
        try:
            project.mkdir(parents=True)
            manifest = {
                "name": name,
                "project_type": "blank",
                "required_capabilities": {},
                "package_state": {"installed": {}},
                "disabled_plugins": [],
            }
            manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
            (project / "project.json").write_bytes(manifest_bytes)
            lock_bytes = b'{"schema_version": 1, "resolved_capabilities": {}}\n'
            (project / "project.lock.json").write_bytes(lock_bytes)
            with patch.object(runtime_commands, "_resolve_workspace_path", return_value=project), patch.object(
                runtime_commands, "_refresh_project_lock", return_value=False
            ):
                result = runtime_commands._plugin_install(
                    {"project_path": str(project), "plugin_id": "fixture.plugin", "version": "1.0.0"},
                    {},
                )
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["code"], "project_lock_refresh_failed")
            self.assertEqual((project / "project.json").read_bytes(), manifest_bytes)
            self.assertEqual((project / "project.lock.json").read_bytes(), lock_bytes)
        finally:
            shutil.rmtree(project, ignore_errors=True)

    def test_export_player_prepare_reports_project_plugin_closure(self) -> None:
        project = next((ROOT / "workspace" / "projects" / "samples").glob("pvaec-*细胞*"))
        proc = self._run(
            "run",
            "export.player.prepare",
            "--json",
            json.dumps({"project_path": str(project)}, ensure_ascii=False),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        plugin_ids = {row["id"] for row in data["result"]["enabled_plugins"]}
        self.assertIn("vitalloom.pvaec.simulation", plugin_ids)
        self.assertIn("asset_dependencies", data["result"])
        self.assertIn("asset_export_closure", data["result"])

    def test_asset_export_closure_cli_reports_project_files(self) -> None:
        samples = ROOT / "workspace" / "projects" / "samples"
        project = next(path for path in samples.iterdir() if "Roguelike" in path.name)
        proc = self._run(
            "run",
            "asset.export_closure",
            "--json",
            json.dumps({"project_path": str(project)}, ensure_ascii=False),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        result = data["result"]
        self.assertIn("files", result)
        self.assertIn("enabled_plugins", result)
        self.assertGreater(result["file_count"], 0)
        self.assertEqual(result["missing_total"], 0)


if __name__ == "__main__":
    unittest.main()
