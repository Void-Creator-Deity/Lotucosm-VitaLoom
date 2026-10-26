# -*- coding: utf-8 -*-
"""Build and launch configuration guards for the FrameCore suite layout."""
from __future__ import annotations

import unittest
from pathlib import Path

from hub.hub_launcher import editor_subprocess_command


ROOT = Path(__file__).resolve().parents[1]


class BuildConfigSeedTests(unittest.TestCase):
    def test_root_entrypoints_are_framecore_bootstraps(self) -> None:
        main_text = (ROOT / "main.py").read_text(encoding="utf-8")
        player_text = (ROOT / "player.py").read_text(encoding="utf-8")
        self.assertIn("load_default_suite_manifest", main_text)
        self.assertIn("_run_product_entry", player_text)

    def test_build_scripts_reference_suite_layout(self) -> None:
        build_text = (ROOT / "tools" / "build_exe.py").read_text(encoding="utf-8")
        self.assertIn("FrameCore", build_text)
        self.assertNotIn('("core", "core")', build_text)


class HubSubprocessCommandTests(unittest.TestCase):
    def test_dev_mode_uses_product_runtime_main(self) -> None:
        program, args, version = editor_subprocess_command(str(ROOT / "workspace" / "projects" / "samples"))
        self.assertTrue(program)
        self.assertEqual(args[0], str(version.runtime_root / "main.py"))
        self.assertIn("--editor", args)
        self.assertIn("--project", args)


if __name__ == "__main__":
    unittest.main()
