# -*- coding: utf-8 -*-
"""Digest-only script transport boundary with explicit nonportability."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


SCHEMA_VERSION = 1
STATUS = "worldbridge_e567_script_portability_boundary"
SCOPE = "digest_and_project_relative_path_transport_only"
POLICY = "never_embed_or_execute_portable_script_source_v1"
PROOF_FIELDS = (
    "artifact_has_no_executable_blob",
    "source_bundle_digest_only",
    "source_available_rehydrated",
    "source_missing_quarantined",
    "source_digest_drift_quarantined",
    "manifest_trust_drift_quarantined",
    "arbitrary_external_source_quarantined",
    "all_quarantine_live_owners_preserved",
)
CLOSED_CAPABILITY_FIELDS = (
    "portable_sr_executable_script_checkpoint",
    "embedded_python_source_admitted",
    "embedded_bytecode_admitted",
    "embedded_pickle_admitted",
    "default_ready",
)
ALLOWED_SOURCE_KEYS = {"path", "sha256"}
FORBIDDEN_KEYS = {
    "code",
    "source_text",
    "source_code",
    "source_bytes",
    "source_blob",
    "raw_source",
    "module_source",
    "python_source",
    "bytecode",
    "pyc",
    "pickle",
    "pickled",
    "executable",
    "executable_blob",
    "blob",
    "base64_source",
}
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _witness_digest(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload["witness_digest"] = ""
    return _digest(payload)


def _scan_forbidden(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.strip().casefold()
            if normalized in FORBIDDEN_KEYS:
                findings.append(f"forbidden_executable_key:{path}.{key_text}")
            elif (
                normalized.startswith("source_")
                and normalized
                not in {"source_bundle", "source_path", "source_sha256"}
            ):
                findings.append(f"forbidden_source_payload_key:{path}.{key_text}")
            findings.extend(_scan_forbidden(child, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_scan_forbidden(child, f"{path}[{index}]"))
    return findings


def validate_digest_only_artifact(artifact: object) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(artifact, Mapping):
        return {"valid": False, "errors": ["artifact_not_mapping"]}
    errors.extend(_scan_forbidden(artifact))
    bundle = artifact.get("source_bundle")
    sources = bundle.get("sources") if isinstance(bundle, Mapping) else None
    if not isinstance(sources, list):
        errors.append("source_bundle_sources_missing")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, Mapping):
                errors.append(f"source_{index}_not_mapping")
                continue
            if set(source) != ALLOWED_SOURCE_KEYS:
                errors.append(f"source_{index}_keys_invalid")
            path = source.get("path")
            source_digest = source.get("sha256")
            if (
                not isinstance(path, str)
                or not path.casefold().startswith("scripts/")
                or not path.casefold().endswith(".py")
            ):
                errors.append(f"source_{index}_path_invalid")
            if (
                not isinstance(source_digest, str)
                or _DIGEST_RE.fullmatch(source_digest) is None
            ):
                errors.append(f"source_{index}_digest_invalid")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


def _result_projection(
    value: object,
    *,
    field: str,
    expected_decision: str,
    required_error: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {
            "valid": False,
            "errors": [f"{field}_not_mapping"],
            "decision": None,
            "live_owner_preserved": None,
        }
    decision = value.get("decision")
    if decision != expected_decision:
        errors.append(f"{field}_decision_mismatch")
    if expected_decision == "rehydrated" and value.get("admitted") is not True:
        errors.append(f"{field}_not_admitted")
    if expected_decision == "quarantined":
        if value.get("admitted") is not False:
            errors.append(f"{field}_admitted_overclaim")
        if value.get("live_owner_preserved") is not True:
            errors.append(f"{field}_live_owner_not_preserved")
        rendered = "\n".join(str(item) for item in value.get("errors", ()))
        if required_error is not None and required_error not in rendered:
            errors.append(f"{field}_reason_missing")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
        "live_owner_preserved": value.get("live_owner_preserved"),
    }


def build_worldbridge_e567_script_portability_boundary(
    *,
    artifact: Mapping[str, Any],
    source_available_result: Mapping[str, Any],
    source_missing_result: Mapping[str, Any],
    source_digest_drift_result: Mapping[str, Any],
    manifest_trust_drift_result: Mapping[str, Any],
    arbitrary_external_source_result: Mapping[str, Any],
) -> dict[str, Any]:
    artifact_validation = validate_digest_only_artifact(artifact)
    results = {
        "source_available": _result_projection(
            source_available_result,
            field="source_available",
            expected_decision="rehydrated",
        ),
        "source_missing": _result_projection(
            source_missing_result,
            field="source_missing",
            expected_decision="quarantined",
            required_error="source_bundle_source_missing",
        ),
        "source_digest_drift": _result_projection(
            source_digest_drift_result,
            field="source_digest_drift",
            expected_decision="quarantined",
            required_error="source_bundle_source_digest_mismatch",
        ),
        "manifest_trust_drift": _result_projection(
            manifest_trust_drift_result,
            field="manifest_trust_drift",
            expected_decision="quarantined",
            required_error="source_bundle_source_untrusted",
        ),
        "arbitrary_external_source": _result_projection(
            arbitrary_external_source_result,
            field="arbitrary_external_source",
            expected_decision="quarantined",
        ),
    }
    errors = list(artifact_validation["errors"])
    for result in results.values():
        errors.extend(result["errors"])
    proof = {
        "artifact_has_no_executable_blob": (
            artifact_validation["valid"] is True
        ),
        "source_bundle_digest_only": (
            artifact_validation["valid"] is True
        ),
        "source_available_rehydrated": results["source_available"]["valid"],
        "source_missing_quarantined": results["source_missing"]["valid"],
        "source_digest_drift_quarantined": results[
            "source_digest_drift"
        ]["valid"],
        "manifest_trust_drift_quarantined": results[
            "manifest_trust_drift"
        ]["valid"],
        "arbitrary_external_source_quarantined": results[
            "arbitrary_external_source"
        ]["valid"],
        "all_quarantine_live_owners_preserved": all(
            results[field]["live_owner_preserved"] is True
            for field in (
                "source_missing",
                "source_digest_drift",
                "manifest_trust_drift",
                "arbitrary_external_source",
            )
        ),
    }
    for field in PROOF_FIELDS:
        if proof[field] is not True:
            errors.append(f"{field}_not_proven")
    if errors:
        raise ValueError(
            "E567 script portability boundary rejected: "
            + ",".join(dict.fromkeys(errors))
        )
    witness: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "read_only": True,
        "scope": SCOPE,
        "policy": POLICY,
        "artifact_digest": artifact.get("artifact_digest"),
        "artifact": copy.deepcopy(dict(artifact)),
        "source_results": copy.deepcopy(results),
        **proof,
        "executable_source_portability_closed": True,
        "digest_only_source_transport": True,
        **{field: False for field in CLOSED_CAPABILITY_FIELDS},
        "witness_digest": "",
    }
    witness["witness_digest"] = _witness_digest(witness)
    return witness


def validate_worldbridge_e567_script_portability_boundary(
    value: object,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return {"valid": False, "errors": ["witness_not_mapping"]}
    required = {
        "schema_version",
        "status",
        "read_only",
        "scope",
        "policy",
        "artifact_digest",
        "artifact",
        "source_results",
        *PROOF_FIELDS,
        "executable_source_portability_closed",
        "digest_only_source_transport",
        *CLOSED_CAPABILITY_FIELDS,
        "witness_digest",
    }
    if set(value) != required:
        errors.append("witness_keys_invalid")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if value.get("status") != STATUS:
        errors.append("status_mismatch")
    if value.get("scope") != SCOPE:
        errors.append("scope_mismatch")
    if value.get("policy") != POLICY:
        errors.append("policy_mismatch")
    artifact_validation = validate_digest_only_artifact(value.get("artifact"))
    if artifact_validation["valid"] is not True:
        errors.extend(artifact_validation["errors"])
    artifact = value.get("artifact")
    if not isinstance(artifact, Mapping) or value.get(
        "artifact_digest"
    ) != artifact.get("artifact_digest"):
        errors.append("artifact_digest_mismatch")
    results = value.get("source_results")
    if not isinstance(results, Mapping):
        errors.append("source_results_invalid")
    else:
        expected_fields = {
            "source_available",
            "source_missing",
            "source_digest_drift",
            "manifest_trust_drift",
            "arbitrary_external_source",
        }
        if set(results) != expected_fields:
            errors.append("source_results_keys_invalid")
        for field in expected_fields:
            result = results.get(field)
            if not isinstance(result, Mapping) or result.get("valid") is not True:
                errors.append(f"{field}_not_valid")
        if not all(
            results.get(field, {}).get("live_owner_preserved") is True
            for field in (
                "source_missing",
                "source_digest_drift",
                "manifest_trust_drift",
                "arbitrary_external_source",
            )
        ):
            errors.append("quarantine_live_owner_not_preserved")
    for field in PROOF_FIELDS:
        if value.get(field) is not True:
            errors.append(f"{field}_not_proven")
    if value.get("executable_source_portability_closed") is not True:
        errors.append("executable_source_portability_not_closed")
    if value.get("digest_only_source_transport") is not True:
        errors.append("digest_only_source_transport_not_proven")
    for field in CLOSED_CAPABILITY_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field}_overclaim")
    digest = value.get("witness_digest")
    if (
        not isinstance(digest, str)
        or _DIGEST_RE.fullmatch(digest) is None
        or digest != _witness_digest(value)
    ):
        errors.append("witness_digest_mismatch")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors))}


__all__ = [
    "CLOSED_CAPABILITY_FIELDS",
    "POLICY",
    "PROOF_FIELDS",
    "SCHEMA_VERSION",
    "SCOPE",
    "STATUS",
    "build_worldbridge_e567_script_portability_boundary",
    "validate_digest_only_artifact",
    "validate_worldbridge_e567_script_portability_boundary",
]
