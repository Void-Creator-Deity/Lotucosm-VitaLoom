# -*- coding: utf-8 -*-
"""Deterministic, Qt-free project asset index snapshots.

This module is the Authority for project-relative file identity, content metadata,
scene dependency diagnostics, provenance correlation, and export readiness.
It intentionally builds immutable JSON snapshots; persistence and incremental
refresh belong to a later Gate.
"""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INDEXED_FOLDERS = ("scenes", "scripts", "assets", "addons")
FIXED_FILES = ("project.json", "project.lock.json")
PATH_KEYS = frozenset(
    {
        "sprite_path",
        "prefab_path",
        "icon_path",
        "mesh_path",
        "texture_path",
        "audio_path",
        "asset_path",
        "file_path",
        "source_path",
    }
)
PROVENANCE_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".bmp",
        ".svg",
        ".wav",
        ".mp3",
        ".ogg",
        ".flac",
        ".m4a",
    }
)


def _slash(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative(project: Path, path: Path) -> str | None:
    try:
        return _slash(path.relative_to(project))
    except ValueError:
        try:
            return _slash(path.resolve().relative_to(project))
        except (OSError, ValueError):
            return None


def _file_kind(relative_path: str) -> str:
    head = relative_path.split("/", 1)[0]
    if head in INDEXED_FOLDERS:
        return head[:-1] if head.endswith("s") else head
    return "project"


def _inventory(
    project: Path,
    *,
    digest_cache: Mapping[str, Mapping[str, Any]] | None = None,
    cache_stats: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Return current inventory facts, optionally reusing caller-owned digests.

    The cache is deliberately supplied by a higher Authority rather than retained
    in this Module.  A hit requires path, byte count, and nanosecond mtime to
    match; it is therefore a metadata optimization, not a stronger content claim.
    Default callers retain the Phase 7 full-read behavior and no filesystem writes
    occur here.
    """

    candidates: set[Path] = set()
    for name in FIXED_FILES:
        path = project / name
        if path.is_file():
            candidates.add(path)
    for folder in INDEXED_FOLDERS:
        root = project / folder
        if root.is_dir():
            candidates.update(path for path in root.rglob("*") if path.is_file())

    records: list[dict[str, Any]] = []
    pending_digests: list[tuple[dict[str, Any], Path]] = []
    for path in candidates:
        relative_path = _relative(project, path)
        if relative_path is None:
            continue
        stat = path.stat()
        record: dict[str, Any] = {
            "path": relative_path,
            "kind": _file_kind(relative_path),
            "suffix": path.suffix.lower(),
            "bytes": stat.st_size,
            "sha256": "",
        }
        cached = digest_cache.get(relative_path) if digest_cache is not None else None
        if (
            isinstance(cached, Mapping)
            and cached.get("bytes") == stat.st_size
            and cached.get("mtime_ns") == stat.st_mtime_ns
            and isinstance(cached.get("sha256"), str)
        ):
            record["sha256"] = str(cached["sha256"])
            if cache_stats is not None:
                cache_stats["cache_hits"] = cache_stats.get("cache_hits", 0) + 1
        else:
            pending_digests.append((record, path))
            if cache_stats is not None:
                cache_stats["cache_misses"] = cache_stats.get("cache_misses", 0) + 1
        records.append(record)

    if pending_digests:
        workers = min(16, len(pending_digests))
        if workers == 1:
            digests = [_digest(pending_digests[0][1])]
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                digests = list(executor.map(_digest, (path for _, path in pending_digests)))
        for (record, _), sha256 in zip(pending_digests, digests):
            record["sha256"] = sha256

    return sorted(records, key=lambda row: row["path"])


def _load_provenance(project: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = project / "assets" / "manifest.json"
    summary: dict[str, Any] = {
        "manifest_path": "assets/manifest.json",
        "manifest_status": "missing",
        "proven_assets": 0,
        "unproven_assets": 0,
        "invalid_assets": 0,
        "not_required_assets": 0,
    }
    if not manifest_path.is_file():
        return {}, summary
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        summary.update(
            {
                "manifest_status": "malformed",
                "manifest_error": {
                    "code": "invalid_json",
                    "line": exc.lineno,
                    "column": exc.colno,
                },
            }
        )
        return {}, summary
    except OSError:
        summary.update({"manifest_status": "unreadable", "manifest_error": {"code": "read_error"}})
        return {}, summary
    if not isinstance(data, Mapping) or not isinstance(data.get("sources"), Mapping):
        summary.update({"manifest_status": "invalid", "manifest_error": {"code": "invalid_sources"}})
        return {}, summary
    summary["manifest_status"] = "ok"
    return dict(data["sources"]), summary


def _provenance_for_asset(asset_id: str, sources: Mapping[str, Any]) -> dict[str, Any]:
    relative_to_assets = asset_id.removeprefix("assets/")
    suffix = Path(asset_id).suffix.lower()
    if relative_to_assets == "manifest.json" or suffix not in PROVENANCE_EXTENSIONS:
        return {"status": "not_required"}
    entry = sources.get(relative_to_assets)
    if entry is None:
        return {"status": "unproven"}
    if not isinstance(entry, Mapping):
        return {"status": "invalid"}
    origin = entry.get("origin")
    license_name = entry.get("license")
    if not isinstance(origin, str) or not origin.strip() or not isinstance(license_name, str) or not license_name.strip():
        return {"status": "invalid"}
    result: dict[str, Any] = {
        "status": "proven",
        "origin": origin.strip(),
        "license": license_name.strip(),
    }
    for key in ("generator", "source_url", "author"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    return result


def _asset_rows(
    inventory: list[dict[str, Any]], sources: Mapping[str, Any], provenance_summary: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in inventory:
        path = item["path"]
        if not path.startswith("assets/"):
            continue
        provenance = _provenance_for_asset(path, sources)
        status = provenance["status"]
        key = {
            "proven": "proven_assets",
            "unproven": "unproven_assets",
            "invalid": "invalid_assets",
            "not_required": "not_required_assets",
        }[status]
        provenance_summary[key] += 1
        rows.append(
            {
                "id": path,
                "path": path,
                "bytes": item["bytes"],
                "suffix": item["suffix"],
                "sha256": item["sha256"],
                "provenance": provenance,
            }
        )
    provenance_summary["total_assets"] = len(rows)
    return rows


def resolve_project_asset_reference(
    project_root: str | Path,
    owner_path: str | Path,
    raw_ref: str,
    *,
    generated_target: str | None = None,
) -> dict[str, Any]:
    """Resolve one scene/project reference with the canonical Index semantics.

    The result is JSON-only and deliberately exposes no write location.  Mutation
    Authorities may use it for parity, while their own structured traversal owns
    safe write tokens.
    """

    project = Path(project_root).expanduser().resolve()
    owner = Path(owner_path).expanduser().resolve()
    raw = raw_ref.strip()
    if not raw:
        return {"target": "", "status": "invalid", "exists": False}
    if generated_target is not None:
        candidate = project / generated_target
    else:
        raw_path = Path(raw)
        if raw_path.is_absolute():
            candidate = raw_path
        else:
            project_candidate = project / raw_path
            owner_candidate = owner.parent / raw_path
            if project_candidate.exists():
                candidate = project_candidate
            elif owner_candidate.exists():
                candidate = owner_candidate
            else:
                candidate = project_candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return {"target": _slash(raw), "status": "invalid", "exists": False}
    target = _relative(project, resolved)
    if target is None:
        return {"target": _slash(raw), "status": "outside_project", "exists": resolved.is_file()}
    exists = resolved.is_file()
    return {"target": target, "status": "ok" if exists else "missing", "exists": exists}


def _resolve_reference(
    project: Path,
    scene: Path,
    raw_ref: str,
    *,
    kind: str,
    generated_target: str | None = None,
) -> dict[str, Any]:
    return resolve_project_asset_reference(
        project,
        scene,
        raw_ref,
        generated_target=generated_target,
    )


def _edge(
    *,
    project: Path,
    scene: Path,
    scene_label: str,
    pointer: str,
    kind: str,
    raw_ref: str,
    generated_target: str | None = None,
) -> dict[str, Any]:
    resolved = _resolve_reference(
        project,
        scene,
        raw_ref,
        kind=kind,
        generated_target=generated_target,
    )
    return {
        "scene": scene_label,
        "json_pointer": pointer,
        "kind": kind,
        "raw_ref": raw_ref,
        "target": resolved["target"],
        "status": resolved["status"],
        "exists": resolved["exists"],
    }


def _script_edges(
    value: Any,
    *,
    project: Path,
    scene: Path,
    scene_label: str,
    pointer: str,
) -> Iterator[dict[str, Any]]:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        item_pointer = f"{pointer}[{index}]"
        raw = ""
        generated: str | None = None
        if isinstance(item, Mapping):
            path_value = item.get("path")
            name_value = item.get("name")
            if isinstance(path_value, str) and path_value.strip():
                raw = path_value.strip()
            elif isinstance(name_value, str) and name_value.strip():
                raw = name_value.strip()
                filename = raw if raw.endswith(".py") else f"{raw}.py"
                generated = f"scripts/{filename}"
        elif isinstance(item, str) and item.strip():
            raw = item.strip()
            filename = raw if raw.endswith(".py") else f"{raw}.py"
            generated = f"scripts/{filename}"
        if raw:
            yield _edge(
                project=project,
                scene=scene,
                scene_label=scene_label,
                pointer=item_pointer,
                kind="script",
                raw_ref=raw,
                generated_target=generated,
            )


def _walk_dependencies(
    value: Any,
    *,
    project: Path,
    scene: Path,
    scene_label: str,
    pointer: str,
) -> Iterator[dict[str, Any]]:
    if isinstance(value, Mapping):
        scripts = value.get("scripts")
        if scripts is not None:
            yield from _script_edges(
                scripts,
                project=project,
                scene=scene,
                scene_label=scene_label,
                pointer=f"{pointer}.scripts",
            )
        for key, child in value.items():
            if key == "scripts":
                continue
            child_pointer = f"{pointer}.{key}"
            if isinstance(key, str) and (key in PATH_KEYS or key.endswith("_path")):
                if isinstance(child, str) and child.strip():
                    yield _edge(
                        project=project,
                        scene=scene,
                        scene_label=scene_label,
                        pointer=child_pointer,
                        kind="asset",
                        raw_ref=child.strip(),
                    )
            elif isinstance(child, (Mapping, list)):
                yield from _walk_dependencies(
                    child,
                    project=project,
                    scene=scene,
                    scene_label=scene_label,
                    pointer=child_pointer,
                )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_dependencies(
                child,
                project=project,
                scene=scene,
                scene_label=scene_label,
                pointer=f"{pointer}[{index}]",
            )


def _dependency_snapshot(project: Path) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    malformed_scenes: list[dict[str, Any]] = []

    project_file = project / "project.json"
    if project_file.is_file():
        try:
            project_data = json.loads(project_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            project_data = {}
        active_scene = project_data.get("active_scene") if isinstance(project_data, Mapping) else None
        if isinstance(active_scene, str) and active_scene.strip():
            raw = active_scene.strip()
            clean = _slash(raw)
            generated = clean if clean.startswith("scenes/") else f"scenes/{clean}"
            edges.append(
                _edge(
                    project=project,
                    scene=project_file,
                    scene_label="project.json",
                    pointer="$.active_scene",
                    kind="active_scene",
                    raw_ref=raw,
                    generated_target=generated,
                )
            )

    scenes_root = project / "scenes"
    if scenes_root.is_dir():
        for scene in sorted(scenes_root.rglob("*.pond")):
            scene_label = _relative(project, scene) or _slash(scene)
            try:
                data = json.loads(scene.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                malformed_scenes.append(
                    {
                        "scene": scene_label,
                        "error": "invalid_json",
                        "line": exc.lineno,
                        "column": exc.colno,
                    }
                )
                continue
            except OSError:
                malformed_scenes.append({"scene": scene_label, "error": "read_error"})
                continue
            edges.extend(
                _walk_dependencies(
                    data,
                    project=project,
                    scene=scene,
                    scene_label=scene_label,
                    pointer="$",
                )
            )

    edges.sort(
        key=lambda item: (
            item["scene"],
            item["json_pointer"],
            item["kind"],
            item["raw_ref"],
            item["target"],
        )
    )
    malformed_scenes.sort(key=lambda item: item["scene"])
    by_kind: dict[str, int] = {}
    missing_by_kind: dict[str, int] = {}
    outside_by_kind: dict[str, int] = {}
    invalid_by_kind: dict[str, int] = {}
    missing_scripts: set[str] = set()
    missing_assets: set[str] = set()
    outside_project: set[str] = set()
    invalid_references: set[str] = set()
    for item in edges:
        kind = item["kind"]
        by_kind[kind] = by_kind.get(kind, 0) + 1
        status = item["status"]
        if status == "missing":
            missing_by_kind[kind] = missing_by_kind.get(kind, 0) + 1
            if kind == "script":
                missing_scripts.add(item["target"])
            elif kind == "asset":
                missing_assets.add(item["target"])
        elif status == "outside_project":
            outside_by_kind[kind] = outside_by_kind.get(kind, 0) + 1
            outside_project.add(item["raw_ref"])
        elif status == "invalid":
            invalid_by_kind[kind] = invalid_by_kind.get(kind, 0) + 1
            invalid_references.add(item["raw_ref"])

    missing_total = sum(missing_by_kind.values())
    outside_total = sum(outside_by_kind.values())
    invalid_total = sum(invalid_by_kind.values())
    return {
        "edges": edges,
        "total_edges": len(edges),
        "by_kind": dict(sorted(by_kind.items())),
        "missing_scripts": sorted(missing_scripts),
        "missing_assets": sorted(missing_assets),
        "missing_total": missing_total,
        "missing_by_kind": dict(sorted(missing_by_kind.items())),
        "outside_project": sorted(outside_project),
        "outside_project_total": outside_total,
        "outside_project_by_kind": dict(sorted(outside_by_kind.items())),
        "invalid_references": sorted(invalid_references),
        "invalid_total": invalid_total,
        "invalid_by_kind": dict(sorted(invalid_by_kind.items())),
        "malformed_scenes": malformed_scenes,
        "ready": missing_total == 0 and outside_total == 0 and invalid_total == 0 and not malformed_scenes,
    }


def _export_snapshot(
    inventory: list[dict[str, Any]], dependencies: Mapping[str, Any], provenance: Mapping[str, Any]
) -> dict[str, Any]:
    warnings: list[str] = []
    if dependencies["missing_total"]:
        warnings.append("export_closure_has_missing_dependencies")
    if dependencies["outside_project_total"]:
        warnings.append("export_closure_has_outside_project_dependencies")
    if dependencies["invalid_total"]:
        warnings.append("export_closure_has_invalid_dependencies")
    if dependencies["malformed_scenes"]:
        warnings.append("export_closure_has_malformed_scenes")
    if provenance.get("unproven_assets") or provenance.get("invalid_assets"):
        warnings.append("asset_provenance_incomplete")
    metadata = [
        {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
        for row in inventory
    ]
    return {
        "files": [row["path"] for row in inventory],
        "file_count": len(inventory),
        "file_metadata": metadata,
        "warnings": warnings,
        "ready": bool(dependencies["ready"]),
    }


def build_project_asset_index(
    project_root: str | Path,
    *,
    digest_cache: Mapping[str, Mapping[str, Any]] | None = None,
    cache_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build a fresh deterministic JSON-only asset index snapshot.

    The project root must exist and be a directory. Project manifests are indexed
    as files but their presence is not fabricated by this Module.  Higher-level
    persistent Authorities may provide a metadata digest cache and mutable
    counters; neither changes snapshot facts or causes persistence here.
    """

    project = Path(project_root).expanduser().resolve()
    if not project.is_dir():
        raise FileNotFoundError(f"Project root does not exist: {project}")

    inventory = _inventory(project, digest_cache=digest_cache, cache_stats=cache_stats)
    sources, provenance = _load_provenance(project)
    assets = _asset_rows(inventory, sources, provenance)
    dependencies = _dependency_snapshot(project)
    export = _export_snapshot(inventory, dependencies, provenance)
    revision_facts = {
        "schema_version": SCHEMA_VERSION,
        "inventory": inventory,
        "assets": assets,
        "dependencies": dependencies,
        "provenance": provenance,
        "export": export,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "index_revision": _stable_digest(revision_facts),
        "inventory": inventory,
        "file_count": len(inventory),
        "assets": assets,
        "asset_count": len(assets),
        "dependencies": dependencies,
        "provenance": provenance,
        "export": export,
        "coverage": {
            "inventory_files": len(inventory),
            "asset_files": len(assets),
            "dependency_edges": dependencies["total_edges"],
            "malformed_scenes": len(dependencies["malformed_scenes"]),
        },
    }

