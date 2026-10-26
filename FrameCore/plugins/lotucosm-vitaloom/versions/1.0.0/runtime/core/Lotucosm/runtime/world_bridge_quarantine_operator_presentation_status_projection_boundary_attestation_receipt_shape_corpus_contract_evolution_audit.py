# -*- coding: utf-8 -*-
"""Qt-free E258 receipt-shape corpus exact-current contract-evolution audit."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract as build_e256_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import (
    SCOPE as E257_SCOPE,
    STATUS as E257_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract as build_e257_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit as decode_e257_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit as validate_e257_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract as validate_e257_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit"
SCOPE = "e257_ordered_receipt_shape_corpus_exact_current_contract_evolution_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-corpus-contract-evolution-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 16 * 1024
MAX_RECORD_BYTES = 12 * 1024
MAX_CONTRACT_BYTES = 8 * 1024
MAX_POLICY_BYTES = 8 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E257_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E257_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract"

STATIC_POLICIES = {
    "read_only": True,
    "exact_current_contract_evolution_only": True,
    "actual_fresh_process_started": False,
    "ipc_transport_created": False,
    "dynamic_source_import_admitted": False,
    "raw_receipt_input_admitted": False,
    "receipt_consumer_operation_admitted": False,
    "runtime_action_authority": False,
    "ui_authority": False,
    "file_written": False,
    "network_transmitted": False,
    "persistence_admitted": False,
    "replay_admitted": False,
    "restore_admitted": False,
    "recovery_admitted": False,
    "same_runtime_retry_admitted": False,
    "quarantine_clear_admitted": False,
    "mutation_executed": False,
    "default_ready": False,
}
DO_NOT_CLAIM = (
    "contract_evolution_audit_is_not_migration_or_execution",
    "contract_evolution_audit_is_not_process_or_ipc_execution",
    "contract_evolution_audit_is_not_command_mcp_or_runtime_authority",
    "contract_evolution_audit_is_not_receipt_consumption_or_ui_authority",
    "contract_evolution_audit_is_not_replay_restore_recovery_or_retry",
    "contract_evolution_audit_is_not_persistence_or_file_network_output",
    "contract_evolution_audit_is_not_runtime_reconstruction_or_admission",
    "unified_pond_default_ready",
)
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json", "boundary_input_kind",
    "e257_status", "e257_scope", "e257_contract_digest", "e256_contract_digest", "corpus_size", "corpus_order",
    "corpus_order_digest", "corpus_record_digest", "e257_source_unit_digests", "e257_source_provenance_digest",
    "attestation_source_provenance_digests", "attestation_source_provenance_digest", "receipt_shape_digest",
    "unique_corpus_valid", "version_compatibility_valid", "receipt_shape_closure_valid", "contract_evolution_policy_digest",
    "contract_evolution_valid", "source_order", "source_order_digest", "source_unit_digest", "source_topology_valid",
    "deterministic_corpus_valid", "audit_digest", "do_not_claim", *STATIC_POLICIES,
}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "accepted_e257_schema_version": 1,
        "accepted_e257_status": E257_STATUS,
        "accepted_e257_scope": E257_SCOPE,
        "accepted_e257_contract_digest": _digest(build_e257_contract()),
        "accepted_e256_contract_digest": _digest(build_e256_contract()),
        "contract_evolution_mode": "exact_current_contract_and_receipt_shape_only",
        "migration_admitted": False,
        "mixed_version_admitted": False,
        "unknown_contract_admitted": False,
        "execution_admitted": False,
        "operational_compatibility_authority": False,
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
    }


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy(policy: object) -> dict[str, Any]:
    if not isinstance(policy, Mapping):
        return {"valid": False, "errors": ["policy_not_mapping"]}
    expected = build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy()
    return {"valid": dict(policy) == expected, "errors": [] if dict(policy) == expected else ["policy_drift"]}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution(
    e257_audit_corpus_bytes: Sequence[bytes | bytearray | memoryview],
    e257_contract_bytes: bytes | bytearray | memoryview,
    contract_evolution_policy_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    e257_contract = _exact_e257_contract(e257_contract_bytes)
    policy = _exact_policy(contract_evolution_policy_bytes)
    records = _decode_corpus(e257_audit_corpus_bytes)
    if len(records) < 2:
        raise ValueError("receipt-shape corpus requires at least two records")
    if records != sorted(records, key=lambda record: record["audit_digest"]):
        raise ValueError("receipt-shape corpus order drift detected")
    audit_digests = [record["audit_digest"] for record in records]
    if len(set(audit_digests)) != len(audit_digests):
        raise ValueError("duplicate receipt-shape corpus record")
    expected_e257_digest = _digest(e257_contract)
    expected_e256_digest = _digest(build_e256_contract())
    expected_shape_digest = records[0]["receipt_shape_digest"]
    for record in records:
        if validate_e257_audit(record)["valid"] is not True:
            raise ValueError("invalid E257 corpus record")
        if (record.get("schema_version"), record.get("status"), record.get("scope")) != (1, E257_STATUS, E257_SCOPE):
            raise ValueError("mixed E257 version or identity")
        if record.get("e256_contract_digest") != expected_e256_digest:
            raise ValueError("stale E256 contract digest")
        if record.get("receipt_shape_digest") != _digest(record.get("receipt_shape")) or record.get("receipt_shape_digest") != expected_shape_digest:
            raise ValueError("receipt shape closure drift detected")
    if policy.get("accepted_e257_contract_digest") != expected_e257_digest or policy.get("accepted_e256_contract_digest") != expected_e256_digest:
        raise ValueError("contract evolution policy contract identity drift detected")
    order = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("contract evolution source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    e257_source_unit_digests = [record["source_unit_digest"] for record in records]
    attestation_provenance_digests = [record["attestation_source_provenance_digest"] for record in records]
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e257_receipt_shape_corpus_contract_policy_bytes",
        "e257_status": E257_STATUS,
        "e257_scope": E257_SCOPE,
        "e257_contract_digest": expected_e257_digest,
        "e256_contract_digest": expected_e256_digest,
        "corpus_size": len(records),
        "corpus_order": audit_digests,
        "corpus_order_digest": _digest(audit_digests),
        "corpus_record_digest": _digest([_digest(record) for record in records]),
        "e257_source_unit_digests": e257_source_unit_digests,
        "e257_source_provenance_digest": _digest(e257_source_unit_digests),
        "attestation_source_provenance_digests": attestation_provenance_digests,
        "attestation_source_provenance_digest": _digest(attestation_provenance_digests),
        "receipt_shape_digest": expected_shape_digest,
        "unique_corpus_valid": True,
        "version_compatibility_valid": True,
        "receipt_shape_closure_valid": True,
        "contract_evolution_policy_digest": _digest(policy),
        "contract_evolution_valid": True,
        "source_order": list(order),
        "source_order_digest": _digest(list(order)),
        "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True,
        "deterministic_corpus_valid": True,
        "do_not_claim": list(DO_NOT_CLAIM),
        **STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(audit)["valid"] is not True:
        raise RuntimeError("constructed invalid receipt-shape contract-evolution audit")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value = dict(audit)
    errors: list[str] = []
    if set(value) != REQUIRED_AUDIT_KEYS: errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE): errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e257_receipt_shape_corpus_contract_policy_bytes": errors.append("boundary_input_kind_mismatch")
    if (value.get("e257_status"), value.get("e257_scope")) != (E257_STATUS, E257_SCOPE): errors.append("e257_identity_mismatch")
    if not isinstance(value.get("corpus_size"), int) or not 2 <= value.get("corpus_size") <= MAX_RECORDS: errors.append("corpus_size_invalid")
    corpus_order = value.get("corpus_order")
    if not isinstance(corpus_order, list) or len(corpus_order) != value.get("corpus_size") or corpus_order != sorted(corpus_order) or len(set(corpus_order)) != len(corpus_order) or not all(_is_sha256(item) for item in corpus_order): errors.append("corpus_order_invalid")
    for plural, aggregate in (("e257_source_unit_digests", "e257_source_provenance_digest"), ("attestation_source_provenance_digests", "attestation_source_provenance_digest")):
        items = value.get(plural)
        if not isinstance(items, list) or len(items) != value.get("corpus_size") or not all(_is_sha256(item) for item in items) or value.get(aggregate) != _digest(items): errors.append(f"{plural}_invalid")
    for key in ("e257_contract_digest", "e256_contract_digest", "corpus_order_digest", "corpus_record_digest", "receipt_shape_digest", "contract_evolution_policy_digest", "source_order_digest", "source_unit_digest"):
        if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
    if value.get("corpus_order_digest") != _digest(corpus_order): errors.append("corpus_order_digest_mismatch")
    if value.get("e257_contract_digest") != _digest(build_e257_contract()): errors.append("e257_contract_digest_mismatch")
    if value.get("e256_contract_digest") != _digest(build_e256_contract()): errors.append("e256_contract_digest_mismatch")
    if value.get("contract_evolution_policy_digest") != _digest(build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy()): errors.append("contract_evolution_policy_digest_mismatch")
    for key in ("unique_corpus_valid", "version_compatibility_valid", "receipt_shape_closure_valid", "contract_evolution_valid", "source_topology_valid", "deterministic_corpus_valid"):
        if value.get(key) is not True: errors.append(f"{key}_mismatch")
    if value.get("source_order") != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)): errors.append("source_order_mismatch")
    for key, expected in STATIC_POLICIES.items():
        if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value): errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(audit)["valid"] is not True:
        raise ValueError("invalid receipt-shape contract-evolution audit")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "receipt-shape contract-evolution audit"), "receipt-shape contract-evolution audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit(value)["valid"] is not True:
        raise ValueError("invalid receipt-shape contract-evolution audit")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "accepted_e257_status": E257_STATUS,
        "accepted_e257_scope": E257_SCOPE,
        "accepted_e257_contract_digest": _digest(build_e257_contract()),
        "accepted_e256_contract_digest": _digest(build_e256_contract()),
        "required_source_units": list(REQUIRED_SOURCE_UNITS),
        "source_order": list(REQUIRED_SOURCE_UNITS),
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
        "contract_evolution_mode": "exact_current_contract_and_receipt_shape_only",
        "explicit_input_dependency_closure_only": True,
        "static_policies": copy.deepcopy(STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM),
        "actual_fresh_process_started": False,
        "ipc_transport_created": False,
        "contract_valid": True,
    }


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    value, expected = dict(contract), _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected): errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _exact_e257_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E257 contract"), "E257 contract")
    if validate_e257_contract(value)["valid"] is not True or value != build_e257_contract():
        raise ValueError("E257 contract drift detected")
    return value


def _exact_policy(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_POLICY_BYTES, "contract evolution policy"), "contract evolution policy")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy(value)["valid"] is not True:
        raise ValueError("contract evolution policy drift detected")
    return value


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence):
        raise ValueError("receipt-shape corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS:
        raise ValueError("receipt-shape corpus exceeds bounded record count")
    return [decode_e257_audit(_bounded(item, MAX_RECORD_BYTES, "E257 corpus record")) for item in corpus]


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS:
        raise ValueError("source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS):
        raise ValueError("source units must be exactly E257 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e257 = trees[E257_MODULE]
    for seam in (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract",
    ):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e257.body) != 1:
            edges.append(f"e257_seam_missing:{seam}")
    status = _named_function(trees[STATUS_MODULE], "build_runtime_worldbridge_status", STATUS_MODULE)
    if not _imports_symbol(trees[STATUS_MODULE], __name__, CONTRACT_BUILDER): edges.append("status_contract_import_missing")
    if CONTRACT_KEY not in _string_constants(status) or MODULE_ID not in _string_constants(status) or CONTRACT_BUILDER not in _called_names(status): edges.append("status_contract_registration_missing")
    forbidden_roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib", "import" + "lib"}
    forbidden_calls = {"open", "P" + "ath", "Pond", "Game" + "Viewport", "consume_worldbridge_quarantine_operator_presentation_receipt"}
    for module, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden_roots for alias in node.names): edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden_roots: edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.Call):
                name = _qualified_name(node.func)
                if name and name.rsplit(".", 1)[-1] in forbidden_calls: edges.append(f"{module}:forbidden_call")
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
