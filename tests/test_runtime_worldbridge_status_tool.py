# -*- coding: utf-8 -*-
"""Runtime WorldBridge status tool tests for Phase 6C."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


ROOT = Path(__file__).resolve().parents[1]


def test_worldbridge_status_defaults_to_dual_and_not_ready_for_default() -> None:
    status = build_runtime_worldbridge_status()

    assert status["schema_version"] == 1
    assert status["read_only"] is True
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert "lossless_mapping" in status["known_gaps"]
    assert "full_unified_runtime_replay" in status["do_not_claim"]


def test_worldbridge_status_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_runtime_worldbridge_status.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(proc.stdout) == build_runtime_worldbridge_status()


def test_worldbridge_status_includes_mapping_audit_summary() -> None:
    status = build_runtime_worldbridge_status()

    audit = status["mapping_audit"]
    assert audit["status"] == "worldbridge_mapping_loss_audit"
    assert audit["lossless"] is False
    assert audit["safe_extension_candidate"] == "size_radius"


def test_worldbridge_status_exposes_script_entropy_quarantine_contract() -> None:
    status = build_runtime_worldbridge_status()
    contract = status["script_entropy_admission"]
    assert contract["status"] == "script_entropy_admission_contract"
    assert contract["availability"] == "contract_only"
    assert contract["opaque_findings_fail_closed"] is True
    assert contract["admitted"] is False
    assert contract["quarantined"] is True
    assert contract["reasons"] == ["current_script_evidence_not_observed"]
    assert contract["replay_admitted"] is False
    assert contract["default_ready"] is False


def test_viewport_quarantine_projection_includes_script_findings() -> None:
    from core.VitaLoom.viewports.game_viewport import GameViewport

    viewport = GameViewport.__new__(GameViewport)
    viewport._worldbridge_handoff_suspended = False
    viewport._sr_runtime_rng = object()
    viewport._sr_runtime_epoch = "epoch-e347"
    viewport._sr_script_entropy_audits = [{
        "path": "dynamic.py",
        "deterministic_ready": False,
        "findings": [{
            "kind": "opaque_dynamic_import",
            "authority": "unknown_dynamic_module",
        }],
    }]
    viewport._sr_script_entropy_receipts = []
    viewport._sr_script_trust_denials = [{"path": "scripts/blocked.py", "reason": "script_not_trusted"}]

    diagnostic = viewport.query_worldbridge_quarantine_diagnostic()
    script = diagnostic["script_entropy_admission"]
    assert script["quarantined"] is True
    assert script["admitted"] is False
    assert script["reasons"] == ["legacy_audit", "receipt_missing"]
    assert script["findings"] == [{
        "kind": "opaque_dynamic_import",
        "authority": "unknown_dynamic_module",
    }]
    assert script["trust_denials"] == [{"path": "scripts/blocked.py", "reason": "script_not_trusted"}]
    assert script["quarantined"] is True
    assert script["admitted"] is False
    assert script["replay_admitted"] is False
    assert script["default_ready"] is False
