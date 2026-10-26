"""
package_services：安装/卸载/查询 API。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import unittest
import tempfile
import os
from pathlib import Path

from builtin.editor_extensions.package_services import (
    PackageCatalogService,
    PackageOperationService,
    parse_dependency_expr,
    parse_version,
    version_gte,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakeProjectManager:
    def __init__(self, project_path="."):
        self.cfg = {"disabled_plugins": [], "package_version_overrides": {}}
        self.project_path = project_path

    def get_current_project_config(self):
        return dict(self.cfg)

    def update_project_config_fields(self, fields):
        self.cfg.update(fields)
        return True

    def get_current_project_path(self):
        return self.project_path


class TestPackageServices(unittest.TestCase):
    def test_version_helpers(self):
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))
        self.assertTrue(version_gte("1.2.0", "1.1.9"))
        self.assertEqual(parse_dependency_expr("a>=1.0.0"), ("a", ">=", "1.0.0"))

    def test_catalog_overrides_and_updates(self):
        catalog = PackageCatalogService(".")
        merged = [{"id": "a", "version": "1.0.0"}]
        out = catalog.apply_version_overrides(merged, {"a": "1.2.0"})
        self.assertEqual(out[0]["version"], "1.2.0")
        loaded = [[{"id": "a", "version": "1.0.0"}], [{"id": "a", "version": "1.3.0"}]]
        updates = catalog.collect_update_candidates(loaded, out)
        self.assertEqual(updates.get("a"), "1.3.0")

    def test_catalog_annotates_project_lock_status(self):
        catalog = PackageCatalogService(str(ROOT))
        packages, _updates, errors = catalog.load_all_packages({})
        self.assertEqual(errors, [])
        project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
        annotated = catalog.annotate_project_lock_status(packages, str(project))
        lookup = {str(pkg.get("id", "")): pkg for pkg in annotated}
        sr2d = lookup["vitalloom.engine.sr2d"]
        pvaec = lookup["vitalloom.pvaec.simulation"]
        assets = lookup["vitalloom.assets.demo"]
        self.assertTrue(sr2d["project_required"])
        self.assertEqual(sr2d["project_lock_status"], "locked")
        self.assertEqual(sr2d["project_lock_admission"], "current")
        self.assertEqual(sr2d["project_locked_version"], "1.0.0")
        self.assertEqual(pvaec["project_lock_status"], "locked")
        self.assertEqual(pvaec["project_lock_admission"], "current")
        self.assertFalse(assets["project_required"])
        self.assertEqual(assets["project_lock_status"], "optional")

    def test_operation_state_compatibility(self):
        pm = _FakeProjectManager()
        ops = PackageOperationService(pm)
        self.assertEqual(ops.get_version_overrides(), {})
        ok = ops.write_version_overrides({"a": "1.1.0"}, action="update")
        self.assertTrue(ok)
        self.assertEqual(pm.cfg.get("package_version_overrides", {}).get("a"), "1.1.0")
        state = pm.cfg.get("package_state", {})
        self.assertIn("operation_log", state)
        self.assertEqual(state.get("version_overrides", {}).get("a"), "1.1.0")

    def test_export_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            pm = _FakeProjectManager(project_path=td)
            ops = PackageOperationService(pm)
            plan = {
                "items": [
                    {"id": "a", "current_version": "1.0.0", "target_version": "1.2.0", "source": "builtin"},
                ],
                "count": 1,
                "source_summary": {"builtin": 1},
            }
            out_path, err = ops.export_plan_to_logs(plan)
            self.assertIsNone(err)
            self.assertTrue(os.path.exists(str(out_path)))
            ok, _ = ops.apply_update_plan(plan, action="update")
            self.assertTrue(ok)
            self.assertEqual(ops.get_version_overrides().get("a"), "1.2.0")
            ok2, latest = ops.rollback_from_latest_export()
            self.assertTrue(ok2)
            self.assertTrue(str(latest).endswith(".json"))
            self.assertEqual(ops.get_version_overrides().get("a"), "1.0.0")


if __name__ == "__main__":
    unittest.main()

