# -*- coding: utf-8 -*-
"""Bounded, Qt-free operator presentation for E241 lifecycle evidence.

This module is a consumer boundary only. It redacts opaque lifecycle values and
never turns lifecycle observation into runtime control authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
STATUS = "worldbridge_quarantine_operator_presentation"
SOURCE_STATUS = "worldbridge_quarantine_lifecycle_correlation"
SCOPE = "same_adapter_worldbridge_quarantine_operator_presentation"
UNAVAILABLE_STATUS = "unavailable"

NEGATIVE_CAPABILITIES = (
    "may_clear_quarantine",
    "may_retry_same_runtime_handoff",
    "may_construct_or_reuse_pond",
    "may_call_sr_ps_bridge_mutator",
    "fresh_boundary_is_state_recovery",
    "rollback_performed",
    "compensation_performed",
    "in_place_restore",
    "replay_admitted",
    "cross_adapter_lifecycle_correlation",
    "operator_action_admitted",
    "ui_authority",
    "default_ready",
)
KNOWN_STATES = frozenset(
    {
        "current_quarantined_lifecycle_evidence_incomplete",
        "current_quarantined_failure_tuple_observed",
        "no_captured_failure_lifecycle_evidence",
        "historical_after_observed_disposal_no_current_sr_pond_pair",
        "historical_or_unverified_after_current_quarantine_cleared",
        "fresh_instance_boundary_observed",
        "current_lifecycle_not_proven_fresh_from_failure",
    }
)
DO_NOT_CLAIM = (
    "operator_presentation_is_not_recovery",
    "operator_presentation_is_not_same_runtime_retry",
    "operator_presentation_is_not_re_admission",
    "operator_presentation_is_not_restore_or_replay",
    "operator_presentation_is_not_cross_adapter_correlation",
    "operator_presentation_is_not_ui_authority",
    "unified_pond_default_ready",
)

_STATE_TEXT: dict[str, tuple[str, str]] = {
    "current_quarantined_lifecycle_evidence_incomplete": (
        "当前运行时已隔离，生命周期证据不完整",
        "只能呈示隔离事实；不推断可安全重试或恢复。",
    ),
    "current_quarantined_failure_tuple_observed": (
        "当前运行时仍被隔离，已观测到故障时生命周期对",
        "证据仅限同一适配器，不授权清除隔离或重试交接。",
    ),
    "no_captured_failure_lifecycle_evidence": (
        "未捕获到故障生命周期证据",
        "不应从当前隔离状态反推恢复、重试或重建。",
    ),
    "historical_after_observed_disposal_no_current_sr_pond_pair": (
        "已观察到隔离后销毁边界，但没有当前 SR/Pond 对",
        "这是历史边界记录，不表示运行时已恢复或可重放。",
    ),
    "historical_or_unverified_after_current_quarantine_cleared": (
        "当前隔离已不处于活动状态，但缺少新实例证明",
        "不能由隔离状态变化推断运行时恢复、重试或重准入。",
    ),
    "fresh_instance_boundary_observed": (
        "已观察到独立的新 SR/Pond 生命周期边界",
        "这只是新实例边界观测，不是恢复、重试、重准入、还原、重放或默认就绪。",
    ),
    "current_lifecycle_not_proven_fresh_from_failure": (
        "当前生命周期与故障记录不同，但新实例未被证明",
        "SR 运行时或 Pond 存活令牌只变更一项时，不是新实例证据。",
    ),
}


def _copy_mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return copy.deepcopy(dict(value))


def _require_false_capabilities(value: Mapping[str, Any]) -> None:
    negative = value.get("negative_capabilities")
    if not isinstance(negative, Mapping):
        raise ValueError("negative_capabilities missing")
    for key in (*NEGATIVE_CAPABILITIES[:10], "default_ready"):
        if negative.get(key) is not False:
            raise ValueError(f"negative_capabilities.{key} must be false")


def _validate_source_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("source schema_version mismatch")
    if value.get("read_only") is not True:
        raise ValueError("source must be read-only")
    availability = value.get("availability")
    status = value.get("status")
    _require_false_capabilities(value)
    if status == UNAVAILABLE_STATUS or availability == UNAVAILABLE_STATUS:
        if status != UNAVAILABLE_STATUS or availability != UNAVAILABLE_STATUS:
            raise ValueError("unavailable source status/availability mismatch")
        return {
            "available": False,
            "current_runtime_quarantined": None,
            "reason": value.get("reason") if isinstance(value.get("reason"), str) else "lifecycle_evidence_unavailable",
        }
    if status != SOURCE_STATUS or availability != "available":
        raise ValueError("source is not an E241 lifecycle projection")
    if not isinstance(value.get("current_runtime_quarantined"), bool):
        raise ValueError("current_runtime_quarantined must be bool")
    correlation = value.get("correlation")
    if not isinstance(correlation, Mapping):
        raise ValueError("correlation missing")
    state = correlation.get("state")
    if state not in KNOWN_STATES:
        raise ValueError("unknown lifecycle correlation state")
    if correlation.get("same_adapter_only") is not True:
        raise ValueError("same_adapter_only must be true")
    if correlation.get("fresh_instance_boundary_observed") not in (True, False):
        raise ValueError("fresh_instance_boundary_observed must be bool")
    return {
        "available": True,
        "current_runtime_quarantined": value["current_runtime_quarantined"],
        "state": state,
        "fresh_instance_boundary_observed": correlation["fresh_instance_boundary_observed"],
        "disposal_boundary": (
            correlation.get("observed_disposal", {}).get("boundary")
            if isinstance(correlation.get("observed_disposal"), Mapping)
            else None
        ),
        "disposal_recorded": (
            correlation.get("observed_disposal", {}).get("recorded") is True
            if isinstance(correlation.get("observed_disposal"), Mapping)
            else False
        ),
    }


def _validate_artifact_import_diagnostic(value: object) -> dict[str, Any] | None:
    """Keep import rejection useful without exposing the rejected artifact."""
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("artifact_import_diagnostic must be a mapping or None")
    if value.get("recorded") is not True:
        raise ValueError("artifact_import_diagnostic must be recorded")
    if value.get("schema_version") != 1:
        raise ValueError("artifact_import_diagnostic schema_version mismatch")
    code = value.get("code")
    errors = value.get("errors")
    digest = value.get("diagnostic_digest")
    if not isinstance(code, str) or not code or len(code) > 160:
        raise ValueError("artifact_import_diagnostic code invalid")
    if not isinstance(errors, list) or not errors or len(errors) > 32:
        raise ValueError("artifact_import_diagnostic errors invalid")
    if any(not isinstance(error, str) or not error or len(error) > 512 for error in errors):
        raise ValueError("artifact_import_diagnostic error item invalid")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise ValueError("artifact_import_diagnostic digest invalid")
    return {
        "recorded": True,
        "schema_version": 1,
        "code": code,
        "errors": list(errors),
        "diagnostic_digest": digest,
    }


def _validate_replay_persistence_diagnostic(value: object) -> dict[str, Any] | None:
    """Expose only E509 rejection provenance; never expose the envelope."""
    if value is None:
        return None
    if not isinstance(value, Mapping) or value.get("recorded") is not True:
        raise ValueError("replay_persistence_diagnostic must be recorded")
    if value.get("schema_version") != 1:
        raise ValueError("replay_persistence_diagnostic schema_version mismatch")
    code = value.get("code")
    errors = value.get("errors")
    digest = value.get("diagnostic_digest")
    if not isinstance(code, str) or not code or len(code) > 160:
        raise ValueError("replay_persistence_diagnostic code invalid")
    if not isinstance(errors, list) or not errors or len(errors) > 32:
        raise ValueError("replay_persistence_diagnostic errors invalid")
    if any(not isinstance(error, str) or not error or len(error) > 512 for error in errors):
        raise ValueError("replay_persistence_diagnostic error item invalid")
    payload = {"schema_version": 1, "code": code, "errors": list(errors)}
    expected = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    if set(value) == {"recorded", "schema_version", "code", "errors", "diagnostic_digest"}:
        if digest != expected:
            raise ValueError("replay_persistence_diagnostic digest mismatch")
    else:
        private_required = {"schema_version", "code", "errors", "checkpoint_id", "checkpoint_digest", "diagnostic_digest"}
        if set(value) != private_required | {"recorded"}:
            raise ValueError("replay_persistence_diagnostic shape invalid")
        private_payload = {key: value[key] for key in private_required if key != "diagnostic_digest"}
        private_expected = hashlib.sha256(json.dumps(private_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        if digest != private_expected:
            raise ValueError("replay_persistence_diagnostic digest mismatch")
        digest = expected
    return {"recorded": True, **payload, "diagnostic_digest": digest}


def present_worldbridge_quarantine_lifecycle(
    projection: Mapping[str, Any],
    *,
    artifact_import_diagnostic: Mapping[str, Any] | None = None,
    replay_persistence_diagnostic: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a bounded operator model; opaque epoch/token values are redacted."""
    source = _validate_source_projection(_copy_mapping(projection, "projection"))
    if not source["available"]:
        state = "unavailable"
        headline = "WorldBridge 生命周期证据不可用"
        caveat = "缺少可验证的同适配器证据，不可作为运行时控制依据。"
    else:
        state = source["state"]
        headline, caveat = _STATE_TEXT[state]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "scope": SCOPE,
        "read_only": True,
        "availability": "available" if source["available"] else "unavailable",
        "operator_state": state,
        "headline": headline,
        "caveat": caveat,
        "current_runtime_quarantined": source["current_runtime_quarantined"],
        "same_adapter_only": True,
        "evidence_summary": {
            "failure_lifecycle_values_redacted": True,
            "current_lifecycle_values_redacted": True,
            "disposal_recorded": source.get("disposal_recorded", False),
            "disposal_boundary": source.get("disposal_boundary"),
            "fresh_instance_boundary_observed": source.get("fresh_instance_boundary_observed", False),
        },
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "do_not_claim": list(DO_NOT_CLAIM),
        "artifact_import_diagnostic": _validate_artifact_import_diagnostic(
            artifact_import_diagnostic
        ),
        "replay_persistence_diagnostic": _validate_replay_persistence_diagnostic(
            replay_persistence_diagnostic
        ),
    }
    if not source["available"]:
        result["reason"] = source["reason"]
    return copy.deepcopy(result)


def validate_worldbridge_quarantine_operator_presentation(
    presentation: object,
) -> dict[str, Any]:
    """Validate the already bounded presentation consumed by adapters."""
    if not isinstance(presentation, Mapping):
        return {"valid": False, "errors": ["presentation_must_be_mapping"]}
    value = dict(presentation)
    errors: list[str] = []
    for key, expected in (
        ("schema_version", SCHEMA_VERSION),
        ("status", STATUS),
        ("scope", SCOPE),
    ):
        if value.get(key) != expected:
            errors.append(f"{key}_mismatch")
    availability = value.get("availability")
    if value.get("read_only") is not True or availability not in {"available", "unavailable"}:
        errors.append("read_only_or_availability_invalid")
    state = value.get("operator_state")
    if not isinstance(state, str) or (availability == "available" and state not in KNOWN_STATES) or (availability == "unavailable" and state != UNAVAILABLE_STATUS):
        errors.append("operator_state_invalid")
    if not isinstance(value.get("headline"), str) or not value.get("headline") or not isinstance(value.get("caveat"), str) or not value.get("caveat"):
        errors.append("bounded_text_missing")
    if value.get("same_adapter_only") is not True:
        errors.append("same_adapter_only_required")
    quarantined = value.get("current_runtime_quarantined")
    if (availability == "available" and not isinstance(quarantined, bool)) or (availability == "unavailable" and quarantined is not None):
        errors.append("current_runtime_quarantined_invalid")
    if availability == "unavailable":
        if not isinstance(value.get("reason"), str) or not value.get("reason"):
            errors.append("unavailable_reason_missing")
    elif "reason" in value:
        errors.append("available_reason_unexpected")
    expected_keys = {
        "schema_version", "status", "scope", "read_only", "availability", "operator_state", "headline", "caveat",
        "current_runtime_quarantined", "same_adapter_only", "evidence_summary", "negative_capabilities", "do_not_claim",
        "artifact_import_diagnostic",
        "replay_persistence_diagnostic",
    }
    if availability == "unavailable":
        expected_keys.add("reason")
    if set(value) - expected_keys:
        errors.append("presentation_shape_invalid")
    # E241/E242 callers may provide the pre-E494 shape; absence means no
    # artifact rejection was recorded, while new producers emit this key.
    if "artifact_import_diagnostic" not in value:
        value["artifact_import_diagnostic"] = None
    negative = value.get("negative_capabilities")
    if not isinstance(negative, Mapping):
        errors.append("negative_capabilities_missing")
    else:
        for key in NEGATIVE_CAPABILITIES:
            if negative.get(key) is not False:
                errors.append(f"negative_capabilities_{key}_overclaim")
    summary = value.get("evidence_summary")
    if not isinstance(summary, Mapping):
        errors.append("evidence_summary_missing")
    else:
        expected_summary_keys = {
            "failure_lifecycle_values_redacted", "current_lifecycle_values_redacted", "disposal_recorded",
            "disposal_boundary", "fresh_instance_boundary_observed",
        }
        if set(summary) != expected_summary_keys:
            errors.append("evidence_summary_shape_invalid")
        if summary.get("failure_lifecycle_values_redacted") is not True or summary.get("current_lifecycle_values_redacted") is not True:
            errors.append("opaque_lifecycle_values_not_redacted")
        if summary.get("disposal_recorded") not in {True, False} or summary.get("fresh_instance_boundary_observed") not in {True, False}:
            errors.append("evidence_summary_boolean_invalid")
        boundary = summary.get("disposal_boundary")
        if boundary is not None and not isinstance(boundary, str):
            errors.append("evidence_summary_boundary_invalid")
        if availability == "unavailable" and (summary.get("disposal_recorded") is not False or summary.get("disposal_boundary") is not None or summary.get("fresh_instance_boundary_observed") is not False):
            errors.append("unavailable_evidence_summary_overclaim")
    claims = value.get("do_not_claim")
    if not isinstance(claims, list) or set(claims) != set(DO_NOT_CLAIM):
        errors.append("do_not_claim_incomplete")
    try:
        _validate_artifact_import_diagnostic(value.get("artifact_import_diagnostic"))
    except ValueError as exc:
        errors.append(str(exc))
    try:
        _validate_replay_persistence_diagnostic(value.get("replay_persistence_diagnostic"))
    except ValueError as exc:
        errors.append(str(exc))
    return {"valid": not errors, "errors": errors}


def build_worldbridge_quarantine_operator_presentation_contract() -> dict[str, Any]:
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "authority_scope": "bounded_operator_presentation_of_e241_lifecycle_projection_only",
        "source_status": SOURCE_STATUS,
        "artifact_import_diagnostic_supported": True,
        "replay_persistence_diagnostic_supported": True,
        "opaque_lifecycle_values_exposed": False,
        "ui_authority": False,
        "operator_action_admitted": False,
        "negative_capabilities": {key: False for key in NEGATIVE_CAPABILITIES},
        "states": sorted(KNOWN_STATES),
        "do_not_claim": list(DO_NOT_CLAIM),
    }
    contract["contract_valid"] = validate_worldbridge_quarantine_operator_presentation_contract(contract)["valid"]
    return contract


def validate_worldbridge_quarantine_operator_presentation_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, Mapping):
        return {"valid": False, "errors": ["contract_must_be_mapping"]}
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if contract.get("status") != STATUS:
        errors.append("status_mismatch")
    if contract.get("read_only") is not True:
        errors.append("read_only_required")
    if contract.get("authority_scope") != "bounded_operator_presentation_of_e241_lifecycle_projection_only":
        errors.append("authority_scope_overclaim")
    if contract.get("source_status") != SOURCE_STATUS:
        errors.append("source_status_mismatch")
    if contract.get("artifact_import_diagnostic_supported") is not True:
        errors.append("artifact_import_diagnostic_support_missing")
    if contract.get("replay_persistence_diagnostic_supported") is not True:
        errors.append("replay_persistence_diagnostic_support_missing")
    if contract.get("opaque_lifecycle_values_exposed") is not False:
        errors.append("opaque_lifecycle_values_must_be_redacted")
    for key in ("ui_authority", "operator_action_admitted"):
        if contract.get(key) is not False:
            errors.append(f"{key}_overclaim")
    negative = contract.get("negative_capabilities")
    if not isinstance(negative, Mapping):
        errors.append("negative_capabilities_missing")
    else:
        for key in NEGATIVE_CAPABILITIES:
            if negative.get(key) is not False:
                errors.append(f"negative_capabilities_{key}_overclaim")
    if set(contract.get("states", [])) != set(KNOWN_STATES):
        errors.append("states_mismatch")
    if not isinstance(contract.get("do_not_claim"), list) or set(DO_NOT_CLAIM) - set(contract.get("do_not_claim", [])):
        errors.append("do_not_claim_incomplete")
    return {"valid": not errors, "errors": errors}


__all__ = [
    "DO_NOT_CLAIM",
    "KNOWN_STATES",
    "NEGATIVE_CAPABILITIES",
    "SCHEMA_VERSION",
    "STATUS",
    "build_worldbridge_quarantine_operator_presentation_contract",
    "present_worldbridge_quarantine_lifecycle",
    "validate_worldbridge_quarantine_operator_presentation",
    "validate_worldbridge_quarantine_operator_presentation_contract",
]
