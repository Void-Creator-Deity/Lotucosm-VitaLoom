# -*- coding: utf-8 -*-
"""Persistent, Qt-free project asset identity and refresh Authority.

The Asset Index owns current filesystem, dependency, provenance, and export facts.
This Registry owns durable IDs, tombstones, caller-supplied digest-cache metadata,
and explicit refresh evidence.  It intentionally has no UI, singleton, or command
registration dependency.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.VitaLoom.project.asset_index import build_project_asset_index

SCHEMA_VERSION = 1
REGISTRY_DIRECTORY = ".vitaloom"
REGISTRY_FILENAME = "asset_registry.json"


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _project_path(project_root: str | Path) -> Path:
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"Project root does not exist: {project}")
    return project


def _registry_path(project: Path) -> Path:
    return project / REGISTRY_DIRECTORY / REGISTRY_FILENAME


def _relative_registry_path() -> str:
    return f"{REGISTRY_DIRECTORY}/{REGISTRY_FILENAME}"


def _sorted_entries(entries: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(entries[asset_id]) for asset_id in sorted(entries)]


def _valid_entry(asset_id: str, entry: Any, *, tombstone: bool) -> bool:
    if not isinstance(entry, Mapping) or entry.get("id") != asset_id:
        return False
    if not isinstance(entry.get("path" if not tombstone else "last_path"), str):
        return False
    if not isinstance(entry.get("sha256" if not tombstone else "last_sha256"), str):
        return False
    if tombstone:
        return isinstance(entry.get("deleted_generation"), int)
    return all(
        isinstance(entry.get(key), int)
        for key in ("bytes", "mtime_ns", "created_generation", "updated_generation")
    )


def _validate_registry(data: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(data, Mapping):
        return None, "registry_not_object"
    if data.get("schema_version") != SCHEMA_VERSION:
        return None, "unsupported_schema"
    assets = data.get("assets")
    tombstones = data.get("tombstones")
    if not isinstance(assets, Mapping) or not isinstance(tombstones, Mapping):
        return None, "invalid_entry_collections"
    if not isinstance(data.get("generation"), int) or data["generation"] < 0:
        return None, "invalid_generation"
    if not isinstance(data.get("registry_revision"), str):
        return None, "invalid_registry_revision"
    for asset_id, entry in assets.items():
        if not isinstance(asset_id, str) or not _valid_entry(asset_id, entry, tombstone=False):
            return None, "invalid_active_entry"
    for asset_id, entry in tombstones.items():
        if not isinstance(asset_id, str) or not _valid_entry(asset_id, entry, tombstone=True):
            return None, "invalid_tombstone"
    return {
        "schema_version": SCHEMA_VERSION,
        "generation": int(data["generation"]),
        "registry_revision": str(data["registry_revision"]),
        "assets": {str(asset_id): dict(entry) for asset_id, entry in assets.items()},
        "tombstones": {str(asset_id): dict(entry) for asset_id, entry in tombstones.items()},
    }, None


def _read_registry(project: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    path = _registry_path(project)
    if not path.is_file():
        return None, "missing", None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "malformed", "invalid_json"
    except OSError:
        return None, "malformed", "read_error"
    valid, error = _validate_registry(data)
    if valid is None:
        return None, "malformed", error
    return valid, "ok", None


def _public_tombstones(tombstones: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for asset_id in sorted(tombstones):
        row = dict(tombstones[asset_id])
        row["asset_id"] = row.pop("id")
        rows.append(row)
    return rows


def load_project_asset_registry(project_root: str | Path) -> dict[str, Any]:
    """Load durable registry state without creating, refreshing, or repairing it."""

    project = _project_path(project_root)
    data, status, error = _read_registry(project)
    if data is None:
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "project_path": str(project),
            "registry_path": _relative_registry_path(),
            "status": status,
            "asset_count": 0,
            "assets": [],
            "tombstones": [],
        }
        if error is not None:
            result["error"] = error
        return result
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "registry_path": _relative_registry_path(),
        "status": "ok",
        "generation": data["generation"],
        "registry_revision": data["registry_revision"],
        "asset_count": len(data["assets"]),
        "assets": _sorted_entries(data["assets"]),
        "tombstones": _public_tombstones(data["tombstones"]),
    }


def _write_registry(project: Path, data: Mapping[str, Any]) -> None:
    target = _registry_path(project)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{REGISTRY_FILENAME}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _active_entry(
    asset_id: str,
    row: Mapping[str, Any],
    *,
    mtime_ns: int,
    created_generation: int,
    updated_generation: int,
) -> dict[str, Any]:
    return {
        "id": asset_id,
        "path": str(row["path"]),
        "bytes": int(row["bytes"]),
        "mtime_ns": mtime_ns,
        "sha256": str(row["sha256"]),
        "created_generation": created_generation,
        "updated_generation": updated_generation,
    }


def _current_rows(project: Path, asset_index: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    rows: dict[str, dict[str, Any]] = {}
    mtimes: dict[str, int] = {}
    for source in asset_index["inventory"]:
        row = dict(source)
        path = str(row["path"])
        stat = (project / path).stat()
        rows[path] = row
        mtimes[path] = stat.st_mtime_ns
    return rows, mtimes


def _registry_revision(generation: int, assets: Mapping[str, Any], tombstones: Mapping[str, Any]) -> str:
    return _stable_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "generation": generation,
            "assets": {asset_id: assets[asset_id] for asset_id in sorted(assets)},
            "tombstones": {asset_id: tombstones[asset_id] for asset_id in sorted(tombstones)},
        }
    )


def _canonical_hints(rename_hints: Mapping[str, str] | None) -> dict[str, str]:
    if not rename_hints:
        return {}
    hints: dict[str, str] = {}
    for before, after in rename_hints.items():
        old_path = str(before).replace("\\", "/")
        new_path = str(after).replace("\\", "/")
        if old_path and new_path:
            hints[old_path] = new_path
    return hints


def _canonical_restore_hints(restore_hints: Mapping[str, str] | None) -> dict[str, str]:
    if not restore_hints:
        return {}
    return {
        str(asset_id): str(path).replace("\\", "/")
        for asset_id, path in restore_hints.items()
        if str(asset_id).strip() and str(path).strip()
    }


def _asset_projection(asset_index: Mapping[str, Any], assets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    ids_by_path = {str(entry["path"]): asset_id for asset_id, entry in assets.items()}
    rows: list[dict[str, Any]] = []
    for inventory in asset_index["inventory"]:
        path = str(inventory["path"])
        asset_id = ids_by_path.get(path)
        if asset_id is None:
            raise RuntimeError(f"Registry has no active identity for indexed file: {path}")
        rows.append(
            {
                "path": path,
                "asset_id": asset_id,
                "kind": inventory["kind"],
                "suffix": inventory["suffix"],
                "bytes": inventory["bytes"],
                "sha256": inventory["sha256"],
            }
        )
    return rows


def refresh_project_asset_registry(
    project_root: str | Path,
    *,
    rename_hints: Mapping[str, str] | None = None,
    restore_hints: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Refresh durable identity against current Index facts and write atomically.

    ``rename_hints`` is reserved for an explicit caller that has already completed
    a validated project-contained rename. ``restore_hints`` may reactivate only a
    matching tombstone ID/path/digest pair for a durable transaction undo. External
    filesystem changes receive identity continuity only through one-to-one digest
    matching.
    """

    project = _project_path(project_root)
    previous, read_status, read_error = _read_registry(project)
    recovery: dict[str, Any] = {"status": "none"}
    if previous is None:
        previous = {
            "schema_version": SCHEMA_VERSION,
            "generation": 0,
            "registry_revision": "",
            "assets": {},
            "tombstones": {},
        }
        if read_status == "malformed":
            recovery = {"status": "reinitialized_from_malformed", "error": read_error}

    old_assets: dict[str, dict[str, Any]] = {
        asset_id: dict(entry) for asset_id, entry in previous["assets"].items()
    }
    old_tombstones: dict[str, dict[str, Any]] = {
        asset_id: dict(entry) for asset_id, entry in previous["tombstones"].items()
    }
    digest_cache = {
        str(entry["path"]): {
            "bytes": entry["bytes"],
            "mtime_ns": entry["mtime_ns"],
            "sha256": entry["sha256"],
        }
        for entry in old_assets.values()
    }
    cache_stats = {"cache_hits": 0, "cache_misses": 0}
    asset_index = build_project_asset_index(
        project,
        digest_cache=digest_cache,
        cache_stats=cache_stats,
    )
    current_rows, current_mtimes = _current_rows(project, asset_index)
    old_by_path = {str(entry["path"]): asset_id for asset_id, entry in old_assets.items()}
    new_assets: dict[str, dict[str, Any]] = {}
    consumed_old: set[str] = set()
    consumed_new: set[str] = set()
    changed_files = 0
    renamed_files = 0
    added_files = 0
    ambiguous_renames: list[dict[str, Any]] = []
    previous_generation = int(previous["generation"])

    # First retain entries that still occupy the same canonical path.
    same_path_updates: list[tuple[str, str, dict[str, Any], dict[str, Any], int]] = []
    for path, row in current_rows.items():
        asset_id = old_by_path.get(path)
        if asset_id is None:
            continue
        old = old_assets[asset_id]
        same_path_updates.append((asset_id, path, old, row, current_mtimes[path]))
        consumed_old.add(asset_id)
        consumed_new.add(path)

    # A durable transaction undo may reactivate exactly its matching tombstone.
    restored_updates: list[tuple[str, str, dict[str, Any], dict[str, Any], int]] = []
    for asset_id, path in sorted(_canonical_restore_hints(restore_hints).items()):
        tombstone = old_tombstones.get(asset_id)
        if tombstone is None or path not in current_rows or path in consumed_new:
            continue
        row = current_rows[path]
        if tombstone["last_path"] != path or tombstone["last_sha256"] != row["sha256"]:
            continue
        restored_updates.append((asset_id, path, tombstone, row, current_mtimes[path]))
        consumed_new.add(path)
        renamed_files += 1

    # Validated command callers can preserve identity even for duplicate bytes.
    hinted_updates: list[tuple[str, str, dict[str, Any], dict[str, Any], int]] = []
    for old_path, new_path in sorted(_canonical_hints(rename_hints).items()):
        asset_id = old_by_path.get(old_path)
        if asset_id is None or asset_id in consumed_old or new_path not in current_rows or new_path in consumed_new:
            continue
        old = old_assets[asset_id]
        hinted_updates.append((asset_id, new_path, old, current_rows[new_path], current_mtimes[new_path]))
        consumed_old.add(asset_id)
        consumed_new.add(new_path)
        renamed_files += 1

    unmatched_old = [asset_id for asset_id in sorted(old_assets) if asset_id not in consumed_old]
    unmatched_new = [path for path in sorted(current_rows) if path not in consumed_new]
    old_by_digest: dict[str, list[str]] = {}
    new_by_digest: dict[str, list[str]] = {}
    for asset_id in unmatched_old:
        old_by_digest.setdefault(str(old_assets[asset_id]["sha256"]), []).append(asset_id)
    for path in unmatched_new:
        new_by_digest.setdefault(str(current_rows[path]["sha256"]), []).append(path)

    inferred_updates: list[tuple[str, str, dict[str, Any], dict[str, Any], int]] = []
    for digest in sorted(set(old_by_digest) & set(new_by_digest)):
        old_ids = old_by_digest[digest]
        new_paths = new_by_digest[digest]
        if len(old_ids) == 1 and len(new_paths) == 1:
            asset_id = old_ids[0]
            path = new_paths[0]
            inferred_updates.append((asset_id, path, old_assets[asset_id], current_rows[path], current_mtimes[path]))
            consumed_old.add(asset_id)
            consumed_new.add(path)
            renamed_files += 1
        else:
            ambiguous_renames.append(
                {
                    "sha256": digest,
                    "missing_asset_ids": old_ids,
                    "new_paths": new_paths,
                }
            )

    def changed(old: Mapping[str, Any], row: Mapping[str, Any], mtime_ns: int, path: str) -> bool:
        return (
            old["path"] != path
            or old["bytes"] != row["bytes"]
            or old["mtime_ns"] != mtime_ns
            or old["sha256"] != row["sha256"]
        )

    core_changed = read_status != "ok"
    for asset_id, path, old, row, mtime_ns in same_path_updates + hinted_updates + inferred_updates:
        if changed(old, row, mtime_ns, path):
            core_changed = True
            if old["sha256"] != row["sha256"]:
                changed_files += 1

    remaining_new = [path for path in sorted(current_rows) if path not in consumed_new]
    remaining_old = [asset_id for asset_id in sorted(old_assets) if asset_id not in consumed_old]
    if remaining_new or remaining_old or restored_updates:
        core_changed = True
    generation = previous_generation + 1 if core_changed else previous_generation

    for asset_id, path, old, row, mtime_ns in restored_updates:
        new_assets[asset_id] = _active_entry(
            asset_id,
            row,
            mtime_ns=mtime_ns,
            created_generation=generation,
            updated_generation=generation,
        )
    for asset_id, path, old, row, mtime_ns in same_path_updates + hinted_updates + inferred_updates:
        new_assets[asset_id] = _active_entry(
            asset_id,
            row,
            mtime_ns=mtime_ns,
            created_generation=int(old["created_generation"]),
            updated_generation=generation if changed(old, row, mtime_ns, path) else int(old["updated_generation"]),
        )
    for path in remaining_new:
        asset_id = f"asset_{uuid.uuid4().hex}"
        new_assets[asset_id] = _active_entry(
            asset_id,
            current_rows[path],
            mtime_ns=current_mtimes[path],
            created_generation=generation,
            updated_generation=generation,
        )
        added_files += 1

    tombstones = {
        asset_id: value
        for asset_id, value in old_tombstones.items()
        if asset_id not in {item[0] for item in restored_updates}
    }
    for asset_id in remaining_old:
        old = old_assets[asset_id]
        tombstones[asset_id] = {
            "id": asset_id,
            "last_path": old["path"],
            "last_sha256": old["sha256"],
            "deleted_generation": generation,
        }

    registry_revision = _registry_revision(generation, new_assets, tombstones)
    persistent = {
        "schema_version": SCHEMA_VERSION,
        "generation": generation,
        "registry_revision": registry_revision,
        "assets": {asset_id: new_assets[asset_id] for asset_id in sorted(new_assets)},
        "tombstones": {asset_id: tombstones[asset_id] for asset_id in sorted(tombstones)},
    }
    if core_changed:
        _write_registry(project, persistent)

    projection = _asset_projection(asset_index, new_assets)
    projection_facts_match = all(
        row["sha256"] == current_rows[row["path"]]["sha256"]
        and row["bytes"] == current_rows[row["path"]]["bytes"]
        for row in projection
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "registry_path": _relative_registry_path(),
        "registry_revision": registry_revision,
        "generation": generation,
        "asset_count": len(projection),
        "asset_projection": projection,
        "tombstones": _public_tombstones(tombstones),
        "asset_index": asset_index,
        "recovery": recovery,
        "refresh": {
            "cache_hits": cache_stats["cache_hits"],
            "cache_misses": cache_stats["cache_misses"],
            "changed_files": changed_files,
            "added_files": added_files,
            "deleted_files": len(remaining_old),
            "renamed_files": renamed_files,
            "ambiguous_renames": ambiguous_renames,
            "parity": projection_facts_match,
        },
    }
