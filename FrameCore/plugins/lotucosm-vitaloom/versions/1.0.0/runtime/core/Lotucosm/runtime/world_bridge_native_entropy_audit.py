# -*- coding: utf-8 -*-
"""Static capability audit for the optional SR2D native kernels.

This is deliberately a source audit, not a claim that arbitrary extension
dependencies are deterministic.  The shipped C++/Rust kernels are inspected
for known entropy and clock APIs; imported native/third-party code remains an
opaque boundary until it exposes a separately verifiable contract.
"""
from __future__ import annotations

import hashlib
import importlib
import re
import shutil
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
_FORBIDDEN = re.compile(
    r"(?:\b(?:rand|random|srand|uuid|secrets|chrono|time|clock|thread|sleep)\b|"
    r"std::(?:random|chrono)|getrandom|SystemTime|Instant::now)"
)
_SOURCE_FILES = (
    "native/sr2d_cpp/src/kernel.cpp",
    "native/sr2d_cpp/src/bindings.cpp",
    "native/sr2d_cpp/src/kernel.hpp",
    "native/sr2d_kernel/src/lib.rs",
    "native/sr2d_kernel/Cargo.toml",
    "native/sr2d_cpp/CMakeLists.txt",
)
NATIVE_ADMISSION_EVIDENCE_SCHEMA_VERSION = 1
NATIVE_ADMISSION_EVIDENCE_STATUS = "sr2d_native_admission_evidence"
NATIVE_ADMISSION_EVIDENCE_KEYS = {
    "schema_version",
    "status",
    "native_available",
    "provenance",
    "parity",
    "parity_proven",
    "benchmarks",
    "benchmark_proven",
    "native_admitted",
    "fallback",
    "digest",
}
_EXPECTED_NATIVE_SCENARIOS = {
    "default_bruteforce": ("default", "bruteforce"),
    "dense_spatial_hash": ("dense", "spatial_hash"),
    "sparse_spatial_hash": ("sparse", "spatial_hash"),
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "native" / "sr2d_kernel").is_dir():
            return parent
    raise RuntimeError("VitaLoom repository root is not discoverable")


def _canonical_digest(value: Mapping[str, Any], *, digest_field: str) -> str:
    payload = dict(value)
    payload[digest_field] = ""
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _parity_rows_proven(rows: list[Mapping[str, Any]]) -> bool:
    if len(rows) != len(_EXPECTED_NATIVE_SCENARIOS):
        return False
    by_name = {str(row.get("name")): row for row in rows}
    if set(by_name) != set(_EXPECTED_NATIVE_SCENARIOS):
        return False
    for name, (variant, broadphase) in _EXPECTED_NATIVE_SCENARIOS.items():
        row = by_name[name]
        tolerance = row.get("tolerance")
        if (
            row.get("variant") != variant
            or row.get("broadphase") != broadphase
            or not isinstance(row.get("entities"), int)
            or row.get("entities", 0) <= 0
            or row.get("ticks_compared") != 120
            or not isinstance(tolerance, (int, float))
            or not 0.0 < float(tolerance) <= 1e-4
            or row.get("maximum_delta") != 0.0
            or row.get("first_mismatch_tick") is not None
            or row.get("first_mismatch_delta") is not None
            or row.get("parity") is not True
        ):
            return False
    return True


def _benchmark_rows_proven(rows: list[Mapping[str, Any]]) -> bool:
    if len(rows) != len(_EXPECTED_NATIVE_SCENARIOS):
        return False
    by_name = {str(row.get("name")): row for row in rows}
    if set(by_name) != set(_EXPECTED_NATIVE_SCENARIOS):
        return False
    for name, (variant, broadphase) in _EXPECTED_NATIVE_SCENARIOS.items():
        row = by_name[name]
        speedup = row.get("speedup")
        if (
            row.get("variant") != variant
            or row.get("broadphase") != broadphase
            or not isinstance(speedup, (int, float))
            or float(speedup) <= 1.0
            or row.get("first_position_close") is not True
        ):
            return False
    return True


def build_native_admission_evidence(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize a real native admission run into detached, stable evidence."""
    if not isinstance(report, Mapping):
        raise TypeError("native admission report must be a mapping")
    provenance = report.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    parity: list[dict[str, Any]] = []
    raw_parity = report.get("parity")
    for item in raw_parity if isinstance(raw_parity, list) else []:
        if not isinstance(item, Mapping):
            continue
        parity.append(
            {
                "name": str(item.get("name")),
                "variant": str(item.get("variant")),
                "broadphase": str(item.get("broadphase")),
                "entities": item.get("entities"),
                "ticks_compared": item.get("ticks_compared"),
                "tolerance": item.get("tolerance"),
                "maximum_delta": item.get("maximum_delta"),
                "first_mismatch_tick": item.get("first_mismatch_tick"),
                "first_mismatch_delta": item.get("first_mismatch_delta"),
                "parity": item.get("parity"),
            }
        )
    benchmarks: list[dict[str, Any]] = []
    raw_benchmarks = report.get("benchmarks")
    for item in raw_benchmarks if isinstance(raw_benchmarks, list) else []:
        if not isinstance(item, Mapping):
            continue
        python = item.get("python")
        native = item.get("native")
        python = python if isinstance(python, Mapping) else {}
        native = native if isinstance(native, Mapping) else {}
        benchmarks.append(
            {
                "name": str(item.get("name")),
                "variant": str(python.get("variant")),
                "broadphase": str(python.get("broadphase")),
                "python_adapter": str(python.get("adapter")),
                "native_adapter": str(native.get("adapter")),
                "entities": python.get("entities"),
                "ticks": python.get("ticks"),
                "repeats": python.get("repeats"),
                "speedup": item.get("speedup"),
                "first_position_close": item.get("first_position_close"),
            }
        )
    provenance_proven = (
        provenance.get("available") is True
        and provenance.get("abi_version") == 1
        and provenance.get("entropy_contract") == "none"
        and provenance.get("kernel_callable") is True
        and isinstance(provenance.get("artifact_sha256"), str)
        and _SHA256_RE.fullmatch(str(provenance.get("artifact_sha256"))) is not None
    )
    parity_proven = _parity_rows_proven(parity)
    benchmark_proven = _benchmark_rows_proven(benchmarks)
    native_admitted = (
        report.get("native_available") is True
        and provenance_proven
        and parity_proven
        and benchmark_proven
        and report.get("native_admitted") is True
    )
    evidence: dict[str, Any] = {
        "schema_version": NATIVE_ADMISSION_EVIDENCE_SCHEMA_VERSION,
        "status": NATIVE_ADMISSION_EVIDENCE_STATUS,
        "native_available": report.get("native_available") is True,
        "provenance": {
            "available": provenance.get("available") is True,
            "module_name": provenance.get("module_name"),
            "artifact_sha256": provenance.get("artifact_sha256"),
            "abi_version": provenance.get("abi_version"),
            "entropy_contract": provenance.get("entropy_contract"),
            "kernel_callable": provenance.get("kernel_callable") is True,
        },
        "parity": parity,
        "parity_proven": parity_proven,
        "benchmarks": benchmarks,
        "benchmark_proven": benchmark_proven,
        "native_admitted": native_admitted,
        "fallback": report.get("fallback"),
        "digest": "",
    }
    evidence["digest"] = _canonical_digest(
        evidence,
        digest_field="digest",
    )
    return evidence


def validate_native_admission_evidence(
    evidence: object,
) -> dict[str, Any]:
    """Validate detached native parity/benchmark admission evidence."""
    if not isinstance(evidence, Mapping):
        return {
            "valid": False,
            "errors": ["native_admission_evidence_not_mapping"],
        }
    errors: list[str] = []
    if set(evidence) != NATIVE_ADMISSION_EVIDENCE_KEYS:
        errors.append("native_admission_evidence_keys_invalid")
    if evidence.get("schema_version") != NATIVE_ADMISSION_EVIDENCE_SCHEMA_VERSION:
        errors.append("native_admission_evidence_schema_invalid")
    if evidence.get("status") != NATIVE_ADMISSION_EVIDENCE_STATUS:
        errors.append("native_admission_evidence_status_invalid")
    if evidence.get("native_available") is not True:
        errors.append("native_admission_evidence_unavailable")
    provenance = evidence.get("provenance")
    if not isinstance(provenance, Mapping):
        errors.append("native_admission_evidence_provenance_invalid")
        provenance = {}
    if (
        provenance.get("available") is not True
        or not isinstance(provenance.get("module_name"), str)
        or not provenance.get("module_name")
        or provenance.get("abi_version") != 1
        or provenance.get("entropy_contract") != "none"
        or provenance.get("kernel_callable") is not True
        or not isinstance(provenance.get("artifact_sha256"), str)
        or _SHA256_RE.fullmatch(str(provenance.get("artifact_sha256"))) is None
    ):
        errors.append("native_admission_evidence_provenance_invalid")
    parity = evidence.get("parity")
    parity = parity if isinstance(parity, list) else []
    if not _parity_rows_proven(parity):
        errors.append("native_admission_evidence_parity_invalid")
    benchmarks = evidence.get("benchmarks")
    benchmarks = benchmarks if isinstance(benchmarks, list) else []
    if not _benchmark_rows_proven(benchmarks):
        errors.append("native_admission_evidence_benchmark_invalid")
    if evidence.get("parity_proven") is not True:
        errors.append("native_admission_evidence_parity_not_proven")
    if evidence.get("benchmark_proven") is not True:
        errors.append("native_admission_evidence_benchmark_not_proven")
    if evidence.get("native_admitted") is not True:
        errors.append("native_admission_evidence_not_admitted")
    if not isinstance(evidence.get("fallback"), str) or not evidence.get("fallback"):
        errors.append("native_admission_evidence_fallback_invalid")
    try:
        expected_digest = _canonical_digest(
            evidence,
            digest_field="digest",
        )
    except (TypeError, ValueError, OverflowError):
        expected_digest = None
        errors.append("native_admission_evidence_not_canonical")
    if (
        not isinstance(evidence.get("digest"), str)
        or _SHA256_RE.fullmatch(str(evidence.get("digest"))) is None
        or evidence.get("digest") != expected_digest
    ):
        errors.append("native_admission_evidence_digest_mismatch")
    return {"valid": not errors, "errors": sorted(set(errors))}


def build_native_entropy_audit() -> dict[str, Any]:
    """Return a deterministic, read-only report for the shipped native surface."""
    root = _repository_root()
    files: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for relative in _SOURCE_FILES:
        path = root / relative
        if not path.is_file():
            files.append({"path": relative, "status": "missing"})
            findings.append({"path": relative, "kind": "missing_source"})
            continue
        source = path.read_text(encoding="utf-8")
        matches = [match.group(0) for match in _FORBIDDEN.finditer(source)]
        files.append(
            {
                "path": relative,
                "status": "audited",
                "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "entropy_tokens": sorted(set(matches)),
            }
        )
        if matches:
            findings.append(
                {
                    "path": relative,
                    "kind": "known_entropy_or_clock_token",
                    "tokens": ",".join(sorted(set(matches))),
                }
            )
    source_closed = not findings and all(item["status"] == "audited" for item in files)
    extension_probes = [_probe_extension(name) for name in (
        "_vitalloom_sr2d_cpp", "_vitalloom_sr2d_rust", "_vitalloom_sr2d"
    )]
    available_extensions = [
        item for item in extension_probes
        if item["available"] and item["has_kernel"]
    ]
    if not available_extensions:
        boundary_classification = "optional_native_unavailable"
    elif all(item["entropy_contract"] == "none" for item in available_extensions):
        boundary_classification = "reachable_contractually_no_entropy"
    else:
        boundary_classification = "reachable_but_quarantined"
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "vitalloom_sr2d_native_source_entropy",
        "source_files": files,
        "findings": findings,
        "extension_probes": extension_probes,
        "boundary_classification": boundary_classification,
        "reachable_extension_count": len(available_extensions),
        "shipped_kernel_source_has_known_entropy": not source_closed,
        "shipped_kernel_source_audited": source_closed,
        "opaque_dependency_boundary_closed": False,
        "native_entropy_boundary_closed": False,
        "replay_admitted": False,
        "default_ready": False,
    }


def build_native_entropy_boundary_receipt(
    native_admission_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a conservative build/import/parity boundary receipt.

    Source inspection alone never admits a native backend.  Admission requires
    a real imported kernel, the declared no-entropy contract, and a completed
    build/parity witness; unavailable toolchains remain explicitly quarantined.
    """
    audit = build_native_entropy_audit()
    tools = {
        name: shutil.which(name) is not None
        for name in ("cl", "cmake", "cargo", "maturin")
    }
    imported = [
        item for item in audit["extension_probes"]
        if item.get("available") and item.get("has_kernel")
    ]
    contract_ok = bool(imported) and all(
        item.get("entropy_contract") == "none" for item in imported
    )
    evidence_validation = (
        validate_native_admission_evidence(native_admission_evidence)
        if native_admission_evidence is not None
        else {
            "valid": False,
            "errors": ["native_admission_evidence_missing"],
        }
    )
    source_probe: Mapping[str, Any] | None = None
    if isinstance(native_admission_evidence, Mapping):
        provenance = native_admission_evidence.get("provenance")
        if isinstance(provenance, Mapping):
            source_probe = next(
                (
                    probe
                    for probe in audit["extension_probes"]
                    if probe.get("available") is True
                    and probe.get("has_kernel") is True
                    and probe.get("module") == provenance.get("module_name")
                    and probe.get("artifact_sha256")
                    == provenance.get("artifact_sha256")
                    and probe.get("abi_version") == provenance.get("abi_version")
                    and probe.get("entropy_contract")
                    == provenance.get("entropy_contract")
                ),
                None,
            )
    evidence_source_bound = source_probe is not None
    evidence_proven = (
        evidence_validation == {"valid": True, "errors": []}
        and evidence_source_bound
        and isinstance(native_admission_evidence, Mapping)
        and native_admission_evidence.get("native_admitted") is True
    )
    reasons: list[str] = []
    if not audit["shipped_kernel_source_audited"]:
        reasons.append("source_audit_incomplete")
    if not imported:
        reasons.append("extension_import_unavailable")
    if not contract_ok:
        reasons.append("entropy_contract_unproven")
    if native_admission_evidence is None:
        if not all(tools.values()):
            reasons.append("native_toolchain_unavailable")
        reasons.append("native_admission_evidence_missing")
    else:
        if evidence_validation != {"valid": True, "errors": []}:
            reasons.append("native_admission_evidence_invalid")
        if not evidence_source_bound:
            reasons.append("native_admission_evidence_source_mismatch")
        if not evidence_proven:
            reasons.append("native_admission_not_proven")
    admitted = not reasons and evidence_proven
    payload: dict[str, Any] = {
        "schema_version": 1,
        "boundary": "native_extension_entropy",
        "status": "admitted" if admitted else "quarantined",
        "source_audit_id": audit["audit_id"],
        "source_audited": bool(audit["shipped_kernel_source_audited"]),
        "extension_import_verified": bool(imported),
        "build_verified": bool(evidence_source_bound and evidence_proven),
        "parity_verified": bool(
            evidence_source_bound
            and isinstance(native_admission_evidence, Mapping)
            and native_admission_evidence.get("parity_proven") is True
        ),
        "entropy_contract_verified": contract_ok,
        "toolchain": tools,
        "reachable_extension_count": len(imported),
        "reasons": sorted(set(reasons)),
        "opaque_dependency_boundary_closed": False,
        "native_entropy_boundary_closed": admitted,
        "replay_admitted": False,
        "default_ready": False,
    }
    payload["digest"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def validate_native_entropy_boundary_receipt(receipt: object) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        return {"valid": False, "errors": ["native_boundary_receipt_not_mapping"]}
    required = {
        "schema_version", "boundary", "status", "source_audit_id", "source_audited",
        "extension_import_verified", "build_verified", "parity_verified",
        "entropy_contract_verified", "toolchain", "reachable_extension_count",
        "reasons", "opaque_dependency_boundary_closed", "native_entropy_boundary_closed",
        "replay_admitted", "default_ready", "digest",
    }
    if set(receipt) != required or receipt.get("schema_version") != 1:
        return {"valid": False, "errors": ["native_boundary_receipt_schema_invalid"]}
    errors: list[str] = []
    if receipt.get("boundary") != "native_extension_entropy":
        errors.append("native_boundary_receipt_boundary_invalid")
    if receipt.get("status") not in {"admitted", "quarantined"}:
        errors.append("native_boundary_receipt_status_invalid")
    if not isinstance(receipt.get("toolchain"), dict) or not isinstance(receipt.get("reasons"), list):
        errors.append("native_boundary_receipt_payload_invalid")
    for field in (
        "source_audited", "extension_import_verified", "build_verified", "parity_verified",
        "entropy_contract_verified", "opaque_dependency_boundary_closed",
        "native_entropy_boundary_closed", "replay_admitted", "default_ready",
    ):
        if not isinstance(receipt.get(field), bool):
            errors.append(f"native_boundary_receipt_{field}_invalid")
    if receipt.get("status") == "admitted" and not all(
        receipt.get(field) is True
        for field in (
            "source_audited", "extension_import_verified", "build_verified",
            "parity_verified", "entropy_contract_verified",
        )
    ):
        errors.append("native_boundary_receipt_overclaims_admission")
    canonical = dict(receipt)
    digest = canonical.pop("digest", None)
    expected = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if digest != expected:
        errors.append("native_boundary_receipt_digest_mismatch")
    return {"valid": not errors, "errors": sorted(set(errors))}


def build_native_backend_selection_evidence(
    backend_capability: Mapping[str, Any],
    *,
    requested_backend: str = "auto",
    native_admission_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind the selected SR2D backend to the current native boundary receipt."""
    if not isinstance(backend_capability, Mapping):
        raise TypeError("backend capability must be a mapping")
    backend_id = str(backend_capability.get("backend_id", "unavailable"))
    requested = str(requested_backend or "auto").strip().lower()
    if requested not in {"auto", "python", "cpp", "rust"}:
        raise ValueError("unsupported SR2D backend request: " + requested)
    native_selected = backend_id in {"cpp", "rust"}
    receipt = build_native_entropy_boundary_receipt(
        native_admission_evidence=native_admission_evidence,
    )
    reasons: list[str] = []
    if native_selected:
        if receipt["status"] != "admitted":
            reasons.append("native_boundary_not_admitted")
        if backend_capability.get("abi_version_required") != backend_capability.get(
            "abi_version_exported"
        ):
            reasons.append("selected_backend_abi_mismatch")
        if backend_capability.get("artifact_provenance") != "hashed":
            reasons.append("selected_backend_artifact_provenance_missing")
        if not backend_capability.get("artifact_sha256"):
            reasons.append("selected_backend_artifact_digest_missing")
    else:
        reasons.append("native_backend_not_selected")
    return {
        "schema_version": 1,
        "requested_backend_id": requested,
        "selected_backend_id": backend_id,
        "selected_module_name": backend_capability.get("module_name"),
        "selected_artifact_sha256": backend_capability.get("artifact_sha256"),
        "selected_artifact_provenance": backend_capability.get("artifact_provenance"),
        "selected_abi_version_required": backend_capability.get("abi_version_required"),
        "selected_abi_version_exported": backend_capability.get("abi_version_exported"),
        "native_receipt_digest": receipt["digest"],
        "native_receipt_status": receipt["status"],
        "status": "admitted" if native_selected and not reasons else (
            "reference_python" if not native_selected else "quarantined"
        ),
        "reasons": sorted(set(reasons)),
    }


def validate_native_backend_selection_evidence(
    evidence: object,
    backend_capability: Mapping[str, Any],
    *,
    requested_backend: str = "auto",
    native_admission_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or not isinstance(backend_capability, Mapping):
        return {"valid": False, "errors": ["backend_selection_evidence_not_mapping"]}
    current = build_native_backend_selection_evidence(
        backend_capability,
        requested_backend=requested_backend,
        native_admission_evidence=native_admission_evidence,
    )
    if dict(evidence) != current:
        return {"valid": False, "errors": ["backend_selection_evidence_mismatch"]}
    return {"valid": True, "errors": []}


def _probe_extension(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {
            "module": name,
            "available": False,
            "has_kernel": False,
            "entropy_contract": "unavailable",
            "error_type": type(exc).__name__,
        }
    has_kernel = callable(getattr(module, "step_pvaec_circles", None))
    contract = getattr(module, "VITALLOOM_SR2D_ENTROPY_CONTRACT", None)
    module_path = getattr(module, "__file__", None)
    artifact_sha256 = None
    if isinstance(module_path, str):
        try:
            artifact_sha256 = hashlib.sha256(
                Path(module_path).read_bytes()
            ).hexdigest()
        except OSError:
            artifact_sha256 = None
    return {
        "module": name,
        "module_name": name,
        "available": True,
        "has_kernel": has_kernel,
        "entropy_contract": str(contract) if contract is not None else "missing",
        "abi_version": getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None),
        "artifact_sha256": artifact_sha256,
    }


__all__ = [
    "SCHEMA_VERSION",
    "NATIVE_ADMISSION_EVIDENCE_SCHEMA_VERSION",
    "NATIVE_ADMISSION_EVIDENCE_STATUS",
    "build_native_entropy_audit",
    "build_native_entropy_boundary_receipt",
    "build_native_admission_evidence",
    "build_native_backend_selection_evidence",
    "validate_native_admission_evidence",
    "validate_native_backend_selection_evidence",
    "validate_native_entropy_boundary_receipt",
]
