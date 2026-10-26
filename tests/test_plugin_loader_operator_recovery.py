# -*- coding: utf-8 -*-
"""PluginLoader execution Adapter for confirmation-bound lifecycle recovery."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

from test_plugin_loader_lifecycle_authority import _KernelStub, _write_addon


def _project(path: Path) -> None:
    path.mkdir()
    (path / "project.json").write_text(
        json.dumps({"name": path.name, "disabled_plugins": [], "required_capabilities": {}}),
        encoding="utf-8",
    )


def test_stale_report_rejected_before_discovery_or_sync(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader
    from core.VitaLoom.project.plugin_host_operator import PluginHostOperatorError

    loader = PluginLoader(_KernelStub(tmp_path))
    project = tmp_path / "world"
    _project(project)
    loader.scan_project_addons(project)
    loader.last_lifecycle_report = {"status": "blocked", "diagnostics": [{"code": "cycle"}]}
    inspection = loader.inspect_plugin_host()
    recovery = inspection["recoveries"][0]
    loader.last_lifecycle_report = {"status": "blocked", "diagnostics": [{"code": "missing"}]}

    with patch.object(loader, "scan_project_addons") as scan, patch.object(loader, "sync_plugins_for_project") as sync:
        try:
            loader.resolve_plugin_host_recovery(
                project_path=str(project),
                report_id=inspection["report_id"],
                action=recovery["action"],
                operator_confirmation=recovery["operator_confirmation_required"],
            )
        except PluginHostOperatorError as exc:
            assert exc.code == "plugin_host_report_stale"
        else:
            raise AssertionError("stale report must fail")
        scan.assert_not_called()
        sync.assert_not_called()


def test_blocked_discovery_recovery_runs_normal_discovery_then_sync(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    previous_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
    os.environ["VITALOOM_EAGER_PLUGINS"] = "0"
    try:
        loader = PluginLoader(_KernelStub(tmp_path))
        project = tmp_path / "world"
        _project(project)
        broken = project / "addons" / "example"
        broken.mkdir(parents=True)
        (broken / "example_plugin.py").write_text("raise AssertionError('not authorized')\n", encoding="utf-8")

        blocked = loader.scan_project_addons(project)
        assert blocked["status"] == "blocked"
        inspection = loader.inspect_plugin_host()
        recovery = inspection["recoveries"][0]

        shutil.rmtree(broken)
        _write_addon(project, folder="example", plugin_id="ExamplePlugin")
        with patch("core.VitaLoom.project.plugin_activation.collect_active_plugin_ids", return_value=set()):
            result = loader.resolve_plugin_host_recovery(
                project_path=str(project),
                report_id=inspection["report_id"],
                action=recovery["action"],
                operator_confirmation=recovery["operator_confirmation_required"],
            )
        assert result["status"] == "settled"
        assert result["discovery"]["status"] == "ready"
        assert result["lifecycle"]["status"] == "settled"
        assert "ExamplePlugin" in loader.loaded_plugins
        assert result["after"]["status"] == "settled"
    finally:
        if previous_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = previous_eager


def test_recovery_stops_when_fresh_discovery_is_still_blocked(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    loader = PluginLoader(_KernelStub(tmp_path))
    project = tmp_path / "world"
    _project(project)
    addon = project / "addons" / "broken"
    addon.mkdir(parents=True)
    (addon / "broken_plugin.py").write_text("# never imported\n", encoding="utf-8")
    loader.scan_project_addons(project)
    inspection = loader.inspect_plugin_host()
    recovery = inspection["recoveries"][0]

    with patch.object(loader, "sync_plugins_for_project") as sync:
        result = loader.resolve_plugin_host_recovery(
            project_path=str(project),
            report_id=inspection["report_id"],
            action=recovery["action"],
            operator_confirmation=recovery["operator_confirmation_required"],
        )
    assert result["status"] == "blocked"
    assert result["discovery"]["status"] == "blocked"
    sync.assert_not_called()


def test_failed_project_switch_inspection_distinguishes_requested_and_retained_worlds(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    previous_eager = os.environ.get("VITALOOM_EAGER_PLUGINS")
    os.environ["VITALOOM_EAGER_PLUGINS"] = "0"
    try:
        loader = PluginLoader(_KernelStub(tmp_path))
        old_project = tmp_path / "old"
        _project(old_project)
        _write_addon(old_project, folder="old", plugin_id="OldPlugin")
        assert loader.scan_project_addons(old_project)["status"] == "ready"
        with patch("core.VitaLoom.project.plugin_activation.collect_active_plugin_ids", return_value=set()):
            assert loader.sync_plugins_for_project({}, repo_root=tmp_path)["status"] == "settled"

        new_project = tmp_path / "new"
        _project(new_project)
        broken = new_project / "addons" / "broken"
        broken.mkdir(parents=True)
        (broken / "broken_plugin.py").write_text("# missing manifest\n", encoding="utf-8")
        assert loader.scan_project_addons(new_project)["status"] == "blocked"

        inspection = loader.inspect_plugin_host()
        assert inspection["status"] == "blocked"
        assert inspection["project_path"].endswith("new")
        assert inspection["embedded_catalog_project_path"].endswith("old")
        assert "OldPlugin" in inspection["active_plugin_ids"]
        assert inspection["recoveries"][0]["project_path"] == inspection["project_path"]
    finally:
        if previous_eager is None:
            os.environ.pop("VITALOOM_EAGER_PLUGINS", None)
        else:
            os.environ["VITALOOM_EAGER_PLUGINS"] = previous_eager
