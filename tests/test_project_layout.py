# -*- coding: utf-8 -*-
"""Workspace project layout guards for samples, user projects, and Hub discovery."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.VitaLoom.project.project_manager import ProjectManager
from hub.project_list_model import discover_hub_projects


class ProjectLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        ProjectManager._instance = None  # type: ignore[attr-defined]

    def tearDown(self) -> None:
        ProjectManager._instance = None  # type: ignore[attr-defined]

    def test_repo_has_samples_projects(self) -> None:
        from core.VitaLoom.core.bundle_paths import _dev_repo_root

        root = _dev_repo_root()
        self.assertTrue((root / "workspace" / "projects" / "samples").is_dir())
        self.assertTrue((root / "workspace" / "projects" / "user").is_dir())

    def test_iter_discovered_finds_samples_and_user(self) -> None:
        from core.VitaLoom.core.bundle_paths import iter_discovered_project_dirs

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            sample = base / "workspace" / "projects" / "samples" / "demo_a"
            user = base / "workspace" / "projects" / "user" / "my_game"
            legacy = base / "workspace" / "projects" / "legacy_flat"
            sample.mkdir(parents=True)
            user.mkdir(parents=True)
            legacy.mkdir(parents=True)
            (sample / "project.json").write_text("{}", encoding="utf-8")
            (user / "project.json").write_text("{}", encoding="utf-8")
            (legacy / "project.json").write_text("{}", encoding="utf-8")
            with patch("core.VitaLoom.core.bundle_paths.application_root", return_value=base), patch.dict(
                os.environ, {}, clear=True
            ):
                found = {p.name for p in iter_discovered_project_dirs()}
            self.assertEqual(found, {"demo_a", "my_game"})

    def test_legacy_flat_project_discovery_is_opt_in(self) -> None:
        from core.VitaLoom.core.bundle_paths import iter_discovered_project_dirs

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            legacy = base / "workspace" / "projects" / "legacy_flat"
            legacy.mkdir(parents=True)
            (legacy / "project.json").write_text("{}", encoding="utf-8")
            with patch("core.VitaLoom.core.bundle_paths.application_root", return_value=base), patch.dict(
                os.environ, {}, clear=True
            ):
                self.assertEqual(iter_discovered_project_dirs(), [])
                self.assertEqual(
                    {p.name for p in iter_discovered_project_dirs(include_legacy_flat=True)},
                    {"legacy_flat"},
                )

    def test_project_manager_defaults_to_user_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with patch("core.VitaLoom.core.bundle_paths.application_root", return_value=base), patch(
                "core.VitaLoom.core.bundle_paths.system_config_dir",
                return_value=base / "workspace" / "state" / "system",
            ):
                manager = ProjectManager()
                self.assertTrue(str(manager.projects_dir).replace("\\", "/").endswith("workspace/projects/user"))
                created = manager.create_project("test_layout_proj")
                self.assertIsNotNone(created)
                data = json.loads((Path(created) / "project.json").read_text(encoding="utf-8"))
                self.assertEqual(data.get("suite_id"), "lotucosm.vitaloom.suite")
                self.assertEqual(data.get("product_id"), "lotucosm-vitaloom")

    def test_hub_discovers_samples_in_repo(self) -> None:
        from core.VitaLoom.core.bundle_paths import _dev_repo_root

        entries = discover_hub_projects(_dev_repo_root())
        self.assertTrue(entries)

    def test_sample_scripts_do_not_depend_on_sibling_sample_projects(self) -> None:
        from core.VitaLoom.core.bundle_paths import _dev_repo_root

        samples_root = _dev_repo_root() / "workspace" / "projects" / "samples"
        violations: list[str] = []
        for script in samples_root.glob("*/scripts/*.py"):
            if "__pycache__" in script.parts:
                continue
            text = script.read_text(encoding="utf-8", errors="replace")
            if "parent.parent.parent" in text:
                violations.append(str(script.relative_to(samples_root)))
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
