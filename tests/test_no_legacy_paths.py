"""Repository guards against pre-FrameCore flat runtime paths."""

from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = (
    ROOT
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class TestNoLegacyPaths(unittest.TestCase):
    def test_legacy_plugin_paths_not_importable(self):
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin")

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin.interfaces")

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin.interface")

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("core.plugin.manager")

    def test_legacy_editor_entry_removed(self):
        vitalloom = importlib.import_module("core.VitaLoom")
        self.assertFalse(
            hasattr(vitalloom, "PyQtOrganismEditor"),
            "old PyQtOrganismEditor entry must not be exposed",
        )

    def test_executable_code_does_not_depend_on_flat_sample_project_paths(self):
        legacy_paths = (
            "projects/" + "pvaec-细胞演化",
            "projects\\" + "pvaec-细胞演化",
            "projects/" + "织机教程-迷你Roguelike",
            "projects\\" + "织机教程-迷你Roguelike",
        )
        scanned_roots = (
            RUNTIME_ROOT / "core",
            RUNTIME_ROOT / "builtin",
            ROOT / "tools",
            ROOT / ".cursor" / "rules",
        )
        standalone_files = (ROOT / "main.py", ROOT / "player.py")
        suffixes = {".py", ".json", ".toml", ".mdc"}
        violations: list[str] = []

        for root in scanned_roots:
            self.assertTrue(root.exists(), f"guard scan root missing: {root}")

        files: list[Path] = []
        for root in scanned_roots:
            if root.is_dir():
                files.extend(path for path in root.rglob("*") if path.is_file())
        files.extend(path for path in standalone_files if path.is_file())

        for path in files:
            if path.suffix not in suffixes or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in legacy_paths:
                if token in text:
                    violations.append(f"{path.relative_to(ROOT)}: {token}")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
