# -*- coding: utf-8 -*-
"""Sealed read-only witness for an E543/E544 completed-tick transaction.

The witness consumes detached mappings produced by the real viewport
transaction producer.  It validates the receipt -> binding -> authority ->
portable-checkpoint -> restore chain and records fail-closed tamper evidence.
It never owns a viewport, never mutates runtime state and never grants replay
admission.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .world_bridge_live_checkpoint import validate_worldbridge_live_checkpoint
from .world_bridge_tick_authority import (
    validate_worldbridge_tick_authority_snapshot,
    validate_worldbridge_tick_receipt,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_e545_completed_tick_transaction_witness"
ADMISSION_EFFECT = "none"
BINDING_KEYS = (
    "tick_sequence",
    "pause_reset_epoch",
    "input_digest",
    "context_digest",
    "rng_context_id",
    "rng_start_digest",
    "rng_end_digest",
    "receipt_digest",
)
RESTORE_ORDER = (
    "lifecycle",
    "input",
    "tick_authority",
    "randomness",
    "ps",
    "sr",
    "topology",
    "bridge",
)
FORBIDDEN_PORTABLE_FIELDS = (
    "tick_authority",
    "tick_authority_state",
    "tick_binding",
)

WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "completed_tick_receipt",
    "tick_binding",
    "tick_authority_snapshot",
    "portable_checkpoint",
    "checkpoint_digest",
    "restore_report",
    "stale_transaction_rejection",
    "tamper_rejections",
    "receipt_validated",
    "binding_validated",
    "authority_validated",
    "checkpoint_validated",
    "restore_validated",
    "stale_transaction_rejected",
    "tamper_fail_closed",
    "owner_mutation_prevented",
    "grants_admission",
    "admission_effect",
    "atomic_checkpoint",
    "lossless",
    "replay_admitted",
    "default_ready",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "witness_digest",
)
RESTORE_ADMISSION_FIELDS = (
    "atomic_checkpoint",
    "replay_admitted",
    "default_ready",
)
REQUIRED_TAMPER_CASES = (
    "checkpoint_digest",
    "binding_receipt_digest",
    "authority_last_receipt",
    "portable_authority_field",
    "restore_report_overclaim",
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
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and _DIGEST_RE.fullmatch(value) is not None


def _receipt_binding_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {field: receipt.get(field) for field in BINDING_KEYS}


def _binding_errors(
    binding: object,
    receipt: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(binding, Mapping):
        return ["tick_binding_not_mapping"]
    if set(binding) != set(BINDING_KEYS):
        errors.append("tick_binding_keys_mismatch")
    if binding != _receipt_binding_projection(receipt):
        errors.append("tick_binding_receipt_mismatch")
    return errors


def _restore_report_errors(
    report: object,
    *,
    checkpoint_digest: object,
    binding: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, Mapping):
        return ["restore_report_not_mapping"]
    if report.get("schema_version") != 1:
        errors.append("restore_schema_version_mismatch")
    if report.get("status") != "worldbridge_live_checkpoint":
        errors.append("restore_status_mismatch")
    if report.get("restored") is not True:
        errors.append("restore_not_successful")
    if report.get("rollback_performed") is not False:
        errors.append("restore_rollback_unexpected")
    if report.get("transaction_verified") is not True:
        errors.append("restore_transaction_not_verified")
    if report.get("restore_order") != list(RESTORE_ORDER):
        errors.append("restore_order_mismatch")
    for field in (
        "tick_binding_validated",
        "tick_binding_stable",
        "tick_authority_validated",
        "tick_authority_stable",
    ):
        if report.get(field) is not True:
            errors.append(f"{field}_not_true")
    for field in (
        "tick_binding_errors",
        "tick_authority_errors",
        "owner_binding_errors",
    ):
        if report.get(field) != []:
            errors.append(f"{field}_not_empty")
    for field in RESTORE_ADMISSION_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field}_overclaim")
    if report.get("checkpoint_digest") != checkpoint_digest:
        errors.append("restore_checkpoint_digest_mismatch")
    if report.get("expected_tick_binding") != binding:
        errors.append("restore_expected_binding_mismatch")
    if report.get("actual_tick_binding") != binding:
        errors.append("restore_actual_binding_mismatch")
    return errors


def _rejection_errors(value: object, field: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return [f"{field}_not_mapping"]
    if value.get("fail_closed") is not True:
        errors.append(f"{field}_not_fail_closed")
    if value.get("owner_before_mutation_unchanged") is not True:
        errors.append(f"{field}_owner_mutation_preflight_missing")
    rejection_errors = value.get("errors")
    if (
        not isinstance(rejection_errors, list)
        or not rejection_errors
        or any(not isinstance(item, str) or not item for item in rejection_errors)
    ):
        errors.append(f"{field}_errors_invalid")
    return errors


def _tamper_errors(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["tamper_rejections_not_mapping"]
    for name in REQUIRED_TAMPER_CASES:
        if name not in value:
            errors.append(f"tamper_case_missing:{name}")
            continue
        errors.extend(_rejection_errors(value[name], f"tamper_{name}"))
    return errors


def _build_input_errors(
    *,
    completed_tick_receipt: Mapping[str, Any],
    tick_binding: Mapping[str, Any],
    tick_authority_snapshot: Mapping[str, Any],
    portable_checkpoint: Mapping[str, Any],
    restore_report: Mapping[str, Any],
    stale_transaction_rejection: Mapping[str, Any],
    tamper_rejections: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    receipt_validation = validate_worldbridge_tick_receipt(completed_tick_receipt)
    if receipt_validation != {"valid": True, "errors": []}:
        errors.extend(f"receipt_{item}" for item in receipt_validation["errors"])
        return errors
    errors.extend(_binding_errors(tick_binding, completed_tick_receipt))
    authority_validation = validate_worldbridge_tick_authority_snapshot(
        tick_authority_snapshot
    )
    if authority_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"authority_{item}" for item in authority_validation["errors"]
        )
    if (
        tick_authority_snapshot.get("tick_sequence")
        != completed_tick_receipt.get("tick_sequence")
    ):
        errors.append("authority_tick_sequence_mismatch")
    if tick_authority_snapshot.get("last_receipt") != completed_tick_receipt:
        errors.append("authority_last_receipt_mismatch")
    checkpoint_validation = validate_worldbridge_live_checkpoint(
        portable_checkpoint
    )
    if checkpoint_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"checkpoint_{item}" for item in checkpoint_validation["errors"]
        )
    for field in FORBIDDEN_PORTABLE_FIELDS:
        if field in portable_checkpoint:
            errors.append(f"portable_checkpoint_contains_{field}")
    errors.extend(
        _restore_report_errors(
            restore_report,
            checkpoint_digest=portable_checkpoint.get("digest"),
            binding=tick_binding,
        )
    )
    stale_errors = _rejection_errors(
        stale_transaction_rejection, "stale_transaction_rejection"
    )
    errors.extend(stale_errors)
    stale_reasons = stale_transaction_rejection.get("errors")
    if (
        isinstance(stale_reasons, list)
        and "completed_tick_binding_mismatch" not in stale_reasons
    ):
        errors.append("stale_transaction_mismatch_not_classified")
    errors.extend(_tamper_errors(tamper_rejections))
    return errors


def build_worldbridge_e545_completed_tick_transaction_witness(
    *,
    completed_tick_receipt: Mapping[str, Any],
    tick_binding: Mapping[str, Any],
    tick_authority_snapshot: Mapping[str, Any],
    portable_checkpoint: Mapping[str, Any],
    restore_report: Mapping[str, Any],
    stale_transaction_rejection: Mapping[str, Any],
    tamper_rejections: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a detached, digest-sealed witness from explicit transaction data."""
    receipt = _mapping_copy(completed_tick_receipt, "completed_tick_receipt")
    binding = _mapping_copy(tick_binding, "tick_binding")
    authority = _mapping_copy(tick_authority_snapshot, "tick_authority_snapshot")
    checkpoint = _mapping_copy(portable_checkpoint, "portable_checkpoint")
    restore = _mapping_copy(restore_report, "restore_report")
    stale = _mapping_copy(stale_transaction_rejection, "stale_transaction_rejection")
    tamper = _mapping_copy(tamper_rejections, "tamper_rejections")

    errors = _build_input_errors(
        completed_tick_receipt=receipt,
        tick_binding=binding,
        tick_authority_snapshot=authority,
        portable_checkpoint=checkpoint,
        restore_report=restore,
        stale_transaction_rejection=stale,
        tamper_rejections=tamper,
    )
    if errors:
        raise ValueError(
            "invalid completed-tick transaction witness inputs: "
            + ", ".join(dict.fromkeys(errors))
        )

    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "completed_tick_receipt": receipt,
        "tick_binding": binding,
        "tick_authority_snapshot": authority,
        "portable_checkpoint": checkpoint,
        "checkpoint_digest": checkpoint["digest"],
        "restore_report": restore,
        "stale_transaction_rejection": stale,
        "tamper_rejections": tamper,
        "receipt_validated": True,
        "binding_validated": True,
        "authority_validated": True,
        "checkpoint_validated": True,
        "restore_validated": True,
        "stale_transaction_rejected": True,
        "tamper_fail_closed": True,
        "owner_mutation_prevented": True,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        "atomic_checkpoint": False,
        "lossless": False,
        "replay_admitted": False,
        "default_ready": False,
        "tick_merge_admitted": False,
        "full_unified_replay_admitted": False,
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return copy.deepcopy(witness)


def validate_worldbridge_e545_completed_tick_transaction_witness(
    value: object,
) -> dict[str, Any]:
    """Validate the witness and every embedded detached evidence relationship."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("read_only") is not True:
        errors.append("read_only_mismatch")
    try:
        if set(value) != set(WITNESS_KEYS):
            errors.append("witness_keys_mismatch")
    except Exception:
        return {"valid": False, "errors": errors + ["witness_keys_invalid"]}
    try:
        _canonical(value)
    except (TypeError, ValueError, OverflowError):
        return {"valid": False, "errors": errors + ["witness_not_canonical_json"]}

    receipt = value.get("completed_tick_receipt")
    binding = value.get("tick_binding")
    authority = value.get("tick_authority_snapshot")
    checkpoint = value.get("portable_checkpoint")
    restore = value.get("restore_report")
    stale = value.get("stale_transaction_rejection")
    tamper = value.get("tamper_rejections")
    if not isinstance(receipt, Mapping):
        errors.append("receipt_not_mapping")
    if not isinstance(binding, Mapping):
        errors.append("binding_not_mapping")
    if not isinstance(authority, Mapping):
        errors.append("authority_not_mapping")
    if not isinstance(checkpoint, Mapping):
        errors.append("checkpoint_not_mapping")
    if not isinstance(restore, Mapping):
        errors.append("restore_report_not_mapping")
    if not isinstance(stale, Mapping):
        errors.append("stale_rejection_not_mapping")
    if not isinstance(tamper, Mapping):
        errors.append("tamper_rejections_not_mapping")

    if isinstance(receipt, Mapping) and isinstance(binding, Mapping) and isinstance(
        authority, Mapping
    ) and isinstance(checkpoint, Mapping) and isinstance(restore, Mapping) and isinstance(
        stale, Mapping
    ) and isinstance(tamper, Mapping):
        receipt_validation = validate_worldbridge_tick_receipt(receipt)
        if receipt_validation != {"valid": True, "errors": []}:
            errors.extend(
                f"receipt_{item}" for item in receipt_validation["errors"]
            )
        errors.extend(_binding_errors(binding, receipt))
        authority_validation = validate_worldbridge_tick_authority_snapshot(
            authority
        )
        if authority_validation != {"valid": True, "errors": []}:
            errors.extend(
                f"authority_{item}" for item in authority_validation["errors"]
            )
        if authority.get("tick_sequence") != receipt.get("tick_sequence"):
            errors.append("authority_tick_sequence_mismatch")
        if authority.get("last_receipt") != receipt:
            errors.append("authority_last_receipt_mismatch")
        checkpoint_validation = validate_worldbridge_live_checkpoint(checkpoint)
        if checkpoint_validation != {"valid": True, "errors": []}:
            errors.extend(
                f"checkpoint_{item}" for item in checkpoint_validation["errors"]
            )
        for field in FORBIDDEN_PORTABLE_FIELDS:
            if field in checkpoint:
                errors.append(f"portable_checkpoint_contains_{field}")
        if value.get("checkpoint_digest") != checkpoint.get("digest"):
            errors.append("checkpoint_digest_field_mismatch")
        errors.extend(
            _restore_report_errors(
                restore,
                checkpoint_digest=checkpoint.get("digest"),
                binding=binding,
            )
        )
        errors.extend(
            _rejection_errors(stale, "stale_transaction_rejection")
        )
        stale_reasons = stale.get("errors")
        if (
            isinstance(stale_reasons, list)
            and "completed_tick_binding_mismatch" not in stale_reasons
        ):
            errors.append("stale_transaction_mismatch_not_classified")
        errors.extend(_tamper_errors(tamper))

    for field in (
        "receipt_validated",
        "binding_validated",
        "authority_validated",
        "checkpoint_validated",
        "restore_validated",
        "stale_transaction_rejected",
        "tamper_fail_closed",
        "owner_mutation_prevented",
    ):
        if value.get(field) is not True:
            errors.append(f"{field}_not_true")
    if value.get("grants_admission") is not False:
        errors.append("grants_admission_overclaim")
    if value.get("admission_effect") != ADMISSION_EFFECT:
        errors.append("admission_effect_mismatch")
    for field in (
        "atomic_checkpoint",
        "lossless",
        "replay_admitted",
        "default_ready",
        "tick_merge_admitted",
        "full_unified_replay_admitted",
    ):
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if not _is_digest(digest) or digest != _witness_digest(value):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "ADMISSION_EFFECT",
    "BINDING_KEYS",
    "FORBIDDEN_PORTABLE_FIELDS",
    "RESTORE_ORDER",
    "SCHEMA_VERSION",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e545_completed_tick_transaction_witness",
    "validate_worldbridge_e545_completed_tick_transaction_witness",
]