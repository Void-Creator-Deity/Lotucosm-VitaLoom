# -*- coding: utf-8 -*-
"""Bounded witness for real run artifacts at the WorldBridge replay boundary.

The witness proves provenance and fail-closed rejection of a run artifact.  It
does not turn a PS overlay or a synthetic replay corpus into live replay
authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_replay_admission_witness"
BLOCKERS = (
    "shared_clock_and_delta_contract_missing",
    "shared_queued_input_ordering_missing",
    "shared_random_seed_contract_missing",
    "shared_pause_reset_error_isolation_contract_missing",
    "shared_scene_pond_checkpoint_contract_missing",
    "full_unified_runtime_replay_not_proven",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _read_summary(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "summary.json"
    if not path.is_file():
        raise ValueError("run_summary_missing")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("run_summary_invalid_json") from exc
    if not isinstance(value, dict):
        raise ValueError("run_summary_must_be_mapping")
    return value


def _summary_metadata(summary: Mapping[str, Any]) -> dict[str, Any]:
    config = summary.get("config")
    snapshots = summary.get("snapshots")
    final = summary.get("final")
    if not isinstance(config, Mapping):
        raise ValueError("run_summary_config_missing")
    if not isinstance(snapshots, list):
        raise ValueError("run_summary_snapshots_missing")
    if not isinstance(final, Mapping):
        raise ValueError("run_summary_final_missing")
    seed = config.get("seed")
    ticks = config.get("ticks")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("run_summary_seed_missing")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 1:
        raise ValueError("run_summary_ticks_invalid")
    return {
        "config_digest": _digest(dict(config)),
        "seed": seed,
        "ticks": ticks,
        "snapshot_count": len(snapshots),
        "final_digest": _digest(dict(final)),
    }


def build_worldbridge_replay_admission_witness(
    *,
    run_dir: str | Path,
    project_path: str | Path | None = None,
    project_lock: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a provenance witness from an actual experiment run directory."""
    run_path = Path(run_dir).resolve()
    summary = _read_summary(run_path)
    metadata = _summary_metadata(summary)
    project_binding = {
        "project_path": str(Path(project_path).resolve()) if project_path is not None else None,
        "project_lock_digest": _digest(dict(project_lock)) if isinstance(project_lock, Mapping) else None,
    }
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "run_dir": str(run_path),
        "summary_digest": _digest(summary),
        "summary": metadata,
        "project_binding": project_binding,
        "blockers": list(BLOCKERS),
        "replay_admitted": False,
        "live_adapter_admitted": False,
        "default_ready": False,
    }
    witness["witness_digest"] = _digest({**witness, "witness_digest": ""})
    return copy.deepcopy(witness)


def validate_worldbridge_replay_admission_witness(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_must_be_mapping"]}
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS or value.get("read_only") is not True:
        errors.append("identity_or_read_only_mismatch")
    if not isinstance(value.get("run_dir"), str) or not value["run_dir"]:
        errors.append("run_dir_invalid")
    for field in ("summary_digest", "witness_digest"):
        digest = value.get(field)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append(f"{field}_invalid")
    if not isinstance(value.get("summary"), Mapping):
        errors.append("summary_metadata_invalid")
    else:
        summary = value["summary"]
        for field in ("config_digest", "final_digest"):
            digest = summary.get(field)
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"summary_{field}_invalid")
        if isinstance(summary.get("seed"), bool) or not isinstance(summary.get("seed"), int):
            errors.append("summary_seed_invalid")
        if isinstance(summary.get("ticks"), bool) or not isinstance(summary.get("ticks"), int) or summary.get("ticks", 0) < 1:
            errors.append("summary_ticks_invalid")
        if isinstance(summary.get("snapshot_count"), bool) or not isinstance(summary.get("snapshot_count"), int) or summary.get("snapshot_count", -1) < 0:
            errors.append("summary_snapshot_count_invalid")
    binding = value.get("project_binding")
    if not isinstance(binding, Mapping) or (binding.get("project_path") is not None and not isinstance(binding.get("project_path"), str)):
        errors.append("project_binding_invalid")
    if isinstance(binding, Mapping) and binding.get("project_lock_digest") is not None:
        digest = binding.get("project_lock_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append("project_lock_digest_invalid")
    if value.get("blockers") != list(BLOCKERS):
        errors.append("blockers_mismatch")
    for field in ("replay_admitted", "live_adapter_admitted", "default_ready"):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    expected = _digest({**dict(value), "witness_digest": ""})
    if value.get("witness_digest") != expected:
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_replay_admission_witness(value: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_replay_admission_witness(value)["valid"] is not True:
        raise ValueError("invalid replay admission witness")
    return _canonical(value)


def decode_worldbridge_replay_admission_witness(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("encoded witness must be bytes-like")
    raw = bytes(data)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid encoded replay admission witness") from exc
    if validate_worldbridge_replay_admission_witness(value)["valid"] is not True or _canonical(value) != raw:
        raise ValueError("encoded replay admission witness is not canonical")
    return copy.deepcopy(value)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON constant: {value}")


__all__ = [
    "BLOCKERS",
    "STATUS",
    "build_worldbridge_replay_admission_witness",
    "decode_worldbridge_replay_admission_witness",
    "encode_worldbridge_replay_admission_witness",
    "validate_worldbridge_replay_admission_witness",
]
