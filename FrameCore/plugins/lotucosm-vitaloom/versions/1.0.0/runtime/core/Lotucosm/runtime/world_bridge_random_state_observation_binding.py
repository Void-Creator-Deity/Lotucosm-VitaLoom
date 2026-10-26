# -*- coding: utf-8 -*-
"""Bind one sealed E220 artifact to explicit pre/post E221 RNG observations."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
from collections.abc import Mapping
from typing import Any

import numpy as np

from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
    validate_worldbridge_live_capture_artifact,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    CAPTURED_AUTHORITY_IDS,
    UNCAPTURED_AUTHORITY_IDS,
    _build_capture_from_states,
    validate_worldbridge_global_random_state_capture,
)


SCHEMA_VERSION = 1
BINDING_KIND = "worldbridge_pre_post_random_state_observation_binding"
_BINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

BOUNDARY_SEMANTICS = {
    "before": "caller_observed_before_bound_diagnostic_interval",
    "after": "caller_observed_after_bound_diagnostic_interval",
    "interval_relationship": "caller_asserted_not_clock_verified",
}

_BINDING_KEYS = {
    "schema_version",
    "binding_kind",
    "binding_id",
    "read_only",
    "artifact_id",
    "artifact_digest",
    "session_id",
    "session_digest",
    "artifact",
    "boundary_semantics",
    "before_capture_id",
    "before_capture_digest",
    "after_capture_id",
    "after_capture_digest",
    "boundaries",
    "authority_changes",
    "changed_authority_ids",
    "unchanged_authority_ids",
    "uncaptured_authority_ids",
    "draw_counts_inferred",
    "lane_attribution_inferred",
    "cross_lane_consumption_order_captured",
    "supported_globals_prove_entropy_closure",
    "clocks_compared",
    "time_aligned",
    "causality_inferred",
    "thread_atomic",
    "cross_authority_atomic",
    "atomic_checkpoint",
    "replay_input",
    "checkpoint_state",
    "lossless",
    "replay_admitted",
    "default_ready",
    "binding_digest",
}

_CHANGE_KEYS = {
    "authority_id",
    "before_state_digest",
    "after_state_digest",
    "classification",
}

_FALSE_CLAIMS = (
    "draw_counts_inferred",
    "lane_attribution_inferred",
    "cross_lane_consumption_order_captured",
    "supported_globals_prove_entropy_closure",
    "clocks_compared",
    "time_aligned",
    "causality_inferred",
    "thread_atomic",
    "cross_authority_atomic",
    "atomic_checkpoint",
    "replay_input",
    "checkpoint_state",
    "lossless",
    "replay_admitted",
    "default_ready",
)


def build_worldbridge_random_state_observation_binding(
    artifact: Mapping[str, Any],
    before_capture: Mapping[str, Any],
    after_capture: Mapping[str, Any],
    *,
    binding_id: str,
) -> dict[str, Any]:
    """Build an immutable diagnostic binding from validated nested evidence."""
    clean_id = _clean_binding_id(binding_id)
    artifact_copy = _validated_artifact_copy(artifact)
    before_copy = _validated_capture_copy(before_capture, boundary="before")
    after_copy = _validated_capture_copy(after_capture, boundary="after")
    if before_copy["capture_id"] == after_copy["capture_id"]:
        raise ValueError("before and after capture_id values must be distinct")

    changes = _build_authority_changes(before_copy, after_copy)
    changed_ids = [
        row["authority_id"] for row in changes if row["classification"] == "changed"
    ]
    unchanged_ids = [
        row["authority_id"] for row in changes if row["classification"] == "unchanged"
    ]
    binding: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "binding_kind": BINDING_KIND,
        "binding_id": clean_id,
        "read_only": True,
        "artifact_id": artifact_copy["artifact_id"],
        "artifact_digest": artifact_copy["artifact_digest"],
        "session_id": artifact_copy["session_id"],
        "session_digest": artifact_copy["session_digest"],
        "artifact": artifact_copy,
        "boundary_semantics": copy.deepcopy(BOUNDARY_SEMANTICS),
        "before_capture_id": before_copy["capture_id"],
        "before_capture_digest": before_copy["capture_digest"],
        "after_capture_id": after_copy["capture_id"],
        "after_capture_digest": after_copy["capture_digest"],
        "boundaries": {
            "before": before_copy,
            "after": after_copy,
        },
        "authority_changes": changes,
        "changed_authority_ids": changed_ids,
        "unchanged_authority_ids": unchanged_ids,
        "uncaptured_authority_ids": list(UNCAPTURED_AUTHORITY_IDS),
        "draw_counts_inferred": False,
        "lane_attribution_inferred": False,
        "cross_lane_consumption_order_captured": False,
        "supported_globals_prove_entropy_closure": False,
        "clocks_compared": False,
        "time_aligned": False,
        "causality_inferred": False,
        "thread_atomic": False,
        "cross_authority_atomic": False,
        "atomic_checkpoint": False,
        "replay_input": False,
        "checkpoint_state": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "binding_digest": "",
    }
    binding["binding_digest"] = _binding_digest(binding)
    validation = validate_worldbridge_random_state_observation_binding(binding)
    if validation != {"valid": True, "errors": []}:
        raise RuntimeError(f"invalid observation binding produced: {validation['errors']}")
    return copy.deepcopy(binding)


def validate_worldbridge_random_state_observation_binding(binding: object) -> dict[str, Any]:
    """Validate E222 nested evidence and semantic limits without raising."""
    errors: list[str] = []
    if not isinstance(binding, Mapping):
        return {"valid": False, "errors": ["binding_not_mapping"]}

    try:
        keys = set(binding.keys())
    except Exception:
        return {"valid": False, "errors": ["binding_keys_invalid"]}
    if keys != _BINDING_KEYS:
        errors.append("binding_keys_mismatch")
    if binding.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if binding.get("binding_kind") != BINDING_KIND:
        errors.append("binding_kind_mismatch")
    try:
        _clean_binding_id(binding.get("binding_id"))
    except ValueError:
        errors.append("binding_id_invalid")
    if binding.get("read_only") is not True:
        errors.append("read_only_mismatch")
    if binding.get("boundary_semantics") != BOUNDARY_SEMANTICS:
        errors.append("boundary_semantics_mismatch")
    if binding.get("uncaptured_authority_ids") != list(UNCAPTURED_AUTHORITY_IDS):
        errors.append("uncaptured_authority_ids_mismatch")
    for field in _FALSE_CLAIMS:
        if binding.get(field) is not False:
            errors.append(f"{field}_mismatch")

    artifact = binding.get("artifact")
    artifact_valid = False
    if not isinstance(artifact, Mapping):
        errors.append("artifact_not_mapping")
    else:
        artifact_validation = validate_worldbridge_live_capture_artifact(artifact)
        artifact_valid = artifact_validation == {"valid": True, "errors": []}
        if not artifact_valid:
            errors.append("artifact_invalid")
        for field in ("artifact_id", "artifact_digest", "session_id", "session_digest"):
            if binding.get(field) != artifact.get(field):
                errors.append(f"{field}_reference_mismatch")

    boundaries = binding.get("boundaries")
    before: Mapping[str, Any] | None = None
    after: Mapping[str, Any] | None = None
    captures_valid = False
    if not isinstance(boundaries, Mapping):
        errors.append("boundaries_not_mapping")
    else:
        try:
            boundary_keys = set(boundaries.keys())
        except Exception:
            boundary_keys = set()
            errors.append("boundary_keys_invalid")
        if boundary_keys != {"before", "after"}:
            errors.append("boundary_keys_mismatch")
        candidate_before = boundaries.get("before")
        candidate_after = boundaries.get("after")
        if isinstance(candidate_before, Mapping):
            before = candidate_before
        else:
            errors.append("before_capture_not_mapping")
        if isinstance(candidate_after, Mapping):
            after = candidate_after
        else:
            errors.append("after_capture_not_mapping")
        before_valid = (
            before is not None
            and validate_worldbridge_global_random_state_capture(before)
            == {"valid": True, "errors": []}
        )
        after_valid = (
            after is not None
            and validate_worldbridge_global_random_state_capture(after)
            == {"valid": True, "errors": []}
        )
        if not before_valid:
            errors.append("before_capture_invalid")
        if not after_valid:
            errors.append("after_capture_invalid")
        captures_valid = bool(before_valid and after_valid)

    if before is not None:
        if binding.get("before_capture_id") != before.get("capture_id"):
            errors.append("before_capture_id_reference_mismatch")
        if binding.get("before_capture_digest") != before.get("capture_digest"):
            errors.append("before_capture_digest_reference_mismatch")
    if after is not None:
        if binding.get("after_capture_id") != after.get("capture_id"):
            errors.append("after_capture_id_reference_mismatch")
        if binding.get("after_capture_digest") != after.get("capture_digest"):
            errors.append("after_capture_digest_reference_mismatch")
    if before is not None and after is not None and before.get("capture_id") == after.get("capture_id"):
        errors.append("boundary_capture_ids_not_distinct")

    if captures_valid and before is not None and after is not None:
        expected_changes = _build_authority_changes(before, after)
        if binding.get("authority_changes") != expected_changes:
            errors.append("authority_changes_mismatch")
        expected_changed = [
            row["authority_id"]
            for row in expected_changes
            if row["classification"] == "changed"
        ]
        expected_unchanged = [
            row["authority_id"]
            for row in expected_changes
            if row["classification"] == "unchanged"
        ]
        if binding.get("changed_authority_ids") != expected_changed:
            errors.append("changed_authority_ids_mismatch")
        if binding.get("unchanged_authority_ids") != expected_unchanged:
            errors.append("unchanged_authority_ids_mismatch")
    else:
        _validate_change_shape(binding.get("authority_changes"), errors)

    digest = binding.get("binding_digest")
    if not _is_sha256(digest):
        errors.append("binding_digest_invalid")
    try:
        expected_digest = _binding_digest(binding)
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("binding_not_canonical_json")
    if expected_digest is not None and digest != expected_digest:
        errors.append("binding_digest_mismatch")

    return {"valid": not errors, "errors": errors}


def build_worldbridge_random_state_observation_binding_contract() -> dict[str, Any]:
    """Build deterministic E222 runtime evidence without observing global RNGs."""
    from core.Lotucosm.runtime.world_bridge_live_capture_artifact import (
        build_worldbridge_live_capture_artifact_contract,
    )

    artifact = build_worldbridge_live_capture_artifact_contract()["artifact"]
    python_before_rng = random.Random(222)
    python_after_rng = random.Random(222)
    python_after_rng.random()
    numpy_before_rng = np.random.RandomState(222)
    numpy_after_rng = np.random.RandomState(222)
    before = _build_capture_from_states(
        capture_id="e222-before-example",
        python_state=python_before_rng.getstate(),
        numpy_state=numpy_before_rng.get_state(),
    )
    after = _build_capture_from_states(
        capture_id="e222-after-example",
        python_state=python_after_rng.getstate(),
        numpy_state=numpy_after_rng.get_state(),
    )
    binding = build_worldbridge_random_state_observation_binding(
        artifact,
        before,
        after,
        binding_id="e222-contract-example",
    )
    validation = validate_worldbridge_random_state_observation_binding(binding)
    return {
        "schema_version": SCHEMA_VERSION,
        "contract": "worldbridge_pre_post_random_state_observation_binding",
        "read_only": True,
        "qt_free": True,
        "status_construction_reads_global_rng_state": False,
        "status_construction_advances_global_rng_state": False,
        "supported_authority_ids": list(CAPTURED_AUTHORITY_IDS),
        "uncaptured_authority_ids": list(UNCAPTURED_AUTHORITY_IDS),
        "classification_values": ["changed", "unchanged"],
        "binding": binding,
        "binding_validation": validation,
        "draw_counts_inferred": False,
        "lane_attribution_inferred": False,
        "cross_lane_consumption_order_captured": False,
        "supported_globals_prove_entropy_closure": False,
        "clocks_compared": False,
        "time_aligned": False,
        "causality_inferred": False,
        "atomic_checkpoint": False,
        "replay_admitted": False,
        "default_ready": False,
        "contract_valid": validation == {"valid": True, "errors": []},
    }


def _validated_artifact_copy(artifact: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_worldbridge_live_capture_artifact(artifact)
    if validation != {"valid": True, "errors": []}:
        raise ValueError(f"artifact must be a validated sealed E220 artifact: {validation['errors']}")
    return copy.deepcopy(dict(artifact))


def _validated_capture_copy(capture: Mapping[str, Any], *, boundary: str) -> dict[str, Any]:
    validation = validate_worldbridge_global_random_state_capture(capture)
    if validation != {"valid": True, "errors": []}:
        raise ValueError(f"{boundary} capture must be a validated E221 capture: {validation['errors']}")
    return copy.deepcopy(dict(capture))


def _build_authority_changes(
    before_capture: Mapping[str, Any],
    after_capture: Mapping[str, Any],
) -> list[dict[str, str]]:
    before_authorities = before_capture["authorities"]
    after_authorities = after_capture["authorities"]
    changes: list[dict[str, str]] = []
    for authority_id in CAPTURED_AUTHORITY_IDS:
        before_state = before_authorities[authority_id]
        after_state = after_authorities[authority_id]
        before_digest = hashlib.sha256(_canonical_json_bytes(before_state)).hexdigest()
        after_digest = hashlib.sha256(_canonical_json_bytes(after_state)).hexdigest()
        changes.append(
            {
                "authority_id": authority_id,
                "before_state_digest": before_digest,
                "after_state_digest": after_digest,
                "classification": "unchanged" if before_state == after_state else "changed",
            }
        )
    return changes


def _validate_change_shape(value: object, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != len(CAPTURED_AUTHORITY_IDS):
        errors.append("authority_changes_shape_invalid")
        return
    for row in value:
        if not isinstance(row, Mapping):
            errors.append("authority_change_not_mapping")
            continue
        try:
            keys = set(row.keys())
        except Exception:
            errors.append("authority_change_keys_invalid")
            continue
        if keys != _CHANGE_KEYS:
            errors.append("authority_change_keys_mismatch")
        if row.get("classification") not in {"changed", "unchanged"}:
            errors.append("authority_change_classification_invalid")
        for field in ("before_state_digest", "after_state_digest"):
            if not _is_sha256(row.get(field)):
                errors.append(f"authority_change_{field}_invalid")


def _clean_binding_id(value: object) -> str:
    if not isinstance(value, str) or _BINDING_ID_RE.fullmatch(value) is None:
        raise ValueError("binding_id must be a clean 1-128 character identifier")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _binding_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical["binding_digest"] = ""
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


__all__ = [
    "BINDING_KIND",
    "BOUNDARY_SEMANTICS",
    "SCHEMA_VERSION",
    "build_worldbridge_random_state_observation_binding",
    "build_worldbridge_random_state_observation_binding_contract",
    "validate_worldbridge_random_state_observation_binding",
]
