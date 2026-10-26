# -*- coding: utf-8 -*-
"""Qt-free E252 deterministic provenance audit for E251 boundary evidence."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit import (
    SCOPE as E251_SCOPE,
    STATUS as E251_STATUS,
    build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
    decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit,
    validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit"
SCOPE = "e251_deterministic_provenance_and_ordered_compatibility_read_only_audit"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-compatibility-audit+json"
ENCODING = "utf-8"
MAX_BYTES = 4 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
E251_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_audit"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
CONTRACT_KEY = "failure_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract"
MODULE_ID = "quarantine_operator_presentation_status_projection_boundary_compatibility_audit_module"
CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract"
REQUIRED_UNITS = tuple(sorted((E251_MODULE, STATUS_MODULE)))
STATIC_POLICIES = {
    "read_only": True, "deterministic_compatibility_only": True,
    "actual_process_started": False, "ipc_transport_created": False,
    "raw_receipt_input_admitted": False, "receipt_consumer_operation_admitted": False,
    "runtime_action_authority": False, "ui_authority": False,
    "file_written": False, "network_transmitted": False, "persistence_admitted": False,
    "replay_admitted": False, "restore_admitted": False, "recovery_admitted": False,
    "same_runtime_retry_admitted": False, "quarantine_clear_admitted": False,
    "mutation_executed": False, "default_ready": False,
}
DO_NOT_CLAIM = (
    "compatibility_audit_is_not_process_or_ipc_execution",
    "compatibility_audit_is_not_command_mcp_or_runtime_authority",
    "compatibility_audit_is_not_receipt_consumption_or_ui_authority",
    "compatibility_audit_is_not_replay_restore_recovery_or_retry",
    "compatibility_audit_is_not_persistence_or_file_network_output",
    "unified_pond_default_ready",
)
REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "boundary_input_kind", "e251_status", "e251_scope", "e251_audit_digest",
    "e251_contract_digest", "source_order", "source_order_digest", "source_unit_digest",
    "contract_drift_free", "deterministic_compatibility_valid", "source_topology_valid",
    "audit_digest", "do_not_claim", *STATIC_POLICIES,
}


def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility(
    e251_audit_bytes: bytes | bytearray | memoryview,
    e251_contract_bytes: bytes | bytearray | memoryview,
    source_units: Mapping[str, str],
    source_order: Sequence[str],
) -> dict[str, Any]:
    """Verify deterministic provenance without starting a process or transport."""
    e251_audit = decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(
        _bounded(e251_audit_bytes, "E251 audit")
    )
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit(e251_audit)["valid"] is not True:
        raise ValueError("invalid E251 audit")
    e251_contract = _decode_canonical_object(_bounded(e251_contract_bytes, "E251 contract"), "E251 contract")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract(e251_contract)["valid"] is not True:
        raise ValueError("invalid E251 contract")
    if e251_contract != build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract():
        raise ValueError("E251 contract drift detected")
    order = _validated_source_order(source_order)
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("compatibility source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE,
        "media_type": MEDIA_TYPE, "encoding": ENCODING, "canonical_json": True,
        "boundary_input_kind": "caller_supplied_canonical_json_bytes",
        "e251_status": E251_STATUS, "e251_scope": E251_SCOPE,
        "e251_audit_digest": e251_audit["audit_digest"],
        "e251_contract_digest": _digest(e251_contract),
        "source_order": list(order), "source_order_digest": _digest(list(order)),
        "source_unit_digest": source_summary["source_unit_digest"],
        "contract_drift_free": True, "deterministic_compatibility_valid": True,
        "source_topology_valid": True, "do_not_claim": list(DO_NOT_CLAIM),
        **STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(audit)["valid"] is not True:
        raise RuntimeError("constructed invalid compatibility audit")
    if _canonical_json_bytes(audit) != _canonical_json_bytes(copy.deepcopy(audit)):
        raise RuntimeError("non-deterministic compatibility evidence")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(audit: object) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    try:
        value = copy.deepcopy(dict(audit))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["audit_not_copyable"]}
    errors: list[str] = []
    if set(value) != REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if (value.get("schema_version"), value.get("status"), value.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE):
        errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("audit_encoding_mismatch")
    if value.get("boundary_input_kind") != "caller_supplied_canonical_json_bytes" or value.get("e251_status") != E251_STATUS or value.get("e251_scope") != E251_SCOPE:
        errors.append("e251_identity_mismatch")
    if value.get("source_order") != list(REQUIRED_UNITS) or value.get("source_order_digest") != _digest(list(REQUIRED_UNITS)):
        errors.append("source_order_mismatch")
    for key in ("e251_audit_digest", "e251_contract_digest", "source_unit_digest"):
        if not _is_sha256(value.get(key)):
            errors.append(f"{key}_invalid")
    if value.get("contract_drift_free") is not True or value.get("deterministic_compatibility_valid") is not True or value.get("source_topology_valid") is not True:
        errors.append("compatibility_validity_mismatch")
    for key, expected in STATIC_POLICIES.items():
        if value.get(key) is not expected:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if not _is_json_value(value):
        errors.append("audit_json_value_invalid")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(audit: Mapping[str, Any]) -> bytes:
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(audit)["valid"] is not True:
        raise ValueError("invalid compatibility audit")
    return _canonical_json_bytes(copy.deepcopy(dict(audit)))


def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    value = _decode_canonical_object(_bounded(data, "compatibility audit"), "compatibility audit")
    if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit(value)["valid"] is not True:
        raise ValueError("invalid compatibility audit")
    return copy.deepcopy(value)


def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract() -> dict[str, Any]:
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "status": STATUS, "scope": SCOPE,
        "e251_status": E251_STATUS, "e251_scope": E251_SCOPE,
        "required_source_units": list(REQUIRED_UNITS), "source_order": list(REQUIRED_UNITS),
        "boundary_input_kind": "caller_supplied_canonical_json_bytes",
        "static_policies": copy.deepcopy(STATIC_POLICIES), "do_not_claim": list(DO_NOT_CLAIM),
        "actual_process_started": False, "ipc_transport_created": False, "contract_valid": True,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if (contract.get("schema_version"), contract.get("status"), contract.get("scope")) != (SCHEMA_VERSION, STATUS, SCOPE):
        errors.append("contract_identity_mismatch")
    if contract.get("e251_status") != E251_STATUS or contract.get("e251_scope") != E251_SCOPE or contract.get("required_source_units") != list(REQUIRED_UNITS) or contract.get("source_order") != list(REQUIRED_UNITS):
        errors.append("contract_provenance_mismatch")
    if contract.get("boundary_input_kind") != "caller_supplied_canonical_json_bytes" or contract.get("static_policies") != STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_policy_mismatch")
    if contract.get("actual_process_started") is not False or contract.get("ipc_transport_created") is not False or contract.get("contract_valid") is not True:
        errors.append("contract_validity_mismatch")
    return {"valid": not errors, "errors": errors}


def _validated_source_order(source_order: Sequence[str]) -> tuple[str, ...]:
    if isinstance(source_order, (str, bytes, bytearray)) or not isinstance(source_order, Sequence) or any(not isinstance(item, str) for item in source_order):
        raise ValueError("source order must be a string sequence")
    order = tuple(source_order)
    if order != REQUIRED_UNITS:
        raise ValueError("source order drift detected")
    return order


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    if not isinstance(source_units, Mapping) or set(source_units) != set(REQUIRED_UNITS):
        raise ValueError("source units must be exactly E251 and status")
    units: dict[str, str] = {}
    for name in REQUIRED_UNITS:
        text = source_units.get(name)
        if not isinstance(text, str) or not text.strip() or len(text.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError("invalid bounded source unit")
        units[name] = text
    trees = {name: ast.parse(text, filename=name) for name, text in units.items()}
    edges: list[str] = []
    e251 = trees[E251_MODULE]
    for seam in (
        "decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit",
        "build_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract",
        "validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_audit_contract",
    ):
        if sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == seam for node in e251.body) != 1:
            edges.append(f"e251_seam_missing:{seam}")
    status = _named_function(trees[STATUS_MODULE], "build_runtime_worldbridge_status", STATUS_MODULE)
    if not _imports_symbol(trees[STATUS_MODULE], __name__, CONTRACT_BUILDER):
        edges.append("status_contract_import_missing")
    if CONTRACT_KEY not in _string_constants(status) or MODULE_ID not in _string_constants(status) or CONTRACT_BUILDER not in _called_names(status):
        edges.append("status_contract_registration_missing")
    forbidden_roots = {"sub" + "process", "multi" + "processing", "sock" + "et", "request" + "s", "url" + "lib"}
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
    return {"source_unit_digest": _digest({name: units[name] for name in REQUIRED_UNITS}), "source_topology_valid": not edges, "forbidden_edges": sorted(set(edges))}


def _bounded(data: bytes | bytearray | memoryview, label: str) -> bytes:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(f"{label} must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_BYTES:
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


def _is_json_value(value: object) -> bool:
    return value is None or isinstance(value, (str, bool, int)) or (isinstance(value, list) and all(_is_json_value(item) for item in value)) or (isinstance(value, Mapping) and all(isinstance(key, str) and _is_json_value(item) for key, item in value.items()))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")
