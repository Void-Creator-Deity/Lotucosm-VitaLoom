# -*- coding: utf-8 -*-
"""WorldBridge component projection diagnostics check tool."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_component_projection_diagnostics_tool_reports_summary_only() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_component_projection_diagnostics.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    assert data["status"] == "worldbridge_component_projection_diagnostics"
    assert data["diagnostic_state"] == "read_only_projection_diagnostics"
    assert data["read_only"] is True
    assert data["maps_live_components"] is False
    assert data["default_ready"] is False
    assert "components" not in data
