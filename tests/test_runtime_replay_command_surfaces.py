# -*- coding: utf-8 -*-
"""Runtime replay status command surfaces for Phase 6B."""
from __future__ import annotations

from core.VitaLoom.commands.registry import get_command_registry


def test_runtime_replay_status_command_is_read_only() -> None:
    registry = get_command_registry()
    spec = registry.describe("runtime.replay.status")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_runtime_replay_status_command_reports_readonly_evidence() -> None:
    result = get_command_registry().run("runtime.replay.status", {})

    assert result["ok"] is True
    status = result["result"]
    assert status["read_only"] is True
    assert status["unified_pond_enabled"] is False
    assert {"sr_play", "ps_batch", "ps_replay"}.issubset(status["lanes"]["defined"])
    assert "ps_replay" in status["ecology"]["lanes_defined"]
    assert "unified_pond" in status["do_not_claim"]
    assert "full_unified_runtime_replay" in status["do_not_claim"]
