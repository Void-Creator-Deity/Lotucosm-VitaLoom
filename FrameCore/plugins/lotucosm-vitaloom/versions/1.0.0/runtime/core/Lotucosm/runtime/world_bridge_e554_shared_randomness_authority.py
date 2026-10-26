# -*- coding: utf-8 -*-
"""Composite authority for the shared SR/PS deterministic randomness boundary.

The witness binds one validated cross-lane draw-order observation to the
root-seed-derived stream registry, the complete dynamic-script entropy corpus,
and the selected native SR2D backend.  It admits no replay, checkpoint,
tick-merge, or default-runtime authority by itself.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    validate_worldbridge_deterministic_randomness_snapshot,
)
from core.Lotucosm.runtime.world_bridge_e548_rng_draw_order_authority import (
    validate_worldbridge_e548_rng_draw_order_authority,
)
from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_entropy_boundary_receipt,
    build_native_backend_selection_evidence,
    validate_native_entropy_boundary_receipt,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    build_script_evidence_digest,
)
from core.Lotucosm.script_entropy_audit import (
    build_dynamic_script_boundary_receipt,
    diagnose_script_entropy_admission,
    validate_dynamic_script_boundary_receipt,
    validate_project_script_inventory,
    validate_script_descriptor_coverage,
    validate_script_evidence_corpus,
)


SCHEMA_VERSION = 1
STATUS = "worldbridge_e554_shared_randomness_authority"
SCOPE = "shared_root_seed_with_dynamic_and_native_entropy_boundaries"
ADMISSION_EFFECT = "none"
PROOF_FIELDS = (
    "shared_context_valid",
    "root_seed_derivation_bound",
    "lane_stream_families_valid",
    "cross_lane_draw_order_valid",
    "dynamic_script_corpus_valid",
    "dynamic_script_owner_bound",
    "dynamic_entropy_boundary_closed",
    "native_receipt_source_bound",
    "native_backend_selection_valid",
    "native_backend_excluded_or_admitted",
    "native_entropy_boundary_closed",
    "process_global_entropy_isolated",
)
CLOSED_ADMISSION_FIELDS = (
    "shared_random_seed_contract",
    "cross_lane_rng_draw_order_admitted",
    "dynamic_entropy_boundary_admitted",
    "native_entropy_boundary_admitted",
    "process_global_entropy_admitted",
    "rng_checkpoint_admitted",
    "rng_replay_admitted",
    "replay_admitted",
    "tick_merge_admitted",
    "full_unified_replay_admitted",
    "lossless",
    "default_ready",
)
SCRIPT_EVIDENCE_KEYS = {
    "schema_version",
    "runtime_epoch",
    "audits",
    "receipts",
    "trust_denials",
    "failure_receipts",
    "declared_paths",
    "inventory",
    "owner_stream_name",
    "owner_registry_digest",
    "owner_graph_digest",
    "execution_receipts",
    "boundary_receipt",
    "evidence_digest",
}
WITNESS_KEYS = (
    "schema_version",
    "status",
    "read_only",
    "scope",
    "rng_draw_order_witness",
    "script_evidence",
    "native_boundary_receipt",
    "native_backend_capability",
    "native_admission_evidence",
    "requested_native_backend",
    "project_path",
    "rng_context_id",
    "shared_root_seed_digest",
    "stream_registration",
    "native_runtime_adapter_available",
    "native_closure_mode",
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


def _stream_rows(snapshot: Mapping[str, Any]) -> list[dict[str, str]]:
    streams = snapshot.get("streams")
    if not isinstance(streams, list):
        return []
    return [
        {
            "name": str(stream.get("stream_name")),
            "family": str(stream.get("family")),
        }
        for stream in streams
        if isinstance(stream, Mapping)
    ]


def _registry_digest(rows: list[dict[str, str]]) -> str:
    return hashlib.sha256(_canonical(rows)).hexdigest()


def _native_runtime_available() -> bool:
    try:
        from core.Lotucosm.sr_physics2d import is_native_sr2d_available
    except Exception:
        return False
    try:
        return bool(is_native_sr2d_available())
    except Exception:
        return False


def _evaluate(
    *,
    rng_draw_order: Mapping[str, Any],
    script_evidence: Mapping[str, Any],
    native_receipt: Mapping[str, Any],
    native_capability: Mapping[str, Any],
    native_admission_evidence: Mapping[str, Any] | None,
    requested_native_backend: str,
    project_path: str | None,
    native_runtime_available: bool,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []

    draw_validation = validate_worldbridge_e548_rng_draw_order_authority(
        rng_draw_order
    )
    if draw_validation != {"valid": True, "errors": []}:
        errors.extend(f"draw_{item}" for item in draw_validation["errors"])

    snapshot = rng_draw_order.get("rng_context_snapshot")
    snapshot_validation = validate_worldbridge_deterministic_randomness_snapshot(
        snapshot
    )
    if snapshot_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"snapshot_{item}" for item in snapshot_validation["errors"]
        )
        snapshot = {}

    rows = _stream_rows(snapshot)
    row_by_name = {row["name"]: row for row in rows}
    shared_context_valid = (
        snapshot.get("context_id") == rng_draw_order.get("rng_context_id")
        and isinstance(snapshot.get("root_seed_digest"), str)
        and _DIGEST_RE.fullmatch(str(snapshot.get("root_seed_digest"))) is not None
        and snapshot.get("root_seed_material_revealed") is False
    )
    if not shared_context_valid:
        errors.append("shared_context_binding_mismatch")

    lane_stream_families_valid = (
        row_by_name.get("sr.runtime", {}).get("family") == "python_random"
        and row_by_name.get("ps.pond", {}).get("family")
        == "numpy_pcg64_generator"
    )
    if not lane_stream_families_valid:
        errors.append("lane_stream_family_mismatch")

    sr_rows = [
        row for row in rows if row["name"] == "sr.runtime"
    ]
    expected_script_owner_digest = (
        _registry_digest(sr_rows) if len(sr_rows) == 1 else None
    )
    root_seed_derivation_bound = (
        shared_context_valid
        and row_by_name.get("sr.runtime", {}).get("family") == "python_random"
        and all(
            _DIGEST_RE.fullmatch(str(snapshot.get("streams", [{}])[index].get("derivation_digest")))
            for index in range(len(rows))
        )
    )
    if not root_seed_derivation_bound:
        errors.append("root_seed_derivation_unbound")

    cross_lane_draw_order_valid = all(
        rng_draw_order.get(field) is True
        for field in (
            "phase_order_valid",
            "registration_order_stable",
            "receipt_phase_binding",
            "context_start_bound",
            "context_end_bound",
            "sr_draw_observed",
            "ps_draw_observed",
            "sr_before_ps",
            "lane_stream_isolation",
            "snapshot_bound",
        )
    )
    if not cross_lane_draw_order_valid:
        errors.append("cross_lane_draw_order_missing")

    if set(script_evidence) != SCRIPT_EVIDENCE_KEYS:
        errors.append("script_evidence_keys_invalid")
    for field in (
        "audits",
        "receipts",
        "trust_denials",
        "failure_receipts",
        "declared_paths",
        "inventory",
        "execution_receipts",
    ):
        if not isinstance(script_evidence.get(field), list):
            errors.append(f"script_evidence_{field}_invalid")
    receipt_mapping = rng_draw_order.get("completed_tick_receipt")
    if not isinstance(receipt_mapping, Mapping):
        receipt_mapping = {}
    decision = receipt_mapping.get("clock_decision")
    if not isinstance(decision, Mapping):
        decision = {}
    expected_epoch = decision.get("runtime_epoch")
    runtime_epoch_bound = (
        isinstance(expected_epoch, str)
        and bool(expected_epoch)
        and script_evidence.get("runtime_epoch") == expected_epoch
    )
    if not runtime_epoch_bound:
        errors.append("script_runtime_epoch_mismatch")

    corpus = validate_script_evidence_corpus(
        script_evidence.get("audits"),
        script_evidence.get("receipts"),
        script_evidence.get("trust_denials"),
        script_evidence.get("failure_receipts"),
    )
    if corpus != {"valid": True, "errors": []}:
        errors.extend(f"script_corpus_{item}" for item in corpus["errors"])
    descriptor = validate_script_descriptor_coverage(
        script_evidence.get("declared_paths"),
        script_evidence.get("audits"),
        script_evidence.get("receipts"),
        script_evidence.get("trust_denials"),
        script_evidence.get("failure_receipts"),
    )
    if descriptor != {"valid": True, "errors": []}:
        errors.extend(
            f"script_descriptor_{item}" for item in descriptor["errors"]
        )
    inventory = validate_project_script_inventory(
        script_evidence.get("inventory"),
        project_path=project_path,
        loaded_receipts=script_evidence.get("receipts"),
        trust_denials=script_evidence.get("trust_denials"),
        failure_receipts=script_evidence.get("failure_receipts"),
    )
    if inventory != {"valid": True, "errors": []}:
        errors.extend(f"script_inventory_{item}" for item in inventory["errors"])

    embedded_boundary = script_evidence.get("boundary_receipt")
    boundary_validation = validate_dynamic_script_boundary_receipt(
        embedded_boundary
    )
    if boundary_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"script_boundary_{item}" for item in boundary_validation["errors"]
        )
    expected_boundary = build_dynamic_script_boundary_receipt(
        script_evidence.get("audits"),
        script_evidence.get("receipts"),
        script_evidence.get("trust_denials"),
        script_evidence.get("failure_receipts"),
    )
    boundary_matches = embedded_boundary == expected_boundary
    if not boundary_matches:
        errors.append("script_boundary_mismatch")

    expected_evidence_digest = build_script_evidence_digest(
        script_evidence.get("audits"),
        script_evidence.get("receipts"),
        script_evidence.get("trust_denials"),
        script_evidence.get("failure_receipts"),
        script_evidence.get("declared_paths"),
        script_evidence.get("inventory"),
        script_evidence.get("execution_receipts"),
        script_evidence.get("boundary_receipt"),
    )
    evidence_digest_matches = (
        script_evidence.get("evidence_digest") == expected_evidence_digest
    )
    if not evidence_digest_matches:
        errors.append("script_evidence_digest_mismatch")

    receipts = script_evidence.get("receipts")
    audits = script_evidence.get("audits")
    receipts = receipts if isinstance(receipts, list) else []
    audits = audits if isinstance(audits, list) else []
    owner_families = {
        str(item.get("owner_family"))
        for item in receipts
        if isinstance(item, Mapping)
    }
    owner_family_consistent = not receipts or len(owner_families) == 1
    expected_owner_family = (
        next(iter(owner_families))
        if owner_family_consistent
        and row_by_name.get("sr.runtime", {}).get("family") == "python_random"
        else None
    )
    owner_receipts_valid = all(
        isinstance(item, Mapping)
        and item.get("owner_stream_name") == "sr.runtime"
        and item.get("owner_registry_digest") == expected_script_owner_digest
        and item.get("runtime_epoch") == expected_epoch
        and item.get("deterministic_ready") is True
        for item in receipts
    )
    audit_rows_valid = all(
        isinstance(item, Mapping)
        and item.get("deterministic_ready") is True
        and item.get("findings") == []
        for item in audits
    )
    diagnostic = diagnose_script_entropy_admission(
        audits,
        receipts,
        owner_family=expected_owner_family,
        runtime_epoch=expected_epoch if isinstance(expected_epoch, str) else None,
        owner_stream_name="sr.runtime" if receipts else None,
        owner_registry_digest=expected_script_owner_digest if receipts else None,
    )
    dynamic_script_corpus_valid = (
        corpus == {"valid": True, "errors": []}
        and descriptor == {"valid": True, "errors": []}
        and inventory == {"valid": True, "errors": []}
        and evidence_digest_matches
        and audit_rows_valid
        and owner_family_consistent
        and diagnostic["admitted"] is True
    )
    if not dynamic_script_corpus_valid:
        errors.append("dynamic_script_corpus_incomplete")

    dynamic_script_owner_bound = (
        owner_receipts_valid
        and expected_script_owner_digest is not None
        and script_evidence.get("owner_stream_name") == "sr.runtime"
        and script_evidence.get("owner_registry_digest")
        == expected_script_owner_digest
        and all(
            item.get("owner_family") in owner_families
            for item in receipts
            if isinstance(item, Mapping)
        )
    ) if receipts else (
        script_evidence.get("owner_stream_name") is None
        and script_evidence.get("owner_registry_digest") is None
    )
    if not dynamic_script_owner_bound:
        errors.append("dynamic_script_owner_binding_mismatch")

    boundary_closed = (
        isinstance(expected_boundary, Mapping)
        and expected_boundary.get("status") == "admitted"
        and expected_boundary.get("opaque_findings") is False
        and expected_boundary.get("corpus_valid") is True
    )
    dynamic_entropy_boundary_closed = (
        dynamic_script_corpus_valid
        and dynamic_script_owner_bound
        and boundary_matches
        and boundary_closed
    )
    if not dynamic_entropy_boundary_closed:
        errors.append("dynamic_entropy_boundary_not_closed")

    native_validation = validate_native_entropy_boundary_receipt(native_receipt)
    if native_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"native_receipt_{item}" for item in native_validation["errors"]
        )
    current_native_receipt = build_native_entropy_boundary_receipt(
        native_admission_evidence=native_admission_evidence,
    )
    native_receipt_source_bound = native_receipt == current_native_receipt
    if not native_receipt_source_bound:
        errors.append("native_receipt_source_mismatch")

    try:
        native_selection = build_native_backend_selection_evidence(
            native_capability,
            requested_backend=requested_native_backend,
            native_admission_evidence=native_admission_evidence,
        )
        selection_validation = {
            "valid": True,
            "errors": [],
        }
    except (TypeError, ValueError):
        native_selection = {}
        selection_validation = {
            "valid": False,
            "errors": ["native_backend_selection_invalid"],
        }
    if selection_validation != {"valid": True, "errors": []}:
        errors.extend(
            f"native_selection_{item}"
            for item in selection_validation["errors"]
        )

    selected_backend = native_selection.get("selected_backend_id")
    excluded = (
        native_runtime_available is False
        and selected_backend == "python"
        and native_selection.get("status") == "reference_python"
    )
    admitted_native = (
        native_runtime_available is True
        and selected_backend in {"cpp", "rust"}
        and native_selection.get("status") == "admitted"
        and native_receipt.get("status") == "admitted"
    )
    native_backend_excluded_or_admitted = excluded or admitted_native
    if not native_backend_excluded_or_admitted:
        errors.append("native_backend_neither_excluded_nor_admitted")
    native_closure_mode = (
        "excluded_from_selected_runtime"
        if excluded
        else "admitted_native_contract"
        if admitted_native
        else "open"
    )
    native_entropy_boundary_closed = (
        native_receipt_source_bound
        and native_backend_excluded_or_admitted
    )
    if not native_entropy_boundary_closed:
        errors.append("native_entropy_boundary_not_closed")

    process_global_entropy_isolated = (
        rng_draw_order.get("global_entropy_isolated") is True
        and snapshot.get("global_python_random_touched") is False
        and snapshot.get("global_numpy_random_touched") is False
    )
    if not process_global_entropy_isolated:
        errors.append("process_global_entropy_not_isolated")

    projection = {
        "rng_context_id": rng_draw_order.get("rng_context_id"),
        "shared_root_seed_digest": snapshot.get("root_seed_digest"),
        "stream_registration": rows,
        "native_runtime_adapter_available": native_runtime_available,
        "native_closure_mode": native_closure_mode,
        "shared_context_valid": shared_context_valid,
        "root_seed_derivation_bound": root_seed_derivation_bound,
        "lane_stream_families_valid": lane_stream_families_valid,
        "cross_lane_draw_order_valid": cross_lane_draw_order_valid,
        "dynamic_script_corpus_valid": dynamic_script_corpus_valid,
        "dynamic_script_owner_bound": dynamic_script_owner_bound,
        "dynamic_entropy_boundary_closed": dynamic_entropy_boundary_closed,
        "native_receipt_source_bound": native_receipt_source_bound,
        "native_backend_selection_valid": (
            selection_validation == {"valid": True, "errors": []}
        ),
        "native_backend_excluded_or_admitted": native_backend_excluded_or_admitted,
        "native_entropy_boundary_closed": native_entropy_boundary_closed,
        "process_global_entropy_isolated": process_global_entropy_isolated,
    }
    return list(dict.fromkeys(errors)), projection


def build_worldbridge_e554_shared_randomness_authority(
    *,
    rng_draw_order_witness: Mapping[str, Any],
    script_evidence: Mapping[str, Any],
    native_boundary_receipt: Mapping[str, Any],
    native_backend_capability: Mapping[str, Any],
    native_admission_evidence: Mapping[str, Any] | None = None,
    requested_native_backend: str = "auto",
    project_path: str | None = None,
) -> dict[str, Any]:
    """Build a detached shared-randomness witness from live owner evidence."""
    draw = _mapping_copy(rng_draw_order_witness, "rng_draw_order_witness")
    scripts = _mapping_copy(script_evidence, "script_evidence")
    native = _mapping_copy(
        native_boundary_receipt,
        "native_boundary_receipt",
    )
    capability = _mapping_copy(
        native_backend_capability,
        "native_backend_capability",
    )
    admission = (
        None
        if native_admission_evidence is None
        else _mapping_copy(
            native_admission_evidence,
            "native_admission_evidence",
        )
    )
    requested = str(requested_native_backend or "auto").strip().lower()
    project_root = None if project_path is None else str(project_path)
    errors, projection = _evaluate(
        rng_draw_order=draw,
        script_evidence=scripts,
        native_receipt=native,
        native_capability=capability,
        native_admission_evidence=admission,
        requested_native_backend=requested,
        project_path=project_root,
        native_runtime_available=_native_runtime_available(),
    )
    if errors:
        raise ValueError(
            "E554 shared randomness witness rejected: " + ",".join(errors)
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "rng_draw_order_witness": draw,
        "script_evidence": scripts,
        "native_boundary_receipt": native,
        "native_backend_capability": capability,
        "native_admission_evidence": admission,
        "requested_native_backend": requested,
        "project_path": project_root,
        **projection,
        "grants_admission": False,
        "admission_effect": ADMISSION_EFFECT,
        **{field: False for field in CLOSED_ADMISSION_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e554_shared_randomness_authority(
    value: object,
) -> dict[str, Any]:
    """Revalidate E554 from embedded producers instead of trusting booleans."""
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    allowed_key_sets = {
        frozenset(WITNESS_KEYS),
        frozenset(set(WITNESS_KEYS) - {"native_admission_evidence"}),
    }
    if frozenset(value) not in allowed_key_sets:
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

    draw = value.get("rng_draw_order_witness")
    scripts = value.get("script_evidence")
    native = value.get("native_boundary_receipt")
    capability = value.get("native_backend_capability")
    admission = value.get("native_admission_evidence")
    project_path = value.get("project_path")
    if not all(
        isinstance(item, Mapping)
        for item in (draw, scripts, native, capability)
    ):
        return {
            "valid": False,
            "errors": errors + ["witness_payload_invalid"],
        }
    requested = value.get("requested_native_backend")
    if not isinstance(requested, str):
        return {
            "valid": False,
            "errors": errors + ["requested_native_backend_invalid"],
        }
    if project_path is not None and not isinstance(project_path, str):
        return {
            "valid": False,
            "errors": errors + ["project_path_invalid"],
        }
    if admission is not None and not isinstance(admission, Mapping):
        return {
            "valid": False,
            "errors": errors + ["native_admission_evidence_invalid"],
        }
    native_runtime_available = value.get("native_runtime_adapter_available")
    if not isinstance(native_runtime_available, bool):
        return {
            "valid": False,
            "errors": errors + ["native_runtime_adapter_available_invalid"],
        }
    revalidation, projection = _evaluate(
        rng_draw_order=draw,
        script_evidence=scripts,
        native_receipt=native,
        native_capability=capability,
        native_admission_evidence=admission,
        requested_native_backend=requested,
        project_path=project_path,
        native_runtime_available=native_runtime_available,
    )
    errors.extend(revalidation)
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
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "SCRIPT_EVIDENCE_KEYS",
    "STATUS",
    "WITNESS_KEYS",
    "build_worldbridge_e554_shared_randomness_authority",
    "validate_worldbridge_e554_shared_randomness_authority",
]
