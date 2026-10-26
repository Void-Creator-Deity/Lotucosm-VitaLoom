# -*- coding: utf-8 -*-
"""FrameCore app plugin lifecycle seam regression tests."""
from __future__ import annotations

import sys
from pathlib import Path

from FrameCore.lifecycle import FrameApi, LifecycleRunner
from FrameCore.suite_registry import load_default_suite_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_frame_api_creates_manifest_entry_lifecycle_plugin() -> None:
    suite = load_default_suite_manifest(ROOT)
    api = FrameApi(app_root=ROOT, resource_root=ROOT, suite=suite)
    runner = LifecycleRunner()

    plugin = api.create_lifecycle_plugin()
    runner.load(plugin, api)

    assert plugin.frame_api is api
    assert callable(plugin.run_entry)
    runner.unload_all()
    assert plugin.frame_api is None


def test_plugin_environment_does_not_bind_default_runtime(monkeypatch) -> None:
    suite = load_default_suite_manifest(ROOT)
    api = FrameApi(app_root=ROOT, resource_root=ROOT, suite=suite)
    monkeypatch.delenv("VITALOOM_PRODUCT_VERSION_ROOT", raising=False)
    runtime_root = str(
        ROOT
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    original_path = list(sys.path)
    sys.path[:] = [path for path in sys.path if path != runtime_root]
    try:
        api.install_plugin_env()
        assert "VITALOOM_PRODUCT_VERSION_ROOT" not in __import__("os").environ
        assert runtime_root not in sys.path
        assert str(suite.suite_root) in sys.path
    finally:
        sys.path[:] = original_path


def test_root_main_delegates_hub_without_importing_hub_gui() -> None:
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "create_lifecycle_plugin" in source
    assert "_run_frame_plugin_entry" in source
    assert "from hub." not in source
    assert "from PyQt6" not in source
    assert "SuiteLifecyclePlugin" not in source
