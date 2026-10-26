# -*- coding: utf-8 -*-
"""WorldBridge component projection check tool."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_component_projection import (
    build_worldbridge_component_projection,
)


ROOT = Path(__file__).resolve().parents[1]


def test_component_projection_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_component_projection.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    expected = build_worldbridge_component_projection()
    assert data["schema_version"] == expected["schema_version"]
    assert data["projection_state"] == "read_only_projection"
    assert data["read_only"] is True
    assert data["maps_live_components"] is False
    assert data["default_ready"] is False
    assert "live_component_graph_mapping" in data["do_not_claim"]
