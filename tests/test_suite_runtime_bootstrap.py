# -*- coding: utf-8 -*-
"""Suite runtime bootstrap validation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SuiteRuntimeBootstrapTests(unittest.TestCase):
    def test_bootstrap_loads_default_product_version(self) -> None:
        from core.VitaLoom.suite.runtime_bootstrap import bootstrap_suite_runtime

        runtime = bootstrap_suite_runtime(ROOT)
        self.assertEqual(runtime.suite.suite_id, "lotucosm.vitaloom.suite")
        self.assertEqual(runtime.product_version.product_id, "lotucosm-vitaloom")
        self.assertEqual(runtime.product_version.version, "1.0.0")

    def test_bootstrap_fails_when_version_runtime_missing(self) -> None:
        from core.VitaLoom.suite.runtime_bootstrap import bootstrap_suite_runtime

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "hub").mkdir()
            (root / "catalog").mkdir()
            (root / "catalog" / "package_index.json").write_text(
                json.dumps({"packages": []}), encoding="utf-8"
            )
            version_root = root / "versions" / "1.0.0"
            version_root.mkdir(parents=True)
            (version_root / "version_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "1.0.0",
                        "entrypoints": {"editor": "runtime/main.py --editor"},
                        "physical_roots": ["runtime/core/Lotucosm"],
                        "builtin_capability_index": "runtime/builtin/package_index.json",
                    }
                ),
                encoding="utf-8",
            )
            (root / "plugin_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "plugin_id": "lotucosm-vitaloom",
                        "suite_id": "lotucosm.vitaloom.suite",
                        "product_id": "lotucosm-vitaloom",
                        "display_name": "Lotucosm-VitaLoom",
                        "entry": "hub",
                        "default_version": "1.0.0",
                        "versions": ["1.0.0"],
                        "capability_catalog": "catalog/package_index.json",
                    }
                ),
                encoding="utf-8",
            )
            old_suite = os.environ.get("VITALOOM_SUITE_ROOT")
            old_version = os.environ.get("VITALOOM_PRODUCT_VERSION_ROOT")
            try:
                os.environ["VITALOOM_SUITE_ROOT"] = str(root)
                os.environ["VITALOOM_PRODUCT_VERSION_ROOT"] = str(version_root)
                with self.assertRaises(RuntimeError):
                    bootstrap_suite_runtime(root)
            finally:
                if old_suite is None:
                    os.environ.pop("VITALOOM_SUITE_ROOT", None)
                else:
                    os.environ["VITALOOM_SUITE_ROOT"] = old_suite
                if old_version is None:
                    os.environ.pop("VITALOOM_PRODUCT_VERSION_ROOT", None)
                else:
                    os.environ["VITALOOM_PRODUCT_VERSION_ROOT"] = old_version

    def test_entrypoints_call_suite_bootstrap(self) -> None:
        main_text = (ROOT / "main.py").read_text(encoding="utf-8")
        runtime_main = (
            ROOT
            / "FrameCore"
            / "plugins"
            / "lotucosm-vitaloom"
            / "versions"
            / "1.0.0"
            / "runtime"
            / "main.py"
        ).read_text(encoding="utf-8")
        self.assertIn("load_default_suite_manifest", main_text)
        self.assertIn("bootstrap_suite_runtime(resource_root())", runtime_main)

    def test_main_version_cli_smoke(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--version"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Lotucosm-VitaLoom 1.0.0", proc.stdout)
        self.assertIn("lotucosm-vitaloom 1.0.0", proc.stdout)

    def test_main_hub_cli_smoke(self) -> None:
        config_path = ROOT / "workspace" / "state" / "system" / "editor_config.json"
        before = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
        proc = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--smoke-hub"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Hub smoke OK:", proc.stdout)
        self.assertIn("lotucosm-vitaloom@1.0.0", proc.stdout)
        after = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
