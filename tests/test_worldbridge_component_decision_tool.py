# -*- coding: utf-8 -*-
"""WorldBridge component decision check tool."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)


ROOT = Path(__file__).resolve().parents[1]


def test_component_decision_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_component_decision.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout) == build_worldbridge_component_decision()
