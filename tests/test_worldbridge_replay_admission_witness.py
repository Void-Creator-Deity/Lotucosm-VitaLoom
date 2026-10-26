# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json

import pytest

from core.Lotucosm.runtime.world_bridge_replay_admission_witness import (
    BLOCKERS,
    build_worldbridge_replay_admission_witness,
    decode_worldbridge_replay_admission_witness,
    encode_worldbridge_replay_admission_witness,
    validate_worldbridge_replay_admission_witness,
)
from core.VitaLoom.commands.registry import get_command_registry
from core.VitaLoom.commands import mcp_adapter


def _write_run(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "summary.json").write_text(
        json.dumps(
            {
                "config": {"seed": 42, "ticks": 4},
                "snapshots": [{"tick": 0}, {"tick": 2}, {"tick": 4}],
                "final": {"population": 3, "positions_norm": [[0.1, 0.2]]},
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return run


def test_real_run_summary_witness_is_bounded_and_not_admitted(tmp_path) -> None:
    run = _write_run(tmp_path)
    witness = build_worldbridge_replay_admission_witness(
        run_dir=run,
        project_path=tmp_path / "project",
        project_lock={"schema_version": 1, "runtime_epoch": "epoch-1"},
    )

    assert validate_worldbridge_replay_admission_witness(witness) == {"valid": True, "errors": []}
    assert witness["summary"]["snapshot_count"] == 3
    assert witness["blockers"] == list(BLOCKERS)
    assert witness["replay_admitted"] is False
    assert witness["live_adapter_admitted"] is False
    assert witness["default_ready"] is False


def test_witness_round_trip_and_tamper_rejection(tmp_path) -> None:
    witness = build_worldbridge_replay_admission_witness(run_dir=_write_run(tmp_path))
    encoded = encode_worldbridge_replay_admission_witness(witness)
    assert decode_worldbridge_replay_admission_witness(encoded) == witness

    tampered = copy.deepcopy(witness)
    tampered["summary"]["seed"] = 99
    assert "witness_digest_mismatch" in validate_worldbridge_replay_admission_witness(tampered)["errors"]

    broken = bytearray(encoded)
    broken[-2] = ord(" ")
    with pytest.raises(ValueError, match="invalid encoded|canonical"):
        decode_worldbridge_replay_admission_witness(broken)


def test_witness_rejects_overclaim_duplicate_keys_and_nonfinite_json(tmp_path) -> None:
    witness = build_worldbridge_replay_admission_witness(run_dir=_write_run(tmp_path))
    witness["replay_admitted"] = True
    assert "replay_admitted_overclaim" in validate_worldbridge_replay_admission_witness(witness)["errors"]

    duplicate = b'{"schema_version":1,"schema_version":1}'
    with pytest.raises(ValueError, match="invalid encoded"):
        decode_worldbridge_replay_admission_witness(duplicate)

    nonfinite = b'{"schema_version":NaN}'
    with pytest.raises(ValueError, match="invalid encoded"):
        decode_worldbridge_replay_admission_witness(nonfinite)


def test_missing_or_malformed_real_run_is_fail_closed(tmp_path) -> None:
    with pytest.raises(ValueError, match="run_summary_missing"):
        build_worldbridge_replay_admission_witness(run_dir=tmp_path / "missing")
    run = _write_run(tmp_path)
    (run / "summary.json").write_text('{"config": {"seed": 1}}', encoding="utf-8")
    with pytest.raises(ValueError, match="run_summary_snapshots_missing"):
        build_worldbridge_replay_admission_witness(run_dir=run)


def test_command_and_mcp_expose_witness_as_read_only_evidence(tmp_path, monkeypatch) -> None:
    run = _write_run(tmp_path)
    import core.VitaLoom.commands.runtime_commands as runtime_commands

    monkeypatch.setattr(runtime_commands, "_resolve_workspace_path", lambda raw: run)
    registry = get_command_registry()
    spec = registry.describe("runtime.replay.admission_witness")
    assert spec["mutates"] is False
    result = registry.run("runtime.replay.admission_witness", {"run_dir": str(run)})
    assert result["ok"] is True
    assert result["result"]["replay_admitted"] is False

    calls: list[tuple[str, dict[str, object]]] = []
    original = mcp_adapter.run_command
    try:
        def fake(command_id: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((command_id, dict(payload or {})))
            return result
        mcp_adapter.run_command = fake
        assert mcp_adapter.get_runtime_replay_admission_witness(run_dir=str(run)) == result
    finally:
        mcp_adapter.run_command = original
    assert calls == [("runtime.replay.admission_witness", {"run_dir": str(run)})]
