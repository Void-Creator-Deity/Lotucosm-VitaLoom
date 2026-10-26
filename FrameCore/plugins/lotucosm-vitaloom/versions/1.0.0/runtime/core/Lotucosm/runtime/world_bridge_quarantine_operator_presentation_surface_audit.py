# -*- coding: utf-8 -*-
"""Qt-free E246 audit for the bounded E244/E245 operator presentation surfaces.

This boundary only compares already-produced command, MCP, and Inspector values.  It
cannot observe lifecycle tokens, invoke runtime actions, or grant UI authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from core.Lotucosm.runtime.world_bridge_quarantine_operator_evidence_bundle import (
    validate_worldbridge_quarantine_operator_evidence_bundle,
)
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
    NEGATIVE_CAPABILITIES,
)

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation_surface_audit"
SCOPE = "validated_e244_command_mcp_e245_inspector_surfaces_only"
COMMAND_ID = "runtime.worldbridge.quarantine_operator_evidence_bundle"
MAX_AUDIT_BYTES = 4 * 1024
VISIBLE_FIELD_IDS = (
    "consumer_scope",
    "availability",
    "operator_state",
    "headline",
    "caveat",
    "current_runtime_quarantined",
    "same_adapter_only",
    "evidence_summary",
    "negative_capabilities",
    "do_not_claim",
    "source_export_digest",
    "source_audit_digest",
    "bundle_digest",
)
_RAW_LIFECYCLE_KEYS = frozenset({
    "sr_runtime_epoch",
    "pond_lifetime_token",
    "failure_sr_runtime_epoch",
    "failure_pond_lifetime_token",
    "current_sr_runtime_epoch",
    "current_pond_lifetime_token",
})
_STATIC_POLICIES = {
    "read_only": True,
    "same_adapter_only": True,
    "opaque_lifecycle_values_exposed": False,
    "runtime_action_authority": False,
    "ui_authority": False,
    "quarantine_clear_admitted": False,
    "same_runtime_retry_admitted": False,
    "recovery_admitted": False,
    "replay_or_restore_admitted": False,
    "persistence_admitted": False,
    "default_ready": False,
}
_REQUIRED_AUDIT_KEYS = {
    "schema_version", "status", "scope", "read_only", "visible_field_ids",
    "command_mcp_parity_valid", "inspector_parity_valid", "inspector_fields_editable",
    "same_adapter_only", "opaque_lifecycle_values_exposed", "runtime_action_authority",
    "ui_authority", "quarantine_clear_admitted", "same_runtime_retry_admitted",
    "recovery_admitted", "replay_or_restore_admitted", "persistence_admitted",
    "default_ready", "source_bundle_digest", "visible_field_digest", "audit_digest",
}


def audit_worldbridge_quarantine_operator_presentation_surfaces(
    command_result: Mapping[str, Any],
    mcp_result: Mapping[str, Any],
    inspector_view: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate exact bounded E244/E245 presentation parity across three surfaces."""
    command_bundle = _validated_command_envelope(command_result, "command_result")
    mcp_bundle = _validated_command_envelope(mcp_result, "mcp_result")
    if command_bundle["bundle_digest"] != mcp_bundle["bundle_digest"]:
        raise ValueError("command and MCP evidence bundle digest mismatch")
    command_visible = _visible_values(command_bundle)
    if command_visible != _visible_values(mcp_bundle):
        raise ValueError("command and MCP visible field mismatch")
    inspector_values = _validated_inspector_view(inspector_view, command_bundle)
    if inspector_values != command_visible:
        raise ValueError("Inspector visible field mismatch")
    _reject_raw_lifecycle_keys(command_result, "command_result")
    _reject_raw_lifecycle_keys(mcp_result, "mcp_result")
    _reject_raw_lifecycle_keys(inspector_view, "inspector_view")
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "command_mcp_parity_valid": True,
        "inspector_parity_valid": True,
        "inspector_fields_editable": False,
        "source_bundle_digest": command_bundle["bundle_digest"],
        "visible_field_digest": _digest(command_visible),
        **_STATIC_POLICIES,
    }
    audit["audit_digest"] = _audit_digest(audit)
    validation = validate_worldbridge_quarantine_operator_presentation_surface_audit(audit)
    if validation["valid"] is not True:
        raise RuntimeError("constructed invalid quarantine presentation surface audit: " + ",".join(validation["errors"]))
    if len(_canonical_json_bytes(audit)) > MAX_AUDIT_BYTES:
        raise RuntimeError("quarantine presentation surface audit exceeds bounded size")
    return copy.deepcopy(audit)


def validate_worldbridge_quarantine_operator_presentation_surface_audit(audit: object) -> dict[str, Any]:
    """Fail closed unless an E246 audit retains its complete static policy."""
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
    if value.get("visible_field_ids") != list(VISIBLE_FIELD_IDS):
        errors.append("visible_field_ids_mismatch")
    for key, expected in _STATIC_POLICIES.items():
        if value.get(key) is not expected:
            errors.append(f"policy_{key}_mismatch")
    if value.get("command_mcp_parity_valid") is not True or value.get("inspector_parity_valid") is not True:
        errors.append("surface_parity_missing")
    if value.get("inspector_fields_editable") is not False:
        errors.append("inspector_must_be_non_editable")
    if not _is_sha256(value.get("source_bundle_digest")) or not _is_sha256(value.get("visible_field_digest")):
        errors.append("source_digest_invalid")
    if value.get("audit_digest") != _audit_digest(value):
        errors.append("audit_digest_mismatch")
    if not _is_json_value(value):
        errors.append("audit_non_json_value")
    elif len(_canonical_json_bytes(value)) > MAX_AUDIT_BYTES:
        errors.append("audit_too_large")
    return {"valid": not errors, "errors": errors}


def build_worldbridge_quarantine_operator_presentation_surface_audit_contract() -> dict[str, Any]:
    """Return the static, non-authoritative E246 cross-surface contract."""
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "command_id": COMMAND_ID,
        "visible_field_ids": list(VISIBLE_FIELD_IDS),
        "max_audit_bytes": MAX_AUDIT_BYTES,
        "static_policies": copy.deepcopy(_STATIC_POLICIES),
        "requires_command_mcp_parity": True,
        "requires_inspector_parity": True,
        "requires_non_editable_inspector_fields": True,
        "raw_lifecycle_keys_exposed": False,
    }
    contract["contract_valid"] = True
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_surface_audit_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_surface_audit_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_not_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("status") != STATUS or contract.get("scope") != SCOPE:
        errors.append("contract_identity_mismatch")
    if contract.get("command_id") != COMMAND_ID or contract.get("visible_field_ids") != list(VISIBLE_FIELD_IDS):
        errors.append("contract_surface_mismatch")
    if contract.get("max_audit_bytes") != MAX_AUDIT_BYTES or contract.get("static_policies") != _STATIC_POLICIES:
        errors.append("contract_policy_mismatch")
    for key in ("requires_command_mcp_parity", "requires_inspector_parity", "requires_non_editable_inspector_fields"):
        if contract.get(key) is not True:
            errors.append(f"contract_{key}_missing")
    if contract.get("raw_lifecycle_keys_exposed") is not False or contract.get("contract_valid") is not True:
        errors.append("contract_non_authority_mismatch")
    return {"valid": not errors, "errors": errors}


def _validated_command_envelope(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not _is_json_value(value):
        raise ValueError(f"{name} must be a JSON-safe mapping")
    if value.get("ok") is not True or not isinstance(value.get("result"), Mapping):
        raise ValueError(f"{name} must be a successful evidence-bundle command result")
    bundle = copy.deepcopy(dict(value["result"]))
    validation = validate_worldbridge_quarantine_operator_evidence_bundle(bundle)
    if validation["valid"] is not True:
        raise ValueError(f"{name} contains invalid evidence bundle: " + ",".join(validation["errors"]))
    if bundle.get("read_only") is not True or bundle.get("same_adapter_only") is not True:
        raise ValueError(f"{name} overclaims evidence authority")
    if bundle.get("negative_capabilities") != {key: False for key in NEGATIVE_CAPABILITIES}:
        raise ValueError(f"{name} negative capabilities mismatch")
    return bundle


def _validated_inspector_view(value: object, bundle: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not _is_json_value(value):
        raise ValueError("inspector_view must be a JSON-safe mapping")
    if value.get("read_only") is not True or value.get("authority_command_id") != COMMAND_ID:
        raise ValueError("Inspector view authority mismatch")
    if value.get("scope") != bundle.get("consumer_scope") or value.get("error") is not None:
        raise ValueError("Inspector view scope or error mismatch")
    if value.get("available") is not (bundle.get("availability") == "available"):
        raise ValueError("Inspector view availability mismatch")
    section = value.get("section")
    if not isinstance(section, Mapping) or section.get("id") != "worldbridge-quarantine-operator-evidence-bundle":
        raise ValueError("Inspector view section mismatch")
    fields = section.get("fields")
    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes, bytearray)) or len(fields) != len(VISIBLE_FIELD_IDS):
        raise ValueError("Inspector visible field shape mismatch")
    projected: dict[str, Any] = {}
    for expected_id, field in zip(VISIBLE_FIELD_IDS, fields):
        if not isinstance(field, Mapping) or field.get("id") != expected_id or field.get("editable") is not False:
            raise ValueError("Inspector field identity or editability mismatch")
        projected[expected_id] = copy.deepcopy(field.get("value"))
    return projected


def _visible_values(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {field_id: copy.deepcopy(bundle[field_id]) for field_id in VISIBLE_FIELD_IDS}


def _reject_raw_lifecycle_keys(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _RAW_LIFECYCLE_KEYS:
                raise ValueError(f"{name} exposes raw lifecycle key: {key}")
            _reject_raw_lifecycle_keys(item, name)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_lifecycle_keys(item, name)


def _audit_digest(value: Mapping[str, Any]) -> str:
    copy_value = dict(value)
    copy_value.pop("audit_digest", None)
    return _digest(copy_value)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


__all__ = [
    "COMMAND_ID", "MAX_AUDIT_BYTES", "SCOPE", "STATUS", "VISIBLE_FIELD_IDS",
    "audit_worldbridge_quarantine_operator_presentation_surfaces",
    "build_worldbridge_quarantine_operator_presentation_surface_audit_contract",
    "validate_worldbridge_quarantine_operator_presentation_surface_audit",
    "validate_worldbridge_quarantine_operator_presentation_surface_audit_contract",
]


