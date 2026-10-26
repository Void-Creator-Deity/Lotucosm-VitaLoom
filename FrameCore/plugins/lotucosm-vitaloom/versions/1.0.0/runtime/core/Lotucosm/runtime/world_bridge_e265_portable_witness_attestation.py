# -*- coding: utf-8 -*-
"""Qt-free E265 portable-witness attestation over E264 envelope audits."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_e264_envelope_consistency_audit import (
    CROSS_RECORD_KEYS as E264_CROSS_RECORD_KEYS,
    ENVELOPE_RECORD_KEYS as E264_ENVELOPE_RECORD_KEYS,
    FIXED_FALSE_AUTHORITY_FLAGS as E264_FIXED_FALSE_AUTHORITY_FLAGS,
    DO_NOT_CLAIM as E264_DO_NOT_CLAIM,
    STATUS as E264_STATUS,
    SCOPE as E264_SCOPE,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract as build_e264_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy as build_e264_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit as decode_e264_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit as validate_e264_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract as validate_e264_contract,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy as validate_e264_policy,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation_audit"
SCOPE = "e264_envelope_cross_record_consistency_portable_witness_attestation_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-contract-evolution-portable-corpus-witness-provenance-envelope-cross-record-consistency-portable-witness-attestation-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 64 * 1024
MAX_RECORD_BYTES = 32 * 1024
MAX_CONTRACT_BYTES = 24 * 1024
MAX_POLICY_BYTES = 16 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E264_MODULE = "core.Lotucosm.runtime.world_bridge_e264_envelope_consistency_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E264_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract"
FIXED_FALSE_AUTHORITY_FLAGS = copy.deepcopy(E264_FIXED_FALSE_AUTHORITY_FLAGS)
DO_NOT_CLAIM = tuple(E264_DO_NOT_CLAIM) + (
    "portable_witness_attestation_is_not_cross_record_operational_authority",
)
WITNESS_RECORD_KEYS = {
    "e264_audit_digest",
    "e264_envelope_digest",
    "e264_cross_record_consistency_digest",
    "e264_envelope",
    "e264_cross_record_consistency",
}
ATTESTATION_KEYS = {
    "e264_audit_digests",
    "e264_envelope_digests",
    "e264_cross_record_consistency_digests",
    "e264_contract_digest",
    "e263_contract_digest",
    "e262_contract_digest",
    "e260_contract_digest",
    "e259_contract_digest",
    "e258_contract_digest",
    "e257_contract_digest",
    "e256_contract_digest",
    "receipt_shape_digest",
    "contract_evolution_policy_digest",
    "source_orders",
    "source_order_digests",
    "source_unit_digests",
    "corpus_record_digests",
    "e263_aggregate_provenance_digest_lists",
    "fixed_false_authority_flags",
    "records",
}
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "boundary_input_kind", "e264_status", "e264_scope", "e264_contract_digest",
    "e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest",
    "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest",
    "contract_evolution_policy_digest", "corpus_size", "corpus_order", "corpus_order_digest",
    "corpus_record_digests", "corpus_record_digest", "e264_envelope_digests", "e264_envelope_digest",
    "e264_cross_record_consistency_digests", "e264_cross_record_consistency_digest",
    "e263_aggregate_provenance_digest_lists", "e263_aggregate_provenance_digest_matrix_digest",
    "portable_witness_attestation", "portable_witness_attestation_digest",
    "source_order", "source_order_digest", "source_unit_digest", "source_topology_valid",
    "e264_contract_valid", "e264_policy_valid", "exact_current_identity_valid",
    "cross_record_consistency_valid", "portable_witness_attestation_valid", "deterministic_corpus_valid",
    "audit_digest", "do_not_claim", *FIXED_FALSE_AUTHORITY_FLAGS,
}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "accepted_e264_schema_version": 1,
        "accepted_e264_status": E264_STATUS,
        "accepted_e264_scope": E264_SCOPE,
        "accepted_e264_contract_digest": _digest(build_e264_contract()),
        "exact_current_only": True,
        "portable_witness_attestation_only": True,
        "cross_record_consistency_only": True,
        "migration_admitted": False,
        "mixed_version_admitted": False,
        "unknown_contract_admitted": False,
        "execution_admitted": False,
        "operational_compatibility_authority": False,
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
    }


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation_policy(policy: object) -> dict[str, Any]:
    if not isinstance(policy, Mapping):
        return {"valid": False, "errors": ["policy_not_mapping"]}
    expected = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation_policy()
    valid = dict(policy) == expected
    return {"valid": valid, "errors": [] if valid else ["policy_drift"]}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation(
    e264_audit_corpus_bytes: Sequence[bytes | bytearray | memoryview],
    e264_contract_bytes: bytes | bytearray | memoryview,
    attestation_policy_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    e264_contract = _exact_e264_contract(e264_contract_bytes)
    _exact_policy(attestation_policy_bytes)
    records = _decode_corpus(e264_audit_corpus_bytes)
    if len(records) < 2:
        raise ValueError("portable witness attestation requires at least two records")
    if records != sorted(records, key=lambda record: record["audit_digest"]):
        raise ValueError("portable witness attestation corpus order drift detected")
    audit_digests = [record["audit_digest"] for record in records]
    if len(set(audit_digests)) != len(audit_digests):
        raise ValueError("duplicate E264 envelope audit record")

    source_order_value = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if not source_summary["source_topology_valid"]:
        raise ValueError("E265 source topology invalid: " + ",".join(source_summary["forbidden_edges"]))

    e264_contract_digest = _digest(e264_contract)
    first = records[0]
    first_envelope = _validated_e264_envelope(first, e264_contract_digest)
    first_shared = first_envelope["shared"]
    static_shared_keys = (
        "e263_contract_digest", "e262_contract_digest", "e260_contract_digest",
        "e259_contract_digest", "e258_contract_digest", "e257_contract_digest",
        "e256_contract_digest", "receipt_shape_digest", "contract_evolution_policy_digest",
        "fixed_false_authority_flags",
    )
    for record in records:
        if validate_e264_audit(record)["valid"] is not True:
            raise ValueError("invalid E264 envelope audit record")
        if record.get("schema_version") != 1 or record.get("status") != E264_STATUS or record.get("scope") != E264_SCOPE:
            raise ValueError("mixed E264 version or identity")
        envelope = _validated_e264_envelope(record, e264_contract_digest)
        shared = envelope["shared"]
        if any(shared.get(key) != first_shared.get(key) for key in static_shared_keys):
            raise ValueError("E264 cross-record static closure drift")
        if record.get("source_order") != first.get("source_order") or record.get("source_order_digest") != first.get("source_order_digest"):
            raise ValueError("E264 source order drift")
        if record.get("source_topology_valid") is not True:
            raise ValueError("E264 source topology closure is not valid")
        for key, expected in FIXED_FALSE_AUTHORITY_FLAGS.items():
            if record.get(key) is not expected or shared["fixed_false_authority_flags"].get(key) is not expected:
                raise ValueError("E264 authority flag drift")

    corpus_record_digests = [_digest(record) for record in records]
    envelope_digests = [_digest(record["aggregate_provenance_envelope"]) for record in records]
    consistency_digests = [_digest(record["cross_record_consistency"]) for record in records]
    aggregate_digest_lists = [
        list(record["aggregate_provenance_envelope"]["shared"]["aggregate_provenance_digests"])
        for record in records
    ]
    envelope_records = [
        {
            "e264_audit_digest": record["audit_digest"],
            "e264_envelope_digest": envelope_digest,
            "e264_cross_record_consistency_digest": consistency_digest,
            "e264_envelope": copy.deepcopy(record["aggregate_provenance_envelope"]),
            "e264_cross_record_consistency": copy.deepcopy(record["cross_record_consistency"]),
        }
        for record, envelope_digest, consistency_digest in zip(records, envelope_digests, consistency_digests)
    ]
    attestation = {
        "e264_audit_digests": audit_digests,
        "e264_envelope_digests": envelope_digests,
        "e264_cross_record_consistency_digests": consistency_digests,
        "e264_contract_digest": e264_contract_digest,
        "e263_contract_digest": first_shared["e263_contract_digest"],
        "e262_contract_digest": first_shared["e262_contract_digest"],
        "e260_contract_digest": first_shared["e260_contract_digest"],
        "e259_contract_digest": first_shared["e259_contract_digest"],
        "e258_contract_digest": first_shared["e258_contract_digest"],
        "e257_contract_digest": first_shared["e257_contract_digest"],
        "e256_contract_digest": first_shared["e256_contract_digest"],
        "receipt_shape_digest": first_shared["receipt_shape_digest"],
        "contract_evolution_policy_digest": first_shared["contract_evolution_policy_digest"],
        "source_orders": [record["source_order"] for record in records],
        "source_order_digests": [record["source_order_digest"] for record in records],
        "source_unit_digests": [first_shared["source_unit_digests"][index] for index, _record in enumerate(records)],
        "corpus_record_digests": corpus_record_digests,
        "e263_aggregate_provenance_digest_lists": aggregate_digest_lists,
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "records": envelope_records,
    }
    result = {
        "schema_version": 1,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e264_envelope_audit_bytes",
        "e264_status": E264_STATUS,
        "e264_scope": E264_SCOPE,
        "e264_contract_digest": e264_contract_digest,
        "e263_contract_digest": first_shared["e263_contract_digest"],
        "e262_contract_digest": first_shared["e262_contract_digest"],
        "e260_contract_digest": first_shared["e260_contract_digest"],
        "e259_contract_digest": first_shared["e259_contract_digest"],
        "e258_contract_digest": first_shared["e258_contract_digest"],
        "e257_contract_digest": first_shared["e257_contract_digest"],
        "e256_contract_digest": first_shared["e256_contract_digest"],
        "receipt_shape_digest": first_shared["receipt_shape_digest"],
        "contract_evolution_policy_digest": first_shared["contract_evolution_policy_digest"],
        "corpus_size": len(records),
        "corpus_order": audit_digests,
        "corpus_order_digest": _digest(audit_digests),
        "corpus_record_digests": corpus_record_digests,
        "corpus_record_digest": _digest(corpus_record_digests),
        "e264_envelope_digests": envelope_digests,
        "e264_envelope_digest": _digest(envelope_digests),
        "e264_cross_record_consistency_digests": consistency_digests,
        "e264_cross_record_consistency_digest": _digest(consistency_digests),
        "e263_aggregate_provenance_digest_lists": aggregate_digest_lists,
        "e263_aggregate_provenance_digest_matrix_digest": _digest(aggregate_digest_lists),
        "portable_witness_attestation": attestation,
        "portable_witness_attestation_digest": _digest(attestation),
        "source_order": list(source_order_value),
        "source_order_digest": _digest(list(source_order_value)),
        "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True,
        "e264_contract_valid": True,
        "e264_policy_valid": True,
        "exact_current_identity_valid": True,
        "cross_record_consistency_valid": True,
        "portable_witness_attestation_valid": True,
        "deterministic_corpus_valid": True,
        "do_not_claim": list(DO_NOT_CLAIM),
        **copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
    }
    result["audit_digest"] = _audit_digest(result)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(result)["valid"] is not True:
        raise RuntimeError("constructed invalid E265 portable witness attestation")
    return copy.deepcopy(result)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value, errors = dict(audit), []
    if set(value) != REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (1, STATUS, SCOPE):
        errors.append("identity_invalid")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("canonical_metadata_invalid")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e264_envelope_audit_bytes":
        errors.append("boundary_input_kind_invalid")
    if (value.get("e264_status"), value.get("e264_scope")) != (E264_STATUS, E264_SCOPE):
        errors.append("e264_identity_invalid")
    if value.get("e264_contract_digest") != _digest(build_e264_contract()):
        errors.append("e264_contract_digest_mismatch")
    if validate_e264_contract(build_e264_contract())["valid"] is not True or validate_e264_policy(build_e264_policy())["valid"] is not True:
        errors.append("upstream_contract_or_policy_invalid")

    size = value.get("corpus_size")
    size_valid = isinstance(size, int) and not isinstance(size, bool) and 2 <= size <= MAX_RECORDS
    if not size_valid:
        errors.append("corpus_size_invalid")
    order = value.get("corpus_order")
    order_valid = size_valid and _digest_list(order, size) and order == sorted(order) and len(set(order)) == len(order)
    if not order_valid:
        errors.append("corpus_order_invalid")
    record_digests = value.get("corpus_record_digests")
    envelope_digests = value.get("e264_envelope_digests")
    consistency_digests = value.get("e264_cross_record_consistency_digests")
    if not _digest_list(record_digests, size):
        errors.append("corpus_record_digests_invalid")
    if not _digest_list(envelope_digests, size):
        errors.append("e264_envelope_digests_invalid")
    if not _digest_list(consistency_digests, size):
        errors.append("e264_consistency_digests_invalid")
    if _is_sha256(value.get("corpus_order_digest")) and value.get("corpus_order_digest") != _digest(order):
        errors.append("corpus_order_digest_mismatch")
    if _is_sha256(value.get("corpus_record_digest")) and value.get("corpus_record_digest") != _digest(record_digests):
        errors.append("corpus_record_digest_mismatch")
    if _is_sha256(value.get("e264_envelope_digest")) and value.get("e264_envelope_digest") != _digest(envelope_digests):
        errors.append("e264_envelope_digest_mismatch")
    if _is_sha256(value.get("e264_cross_record_consistency_digest")) and value.get("e264_cross_record_consistency_digest") != _digest(consistency_digests):
        errors.append("e264_consistency_digest_mismatch")

    aggregate_lists = value.get("e263_aggregate_provenance_digest_lists")
    matrix_valid = (
        isinstance(aggregate_lists, list)
        and size_valid
        and len(aggregate_lists) == size
        and all(isinstance(items, list) and all(_is_sha256(item) for item in items) for items in aggregate_lists)
    )
    if not matrix_valid:
        errors.append("aggregate_provenance_digest_matrix_invalid")
    if matrix_valid and value.get("e263_aggregate_provenance_digest_matrix_digest") != _digest(aggregate_lists):
        errors.append("aggregate_provenance_digest_matrix_digest_mismatch")

    attestation = value.get("portable_witness_attestation")
    if not isinstance(attestation, Mapping) or set(attestation) != ATTESTATION_KEYS:
        errors.append("portable_witness_attestation_shape_invalid")
    else:
        if not _validate_attestation(attestation, value, order, record_digests, envelope_digests, consistency_digests, aggregate_lists):
            errors.append("portable_witness_attestation_invalid")
    if _is_sha256(value.get("portable_witness_attestation_digest")) and value.get("portable_witness_attestation_digest") != _digest(attestation):
        errors.append("portable_witness_attestation_digest_mismatch")

    source_order = value.get("source_order")
    if source_order != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)):
        errors.append("source_order_mismatch")
    if not _is_sha256(value.get("source_unit_digest")):
        errors.append("source_unit_digest_invalid")
    if value.get("source_topology_valid") is not True:
        errors.append("source_topology_invalid")
    for key in ("e264_contract_valid", "e264_policy_valid", "exact_current_identity_valid", "cross_record_consistency_valid", "portable_witness_attestation_valid", "deterministic_corpus_valid"):
        if value.get(key) is not True:
            errors.append(f"{key}_mismatch")
    for key, expected in FIXED_FALSE_AUTHORITY_FLAGS.items():
        if value.get(key) is not expected:
            errors.append(f"authority_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(audit)["valid"] is not True:
        raise ValueError("invalid E265 portable witness attestation")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "E265 portable witness attestation"), "E265 portable witness attestation")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit(value)["valid"] is not True:
        raise ValueError("invalid E265 portable witness attestation")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": STATUS,
        "scope": SCOPE,
        "accepted_e264_status": E264_STATUS,
        "accepted_e264_scope": E264_SCOPE,
        "accepted_e264_contract_digest": _digest(build_e264_contract()),
        "required_source_units": list(REQUIRED_SOURCE_UNITS),
        "source_order": list(REQUIRED_SOURCE_UNITS),
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
        "attestation_mode": "exact_current_portable_witness_attestation_only",
        "explicit_input_dependency_closure_only": True,
        "static_policies": copy.deepcopy(E264_FIXED_FALSE_AUTHORITY_FLAGS),
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "witness_record_keys": sorted(WITNESS_RECORD_KEYS),
        "attestation_keys": sorted(ATTESTATION_KEYS),
        "do_not_claim": list(DO_NOT_CLAIM),
        "actual_fresh_process_started": False,
        "ipc_transport_created": False,
        "contract_valid": True,
    }


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    value, expected = dict(contract), _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected):
        errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _exact_e264_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E264 contract"), "E264 contract")
    if validate_e264_contract(value)["valid"] is not True or value != build_e264_contract():
        raise ValueError("E264 contract drift detected")
    return value


def _exact_policy(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_POLICY_BYTES, "E265 policy"), "E265 policy")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_portable_witness_attestation_policy(value)["valid"] is not True:
        raise ValueError("E265 policy drift detected")
    return value


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence):
        raise ValueError("E265 corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS:
        raise ValueError("E265 corpus exceeds bounded record count")
    return [decode_e264_audit(_bounded(item, MAX_RECORD_BYTES, "E264 corpus record")) for item in corpus]


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("E265 source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS:
        raise ValueError("E265 source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS):
        raise ValueError("E265 source units must be exactly E264 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded E265 source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e264 = trees[E264_MODULE]
    seams = (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract",
    )
    for seam in seams:
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e264.body) != 1:
            edges.append(f"e264_seam_missing:{seam}")
    status = _named_function(trees[STATUS_MODULE], "build_runtime_worldbridge_status", STATUS_MODULE)
    if not _imports_symbol(trees[STATUS_MODULE], __name__, CONTRACT_BUILDER):
        edges.append("status_contract_import_missing")
    if CONTRACT_KEY not in _string_constants(status) or MODULE_ID not in _string_constants(status) or CONTRACT_BUILDER not in _called_names(status):
        edges.append("status_contract_registration_missing")
    roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib", "import" + "lib"}
    calls = {"op" + "en", "P" + "ath", "Pond", "Game" + "Viewport", "consume_worldbridge_quarantine_operator_presentation_receipt", "exec", "eval", "compile"}
    for module, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in roots for alias in node.names):
                edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in roots:
                edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.Call):
                name = _qualified_name(node.func)
                if name and name.rsplit(".", 1)[-1] in calls:
                    edges.append(f"{module}:forbidden_call")
    return {
        "source_unit_digest": _digest({name: units[name] for name in REQUIRED_SOURCE_UNITS}),
        "source_topology_valid": not edges,
        "forbidden_edges": sorted(set(edges)),
    }


def _validated_e264_envelope(record: Mapping[str, Any], e264_contract_digest: str) -> dict[str, Any]:
    envelope = record.get("aggregate_provenance_envelope")
    consistency = record.get("cross_record_consistency")
    if not isinstance(envelope, Mapping) or set(envelope) != {"records", "shared"}:
        raise ValueError("E264 envelope shape drift detected")
    if not isinstance(consistency, Mapping) or set(consistency) != E264_CROSS_RECORD_KEYS:
        raise ValueError("E264 consistency shape drift detected")
    if record.get("aggregate_provenance_envelope_digest") != _digest(envelope):
        raise ValueError("E264 envelope digest drift detected")
    if record.get("cross_record_consistency_digest") != _digest(consistency):
        raise ValueError("E264 consistency digest drift detected")
    envelope_records = envelope.get("records")
    shared = envelope.get("shared")
    if not isinstance(envelope_records, list) or not isinstance(shared, Mapping) or set(shared) != E264_CROSS_RECORD_KEYS:
        raise ValueError("E264 envelope payload shape drift detected")
    if len(envelope_records) != record.get("corpus_size"):
        raise ValueError("E264 envelope record count drift detected")
    for item in envelope_records:
        if not isinstance(item, Mapping) or set(item) != E264_ENVELOPE_RECORD_KEYS:
            raise ValueError("E264 nested envelope record shape drift detected")
        aggregate = item.get("aggregate_provenance")
        if not isinstance(aggregate, Mapping) or item.get("aggregate_provenance_digest") != _digest(aggregate):
            raise ValueError("E264 nested aggregate provenance drift detected")
    if dict(consistency) != dict(shared):
        raise ValueError("E264 consistency/shared payload drift detected")
    if shared.get("fixed_false_authority_flags") != FIXED_FALSE_AUTHORITY_FLAGS:
        raise ValueError("E264 fixed authority flags drift detected")
    if e264_contract_digest != _digest(build_e264_contract()):
        raise ValueError("E264 contract digest closure drift detected")
    if shared.get("e263_contract_digest") != build_e264_contract().get("accepted_e263_contract_digest"):
        raise ValueError("E264 accepted E263 identity drift detected")
    return {"records": copy.deepcopy(envelope_records), "shared": copy.deepcopy(shared)}


def _validate_attestation(attestation: Mapping[str, Any], value: Mapping[str, Any], order: object, record_digests: object, envelope_digests: object, consistency_digests: object, aggregate_lists: object) -> bool:
    if attestation.get("e264_audit_digests") != order or attestation.get("e264_envelope_digests") != envelope_digests or attestation.get("e264_cross_record_consistency_digests") != consistency_digests:
        return False
    if attestation.get("e264_contract_digest") != value.get("e264_contract_digest"):
        return False
    for key in ("e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest", "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest", "contract_evolution_policy_digest"):
        if not _is_sha256(attestation.get(key)) or attestation.get(key) != value.get(key):
            return False
    for key in ("source_orders", "source_order_digests", "source_unit_digests"):
        if not isinstance(attestation.get(key), list) or len(attestation[key]) != value.get("corpus_size"):
            return False
    if attestation.get("corpus_record_digests") != record_digests or attestation.get("e263_aggregate_provenance_digest_lists") != aggregate_lists:
        return False
    if attestation.get("fixed_false_authority_flags") != FIXED_FALSE_AUTHORITY_FLAGS:
        return False
    records = attestation.get("records")
    if not isinstance(records, list) or len(records) != value.get("corpus_size"):
        return False
    for index, item in enumerate(records):
        if not isinstance(item, Mapping) or set(item) != WITNESS_RECORD_KEYS:
            return False
        if item.get("e264_audit_digest") != order[index] or item.get("e264_envelope_digest") != envelope_digests[index] or item.get("e264_cross_record_consistency_digest") != consistency_digests[index]:
            return False
        envelope = item.get("e264_envelope")
        consistency = item.get("e264_cross_record_consistency")
        if not isinstance(envelope, Mapping) or set(envelope) != {"records", "shared"} or not isinstance(consistency, Mapping) or set(consistency) != E264_CROSS_RECORD_KEYS:
            return False
        if _digest(envelope) != envelope_digests[index] or _digest(consistency) != consistency_digests[index] or dict(envelope["shared"]) != dict(consistency):
            return False
        shared = envelope.get("shared")
        if not isinstance(shared, Mapping) or shared.get("fixed_false_authority_flags") != FIXED_FALSE_AUTHORITY_FLAGS:
            return False
        nested = envelope.get("records")
        if not isinstance(nested, list):
            return False
        if [nested_item.get("aggregate_provenance_digest") for nested_item in nested if isinstance(nested_item, Mapping)] != aggregate_lists[index]:
            return False
    return True


def _bounded(data: bytes | bytearray | memoryview, limit: int, label: str) -> bytes:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(f"{label} must be bytes-like")
    raw = bytes(data)
    if len(raw) > limit:
        raise ValueError(f"{label} exceeds bounded size")
    return raw


def _decode_canonical_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid canonical {label}") from exc
    if not isinstance(value, dict) or _canonical_json_bytes(value) != raw:
        raise ValueError(f"{label} is non-canonical")
    return value


def _named_function(tree: ast.Module, name: str, module: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"{module} must define exactly one {name}")
    return matches[0]


def _imports_symbol(tree: ast.AST, module: str, symbol: str) -> bool:
    return any(isinstance(node, ast.ImportFrom) and node.module == module and any(alias.name == symbol for alias in node.names) for node in ast.walk(tree))


def _called_names(tree: ast.AST) -> set[str]:
    return {name for node in ast.walk(tree) if isinstance(node, ast.Call) if (name := _qualified_name(node.func))}


def _string_constants(tree: ast.AST) -> set[str]:
    return {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _qualified_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _audit_digest(value: Mapping[str, Any]) -> str:
    copied = dict(value)
    copied.pop("audit_digest", None)
    return _digest(copied)


def _digest_list(value: object, expected_size: object) -> bool:
    return isinstance(value, list) and isinstance(expected_size, int) and not isinstance(expected_size, bool) and len(value) == expected_size and all(_is_sha256(item) for item in value)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")





