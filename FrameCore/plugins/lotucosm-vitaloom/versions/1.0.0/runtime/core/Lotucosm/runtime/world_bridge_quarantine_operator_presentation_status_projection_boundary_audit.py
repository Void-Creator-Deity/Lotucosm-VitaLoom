# -*- coding: utf-8 -*-
"""Qt-free E251 audit for canonical status-projection boundary evidence."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit import (
    SCOPE as E250_SCOPE,
    STATUS as E250_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_audit"
SCOPE = "e250_canonical_status_projection_contract_drift_and_conceptual_cross_process_read_only_boundary"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-audit+json"
ENCODING = "utf-8"
MAX_BYTES = 4 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E250_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract"
_STATIC = {"read_only": True, "canonical_byte_boundary_only": True, "actual_process_started": False, "ipc_transport_created": False, "raw_receipt_input_admitted": False, "receipt_consumer_operation_admitted": False, "runtime_action_authority": False, "ui_authority": False, "file_written": False, "network_transmitted": False, "persistence_admitted": False, "replay_admitted": False, "restore_admitted": False, "recovery_admitted": False, "same_runtime_retry_admitted": False, "quarantine_clear_admitted": False, "mutation_executed": False, "default_ready": False}
DO_NOT_CLAIM = ("boundary_audit_is_not_actual_process_or_ipc_execution", "boundary_audit_is_not_command_mcp_or_runtime_authority", "boundary_audit_is_not_receipt_consumption_or_ui_authority", "boundary_audit_is_not_replay_restore_recovery_or_retry", "boundary_audit_is_not_persistence_or_file_network_output", "unified_pond_default_ready")
_REQUIRED = {"schema_version", "status", "scope", "media_type", "encoding", "canonical_json", "boundary_input_kind", "e250_status", "e250_scope", "e250_audit_digest", "e250_contract_digest", "contract_drift_free", "cross_process_read_only_boundary_valid", "source_topology_valid", "source_unit_digest", "audit_digest", "do_not_claim", *_STATIC}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary(e250_audit_bytes: bytes | bytearray | memoryview, e250_contract_bytes: bytes | bytearray | memoryview, source_units: Mapping[str, str]) -> dict[str, Any]:
    """Validate supplied canonical E250 bytes without starting a process or transport."""
    e250_audit = decode_worldbridge_quarantine_operator_presentation_status_projection_audit(_bounded(e250_audit_bytes, "e250 audit"))
    if validate_worldbridge_quarantine_operator_presentation_status_projection_audit(e250_audit)["valid"] is not True:
        raise ValueError("invalid E250 audit")
    contract = _decode_object(_bounded(e250_contract_bytes, "e250 contract"), "E250 contract")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(contract)["valid"] is not True:
        raise ValueError("invalid E250 contract")
    if contract != build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract():
        raise ValueError("E250 contract drift detected")
    summary = _audit_sources(source_units)
    if summary["source_topology_valid"] is not True:
        raise ValueError("boundary source topology invalid: " + ",".join(summary["forbidden_edges"]))
    value: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "media_type": MEDIA_TYPE, "encoding": ENCODING, "canonical_json": True, "boundary_input_kind": "caller_supplied_canonical_json_bytes", "e250_status": E250_STATUS, "e250_scope": E250_SCOPE, "e250_audit_digest": e250_audit["audit_digest"], "e250_contract_digest": _digest(contract), "contract_drift_free": True, "cross_process_read_only_boundary_valid": True, "source_topology_valid": True, "source_unit_digest": summary["source_unit_digest"], "do_not_claim": list(DO_NOT_CLAIM), **_STATIC}
    value["audit_digest"] = _audit_digest(value)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(value)["valid"] is not True:
        raise RuntimeError("constructed invalid boundary audit")
    return copy.deepcopy(value)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping): return {"valid": False, "errors": ["audit_not_mapping"]}
    try: value = copy.deepcopy(dict(audit))
    except (TypeError, ValueError): return {"valid": False, "errors": ["audit_not_copyable"]}
    errors: list[str] = []
    if set(value) != _REQUIRED: errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE): errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_json_bytes" or value.get("e250_status") != E250_STATUS or value.get("e250_scope") != E250_SCOPE: errors.append("boundary_identity_mismatch")
    if not _sha(value.get("e250_audit_digest")) or not _sha(value.get("e250_contract_digest")) or not _sha(value.get("source_unit_digest")): errors.append("digest_invalid")
    if value.get("contract_drift_free") is not True or value.get("cross_process_read_only_boundary_valid") is not True or value.get("source_topology_valid") is not True: errors.append("boundary_validity_mismatch")
    for key, expected in _STATIC.items():
        if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
    if not _json_value(value): errors.append("audit_json_value_invalid")
    if value.get("audit_digest") != _audit_digest(value): errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(audit)["valid"] is not True: raise ValueError("invalid boundary audit")
    return _canonical(copy.deepcopy(dict(audit)))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_object(_bounded(data, "boundary audit"), "boundary audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(value)["valid"] is not True: raise ValueError("invalid boundary audit")
    return copy.deepcopy(value)


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract() -> dict[str, Any]:
    value: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE, "e250_status": E250_STATUS, "e250_scope": E250_SCOPE, "required_source_units": sorted((E250_MODULE, STATUS_MODULE)), "boundary_input_kind": "caller_supplied_canonical_json_bytes", "static_policies": copy.deepcopy(_STATIC), "do_not_claim": list(DO_NOT_CLAIM), "actual_process_started": False, "ipc_transport_created": False, "contract_valid": True}
    value["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(value)["valid"]
    return value


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping): return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if (contract.get("schema_version"), contract.get("status"), contract.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE): errors.append("contract_identity_mismatch")
    if contract.get("e250_status") != E250_STATUS or contract.get("e250_scope") != E250_SCOPE or contract.get("required_source_units") != sorted((E250_MODULE, STATUS_MODULE)): errors.append("contract_e250_mismatch")
    if contract.get("boundary_input_kind") != "caller_supplied_canonical_json_bytes" or contract.get("static_policies") != _STATIC or contract.get("do_not_claim") != list(DO_NOT_CLAIM): errors.append("contract_policy_mismatch")
    if contract.get("actual_process_started") is not False or contract.get("ipc_transport_created") is not False or contract.get("contract_valid") is not True: errors.append("contract_validity_mismatch")
    return {"valid": not errors, "errors": errors}


def _audit_sources(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != {E250_MODULE, STATUS_MODULE}: raise ValueError("source units must be exactly E250 and status")
    units: dict[str, str] = {}
    for name in (E250_MODULE, STATUS_MODULE):
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES: raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e250 = trees[E250_MODULE]
    for name in ("decode_worldbridge_quarantine_operator_presentation_status_projection_audit", "build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract", "validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract"):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name for node in e250.body) != 1: edges.append(f"e250_seam_missing:{name}")
    status = _function(trees[STATUS_MODULE], "build_runtime_worldbridge_status", STATUS_MODULE)
    if not any(isinstance(node, ast.ImportFrom) and node.module == __name__ and any(alias.name == CONTRACT_BUILDER for alias in node.names) for node in ast.walk(trees[STATUS_MODULE])): edges.append("status_contract_import_missing")
    strings = {node.value for node in ast.walk(status) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    calls = {_name(node.func) for node in ast.walk(status) if isinstance(node, ast.Call) and _name(node.func)}
    if CONTRACT_KEY not in strings or MODULE_ID not in strings or CONTRACT_BUILDER not in calls: edges.append("status_contract_registration_missing")
    forbidden_roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib"}
    forbidden_calls = {"open", "P" + "ath", "Pond", "Game" + "Viewport", "consume_worldbridge_quarantine_operator_presentation_receipt"}
    for module, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(name.split(".")[0] in forbidden_roots for name in names): edges.append(f"{module}:forbidden_import")
            elif isinstance(node, ast.Call):
                called = _name(node.func)
                if called and called.rsplit(".", 1)[-1] in forbidden_calls: edges.append(f"{module}:forbidden_call")
    return {"source_unit_digest": _digest({name: units[name] for name in sorted(units)}), "source_topology_valid": not edges, "forbidden_edges": sorted(set(edges))}


def _function(tree: ast.Module, name: str, module: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    found = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(found) != 1: raise ValueError(f"{module} must define exactly one {name}")
    return found[0]


def _bounded(data: bytes | bytearray | memoryview, label: str) -> bytes:
    if not isinstance(data, (bytes, bytearray, memoryview)): raise TypeError(f"{label} must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_BYTES: raise ValueError(f"{label} exceeds bounded size")
    return raw


def _decode_object(raw: bytes, label: str) -> dict[str, Any]:
    try: value = json.loads(raw.decode(ENCODING), object_pairs_hook=_dupes, parse_constant=_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc: raise ValueError(f"invalid canonical {label}") from exc
    if not isinstance(value, dict) or _canonical(value) != raw: raise ValueError(f"{label} is non-canonical")
    return value


def _canonical(value: object) -> bytes: return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)
def _digest(value: object) -> str: return hashlib.sha256(_canonical(value)).hexdigest()
def _audit_digest(value: Mapping[str, Any]) -> str:
    copied = dict(value); copied.pop("audit_digest", None); return _digest(copied)
def _sha(value: object) -> bool: return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
def _json_value(value: object) -> bool:
    return value is None or isinstance(value, (str, bool, int)) or (isinstance(value, list) and all(_json_value(item) for item in value)) or (isinstance(value, Mapping) and all(isinstance(key, str) and _json_value(item) for key, item in value.items()))
def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        base = _name(node.value); return f"{base}.{node.attr}" if base else node.attr
    return None
def _dupes(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out: raise ValueError("duplicate JSON object key")
        out[key] = value
    return out
def _constant(value: str) -> None: raise ValueError(f"non-finite JSON constant: {value}")
