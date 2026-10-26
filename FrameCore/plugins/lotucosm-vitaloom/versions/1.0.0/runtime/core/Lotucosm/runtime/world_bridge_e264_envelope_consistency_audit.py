# -*- coding: utf-8 -*-
"""Qt-free E264 aggregate-provenance envelope cross-record consistency audit."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_e263_aggregate_provenance_audit import (
    AGGREGATE_PROVENANCE_KEYS as E263_AGGREGATE_KEYS,
    DO_NOT_CLAIM as E263_DO_NOT_CLAIM,
    STATIC_POLICIES as E263_STATIC_POLICIES,
    STATUS as E263_STATUS,
    SCOPE as E263_SCOPE,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract as build_e263_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy as build_e263_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit as decode_e263_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit as validate_e263_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract as validate_e263_contract,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy as validate_e263_policy,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit"
SCOPE = "e263_aggregate_provenance_envelope_cross_record_consistency_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-contract-evolution-portable-corpus-witness-provenance-envelope-cross-record-consistency-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 28 * 1024
MAX_RECORD_BYTES = 24 * 1024
MAX_CONTRACT_BYTES = 16 * 1024
MAX_POLICY_BYTES = 16 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E263_MODULE = "core.Lotucosm.runtime.world_bridge_e263_aggregate_provenance_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E263_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract"
FIXED_FALSE_AUTHORITY_FLAGS = {
    **E263_STATIC_POLICIES,
    "actual_fresh_process_started": False,
    "ipc_transport_created": False,
    "default_ready": False,
    "unified_pond_enabled": False,
}
DO_NOT_CLAIM = tuple(E263_DO_NOT_CLAIM) + (
    "aggregate_provenance_envelope_is_not_cross_record_operational_authority",
)
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "boundary_input_kind", "e263_status", "e263_scope", "e263_contract_digest",
    "corpus_size", "corpus_order", "corpus_order_digest", "corpus_record_digests",
    "corpus_record_digest", "aggregate_provenance_digests", "aggregate_provenance_digest",
    "aggregate_provenance_envelope", "aggregate_provenance_envelope_digest",
    "cross_record_consistency", "cross_record_consistency_digest",
    "e263_source_order", "e263_source_order_digest", "e263_source_unit_digest",
    "e263_source_topology_valid", "e263_contract_valid", "e263_policy_valid",
    "exact_current_identity_valid", "cross_record_consistency_valid",
    "aggregate_provenance_envelope_valid", "deterministic_envelope_valid",
    "source_order", "source_order_digest", "source_unit_digest", "source_topology_valid",
    "audit_digest", "do_not_claim", *FIXED_FALSE_AUTHORITY_FLAGS,
}
ENVELOPE_RECORD_KEYS = {
    "audit_digest", "corpus_record_digest", "aggregate_provenance_digest", "aggregate_provenance",
}
CROSS_RECORD_KEYS = {
    "e263_contract_digest", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest",
    "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest",
    "contract_evolution_policy_digest", "source_orders", "source_order_digests", "source_unit_digests",
    "source_topology_values", "fixed_false_authority_flags", "corpus_record_digests",
    "aggregate_provenance_digests",
}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "accepted_e263_schema_version": 1,
        "accepted_e263_status": E263_STATUS,
        "accepted_e263_scope": E263_SCOPE,
        "accepted_e263_contract_digest": _digest(build_e263_contract()),
        "exact_current_only": True,
        "cross_record_consistency_only": True,
        "migration_admitted": False,
        "mixed_version_admitted": False,
        "unknown_contract_admitted": False,
        "execution_admitted": False,
        "operational_compatibility_authority": False,
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
    }


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy(policy: object) -> dict[str, Any]:
    if not isinstance(policy, Mapping):
        return {"valid": False, "errors": ["policy_not_mapping"]}
    expected = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy()
    valid = dict(policy) == expected
    return {"valid": valid, "errors": [] if valid else ["policy_drift"]}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency(
    e263_audit_corpus_bytes: Sequence[bytes | bytearray | memoryview],
    e263_contract_bytes: bytes | bytearray | memoryview,
    envelope_policy_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    e263_contract = _exact_e263_contract(e263_contract_bytes)
    _exact_policy(envelope_policy_bytes)
    records = _decode_corpus(e263_audit_corpus_bytes)
    if len(records) < 2:
        raise ValueError("aggregate provenance envelope requires at least two records")
    if records != sorted(records, key=lambda record: record["audit_digest"]):
        raise ValueError("aggregate provenance envelope corpus order drift detected")
    audit_digests = [record["audit_digest"] for record in records]
    if len(set(audit_digests)) != len(audit_digests):
        raise ValueError("duplicate E263 aggregate provenance record")

    e263_contract_digest = _digest(e263_contract)
    source_order_value = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if not source_summary["source_topology_valid"]:
        raise ValueError("E264 source topology invalid: " + ",".join(source_summary["forbidden_edges"]))

    common_keys = (
        "status", "scope", "e262_contract_digest", "e260_contract_digest", "e259_contract_digest",
        "e258_contract_digest", "e257_contract_digest", "e256_contract_digest", "receipt_shape_digest",
        "contract_evolution_policy_digest", "source_topology_valid",
    )
    first = records[0]
    record_source_order = first.get("source_order")
    record_source_order_digest = first.get("source_order_digest")
    for record in records:
        if validate_e263_audit(record)["valid"] is not True:
            raise ValueError("invalid E263 aggregate provenance record")
        if record.get("schema_version") != 1 or record.get("status") != E263_STATUS or record.get("scope") != E263_SCOPE:
            raise ValueError("mixed E263 version or identity")
        if record.get("aggregate_provenance_valid") is not True:
            raise ValueError("E263 aggregate provenance closure is not valid")
        aggregate = record.get("aggregate_provenance")
        if not isinstance(aggregate, Mapping) or set(aggregate) != E263_AGGREGATE_KEYS:
            raise ValueError("E263 aggregate provenance payload shape drift")
        if record.get("aggregate_provenance_digest") != _digest(aggregate):
            raise ValueError("E263 aggregate provenance digest drift")
        if any(record.get(key) != first.get(key) for key in common_keys):
            raise ValueError("E263 cross-record shared field drift")
        if record.get("source_order") != record_source_order:
            raise ValueError("E263 record source order drift")
        if record.get("source_order_digest") != record_source_order_digest:
            raise ValueError("E263 record source order digest drift")
        if record.get("source_topology_valid") is not True:
            raise ValueError("E263 source topology closure is not valid")
        for key, expected in E263_STATIC_POLICIES.items():
            if record.get(key) is not expected:
                raise ValueError("E263 authority flag drift")

    corpus_record_digests = [_digest(record) for record in records]
    aggregate_digests = [record["aggregate_provenance_digest"] for record in records]
    envelope_records = [
        {
            "audit_digest": record["audit_digest"],
            "corpus_record_digest": record_digest,
            "aggregate_provenance_digest": record["aggregate_provenance_digest"],
            "aggregate_provenance": copy.deepcopy(record["aggregate_provenance"]),
        }
        for record, record_digest in zip(records, corpus_record_digests)
    ]
    shared = {
        "e263_contract_digest": e263_contract_digest,
        "e262_contract_digest": first["e262_contract_digest"],
        "e260_contract_digest": first["e260_contract_digest"],
        "e259_contract_digest": first["e259_contract_digest"],
        "e258_contract_digest": first["e258_contract_digest"],
        "e257_contract_digest": first["e257_contract_digest"],
        "e256_contract_digest": first["e256_contract_digest"],
        "receipt_shape_digest": first["receipt_shape_digest"],
        "contract_evolution_policy_digest": first["contract_evolution_policy_digest"],
        "source_orders": [record["source_order"] for record in records],
        "source_order_digests": [record["source_order_digest"] for record in records],
        "source_unit_digests": [record["source_unit_digest"] for record in records],
        "source_topology_values": [record["source_topology_valid"] for record in records],
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "corpus_record_digests": corpus_record_digests,
        "aggregate_provenance_digests": aggregate_digests,
    }
    envelope = {"records": envelope_records, "shared": shared}
    consistency = copy.deepcopy(shared)
    result = {
        "schema_version": 1,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e263_aggregate_provenance_audit_bytes",
        "e263_status": E263_STATUS,
        "e263_scope": E263_SCOPE,
        "e263_contract_digest": e263_contract_digest,
        "corpus_size": len(records),
        "corpus_order": audit_digests,
        "corpus_order_digest": _digest(audit_digests),
        "corpus_record_digests": corpus_record_digests,
        "corpus_record_digest": _digest(corpus_record_digests),
        "aggregate_provenance_digests": aggregate_digests,
        "aggregate_provenance_digest": _digest(aggregate_digests),
        "aggregate_provenance_envelope": envelope,
        "aggregate_provenance_envelope_digest": _digest(envelope),
        "cross_record_consistency": consistency,
        "cross_record_consistency_digest": _digest(consistency),
        "e263_source_order": list(source_order_value),
        "e263_source_order_digest": _digest(list(source_order_value)),
        "e263_source_unit_digest": source_summary["source_unit_digest"],
        "e263_source_topology_valid": True,
        "e263_contract_valid": True,
        "e263_policy_valid": True,
        "exact_current_identity_valid": True,
        "cross_record_consistency_valid": True,
        "aggregate_provenance_envelope_valid": True,
        "deterministic_envelope_valid": True,
        "source_order": list(source_order_value),
        "source_order_digest": _digest(list(source_order_value)),
        "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True,
        "do_not_claim": list(DO_NOT_CLAIM),
        **copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
    }
    result["audit_digest"] = _audit_digest(result)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(result)["valid"] is not True:
        raise RuntimeError("constructed invalid E264 envelope audit")
    return copy.deepcopy(result)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value, errors = dict(audit), []
    if set(value) != REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if value.get("schema_version") != 1 or value.get("status") != STATUS or value.get("scope") != SCOPE:
        errors.append("identity_invalid")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("canonical_metadata_invalid")
    if value.get("e263_status") != E263_STATUS or value.get("e263_scope") != E263_SCOPE:
        errors.append("e263_identity_invalid")
    if value.get("e263_contract_digest") != _digest(build_e263_contract()):
        errors.append("e263_contract_digest_mismatch")
    if validate_e263_contract(build_e263_contract())["valid"] is not True or validate_e263_policy(build_e263_policy())["valid"] is not True:
        errors.append("upstream_contract_or_policy_invalid")
    size = value.get("corpus_size")
    order = value.get("corpus_order")
    record_digests = value.get("corpus_record_digests")
    aggregate_digests = value.get("aggregate_provenance_digests")
    if not isinstance(size, int) or isinstance(size, bool) or not 2 <= size <= MAX_RECORDS:
        errors.append("corpus_size_invalid")
    if not _digest_list(order, size):
        errors.append("corpus_order_invalid")
    if not _digest_list(record_digests, size):
        errors.append("corpus_record_digests_invalid")
    if not _digest_list(aggregate_digests, size):
        errors.append("aggregate_provenance_digests_invalid")
    if _is_sha256(value.get("corpus_order_digest")) and value.get("corpus_order_digest") != _digest(order):
        errors.append("corpus_order_digest_mismatch")
    if _is_sha256(value.get("corpus_record_digest")) and value.get("corpus_record_digest") != _digest(record_digests):
        errors.append("corpus_record_digest_mismatch")
    if _is_sha256(value.get("aggregate_provenance_digest")) and value.get("aggregate_provenance_digest") != _digest(aggregate_digests):
        errors.append("aggregate_provenance_digest_mismatch")

    envelope = value.get("aggregate_provenance_envelope")
    consistency = value.get("cross_record_consistency")
    if not isinstance(envelope, Mapping) or set(envelope) != {"records", "shared"}:
        errors.append("aggregate_provenance_envelope_shape_invalid")
    else:
        envelope_records = envelope.get("records")
        shared = envelope.get("shared")
        if not isinstance(envelope_records, list) or len(envelope_records) != size:
            errors.append("aggregate_provenance_envelope_records_invalid")
        else:
            for item, audit_digest, record_digest, aggregate_digest in zip(envelope_records, order or (), record_digests or (), aggregate_digests or ()):
                if not isinstance(item, Mapping) or set(item) != ENVELOPE_RECORD_KEYS:
                    errors.append("aggregate_provenance_envelope_record_shape_invalid")
                    continue
                aggregate = item.get("aggregate_provenance")
                if item.get("audit_digest") != audit_digest or item.get("corpus_record_digest") != record_digest or item.get("aggregate_provenance_digest") != aggregate_digest:
                    errors.append("aggregate_provenance_envelope_record_mismatch")
                if not isinstance(aggregate, Mapping) or set(aggregate) != E263_AGGREGATE_KEYS or item.get("aggregate_provenance_digest") != _digest(aggregate):
                    errors.append("aggregate_provenance_envelope_payload_invalid")
        if not _validate_shared(shared, value, order, record_digests, aggregate_digests):
            errors.append("aggregate_provenance_envelope_shared_invalid")
    if _is_sha256(value.get("aggregate_provenance_envelope_digest")) and value.get("aggregate_provenance_envelope_digest") != _digest(envelope):
        errors.append("aggregate_provenance_envelope_digest_mismatch")
    if not isinstance(consistency, Mapping) or set(consistency) != CROSS_RECORD_KEYS:
        errors.append("cross_record_consistency_shape_invalid")
    elif _canonical_json_bytes(consistency) != _canonical_json_bytes(value.get("aggregate_provenance_envelope", {}).get("shared", {})):
        errors.append("cross_record_consistency_payload_mismatch")
    if _is_sha256(value.get("cross_record_consistency_digest")) and value.get("cross_record_consistency_digest") != _digest(consistency):
        errors.append("cross_record_consistency_digest_mismatch")

    source_order = value.get("source_order")
    if source_order != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)):
        errors.append("source_order_mismatch")
    if value.get("e263_source_order") != source_order or value.get("e263_source_order_digest") != value.get("source_order_digest"):
        errors.append("e263_source_order_mismatch")
    if not _is_sha256(value.get("source_unit_digest")) or value.get("e263_source_unit_digest") != value.get("source_unit_digest"):
        errors.append("source_unit_digest_mismatch")
    if value.get("e263_source_topology_valid") is not True or value.get("source_topology_valid") is not True:
        errors.append("source_topology_invalid")
    for key in ("e263_contract_valid", "e263_policy_valid", "exact_current_identity_valid", "cross_record_consistency_valid", "aggregate_provenance_envelope_valid", "deterministic_envelope_valid"):
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


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(audit)["valid"] is not True:
        raise ValueError("invalid E264 envelope audit")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "E264 envelope audit"), "E264 envelope audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit(value)["valid"] is not True:
        raise ValueError("invalid E264 envelope audit")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": STATUS,
        "scope": SCOPE,
        "accepted_e263_status": E263_STATUS,
        "accepted_e263_scope": E263_SCOPE,
        "accepted_e263_contract_digest": _digest(build_e263_contract()),
        "required_source_units": list(REQUIRED_SOURCE_UNITS),
        "source_order": list(REQUIRED_SOURCE_UNITS),
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
        "envelope_mode": "exact_current_cross_record_consistency_only",
        "explicit_input_dependency_closure_only": True,
        "static_policies": copy.deepcopy(E263_STATIC_POLICIES),
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "envelope_record_keys": sorted(ENVELOPE_RECORD_KEYS),
        "cross_record_consistency_keys": sorted(CROSS_RECORD_KEYS),
        "do_not_claim": list(DO_NOT_CLAIM),
        "actual_fresh_process_started": False,
        "ipc_transport_created": False,
        "contract_valid": True,
    }


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    value, expected = dict(contract), _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected):
        errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _exact_e263_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E263 contract"), "E263 contract")
    if validate_e263_contract(value)["valid"] is not True or value != build_e263_contract():
        raise ValueError("E263 contract drift detected")
    return value


def _exact_policy(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_POLICY_BYTES, "E264 policy"), "E264 policy")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_cross_record_consistency_policy(value)["valid"] is not True:
        raise ValueError("E264 policy drift detected")
    return value


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence):
        raise ValueError("E264 corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS:
        raise ValueError("E264 corpus exceeds bounded record count")
    return [decode_e263_audit(_bounded(item, MAX_RECORD_BYTES, "E263 corpus record")) for item in corpus]


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("E264 source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS:
        raise ValueError("E264 source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS):
        raise ValueError("E264 source units must be exactly E263 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded E264 source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e263 = trees[E263_MODULE]
    seams = (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract",
    )
    for seam in seams:
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e263.body) != 1:
            edges.append(f"e263_seam_missing:{seam}")
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


def _validate_shared(shared: object, value: Mapping[str, Any], order: object, record_digests: object, aggregate_digests: object) -> bool:
    if not isinstance(shared, Mapping) or set(shared) != CROSS_RECORD_KEYS:
        return False
    envelope = value.get("aggregate_provenance_envelope")
    records = envelope.get("records") if isinstance(envelope, Mapping) else None
    if not isinstance(records, list) or not records or not isinstance(records[0], Mapping):
        return False
    aggregate = records[0].get("aggregate_provenance")
    if not isinstance(aggregate, Mapping):
        return False
    envelope_aggregates = [
        item.get("aggregate_provenance")
        for item in records
        if isinstance(item, Mapping)
    ]
    if len(envelope_aggregates) != value.get("corpus_size") or any(not isinstance(item, Mapping) for item in envelope_aggregates):
        return False
    first_aggregate = envelope_aggregates[0]
    expected = {
        "e263_contract_digest": value.get("e263_contract_digest"),
        "e262_contract_digest": first_aggregate.get("e262_contract_digest"),
        "e260_contract_digest": first_aggregate.get("e260_contract_digest"),
        "e259_contract_digest": first_aggregate.get("e259_contract_digest"),
        "e258_contract_digest": first_aggregate.get("e258_contract_digest"),
        "e257_contract_digest": first_aggregate.get("e257_contract_digest"),
        "e256_contract_digest": first_aggregate.get("e256_contract_digest"),
        "receipt_shape_digest": first_aggregate.get("receipt_shape_digest"),
        "contract_evolution_policy_digest": first_aggregate.get("contract_evolution_policy_digest"),
        "source_orders": [item.get("source_order") for item in envelope_aggregates],
        "source_order_digests": [item.get("source_order_digest") for item in envelope_aggregates],
        "source_unit_digests": [item.get("source_unit_digest") for item in envelope_aggregates],
        "source_topology_values": [True] * value.get("corpus_size", 0),
        "fixed_false_authority_flags": copy.deepcopy(FIXED_FALSE_AUTHORITY_FLAGS),
        "corpus_record_digests": record_digests,
        "aggregate_provenance_digests": aggregate_digests,
    }
    return dict(shared) == expected


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


