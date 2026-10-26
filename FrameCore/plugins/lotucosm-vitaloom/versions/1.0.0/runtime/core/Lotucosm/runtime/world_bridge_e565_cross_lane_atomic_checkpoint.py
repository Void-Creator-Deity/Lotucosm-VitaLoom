# -*- coding: utf-8 -*-
"""Cross-process SR/PS checkpoint reconstruction authority."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_deterministic_randomness_context import (
    restore_worldbridge_deterministic_randomness_context,
)
from .world_bridge_e504_fresh_dual_lane_witness import (
    build_worldbridge_e504_fresh_dual_lane_witness,
    validate_worldbridge_e504_fresh_dual_lane_witness,
)
from .world_bridge_e551_scene_pond_checkpoint_authority import (
    validate_worldbridge_e551_scene_pond_checkpoint_authority,
)
from .world_bridge_fresh_restore_parity import (
    capture_canonical_ps_state,
    restore_ps_state_to_fresh_pond,
)
from .world_bridge_input_sequence import WorldBridgeInputSequence
from .world_bridge_live_checkpoint import (
    validate_worldbridge_live_checkpoint,
)
from core.VitaLoom.simulation.sr_runtime_structure_parity import (
    build_sr_runtime_structure_fingerprint,
    compare_sr_runtime_structure_fingerprints,
    validate_sr_runtime_structure_fingerprint,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e565_cross_lane_atomic_checkpoint_authority"
SCOPE = "cross_process_dual_lane_checkpoint_reconstruction"
POLICY = "locked_full_state_capture_or_fresh_host_quarantine_v1"
PROOF_FIELDS = (
    "e551_checkpoint_validated",
    "e564_transaction_validated",
    "source_checkpoint_bound",
    "child_process_distinct",
    "structure_equal",
    "fresh_dual_lane_parity",
    "fresh_epoch_distinct",
    "transaction_interlock_released",
    "fresh_host_failure_is_quarantinable",
)
CLOSED_ADMISSION_FIELDS = (
    "portable_sr_executable_script_checkpoint",
    "global_cross_process_atomicity",
    "default_ready",
)
TRANSACTION_FIELDS = {
    "artifact_digest",
    "imported_artifact_digest",
    "project_lock_digest",
    "contention_code",
    "holder_pid",
    "importer_pid",
    "interlock_released",
    "canonical_artifact",
    "atomic_write_failure_preserved_previous",
    "errors",
}
CHILD_FIELDS = {
    "parent_pid",
    "child_pid",
    "source_checkpoint_digest",
    "fresh_checkpoint",
    "structure_comparison",
    "e504_witness",
    "fresh_host_quarantinable",
    "errors",
    "ok",
}
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class CrossLaneCheckpointFreshHostError(RuntimeError):
    """A fresh host failed and must be discarded as one quarantine unit."""

    def __init__(self, message: str):
        super().__init__(message)
        self.quarantine_required = True


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


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def apply_checkpoint_to_fresh_viewport(
    *,
    viewport: Any,
    source_checkpoint: Mapping[str, Any],
    source_structure: Mapping[str, Any],
    source_next_rng_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply portable slices to one fresh viewport or quarantine the host."""
    try:
        validation = validate_worldbridge_live_checkpoint(source_checkpoint)
        if validation["valid"] is not True:
            raise ValueError(
                "source checkpoint invalid: " + ",".join(validation["errors"])
            )
        structure_validation = validate_sr_runtime_structure_fingerprint(
            source_structure
        )
        if structure_validation["valid"] is not True:
            raise ValueError(
                "source structure invalid: "
                + ",".join(structure_validation["errors"])
            )
        checkpoint = copy.deepcopy(dict(source_checkpoint))
        viewport._update_scene_runtime_entities(0.05)
        fresh_structure = build_sr_runtime_structure_fingerprint(
            entities=viewport.scene_runtime_entities,
            scene_path=viewport._sr_runtime_scene_path,
            structural_edges=viewport._sr_structural_edges,
            signal_edges=viewport._sr_signal_edges,
            membrane_attach=viewport._sr_membrane_attach,
            membrane_template=viewport._sr_membrane_template,
        )
        structure = compare_sr_runtime_structure_fingerprints(
            source_structure,
            fresh_structure,
        )
        if structure.get("equal") is not True:
            raise ValueError("fresh SR runtime structure mismatch")

        source_sr = copy.deepcopy(
            checkpoint["sr_state"]["runtime_restore_envelope"]
        )
        viewport.restore_sr_runtime_snapshot_slice(
            copy.deepcopy(source_sr["snapshots"]),
            scene_time=source_sr["scene_time"],
        )
        fresh_dynamic = viewport.capture_sr_runtime_restore_envelope()
        dynamic_equal = _canonical(
            {
                "scene_time": fresh_dynamic.get("scene_time"),
                "snapshots": fresh_dynamic.get("snapshots"),
            }
        ) == _canonical(
            {
                "scene_time": source_sr.get("scene_time"),
                "snapshots": source_sr.get("snapshots"),
            }
        )
        fresh_sr = {
            "schema_version": 1,
            "status": "worldbridge_fresh_sr_restore_parity",
            "fresh_instance": True,
            "structure": structure,
            "dynamic_slice_restored": structure.get("equal") is True,
            "dynamic_state_equal": dynamic_equal,
            "cross_lane_parity": (
                structure.get("equal") is True and dynamic_equal
            ),
            "errors": (
                []
                if structure.get("equal") is True and dynamic_equal
                else ["fresh_sr_dynamic_state_mismatch"]
            ),
            "default_ready": False,
            "replay_admitted": False,
            "lossless": False,
        }

        source_ps = copy.deepcopy(checkpoint["ps_state"])
        source_ps_canonical = _canonical(
            capture_canonical_ps_state(
                restore_ps_state_to_fresh_pond(source_ps)
            )
        )
        viewport._unified_pond.restore_serialized_state_in_place(source_ps)
        fresh_ps = {
            "fresh_instance_created": True,
            "canonical_state_equal": (
                _canonical(capture_canonical_ps_state(viewport._unified_pond))
                == source_ps_canonical
            ),
        }
        randomness = checkpoint.get("randomness_state")
        deterministic = (
            randomness.get("deterministic_context")
            if isinstance(randomness, Mapping)
            else None
        )
        if deterministic is not None:
            restore_worldbridge_deterministic_randomness_context(
                viewport._worldbridge_opt_in_deterministic_randomness_context,
                deterministic,
            )
        source_input = copy.deepcopy(checkpoint["input_state"])
        canonical_sequence = source_input.pop("canonical_sequence", None)
        source_input.pop("shared_transport", None)
        source_input.pop("ps_handoff_input_events", None)
        if canonical_sequence is None:
            raise ValueError("canonical input sequence missing")
        WorldBridgeInputSequence.validate_snapshot(canonical_sequence)
        viewport.restore_sr_input_state(source_input)
        viewport._worldbridge_input_sequence.restore_snapshot(
            canonical_sequence
        )
        fresh_checkpoint = viewport.capture_worldbridge_live_checkpoint(
            "e565-child-fresh"
        )
        viewport._update_scene_runtime_entities(0.05)
        fresh_next_rng = (
            viewport._worldbridge_opt_in_deterministic_randomness_context.snapshot()
        )
        witness = build_worldbridge_e504_fresh_dual_lane_witness(
            source_checkpoint=checkpoint,
            fresh_checkpoint=fresh_checkpoint,
            fresh_sr_restore=fresh_sr,
            fresh_ps_restore=fresh_ps,
            source_next_rng_snapshot=source_next_rng_snapshot,
            fresh_next_rng_snapshot=fresh_next_rng,
        )
        if validate_worldbridge_e504_fresh_dual_lane_witness(
            witness
        ) != {"valid": True, "errors": []}:
            raise ValueError("E504 witness invalid")
        return {
            "fresh_checkpoint": fresh_checkpoint,
            "structure_comparison": structure,
            "e504_witness": witness,
            "fresh_next_rng_snapshot": fresh_next_rng,
            "host_quarantinable": True,
        }
    except Exception as exc:
        raise CrossLaneCheckpointFreshHostError(
            f"{type(exc).__name__}:{exc}"
        ) from exc


def _validate_transaction_evidence(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["transaction_evidence_not_mapping"]
    if set(value) != TRANSACTION_FIELDS:
        errors.append("transaction_evidence_keys_invalid")
    for field in ("artifact_digest", "imported_artifact_digest", "project_lock_digest"):
        item = value.get(field)
        if not isinstance(item, str) or _DIGEST_RE.fullmatch(item) is None:
            errors.append(f"transaction_{field}_invalid")
    if value.get("artifact_digest") != value.get("imported_artifact_digest"):
        errors.append("transaction_artifact_digest_mismatch")
    if value.get("contention_code") != "checkpoint_interlock_held":
        errors.append("transaction_cross_process_contention_missing")
    holder = value.get("holder_pid")
    importer = value.get("importer_pid")
    if (
        isinstance(holder, bool)
        or not isinstance(holder, int)
        or holder < 1
        or isinstance(importer, bool)
        or not isinstance(importer, int)
        or importer < 1
        or holder == importer
    ):
        errors.append("transaction_process_identity_invalid")
    if value.get("interlock_released") is not True:
        errors.append("transaction_interlock_not_released")
    if value.get("canonical_artifact") is not True:
        errors.append("transaction_artifact_not_canonical")
    if value.get("atomic_write_failure_preserved_previous") is not True:
        errors.append("transaction_atomic_failure_evidence_missing")
    if value.get("errors") != []:
        errors.append("transaction_errors_present")
    return errors


def _evaluate(
    *,
    e551_witness: Mapping[str, Any],
    transaction_evidence: Mapping[str, Any],
    source_checkpoint: Mapping[str, Any],
    child_result: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    e551_validation = (
        validate_worldbridge_e551_scene_pond_checkpoint_authority(e551_witness)
    )
    e551_valid = e551_validation == {"valid": True, "errors": []}
    if not e551_valid:
        errors.extend(f"e551_{item}" for item in e551_validation["errors"])
    source_validation = validate_worldbridge_live_checkpoint(source_checkpoint)
    source_valid = source_validation == {"valid": True, "errors": []}
    if not source_valid:
        errors.extend(
            f"source_checkpoint_{item}" for item in source_validation["errors"]
        )
    e551_checkpoint = e551_witness.get("checkpoint")
    source_bound = (
        isinstance(e551_checkpoint, Mapping)
        and source_checkpoint == e551_checkpoint
    )
    if not source_bound:
        errors.append("source_checkpoint_not_bound_to_e551")
    errors.extend(_validate_transaction_evidence(transaction_evidence))

    if set(child_result) != CHILD_FIELDS:
        errors.append("child_result_keys_invalid")
    parent_pid = child_result.get("parent_pid")
    child_pid = child_result.get("child_pid")
    child_distinct = (
        isinstance(parent_pid, int)
        and not isinstance(parent_pid, bool)
        and parent_pid > 0
        and isinstance(child_pid, int)
        and not isinstance(child_pid, bool)
        and child_pid > 0
        and child_pid != parent_pid
    )
    if not child_distinct:
        errors.append("child_process_not_distinct")
    transaction_holder = transaction_evidence.get("holder_pid")
    transaction_importer = transaction_evidence.get("importer_pid")
    if child_pid in {transaction_holder, transaction_importer}:
        errors.append("child_process_reused_transaction_process")
    if child_result.get("ok") is not True:
        errors.append("child_result_not_ok")
    if child_result.get("fresh_host_quarantinable") is not True:
        errors.append("fresh_host_quarantine_boundary_missing")
    if child_result.get("errors") != []:
        errors.append("child_errors_present")
    if child_result.get("source_checkpoint_digest") != source_checkpoint.get(
        "digest"
    ):
        errors.append("child_source_checkpoint_digest_mismatch")

    fresh_checkpoint = child_result.get("fresh_checkpoint")
    if not isinstance(fresh_checkpoint, Mapping):
        fresh_checkpoint = {}
        errors.append("child_fresh_checkpoint_invalid")
    witness = child_result.get("e504_witness")
    if not isinstance(witness, Mapping):
        witness = {}
        errors.append("child_e504_witness_invalid")
    witness_validation = validate_worldbridge_e504_fresh_dual_lane_witness(
        witness
    )
    witness_valid = witness_validation == {"valid": True, "errors": []}
    if not witness_valid:
        errors.extend(
            f"child_e504_{item}" for item in witness_validation["errors"]
        )
    parity = witness.get("fresh_dual_lane_parity") is True
    if not parity:
        errors.append("fresh_dual_lane_parity_not_proven")
    if witness.get("source_checkpoint_digest") != source_checkpoint.get("digest"):
        errors.append("e504_source_checkpoint_mismatch")
    if witness.get("fresh_checkpoint_digest") != fresh_checkpoint.get("digest"):
        errors.append("e504_fresh_checkpoint_mismatch")
    structure = child_result.get("structure_comparison")
    structure_equal = (
        isinstance(structure, Mapping)
        and structure.get("equal") is True
    )
    if not structure_equal:
        errors.append("cross_process_structure_mismatch")
    source_epoch = (
        source_checkpoint.get("lifecycle", {}).get("runtime_epoch")
        if isinstance(source_checkpoint.get("lifecycle"), Mapping)
        else None
    )
    fresh_epoch = (
        fresh_checkpoint.get("lifecycle", {}).get("runtime_epoch")
        if isinstance(fresh_checkpoint.get("lifecycle"), Mapping)
        else None
    )
    epoch_distinct = (
        isinstance(source_epoch, str)
        and isinstance(fresh_epoch, str)
        and source_epoch != fresh_epoch
    )
    if not epoch_distinct:
        errors.append("fresh_runtime_epoch_not_distinct")

    proof = {
        "e551_checkpoint_validated": e551_valid,
        "e564_transaction_validated": not _validate_transaction_evidence(
            transaction_evidence
        ),
        "source_checkpoint_bound": source_bound and source_valid,
        "child_process_distinct": child_distinct,
        "structure_equal": structure_equal,
        "fresh_dual_lane_parity": parity and witness_valid,
        "fresh_epoch_distinct": epoch_distinct,
        "transaction_interlock_released": (
            transaction_evidence.get("interlock_released") is True
        ),
        "fresh_host_failure_is_quarantinable": (
            child_result.get("fresh_host_quarantinable") is True
        ),
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")
    return list(dict.fromkeys(errors)), {
        **proof,
        "source_checkpoint_digest": source_checkpoint.get("digest"),
        "fresh_checkpoint_digest": fresh_checkpoint.get("digest"),
        "e551_witness_digest": e551_witness.get("witness_digest"),
        "transaction_artifact_digest": transaction_evidence.get(
            "artifact_digest"
        ),
    }


def build_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
    *,
    e551_witness: Mapping[str, Any],
    transaction_evidence: Mapping[str, Any],
    source_checkpoint: Mapping[str, Any],
    child_result: Mapping[str, Any],
) -> dict[str, Any]:
    errors, proof = _evaluate(
        e551_witness=e551_witness,
        transaction_evidence=transaction_evidence,
        source_checkpoint=source_checkpoint,
        child_result=child_result,
    )
    if errors:
        raise ValueError(
            "E565 cross-lane checkpoint witness rejected: "
            + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "policy": POLICY,
        "e551_witness": copy.deepcopy(dict(e551_witness)),
        "transaction_evidence": copy.deepcopy(dict(transaction_evidence)),
        "source_checkpoint": copy.deepcopy(dict(source_checkpoint)),
        "child_result": copy.deepcopy(dict(child_result)),
        **proof,
        "atomic_sr_ps_checkpoint": True,
        "cross_lane_restore_admitted": True,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
    value: object,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    required = {
        "schema_version",
        "status",
        "read_only",
        "scope",
        "policy",
        "e551_witness",
        "transaction_evidence",
        "source_checkpoint",
        "child_result",
        *PROOF_FIELDS,
        "source_checkpoint_digest",
        "fresh_checkpoint_digest",
        "e551_witness_digest",
        "transaction_artifact_digest",
        "atomic_sr_ps_checkpoint",
        "cross_lane_restore_admitted",
        *CLOSED_ADMISSION_FIELDS,
        "witness_digest",
    }
    if set(value) != required:
        errors.append("witness_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_required")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("policy") != POLICY:
        errors.append("policy_mismatch")
    e551 = value.get("e551_witness")
    transaction = value.get("transaction_evidence")
    source = value.get("source_checkpoint")
    child = value.get("child_result")
    if not all(
        isinstance(item, Mapping)
        for item in (e551, transaction, source, child)
    ):
        return {"valid": False, "errors": errors + ["witness_payload_invalid"]}
    revalidation, proof = _evaluate(
        e551_witness=e551,
        transaction_evidence=transaction,
        source_checkpoint=source,
        child_result=child,
    )
    errors.extend(revalidation)
    for field, expected in proof.items():
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
    if value.get("atomic_sr_ps_checkpoint") is not True:
        errors.append("atomic_sr_ps_checkpoint_not_admitted")
    if value.get("cross_lane_restore_admitted") is not True:
        errors.append("cross_lane_restore_not_admitted")
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
    "CLOSED_ADMISSION_FIELDS",
    "CrossLaneCheckpointFreshHostError",
    "POLICY",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "apply_checkpoint_to_fresh_viewport",
    "build_worldbridge_e565_cross_lane_atomic_checkpoint_authority",
    "validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority",
]
