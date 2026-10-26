# -*- coding: utf-8 -*-
"""Runtime import layer guard for the product-version code."""
from __future__ import annotations

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


class ImportLayerGuardTests(unittest.TestCase):
    def test_builtin_has_no_sys_path_insert(self) -> None:
        root = RUNTIME_ROOT / "builtin"
        self.assertTrue(root.is_dir(), f"missing runtime builtin root: {root}")
        bad: list[str] = []
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "sys.path.insert" in text:
                bad.append(str(path.relative_to(RUNTIME_ROOT)))
        self.assertEqual(bad, [], "Remove sys.path hacks from: " + repr(bad))

    def test_core_lotucosm_has_no_sys_path_insert_except_launcher(self) -> None:
        root = RUNTIME_ROOT / "core" / "Lotucosm"
        self.assertTrue(root.is_dir(), f"missing runtime Lotucosm root: {root}")
        bad: list[str] = []
        for path in root.glob("*.py"):
            if path.name == "launcher.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "sys.path.insert" in text:
                bad.append(str(path.relative_to(RUNTIME_ROOT)))
        self.assertEqual(bad, [], repr(bad))


if __name__ == "__main__":
    unittest.main()
