# -*- coding: utf-8 -*-
"""Runtime replay status tool tests for Phase 6."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.VitaLoom.simulation.runtime_replay_status import build_runtime_replay_status


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_replay_status_tool_reports_readonly_facts() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_runtime_replay_status.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)

    assert data["schema_version"] == 1
    assert data["read_only"] is True
    assert "active" in data["lanes"]
    assert data["unified_pond_enabled"] is False
    assert "unified_pond" in data["do_not_claim"]
    assert "sr_ps_tick_merge" in data["do_not_claim"]
    assert "full_unified_runtime_replay" in data["do_not_claim"]
    assert "ps_replay" in data["ecology"]["lanes_defined"]


def test_runtime_replay_status_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_runtime_replay_status.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(proc.stdout) == build_runtime_replay_status()
