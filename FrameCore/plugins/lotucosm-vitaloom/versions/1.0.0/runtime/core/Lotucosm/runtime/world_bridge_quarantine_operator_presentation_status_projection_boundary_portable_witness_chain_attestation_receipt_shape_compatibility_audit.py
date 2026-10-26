# -*- coding: utf-8 -*-
"""Qt-free E257 portable witness attestation receipt-shape compatibility audit."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import (
    DO_NOT_CLAIM as E256_DO_NOT_CLAIM,
    SCOPE as E256_SCOPE,
    STATIC_POLICIES as E256_STATIC_POLICIES,
    STATUS as E256_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract as build_e256_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit as decode_e256_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit as encode_e256_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract as validate_e256_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit"
SCOPE = "e256_attestation_receipt_shape_compatibility_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-portable-witness-chain-attestation-receipt-shape-compatibility-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 12 * 1024
MAX_RECORD_BYTES = 8 * 1024
MAX_CONTRACT_BYTES = 8 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E256_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E256_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract"
E256_COMPONENT_KEYS = (
    "e253_audit", "e253_policy", "e254_audit", "e255_audit", "e255_canonical_bytes", "e255_contract",
    "portable_corpus_witness", "source_units",
)

STATIC_POLICIES = {
    "read_only": True,
    "explicit_input_dependency_closure_only": True,
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
    "receipt_shape_audit_is_not_process_or_ipc_execution",
    "receipt_shape_audit_is_not_command_mcp_or_runtime_authority",
    "receipt_shape_audit_is_not_receipt_consumption_or_ui_authority",
    "receipt_shape_audit_is_not_replay_restore_recovery_or_retry",
    "receipt_shape_audit_is_not_persistence_or_file_network_output",
    "receipt_shape_audit_is_not_runtime_reconstruction_or_admission",
    "unified_pond_default_ready",
)
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json", "boundary_input_kind",
    "e256_contract_digest", "corpus_size", "corpus_order", "corpus_order_digest", "corpus_record_digest",
    "attestation_source_unit_digests", "attestation_source_provenance_digest", "component_key_order", "receipt_shape",
    "receipt_shape_digest", "receipt_shape_compatibility_valid", "deterministic_corpus_valid", "source_order",
    "source_order_digest", "source_unit_digest", "source_topology_valid", "audit_digest", "do_not_claim", *STATIC_POLICIES,
}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility(
    e256_corpus_bytes: Sequence[bytes | bytearray | memoryview],
    e256_contract_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    contract = _exact_contract(e256_contract_bytes)
    records = _decode_corpus(e256_corpus_bytes)
    if len(records) < 2:
        raise ValueError("attestation corpus requires at least two records")
    if records != sorted(records, key=lambda item: item["audit_digest"]):
        raise ValueError("attestation corpus order drift detected")
    order_digests = [record["audit_digest"] for record in records]
    if len(set(order_digests)) != len(order_digests):
        raise ValueError("duplicate attestation corpus record")
    shape = _receipt_shape(records[0])
    for record in records:
        if encode_e256_audit(record) != _canonical_json_bytes(record):
            raise ValueError("E256 audit canonical encoding drift detected")
        if (record.get("status"), record.get("scope")) != (E256_STATUS, E256_SCOPE):
            raise ValueError("E256 identity drift detected")
        if _receipt_shape(record) != shape:
            raise ValueError("attestation receipt shape drift detected")
    order = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("receipt shape source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    source_digests = [record["source_unit_digest"] for record in records]
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "media_type": MEDIA_TYPE,
        "encoding": ENCODING, "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e256_attestation_corpus_bytes",
        "e256_contract_digest": _digest(contract), "corpus_size": len(records), "corpus_order": order_digests,
        "corpus_order_digest": _digest(order_digests), "corpus_record_digest": _digest([_digest(record) for record in records]),
        "attestation_source_unit_digests": source_digests, "attestation_source_provenance_digest": _digest(source_digests),
        "component_key_order": list(E256_COMPONENT_KEYS), "receipt_shape": shape, "receipt_shape_digest": _digest(shape),
        "receipt_shape_compatibility_valid": True, "deterministic_corpus_valid": True, "source_order": list(order),
        "source_order_digest": _digest(list(order)), "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True, "do_not_claim": list(DO_NOT_CLAIM), **STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(audit)["valid"] is not True:
        raise RuntimeError("constructed invalid receipt shape compatibility audit")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value = dict(audit)
    errors: list[str] = []
    if set(value) != REQUIRED_AUDIT_KEYS: errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE): errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e256_attestation_corpus_bytes": errors.append("boundary_input_kind_mismatch")
    if not isinstance(value.get("corpus_size"), int) or not 2 <= value.get("corpus_size") <= MAX_RECORDS: errors.append("corpus_size_invalid")
    corpus_order = value.get("corpus_order")
    if not isinstance(corpus_order, list) or len(corpus_order) != value.get("corpus_size") or corpus_order != sorted(corpus_order) or len(set(corpus_order)) != len(corpus_order) or not all(_is_sha256(item) for item in corpus_order): errors.append("corpus_order_invalid")
    source_digests = value.get("attestation_source_unit_digests")
    if not isinstance(source_digests, list) or len(source_digests) != value.get("corpus_size") or not all(_is_sha256(item) for item in source_digests) or value.get("attestation_source_provenance_digest") != _digest(source_digests): errors.append("attestation_source_provenance_invalid")
    for key in ("e256_contract_digest", "corpus_order_digest", "corpus_record_digest", "receipt_shape_digest", "source_order_digest", "source_unit_digest"):
        if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
    if value.get("corpus_order_digest") != _digest(corpus_order): errors.append("corpus_order_digest_mismatch")
    if value.get("component_key_order") != list(E256_COMPONENT_KEYS): errors.append("component_key_order_invalid")
    shape = value.get("receipt_shape")
    if shape != _expected_receipt_shape() or value.get("receipt_shape_digest") != _digest(shape): errors.append("receipt_shape_invalid")
    for key in ("receipt_shape_compatibility_valid", "deterministic_corpus_valid", "source_topology_valid"):
        if value.get(key) is not True: errors.append(f"{key}_mismatch")
    if value.get("source_order") != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)): errors.append("source_order_mismatch")
    for key, expected in STATIC_POLICIES.items():
        if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value): errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(audit)["valid"] is not True: raise ValueError("invalid receipt shape compatibility audit")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "receipt shape compatibility audit"), "receipt shape compatibility audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit(value)["valid"] is not True: raise ValueError("invalid receipt shape compatibility audit")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "accepted_e256_status": E256_STATUS, "accepted_e256_scope": E256_SCOPE, "required_source_units": list(REQUIRED_SOURCE_UNITS), "source_order": list(REQUIRED_SOURCE_UNITS), "corpus_min_records": 2, "corpus_max_records": MAX_RECORDS, "component_key_order": list(E256_COMPONENT_KEYS), "explicit_input_dependency_closure_only": True, "static_policies": copy.deepcopy(STATIC_POLICIES), "do_not_claim": list(DO_NOT_CLAIM), "actual_fresh_process_started": False, "ipc_transport_created": False, "contract_valid": True}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping): return {"valid": False, "errors": ["contract_not_mapping"]}
    value, expected = dict(contract), _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected): errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _exact_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E256 contract"), "E256 contract")
    if validate_e256_contract(value)["valid"] is not True or value != build_e256_contract(): raise ValueError("E256 contract drift detected")
    return value


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence): raise ValueError("attestation corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS: raise ValueError("attestation corpus exceeds bounded record count")
    return [decode_e256_audit(_bounded(item, MAX_RECORD_BYTES, "E256 corpus record")) for item in corpus]


def _receipt_shape(record: Mapping[str, Any]) -> dict[str, Any]:
    expected = _expected_receipt_shape()
    if {key: record.get(key) for key in expected["identity_keys"]} != expected["identity"]:
        raise ValueError("E256 identity receipt shape drift detected")
    if tuple(record.get("component_digests", {})) != E256_COMPONENT_KEYS:
        raise ValueError("E256 component key receipt shape drift detected")
    if record.get("source_order") != list(REQUIRED_E256_SOURCE_ORDER) or record.get("do_not_claim") != list(E256_DO_NOT_CLAIM):
        raise ValueError("E256 source or claim receipt shape drift detected")
    if {key: record.get(key) for key in E256_STATIC_POLICIES} != E256_STATIC_POLICIES:
        raise ValueError("E256 policy receipt shape drift detected")
    if record.get("deterministic_attestation_valid") is not True or record.get("portable_witness_chain_attestation_valid") is not True or record.get("source_topology_valid") is not True:
        raise ValueError("E256 validity receipt shape drift detected")
    return expected


REQUIRED_E256_SOURCE_ORDER = tuple(sorted(("core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit", STATUS_MODULE)))


def _expected_receipt_shape() -> dict[str, Any]:
    identity = {"schema_version": 1, "status": E256_STATUS, "scope": E256_SCOPE, "media_type": "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-portable-witness-chain-deterministic-attestation-audit+json", "encoding": ENCODING, "canonical_json": True, "boundary_input_kind": "caller_supplied_canonical_e255_witness_contract_source_bytes"}
    return {"identity_keys": list(identity), "identity": identity, "component_key_order": list(E256_COMPONENT_KEYS), "source_order": list(REQUIRED_E256_SOURCE_ORDER), "static_policies": copy.deepcopy(E256_STATIC_POLICIES), "do_not_claim": list(E256_DO_NOT_CLAIM), "deterministic_attestation_valid": True, "portable_witness_chain_attestation_valid": True, "source_topology_valid": True}


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order): raise ValueError("source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS: raise ValueError("source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS): raise ValueError("source units must be exactly E256 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES: raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e256 = trees[E256_MODULE]
    for seam in (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit",
        "encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract",
    ):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e256.body) != 1: edges.append(f"e256_seam_missing:{seam}")
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
    if not isinstance(data, (bytes, bytearray, memoryview)): raise TypeError(f"{label} must be bytes-like")
    raw = bytes(data)
    if len(raw) > limit: raise ValueError(f"{label} exceeds bounded size")
    return raw


def _decode_canonical_object(raw: bytes, label: str) -> dict[str, Any]:
    try: value = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc: raise ValueError(f"invalid canonical {label}") from exc
    if not isinstance(value, dict) or _canonical_json_bytes(value) != raw: raise ValueError(f"{label} is non-canonical")
    return value


def _named_function(tree: ast.Module, name: str, module: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(matches) != 1: raise ValueError(f"{module} must define exactly one {name}")
    return matches[0]


def _imports_symbol(tree: ast.AST, module: str, symbol: str) -> bool:
    return any(isinstance(node, ast.ImportFrom) and node.module == module and any(alias.name == symbol for alias in node.names) for node in ast.walk(tree))


def _called_names(tree: ast.AST) -> set[str]: return {name for node in ast.walk(tree) if isinstance(node, ast.Call) if (name := _qualified_name(node.func))}
def _string_constants(tree: ast.AST) -> set[str]: return {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        base = _qualified_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None

def _canonical_json_bytes(value: object) -> bytes: return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)
def _digest(value: object) -> str: return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()
def _audit_digest(value: Mapping[str, Any]) -> str:
    copied = dict(value); copied.pop("audit_digest", None); return _digest(copied)
def _is_sha256(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value: raise ValueError("duplicate JSON object key")
        value[key] = item
    return value
def _reject_constant(value: str) -> None: raise ValueError(f"non-finite JSON constant: {value}")
