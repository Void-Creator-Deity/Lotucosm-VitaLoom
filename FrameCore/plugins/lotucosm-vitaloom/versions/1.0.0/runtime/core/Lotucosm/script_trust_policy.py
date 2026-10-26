"""Explicit project-local trust policy for executable scene scripts."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any


def evaluate_project_script_trust(
    script_path: str | Path,
    project_path: str | Path | None,
    *,
    source_sha256: str,
) -> dict[str, Any]:
    """Require a project manifest path+digest grant before executing a script."""
    source = Path(script_path).resolve()
    if project_path is None:
        return _denied("project_context_missing")
    root = Path(project_path).resolve()
    try:
        relative = source.relative_to(root).as_posix()
    except ValueError:
        return _denied("script_outside_project")
    if not relative.casefold().startswith("scripts/") or not relative.casefold().endswith(".py"):
        return _denied("script_path_not_project_script")

    manifest_path = root / "project.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _denied("project_manifest_unavailable")
    trust = manifest.get("script_trust") if isinstance(manifest, dict) else None
    grants = trust.get("sha256_allowlist") if isinstance(trust, dict) else None
    if not isinstance(grants, list):
        return _denied("script_trust_not_configured")
    matching_grants = [
        grant for grant in grants
        if isinstance(grant, dict) and grant.get("path") == relative
    ]
    if not matching_grants:
        return _denied("script_not_trusted")
    if len(matching_grants) != 1:
        return _denied("script_trust_ambiguous")
    granted_digest = matching_grants[0].get("sha256")
    if not isinstance(granted_digest, str):
        return _denied("script_trust_digest_invalid")
    normalized = granted_digest.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        return _denied("script_trust_digest_invalid")
    actual = str(source_sha256).strip().lower()
    if not hmac.compare_digest(normalized, actual):
        return _denied("script_trust_digest_mismatch")
    return {
        "trusted": True,
        "reason": "explicit_project_digest_grant",
        "relative_path": relative,
        "source_sha256": actual,
    }


def validate_project_script_trust_sources(
    project_path: str | Path,
) -> dict[str, Any]:
    """Validate every manifest grant against the files currently on disk.

    This is the project-level counterpart to the per-script admission check.
    It is used before Player/export output is accepted, so a copied, removed,
    duplicated, or path-escaped grant cannot remain valid by lock digest alone.
    """
    root = Path(project_path).resolve()
    try:
        manifest = json.loads((root / "project.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _source_denied("project_manifest_unavailable")
    if not isinstance(manifest, dict):
        return _source_denied("project_manifest_invalid")
    trust = manifest.get("script_trust")
    if not isinstance(trust, dict):
        return _source_denied("script_trust_invalid")
    grants = trust.get("sha256_allowlist")
    if not isinstance(grants, list):
        return _source_denied("script_trust_not_configured")

    seen: set[str] = set()
    for grant in grants:
        if not isinstance(grant, dict):
            return _source_denied("script_trust_grant_invalid")
        raw_path = grant.get("path")
        relative = str(raw_path or "").strip().replace("\\", "/")
        if (
            not relative
            or relative != str(raw_path or "").strip()
            or not relative.casefold().startswith("scripts/")
            or not relative.casefold().endswith(".py")
            or relative in seen
        ):
            return _source_denied("script_trust_path_invalid")
        seen.add(relative)
        try:
            source = (root / relative).resolve()
            resolved_relative = source.relative_to(root).as_posix()
        except (OSError, ValueError):
            return _source_denied("script_outside_project")
        if resolved_relative != relative or not resolved_relative.casefold().startswith("scripts/"):
            return _source_denied("script_path_not_project_script", relative)
        if not source.is_file():
            return _source_denied("script_source_missing", relative)
        digest = str(grant.get("sha256") or "").strip().lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            return _source_denied("script_trust_digest_invalid", relative)
        try:
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
        except (OSError, IOError):
            return _source_denied("script_source_unreadable", relative)
        if not hmac.compare_digest(actual, digest):
            return _source_denied("script_source_digest_mismatch", relative)
    return {
        "trusted": True,
        "reason": "project_script_sources_match",
        "checked_count": len(grants),
        "relative_path": None,
    }


def _denied(reason: str) -> dict[str, Any]:
    return {
        "trusted": False,
        "reason": reason,
        "relative_path": None,
        "source_sha256": None,
    }


def _source_denied(reason: str, relative_path: str | None = None) -> dict[str, Any]:
    return {
        "trusted": False,
        "reason": reason,
        "checked_count": 0,
        "relative_path": relative_path,
    }


__all__ = ["evaluate_project_script_trust", "validate_project_script_trust_sources"]
