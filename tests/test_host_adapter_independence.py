# -*- coding: utf-8 -*-
"""E8 headless seams for Project World creation and runtime replay."""
from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path
from unittest.mock import patch


def _block_pyqt_imports(monkeypatch):
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)


def test_project_world_creation_authority_is_headless(tmp_path: Path, monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    from core.VitaLoom.project.project_world_creation import create_project_world

    target = tmp_path / "demo"
    report = create_project_world("Demo", target, project_type="pvaec")
    manifest = json.loads((target / "project.json").read_text(encoding="utf-8"))
    scene = json.loads((target / "scenes" / "main_scene.pond").read_text(encoding="utf-8"))

    assert report["status"] == "created"
    assert manifest["project_type"] == "pvaec"
    assert "vitalloom.pvaec.simulation" in manifest["required_capabilities"]
    assert scene["name"] == "主场景"
    assert (target / "assets").is_dir()
    assert (target / "scripts").is_dir()


def test_project_world_creation_refuses_existing_target(tmp_path: Path) -> None:
    from core.VitaLoom.project.project_world_creation import ProjectWorldCreationError, create_project_world

    target = tmp_path / "existing"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    try:
        create_project_world("Demo", target)
    except ProjectWorldCreationError as exc:
        assert exc.code == "project_target_exists"
    else:
        raise AssertionError("existing target must fail closed")
    assert marker.read_text(encoding="utf-8") == "keep"


def test_project_world_creation_cleans_up_when_lock_generation_fails(
    tmp_path: Path,
) -> None:
    from core.VitaLoom.project.project_world_creation import (
        ProjectWorldCreationError,
        create_project_world,
    )

    target = tmp_path / "lock-failure"
    with patch(
        "core.VitaLoom.suite.project_lock.ensure_project_lock",
        side_effect=OSError("lock store unavailable"),
    ):
        try:
            create_project_world("Demo", target, repo_root=tmp_path)
        except ProjectWorldCreationError as exc:
            assert exc.code == "project_lock_creation_failed"
        else:
            raise AssertionError("lock generation failure must fail closed")
    assert not target.exists()


def test_ecology_registry_uses_structural_ps_provider_without_pyqt(monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.simulation.ecology_registry", None)
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
    )
    from core.VitaLoom.simulation.ecology_registry import collect_ecology_snapshots
    from core.VitaLoom.core.service_keys import PS_EXPERIMENT, SIMULATION_SR_HOST

    class Sr:
        def get_sr_ecology_snapshot(self):
            return {"population": 2}
    class Ps:
        def get_ecology_snapshot(self):
            return {"ps_active": True, "ps_has_result": True, "ps_population": 3}
    registry = InMemoryRuntimeCapabilityRegistry()
    registry.register(SIMULATION_SR_HOST, Sr())
    registry.register(PS_EXPERIMENT, Ps())
    ctx = type("Context", (), {"services": registry})()
    snapshots = collect_ecology_snapshots(ctx)
    assert [item.lane.value for item in snapshots][:2] == ["sr_play", "ps_batch"]
    assert snapshots[1].population == 3


def test_runtime_replay_status_runs_without_pyqt(tmp_path: Path, monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.simulation.runtime_replay_status", None)
    from core.VitaLoom.simulation.runtime_replay_status import build_runtime_replay_status

    result = build_runtime_replay_status(project_path=tmp_path)
    assert result["status"] == "read_only_replay_evidence"
    assert result["read_only"] is True
    assert "ps_replay" in result["lanes"]["defined"]


def test_project_create_command_does_not_import_project_manager() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py"
    ).read_text(encoding="utf-8")
    block = source.split("def _project_create", 1)[1].split("def _project_lock_check", 1)[0]
    assert "project_world_creation" in block
    assert "project_manager" not in block


def test_project_manager_is_only_host_adapter_for_creation() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/project/project_manager.py"
    ).read_text(encoding="utf-8")
    block = source.split("    def create_project", 1)[1].split("    def _sync_viewport_into_scene_manager", 1)[0]

    assert "create_project_world" in block
    assert "project_world_creation" in block
    assert "project_created.emit" in block
    assert "emit_project_opened" in block
    assert '"required_capabilities"' not in block
    assert "_create_default_scene" not in block
