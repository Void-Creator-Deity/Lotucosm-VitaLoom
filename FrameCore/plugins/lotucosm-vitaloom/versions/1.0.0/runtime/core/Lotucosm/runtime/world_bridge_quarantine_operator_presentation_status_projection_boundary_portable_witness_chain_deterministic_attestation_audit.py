# -*- coding: utf-8 -*-
"""Qt-free E256 portable witness chain deterministic attestation audit."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit import (
    SCOPE as E255_SCOPE,
    STATUS as E255_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract as build_e255_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit as decode_e255_audit,
    encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit as encode_e255_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract as validate_e255_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit"
SCOPE = "e255_portable_witness_chain_deterministic_attestation_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-portable-witness-chain-deterministic-attestation-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 8 * 1024
MAX_CONTRACT_BYTES = 8 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E255_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E255_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract"

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
    "attestation_is_not_process_or_ipc_execution",
    "attestation_is_not_command_mcp_or_runtime_authority",
    "attestation_is_not_receipt_consumption_or_ui_authority",
    "attestation_is_not_replay_restore_recovery_or_retry",
    "attestation_is_not_persistence_or_file_network_output",
    "attestation_is_not_runtime_reconstruction_or_admission",
    "unified_pond_default_ready",
)
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json", "boundary_input_kind",
    "e255_audit_digest", "e255_canonical_bytes_digest", "e255_contract_digest", "portable_corpus_witness_digest",
    "e254_audit_digest", "e253_audit_digest", "e253_policy_digest", "component_digests",
    "portable_witness_chain_attestation_digest", "deterministic_attestation_valid", "portable_witness_chain_attestation_valid",
    "source_order", "source_order_digest", "source_unit_digest", "source_topology_valid", "audit_digest", "do_not_claim",
    *STATIC_POLICIES,
}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation(
    e255_audit_bytes: bytes | bytearray | memoryview,
    e255_contract_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    raw_audit = _bounded(e255_audit_bytes, MAX_AUDIT_BYTES, "E255 audit")
    e255 = decode_e255_audit(raw_audit)
    if encode_e255_audit(e255) != raw_audit:
        raise ValueError("E255 audit canonical encoding drift detected")
    e255_contract = _exact_contract(e255_contract_bytes)
    if (e255.get("status"), e255.get("scope")) != (E255_STATUS, E255_SCOPE):
        raise ValueError("E255 identity drift detected")
    _require_e255_component_linkage(e255)
    order = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("attestation source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    components = dict(sorted({
        "e253_audit": e255["e253_audit_digest"],
        "e253_policy": e255["e253_policy_digest"],
        "e254_audit": e255["e254_audit_digest"],
        "e255_audit": e255["audit_digest"],
        "e255_canonical_bytes": _bytes_digest(raw_audit),
        "e255_contract": _digest(e255_contract),
        "portable_corpus_witness": e255["portable_corpus_witness_digest"],
        "source_units": source_summary["source_unit_digest"],
    }.items()))
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "media_type": MEDIA_TYPE,
        "encoding": ENCODING, "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e255_witness_contract_source_bytes",
        "e255_audit_digest": e255["audit_digest"], "e255_canonical_bytes_digest": _bytes_digest(raw_audit),
        "e255_contract_digest": _digest(e255_contract), "portable_corpus_witness_digest": e255["portable_corpus_witness_digest"],
        "e254_audit_digest": e255["e254_audit_digest"], "e253_audit_digest": e255["e253_audit_digest"],
        "e253_policy_digest": e255["e253_policy_digest"], "component_digests": components,
        "portable_witness_chain_attestation_digest": _digest(components), "deterministic_attestation_valid": True,
        "portable_witness_chain_attestation_valid": True, "source_order": list(order),
        "source_order_digest": _digest(list(order)), "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True, "do_not_claim": list(DO_NOT_CLAIM), **STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(audit)["valid"] is not True:
        raise RuntimeError("constructed invalid deterministic attestation")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value = dict(audit)
    errors: list[str] = []
    if set(value) != REQUIRED_AUDIT_KEYS: errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE): errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e255_witness_contract_source_bytes": errors.append("boundary_input_kind_mismatch")
    for key in ("e255_audit_digest", "e255_canonical_bytes_digest", "e255_contract_digest", "portable_corpus_witness_digest", "e254_audit_digest", "e253_audit_digest", "e253_policy_digest", "portable_witness_chain_attestation_digest", "source_order_digest", "source_unit_digest"):
        if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
    components = value.get("component_digests")
    expected_components = {"e253_audit", "e253_policy", "e254_audit", "e255_audit", "e255_canonical_bytes", "e255_contract", "portable_corpus_witness", "source_units"}
    if not isinstance(components, dict) or tuple(components) != tuple(sorted(components)) or set(components) != expected_components or not all(_is_sha256(item) for item in components.values()) or value.get("portable_witness_chain_attestation_digest") != _digest(components): errors.append("component_digests_invalid")
    elif components != {
        "e253_audit": value.get("e253_audit_digest"), "e253_policy": value.get("e253_policy_digest"),
        "e254_audit": value.get("e254_audit_digest"), "e255_audit": value.get("e255_audit_digest"),
        "e255_canonical_bytes": value.get("e255_canonical_bytes_digest"), "e255_contract": value.get("e255_contract_digest"),
        "portable_corpus_witness": value.get("portable_corpus_witness_digest"), "source_units": value.get("source_unit_digest"),
    }: errors.append("component_linkage_invalid")
    if value.get("source_order") != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)): errors.append("source_order_mismatch")
    for key in ("deterministic_attestation_valid", "portable_witness_chain_attestation_valid", "source_topology_valid"):
        if value.get(key) is not True: errors.append(f"{key}_mismatch")
    for key, expected in STATIC_POLICIES.items():
        if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value): errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(audit)["valid"] is not True: raise ValueError("invalid deterministic attestation")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "deterministic attestation"), "deterministic attestation")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit(value)["valid"] is not True: raise ValueError("invalid deterministic attestation")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "accepted_e255_status": E255_STATUS, "accepted_e255_scope": E255_SCOPE, "required_source_units": list(REQUIRED_SOURCE_UNITS), "source_order": list(REQUIRED_SOURCE_UNITS), "explicit_input_dependency_closure_only": True, "static_policies": copy.deepcopy(STATIC_POLICIES), "do_not_claim": list(DO_NOT_CLAIM), "actual_fresh_process_started": False, "ipc_transport_created": False, "contract_valid": True}


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping): return {"valid": False, "errors": ["contract_not_mapping"]}
    value, expected = dict(contract), _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected): errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _require_e255_component_linkage(e255: Mapping[str, Any]) -> None:
    components = e255.get("component_digests")
    expected = {
        "e252_contract": e255.get("e252_contract_digest"), "e252_corpus": e255.get("corpus_record_digest"),
        "e253_audit": e255.get("e253_audit_digest"), "e253_contract": e255.get("e253_contract_digest"),
        "e253_policy": e255.get("e253_policy_digest"), "e254_audit": e255.get("e254_audit_digest"),
        "e254_contract": e255.get("e254_contract_digest"), "source_units": e255.get("source_unit_digest"),
    }
    if components != expected or e255.get("portable_corpus_witness_digest") != _digest(expected):
        raise ValueError("E255 component linkage drift detected")


def _exact_contract(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(raw, MAX_CONTRACT_BYTES, "E255 contract"), "E255 contract")
    if validate_e255_contract(value)["valid"] is not True or value != build_e255_contract(): raise ValueError("E255 contract drift detected")
    return value


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order): raise ValueError("source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS: raise ValueError("source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS): raise ValueError("source units must be exactly E255 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES: raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e255 = trees[E255_MODULE]
    for seam in (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit",
        "encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit_contract",
    ):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e255.body) != 1: edges.append(f"e255_seam_missing:{seam}")
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
def _bytes_digest(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
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
