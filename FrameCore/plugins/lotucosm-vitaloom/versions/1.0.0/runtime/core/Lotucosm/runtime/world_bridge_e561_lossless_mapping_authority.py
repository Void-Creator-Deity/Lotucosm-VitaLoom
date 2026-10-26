# -*- coding: utf-8 -*-
"""Declared-no-silent-loss authority for the WorldBridge mapping ledger.

Losslessness here means every declared field/lane cell has an explicit
disposition and no observed cell is silently dropped. It does not claim that
live executable SR scripts can be rehydrated from a portable checkpoint.
That boundary remains explicit and fail-closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_e557_field_roundtrip_authority import (
    validate_worldbridge_e557_field_roundtrip_authority,
)
from .world_bridge_e560_behavior_equivalence_authority import (
    ELIGIBLE_BEHAVIOR_ROUTES,
    LANE_LOCAL_BEHAVIOR_ROUTES,
    validate_worldbridge_e560_behavior_equivalence_authority,
)
from .world_bridge_mutation_authority import (
    MAPPING_FIELDS,
    WORLD_BRIDGE_LIVE_MAPPER_PATHS,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e561_lossless_mapping_authority"
SCOPE = "declared_mapping_dispositions_with_explicit_nonportable_boundaries"
LOSSLESS_POLICY = "no_silent_loss_with_explicit_owner_boundaries_v1"
ADMISSION_EFFECT = "none"
FIELD_DISPOSITIONS = {
    "position": "bidirectional_owner_roundtrip",
    "energy": "bidirectional_owner_roundtrip",
    "health": "bidirectional_owner_roundtrip",
    "max_energy": "creation_only_sr_to_ps_capacity",
    "max_health": "creation_only_sr_to_ps_capacity",
    "size_radius": "bidirectional_owner_roundtrip",
    "velocity_acceleration": "bidirectional_owner_roundtrip",
    "developmental_profile": "spawn_profile_sr_to_ps_boundary",
    "social_enabled": "spawn_profile_sr_to_ps_boundary",
    "active_visible_state": "active_bidirectional_visible_sr_local",
    "render_identity": "sr_local_render_owner_ps_absent",
    "scripts": "lane_local_executable_sr_fail_closed_ps_restored",
    "membrane_component_graph": "lane_local_topology_owners",
    "hierarchy": "lane_local_hierarchy_sr_absent_ps_restored",
    "memory_genes": "bidirectional_value_copy_owner_replace",
}
EXPECTED_LANE_VERDICTS = {
    "position": {"sr": "restored", "ps": "restored"},
    "energy": {"sr": "restored", "ps": "restored"},
    "health": {"sr": "restored", "ps": "restored"},
    "max_energy": {"sr": "restored", "ps": "restored"},
    "max_health": {"sr": "restored", "ps": "restored"},
    "size_radius": {"sr": "restored", "ps": "restored"},
    "velocity_acceleration": {"sr": "restored", "ps": "restored"},
    "developmental_profile": {"sr": "restored", "ps": "restored"},
    "social_enabled": {"sr": "restored", "ps": "restored"},
    "active_visible_state": {"sr": "restored", "ps": "restored"},
    "render_identity": {"sr": "restored", "ps": "lane_owner_absent"},
    "scripts": {"sr": "fail_closed_restore", "ps": "restored"},
    "membrane_component_graph": {"sr": "restored", "ps": "restored"},
    "hierarchy": {"sr": "lane_owner_absent", "ps": "restored"},
    "memory_genes": {"sr": "restored", "ps": "restored"},
}
DECLARED_OWNER_ABSENCES = (
    {"field": "hierarchy", "lane": "sr"},
    {"field": "render_identity", "lane": "ps"},
)
LIVE_PRESERVED_FAIL_CLOSED_CELLS = ({"field": "scripts", "lane": "sr"},)
NONPORTABLE_OWNER_BOUNDARIES = ("scripts:sr",)
RESOLVED_FIELD_BLOCKERS = (
    "cross_lane_behavior_authority_not_admitted",
    "lane_local_hierarchy_and_render_identity_not_cross_lane",
    "sr_executable_scripts_not_portable",
)
PROOF_FIELDS = (
    "field_authority_valid",
    "behavior_authority_valid",
    "field_set_exact",
    "disposition_set_exact",
    "expected_lane_verdicts_match",
    "no_silent_loss",
    "declared_owner_absences_preserved",
    "live_fail_closed_owner_preserved",
    "lane_local_routes_preserved",
    "creation_and_spawn_boundaries_preserved",
    "mapper_paths_match",
)
CLOSED_ADMISSION_FIELDS = (
    "lossless",
    "cross_lane_behavior_admitted",
    "behavior_equivalence_admitted",
    "tick_merge_admitted",
    "replay_admitted",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "lossless_policy",
    "field_roundtrip_witness",
    "behavior_equivalence_witness",
    "field_witness_digest",
    "behavior_witness_digest",
    "field_disposition_matrix",
    "silent_loss_cells",
    "nonportable_owner_boundaries",
    "portable_checkpoint_lossless",
    "lossless_mapping_result_digest",
    *PROOF_FIELDS,
    "remaining_lossless_blockers",
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


def _field_cells(
    field_witness: Mapping[str, Any],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    result = field_witness.get("field_roundtrip_result")
    matrix = result.get("matrix") if isinstance(result, Mapping) else None
    if not isinstance(matrix, list):
        return {}
    cells: dict[tuple[str, str], Mapping[str, Any]] = {}
    for item in matrix:
        if not isinstance(item, Mapping):
            continue
        field = item.get("field")
        lane = item.get("lane")
        if isinstance(field, str) and lane in {"sr", "ps"}:
            cells[(field, str(lane))] = item
    return cells


def _disposition_matrix(
    cells: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for field in MAPPING_FIELDS:
        matrix.append(
            {
                "field": field,
                "disposition": FIELD_DISPOSITIONS[field],
                "mapper_paths": list(WORLD_BRIDGE_LIVE_MAPPER_PATHS[field]),
                "lanes": {
                    lane: {
                        "verdict": cells.get((field, lane), {}).get("verdict"),
                        "live_preserved_on_reject": cells.get(
                            (field, lane), {}
                        ).get("live_preserved_on_reject"),
                    }
                    for lane in ("sr", "ps")
                },
            }
        )
    return matrix


def _evaluate(
    *,
    field_witness: Mapping[str, Any],
    behavior_witness: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    field_validation = validate_worldbridge_e557_field_roundtrip_authority(
        field_witness
    )
    field_authority_valid = field_validation == {
        "valid": True,
        "errors": [],
    }
    if not field_authority_valid:
        errors.extend(
            f"field_{item}" for item in field_validation["errors"]
        )

    behavior_validation = (
        validate_worldbridge_e560_behavior_equivalence_authority(
            behavior_witness
        )
    )
    behavior_authority_valid = behavior_validation == {
        "valid": True,
        "errors": [],
    }
    if not behavior_authority_valid:
        errors.extend(
            f"behavior_{item}" for item in behavior_validation["errors"]
        )

    cells = _field_cells(field_witness)
    field_set_exact = set(FIELD_DISPOSITIONS) == set(MAPPING_FIELDS)
    disposition_set_exact = set(WORLD_BRIDGE_LIVE_MAPPER_PATHS) == set(
        MAPPING_FIELDS
    )
    if not field_set_exact:
        errors.append("lossless_field_set_mismatch")
    if not disposition_set_exact:
        errors.append("lossless_disposition_set_mismatch")

    expected_cell_keys = {
        (field, lane) for field in MAPPING_FIELDS for lane in ("sr", "ps")
    }
    if set(cells) != expected_cell_keys:
        errors.append("lossless_cell_matrix_incomplete")

    expected_lane_verdicts_match = True
    silent_loss_cells: list[dict[str, str]] = []
    for field in MAPPING_FIELDS:
        for lane in ("sr", "ps"):
            cell = cells.get((field, lane))
            expected = EXPECTED_LANE_VERDICTS[field][lane]
            actual = cell.get("verdict") if isinstance(cell, Mapping) else None
            if actual != expected:
                expected_lane_verdicts_match = False
                silent_loss_cells.append({"field": field, "lane": lane})
                errors.append(
                    "lossless_lane_verdict_mismatch:"
                    f"{field}:{lane}={actual!r},expected={expected!r}"
                )
    if not expected_lane_verdicts_match:
        errors.append("lossless_lane_verdict_mismatch")

    absent = [
        {"field": field, "lane": lane}
        for (field, lane), cell in cells.items()
        if str(cell.get("verdict", "")).startswith(
            ("owner_absent", "lane_owner_absent")
        )
    ]
    declared_owner_absences_preserved = (
        sorted(absent, key=lambda item: (item["field"], item["lane"]))
        == sorted(
            DECLARED_OWNER_ABSENCES,
            key=lambda item: (item["field"], item["lane"]),
        )
    )
    if not declared_owner_absences_preserved:
        errors.append("unexpected_lossless_owner_absences")

    fail_closed = [
        {"field": field, "lane": lane}
        for (field, lane), cell in cells.items()
        if cell.get("verdict") == "fail_closed_restore"
    ]
    live_fail_closed_owner_preserved = (
        fail_closed
        == [dict(item) for item in LIVE_PRESERVED_FAIL_CLOSED_CELLS]
        and cells.get(("scripts", "sr"), {}).get("live_preserved_on_reject")
        is True
    )
    if not live_fail_closed_owner_preserved:
        errors.append("lossless_fail_closed_owner_not_preserved")

    lane_local_routes = behavior_witness.get("lane_local_behavior_routes")
    lane_local_routes_preserved = (
        behavior_witness.get("eligible_behavior_routes")
        == list(ELIGIBLE_BEHAVIOR_ROUTES)
        and lane_local_routes == LANE_LOCAL_BEHAVIOR_ROUTES
    )
    if not lane_local_routes_preserved:
        errors.append("lossless_lane_local_route_mismatch")

    creation_and_spawn_boundaries_preserved = (
        WORLD_BRIDGE_LIVE_MAPPER_PATHS["max_energy"]
        == ("creation_seed",)
        and WORLD_BRIDGE_LIVE_MAPPER_PATHS["max_health"]
        == ("creation_seed",)
        and WORLD_BRIDGE_LIVE_MAPPER_PATHS["developmental_profile"]
        == ("spawn_profile_seed",)
        and WORLD_BRIDGE_LIVE_MAPPER_PATHS["social_enabled"]
        == ("spawn_profile_seed",)
    )
    if not creation_and_spawn_boundaries_preserved:
        errors.append("lossless_creation_spawn_boundary_mismatch")

    mapper_paths_match = all(
        isinstance(WORLD_BRIDGE_LIVE_MAPPER_PATHS[field], tuple)
        for field in MAPPING_FIELDS
    )
    if not mapper_paths_match:
        errors.append("lossless_mapper_path_inventory_invalid")

    no_silent_loss = (
        not silent_loss_cells
        and field_witness.get("restored_cell_count") == 27
        and field_witness.get("owner_absent_cells")
        == [
            {"field": "hierarchy", "lane": "sr"},
            {"field": "render_identity", "lane": "ps"},
        ]
        and field_witness.get("fail_closed_cells")
        == [{"field": "scripts", "lane": "sr"}]
    )
    if not no_silent_loss:
        errors.append("silent_loss_detected")

    proof = {
        "field_authority_valid": field_authority_valid,
        "behavior_authority_valid": behavior_authority_valid,
        "field_set_exact": field_set_exact,
        "disposition_set_exact": disposition_set_exact,
        "expected_lane_verdicts_match": expected_lane_verdicts_match,
        "no_silent_loss": no_silent_loss,
        "declared_owner_absences_preserved": (
            declared_owner_absences_preserved
        ),
        "live_fail_closed_owner_preserved": (
            live_fail_closed_owner_preserved
        ),
        "lane_local_routes_preserved": lane_local_routes_preserved,
        "creation_and_spawn_boundaries_preserved": (
            creation_and_spawn_boundaries_preserved
        ),
        "mapper_paths_match": mapper_paths_match,
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")

    result_payload = {
        "field_disposition_matrix": _disposition_matrix(cells),
        "silent_loss_cells": silent_loss_cells,
        "nonportable_owner_boundaries": list(
            NONPORTABLE_OWNER_BOUNDARIES
        ),
        "portable_checkpoint_lossless": False,
    }
    return list(dict.fromkeys(errors)), {
        **proof,
        **result_payload,
        "field_witness_digest": field_witness.get("witness_digest"),
        "behavior_witness_digest": behavior_witness.get("witness_digest"),
        "lossless_mapping_result_digest": _digest(result_payload),
    }


def build_worldbridge_e561_lossless_mapping_authority(
    *,
    field_roundtrip_witness: Mapping[str, Any],
    behavior_equivalence_witness: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a declared-no-silent-loss mapping witness."""
    field_witness = _mapping_copy(
        field_roundtrip_witness,
        "field_roundtrip_witness",
    )
    behavior_witness = _mapping_copy(
        behavior_equivalence_witness,
        "behavior_equivalence_witness",
    )
    errors, projection = _evaluate(
        field_witness=field_witness,
        behavior_witness=behavior_witness,
    )
    if errors:
        raise ValueError(
            "E561 lossless mapping witness rejected: "
            + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "lossless_policy": LOSSLESS_POLICY,
        "field_roundtrip_witness": field_witness,
        "behavior_equivalence_witness": behavior_witness,
        **projection,
        "remaining_lossless_blockers": [],
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e561_lossless_mapping_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute all field dispositions from the embedded producers."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if set(value) != set(WITNESS_KEYS):
        errors.append("witness_keys_invalid")
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {
            "valid": False,
            "errors": errors + ["witness_not_canonical_json"],
        }
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("lossless_policy") != LOSSLESS_POLICY:
        errors.append("lossless_policy_mismatch")

    field_witness = value.get("field_roundtrip_witness")
    behavior_witness = value.get("behavior_equivalence_witness")
    if not isinstance(field_witness, Mapping) or not isinstance(
        behavior_witness,
        Mapping,
    ):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, projection = _evaluate(
        field_witness=field_witness,
        behavior_witness=behavior_witness,
    )
    errors.extend(revalidation)
    for field, expected in projection.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("remaining_lossless_blockers") != []:
        errors.append("remaining_lossless_blockers_mismatch")
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
    "DECLARED_OWNER_ABSENCES",
    "EXPECTED_LANE_VERDICTS",
    "FIELD_DISPOSITIONS",
    "LIVE_PRESERVED_FAIL_CLOSED_CELLS",
    "LOSSLESS_POLICY",
    "NONPORTABLE_OWNER_BOUNDARIES",
    "PROOF_FIELDS",
    "RESOLVED_FIELD_BLOCKERS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e561_lossless_mapping_authority",
    "validate_worldbridge_e561_lossless_mapping_authority",
]
