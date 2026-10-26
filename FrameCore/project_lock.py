# -*- coding: utf-8 -*-
"""Project runtime lock resolution for FrameCore and Suite Hub."""
from __future__ import annotations

import json
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from FrameCore.product_registry import ProductRegistry, ProductVersion, load_product_registry
from FrameCore.suite_registry import SuiteManifest, load_default_suite_manifest

DEFAULT_SUITE_ID = "lotucosm.vitaloom.suite"
DEFAULT_PRODUCT_ID = "lotucosm-vitaloom"
IMPLICIT_PACKAGES = (
    "vitalloom.core.platform",
    "vitalloom.editor_essentials",
    "vitalloom.lotuspond.runtime",
)
CAPABILITY_PACKAGES = {
    "sr2d": ["vitalloom.engine.sr2d"],
    "game_script": ["vitalloom.engine.sr2d"],
    "pvaec": ["vitalloom.pvaec.simulation"],
}
SUPPORTED_SR2D_BACKENDS = ("auto", "python", "cpp", "rust")


def normalize_sr2d_backend_request(value: object) -> str:
    requested = str(value or "auto").strip().lower()
    if requested not in SUPPORTED_SR2D_BACKENDS:
        raise ValueError(
            "sr2d backend must be one of: " + ", ".join(SUPPORTED_SR2D_BACKENDS)
        )
    return requested


def collect_runtime_backend_selection(project_data: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw = project_data.get("sr2d_backend", "auto")
    return {"sr2d": {"requested": normalize_sr2d_backend_request(raw)}}


@dataclass(frozen=True)
class ProjectRuntimeResolution:
    suite_id: str
    suite_version: str
    product_id: str
    product_version: str
    resolved_capabilities: dict[str, str] = field(default_factory=dict)
    runtime_backend_selection: dict[str, dict[str, str]] = field(default_factory=dict)
    runtime_backend_selection_mismatch: bool = False
    lock_missing: bool = False
    product_version_missing: bool = False
    missing_capabilities: tuple[str, ...] = ()
    capability_constraint_mismatches: tuple[str, ...] = ()
    capability_version_mismatches: tuple[str, ...] = ()
    lock_error: str = ""
    lock_legacy: bool = False

    @property
    def lock_status_text(self) -> str:
        if self.lock_error:
            return "锁无效"
        if self.product_version_missing:
            return "产品版本缺失"
        if self.missing_capabilities:
            return "能力缺失"
        if self.capability_constraint_mismatches:
            return "能力约束不符"
        if self.capability_version_mismatches:
            return "能力版本不符"
        if self.runtime_backend_selection_mismatch:
            return "运行时 backend 声明不符"
        if self.lock_missing:
            return "未锁定"
        return "已锁定"

    @property
    def has_blocking_issues(self) -> bool:
        return bool(
            self.lock_error
            or self.product_version_missing
            or self.missing_capabilities
            or self.capability_constraint_mismatches
            or self.capability_version_mismatches
            or self.runtime_backend_selection_mismatch
        )

    @property
    def lock_admission_code(self) -> str:
        """Canonical machine-readable lock admission state for all consumers."""
        if self.lock_error:
            return "unsupported_schema" if "unsupported" in self.lock_error else "invalid"
        if self.product_version_missing:
            return "version_missing"
        if self.missing_capabilities:
            return "missing"
        if self.capability_version_mismatches:
            return "stale"
        if self.capability_constraint_mismatches:
            return "constraint_mismatch"
        if self.lock_missing:
            return "missing"
        if self.lock_legacy:
            return "legacy"
        return "current"

    @property
    def blocking_issue_codes(self) -> tuple[str, ...]:
        """Canonical machine codes for each independent blocking condition."""
        codes: list[str] = []
        if self.lock_error:
            codes.append(self.lock_admission_code)
        if self.product_version_missing:
            codes.append("version_missing")
        if self.missing_capabilities:
            codes.append("capabilities_missing")
        if self.capability_constraint_mismatches:
            codes.append("constraint_mismatch")
        if self.capability_version_mismatches:
            codes.append("stale")
        if self.runtime_backend_selection_mismatch:
            codes.append("runtime_backend_mismatch")
        if self.lock_missing:
            codes.append("lock_missing")
        return tuple(dict.fromkeys(codes))

    @property
    def blocking_issue_summary(self) -> str:
        parts: list[str] = []
        if self.lock_error:
            parts.append(self.lock_error)
        if self.product_version_missing:
            parts.append(f"missing product version: {self.product_id} {self.product_version}")
        if self.missing_capabilities:
            parts.append("missing capabilities: " + ", ".join(self.missing_capabilities))
        if self.capability_constraint_mismatches:
            parts.append(
                "capability constraints not satisfied: "
                + ", ".join(self.capability_constraint_mismatches)
            )
        if self.capability_version_mismatches:
            parts.append(
                "stale capability versions: "
                + ", ".join(self.capability_version_mismatches)
            )
        if self.runtime_backend_selection_mismatch:
            parts.append("runtime backend selection does not match project manifest")
        return "; ".join(parts)


def parse_version_tuple(version: str) -> tuple[int, int, int]:
    parts = (version or "0.0.0").strip().split(".")
    nums: list[int] = []
    for index in range(3):
        try:
            nums.append(int(parts[index]) if index < len(parts) else 0)
        except ValueError:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def version_matches_constraint(version: str, constraint: str) -> bool:
    text = (constraint or "").strip()
    if not text:
        return True
    current = parse_version_tuple(version)
    clauses = [c.strip() for c in text.split(",") if c.strip()]
    if not clauses:
        return True
    if not any(c[0] in "<>=" for c in clauses):
        return current == parse_version_tuple(text)
    for clause in clauses:
        match = re.match(r"^(>=|<=|>|<|==|=)\s*(\d+\.\d+\.\d+)$", clause)
        if not match:
            return False
        op, expected = match.group(1), parse_version_tuple(match.group(2))
        if op == ">=" and current < expected:
            return False
        if op == "<=" and current > expected:
            return False
        if op == ">" and current <= expected:
            return False
        if op == "<" and current >= expected:
            return False
        if op in ("==", "=") and current != expected:
            return False
    return True


def collect_required_package_ids(project_data: dict[str, Any]) -> list[str]:
    required = project_data.get("required_packages")
    if not isinstance(required, list) or not required:
        required = project_data.get("recommended_packages", [])
    if not isinstance(required, list):
        required = []
    required_capabilities = project_data.get("required_capabilities", {})
    extra_required: list[str] = []
    if isinstance(required_capabilities, dict):
        extra_required.extend(str(k) for k in required_capabilities.keys())
    elif isinstance(required_capabilities, list):
        extra_required.extend(str(x) for x in required_capabilities)

    ids: list[str] = []
    seen: set[str] = set()
    for pkg_id in list(IMPLICIT_PACKAGES) + list(required) + extra_required:
        value = str(pkg_id or "").strip()
        if value and value not in seen:
            seen.add(value)
            ids.append(value)

    capabilities = project_data.get("capabilities", [])
    if isinstance(capabilities, list):
        for capability in capabilities:
            key = str(capability or "").strip().lower()
            for pkg_id in CAPABILITY_PACKAGES.get(key, []):
                if pkg_id not in seen:
                    seen.add(pkg_id)
                    ids.append(pkg_id)
    return ids


def collect_required_capability_constraints(project_data: dict[str, Any]) -> dict[str, str]:
    required_capabilities = project_data.get("required_capabilities", {})
    if not isinstance(required_capabilities, dict):
        return {}
    constraints: dict[str, str] = {}
    for raw_id, raw_constraint in required_capabilities.items():
        pkg_id = str(raw_id or "").strip()
        constraint = str(raw_constraint or "").strip()
        if pkg_id and constraint:
            constraints[pkg_id] = constraint
    return constraints


def select_product_version(
    registry: ProductRegistry,
    product_id: str,
    version_constraint: str,
) -> ProductVersion | None:
    if not version_constraint:
        return registry.get_default_version(product_id)
    exact = registry.get_version(product_id, version_constraint)
    if exact is not None:
        return exact
    candidates = [
        version
        for (pid, _raw_version), version in registry.versions.items()
        if pid == product_id and version_matches_constraint(version.version, version_constraint)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda version: parse_version_tuple(version.version), reverse=True)
    return candidates[0]


def project_lock_path(project_path: str | Path) -> Path:
    return Path(project_path) / "project.lock.json"


def load_project_lock(project_path: str | Path) -> dict[str, Any] | None:
    path = project_lock_path(project_path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def project_lock_schema_error(lock_data: dict[str, Any] | None) -> str:
    """Return an explicit error for unsupported lock schema versions.

    A missing schema field is the legacy lock shape and remains readable. New
    schema versions must not be interpreted by an older runtime as if they
    were current data.
    """
    if not isinstance(lock_data, dict):
        return "project.lock.json is not an object"
    raw_version = lock_data.get("schema_version")
    if raw_version is None:
        return ""
    if raw_version != 1:
        return f"unsupported project.lock.json schema_version: {raw_version}"
    return ""


def _suite_and_registry(repo_root: str | Path) -> tuple[SuiteManifest, ProductRegistry]:
    suite_root = os.environ.get("VITALOOM_SUITE_ROOT")
    if suite_root:
        from FrameCore.suite_registry import load_suite_manifest

        suite = load_suite_manifest(suite_root)
    else:
        suite = load_default_suite_manifest(repo_root)
    if suite.suite_root is None:
        raise RuntimeError("suite manifest did not record suite root")
    return suite, load_product_registry(suite.suite_root)


def load_package_catalog(
    repo_root: str | Path,
    *,
    product_id: str = DEFAULT_PRODUCT_ID,
    product_version: str = "",
) -> list[dict[str, Any]]:
    """Read the selected product capability catalog with an export-runtime fallback."""
    root = Path(repo_root)
    candidates: list[Path] = []
    if os.environ.get("VITALOOM_EXPORT_ROOT"):
        candidates.append(root / "builtin" / "package_index.json")
    else:
        suite, registry = _suite_and_registry(repo_root)
        selected = (
            registry.get_version(product_id, product_version)
            if product_version
            else registry.get_default_version(product_id)
        )
        if selected and selected.builtin_capability_index:
            candidates.append(selected.version_root / selected.builtin_capability_index)
        if suite.suite_root is not None and suite.capability_catalog:
            candidates.append(suite.suite_root / suite.capability_catalog)
    candidates.append(root / "builtin" / "package_index.json")

    visited: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in visited:
            continue
        visited.add(resolved)
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            packages = data.get("packages", [])
            return packages if isinstance(packages, list) else []
        except Exception:
            return []
    return []


def _catalog_versions(
    repo_root: str | Path,
    *,
    product_id: str = DEFAULT_PRODUCT_ID,
    product_version: str = "",
) -> dict[str, str]:
    versions: dict[str, str] = {}
    for pkg in load_package_catalog(
        repo_root,
        product_id=product_id,
        product_version=product_version,
    ):
        if not isinstance(pkg, dict):
            continue
        pkg_id = str(pkg.get("id", "") or "").strip()
        version = str(pkg.get("version", "") or "").strip()
        if pkg_id and version:
            versions[pkg_id] = version
    return versions


def _project_installed_versions(project_data: dict[str, Any]) -> dict[str, str]:
    """Read Project World installed versions without importing product runtime modules."""
    state = project_data.get("package_state")
    if not isinstance(state, dict):
        return {}
    installed = state.get("installed")
    if not isinstance(installed, dict):
        return {}
    versions: dict[str, str] = {}
    for raw_id, raw_info in installed.items():
        package_id = str(raw_id or "").strip()
        if not package_id:
            continue
        version = "0.0.0"
        if isinstance(raw_info, dict):
            version = str(raw_info.get("version") or version)
        versions[package_id] = version
    return versions


def _available_capability_versions(
    repo_root: str | Path,
    project_data: dict[str, Any],
    *,
    product_id: str = DEFAULT_PRODUCT_ID,
    product_version: str = "",
) -> dict[str, str]:
    versions = _catalog_versions(
        repo_root,
        product_id=product_id,
        product_version=product_version,
    )
    for package_id, version in _project_installed_versions(project_data).items():
        versions.setdefault(package_id, version)
    return versions

def build_project_lock(
    project_data: dict[str, Any],
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    suite, registry = _suite_and_registry(repo_root)
    product_id = str(project_data.get("product_id", "") or DEFAULT_PRODUCT_ID)
    constraint = str(project_data.get("loom_editor_version", "") or "")
    product_version = select_product_version(registry, product_id, constraint)
    resolved_product_version = product_version.version if product_version else constraint
    available_versions = _available_capability_versions(
        repo_root,
        project_data,
        product_id=product_id,
        product_version=resolved_product_version,
    )
    required_ids = collect_required_package_ids(project_data)
    resolved_capabilities = {
        pkg_id: available_versions[pkg_id]
        for pkg_id in required_ids
        if pkg_id in available_versions
    }
    lock = {
        "schema_version": 1,
        "resolved_suite": {"id": suite.suite_id, "version": suite.version},
        "resolved_product": {"id": product_id, "version": resolved_product_version},
        "resolved_capabilities": resolved_capabilities,
        "runtime_backend_selection": collect_runtime_backend_selection(project_data),
    }
    trust = project_data.get("script_trust")
    if "script_trust" in project_data:
        if not isinstance(trust, dict):
            raise ValueError("script_trust must be an object")
        grants = trust.get("sha256_allowlist")
        if not isinstance(grants, list):
            raise ValueError("script_trust.sha256_allowlist must be a list")
        normalized = []
        for grant in grants:
            if not isinstance(grant, dict):
                raise ValueError("script_trust grant must be an object")
            path = str(grant.get("path") or "").strip().replace("\\", "/")
            digest = str(grant.get("sha256") or "").strip().lower()
            if not path or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("script_trust grant path or sha256 is invalid")
            normalized.append({"path": path, "sha256": digest})
        normalized.sort(key=lambda item: item["path"])
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        lock["script_trust"] = {
            "schema_version": 1,
            "sha256_allowlist_digest": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "grant_count": len(normalized),
        }
    return lock


def build_project_lock_for_path(
    project_path: str | Path,
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    project_json = Path(project_path) / "project.json"
    if not project_json.is_file():
        raise FileNotFoundError(f"missing project.json: {project_json}")
    data = json.loads(project_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"project.json root must be an object: {project_json}")
    return build_project_lock(data, repo_root=repo_root)


def project_script_trust_lock_matches(
    project_path: str | Path,
    lock_data: dict[str, Any] | None,
    *,
    repo_root: str | Path,
) -> bool:
    """Check the lock's trust digest against the current project manifest."""
    expected = build_project_lock_for_path(project_path, repo_root=repo_root)
    expected_trust = expected.get("script_trust")
    actual_trust = lock_data.get("script_trust") if isinstance(lock_data, dict) else None
    return expected_trust == actual_trust


def write_project_lock(project_path: str | Path, lock_data: dict[str, Any]) -> Path:
    path = project_lock_path(project_path)
    path.write_text(
        json.dumps(lock_data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def ensure_project_lock(
    project_path: str | Path,
    *,
    repo_root: str | Path,
    overwrite: bool = False,
) -> Path:
    path = project_lock_path(project_path)
    if path.is_file() and not overwrite:
        return path
    return write_project_lock(
        project_path,
        build_project_lock_for_path(project_path, repo_root=repo_root),
    )


def _resolve_from_lock(
    lock: dict[str, Any],
    suite: SuiteManifest,
) -> tuple[str, str, str, str, dict[str, str]]:
    raw_suite = lock.get("resolved_suite", {})
    raw_product = lock.get("resolved_product", {})
    raw_caps = lock.get("resolved_capabilities", {})
    suite_id = (
        str(raw_suite.get("id", ""))
        if isinstance(raw_suite, dict)
        else ""
    ) or suite.suite_id
    suite_version = (
        str(raw_suite.get("version", ""))
        if isinstance(raw_suite, dict)
        else ""
    ) or suite.version
    product_id = (
        str(raw_product.get("id", ""))
        if isinstance(raw_product, dict)
        else ""
    ) or DEFAULT_PRODUCT_ID
    product_version = (
        str(raw_product.get("version", ""))
        if isinstance(raw_product, dict)
        else ""
    )
    caps = {str(k): str(v) for k, v in raw_caps.items()} if isinstance(raw_caps, dict) else {}
    return suite_id, suite_version, product_id, product_version, caps


def _read_project_data(project_path: str | Path) -> dict[str, Any]:
    project_json = Path(project_path) / "project.json"
    if not project_json.is_file():
        return {}
    try:
        raw = json.loads(project_json.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _resolve_exported_project_runtime(
    project_path: str | Path,
    *,
    repo_root: str | Path,
) -> ProjectRuntimeResolution:
    """Resolve a standalone Player export that has no plugin manifest."""
    project_data = _read_project_data(project_path)
    lock = load_project_lock(project_path)
    lock_file_exists = project_lock_path(project_path).is_file()
    lock_missing = not lock_file_exists
    lock_error = ""
    lock_legacy = bool(lock_file_exists and isinstance(lock, dict) and "schema_version" not in lock)
    if lock_file_exists and lock is None:
        lock_error = "project.lock.json is invalid or unreadable"
    if lock is None:
        product_id = str(project_data.get("product_id", "") or DEFAULT_PRODUCT_ID)
        product_version = str(project_data.get("loom_editor_version", "") or "1.0.0")
        available = _available_capability_versions(
            repo_root,
            project_data,
            product_id=product_id,
            product_version=product_version,
        )
        required_ids = collect_required_package_ids(project_data)
        lock = {
            "resolved_suite": {"id": DEFAULT_SUITE_ID, "version": product_version},
            "resolved_product": {"id": product_id, "version": product_version},
            "resolved_capabilities": {
                package_id: available[package_id]
                for package_id in required_ids
                if package_id in available
            },
        }
    else:
        lock_error = project_lock_schema_error(lock)

    raw_suite = lock.get("resolved_suite", {})
    raw_product = lock.get("resolved_product", {})
    raw_caps = lock.get("resolved_capabilities", {})
    suite_id = (
        str(raw_suite.get("id", "")) if isinstance(raw_suite, dict) else ""
    ) or DEFAULT_SUITE_ID
    suite_version = (
        str(raw_suite.get("version", "")) if isinstance(raw_suite, dict) else ""
    ) or "1.0.0"
    product_id = (
        str(raw_product.get("id", "")) if isinstance(raw_product, dict) else ""
    ) or DEFAULT_PRODUCT_ID
    product_version = (
        str(raw_product.get("version", "")) if isinstance(raw_product, dict) else ""
    ) or "1.0.0"
    caps = {str(k): str(v) for k, v in raw_caps.items()} if isinstance(raw_caps, dict) else {}
    expected_backend_selection = collect_runtime_backend_selection(project_data)
    actual_backend_selection = lock.get("runtime_backend_selection")
    available_versions = _available_capability_versions(
        repo_root,
        project_data,
        product_id=product_id,
        product_version=product_version,
    )
    required_ids = set(collect_required_package_ids(project_data))
    constraints = collect_required_capability_constraints(project_data)
    missing_caps = tuple(sorted(package_id for package_id in required_ids if package_id not in available_versions))
    version_mismatches = tuple(
        sorted(
            package_id
            for package_id in required_ids
            if package_id in caps
            and package_id in available_versions
            and caps[package_id] != available_versions[package_id]
        )
    )
    constraint_mismatches = tuple(
        sorted(
            package_id
            for package_id, constraint in constraints.items()
            if package_id in available_versions
            and not version_matches_constraint(available_versions[package_id], constraint)
        )
    )
    return ProjectRuntimeResolution(
        suite_id=suite_id,
        suite_version=suite_version,
        product_id=product_id,
        product_version=product_version,
        resolved_capabilities=caps,
        runtime_backend_selection=(
            actual_backend_selection
            if isinstance(actual_backend_selection, dict)
            else expected_backend_selection
        ),
        runtime_backend_selection_mismatch=(
            lock_file_exists
            and actual_backend_selection is not None
            and actual_backend_selection != expected_backend_selection
        ),
        lock_missing=lock_missing,
        product_version_missing=False,
        missing_capabilities=missing_caps,
        capability_constraint_mismatches=constraint_mismatches,
        capability_version_mismatches=version_mismatches,
        lock_error=lock_error,
        lock_legacy=lock_legacy,
    )


def resolve_project_runtime(
    project_path: str | Path,
    *,
    repo_root: str | Path,
) -> ProjectRuntimeResolution:
    """Resolve the product version and capability lock for a Project World."""
    if os.environ.get("VITALOOM_EXPORT_ROOT"):
        return _resolve_exported_project_runtime(project_path, repo_root=repo_root)

    suite, registry = _suite_and_registry(repo_root)
    project_data = _read_project_data(project_path)
    lock = load_project_lock(project_path)
    lock_file_exists = project_lock_path(project_path).is_file()
    lock_error = ""
    lock_legacy = bool(lock_file_exists and isinstance(lock, dict) and "schema_version" not in lock)
    if lock_file_exists and lock is None:
        lock_error = "project.lock.json is invalid or unreadable"
    if lock is None:
        lock = build_project_lock(project_data, repo_root=repo_root)
        lock_missing = not lock_file_exists
    else:
        lock_missing = False
        lock_error = project_lock_schema_error(lock)

    suite_id, suite_version, product_id, product_version, caps = _resolve_from_lock(lock, suite)
    product_missing = bool(product_version) and not registry.has_version(product_id, product_version)
    available_versions = _available_capability_versions(
        repo_root,
        project_data,
        product_id=product_id,
        product_version=product_version,
    )
    required_ids = set(collect_required_package_ids(project_data))
    capability_constraints = collect_required_capability_constraints(project_data)
    missing_from_available = {
        package_id for package_id in required_ids if package_id not in available_versions
    }
    missing_from_lock = set() if lock_missing else {
        package_id for package_id in required_ids if package_id not in caps
    }
    missing_caps = tuple(sorted(missing_from_available | missing_from_lock))
    version_mismatches = tuple(
        sorted(
            package_id
            for package_id in required_ids
            if package_id in caps
            and package_id in available_versions
            and caps[package_id] != available_versions[package_id]
        )
    )
    constraint_mismatches = tuple(
        sorted(
            package_id
            for package_id, constraint in capability_constraints.items()
            if package_id in available_versions
            and not version_matches_constraint(available_versions[package_id], constraint)
        )
    )
    if lock_missing and not caps:
        caps = {
            package_id: available_versions[package_id]
            for package_id in required_ids
            if package_id in available_versions
        }
    expected_backend_selection = collect_runtime_backend_selection(project_data)
    actual_backend_selection = lock.get("runtime_backend_selection")
    return ProjectRuntimeResolution(
        suite_id=suite_id,
        suite_version=suite_version,
        product_id=product_id,
        product_version=product_version,
        resolved_capabilities=caps,
        runtime_backend_selection=(
            actual_backend_selection
            if isinstance(actual_backend_selection, dict)
            else expected_backend_selection
        ),
        runtime_backend_selection_mismatch=(
            not lock_missing
            and actual_backend_selection is not None
            and actual_backend_selection != expected_backend_selection
        ),
        lock_missing=lock_missing,
        product_version_missing=product_missing,
        missing_capabilities=missing_caps,
        capability_constraint_mismatches=constraint_mismatches,
        capability_version_mismatches=version_mismatches,
        lock_error=lock_error,
        lock_legacy=lock_legacy,
    )
