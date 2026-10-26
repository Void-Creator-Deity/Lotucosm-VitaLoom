# -*- coding: utf-8 -*-
"""Qt-free E266 cross-record attestation matrix over E265 witnesses."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_e264_envelope_consistency_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract as build_e264_contract,
)
from core.Lotucosm.runtime.world_bridge_e265_portable_witness_attestation import (
    FIXED_FALSE_AUTHORITY_FLAGS as E265_FIXED_FALSE_AUTHORITY_FLAGS,
    DO_NOT_CLAIM as E265_DO_NOT_CLAIM,
    STATUS as E265_STATUS,
    SCOPE as E265_SCOPE,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract as build_e265_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit as decode_e265_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit as validate_e265_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract as validate_e265_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_audit"
SCOPE = "e265_portable_witness_attestation_cross_record_attestation_matrix_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-contract-evolution-portable-witness-attestation-cross-record-attestation-matrix-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 96 * 1024
MAX_RECORD_BYTES = 64 * 1024
MAX_CONTRACT_BYTES = 32 * 1024
MAX_POLICY_BYTES = 16 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E265_MODULE = "core.Lotucosm.runtime.world_bridge_e265_portable_witness_attestation"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E265_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_portable_witness_attestation_cross_record_attestation_matrix_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_contract"
FIXED_FALSE_AUTHORITY_FLAGS = copy.deepcopy(E265_FIXED_FALSE_AUTHORITY_FLAGS)
DO_NOT_CLAIM = tuple(E265_DO_NOT_CLAIM) + ("cross_record_attestation_matrix_is_not_operational_authority",)

MATRIX_RECORD_KEYS = {
    "e265_audit_digest", "e265_portable_witness_attestation_digest",
    "e264_audit_digests", "e264_envelope_digests", "e264_cross_record_consistency_digests",
    "e263_aggregate_provenance_digest_lists", "e264_contract_digest", "e263_contract_digest",
    "e262_contract_digest", "e260_contract_digest", "e259_contract_digest", "e258_contract_digest",
    "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest",
    "contract_evolution_policy_digest", "source_order", "source_order_digest", "source_unit_digest",
}
MATRIX_KEYS = {
    "e265_audit_digests", "e265_portable_witness_attestation_digests", "e264_audit_digest_matrix",
    "e264_envelope_digest_matrix", "e264_cross_record_consistency_digest_matrix",
    "e263_aggregate_provenance_digest_matrix", "e265_contract_digest", "e264_contract_digests",
    "e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest",
    "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest",
    "contract_evolution_policy_digest", "source_orders", "source_order_digests", "source_unit_digests",
    "fixed_false_authority_flags", "records",
}
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "boundary_input_kind", "e265_status", "e265_scope", "e265_contract_digest", "corpus_size",
    "corpus_order", "corpus_order_digest", "corpus_record_digests", "corpus_record_digest",
    "e265_portable_witness_attestation_digests", "e265_portable_witness_attestation_digest",
    "cross_record_attestation_matrix", "cross_record_attestation_matrix_digest", "e265_contract_valid",
    "exact_current_identity_valid", "cross_record_attestation_matrix_valid", "deterministic_corpus_valid",
    "source_order", "source_order_digest", "source_unit_digest", "source_topology_valid", "do_not_claim",
    "audit_digest", *FIXED_FALSE_AUTHORITY_FLAGS,
}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_policy() -> dict[str, Any]:
    return {
        "schema_version": 1, "accepted_e265_schema_version": 1, "accepted_e265_status": E265_STATUS,
        "accepted_e265_scope": E265_SCOPE, "accepted_e265_contract_digest": _digest(build_e265_contract()),
        "exact_current_only": True, "cross_record_attestation_matrix_only": True,
        "migration_admitted": False, "mixed_version_admitted": False, "unknown_contract_admitted": False,
        "execution_admitted": False, "operational_compatibility_authority": False,
        "corpus_min_records": 2, "corpus_max_records": MAX_RECORDS,
    }


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_policy(policy: object) -> dict[str, Any]:
    if not isinstance(policy, Mapping):
        return {"valid": False, "errors": ["policy_not_mapping"]}
    expected = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_policy()
    valid = dict(policy) == expected
    return {"valid": valid, "errors": [] if valid else ["policy_drift"]}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(corpus: Sequence[bytes | bytearray | memoryview], contract_bytes: bytes | bytearray | memoryview, policy_bytes: bytes | bytearray | memoryview, source_units: Mapping[str, str], source_order: Sequence[str]) -> dict[str, Any]:
    contract = _exact_e265_contract(contract_bytes)
    _exact_policy(policy_bytes)
    records = _decode_corpus(corpus)
    if len(records) < 2:
        raise ValueError("E266 matrix requires at least two records")
    if records != sorted(records, key=lambda item: item["audit_digest"]):
        raise ValueError("E266 corpus order drift detected")
    order = [item["audit_digest"] for item in records]
    if len(set(order)) != len(order):
        raise ValueError("duplicate E265 audit record")
    source_order_value = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if not source_summary["source_topology_valid"]:
        raise ValueError("E266 source topology invalid")
    contract_digest = _digest(contract)
    rows = [_matrix_row(item, contract_digest, list(source_order_value), source_summary["source_unit_digest"]) for item in records]
    _validate_rows(rows)
    matrix = _build_matrix(rows, order, contract_digest)
    record_digests = [_digest(item) for item in records]
    witness_digests = [item["portable_witness_attestation_digest"] for item in records]
    result = {
        "schema_version": 1, "status": STATUS, "scope": SCOPE, "media_type": MEDIA_TYPE,
        "encoding": ENCODING, "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e265_portable_witness_attestation_audit_bytes",
        "e265_status": E265_STATUS, "e265_scope": E265_SCOPE, "e265_contract_digest": contract_digest,
        "corpus_size": len(records), "corpus_order": order, "corpus_order_digest": _digest(order),
        "corpus_record_digests": record_digests, "corpus_record_digest": _digest(record_digests),
        "e265_portable_witness_attestation_digests": witness_digests,
        "e265_portable_witness_attestation_digest": _digest(witness_digests),
        "cross_record_attestation_matrix": matrix, "cross_record_attestation_matrix_digest": _digest(matrix),
        "e265_contract_valid": True, "exact_current_identity_valid": True,
        "cross_record_attestation_matrix_valid": True, "deterministic_corpus_valid": True,
        "source_order": list(source_order_value), "source_order_digest": _digest(list(source_order_value)),
        "source_unit_digest": source_summary["source_unit_digest"], "source_topology_valid": True,
        "do_not_claim": list(DO_NOT_CLAIM), **copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
    }
    result["audit_digest"] = _audit_digest(result)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(result)["valid"] is not True:
        raise RuntimeError("constructed invalid E266 matrix")
    return copy.deepcopy(result)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value, errors = dict(audit), []
    if set(value) != REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (1, STATUS, SCOPE):
        errors.append("identity_invalid")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("canonical_metadata_invalid")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e265_portable_witness_attestation_audit_bytes":
        errors.append("boundary_input_kind_invalid")
    if (value.get("e265_status"), value.get("e265_scope")) != (E265_STATUS, E265_SCOPE):
        errors.append("e265_identity_invalid")
    if value.get("e265_contract_digest") != _digest(build_e265_contract()):
        errors.append("e265_contract_digest_mismatch")
    if validate_e265_contract(build_e265_contract())["valid"] is not True:
        errors.append("upstream_contract_invalid")
    size = value.get("corpus_size")
    size_valid = isinstance(size, int) and not isinstance(size, bool) and 2 <= size <= MAX_RECORDS
    if not size_valid:
        errors.append("corpus_size_invalid")
    order = value.get("corpus_order")
    if not (size_valid and _digest_list(order, size) and order == sorted(order) and len(set(order)) == len(order)):
        errors.append("corpus_order_invalid")
    record_digests = value.get("corpus_record_digests")
    if not _digest_list(record_digests, size):
        errors.append("corpus_record_digests_invalid")
    if _is_sha256(value.get("corpus_order_digest")) and value.get("corpus_order_digest") != _digest(order):
        errors.append("corpus_order_digest_mismatch")
    if _is_sha256(value.get("corpus_record_digest")) and value.get("corpus_record_digest") != _digest(record_digests):
        errors.append("corpus_record_digest_mismatch")
    witness = value.get("e265_portable_witness_attestation_digests")
    if not _digest_list(witness, size):
        errors.append("portable_witness_digest_list_invalid")
    if _is_sha256(value.get("e265_portable_witness_attestation_digest")) and value.get("e265_portable_witness_attestation_digest") != _digest(witness):
        errors.append("portable_witness_digest_mismatch")
    matrix = value.get("cross_record_attestation_matrix")
    if not isinstance(matrix, Mapping) or set(matrix) != MATRIX_KEYS:
        errors.append("matrix_shape_invalid")
    elif not _validate_matrix(matrix, value, order, witness):
        errors.append("matrix_invalid")
    if _is_sha256(value.get("cross_record_attestation_matrix_digest")) and value.get("cross_record_attestation_matrix_digest") != _digest(matrix):
        errors.append("matrix_digest_mismatch")
    if value.get("source_order") != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)):
        errors.append("source_order_mismatch")
    if not _is_sha256(value.get("source_unit_digest")):
        errors.append("source_unit_digest_invalid")
    if value.get("source_topology_valid") is not True:
        errors.append("source_topology_invalid")
    for key in ("e265_contract_valid", "exact_current_identity_valid", "cross_record_attestation_matrix_valid", "deterministic_corpus_valid"):
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


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(audit)["valid"] is not True:
        raise ValueError("invalid E266 matrix")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "E266 matrix"), "E266 matrix")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix(value)["valid"] is not True:
        raise ValueError("invalid E266 matrix")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {
        "schema_version": 1, "status": STATUS, "scope": SCOPE,
        "accepted_e265_status": E265_STATUS, "accepted_e265_scope": E265_SCOPE,
        "accepted_e265_contract_digest": _digest(build_e265_contract()),
        "required_source_units": list(REQUIRED_SOURCE_UNITS), "source_order": list(REQUIRED_SOURCE_UNITS),
        "corpus_min_records": 2, "corpus_max_records": MAX_RECORDS,
        "matrix_mode": "exact_current_cross_record_attestation_matrix_only",
        "explicit_input_dependency_closure_only": True,
        "static_policies": copy.deepcopy(E265_FIXED_FALSE_AUTHORITY_FLAGS),
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "matrix_record_keys": sorted(MATRIX_RECORD_KEYS), "matrix_keys": sorted(MATRIX_KEYS),
        "do_not_claim": list(DO_NOT_CLAIM), "actual_fresh_process_started": False,
        "ipc_transport_created": False, "contract_valid": True,
    }


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    expected = _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if contract.get(key) != expected[key]]
    if set(contract) != set(expected):
        errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _exact_e265_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E265 contract"), "E265 contract")
    if validate_e265_contract(value)["valid"] is not True or value != build_e265_contract():
        raise ValueError("E265 contract drift detected")
    return value


def _exact_policy(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_POLICY_BYTES, "E266 policy"), "E266 policy")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_cross_record_attestation_matrix_policy(value)["valid"] is not True:
        raise ValueError("E266 policy drift detected")
    return value


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence):
        raise ValueError("E266 corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS:
        raise ValueError("E266 corpus exceeds bounded record count")
    return [decode_e265_audit(_bounded(item, MAX_RECORD_BYTES, "E265 corpus record")) for item in corpus]


def _matrix_row(record: Mapping[str, Any], e265_contract_digest: str, source_order: list[str], source_unit_digest: str) -> dict[str, Any]:
    if validate_e265_audit(record)["valid"] is not True:
        raise ValueError("invalid E265 audit record")
    if record.get("schema_version") != 1 or record.get("status") != E265_STATUS or record.get("scope") != E265_SCOPE:
        raise ValueError("mixed E265 version or identity")
    if record.get("e264_contract_digest") != _digest(build_e264_contract()):
        raise ValueError("E265 upstream E264 contract identity drift")
    attestation = record.get("portable_witness_attestation")
    if not isinstance(attestation, Mapping):
        raise ValueError("E265 portable witness attestation missing")
    row = {key: copy.deepcopy(attestation.get(key)) for key in MATRIX_RECORD_KEYS}
    row.update({"e265_audit_digest": record["audit_digest"], "e265_portable_witness_attestation_digest": record["portable_witness_attestation_digest"], "e264_contract_digest": record["e264_contract_digest"], "source_order": list(source_order), "source_order_digest": _digest(list(source_order)), "source_unit_digest": source_unit_digest})
    if row.get("e265_audit_digest") != record["audit_digest"] or row.get("e265_portable_witness_attestation_digest") != record["portable_witness_attestation_digest"]:
        raise ValueError("E266 matrix row identity drift")
    return row


def _validate_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError("E266 matrix rows missing")
    shared_keys = ("e264_contract_digest", "e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest", "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest", "contract_evolution_policy_digest")
    first = rows[0]
    for row in rows:
        if set(row) != MATRIX_RECORD_KEYS:
            raise ValueError("E266 matrix row shape drift")
        if row.get("source_order") != list(REQUIRED_SOURCE_UNITS) or row.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)) or not _is_sha256(row.get("source_unit_digest")):
            raise ValueError("E266 row source identity drift")
        for key in shared_keys:
            if row.get(key) != first.get(key) or not _is_sha256(row.get(key)):
                raise ValueError("E266 cross-record identity drift")
        row_size = len(row.get("e264_audit_digests", []))
        for key in ("e264_audit_digests", "e264_envelope_digests", "e264_cross_record_consistency_digests"):
            if not _digest_list(row.get(key), row_size):
                raise ValueError("E266 upstream digest row invalid")
        aggregate = row.get("e263_aggregate_provenance_digest_lists")
        if not isinstance(aggregate, list) or len(aggregate) != row_size or any(not isinstance(items, list) or any(not _is_sha256(item) for item in items) for items in aggregate):
            raise ValueError("E266 provenance row invalid")


def _build_matrix(rows: Sequence[Mapping[str, Any]], e265_digests: list[str], contract_digest: str) -> dict[str, Any]:
    first = rows[0]
    return {
        "e265_audit_digests": e265_digests,
        "e265_portable_witness_attestation_digests": [row["e265_portable_witness_attestation_digest"] for row in rows],
        "e264_audit_digest_matrix": [row["e264_audit_digests"] for row in rows],
        "e264_envelope_digest_matrix": [row["e264_envelope_digests"] for row in rows],
        "e264_cross_record_consistency_digest_matrix": [row["e264_cross_record_consistency_digests"] for row in rows],
        "e263_aggregate_provenance_digest_matrix": [row["e263_aggregate_provenance_digest_lists"] for row in rows],
        "e265_contract_digest": contract_digest,
        "e264_contract_digests": [row["e264_contract_digest"] for row in rows],
        **{key: first[key] for key in ("e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest", "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest", "contract_evolution_policy_digest")},
        "source_orders": [row["source_order"] for row in rows], "source_order_digests": [row["source_order_digest"] for row in rows],
        "source_unit_digests": [row["source_unit_digest"] for row in rows],
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS), "records": [copy.deepcopy(row) for row in rows],
    }


def _validate_matrix(matrix: Mapping[str, Any], value: Mapping[str, Any], order: object, witness: object) -> bool:
    size = value.get("corpus_size")
    if not isinstance(size, int) or isinstance(size, bool) or not 2 <= size <= MAX_RECORDS:
        return False
    if not isinstance(order, list) or not isinstance(witness, list) or len(order) != size or len(witness) != size:
        return False
    if matrix.get("e265_audit_digests") != order or matrix.get("e265_portable_witness_attestation_digests") != witness:
        return False
    if matrix.get("fixed_false_authority_flags") != FIXED_FALSE_AUTHORITY_FLAGS or matrix.get("e265_contract_digest") != value.get("e265_contract_digest"):
        return False
    row_lists = {
        "e264_audit_digest_matrix": matrix.get("e264_audit_digest_matrix"),
        "e264_envelope_digest_matrix": matrix.get("e264_envelope_digest_matrix"),
        "e264_cross_record_consistency_digest_matrix": matrix.get("e264_cross_record_consistency_digest_matrix"),
        "e263_aggregate_provenance_digest_matrix": matrix.get("e263_aggregate_provenance_digest_matrix"),
    }
    if any(not isinstance(items, list) or len(items) != size for items in row_lists.values()):
        return False
    for key in ("e264_contract_digests", "source_orders", "source_order_digests", "source_unit_digests"):
        items = matrix.get(key)
        if not isinstance(items, list) or len(items) != size:
            return False
    if not all(_is_sha256(item) for item in matrix["e264_contract_digests"]):
        return False
    if not all(item == list(REQUIRED_SOURCE_UNITS) for item in matrix["source_orders"]):
        return False
    if not all(item == _digest(list(REQUIRED_SOURCE_UNITS)) for item in matrix["source_order_digests"]):
        return False
    if not all(_is_sha256(item) for item in matrix["source_unit_digests"]):
        return False
    rows = matrix.get("records")
    if not isinstance(rows, list) or len(rows) != size:
        return False
    if any(not isinstance(row, Mapping) or set(row) != MATRIX_RECORD_KEYS for row in rows):
        return False
    shared_keys = ("e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest", "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest", "contract_evolution_policy_digest")
    first = rows[0]
    if first.get("e264_contract_digest") != matrix["e264_contract_digests"][0]:
        return False
    for index, row in enumerate(rows):
        if row.get("e265_audit_digest") != order[index] or row.get("e265_portable_witness_attestation_digest") != witness[index]:
            return False
        if not _is_sha256(row.get("e265_audit_digest")) or not _is_sha256(row.get("e265_portable_witness_attestation_digest")):
            return False
        if row.get("source_order") != matrix["source_orders"][index] or row.get("source_order_digest") != matrix["source_order_digests"][index] or row.get("source_unit_digest") != matrix["source_unit_digests"][index]:
            return False
        if row.get("e264_contract_digest") != matrix["e264_contract_digests"][index] or not _is_sha256(row.get("e264_contract_digest")):
            return False
        if matrix["e264_audit_digest_matrix"][index] != row.get("e264_audit_digests") or matrix["e264_envelope_digest_matrix"][index] != row.get("e264_envelope_digests") or matrix["e264_cross_record_consistency_digest_matrix"][index] != row.get("e264_cross_record_consistency_digests") or matrix["e263_aggregate_provenance_digest_matrix"][index] != row.get("e263_aggregate_provenance_digest_lists"):
            return False
        row_size = row.get("e264_audit_digests")
        if not isinstance(row_size, list) or not row_size:
            return False
        if not _digest_list(row_size, len(row_size)) or not _digest_list(row.get("e264_envelope_digests"), len(row_size)) or not _digest_list(row.get("e264_cross_record_consistency_digests"), len(row_size)):
            return False
        aggregates = row.get("e263_aggregate_provenance_digest_lists")
        if not isinstance(aggregates, list) or len(aggregates) != len(row_size) or any(not isinstance(items, list) or not items or any(not _is_sha256(item) for item in items) for items in aggregates):
            return False
        if row.get("e265_audit_digest") != order[index]:
            return False
        for key in shared_keys:
            if row.get(key) != first.get(key) or not _is_sha256(row.get(key)):
                return False
    for key in shared_keys:
        if matrix.get(key) != first.get(key) or not _is_sha256(matrix.get(key)):
            return False
    return True


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray, memoryview)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("E266 source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS:
        raise ValueError("E266 source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS):
        raise ValueError("E266 source units must be exactly E265 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded E266 source unit")
        units[name] = text
    try:
        trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    except SyntaxError as exc:
        raise ValueError("invalid E266 source syntax") from exc
    edges: list[str] = []
    e265 = trees[E265_MODULE]
    required_e265_seams = (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_witness_attestation_audit_contract",
    )
    for seam in required_e265_seams:
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e265.body) != 1:
            edges.append(f"e265_seam_missing:{seam}")
    status_tree = trees[STATUS_MODULE]
    if not _imports_symbol(status_tree, __name__, CONTRACT_BUILDER):
        edges.append("status_e266_contract_import_missing")
    status_fn = _named_function(status_tree, "build_runtime_worldbridge_status", STATUS_MODULE)
    if CONTRACT_KEY not in _string_constants(status_fn) or MODULE_ID not in _string_constants(status_fn) or CONTRACT_BUILDER not in _called_names(status_fn):
        edges.append("status_e266_contract_registration_missing")
    forbidden_roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib", "import" + "lib"}
    forbidden_calls = {"op" + "en", "P" + "ath", "Pond", "Game" + "Viewport", "consume_worldbridge_quarantine_operator_presentation_receipt", "exec", "eval", "compile"}
    for module, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden_roots for alias in node.names):
                edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden_roots:
                edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.Call):
                name = _qualified_name(node.func)
                if name and name.rsplit(".", 1)[-1] in forbidden_calls:
                    edges.append(f"{module}:forbidden_call")
    return {"source_unit_digest": _digest({name: units[name] for name in REQUIRED_SOURCE_UNITS}), "source_topology_valid": not edges, "forbidden_edges": sorted(set(edges))}


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

