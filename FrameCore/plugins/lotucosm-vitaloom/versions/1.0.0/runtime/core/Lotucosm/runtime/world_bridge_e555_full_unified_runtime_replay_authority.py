# -*- coding: utf-8 -*-
"""Full unified runtime replay authority over a real E533/E539 host pair.

E555 composes already-admitted shared capabilities with a multi-tick,
source/fresh replay trace. It proves replay authority as evidence only; live
default-runtime readiness remains a separate gate.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .world_bridge_e533_capture_binding import (
    decode_worldbridge_e533_capture_binding,
    encode_worldbridge_e533_capture_binding,
    validate_worldbridge_e533_capture_binding,
)
from .world_bridge_e538_shared_contracts import (
    REQUIREMENT_IDS,
    validate_worldbridge_e538_shared_contract,
)
from .world_bridge_e539_replay_trace_candidate import (
    build_worldbridge_e539_replay_trace_candidate,
    validate_worldbridge_e539_replay_trace_candidate,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e555_full_unified_runtime_replay_authority"
SCOPE = "multi_tick_fresh_host_unified_runtime_replay"
ADMISSION_EFFECT = "none"
MINIMUM_TRACE_COUNT = 3
REPLAY_PRECONDITION_BLOCKERS = (
    "full_unified_runtime_replay_not_proven",
    "unified_default_runtime_readiness_not_proven",
)
PROOF_FIELDS = (
    "artifact_valid",
    "shared_prerequisites_admitted",
    "trace_valid",
    "multi_tick_trace",
    "distinct_runtime_epochs",
    "host_capture_pair_bound",
    "topology_tick_bound",
    "checkpoint_scene_bound",
    "all_tick_portable_state_parity",
    "source_fresh_parity_proven",
    "canonical_artifact_roundtrip",
)
CLOSED_ADMISSION_FIELDS = (
    "replay_admitted",
    "full_unified_replay_admitted",
    "cross_lane_behavior_admitted",
    "tick_merge_admitted",
    "lossless",
    "default_ready",
)
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "e533_artifact",
    "shared_contract",
    "e507_witnesses",
    "e539_trace",
    "artifact_digest",
    "shared_contract_digest",
    "trace_digest",
    "trace_count",
    "source_runtime_epoch",
    "fresh_runtime_epoch",
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


def _sequence_copy(value: object, field: str) -> list[dict[str, Any]]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise TypeError(f"{field} must be a sequence")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise TypeError(f"{field}[{index}] must be a mapping")
        copied = _json_copy(dict(item), f"{field}[{index}]")
        if not isinstance(copied, dict):
            raise TypeError(f"{field}[{index}] must remain a mapping")
        result.append(copied)
    return result


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _precondition_errors(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    validation = validate_worldbridge_e538_shared_contract(contract)
    if validation != {"valid": True, "errors": []}:
        errors.extend(f"contract_{item}" for item in validation["errors"])
        return errors
    requirements = contract.get("requirements")
    if not isinstance(requirements, Mapping):
        return ["contract_requirements_invalid"]
    for requirement_id in REQUIREMENT_IDS:
        requirement = requirements.get(requirement_id)
        if not isinstance(requirement, Mapping):
            errors.append(f"requirement_{requirement_id}_missing")
        elif (
            requirement.get("validated") is not True
            or requirement.get("capability_admitted") is not True
            or requirement.get("blocking") is not False
        ):
            errors.append(f"requirement_{requirement_id}_not_admitted")
    if contract.get("remaining_admission_blockers") != list(
        REPLAY_PRECONDITION_BLOCKERS
    ):
        errors.append("replay_precondition_blockers_mismatch")
    admissions = contract.get("admissions")
    if not isinstance(admissions, Mapping):
        errors.append("contract_admissions_invalid")
    else:
        for field in ("replay_admitted", "full_unified_replay_admitted", "default_ready"):
            if admissions.get(field) is not False:
                errors.append(f"contract_{field}_must_remain_false")
    if contract.get("full_unified_replay_witness") is not None:
        errors.append("precondition_contract_contains_replay_witness")
    return errors


def _evaluate(
    *,
    artifact: Mapping[str, Any],
    shared_contract: Mapping[str, Any],
    e507_witnesses: list[dict[str, Any]],
) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    artifact_validation = validate_worldbridge_e533_capture_binding(artifact)
    artifact_valid = artifact_validation == {"valid": True, "errors": []}
    if not artifact_valid:
        errors.extend(f"artifact_{item}" for item in artifact_validation["errors"])
    precondition_errors = _precondition_errors(shared_contract)
    errors.extend(precondition_errors)
    shared_prerequisites_admitted = not precondition_errors

    try:
        trace = build_worldbridge_e539_replay_trace_candidate(
            e533_artifact=artifact,
            e538_contract=shared_contract,
            e507_witnesses=e507_witnesses,
        )
    except (TypeError, ValueError) as exc:
        errors.append(f"trace_build_failed:{exc}")
        trace = {}
    trace_validation = validate_worldbridge_e539_replay_trace_candidate(
        trace,
        e533_artifact=artifact,
        e538_contract=shared_contract,
        e507_witnesses=e507_witnesses,
    )
    trace_valid = trace_validation == {"valid": True, "errors": []}
    if not trace_valid:
        errors.extend(f"trace_{item}" for item in trace_validation["errors"])

    trace_count = trace.get("trace_count")
    multi_tick_trace = (
        isinstance(trace_count, int)
        and not isinstance(trace_count, bool)
        and trace_count >= MINIMUM_TRACE_COUNT
    )
    if not multi_tick_trace:
        errors.append("multi_tick_trace_too_short")

    source_epoch = trace.get("source_host", {}).get("runtime_epoch") if isinstance(
        trace.get("source_host"), Mapping
    ) else None
    fresh_epoch = trace.get("fresh_host", {}).get("runtime_epoch") if isinstance(
        trace.get("fresh_host"), Mapping
    ) else None
    distinct_runtime_epochs = (
        isinstance(source_epoch, str)
        and isinstance(fresh_epoch, str)
        and bool(source_epoch)
        and bool(fresh_epoch)
        and source_epoch != fresh_epoch
    )
    if not distinct_runtime_epochs:
        errors.append("runtime_epochs_not_distinct")

    host_capture_pair_bound = artifact.get("host_capture_pair_binding_proven") is True
    topology_tick_bound = artifact.get("topology_tick_binding_proven") is True
    checkpoint_scene_bound = artifact.get("checkpoint_scene_binding_proven") is True
    for field, value in (
        ("host_capture_pair_bound", host_capture_pair_bound),
        ("topology_tick_bound", topology_tick_bound),
        ("checkpoint_scene_bound", checkpoint_scene_bound),
    ):
        if value is not True:
            errors.append(f"{field}_not_proven")

    all_tick_portable_state_parity = (
        trace.get("all_portable_state_parity") is True
    )
    source_fresh_parity_proven = (
        trace.get("source_fresh_parity_proven") is True
    )
    if not all_tick_portable_state_parity:
        errors.append("all_tick_portable_state_parity_not_proven")
    if not source_fresh_parity_proven:
        errors.append("source_fresh_parity_not_proven")

    try:
        encoded = encode_worldbridge_e533_capture_binding(artifact)
        decoded = decode_worldbridge_e533_capture_binding(encoded)
        canonical_artifact_roundtrip = decoded == artifact
    except (TypeError, ValueError):
        canonical_artifact_roundtrip = False
    if not canonical_artifact_roundtrip:
        errors.append("canonical_artifact_roundtrip_failed")

    proof = {
        "artifact_valid": artifact_valid,
        "shared_prerequisites_admitted": shared_prerequisites_admitted,
        "trace_valid": trace_valid,
        "multi_tick_trace": multi_tick_trace,
        "distinct_runtime_epochs": distinct_runtime_epochs,
        "host_capture_pair_bound": host_capture_pair_bound,
        "topology_tick_bound": topology_tick_bound,
        "checkpoint_scene_bound": checkpoint_scene_bound,
        "all_tick_portable_state_parity": all_tick_portable_state_parity,
        "source_fresh_parity_proven": source_fresh_parity_proven,
        "canonical_artifact_roundtrip": canonical_artifact_roundtrip,
    }
    projection = {
        "artifact_digest": artifact.get("artifact_digest"),
        "shared_contract_digest": _digest(shared_contract),
        "trace_digest": trace.get("trace_digest"),
        "trace_count": trace_count,
        "source_runtime_epoch": source_epoch,
        "fresh_runtime_epoch": fresh_epoch,
        **proof,
    }
    return list(dict.fromkeys(errors)), projection, trace


def build_worldbridge_e555_full_unified_runtime_replay_authority(
    *,
    e533_artifact: Mapping[str, Any],
    shared_contract: Mapping[str, Any],
    e507_witnesses: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build a detached full-runtime replay witness without default readiness."""
    artifact = _mapping_copy(e533_artifact, "e533_artifact")
    contract = _mapping_copy(shared_contract, "shared_contract")
    witnesses = _sequence_copy(e507_witnesses, "e507_witnesses")
    errors, projection, trace = _evaluate(
        artifact=artifact,
        shared_contract=contract,
        e507_witnesses=witnesses,
    )
    if errors:
        raise ValueError(
            "E555 full replay witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "e533_artifact": artifact,
        "shared_contract": contract,
        "e507_witnesses": witnesses,
        "e539_trace": trace,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e555_full_unified_runtime_replay_authority(
    value: object,
) -> dict[str, Any]:
    """Recompute the replay trace and reject every unearned proof."""
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

    artifact = value.get("e533_artifact")
    contract = value.get("shared_contract")
    raw_witnesses = value.get("e507_witnesses")
    embedded_trace = value.get("e539_trace")
    if not all(
        isinstance(item, Mapping)
        for item in (artifact, contract, embedded_trace)
    ) or not isinstance(raw_witnesses, list):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    if any(not isinstance(item, Mapping) for item in raw_witnesses):
        return {
            "valid": False,
            "errors": errors + ["witness_e507_entries_invalid"],
        }
    witnesses = [dict(item) for item in raw_witnesses]
    revalidation, projection, trace = _evaluate(
        artifact=artifact,
        shared_contract=contract,
        e507_witnesses=witnesses,
    )
    errors.extend(revalidation)
    if embedded_trace != trace:
        errors.append("e539_trace_recompute_mismatch")
    for field, expected in projection.items():
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
    "MINIMUM_TRACE_COUNT",
    "PROOF_FIELDS",
    "REPLAY_PRECONDITION_BLOCKERS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e555_full_unified_runtime_replay_authority",
    "validate_worldbridge_e555_full_unified_runtime_replay_authority",
]
