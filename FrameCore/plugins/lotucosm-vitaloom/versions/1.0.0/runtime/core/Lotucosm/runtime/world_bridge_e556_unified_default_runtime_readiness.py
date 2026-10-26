# -*- coding: utf-8 -*-
"""Default-runtime readiness on top of full replay authority.

E556 proves that default configuration remains safely dual, unified Pond is
entered only by explicit project configuration, and the resulting single-host
runtime consumes the same scheduler/tick/RNG owners for multiple real ticks.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge import (
    RUNTIME_MODE_DUAL,
    RUNTIME_MODE_UNIFIED,
    resolve_runtime_mode,
    unified_pond_enabled,
)
from .world_bridge_e555_full_unified_runtime_replay_authority import (
    validate_worldbridge_e555_full_unified_runtime_replay_authority,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e556_unified_default_runtime_readiness"
SCOPE = "explicit_unified_mode_readiness_with_safe_dual_default"
ADMISSION_EFFECT = "none"
MINIMUM_LIVE_TICK_COUNT = 3
PROOF_FIELDS = (
    "replay_authority_valid",
    "default_mode_remains_dual",
    "invalid_mode_falls_back_to_dual",
    "explicit_unified_mode_selected",
    "live_unified_mode_entered",
    "live_tick_count_sufficient",
    "tick_sequence_continuous",
    "receipts_unique",
    "pond_advanced_each_tick",
    "scheduler_owner_continuous",
    "rng_context_continuous",
    "reference_backend_selected",
    "no_fallback_observed",
    "no_duplicate_tick_authority",
    "project_binding_matches_replay",
)
CLOSED_ADMISSION_FIELDS = (
    "default_ready",
    "tick_merge_admitted",
    "cross_lane_behavior_admitted",
    "lossless",
)
UNIFIED_MODE_KEYS = {
    "project_binding",
    "resolved_runtime_mode",
    "unified_pond_enabled",
    "tick_authority_sequence",
    "scheduler_snapshot",
    "rng_context_id",
    "native_backend_selection",
    "tick_receipts",
    "fallback_used",
    "duplicate_tick_authority_detected",
}
TICK_RECEIPT_KEYS = {
    "tick_sequence",
    "decision_digest",
    "receipt_digest",
    "rng_context_id",
    "pond_time_before",
    "pond_time_after",
}
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "full_unified_replay_witness",
    "runtime_mode_policy",
    "unified_mode_evidence",
    "replay_witness_digest",
    "project_binding_digest",
    "live_tick_count",
    "tick_sequences",
    *PROOF_FIELDS,
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


def _runtime_mode_policy() -> dict[str, Any]:
    samples = {
        "missing_config": None,
        "default_mode": {},
        "invalid_mode": {"runtime_mode": "unregistered_mode"},
        "explicit_dual": {"runtime_mode": RUNTIME_MODE_DUAL},
        "explicit_unified": {"runtime_mode": RUNTIME_MODE_UNIFIED},
    }
    results = {
        name: {
            "resolved_mode": resolve_runtime_mode(config),
            "unified_enabled": unified_pond_enabled(config),
        }
        for name, config in samples.items()
    }
    return {
        "default_runtime_mode": RUNTIME_MODE_DUAL,
        "unified_runtime_mode": RUNTIME_MODE_UNIFIED,
        "samples": results,
    }


def _evaluate(
    *,
    replay_witness: Mapping[str, Any],
    unified_mode: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    replay_validation = (
        validate_worldbridge_e555_full_unified_runtime_replay_authority(
            replay_witness
        )
    )
    replay_authority_valid = (
        replay_validation == {"valid": True, "errors": []}
    )
    if not replay_authority_valid:
        errors.extend(f"replay_{item}" for item in replay_validation["errors"])

    policy = _runtime_mode_policy()
    samples = policy["samples"]
    default_mode_remains_dual = (
        samples["missing_config"]["resolved_mode"] == RUNTIME_MODE_DUAL
        and samples["missing_config"]["unified_enabled"] is False
        and samples["default_mode"]["resolved_mode"] == RUNTIME_MODE_DUAL
        and samples["default_mode"]["unified_enabled"] is False
        and samples["explicit_dual"]["resolved_mode"] == RUNTIME_MODE_DUAL
        and samples["explicit_dual"]["unified_enabled"] is False
    )
    invalid_mode_falls_back_to_dual = (
        samples["invalid_mode"]["resolved_mode"] == RUNTIME_MODE_DUAL
        and samples["invalid_mode"]["unified_enabled"] is False
    )
    explicit_unified_mode_selected = (
        samples["explicit_unified"]["resolved_mode"] == RUNTIME_MODE_UNIFIED
        and samples["explicit_unified"]["unified_enabled"] is True
    )
    if not default_mode_remains_dual:
        errors.append("default_mode_not_dual")
    if not invalid_mode_falls_back_to_dual:
        errors.append("invalid_mode_not_fail_closed")
    if not explicit_unified_mode_selected:
        errors.append("explicit_unified_mode_not_selected")

    if set(unified_mode) != UNIFIED_MODE_KEYS:
        errors.append("unified_mode_evidence_keys_invalid")
    live_unified_mode_entered = (
        unified_mode.get("resolved_runtime_mode") == RUNTIME_MODE_UNIFIED
        and unified_mode.get("unified_pond_enabled") is True
    )
    if not live_unified_mode_entered:
        errors.append("live_unified_mode_not_entered")

    replay_artifact = replay_witness.get("e533_artifact")
    replay_project_binding = (
        replay_artifact.get("project_binding")
        if isinstance(replay_artifact, Mapping)
        else None
    )
    project_binding_matches_replay = (
        isinstance(replay_project_binding, Mapping)
        and unified_mode.get("project_binding") == dict(replay_project_binding)
    )
    if not project_binding_matches_replay:
        errors.append("project_binding_replay_mismatch")

    ticks = unified_mode.get("tick_receipts")
    if not isinstance(ticks, list):
        errors.append("tick_receipts_invalid")
        ticks = []
    live_tick_count = len(ticks)
    live_tick_count_sufficient = live_tick_count >= MINIMUM_LIVE_TICK_COUNT
    if not live_tick_count_sufficient:
        errors.append("live_tick_count_insufficient")

    tick_sequences: list[int] = []
    receipts_unique = True
    pond_advanced_each_tick = True
    receipt_rng_ids: set[str] = set()
    receipt_digests: set[str] = set()
    for index, receipt in enumerate(ticks):
        if not isinstance(receipt, Mapping) or set(receipt) != TICK_RECEIPT_KEYS:
            errors.append(f"tick_receipt_{index}_schema_invalid")
            receipts_unique = False
            pond_advanced_each_tick = False
            continue
        sequence = receipt.get("tick_sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            errors.append(f"tick_receipt_{index}_sequence_invalid")
            continue
        tick_sequences.append(sequence)
        for field in ("decision_digest", "receipt_digest"):
            if (
                not isinstance(receipt.get(field), str)
                or _DIGEST_RE.fullmatch(receipt[field]) is None
            ):
                errors.append(f"tick_receipt_{index}_{field}_invalid")
        digest = receipt.get("receipt_digest")
        if digest in receipt_digests:
            receipts_unique = False
        receipt_digests.add(digest)
        rng_context_id = receipt.get("rng_context_id")
        if not isinstance(rng_context_id, str) or not rng_context_id:
            errors.append(f"tick_receipt_{index}_rng_context_invalid")
        else:
            receipt_rng_ids.add(rng_context_id)
        before = receipt.get("pond_time_before")
        after = receipt.get("pond_time_after")
        if (
            isinstance(before, bool)
            or not isinstance(before, int)
            or isinstance(after, bool)
            or not isinstance(after, int)
            or after != before + 1
        ):
            pond_advanced_each_tick = False
    expected_sequences = (
        list(range(1, live_tick_count + 1))
        if live_tick_count
        else []
    )
    tick_sequence_continuous = tick_sequences == expected_sequences
    authority_sequence = unified_mode.get("tick_authority_sequence")
    if (
        tick_sequence_continuous
        and authority_sequence != (tick_sequences[-1] if tick_sequences else 0)
    ):
        tick_sequence_continuous = False
    if not tick_sequence_continuous:
        errors.append("tick_sequence_not_continuous")
    if not receipts_unique:
        errors.append("tick_receipts_not_unique")
    if not pond_advanced_each_tick:
        errors.append("pond_not_advanced_each_tick")

    scheduler = unified_mode.get("scheduler_snapshot")
    scheduler_owner_continuous = (
        isinstance(scheduler, Mapping)
        and isinstance(scheduler.get("scheduler_owner_id"), str)
        and bool(scheduler.get("scheduler_owner_id"))
        and scheduler.get("accepted_count", 0) >= 0
        and scheduler.get("rejected_count", 0) >= 0
    )
    if not scheduler_owner_continuous:
        errors.append("scheduler_owner_missing")

    rng_context_id = unified_mode.get("rng_context_id")
    rng_context_continuous = (
        isinstance(rng_context_id, str)
        and bool(rng_context_id)
        and receipt_rng_ids == {rng_context_id}
    )
    if not rng_context_continuous:
        errors.append("rng_context_not_continuous")

    backend = unified_mode.get("native_backend_selection")
    reference_backend_selected = (
        isinstance(backend, Mapping)
        and backend.get("selected_backend_id") == "python"
        and backend.get("status") == "reference_python"
    )
    if not reference_backend_selected:
        errors.append("reference_backend_not_selected")

    no_fallback_observed = unified_mode.get("fallback_used") is False
    if not no_fallback_observed:
        errors.append("fallback_observed")
    no_duplicate_tick_authority = (
        unified_mode.get("duplicate_tick_authority_detected") is False
    )
    if not no_duplicate_tick_authority:
        errors.append("duplicate_tick_authority_observed")

    projection = {
        "replay_witness_digest": replay_witness.get("witness_digest"),
        "project_binding_digest": (
            _digest(unified_mode.get("project_binding"))
            if isinstance(unified_mode.get("project_binding"), Mapping)
            else None
        ),
        "live_tick_count": live_tick_count,
        "tick_sequences": tick_sequences,
        "replay_authority_valid": replay_authority_valid,
        "default_mode_remains_dual": default_mode_remains_dual,
        "invalid_mode_falls_back_to_dual": invalid_mode_falls_back_to_dual,
        "explicit_unified_mode_selected": explicit_unified_mode_selected,
        "live_unified_mode_entered": live_unified_mode_entered,
        "live_tick_count_sufficient": live_tick_count_sufficient,
        "tick_sequence_continuous": tick_sequence_continuous,
        "receipts_unique": receipts_unique,
        "pond_advanced_each_tick": pond_advanced_each_tick,
        "scheduler_owner_continuous": scheduler_owner_continuous,
        "rng_context_continuous": rng_context_continuous,
        "reference_backend_selected": reference_backend_selected,
        "no_fallback_observed": no_fallback_observed,
        "no_duplicate_tick_authority": no_duplicate_tick_authority,
        "project_binding_matches_replay": project_binding_matches_replay,
    }
    return list(dict.fromkeys(errors)), {
        **projection,
        "runtime_mode_policy": policy,
    }


def build_worldbridge_e556_unified_default_runtime_readiness(
    *,
    full_unified_replay_witness: Mapping[str, Any],
    unified_mode_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build default-readiness evidence while keeping runtime_mode default dual."""
    replay = _mapping_copy(
        full_unified_replay_witness,
        "full_unified_replay_witness",
    )
    unified = _mapping_copy(unified_mode_evidence, "unified_mode_evidence")
    errors, payload = _evaluate(
        replay_witness=replay,
        unified_mode=unified,
    )
    if errors:
        raise ValueError(
            "E556 default readiness rejected: " + ",".join(errors)
        )
    policy = payload.pop("runtime_mode_policy")
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "full_unified_replay_witness": replay,
        "runtime_mode_policy": policy,
        "unified_mode_evidence": unified,
        **payload,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e556_unified_default_runtime_readiness(
    value: object,
) -> dict[str, Any]:
    """Recompute policy, replay and live-mode evidence without overclaiming."""
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

    replay = value.get("full_unified_replay_witness")
    unified = value.get("unified_mode_evidence")
    if not isinstance(replay, Mapping) or not isinstance(unified, Mapping):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    revalidation, payload = _evaluate(
        replay_witness=replay,
        unified_mode=unified,
    )
    errors.extend(revalidation)
    policy = payload.pop("runtime_mode_policy")
    if value.get("runtime_mode_policy") != policy:
        errors.append("runtime_mode_policy_mismatch")
    for field, expected in payload.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
        if field in PROOF_FIELDS and value.get(field) is not True:
            errors.append(f"{field}_not_true")
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
    "MINIMUM_LIVE_TICK_COUNT",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "TICK_RECEIPT_KEYS",
    "UNIFIED_MODE_KEYS",
    "WITNESS_KEYS",
    "build_worldbridge_e556_unified_default_runtime_readiness",
    "validate_worldbridge_e556_unified_default_runtime_readiness",
]
