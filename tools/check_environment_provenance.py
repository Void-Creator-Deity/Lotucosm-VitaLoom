#!/usr/bin/env python3
"""Read-only diagnostic for VitaLoom's Python environment provenance.

This tool never invokes a package manager and never writes to the project or
Python environment.  It reports observed interpreter ownership, package import
origins, editable-install hooks, and selected uv.lock version drift.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import re
import sys
import sysconfig
import tomllib
from pathlib import Path
from typing import Any, Mapping

KEY_DISTRIBUTIONS = (
    "numpy",
    "pygame",
    "PyQt6",
    "pytest",
    "lotucosm-vitaloom",
)
KEY_MODULES = (
    "numpy",
    "pygame",
    "PyQt6",
    "pytest",
    "FrameCore",
)


def normalize_distribution_name(name: str) -> str:
    """Return the PEP 503-style comparison key for a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def classify_environment(
    prefix: Path,
    base_prefix: Path,
    conda_meta_exists: bool,
) -> str:
    """Classify observed interpreter ownership without guessing its manager."""
    if conda_meta_exists:
        return "conda_prefix"
    if prefix != base_prefix:
        return "stdlib_or_uv_venv"
    return "standalone_or_unknown_prefix"


def read_lock_versions(lock_path: Path) -> dict[str, str]:
    """Read package versions from uv.lock's standard package table."""
    with lock_path.open("rb") as lock_file:
        lock_data = tomllib.load(lock_file)
    packages = lock_data.get("package", [])
    if not isinstance(packages, list):
        raise ValueError("uv.lock 的 package 字段不是数组")

    versions: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, Mapping):
            continue
        name = package.get("name")
        version = package.get("version")
        if isinstance(name, str) and isinstance(version, str):
            versions[normalize_distribution_name(name)] = version
    return versions


def calculate_lock_drift(
    distributions: Mapping[str, Mapping[str, Any]],
    lock_versions: Mapping[str, str],
) -> dict[str, dict[str, str | None]]:
    """Return only selected installed-versus-lock version differences."""
    drift: dict[str, dict[str, str | None]] = {}
    for display_name, fact in distributions.items():
        installed_version = fact.get("version")
        locked_version = lock_versions.get(normalize_distribution_name(display_name))
        if isinstance(installed_version, str) and isinstance(locked_version, str):
            if installed_version != locked_version:
                drift[display_name] = {
                    "installed": installed_version,
                    "locked": locked_version,
                }
    return drift


def _distribution_fact(name: str) -> dict[str, Any]:
    normalized_name = normalize_distribution_name(name)
    for distribution in importlib.metadata.distributions():
        metadata_name = distribution.metadata.get("Name")
        if not metadata_name or normalize_distribution_name(metadata_name) != normalized_name:
            continue
        installer = distribution.read_text("INSTALLER")
        return {
            "installed": True,
            "version": distribution.version,
            "path": str(Path(distribution.locate_file(""))),
            "installer": installer.strip() if installer else None,
        }
    return {
        "installed": False,
        "version": None,
        "path": None,
        "installer": None,
    }


def _module_origin(name: str) -> str | None:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, AttributeError, ValueError):
        return None
    if spec is None:
        return None
    return spec.origin


def _editable_hooks(site_packages: Path) -> list[str]:
    if not site_packages.is_dir():
        return []
    return sorted(
        candidate.name
        for candidate in site_packages.glob("__editable__.lotucosm_vitaloom*")
        if candidate.is_file()
    )


def build_report(project_root: Path) -> dict[str, Any]:
    """Build a serializable, read-only provenance report for *project_root*."""
    project_root = project_root.resolve()
    prefix = Path(sys.prefix).resolve()
    base_prefix = Path(sys.base_prefix).resolve()
    conda_meta_present = (prefix / "conda-meta").is_dir()
    site_packages = Path(sysconfig.get_paths()["purelib"]).resolve()
    distributions = {name: _distribution_fact(name) for name in KEY_DISTRIBUTIONS}
    lock_path = project_root / "uv.lock"

    lock_error: str | None = None
    if lock_path.is_file():
        try:
            lock_versions = read_lock_versions(lock_path)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
            lock_versions = {}
            lock_error = f"{type(error).__name__}: {error}"
    else:
        lock_versions = {}

    return {
        "project_root": str(project_root),
        "executable": str(Path(sys.executable).resolve()),
        "prefix": str(prefix),
        "base_prefix": str(base_prefix),
        "environment_kind": classify_environment(prefix, base_prefix, conda_meta_present),
        "conda_meta_present": conda_meta_present,
        "site_packages": str(site_packages),
        "project_editable_hook_present": bool(_editable_hooks(site_packages)),
        "project_editable_hooks": _editable_hooks(site_packages),
        "distributions": distributions,
        "module_origins": {name: _module_origin(name) for name in KEY_MODULES},
        "uv_lock_present": lock_path.is_file(),
        "uv_lock_versions": {
            name: lock_versions.get(normalize_distribution_name(name))
            for name in KEY_DISTRIBUTIONS
        },
        "uv_lock_error": lock_error,
        "lock_drift": calculate_lock_drift(distributions, lock_versions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="项目根目录（默认：本工具所在仓库根目录）",
    )
    args = parser.parse_args()
    print(json.dumps(build_report(args.project_root), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
