# -*- coding: utf-8 -*-
"""Qt-free E250 audit for read-only WorldBridge status projection surfaces.

This module receives already-produced command/MCP envelopes and caller-supplied
source text.  It extracts only two static E248/E249 contracts from the broad
WorldBridge status document; it never accepts a receipt, imports command/MCP/UI
modules, calls a consumer operation, or executes a runtime action.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit import (
    build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
    validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer import (
    build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
    validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_status_projection_audit"
SCOPE = "e248_e249_contracts_on_existing_read_only_status_command_mcp_mirror"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 4 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
COMMAND_ID = "runtime.worldbridge.status"
COMMAND_MODULE = "core.VitaLoom.commands.runtime_commands"
MCP_MODULE = "core.VitaLoom.commands.mcp_adapter"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
COMMAND_HANDLER = "_runtime_worldbridge_status"
MCP_HELPER = "get_runtime_worldbridge_status"
STATUS_BUILDER = "build_runtime_worldbridge_status"
CONSUMER_CONTRACT_KEY = "failure_quarantine_operator_presentation_receipt_consumer_contract"
NON_CONSUMPTION_CONTRACT_KEY = "failure_quarantine_operator_presentation_consumer_non_consumption_audit_contract"
CONSUMER_MODULE_ID = "quarantine_operator_presentation_receipt_consumer_module"
NON_CONSUMPTION_MODULE_ID = "quarantine_operator_presentation_consumer_non_consumption_audit_module"
CONSUMER_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer"
NON_CONSUMPTION_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_consumer_non_consumption_audit"
CONSUMER_CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract"
NON_CONSUMPTION_CONTRACT_BUILDER = "build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract"

_FORBIDDEN_OPERATION_SYMBOLS = frozenset({
    "consume_worldbridge_quarantine_operator_presentation_receipt",
    "decode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "encode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "validate_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "build_worldbridge_quarantine_operator_presentation_surface_receipt",
    "decode_worldbridge_quarantine_operator_presentation_surface_receipt",
    "encode_worldbridge_quarantine_operator_presentation_surface_receipt",
    "validate_worldbridge_quarantine_operator_presentation_surface_receipt",
})
_STATIC_POLICIES = {
    "read_only": True,
    "status_projection_only": True,
    "command_mcp_direct_mirror_only": True,
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
    "status_projection_audit_is_not_receipt_consumption_or_execution",
    "status_projection_audit_is_not_command_or_mcp_authority",
    "status_projection_audit_is_not_inspector_or_ui_authority",
    "status_projection_audit_is_not_replay_restore_recovery_or_retry",
    "status_projection_audit_is_not_persistence_or_file_network_output",
    "unified_pond_default_ready",
)
_REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "command_id", "projection_keys", "pilot_module_ids", "command_mcp_parity_valid",
    "status_contract_projection_valid", "source_topology_valid", "source_unit_digest",
    "projection_digest", "audit_digest", "do_not_claim", *_STATIC_POLICIES,
}
_REQUIRED_SOURCE_UNITS = frozenset({COMMAND_MODULE, MCP_MODULE, STATUS_MODULE})
_PROJECTION_KEYS = (
    "runtime_mode",
    "unified_pond_enabled",
    "default_ready",
    CONSUMER_CONTRACT_KEY,
    NON_CONSUMPTION_CONTRACT_KEY,
)
_PILOT_MODULE_IDS = (CONSUMER_MODULE_ID, NON_CONSUMPTION_MODULE_ID)


def audit_worldbridge_quarantine_operator_presentation_status_projection(
    command_result: Mapping[str, Any],
    mcp_result: Mapping[str, Any],
    source_units: Mapping[str, str],
) -> dict[str, Any]:
    """Audit the existing status command/MCP mirror without executing either surface."""
    command_projection = _validated_status_projection(command_result, "command_result")
    mcp_projection = _validated_status_projection(mcp_result, "mcp_result")
    if command_projection != mcp_projection:
        raise ValueError("command and MCP status projection mismatch")
    source_summary = _audit_source_topology(source_units)
    if source_summary["source_topology_valid"] is not True:
        raise ValueError("status projection source topology invalid: " + ",".join(source_summary["forbidden_edges"]))
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "command_id": COMMAND_ID,
        "projection_keys": list(_PROJECTION_KEYS),
        "pilot_module_ids": list(_PILOT_MODULE_IDS),
        "command_mcp_parity_valid": True,
        "status_contract_projection_valid": True,
        "source_topology_valid": True,
        "source_unit_digest": source_summary["source_unit_digest"],
        "projection_digest": _digest(command_projection),
        "do_not_claim": list(DO_NOT_CLAIM),
        **_STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    validation = validate_worldbridge_quarantine_operator_presentation_status_projection_audit(audit)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid status projection audit: " + ",".join(validation["errors"]))
    if len(_canonical_json_bytes(audit)) > MAX_AUDIT_BYTES:
        raise RuntimeError("status projection audit exceeds bounded size")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_status_projection_audit(audit: object) -> dict[str, Any]:
    """Fail closed unless the E250 record preserves fixed read-only policies."""
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    try:
        value = copy.deepcopy(dict(audit))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["audit_not_copyable"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_AUDIT_KEYS:
        errors.append("audit_shape_invalid")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS or value.get("scope") != SCOPE:
        errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("audit_encoding_mismatch")
    if value.get("command_id") != COMMAND_ID:
        errors.append("command_id_mismatch")
    if value.get("projection_keys") != list(_PROJECTION_KEYS) or value.get("pilot_module_ids") != list(_PILOT_MODULE_IDS):
        errors.append("projection_allowlist_mismatch")
    if value.get("command_mcp_parity_valid") is not True or value.get("status_contract_projection_valid") is not True:
        errors.append("projection_validity_mismatch")
    if value.get("source_topology_valid") is not True or not _is_sha256(value.get("source_unit_digest")):
        errors.append("source_topology_mismatch")
    if not _is_sha256(value.get("projection_digest")):
        errors.append("projection_digest_invalid")
    for key, expected in _STATIC_POLICIES.items():
        if value.get(key) is not expected:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if not _is_json_value(value):
        errors.append("audit_json_value_invalid")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    try:
        if len(_canonical_json_bytes(value)) > MAX_AUDIT_BYTES:
            errors.append("audit_size_exceeded")
    except (TypeError, ValueError):
        errors.append("audit_canonicalization_failed")
    return {"valid": not errors, "errors": errors}


def encode_worldbridge_quarantine_operator_presentation_status_projection_audit(audit: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_quarantine_operator_presentation_status_projection_audit(audit)
    if validation["valid"] is not True:
        raise ValueError("invalid status projection audit: " + ",".join(validation["errors"]))
    return _canonical_json_bytes(copy.deepcopy(dict(audit)))


def decode_worldbridge_quarantine_operator_presentation_status_projection_audit(
    data: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("audit data must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_AUDIT_BYTES:
        raise ValueError("audit data exceeds bounded size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError("invalid canonical status projection audit") from exc
    if not isinstance(decoded, dict) or _canonical_json_bytes(decoded) != raw:
        raise ValueError("status projection audit is non-canonical")
    validation = validate_worldbridge_quarantine_operator_presentation_status_projection_audit(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid status projection audit: " + ",".join(validation["errors"]))
    return copy.deepcopy(decoded)


def build_worldbridge_quarantine_operator_presentation_status_projection_audit_contract() -> dict[str, Any]:
    """Return the static contract for the E250 read-only projection audit."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "command_id": COMMAND_ID,
        "projection_keys": list(_PROJECTION_KEYS),
        "pilot_module_ids": list(_PILOT_MODULE_IDS),
        "required_source_units": sorted(_REQUIRED_SOURCE_UNITS),
        "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM),
        "raw_receipt_input_admitted": False,
        "consumer_operation_admitted": False,
        "contract_valid": True,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_status_projection_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != STATUS or contract.get("scope") != SCOPE:
        errors.append("contract_identity_mismatch")
    if contract.get("command_id") != COMMAND_ID:
        errors.append("contract_command_mismatch")
    if contract.get("projection_keys") != list(_PROJECTION_KEYS) or contract.get("pilot_module_ids") != list(_PILOT_MODULE_IDS):
        errors.append("contract_projection_mismatch")
    if contract.get("required_source_units") != sorted(_REQUIRED_SOURCE_UNITS):
        errors.append("contract_source_units_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_policy_mismatch")
    if contract.get("raw_receipt_input_admitted") is not False or contract.get("consumer_operation_admitted") is not False:
        errors.append("contract_operation_mismatch")
    if contract.get("contract_valid") is not True:
        errors.append("contract_validity_mismatch")
    return {"valid": not errors, "errors": errors}


def _validated_status_projection(envelope: object, name: str) -> dict[str, Any]:
    if not isinstance(envelope, Mapping) or envelope.get("ok") is not True:
        raise ValueError(f"{name} must be a successful command envelope")
    result = envelope.get("result")
    if not isinstance(result, Mapping):
        raise ValueError(f"{name} result must be a mapping")
    _reject_raw_receipt_top_level_keys(result, name)
    if result.get("runtime_mode") != "dual" or result.get("unified_pond_enabled") is not False or result.get("default_ready") is not False:
        raise ValueError(f"{name} default boundary mismatch")
    consumer = _validated_contract(
        result.get(CONSUMER_CONTRACT_KEY),
        validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract,
        "receipt consumer",
    )
    non_consumption = _validated_contract(
        result.get(NON_CONSUMPTION_CONTRACT_KEY),
        validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract,
        "non-consumption audit",
    )
    pilot_modules = result.get("pilot_modules")
    if not isinstance(pilot_modules, Sequence) or isinstance(pilot_modules, (str, bytes, bytearray)):
        raise ValueError(f"{name} pilot_modules must be a sequence")
    if any(not isinstance(item, str) for item in pilot_modules):
        raise ValueError(f"{name} pilot_modules contains a non-string")
    if any(list(pilot_modules).count(module_id) != 1 for module_id in _PILOT_MODULE_IDS):
        raise ValueError(f"{name} pilot module projection mismatch")
    projection = {
        "runtime_mode": "dual",
        "unified_pond_enabled": False,
        "default_ready": False,
        CONSUMER_CONTRACT_KEY: consumer,
        NON_CONSUMPTION_CONTRACT_KEY: non_consumption,
        "pilot_module_ids": list(_PILOT_MODULE_IDS),
    }
    return copy.deepcopy(projection)


def _validated_contract(value: object, validator: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} contract must be a mapping")
    copied = copy.deepcopy(dict(value))
    validation = validator(copied)
    if validation["valid"] is not True:
        raise ValueError(f"invalid {label} contract: " + ",".join(validation["errors"]))
    return copied


def _audit_source_topology(source_units: Mapping[str, str]) -> dict[str, Any]:
    units = _validated_source_units(source_units)
    parsed: dict[str, ast.Module] = {}
    for unit_name, source in units.items():
        try:
            parsed[unit_name] = ast.parse(source, filename=unit_name)
        except SyntaxError as exc:
            raise ValueError(f"invalid source syntax in {unit_name}: {exc.msg}") from exc
    edges: list[str] = []
    command = _named_function(parsed[COMMAND_MODULE], COMMAND_HANDLER, COMMAND_MODULE)
    command_calls = _called_names(command)
    if not {"command_ok", STATUS_BUILDER}.issubset(command_calls) or command_calls - {"command_ok", "command_error", STATUS_BUILDER, "_resolve_workspace_path", "str", "payload.get"}:
        edges.append("command_handler_not_status_projection")
    edges.extend(_forbidden_edges(COMMAND_MODULE, command))
    edges.extend(_forbidden_import_edges(COMMAND_MODULE, parsed[COMMAND_MODULE], allowed_symbols=frozenset()))
    mcp = _named_function(parsed[MCP_MODULE], MCP_HELPER, MCP_MODULE)
    mcp_calls = _called_names(mcp)
    if mcp_calls - {"run_command", "dict"} or "run_command" not in mcp_calls or COMMAND_ID not in _string_constants(mcp):
        edges.append("mcp_helper_not_direct_status_mirror")
    edges.extend(_forbidden_edges(MCP_MODULE, mcp))
    edges.extend(_forbidden_import_edges(MCP_MODULE, parsed[MCP_MODULE], allowed_symbols=frozenset()))
    status = _named_function(parsed[STATUS_MODULE], STATUS_BUILDER, STATUS_MODULE)
    status_calls = _called_names(status)
    if not {CONSUMER_CONTRACT_BUILDER, NON_CONSUMPTION_CONTRACT_BUILDER}.issubset(status_calls):
        edges.append("status_contract_builders_missing")
    if CONSUMER_CONTRACT_KEY not in _string_constants(status) or NON_CONSUMPTION_CONTRACT_KEY not in _string_constants(status):
        edges.append("status_contract_keys_missing")
    if not _imports_symbol(parsed[STATUS_MODULE], CONSUMER_MODULE, CONSUMER_CONTRACT_BUILDER):
        edges.append("status_consumer_contract_import_missing")
    if not _imports_symbol(parsed[STATUS_MODULE], NON_CONSUMPTION_MODULE, NON_CONSUMPTION_CONTRACT_BUILDER):
        edges.append("status_non_consumption_contract_import_missing")
    edges.extend(_forbidden_edges(STATUS_MODULE, status))
    edges.extend(_forbidden_import_edges(
        STATUS_MODULE,
        parsed[STATUS_MODULE],
        allowed_symbols=frozenset({CONSUMER_CONTRACT_BUILDER, NON_CONSUMPTION_CONTRACT_BUILDER}),
    ))
    return {
        "source_unit_digest": _source_unit_digest(units),
        "source_topology_valid": not edges,
        "forbidden_edges": sorted(set(edges)),
    }


def _validated_source_units(source_units: object) -> dict[str, str]:
    if not isinstance(source_units, Mapping) or set(source_units) != _REQUIRED_SOURCE_UNITS:
        raise ValueError("source_units must contain exactly the E250 command, MCP, and status modules")
    copied: dict[str, str] = {}
    for name in sorted(_REQUIRED_SOURCE_UNITS):
        source = source_units.get(name)
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"source unit must be non-empty text: {name}")
        if len(source.encode(ENCODING)) > MAX_SOURCE_BYTES:
            raise ValueError(f"source unit exceeds bounded size: {name}")
        copied[name] = source
    return copied


def _named_function(tree: ast.Module, name: str, module: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    matches = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"{module} must define exactly one {name}")
    return matches[0]


def _forbidden_edges(module: str, function: ast.AST) -> list[str]:
    names = _called_names(function)
    return [f"{module}:calls:{name}" for name in sorted(names & _FORBIDDEN_OPERATION_SYMBOLS)]


def _forbidden_import_edges(module: str, tree: ast.AST, *, allowed_symbols: frozenset[str]) -> list[str]:
    edges: list[str] = []
    monitored_modules = {CONSUMER_MODULE, NON_CONSUMPTION_MODULE}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in monitored_modules:
            imported = {alias.name for alias in node.names}
            if not imported.issubset(allowed_symbols):
                edges.append(f"{module}:imports_operational_consumer_symbol")
        elif isinstance(node, ast.Import) and any(alias.name in monitored_modules for alias in node.names):
            edges.append(f"{module}:imports_consumer_module")
    return edges


def _reject_raw_receipt_top_level_keys(result: Mapping[str, Any], name: str) -> None:
    forbidden = {"receipt", "raw_receipt", "receipt_bytes", "surface_receipt"}
    leaked = sorted(forbidden & {str(key) for key in result})
    if leaked:
        raise ValueError(f"{name} exposes raw receipt input: {','.join(leaked)}")


def _imports_symbol(tree: ast.AST, module: str, symbol: str) -> bool:
    return any(
        isinstance(node, ast.ImportFrom) and node.module == module and any(alias.name == symbol for alias in node.names)
        for node in ast.walk(tree)
    )


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _qualified_name(node.func)
            if name:
                names.add(name)
    return names


def _string_constants(tree: ast.AST) -> set[str]:
    return {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _qualified_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _source_unit_digest(units: Mapping[str, str]) -> str:
    return _digest({name: units[name] for name in sorted(units)})


def _audit_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("audit_digest", None)
    return _digest(canonical)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(ENCODING)


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return False
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")
