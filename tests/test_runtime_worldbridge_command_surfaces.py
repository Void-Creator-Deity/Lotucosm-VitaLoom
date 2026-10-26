# -*- coding: utf-8 -*-
"""Runtime WorldBridge status command surfaces for Phase 6C."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from core.VitaLoom.commands.registry import get_command_registry


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "workspace"


def test_worldbridge_status_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.status")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_status_command_reports_gate_evidence() -> None:
    result = get_command_registry().run("runtime.worldbridge.status", {})

    assert result["ok"] is True
    status = result["result"]
    assert status["read_only"] is True
    assert status["default_ready"] is False
    assert status["unified_pond_enabled"] is False
    assert "world_bridge_module" in status["pilot_modules"]
    assert "lossless_mapping" in status["known_gaps"]


def test_worldbridge_status_command_reports_explicit_project_flag() -> None:
    project = Path(tempfile.mkdtemp(prefix="worldbridge_flag_", dir=str(WORKSPACE)))
    try:
        (project / "project.json").write_text(
            json.dumps(
                {
                    "name": "worldbridge_flag_fixture",
                    "runtime_mode": "unified_pond",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = get_command_registry().run(
            "runtime.worldbridge.status",
            {"project_path": str(project)},
        )

        assert result["ok"] is True
        status = result["result"]
        assert status["runtime_mode"] == "unified_pond"
        assert status["unified_pond_enabled"] is True
        assert status["default_ready"] is False
        assert status["known_gaps"]
        assert list(project.rglob("*.pond")) == []
    finally:
        shutil.rmtree(project, ignore_errors=True)


def test_worldbridge_mapping_audit_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.mapping_audit")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_mapping_audit_command_reports_losses() -> None:
    result = get_command_registry().run("runtime.worldbridge.mapping_audit", {})

    assert result["ok"] is True
    audit = result["result"]
    assert audit["read_only"] is True
    assert audit["lossless"] is False
    assert audit["fields"]["membrane_component_graph"]["state"] == "not_mapped"


def test_worldbridge_component_decision_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.component_decision")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_component_decision_command_reports_forbidden_behavior() -> None:
    result = get_command_registry().run("runtime.worldbridge.component_decision", {})

    assert result["ok"] is True
    decision = result["result"]
    assert decision["maps_live_components"] is False
    assert "auto_ingest" in decision["forbidden_behavior"]


def test_worldbridge_component_projection_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.component_projection")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_component_projection_command_reports_projection_state() -> None:
    result = get_command_registry().run("runtime.worldbridge.component_projection", {})

    assert result["ok"] is True
    projection = result["result"]
    assert projection["projection_state"] == "read_only_projection"
    assert projection["maps_live_components"] is False
    assert projection["default_ready"] is False


def test_worldbridge_component_projection_diagnostics_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.component_projection_diagnostics")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_component_projection_diagnostics_command_reports_summary_only() -> None:
    result = get_command_registry().run(
        "runtime.worldbridge.component_projection_diagnostics",
        {},
    )

    assert result["ok"] is True
    diagnostics = result["result"]
    assert diagnostics["diagnostic_state"] == "read_only_projection_diagnostics"
    assert diagnostics["maps_live_components"] is False
    assert "components" not in diagnostics
