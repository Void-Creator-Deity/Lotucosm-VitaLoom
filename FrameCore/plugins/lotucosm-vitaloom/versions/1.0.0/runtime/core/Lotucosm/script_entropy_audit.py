"""Static entropy audit for dynamically loaded simulation scripts.

The audit is deliberately conservative: it reports direct process-global or
OS entropy access, while allowing scripts to consume the host-injected
``ScriptBase`` owner.  It does not execute untrusted source.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

_MODULES = {
    "random": "python_process_global_random",
    "numpy.random": "numpy_legacy_global_randomstate",
    "np.random": "numpy_legacy_global_randomstate",
    "secrets": "os_entropy",
    "uuid": "os_entropy",
}
_DYNAMIC_IMPORTS = {"__import__", "builtins.__import__", "importlib.import_module"}
_DYNAMIC_EXECUTION = {"eval", "exec", "builtins.eval", "builtins.exec"}
_LOCAL_RNG_CONSTRUCTORS = {
    "random.Random",
    "numpy.random.Generator",
    "numpy.random.RandomState",
    "numpy.random.default_rng",
    "np.random.Generator",
    "np.random.RandomState",
    "np.random.default_rng",
}
_OWNER_DRAW_METHODS = {
    "random", "uniform", "randrange", "randint", "gauss", "normal",
    "choice", "choices", "sample", "integers", "random_sample",
}


def _entropy_authority(dotted: str) -> str | None:
    for module, authority in _MODULES.items():
        if dotted == module or dotted.startswith(module + "."):
            return authority
    return None


def _dotted_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value, aliases)
        return f"{prefix}.{node.attr}" if prefix else None
    return None


def audit_script_entropy(source: str, *, path: str = "") -> dict[str, Any]:
    """Return a stable, JSON-safe report without importing or executing source."""
    findings: list[dict[str, Any]] = []
    try:
        tree = ast.parse(source, filename=path or "<script>")
    except SyntaxError as exc:
        return {
            "schema_version": 1,
            "path": str(path),
            "parseable": False,
            "deterministic_ready": False,
            "findings": [{"kind": "syntax_error", "line": int(exc.lineno or 0)}],
        }

    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                bound_name = item.asname or item.name.split(".")[0]
                bound_value = item.name if item.asname else item.name.split(".")[0]
                aliases[bound_name] = bound_value
                authority = _entropy_authority(item.name)
                if authority is not None:
                    findings.append({
                        "kind": "global_entropy_import",
                        "authority": authority,
                        "line": int(node.lineno),
                        "symbol": item.name,
                    })
        elif isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            for item in node.names:
                imported_path = f"{module}.{item.name}"
                aliases[item.asname or item.name] = imported_path
                authority = _entropy_authority(module) or _entropy_authority(imported_path)
                if authority is not None:
                    findings.append({
                        "kind": "global_entropy_import",
                        "authority": authority,
                        "line": int(node.lineno),
                        "symbol": imported_path,
                    })
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
            assigned = _dotted_name(node.value, aliases)
            if assigned:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases[target.id] = assigned
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, (ast.Name, ast.Attribute)):
            assigned = _dotted_name(node.value, aliases)
            if assigned and isinstance(node.target, ast.Name):
                aliases[node.target.id] = assigned

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            dotted = _dotted_name(node.func, aliases)
            if dotted in _LOCAL_RNG_CONSTRUCTORS:
                findings.append({
                    "kind": "unregistered_local_rng_constructor",
                    "authority": "dynamic_script_plugin_entropy",
                    "line": int(node.lineno),
                    "symbol": dotted,
                })
                continue
            if dotted:
                segments = dotted.split(".")
                if (
                    len(segments) >= 2
                    and segments[-1] in _OWNER_DRAW_METHODS
                    and any("rng" in segment.lower() for segment in segments[:-1])
                ):
                    findings.append({
                        "kind": "untracked_owner_consumption",
                        "authority": "dynamic_script_plugin_entropy",
                        "line": int(node.lineno),
                        "symbol": dotted,
                    })
                    continue
            authority = _entropy_authority(dotted or "")
            if authority is not None:
                findings.append({
                    "kind": "global_entropy_call",
                    "authority": authority,
                    "line": int(node.lineno),
                    "symbol": dotted,
                })
                continue
            if dotted in _DYNAMIC_IMPORTS:
                findings.append({
                    "kind": "opaque_dynamic_import",
                    "authority": "unknown_dynamic_module",
                    "line": int(node.lineno),
                    "symbol": dotted,
                })
                continue
            if dotted in _DYNAMIC_EXECUTION:
                findings.append({
                    "kind": "opaque_dynamic_execution",
                    "authority": "unknown_dynamic_code",
                    "line": int(node.lineno),
                    "symbol": dotted,
                })
                continue
            if dotted in {"getattr", "builtins.getattr"} and len(node.args) >= 2:
                target = _dotted_name(node.args[0], aliases) if isinstance(node.args[0], (ast.Name, ast.Attribute)) else None
                attribute = node.args[1].value if isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str) else ""
                if target and _entropy_authority(f"{target}.{attribute}"):
                    findings.append({
                        "kind": "opaque_reflective_entropy_access",
                        "authority": _entropy_authority(f"{target}.{attribute}"),
                        "line": int(node.lineno),
                        "symbol": f"{target}.{attribute}",
                    })

    deduped = []
    seen = set()
    for finding in findings:
        key = tuple(sorted(finding.items()))
        if key not in seen:
            seen.add(key)
            deduped.append(finding)
    return {
        "schema_version": 1,
        "path": str(path),
        "parseable": True,
        "deterministic_ready": not deduped,
        "findings": deduped,
    }


def audit_script_file(path: str | Path) -> dict[str, Any]:
    """Audit one source file, reporting unreadable files as non-admissible."""
    source_path = Path(path)
    try:
        source_bytes = source_path.read_bytes()
        source = source_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return {
            "schema_version": 1,
            "path": str(source_path),
            "parseable": False,
            "deterministic_ready": False,
            "findings": [{"kind": "read_error", "error": type(exc).__name__}],
        }
    audit = audit_script_entropy(source, path=str(source_path))
    audit["source_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    return audit


def build_script_entropy_receipt(
    audit: dict[str, Any],
    *,
    owner_family: str,
    runtime_epoch: str,
    source_sha256: str | None = None,
    owner_stream_name: str | None = None,
    owner_registry_digest: str | None = None,
) -> dict[str, Any]:
    """Seal an admitted script audit with source and owner provenance."""
    if not isinstance(audit, dict):
        raise TypeError("audit must be a mapping")
    path = str(audit.get("path") or "")
    if not path:
        raise ValueError("script audit path is required")
    if not str(owner_family).strip() or not str(runtime_epoch).strip():
        raise ValueError("script owner family and runtime epoch are required")
    if (owner_stream_name is None) != (owner_registry_digest is None):
        raise ValueError("owner stream name and registry digest must be provided together")
    if owner_stream_name is not None:
        if not str(owner_stream_name).strip():
            raise ValueError("owner stream name is required")
        digest = str(owner_registry_digest).strip().lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("owner registry digest is invalid")
    if source_sha256 is None:
        try:
            source_digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except (OSError, UnicodeError) as exc:
            raise ValueError("script source is not readable") from exc
    else:
        source_digest = str(source_sha256).strip().lower()
        if len(source_digest) != 64 or any(char not in "0123456789abcdef" for char in source_digest):
            raise ValueError("script source digest is invalid")
    audited_digest = audit.get("source_sha256")
    if audited_digest is not None and str(audited_digest).lower() != source_digest:
        raise ValueError("script audit source digest mismatch")
    audit_digest = hashlib.sha256(
        json.dumps(audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if audit.get("deterministic_ready") is not True:
        raise ValueError("script entropy audit is not deterministic-ready")
    receipt = {
        "schema_version": 1,
        "path": path,
        "source_sha256": source_digest,
        "audit_sha256": audit_digest,
        "owner_family": str(owner_family).strip(),
        "runtime_epoch": str(runtime_epoch).strip(),
        "deterministic_ready": True,
    }
    if owner_stream_name is not None:
        receipt["owner_stream_name"] = str(owner_stream_name).strip()
        receipt["owner_registry_digest"] = str(owner_registry_digest).strip().lower()
    return receipt


def diagnose_script_entropy_admission(
    audits: object,
    receipts: object,
    *,
    owner_family: str | None = None,
    runtime_epoch: str | None = None,
    owner_stream_name: str | None = None,
    owner_registry_digest: str | None = None,
) -> dict[str, Any]:
    """Classify script evidence gaps without admitting opaque or stale owners."""
    if not isinstance(audits, list) or not isinstance(receipts, list):
        return {"admitted": False, "reasons": ["legacy_audit"]}
    reasons: list[str] = []
    if not audits:
        return {"admitted": True, "reasons": []}
    if not receipts:
        reasons = ["receipt_missing"]
        if any(
            not isinstance(audit, dict) or audit.get("deterministic_ready") is not True
            for audit in audits
        ):
            reasons.append("legacy_audit")
        return {"admitted": False, "reasons": sorted(reasons)}

    receipt_by_path: dict[str, list[dict[str, Any]]] = {}
    for receipt in receipts:
        if isinstance(receipt, dict):
            receipt_by_path.setdefault(str(receipt.get("path") or ""), []).append(receipt)

    for audit in audits:
        if not isinstance(audit, dict):
            reasons.append("legacy_audit")
            continue
        if audit.get("deterministic_ready") is not True or audit.get("findings") != []:
            reasons.append("legacy_audit")
        path = str(audit.get("path") or "")
        candidates = receipt_by_path.get(path, [])
        if not candidates:
            reasons.append("receipt_missing")
            continue
        receipt = candidates.pop(0)
        if audit.get("deterministic_ready") is not True or audit.get("findings") != []:
            continue
        current_digest = None
        if isinstance(audit.get("source_sha256"), str):
            try:
                source_bytes = Path(path).read_bytes()
                current_digest = hashlib.sha256(source_bytes).hexdigest()
                current_audit = audit_script_entropy(source_bytes.decode("utf-8"), path=path)
            except (OSError, UnicodeError):
                reasons.append("source_digest_changed")
                continue
            if current_digest != audit.get("source_sha256"):
                reasons.append("source_digest_changed")
                continue
            if current_audit != {key: audit.get(key) for key in current_audit}:
                reasons.append("legacy_audit")
                continue
        try:
            current = build_script_entropy_receipt(
                audit,
                owner_family=str(receipt.get("owner_family") or ""),
                runtime_epoch=str(receipt.get("runtime_epoch") or ""),
                source_sha256=current_digest,
                owner_stream_name=owner_stream_name,
                owner_registry_digest=owner_registry_digest,
            )
        except (TypeError, ValueError):
            reasons.append("opaque_owner")
            continue
        if current["source_sha256"] != receipt.get("source_sha256"):
            reasons.append("source_digest_changed")
        if current["audit_sha256"] != receipt.get("audit_sha256"):
            reasons.append("legacy_audit")
        if not receipt.get("owner_family") or not receipt.get("runtime_epoch"):
            reasons.append("opaque_owner")
        if owner_family is not None and receipt.get("owner_family") != owner_family:
            reasons.append("opaque_owner")
        if runtime_epoch is not None and receipt.get("runtime_epoch") != runtime_epoch:
            reasons.append("opaque_owner")
        if owner_stream_name is not None:
            if receipt.get("owner_stream_name") != owner_stream_name:
                reasons.append("opaque_owner")
            if receipt.get("owner_registry_digest") != owner_registry_digest:
                reasons.append("opaque_owner")
    if any(receipts_for_path for receipts_for_path in receipt_by_path.values()):
        reasons.append("receipt_missing")
    return {"admitted": not reasons, "reasons": sorted(set(reasons))}


def validate_script_evidence_corpus(
    audits: object,
    receipts: object,
    trust_denials: object,
    failure_receipts: object,
) -> dict[str, Any]:
    """Validate coverage between loaded-script outcomes and persisted evidence."""
    errors: list[str] = []
    if not all(isinstance(value, list) for value in (
        audits, receipts, trust_denials, failure_receipts
    )):
        return {"valid": False, "errors": ["script_evidence_corpus_not_lists"]}

    audit_by_path: dict[str, str] = {}
    for audit in audits:
        if not isinstance(audit, dict) or not str(audit.get("path") or ""):
            errors.append("audit_entry_invalid")
            continue
        path = str(audit["path"])
        payload = json.dumps(
            audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        prior = audit_by_path.get(path)
        if prior is not None and prior != payload:
            errors.append("conflicting_audit_path")
        else:
            audit_by_path[path] = payload

    receipt_by_path: dict[str, str] = {}
    for receipt in receipts:
        if not isinstance(receipt, dict) or not str(receipt.get("path") or ""):
            errors.append("receipt_entry_invalid")
            continue
        path = str(receipt["path"])
        payload = json.dumps(
            receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        prior = receipt_by_path.get(path)
        if prior is not None and prior != payload:
            errors.append("conflicting_receipt_path")
        else:
            receipt_by_path[path] = payload
    for path in audit_by_path:
        if path not in receipt_by_path:
            errors.append("receipt_missing_for_audit")
    for path in receipt_by_path:
        if path not in audit_by_path:
            errors.append("receipt_without_audit")

    denial_paths: list[str] = []
    for denial in trust_denials:
        if not isinstance(denial, dict) or not str(denial.get("path") or ""):
            errors.append("trust_denial_entry_invalid")
            continue
        denial_paths.append(str(denial["path"]))
    trust_failure_paths = {
        str(failure.get("path"))
        for failure in failure_receipts
        if isinstance(failure, dict) and failure.get("phase") == "trust"
    }
    for path in denial_paths:
        if path not in trust_failure_paths:
            errors.append("trust_denial_failure_missing")
    for failure in failure_receipts:
        if not isinstance(failure, dict) or not str(failure.get("path") or ""):
            errors.append("failure_receipt_entry_invalid")

    return {"valid": not errors, "errors": sorted(set(errors))}


def build_dynamic_script_boundary_receipt(
    audits: object,
    receipts: object,
    trust_denials: object,
    failure_receipts: object,
) -> dict[str, Any]:
    """Summarize dynamic-script evidence without admitting opaque entropy."""
    corpus = validate_script_evidence_corpus(
        audits, receipts, trust_denials, failure_receipts
    )
    audit_rows = audits if isinstance(audits, list) else []
    opaque = any(
        not isinstance(item, dict)
        or item.get("deterministic_ready") is not True
        or bool(item.get("findings"))
        for item in audit_rows
    )
    status = "admitted" if corpus["valid"] and not opaque else "quarantined"
    payload = {
        "schema_version": 1,
        "boundary": "dynamic_script_entropy",
        "status": status,
        "audit_count": len(audits) if isinstance(audits, list) else 0,
        "receipt_count": len(receipts) if isinstance(receipts, list) else 0,
        "trust_denial_count": len(trust_denials) if isinstance(trust_denials, list) else 0,
        "failure_receipt_count": len(failure_receipts) if isinstance(failure_receipts, list) else 0,
        "opaque_findings": bool(opaque),
        "corpus_valid": bool(corpus["valid"]),
        "corpus_errors": list(corpus["errors"]),
    }
    payload["digest"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def validate_dynamic_script_boundary_receipt(receipt: object) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        return {"valid": False, "errors": ["dynamic_boundary_receipt_not_mapping"]}
    required = {
        "schema_version", "boundary", "status", "audit_count", "receipt_count",
        "trust_denial_count", "failure_receipt_count", "opaque_findings",
        "corpus_valid", "corpus_errors", "digest",
    }
    if set(receipt) != required or receipt.get("schema_version") != 1:
        return {"valid": False, "errors": ["dynamic_boundary_receipt_schema_invalid"]}
    errors: list[str] = []
    if receipt.get("boundary") != "dynamic_script_entropy":
        errors.append("dynamic_boundary_receipt_boundary_invalid")
    if receipt.get("status") not in {"admitted", "quarantined"}:
        errors.append("dynamic_boundary_receipt_status_invalid")
    for field in ("audit_count", "receipt_count", "trust_denial_count", "failure_receipt_count"):
        value = receipt.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"dynamic_boundary_receipt_{field}_invalid")
    if not isinstance(receipt.get("opaque_findings"), bool) or not isinstance(
        receipt.get("corpus_valid"), bool
    ) or not isinstance(receipt.get("corpus_errors"), list):
        errors.append("dynamic_boundary_receipt_flags_invalid")
    if receipt.get("status") == "admitted" and (
        receipt.get("opaque_findings") is not False or receipt.get("corpus_valid") is not True
    ):
        errors.append("dynamic_boundary_receipt_overclaims_admission")
    canonical = dict(receipt)
    digest = canonical.pop("digest", None)
    expected = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if digest != expected:
        errors.append("dynamic_boundary_receipt_digest_mismatch")
    return {"valid": not errors, "errors": sorted(set(errors))}


def validate_script_descriptor_coverage(
    declared_paths: object,
    audits: object,
    receipts: object,
    trust_denials: object,
    failure_receipts: object,
) -> dict[str, Any]:
    """Ensure every declared scene script produced an observable outcome."""
    if not isinstance(declared_paths, list):
        return {"valid": False, "errors": ["declared_script_paths_not_list"]}
    outcome = set()
    for collection in (audits, receipts, trust_denials, failure_receipts):
        if isinstance(collection, list):
            outcome.update(
                str(item.get("path") or "")
                for item in collection
                if isinstance(item, dict) and str(item.get("path") or "")
            )
    errors: list[str] = []
    seen: set[str] = set()
    for value in declared_paths:
        path = str(value or "")
        if not path:
            errors.append("declared_script_path_invalid")
        elif path in seen:
            errors.append("duplicate_declared_script_path")
        elif path not in outcome:
            errors.append("declared_script_outcome_missing")
        seen.add(path)
    return {"valid": not errors, "errors": sorted(set(errors))}


def _normalise_inventory_path(value: object) -> str:
    """Keep inventory keys stable across Windows and POSIX evidence writers."""
    return str(value or "").strip().replace("\\", "/")


def build_project_script_inventory(
    project_manifest: object,
    *,
    project_path: str | Path | None = None,
    scene_script_paths: object = (),
    project_lock: object = None,
    loaded_receipts: object = (),
    trust_denials: object = (),
    failure_receipts: object = (),
) -> list[dict[str, Any]]:
    """Build one stable inventory for project-declared executable sources.

    Package ids and resource-only package entries are intentionally ignored.
    Only project script trust grants, scene script descriptors, and validated
    project addon ``plugin.json`` entries become executable inventory items.
    """
    del project_lock  # Reserved for lock digest validation at the caller seam.
    declared: dict[tuple[str, str], dict[str, Any]] = {}

    project_root = None
    if project_path is not None:
        try:
            project_root = Path(project_path).resolve()
        except (OSError, RuntimeError):
            project_root = None

    def canonical_path(path: object) -> str:
        normalized = _normalise_inventory_path(path)
        if project_root is not None and normalized:
            try:
                candidate_path = Path(normalized)
                candidate = (
                    candidate_path
                    if candidate_path.is_absolute()
                    else project_root / candidate_path
                ).resolve()
                normalized = candidate.relative_to(project_root).as_posix()
            except (OSError, RuntimeError, ValueError):
                pass
        return normalized

    def add(path: object, *, source: str, kind: str) -> None:
        normalized = canonical_path(path)
        if not normalized:
            return
        key = (kind, normalized)
        declared.setdefault(key, {
            "path": normalized,
            "source": source,
            "kind": kind,
            "declared": True,
        })

    manifest = project_manifest if isinstance(project_manifest, dict) else {}
    trust = manifest.get("script_trust")
    grants = trust.get("sha256_allowlist") if isinstance(trust, dict) else ()
    if isinstance(grants, list):
        for grant in grants:
            if isinstance(grant, dict):
                add(grant.get("path"), source="project_manifest", kind="project_script")

    if isinstance(scene_script_paths, (list, tuple, set, frozenset)):
        for path in scene_script_paths:
            add(path, source="scene_descriptor", kind="project_script")

    if project_path is not None:
        root = Path(project_path)
        addons_root = root / "addons"
        try:
            addon_dirs = sorted(
                (item for item in addons_root.iterdir() if item.is_dir() and not item.is_symlink()),
                key=lambda item: item.name.casefold(),
            ) if addons_root.is_dir() and not addons_root.is_symlink() else ()
        except OSError:
            addon_dirs = ()
        for addon_root in addon_dirs:
            manifest_path = addon_root / "plugin.json"
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict) or payload.get("schema_version") != 1:
                continue
            entry = _normalise_inventory_path(payload.get("entry"))
            if not entry or Path(entry).is_absolute() or ".." in Path(entry).parts:
                continue
            entry_path = addon_root / Path(entry)
            if not entry_path.is_file() or entry_path.is_symlink():
                continue
            try:
                relative = entry_path.resolve().relative_to(root.resolve()).as_posix()
            except (OSError, RuntimeError, ValueError):
                continue
            add(relative, source="project_addon_manifest", kind="project_addon")
            declared[("project_addon", canonical_path(relative))]["entry_sha256"] = hashlib.sha256(
                entry_path.read_bytes()
            ).hexdigest()
            declared[("project_addon", canonical_path(relative))]["manifest_sha256"] = hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest()

    outcomes: dict[tuple[str, str], str] = {}
    for collection, outcome in (
        (loaded_receipts, "loaded"),
        (trust_denials, "denied"),
        (failure_receipts, "failed"),
    ):
        if not isinstance(collection, (list, tuple)):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            path = canonical_path(item.get("path"))
            if path:
                key = ("project_addon" if item.get("kind") == "project_addon" else "project_script", path)
                outcomes[key] = outcome
                if key in declared and key[0] == "project_addon":
                    for digest_name in ("entry_sha256", "manifest_sha256"):
                        expected = declared[key].get(digest_name)
                        actual = str(item.get(digest_name) or "")
                        if expected and actual and expected != actual:
                            outcomes[key] = "digest_mismatch"

    result: list[dict[str, Any]] = []
    for key in sorted(declared):
        row = dict(declared[key])
        outcome = outcomes.get(key)
        row["loaded"] = outcome in {"loaded", "runtime_loaded"}
        row["outcome"] = outcome or "declared_not_loaded"
        result.append(row)
    return result


def validate_project_script_inventory(
    inventory: object,
    *,
    project_path: str | Path | None = None,
    loaded_receipts: object = (),
    trust_denials: object = (),
    failure_receipts: object = (),
) -> dict[str, Any]:
    """Fail closed when declared executable sources lack an observed outcome."""
    if not isinstance(inventory, list):
        return {"valid": False, "errors": ["script_inventory_not_list"]}
    errors: list[str] = []
    project_root = None
    if project_path is not None:
        try:
            project_root = Path(project_path).resolve()
        except (OSError, RuntimeError):
            project_root = None

    def canonical_observed_path(value: object) -> str:
        normalized = _normalise_inventory_path(value)
        if project_root is not None and normalized:
            candidate_path = Path(normalized)
            try:
                candidate = (
                    candidate_path
                    if candidate_path.is_absolute()
                    else project_root / candidate_path
                ).resolve()
                normalized = candidate.relative_to(project_root).as_posix()
            except (OSError, RuntimeError, ValueError):
                pass
        return normalized

    declared: set[tuple[str, str]] = set()
    for item in inventory:
        if not isinstance(item, dict):
            errors.append("script_inventory_entry_invalid")
            continue
        path = _normalise_inventory_path(item.get("path"))
        kind = str(item.get("kind") or "project_script")
        key = (kind, path)
        if not path:
            errors.append("script_inventory_path_invalid")
        elif key in declared:
            errors.append("duplicate_script_inventory_entry")
        declared.add(key)
        if item.get("outcome") == "digest_mismatch":
            errors.append("project_addon_source_digest_mismatch")

    observed: set[tuple[str, str]] = set()
    for collection in (loaded_receipts, trust_denials, failure_receipts):
        if not isinstance(collection, (list, tuple)):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            path = canonical_observed_path(item.get("path"))
            if path:
                kind = str(item.get("kind") or "project_script")
                observed.add((kind, path))
    for key in sorted(declared - observed):
        errors.append("declared_executable_outcome_missing")
    for key in sorted(observed - declared):
        errors.append("runtime_executable_not_declared")
    return {"valid": not errors, "errors": sorted(set(errors))}


def project_script_entropy_admission(
    audits: object,
    receipts: object,
    *,
    owner_family: str | None = None,
    runtime_epoch: str | None = None,
    owner_stream_name: str | None = None,
    owner_registry_digest: str | None = None,
    trust_denials: object = (),
) -> dict[str, Any]:
    """Build the shared read-only status/quarantine projection for scripts."""
    diagnostic = diagnose_script_entropy_admission(
        audits,
        receipts,
        owner_family=owner_family,
        runtime_epoch=runtime_epoch,
        owner_stream_name=owner_stream_name,
        owner_registry_digest=owner_registry_digest,
    )
    findings: list[dict[str, str]] = []
    denied_scripts = []
    if isinstance(trust_denials, (list, tuple)):
        for denial in trust_denials:
            if isinstance(denial, dict):
                denied_scripts.append({
                    "path": str(denial.get("path") or ""),
                    "reason": str(denial.get("reason") or "untrusted"),
                })
    if isinstance(audits, list):
        for audit in audits:
            if isinstance(audit, dict):
                for finding in audit.get("findings", ()):
                    if isinstance(finding, dict):
                        findings.append({
                            "kind": str(finding.get("kind") or "unknown"),
                            "authority": str(finding.get("authority") or "unknown"),
                        })
    return {
        "schema_version": 1,
        "status": "script_entropy_admission_projection",
        "read_only": True,
        "availability": "observed" if isinstance(audits, list) else "unavailable",
        "reasons": list(diagnostic["reasons"]),
        "findings": findings,
        "trust_denials": denied_scripts,
        "quarantined": bool(not diagnostic["admitted"] or denied_scripts),
        "admitted": bool(diagnostic["admitted"] and not denied_scripts),
        "replay_admitted": False,
        "default_ready": False,
    }


def build_script_entropy_admission_contract() -> dict[str, Any]:
    """Describe the common status projection without claiming live evidence."""
    projection = project_script_entropy_admission(None, None)
    return {
        **projection,
        "status": "script_entropy_admission_contract",
        "availability": "contract_only",
        "admitted": False,
        "quarantined": True,
        "reasons": ["current_script_evidence_not_observed"],
        "reason_taxonomy": [
            "legacy_audit",
            "receipt_missing",
            "source_digest_changed",
            "opaque_owner",
        ],
        "opaque_findings_fail_closed": True,
    }


__all__ = [
    "audit_script_entropy",
    "audit_script_file",
    "build_script_entropy_receipt",
    "diagnose_script_entropy_admission",
    "validate_script_evidence_corpus",
    "build_dynamic_script_boundary_receipt",
    "validate_dynamic_script_boundary_receipt",
    "validate_script_descriptor_coverage",
    "build_project_script_inventory",
    "validate_project_script_inventory",
    "project_script_entropy_admission",
    "build_script_entropy_admission_contract",
]
