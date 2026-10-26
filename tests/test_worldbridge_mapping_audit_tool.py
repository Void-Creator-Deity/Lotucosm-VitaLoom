# -*- coding: utf-8 -*-
"""WorldBridge mapping audit check tool."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


ROOT = Path(__file__).resolve().parents[1]


def test_mapping_audit_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_mapping_audit.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout) == build_worldbridge_mapping_audit()
