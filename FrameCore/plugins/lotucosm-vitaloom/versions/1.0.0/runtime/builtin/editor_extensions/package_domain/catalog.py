"""Qt-free package catalog rules shared by runtime hosts and UI adapters."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


def normalize_package(pkg: Dict[str, Any], source: str) -> Dict[str, Any]:
    if not isinstance(pkg, dict):
        return {}
    normalized = dict(pkg)
    normalized.setdefault("id", "")
    normalized.setdefault("display_name", normalized.get("id", ""))
    normalized.setdefault("version", "")
    normalized.setdefault("category", "")
    normalized.setdefault("description", "")
    normalized.setdefault("dependencies", [])
    normalized.setdefault("conflicts", [])
    normalized.setdefault("plugins", [])
    normalized.setdefault("source", source)
    return normalized


def merge_package_lists(
    package_lists: List[List[Dict[str, Any]]], priority_sources: List[str]
) -> List[Dict[str, Any]]:
    """Merge packages by id, preferring sources earlier in priority_sources."""
    priority = {name: index for index, name in enumerate(priority_sources)}
    merged: Dict[str, Dict[str, Any]] = {}
    for package_list in package_lists:
        for package in package_list:
            if not isinstance(package, dict):
                continue
            package_id = str(package.get("id", "") or "")
            if not package_id:
                continue
            source = str(package.get("source", "unknown"))
            current = merged.get(package_id)
            if current is None:
                merged[package_id] = package
                continue
            current_source = str(current.get("source", "unknown"))
            if priority.get(source, 10_000) < priority.get(current_source, 10_000):
                merged[package_id] = package
    return sorted(
        merged.values(),
        key=lambda package: (str(package.get("display_name", "")), str(package.get("id", ""))),
    )


def parse_version(version: str) -> tuple[int, int, int]:
    parts = (version or "0.0.0").split(".")
    numbers: list[int] = []
    for index in range(3):
        try:
            numbers.append(int(parts[index]) if index < len(parts) else 0)
        except (TypeError, ValueError):
            numbers.append(0)
    return numbers[0], numbers[1], numbers[2]


def version_gte(actual: str, expected_min: str) -> bool:
    return parse_version(actual) >= parse_version(expected_min)


def parse_dependency_expr(expr: str) -> tuple[str, str, str]:
    text = (expr or "").strip()
    if ">=" in text:
        package_id, version = text.split(">=", 1)
        return package_id.strip(), ">=", version.strip()
    return text, "", ""


def should_block_enable(enable_constraint_mode: str, has_dependency_or_conflict_issue: bool) -> bool:
    """Keep the editor enable action's legacy contract: only block mode prevents enable."""
    return bool(has_dependency_or_conflict_issue) and str(enable_constraint_mode).lower() == "block"


def collect_update_candidates(
    loaded_lists: List[List[Dict[str, Any]]], merged: List[Dict[str, Any]]
) -> Dict[str, str]:
    highest: Dict[str, str] = {}
    for package_list in loaded_lists:
        for package in package_list:
            if not isinstance(package, dict):
                continue
            package_id = str(package.get("id", "") or "")
            if not package_id:
                continue
            version = str(package.get("version", "") or "0.0.0")
            current = highest.get(package_id)
            if current is None or version_gte(version, current):
                highest[package_id] = version
    updates: Dict[str, str] = {}
    for package in merged:
        package_id = str(package.get("id", "") or "")
        if not package_id:
            continue
        current = str(package.get("version", "") or "0.0.0")
        latest = highest.get(package_id, current)
        if version_gte(latest, current) and parse_version(latest) != parse_version(current):
            updates[package_id] = latest
    return updates


def select_target_updates(update_candidates: Dict[str, str], checked_ids: Set[str]) -> Dict[str, str]:
    if not checked_ids:
        return dict(update_candidates)
    return {package_id: version for package_id, version in update_candidates.items() if package_id in checked_ids}


def matches_status_filter(
    is_enabled: bool,
    has_issues: bool,
    status_filter: str,
    *,
    implicitly_enabled: bool = False,
) -> bool:
    if status_filter == "enabled":
        return implicitly_enabled or is_enabled
    if status_filter == "disabled":
        return not implicitly_enabled and not is_enabled
    if status_filter == "issues":
        return has_issues
    return True


def apply_version_overrides(
    packages: List[Dict[str, Any]], overrides: Dict[str, str]
) -> List[Dict[str, Any]]:
    if not overrides:
        return packages
    result: List[Dict[str, Any]] = []
    for package in packages:
        package_id = str(package.get("id", "") or "")
        if package_id and package_id in overrides:
            overridden = dict(package)
            overridden["version"] = overrides[package_id]
            result.append(overridden)
        else:
            result.append(package)
    return result