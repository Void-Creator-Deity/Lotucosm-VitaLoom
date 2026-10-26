# -*- coding: utf-8 -*-
"""Package imports should not initialize runtime singletons."""
from __future__ import annotations

import subprocess
import sys
import unittest
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = SUITE_ROOT / "versions" / "1.0.0"
RUNTIME_ROOT = VERSION_ROOT / "runtime"


class PackageImportSideEffectTests(unittest.TestCase):
    def _run_import(self, module: str) -> subprocess.CompletedProcess[str]:
        return self._run_code(f"import {module}; print('ok')")

    def _run_code(self, code: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "FRAMECORE_ROOT": str(ROOT / "FrameCore"),
                "VITALOOM_SUITE_ROOT": str(SUITE_ROOT),
                "VITALOOM_PRODUCT_VERSION_ROOT": str(VERSION_ROOT),
                "VITALOOM_APP_ROOT": str(ROOT),
                "PYTHONPATH": str(RUNTIME_ROOT)
                + os.pathsep
                + str(ROOT)
                + os.pathsep
                + env.get("PYTHONPATH", ""),
            }
        )
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_core_package_import_is_side_effect_light(self) -> None:
        self.assertFalse((ROOT / "core").exists())
        proc = self._run_import("core")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("Cosmos", proc.stdout + proc.stderr)

    def test_metadata_import_is_side_effect_light(self) -> None:
        proc = self._run_import("core.VitaLoom.project.project_manifest")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("Cosmos", proc.stdout + proc.stderr)

    def test_readonly_command_registry_imports_without_pyqt6(self) -> None:
        proc = self._run_code(
            "import sys; "
            "sys.modules['PyQt6'] = None; "
            "from core.VitaLoom.commands.registry import get_command_registry; "
            "spec = get_command_registry().describe(" 
            "'runtime.worldbridge.component_projection_diagnostics'); "
            "assert spec['mutates'] is False; "
            "assert spec['requires_gui'] is False; "
            "print('headless-command-registry-ok')"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("headless-command-registry-ok", proc.stdout)

    def test_vitaloom_package_imports_are_side_effect_light(self) -> None:
        for module in (
            "core.VitaLoom.core",
            "core.VitaLoom.kernel",
            "core.VitaLoom.player",
            "core.VitaLoom.project",
            "core.VitaLoom.scene",
            "core.VitaLoom.suite",
            "core.VitaLoom.tools",
            "core.VitaLoom.viewports",
        ):
            with self.subTest(module=module):
                proc = self._run_import(module)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertNotIn("Cosmos", proc.stdout + proc.stderr)

    def test_product_runtime_exports_still_resolve_lazily(self) -> None:
        proc = self._run_import("core.VitaLoom.scene")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
