# -*- coding: utf-8 -*-
"""Qt-free E249 audit proving the E248 consumer remains status-only.

The audit accepts caller-supplied production source units and inspects their ASTs.
It records import/call topology, not source contents, and never imports or invokes
legacy UI adapter, command, MCP, Inspector, or runtime-action code.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit"
SCOPE = "e248_receipt_consumer_status_registration_only"
MEDIA_TYPE = "application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-consumer-non-consumption-audit+json"
ENCODING = "utf-8"
MAX_AUDIT_BYTES = 4 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
TARGET_MODULE = "core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_receipt_consumer"
STATUS_MODULE = "core.VitaLoom.simulation.runtime_worldbridge_status"
REGISTRATION_SYMBOL = "build_worldbridge_quarantine_operator_presentation_receipt_consumer_contract"
FORBIDDEN_SYMBOLS = frozenset({
    "consume_worldbridge_quarantine_operator_presentation_receipt",
    "decode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "encode_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "validate_worldbridge_quarantine_operator_presentation_receipt_consumer",
    "validate_worldbridge_quarantine_operator_presentation_receipt_consumer_contract",
})
DO_NOT_CLAIM = (
    "consumer_non_consumption_audit_is_not_runtime_execution",
    "consumer_non_consumption_audit_is_not_command_or_mcp_authority",
    "consumer_non_consumption_audit_is_not_inspector_or_ui_authority",
    "consumer_non_consumption_audit_is_not_replay_or_restore",
    "consumer_non_consumption_audit_is_not_recovery_or_retry",
    "consumer_non_consumption_audit_is_not_persistence_or_file_network_output",
    "unified_pond_default_ready",
)
_STATIC_POLICIES = {
    "read_only": True,
    "source_scan_only": True,
    "status_registration_only": True,
    "consumer_invocation_admitted": False,
    "legacy_ui_consumption_admitted": False,
    "command_registry_consumption_admitted": False,
    "mcp_consumption_admitted": False,
    "inspector_consumption_admitted": False,
    "runtime_action_consumption_admitted": False,
    "file_written": False,
    "network_transmitted": False,
    "receipt_persisted": False,
    "replay_admitted": False,
    "restore_admitted": False,
    "recovery_admitted": False,
    "same_runtime_retry_admitted": False,
    "quarantine_clear_admitted": False,
    "mutation_executed": False,
    "default_ready": False,
}
_REQUIRED_KEYS = {
    "schema_version", "status", "scope", "media_type", "encoding", "canonical_json",
    "target_module", "status_module", "registration_symbol", "scanned_unit_count",
    "source_unit_digest", "registration_edges", "forbidden_edges", "non_consumption_valid",
    "do_not_claim", "audit_digest", *_STATIC_POLICIES,
}


def audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(
    source_units: Mapping[str, str],
) -> dict[str, Any]:
    """Audit production source ASTs and prove E248 has no runtime consumer edge."""
    units = _validated_source_units(source_units)
    registration_edges: list[dict[str, str]] = []
    forbidden_edges: list[str] = []
    for unit_name, source in units.items():
        if unit_name == TARGET_MODULE:
            continue
        try:
            tree = ast.parse(source, filename=unit_name)
        except SyntaxError as exc:
            raise ValueError(f"invalid source syntax in {unit_name}: {exc.msg}") from exc
        imported_symbols, module_aliases = _target_imports(tree)
        if unit_name == STATUS_MODULE:
            if imported_symbols - {REGISTRATION_SYMBOL} or module_aliases:
                forbidden_edges.append(f"{unit_name}:target_import_not_registration_only")
            if REGISTRATION_SYMBOL in imported_symbols:
                registration_edges.append({"module": unit_name, "symbol": REGISTRATION_SYMBOL})
            for call_name in _called_names(tree):
                if call_name in FORBIDDEN_SYMBOLS:
                    forbidden_edges.append(f"{unit_name}:calls:{call_name}")
        else:
            if imported_symbols or module_aliases:
                forbidden_edges.append(f"{unit_name}:imports_target_consumer")
            for call_name in _called_names(tree):
                if call_name in FORBIDDEN_SYMBOLS or call_name.startswith(TARGET_MODULE + "."):
                    forbidden_edges.append(f"{unit_name}:calls:{call_name}")
    if registration_edges != [{"module": STATUS_MODULE, "symbol": REGISTRATION_SYMBOL}]:
        forbidden_edges.append("status_registration_edge_missing_or_duplicated")
    source_digest = _source_unit_digest(units)
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "encoding": ENCODING,
        "canonical_json": True,
        "target_module": TARGET_MODULE,
        "status_module": STATUS_MODULE,
        "registration_symbol": REGISTRATION_SYMBOL,
        "scanned_unit_count": len(units),
        "source_unit_digest": source_digest,
        "registration_edges": copy.deepcopy(registration_edges),
        "forbidden_edges": list(forbidden_edges),
        "non_consumption_valid": not forbidden_edges,
        **_STATIC_POLICIES,
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    audit["audit_digest"] = _audit_digest(audit)
    validation = validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(audit)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid E249 non-consumption audit: " + ",".join(validation["errors"]))
    if len(_canonical_json_bytes(audit)) > MAX_AUDIT_BYTES:
        raise RuntimeError("E249 non-consumption audit exceeds bounded size")
    return copy.deepcopy(audit)


def encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(audit: Mapping[str, Any]) -> bytes:
    validation = validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(audit)
    if validation["valid"] is not True:
        raise ValueError("invalid E249 non-consumption audit: " + ",".join(validation["errors"]))
    encoded = _canonical_json_bytes(dict(audit))
    if len(encoded) > MAX_AUDIT_BYTES:
        raise ValueError("E249 non-consumption audit exceeds bounded size")
    return bytes(encoded)


def decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit(
    data: bytes | bytearray | memoryview,
) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("E249 audit data must be bytes-like")
    raw = bytes(data)
    if len(raw) > MAX_AUDIT_BYTES:
        raise ValueError("E249 non-consumption audit exceeds bounded size")
    try:
        decoded = json.loads(raw.decode(ENCODING), object_pairs_hook=_reject_duplicate_object_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid canonical E249 non-consumption audit JSON") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError("E249 non-consumption audit must decode to mapping")
    validation = validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(decoded)
    if validation["valid"] is not True:
        raise ValueError("invalid E249 non-consumption audit: " + ",".join(validation["errors"]))
    if _canonical_json_bytes(dict(decoded)) != raw:
        raise ValueError("non-canonical E249 non-consumption audit JSON")
    return copy.deepcopy(dict(decoded))


def validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption(
    audit: object,
    *,
    source_units: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(audit, Mapping):
        return {"valid": False, "errors": ["audit_not_mapping"]}
    try:
        value = copy.deepcopy(dict(audit))
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["audit_not_copyable"]}
    errors: list[str] = []
    if set(value) != _REQUIRED_KEYS:
        errors.append("audit_shape_invalid")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != STATUS or value.get("scope") != SCOPE:
        errors.append("audit_identity_mismatch")
    if value.get("media_type") != MEDIA_TYPE or value.get("encoding") != ENCODING or value.get("canonical_json") is not True:
        errors.append("audit_encoding_mismatch")
    if value.get("target_module") != TARGET_MODULE or value.get("status_module") != STATUS_MODULE or value.get("registration_symbol") != REGISTRATION_SYMBOL:
        errors.append("audit_target_mismatch")
    if type(value.get("scanned_unit_count")) is not int or value["scanned_unit_count"] < 1:
        errors.append("scanned_unit_count_invalid")
    if not _is_sha256(value.get("source_unit_digest")):
        errors.append("source_unit_digest_invalid")
    if value.get("registration_edges") != [{"module": STATUS_MODULE, "symbol": REGISTRATION_SYMBOL}]:
        errors.append("registration_edges_invalid")
    if not isinstance(value.get("forbidden_edges"), list) or not all(isinstance(item, str) for item in value["forbidden_edges"]):
        errors.append("forbidden_edges_invalid")
    if value.get("non_consumption_valid") is not (not value.get("forbidden_edges")):
        errors.append("non_consumption_claim_invalid")
    for key, expected in _STATIC_POLICIES.items():
        actual = value.get(key)
        matches = actual is expected if isinstance(expected, bool) else actual == expected
        if not matches:
            errors.append(f"policy_{key}_mismatch")
    if value.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("do_not_claim_mismatch")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    if not _is_json_value(value):
        errors.append("audit_non_json_value")
    elif len(_canonical_json_bytes(value)) > MAX_AUDIT_BYTES:
        errors.append("audit_too_large")
    if source_units is not None:
        try:
            recomputed = audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption(source_units)
        except (TypeError, ValueError, RuntimeError):
            errors.append("source_units_invalid")
        else:
            if value.get("source_unit_digest") != recomputed.get("source_unit_digest"):
                errors.append("source_unit_digest_mismatch")
            if value.get("registration_edges") != recomputed.get("registration_edges") or value.get("forbidden_edges") != recomputed.get("forbidden_edges"):
                errors.append("source_graph_mismatch")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract() -> dict[str, Any]:
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "media_type": MEDIA_TYPE,
        "max_audit_bytes": MAX_AUDIT_BYTES,
        "max_source_bytes": MAX_SOURCE_BYTES,
        "target_module": TARGET_MODULE,
        "status_module": STATUS_MODULE,
        "registration_symbol": REGISTRATION_SYMBOL,
        "forbidden_symbols": sorted(FORBIDDEN_SYMBOLS),
        "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "do_not_claim": list(DO_NOT_CLAIM),
        "source_scan_only": True,
        "contract_valid": True,
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != STATUS or contract.get("scope") != SCOPE:
        errors.append("contract_identity_mismatch")
    if contract.get("media_type") != MEDIA_TYPE or contract.get("max_audit_bytes") != MAX_AUDIT_BYTES or contract.get("max_source_bytes") != MAX_SOURCE_BYTES:
        errors.append("contract_bounds_mismatch")
    if contract.get("target_module") != TARGET_MODULE or contract.get("status_module") != STATUS_MODULE or contract.get("registration_symbol") != REGISTRATION_SYMBOL:
        errors.append("contract_target_mismatch")
    if contract.get("forbidden_symbols") != sorted(FORBIDDEN_SYMBOLS):
        errors.append("contract_forbidden_symbols_mismatch")
    if contract.get("static_policies") != _STATIC_POLICIES or contract.get("do_not_claim") != list(DO_NOT_CLAIM):
        errors.append("contract_policy_mismatch")
    if contract.get("source_scan_only") is not True or contract.get("contract_valid") is not True:
        errors.append("contract_authority_mismatch")
    return {"valid": not errors, "errors": errors}


def _validated_source_units(source_units: object) -> dict[str, str]:
    if not isinstance(source_units, Mapping) or not source_units:
        raise TypeError("source_units must be a non-empty mapping")
    result: dict[str, str] = {}
    total_bytes = 0
    for unit_name, source in source_units.items():
        if not isinstance(unit_name, str) or not unit_name or "\\" in unit_name or "/" in unit_name or ".." in unit_name:
            raise ValueError("source unit names must be normalized module identifiers")
        if not isinstance(source, str):
            raise TypeError(f"source unit {unit_name} must be text")
        total_bytes += len(source.encode(ENCODING))
        if total_bytes > MAX_SOURCE_BYTES:
            raise ValueError("source units exceed bounded audit input")
        result[unit_name] = source
    if TARGET_MODULE not in result or STATUS_MODULE not in result:
        raise ValueError("source units must include target and status modules")
    return result


def _target_imports(tree: ast.AST) -> tuple[set[str], set[str]]:
    imported_symbols: set[str] = set()
    module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == TARGET_MODULE:
            for alias in node.names:
                if alias.name == "*":
                    module_aliases.add("*")
                else:
                    imported_symbols.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == TARGET_MODULE:
                    module_aliases.add(alias.asname or TARGET_MODULE)
    return imported_symbols, module_aliases


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            qualified = _qualified_name(node.func)
            if qualified:
                names.add(qualified)
    return names


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def _source_unit_digest(units: Mapping[str, str]) -> str:
    entries = {name: hashlib.sha256(source.encode(ENCODING)).hexdigest() for name, source in sorted(units.items())}
    return hashlib.sha256(_canonical_json_bytes(entries)).hexdigest()


def _audit_digest(value: Mapping[str, Any]) -> str:
    canonical = dict(value)
    canonical.pop("audit_digest", None)
    return hashlib.sha256(_canonical_json_bytes(canonical)).hexdigest()


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
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


__all__ = [
    "DO_NOT_CLAIM", "ENCODING", "MAX_AUDIT_BYTES", "MAX_SOURCE_BYTES", "MEDIA_TYPE", "REGISTRATION_SYMBOL", "SCOPE", "STATUS", "STATUS_MODULE", "TARGET_MODULE",
    "audit_worldbridge_quarantine_operator_presentation_consumer_non_consumption",
    "build_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract",
    "decode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit",
    "encode_worldbridge_quarantine_operator_presentation_consumer_non_consumption_audit",
    "validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption",
    "validate_worldbridge_quarantine_operator_presentation_consumer_non_consumption_contract",
]

