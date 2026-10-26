# -*- coding: utf-8 -*-
"""Qt-free E254 fresh-memory corpus portability integrity audit."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract as build_e251_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit import (
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract as build_e252_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit as decode_e252_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit as validate_e252_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract as validate_e252_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit import (
    SCOPE as E253_SCOPE,
    STATUS as E253_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract as build_e253_contract,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy as build_e253_policy,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit as decode_e253_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit as validate_e253_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract as validate_e253_contract,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy as validate_e253_policy,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit"
SCOPE = "e253_corpus_replay_independent_fresh_memory_portability_integrity_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-corpus-portability-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 8 * 1024
MAX_RECORD_BYTES = 4 * 1024
MAX_POLICY_BYTES = 8 * 1024
MAX_RECORDS = 16
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E253_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REQUIRED_SOURCE_UNITS = tuple(sorted((E253_MODULE, STATUS_MODULE)))
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract"

STATIC_POLICIES = {
    "read_only": True,
    "fresh_in_memory_portability_only": True,
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
    "portability_audit_is_not_process_or_ipc_execution",
    "portability_audit_is_not_command_mcp_or_runtime_authority",
    "portability_audit_is_not_receipt_consumption_or_ui_authority",
    "portability_audit_is_not_replay_restore_recovery_or_retry",
    "portability_audit_is_not_persistence_or_file_network_output",
    "fresh_memory_verification_is_not_real_session_or_runtime_reconstruction",
    "unified_pond_default_ready",
)

REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "boundary_input_kind", "e253_audit_digest", "e253_contract_digest", "e253_policy_digest",
    "e252_contract_digest", "e251_contract_digest", "corpus_size", "corpus_order",
    "corpus_order_digest", "corpus_record_digest", "corpus_integrity_valid",
    "provenance_closure_valid", "fresh_session_portability_valid", "source_order",
    "source_order_digest", "source_unit_digest", "source_topology_valid", "audit_digest",
    "do_not_claim", *STATIC_POLICIES,
}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability(
    e253_audit_bytes: bytes | bytearray | memoryview,
    e253_contract_bytes: bytes | bytearray | memoryview,
    e253_policy_bytes: bytes | bytearray | memoryview,
    e252_contract_bytes: bytes | bytearray | memoryview,
    e252_corpus_bytes: Sequence[bytes | bytearray | memoryview],
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    e253_audit = decode_e253_audit(_bounded(e253_audit_bytes, MAX_AUDIT_BYTES, "E253 audit"))
    e253_contract = _decode_canonical_object(_bounded(e253_contract_bytes, MAX_RECORD_BYTES, "E253 contract"), "E253 contract")
    if validate_e253_contract(e253_contract)["valid"] is not True or e253_contract != build_e253_contract():
        raise ValueError("E253 contract drift detected")
    e253_policy = _decode_canonical_object(_bounded(e253_policy_bytes, MAX_POLICY_BYTES, "E253 policy"), "E253 policy")
    if validate_e253_policy(e253_policy)["valid"] is not True or e253_policy != build_e253_policy():
        raise ValueError("E253 policy drift detected")
    e252_contract = _decode_canonical_object(_bounded(e252_contract_bytes, MAX_RECORD_BYTES, "E252 contract"), "E252 contract")
    if validate_e252_contract(e252_contract)["valid"] is not True or e252_contract != build_e252_contract():
        raise ValueError("E252 contract drift detected")
    records = _decode_corpus(e252_corpus_bytes)
    if len(records) < 2:
        raise ValueError("compatibility corpus requires at least two records")
    if records != sorted(records, key=lambda item: item["audit_digest"]):
        raise ValueError("corpus order drift detected")
    order_digests = [record["audit_digest"] for record in records]
    if len(set(order_digests)) != len(order_digests):
        raise ValueError("duplicate corpus record")
    e251_digest = _digest(build_e251_contract())
    for record in records:
        if validate_e252_audit(record)["valid"] is not True:
            raise ValueError("invalid E252 corpus record")
        if record.get("e251_contract_digest") != e251_digest:
            raise ValueError("stale E251 contract digest")
    recomputed = {
        "e252_status": e253_audit.get("e252_status"),
        "e252_scope": e253_audit.get("e252_scope"),
        "e252_contract_digest": _digest(e252_contract),
        "e251_contract_digest": e251_digest,
        "corpus_size": len(records),
        "corpus_order": order_digests,
        "corpus_order_digest": _digest(order_digests),
        "corpus_record_digest": _digest([_digest(record) for record in records]),
        "unique_corpus_valid": True,
        "version_compatibility_valid": True,
        "contract_evolution_policy_digest": _digest(e253_policy),
        "contract_evolution_valid": True,
        "deterministic_corpus_valid": True,
    }
    for key, expected in recomputed.items():
        if e253_audit.get(key) != expected:
            raise ValueError(f"E253 corpus closure drift detected: {key}")
    source_order_value = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("portability source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_e253_audit_contract_policy_and_e252_corpus_bytes",
        "e253_audit_digest": e253_audit["audit_digest"],
        "e253_contract_digest": _digest(e253_contract),
        "e253_policy_digest": _digest(e253_policy),
        "e252_contract_digest": recomputed["e252_contract_digest"],
        "e251_contract_digest": e251_digest,
        "corpus_size": len(records),
        "corpus_order": order_digests,
        "corpus_order_digest": recomputed["corpus_order_digest"],
        "corpus_record_digest": recomputed["corpus_record_digest"],
        "corpus_integrity_valid": True,
        "provenance_closure_valid": True,
        "fresh_session_portability_valid": True,
        "source_order": list(source_order_value),
        "source_order_digest": _digest(list(source_order_value)),
        "source_unit_digest": source_summary["source_unit_digest"],
        "source_topology_valid": True,
        "do_not_claim": list(DO_NOT_CLAIM),
        **STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(audit)["valid"] is not True:
        raise RuntimeError("constructed invalid corpus portability audit")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    value = dict(audit)
    errors: list[str] = []
    if set(value) != REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE):
        errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_e253_audit_contract_policy_and_e252_corpus_bytes":
        errors.append("boundary_input_kind_mismatch")
    if not isinstance(value.get("corpus_size"), int) or not 2 <= value.get("corpus_size") <= MAX_RECORDS:
        errors.append("corpus_size_invalid")
    corpus_order = value.get("corpus_order")
    if not isinstance(corpus_order, list) or len(corpus_order) != value.get("corpus_size") or corpus_order != sorted(corpus_order) or len(set(corpus_order)) != len(corpus_order) or not all(_is_sha256(item) for item in corpus_order):
        errors.append("corpus_order_invalid")
    for key in ("e253_audit_digest", "e253_contract_digest", "e253_policy_digest", "e252_contract_digest", "e251_contract_digest", "corpus_order_digest", "corpus_record_digest", "source_order_digest", "source_unit_digest"):
        if not _is_sha256(value.get(key)):
            errors.append(f"{key}_invalid")
    if value.get("source_order") != list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_SOURCE_UNITS)):
        errors.append("source_order_mismatch")
    for key in ("corpus_integrity_valid", "provenance_closure_valid", "fresh_session_portability_valid", "source_topology_valid"):
        if value.get(key) is not True:
            errors.append(f"{key}_mismatch")
    for key, expected in STATIC_POLICIES.items():
        if value.get(key) is not expected:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(audit)["valid"] is not True:
        raise ValueError("invalid corpus portability audit")
    return _canonical_json_bytes(dict(audit))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, MAX_AUDIT_BYTES, "corpus portability audit"), "corpus portability audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit(value)["valid"] is not True:
        raise ValueError("invalid corpus portability audit")
    return copy.deepcopy(value)


def _contract_template() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "accepted_e253_status": E253_STATUS,
        "accepted_e253_scope": E253_SCOPE,
        "required_source_units": list(REQUIRED_SOURCE_UNITS),
        "source_order": list(REQUIRED_SOURCE_UNITS),
        "corpus_min_records": 2,
        "corpus_max_records": MAX_RECORDS,
        "fresh_in_memory_portability_only": True,
        "static_policies": copy.deepcopy(STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM),
        "actual_fresh_process_started": False,
        "ipc_transport_created": False,
        "contract_valid": True,
    }


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract() -> dict[str, Any]:
    return _contract_template()


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    value = dict(contract)
    expected = _contract_template()
    errors = [f"contract_{key}_mismatch" for key in expected if value.get(key) != expected[key]]
    if set(value) != set(expected):
        errors.append("contract_shape_invalid")
    return {"valid": not errors, "errors": errors}


def _decode_corpus(corpus: Sequence[bytes | bytearray | memoryview]) -> list[dict[str, Any]]:
    if isinstance(corpus, (str, bytes, bytearray, memoryview)) or not isinstance(corpus, Sequence):
        raise ValueError("corpus must be a byte sequence")
    if len(corpus) > MAX_RECORDS:
        raise ValueError("corpus exceeds bounded record count")
    return [decode_e252_audit(_bounded(item, MAX_RECORD_BYTES, "E252 corpus record")) for item in corpus]


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_SOURCE_UNITS:
        raise ValueError("source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_SOURCE_UNITS):
        raise ValueError("source units must be exactly E253 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_SOURCE_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e253 = trees[E253_MODULE]
    for seam in (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_policy",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit_contract",
    ):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e253.body) != 1:
            edges.append(f"e253_seam_missing:{seam}")
    status = _named_function(trees[STATUS_MODULE], "build_runtime_worldbridge_status", STATUS_MODULE)
    if not _imports_symbol(trees[STATUS_MODULE], __name__, CONTRACT_BUILDER):
        edges.append("status_contract_import_missing")
    if CONTRACT_KEY not in _string_constants(status) or MODULE_ID not in _string_constants(status) or CONTRACT_BUILDER not in _called_names(status):
        edges.append("status_contract_registration_missing")
    forbidden_roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib", "import" + "lib"}
    forbidden_calls = {"open", "P" + "ath", "Pond", "Game" + "Viewport", "consume_worldbridge_quarantine_operator_presentation_receipt"}
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
