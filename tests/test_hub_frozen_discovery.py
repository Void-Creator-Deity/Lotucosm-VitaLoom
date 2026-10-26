# -*- coding: utf-8 -*-
"""Hub project discovery tests for frozen installs and external recent projects."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hub.project_list_model import discover_hub_projects


class HubFrozenDiscoveryTests(unittest.TestCase):
    def _make_install_layout(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="vitaloom_install_"))
        demo = root / "workspace" / "projects" / "samples" / "demo"
        demo.mkdir(parents=True)
        (root / "workspace" / "projects" / "user").mkdir(parents=True, exist_ok=True)
        (demo / "project.json").write_text(
            json.dumps({"name": "Demo", "loom_editor_version": "1.0.0"}),
            encoding="utf-8",
        )
        sys_dir = root / "workspace" / "state" / "system"
        sys_dir.mkdir(parents=True)
        external = root.parent / "outside_install_external"
        external.mkdir(parents=True, exist_ok=True)
        (external / "project.json").write_text(
            json.dumps({"name": "External", "loom_editor_version": "1.0.0"}),
            encoding="utf-8",
        )
        (sys_dir / "hub_projects.json").write_text(
            json.dumps({"schema_version": 1, "projects": [str(external.resolve())]}),
            encoding="utf-8",
        )
        return root

    def test_frozen_default_hides_external_recent(self) -> None:
        root = self._make_install_layout()
        with patch("hub.hub_paths.application_root", return_value=root), patch(
            "hub.project_list_model.is_frozen_bundle",
            return_value=True,
        ):
            entries = discover_hub_projects(root, include_external_recent=False)
        names = {entry.name for entry in entries}
        self.assertIn("Demo", names)
        self.assertNotIn("External", names)

    def test_frozen_opt_in_shows_external_recent(self) -> None:
        root = self._make_install_layout()
        with patch("hub.hub_paths.application_root", return_value=root), patch(
            "hub.project_list_model.is_frozen_bundle",
            return_value=True,
        ):
            entries = discover_hub_projects(root, include_external_recent=True)
        names = {entry.name for entry in entries}
        self.assertIn("Demo", names)
        self.assertIn("External", names)


if __name__ == "__main__":
    unittest.main()
