# -*- coding: utf-8 -*-
"""Canonical durable command-audit storage with legacy read compatibility.

The historic ``.vitalloom`` directory was published by earlier Registry builds.
New audit records live in ``.vitaloom`` alongside the project-owned transaction
artifacts.  This module deliberately *reads* both namespaces and never moves
or rewrites legacy history: audit files are evidence, so an implicit migration
would make recovery and provenance harder to review.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


CANONICAL_AUDIT_NAMESPACE = ".vitaloom"
LEGACY_AUDIT_NAMESPACES = (".vitalloom",)
COMMAND_AUDIT_FILENAME = "command_audit.jsonl"


class CommandAuditHistoryError(ValueError):
    """Raised when durable audit history cannot be safely interpreted."""


def canonical_command_audit_path(project_root: str | Path) -> Path:
    """Return the only path to which new command audit entries may be written."""

    return Path(project_root) / CANONICAL_AUDIT_NAMESPACE / COMMAND_AUDIT_FILENAME


def project_command_audit_paths(project_root: str | Path) -> tuple[Path, ...]:
    """Return canonical then legacy audit paths, without creating either path."""

    project = Path(project_root)
    return (
        canonical_command_audit_path(project),
        *(project / namespace / COMMAND_AUDIT_FILENAME for namespace in LEGACY_AUDIT_NAMESPACES),
    )


def project_command_audit_exists(project_root: str | Path) -> bool:
    return any(path.is_file() for path in project_command_audit_paths(project_root))


def read_project_command_audit_entries(
    project_root: str | Path,
    *,
    strict: bool = False,
) -> list[dict[str, Any]]:
    """Read a deterministic union of canonical and legacy command audit records.

    Entries are ordered by their recorded UTC timestamp, then by namespace and
    line number.  Identical duplicated audit IDs are collapsed; conflicting
    duplicates are unsafe and therefore fail in ``strict`` mode (and are
    omitted otherwise).  Strict consumers such as irreversible pruning also
    reject malformed non-empty files, so corrupt legacy data cannot act as
    provenance evidence.
    """

    collected: list[tuple[dict[str, Any], int, int]] = []
    conflicting_ids: set[str] = set()
    seen_by_id: dict[str, tuple[str, dict[str, Any]]] = {}

    for namespace_rank, path in enumerate(project_command_audit_paths(project_root)):
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            if strict:
                raise CommandAuditHistoryError(f"Cannot read command audit: {path}") from exc
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                if strict:
                    raise CommandAuditHistoryError(
                        f"Malformed command audit record in {path} at line {line_number}"
                    ) from exc
                continue
            if not isinstance(entry, dict):
                if strict:
                    raise CommandAuditHistoryError(
                        f"Non-object command audit record in {path} at line {line_number}"
                    )
                continue
            audit_id = str(entry.get("audit_id") or "")
            if audit_id:
                fingerprint = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
                previous = seen_by_id.get(audit_id)
                if previous is not None:
                    if previous[0] == fingerprint:
                        continue
                    conflicting_ids.add(audit_id)
                    continue
                seen_by_id[audit_id] = (fingerprint, entry)
            collected.append((entry, namespace_rank, line_number))

    if conflicting_ids:
        if strict:
            ids = ", ".join(sorted(conflicting_ids))
            raise CommandAuditHistoryError(f"Conflicting command audit ids: {ids}")
        collected = [item for item in collected if str(item[0].get("audit_id") or "") not in conflicting_ids]

    collected.sort(key=_audit_entry_order_key)
    return [entry for entry, _namespace_rank, _line_number in collected]


def _audit_entry_order_key(item: tuple[dict[str, Any], int, int]) -> tuple[int, datetime, int, int]:
    entry, namespace_rank, line_number = item
    raw_at = str(entry.get("at") or "")
    try:
        timestamp = datetime.fromisoformat(raw_at.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)
        return (1, timestamp, namespace_rank, line_number)
    except ValueError:
        # Historic hand-authored fixtures may lack a timestamp.  Preserve a
        # deterministic order without elevating them over timestamped records.
        return (0, datetime.min.replace(tzinfo=timezone.utc), namespace_rank, line_number)
