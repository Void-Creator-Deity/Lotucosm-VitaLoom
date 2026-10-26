# -*- coding: utf-8 -*-
"""Evidence authority for the live WorldBridge field round-trip matrix.

This witness formalizes every declared field/lane cell and binds the matrix to
the full unified replay authority. It does not claim cross-lane losslessness:
lane-specific absences and SR executable-script rejection remain explicit.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e555_full_unified_runtime_replay_authority import (
    validate_worldbridge_e555_full_unified_runtime_replay_authority,
)
from .world_bridge_mutation_authority import MAPPING_FIELDS


SCHEMA_VERSION = 1
STATUS = "worldbridge_e557_field_roundtrip_authority"
SCOPE = "live_owner_field_roundtrip_with_explicit_lane_boundaries"
ADMISSION_EFFECT = "none"
EXPECTED_RESTORED_CELLS = 27
EXPECTED_OWNER_ABSENT_CELLS = 2
EXPECTED_FAIL_CLOSED_CELLS = 1
EXPECTED_OWNER_ABSENCES = (
    ("hierarchy", "sr"),
    ("render_identity", "ps"),
)
EXPECTED_FAIL_CLOSED = (("scripts", "sr"),)
REMAINING_MAPPING_BLOCKERS = (
    "cross_lane_behavior_authority_not_admitted",
    "lane_local_hierarchy_and_render_identity_not_cross_lane",
    "sr_executable_scripts_not_portable",
)
PROOF_FIELDS = (
    "result_shape_valid",
    "all_declared_fields_present",
    "all_expected_lanes_present",
    "all_available_cells_closed",
    "expected_lane_owner_absences",
    "sr_script_fail_closed",
    "capture_contract_closed",
    "runtime_admissions_closed",
    "replay_authority_bound",
)
CLOSED_ADMISSION_FIELDS = (
    "lossless",
    "cross_lane_behavior_admitted",
    "tick_merge_admitted",
    "default_ready",
)
RESULT_KEYS = {
    "schema_version",
    "status",
    "real_game_viewport",
    "read_only",
    "probe_entity_id",
    "probe_organism_id",
    "declared_field_count",
    "matrix_cell_count",
    "restored_cells",
    "lost_cells",
    "owner_absent_cells",
    "no_mutation_api_cells",
    "not_writable_cells",
    "fail_closed_cells",
    "fail_closed_enforced_cells",
    "fail_closed_leaks",
    "declared_checkpoint_scopes",
    "capture_required_cells",
    "capture_restored_cells",
    "capture_contract_violations",
    "owner_contract_findings",
    "checkpoint_scope",
    "matrix",
    "runtime_admissions_closed",
    "atomic_checkpoint",
    "lossless",
    "replay_admitted",
    "default_ready",
    "errors",
    "ok",
}
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "field_roundtrip_result",
    "full_unified_replay_witness",
    "field_result_digest",
    "replay_witness_digest",
    "restored_cell_count",
    "owner_absent_cells",
    "fail_closed_cells",
    *PROOF_FIELDS,
    "remaining_mapping_blockers",
    "grants_admission",
    "admission_effect",
    *CLOSED_ADMISSION_FIELDS,
    "witness_digest",
)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _json_copy(value: object, field: str) -> Any:
    try:
        return json.loads(_canonical(value).decode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite canonical JSON") from exc


def _mapping_copy(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    copied = _json_copy(dict(value), field)
    if not isinstance(copied, dict):
        raise TypeError(f"{field} must remain a mapping")
    return copied


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _evaluate(
    *,
    field_result: Mapping[str, Any],
    replay_witness: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    result_shape_valid = (
        set(field_result) == RESULT_KEYS
        and field_result.get("schema_version") == 2
        and field_result.get("status") == "worldbridge_e537_field_roundtrip"
        and field_result.get("real_game_viewport") is True
        and field_result.get("read_only") is True
        and field_result.get("ok") is True
        and field_result.get("errors") == []
    )
    if not result_shape_valid:
        errors.append("field_result_shape_invalid")

    matrix = field_result.get("matrix")
    if not isinstance(matrix, list):
        matrix = []
        errors.append("field_matrix_invalid")
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for index, cell in enumerate(matrix):
        if not isinstance(cell, Mapping):
            errors.append(f"field_cell_{index}_invalid")
            continue
        field = cell.get("field")
        lane = cell.get("lane")
        if not isinstance(field, str) or not isinstance(lane, str) or lane not in {
            "sr",
            "ps",
        }:
            errors.append(f"field_cell_{index}_identity_invalid")
            continue
        key = (field, lane)
        if key in cells:
            errors.append(f"field_cell_{index}_duplicate")
        cells[key] = dict(cell)

    all_declared_fields_present = set(MAPPING_FIELDS) == {
        field for field, _lane in cells
    }
    expected_cell_keys = {
        (field, lane) for field in MAPPING_FIELDS for lane in ("sr", "ps")
    }
    all_expected_lanes_present = set(cells) == expected_cell_keys
    if not all_declared_fields_present:
        errors.append("declared_field_set_mismatch")
    if not all_expected_lanes_present:
        errors.append("field_lane_matrix_incomplete")

    restored = {
        key for key, cell in cells.items() if cell.get("verdict") == "restored"
    }
    owner_absent = {
        key for key, cell in cells.items()
        if str(cell.get("verdict", "")).startswith(
            ("lane_owner_absent", "owner_absent")
        )
    }
    fail_closed = {
        key for key, cell in cells.items()
        if cell.get("verdict") == "fail_closed_restore"
    }
    other = set(cells) - restored - owner_absent - fail_closed
    all_available_cells_closed = not other
    expected_lane_owner_absences = owner_absent == set(EXPECTED_OWNER_ABSENCES)
    sr_script_fail_closed = (
        fail_closed == set(EXPECTED_FAIL_CLOSED)
        and ("scripts", "sr") in cells
        and cells[("scripts", "sr")].get("live_preserved_on_reject") is True
    )
    if not all_available_cells_closed:
        errors.append("unclassified_field_cells")
    if not expected_lane_owner_absences:
        errors.append("unexpected_lane_owner_absence_set")
    if not sr_script_fail_closed:
        errors.append("sr_script_fail_closed_boundary_mismatch")

    capture_contract_closed = (
        field_result.get("capture_required_cells") == 10
        and field_result.get("capture_restored_cells") == 10
        and field_result.get("capture_contract_violations") == []
        and field_result.get("owner_contract_findings") == []
    )
    runtime_admissions_closed = (
        field_result.get("runtime_admissions_closed") is True
        and field_result.get("atomic_checkpoint") is False
        and field_result.get("lossless") is False
        and field_result.get("replay_admitted") is False
        and field_result.get("default_ready") is False
    )
    if not capture_contract_closed:
        errors.append("capture_contract_not_closed")
    if not runtime_admissions_closed:
        errors.append("field_result_runtime_admission_overclaim")

    aggregate_matches = (
        len(restored) == EXPECTED_RESTORED_CELLS
        and len(owner_absent) == EXPECTED_OWNER_ABSENT_CELLS
        and len(fail_closed) == EXPECTED_FAIL_CLOSED_CELLS
        and field_result.get("restored_cells") == len(restored)
        and field_result.get("owner_absent_cells") == len(owner_absent)
        and field_result.get("fail_closed_cells") == len(fail_closed)
        and field_result.get("fail_closed_enforced_cells")
        == len(fail_closed)
        and field_result.get("fail_closed_leaks") == []
        and field_result.get("lost_cells") == 0
        and field_result.get("no_mutation_api_cells") == 0
        and field_result.get("not_writable_cells") == 0
        and field_result.get("matrix_cell_count") == len(cells)
        and field_result.get("declared_field_count") == len(MAPPING_FIELDS)
    )
    if not aggregate_matches:
        errors.append("field_aggregate_mismatch")

    replay_validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            replay_witness
        )
    )
    replay_authority_bound = (
        replay_validation == {"valid": True, "errors": []}
        and replay_witness.get("trace_count", 0) >= 3
        and replay_witness.get("all_tick_portable_state_parity") is True
        and replay_witness.get("source_fresh_parity_proven") is True
    )
    if not replay_authority_bound:
        errors.extend(f"replay_{item}" for item in replay_validation["errors"])
        if not replay_validation["errors"]:
            errors.append("replay_authority_incomplete")

    proof = {
        "result_shape_valid": result_shape_valid,
        "all_declared_fields_present": all_declared_fields_present,
        "all_expected_lanes_present": all_expected_lanes_present,
        "all_available_cells_closed": all_available_cells_closed,
        "expected_lane_owner_absences": expected_lane_owner_absences,
        "sr_script_fail_closed": sr_script_fail_closed,
        "capture_contract_closed": capture_contract_closed,
        "runtime_admissions_closed": runtime_admissions_closed,
        "replay_authority_bound": replay_authority_bound,
    }
    projection = {
        "field_result_digest": _digest(field_result),
        "replay_witness_digest": replay_witness.get("witness_digest"),
        "restored_cell_count": len(restored),
        "owner_absent_cells": [
            {"field": field, "lane": lane}
            for field, lane in sorted(owner_absent)
        ],
        "fail_closed_cells": [
            {"field": field, "lane": lane}
            for field, lane in sorted(fail_closed)
        ],
        **proof,
    }
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e557_field_roundtrip_authority(
    *,
    field_roundtrip_result: Mapping[str, Any],
    full_unified_replay_witness: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a detached field matrix witness without claiming losslessness."""
    field_result = _mapping_copy(
        field_roundtrip_result,
        "field_roundtrip_result",
    )
    replay = _mapping_copy(
        full_unified_replay_witness,
        "full_unified_replay_witness",
    )
    errors, projection = _evaluate(
        field_result=field_result,
        replay_witness=replay,
    )
    if errors:
        raise ValueError(
            "E557 field round-trip witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "field_roundtrip_result": field_result,
        "full_unified_replay_witness": replay,
        **projection,
        "remaining_mapping_blockers": list(REMAINING_MAPPING_BLOCKERS),
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e557_field_roundtrip_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute the field matrix and replay binding from producers."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "errors": errors + ["witness_not_canonical_json"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")

    field_result = value.get("field_roundtrip_result")
    replay = value.get("full_unified_replay_witness")
    if not isinstance(field_result, Mapping) or not isinstance(replay, Mapping):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        field_result=field_result,
        replay_witness=replay,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_mapping_blockers") != list(
        REMAINING_MAPPING_BLOCKERS
    ):
        errors.append("remaining_mapping_blockers_mismatch")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in CLOSED_ADMISSION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "CLOSED_ADMISSION_FIELDS",
    "EXPECTED_FAIL_CLOSED",
    "EXPECTED_FAIL_CLOSED_CELLS",
    "EXPECTED_OWNER_ABSENCES",
    "EXPECTED_OWNER_ABSENT_CELLS",
    "EXPECTED_RESTORED_CELLS",
    "PROOF_FIELDS",
    "REMAINING_MAPPING_BLOCKERS",
    "RESULT_KEYS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e557_field_roundtrip_authority",
    "validate_worldbridge_e557_field_roundtrip_authority",
]
