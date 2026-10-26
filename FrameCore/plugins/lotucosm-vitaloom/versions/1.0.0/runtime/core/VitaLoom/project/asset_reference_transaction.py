# -*- coding: utf-8 -*-
"""Qt-free Authority for dependency-aware asset file mutations.

The Asset Index owns current dependency/export facts and the Asset Registry owns
persistent identity.  This Module owns the difficult middle: deterministic
reference-impact plans, reversible multi-file mutations, and durable guarded
undo/redo receipts.  It intentionally imports no Qt, editor singleton, project
manager, or Command Registry object.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import uuid
from functools import wraps
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from core.VitaLoom.project.command_audit import (
    CommandAuditHistoryError,
    read_project_command_audit_entries,
)
from core.VitaLoom.project.asset_transaction_interlock import (
    AssetTransactionInterlockError,
)
from core.VitaLoom.project.project_write_authority import (
    ProjectWriteInterlockError,
    project_write_interlock,
)
from core.VitaLoom.project.asset_index import (
    PATH_KEYS,
    build_project_asset_index,
    resolve_project_asset_reference,
)
from core.VitaLoom.project.asset_registry import (
    load_project_asset_registry,
    refresh_project_asset_registry,
)

SCHEMA_VERSION = 1
TRANSACTION_DIRECTORY = ".vitaloom/asset_transactions"
PRUNE_DIRECTORY = ".vitaloom/asset_transaction_prunes"


class AssetReferenceTransactionError(RuntimeError):
    """Structured failure raised when a transaction cannot safely proceed."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = str(code)
        self.details = dict(details or {})


def _slash(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _preflight_asset_reference_apply(project: Path, plan: Mapping[str, Any]) -> None:
    """Reject an obviously non-mutating apply request before materializing lock metadata.

    The full project/digest preflight still runs after interlock acquisition.  This
    narrow check preserves the established zero-write contract for a plan that is
    already declared blocked by its read-only planner.
    """

    if str(plan.get("project_path")) != str(project):
        raise AssetReferenceTransactionError("asset_transaction_project_mismatch", "Plan belongs to a different project")
    if not bool(plan.get("ready")):
        raise AssetReferenceTransactionError(
            "asset_references_blocking",
            "Asset mutation is blocked by live or non-rewritable references",
            details={"blocked_references": list(plan.get("blocked_references") or [])},
        )


def _mutation_interlocked(authority_action: str, *, preflight: Any | None = None):
    """Guard exactly one public durable mutation seam with the project interlock."""

    def decorate(function):
        @wraps(function)
        def guarded(project_root: str | Path, *args: Any, **kwargs: Any):
            project = _project_path(project_root)
            if preflight is not None:
                preflight(project, *args, **kwargs)
            try:
                with project_write_interlock(
                    project,
                    authority_action=authority_action,
                ):
                    return function(project, *args, **kwargs)
            except AssetTransactionInterlockError as exc:
                raise AssetReferenceTransactionError(exc.code, str(exc), details=exc.details) from exc
            except ProjectWriteInterlockError as exc:
                code = (
                    "asset_transaction_interlock_held"
                    if exc.code == "project_write_interlock_held"
                    else exc.code
                )
                raise AssetReferenceTransactionError(
                    code,
                    str(exc),
                    details=exc.details,
                ) from exc

        return guarded

    return decorate


def _project_path(project_root: str | Path) -> Path:
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir() or not (project / "project.json").is_file():
        raise AssetReferenceTransactionError(
            "project_not_found", "project_root must contain project.json", details={"project_path": str(project)}
        )
    return project


def _relative(project: Path, path: Path) -> str:
    try:
        return _slash(path.resolve().relative_to(project))
    except ValueError as exc:
        raise AssetReferenceTransactionError("asset_path_outside_project", "Path must stay inside the project") from exc


def _project_file(project: Path, value: str, *, must_exist: bool = True) -> Path:
    raw = str(value or "").strip()
    if not raw or Path(raw).is_absolute():
        raise AssetReferenceTransactionError("asset_path_outside_project", "Asset path must be project-relative")
    candidate = (project / raw).resolve()
    _relative(project, candidate)
    if must_exist and not candidate.is_file():
        raise AssetReferenceTransactionError("asset_not_found", "Source asset file does not exist", details={"path": raw})
    return candidate


def _pointer(tokens: list[str | int]) -> str:
    result = "$"
    for token in tokens:
        result += f"[{token}]" if isinstance(token, int) else f".{token}"
    return result


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetReferenceTransactionError(
            "asset_reference_owner_malformed",
            "Reference owner JSON is malformed",
            details={"path": str(path), "line": exc.lineno, "column": exc.colno},
        ) from exc
    except OSError as exc:
        raise AssetReferenceTransactionError("asset_reference_owner_unreadable", "Reference owner cannot be read") from exc


def _write_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _transaction_root(project: Path) -> Path:
    return project / TRANSACTION_DIRECTORY


def _journal_path(project: Path, transaction_id: str) -> Path:
    clean = str(transaction_id or "").strip()
    if not clean or any(character in clean for character in "\\/"):
        raise AssetReferenceTransactionError("invalid_transaction_id", "Invalid transaction id")
    return _transaction_root(project) / f"{clean}.json"


def _read_journal(project: Path, transaction_id: str) -> tuple[Path, dict[str, Any]]:
    """Read one durable receipt only after strict structural validation."""

    journal_path = _journal_path(project, transaction_id)
    if not journal_path.is_file():
        raise AssetReferenceTransactionError("asset_transaction_not_found", "Transaction journal does not exist")
    try:
        data = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetReferenceTransactionError("asset_transaction_malformed", "Transaction journal is unreadable") from exc
    classification, receipt_code = _validate_recovery_journal(data, transaction_id=str(transaction_id))
    if classification is not None:
        raise AssetReferenceTransactionError(
            "asset_transaction_malformed",
            "Transaction journal receipt is structurally invalid",
            details={"receipt_code": str(receipt_code), "classification": str(classification)},
        )
    return journal_path, dict(data)


def _write_journal(path: Path, journal: Mapping[str, Any]) -> None:
    encoded = json.dumps(dict(journal), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_atomic(path, encoded)


def _iter_reference_locations(
    value: Any,
    *,
    project: Path,
    owner: Path,
    owner_label: str,
    tokens: list[str | int],
) -> Iterator[dict[str, Any]]:
    if isinstance(value, Mapping):
        scripts = value.get("scripts")
        if isinstance(scripts, list):
            for index, item in enumerate(scripts):
                script_tokens = [*tokens, "scripts", index]
                if isinstance(item, Mapping):
                    path_value = item.get("path")
                    name_value = item.get("name")
                    if isinstance(path_value, str) and path_value.strip():
                        yield {
                            "owner_path": owner_label,
                            "location_tokens": [*script_tokens, "path"],
                            "json_pointer": _pointer([*script_tokens, "path"]),
                            "kind": "script_path",
                            "raw_ref": path_value.strip(),
                            "generated_target": None,
                        }
                    elif isinstance(name_value, str) and name_value.strip():
                        raw = name_value.strip()
                        filename = raw if raw.endswith(".py") else f"{raw}.py"
                        yield {
                            "owner_path": owner_label,
                            "location_tokens": [*script_tokens, "name"],
                            "json_pointer": _pointer([*script_tokens, "name"]),
                            "kind": "script_name",
                            "raw_ref": raw,
                            "generated_target": f"scripts/{filename}",
                        }
                elif isinstance(item, str) and item.strip():
                    raw = item.strip()
                    filename = raw if raw.endswith(".py") else f"{raw}.py"
                    yield {
                        "owner_path": owner_label,
                        "location_tokens": script_tokens,
                        "json_pointer": _pointer(script_tokens),
                        "kind": "script_name",
                        "raw_ref": raw,
                        "generated_target": f"scripts/{filename}",
                    }
        for key, child in value.items():
            if key == "scripts":
                continue
            child_tokens = [*tokens, str(key)]
            if isinstance(key, str) and (key in PATH_KEYS or key.endswith("_path")):
                if isinstance(child, str) and child.strip():
                    yield {
                        "owner_path": owner_label,
                        "location_tokens": child_tokens,
                        "json_pointer": _pointer(child_tokens),
                        "kind": "asset",
                        "raw_ref": child.strip(),
                        "generated_target": None,
                    }
            elif isinstance(child, (Mapping, list)):
                yield from _iter_reference_locations(
                    child, project=project, owner=owner, owner_label=owner_label, tokens=child_tokens
                )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_reference_locations(
                child, project=project, owner=owner, owner_label=owner_label, tokens=[*tokens, index]
            )


def _all_locations(project: Path, *, strict_malformed: bool = False) -> Iterator[dict[str, Any]]:
    project_file = project / "project.json"
    project_data = _read_json(project_file)
    if isinstance(project_data, Mapping):
        active_scene = project_data.get("active_scene")
        if isinstance(active_scene, str) and active_scene.strip():
            raw = active_scene.strip()
            clean = _slash(raw)
            yield {
                "owner_path": "project.json",
                "location_tokens": ["active_scene"],
                "json_pointer": "$.active_scene",
                "kind": "active_scene",
                "raw_ref": raw,
                "generated_target": clean if clean.startswith("scenes/") else f"scenes/{clean}",
            }
    scenes_root = project / "scenes"
    if not scenes_root.is_dir():
        return
    for owner in sorted(scenes_root.rglob("*.pond")):
        owner_label = _relative(project, owner)
        try:
            data = _read_json(owner)
        except AssetReferenceTransactionError:
            if strict_malformed:
                raise
            continue
        yield from _iter_reference_locations(data, project=project, owner=owner, owner_label=owner_label, tokens=[])


def _replacement_for(location: Mapping[str, Any], *, project: Path, owner: Path, source: Path, target: Path) -> str | None:
    kind = str(location["kind"])
    raw = str(location["raw_ref"])
    target_relative = _relative(project, target)
    if kind == "active_scene":
        if not target_relative.startswith("scenes/"):
            return None
        return target_relative if _slash(raw).startswith("scenes/") else target_relative.removeprefix("scenes/")
    if kind == "script_name":
        if not target_relative.startswith("scripts/"):
            return None
        filename = target_relative.removeprefix("scripts/")
        return filename if raw.endswith(".py") else filename.removesuffix(".py")
    raw_path = Path(raw)
    if raw_path.is_absolute():
        return _slash(target)
    project_candidate = (project / raw_path).resolve()
    if project_candidate == source:
        return target_relative
    owner_candidate = (owner.parent / raw_path).resolve()
    if owner_candidate == source:
        return _slash(os.path.relpath(target, owner.parent))
    return None


def _owner_file(project: Path, owner_path: str) -> Path:
    candidate = (project / owner_path).resolve()
    _relative(project, candidate)
    return candidate


def _set_location(data: Any, tokens: list[str | int], value: str) -> None:
    target = data
    for token in tokens[:-1]:
        target = target[token]
    target[tokens[-1]] = value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _protected(path: str) -> bool:
    return path in {"project.json", "project.lock.json"} or path.startswith(".vitaloom/")


def _retirement_path_fact(project: Path, value: str | None, *, role: str) -> tuple[dict[str, Any], Path | None]:
    """Read one policy input without accepting absolute or escaped paths."""

    raw = str(value or "").strip()
    result: dict[str, Any] = {"requested_path": raw or None, "path": None, "status": "not_requested"}
    if not raw:
        return result, None
    raw_path = Path(raw)
    if raw_path.is_absolute():
        result["status"] = "outside_project"
        return result, None
    try:
        candidate = (project / raw_path).resolve()
        relative = _relative(project, candidate)
    except (OSError, AssetReferenceTransactionError):
        result["status"] = "outside_project"
        return result, None
    result["path"] = relative
    if _protected(relative):
        result["status"] = "protected"
        return result, candidate
    if not candidate.exists():
        result["status"] = "not_found"
        return result, candidate
    if not candidate.is_file():
        result["status"] = "not_file"
        return result, candidate
    result["status"] = "ok"
    result["role"] = role
    return result, candidate


def _retirement_blocker(code: str, *, path: str | None = None, message: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"code": str(code)}
    if path is not None:
        result["path"] = str(path)
    if message is not None:
        result["message"] = str(message)
    return result


def _retirement_index_facts(project: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read existing Index/Registry Authorities without creating Registry state."""

    index = build_project_asset_index(project)
    registry = load_project_asset_registry(project)
    return index, registry


def analyze_asset_retirement_policy(
    project_root: str | Path,
    *,
    source_path: str,
    replacement_path: str | None = None,
) -> dict[str, Any]:
    """Analyze referenced-asset retirement without changing project state.

    This is intentionally a policy/impact Authority, not a mutation plan: it uses
    existing canonical location and replacement-style logic, reads Index/Registry
    facts, and never writes `.pond`, Registry, journal, backup, export, or undo
    state. A future gate may only consume this output after separately proving a
    mutation contract.
    """

    project = _project_path(project_root)
    index, registry = _retirement_index_facts(project)
    source, source_file = _retirement_path_fact(project, source_path, role="source")
    replacement, replacement_file = _retirement_path_fact(project, replacement_path, role="replacement")
    blockers: list[dict[str, Any]] = []
    warnings: list[str] = []
    malformed_owners = [dict(row) for row in index["dependencies"]["malformed_scenes"]]
    inventory = {str(row["path"]): dict(row) for row in index["inventory"]}
    source_asset = inventory.get(str(source.get("path") or ""))
    if source_asset is not None:
        source["asset"] = source_asset

    source_status = str(source["status"])
    if source_status != "ok":
        code = {
            "not_requested": "source_path_required",
            "outside_project": "source_path_outside_project",
            "protected": "source_path_protected",
            "not_found": "source_not_found",
            "not_file": "source_not_file",
        }.get(source_status, "source_path_invalid")
        blockers.append(_retirement_blocker(code, path=source.get("path") or source.get("requested_path")))

    mode = "replace" if replacement_path is not None and str(replacement_path).strip() else "remove"
    if mode == "replace":
        replacement_status = str(replacement["status"])
        if replacement_status != "ok":
            code = {
                "not_requested": "replacement_path_required",
                "outside_project": "replacement_path_outside_project",
                "protected": "replacement_path_protected",
                "not_found": "replacement_not_found",
                "not_file": "replacement_not_file",
            }.get(replacement_status, "replacement_path_invalid")
            blockers.append(_retirement_blocker(code, path=replacement.get("path") or replacement.get("requested_path")))
        elif source.get("path") == replacement.get("path"):
            blockers.append(_retirement_blocker("replacement_same_as_source", path=str(source["path"])))
        else:
            warnings.append("replacement_semantic_compatibility_not_inferred")

    for malformed in malformed_owners:
        blockers.append(
            _retirement_blocker(
                "reference_owner_malformed",
                path=str(malformed.get("scene", "")),
                message=str(malformed.get("error", "malformed_scene")),
            )
        )

    live_references: list[dict[str, Any]] = []
    proposed: list[dict[str, Any]] = []
    blocked_references: list[dict[str, Any]] = []
    if source_status == "ok" and source_file is not None:
        try:
            locations = list(_all_locations(project))
        except AssetReferenceTransactionError as exc:
            blockers.append(_retirement_blocker("project_reference_metadata_malformed", message=exc.code))
            locations = []
        for location in locations:
            owner = _owner_file(project, str(location["owner_path"]))
            resolved = resolve_project_asset_reference(
                project,
                owner,
                str(location["raw_ref"]),
                generated_target=location.get("generated_target"),
            )
            if resolved["status"] != "ok" or resolved["target"] != source["path"]:
                continue
            record = dict(location)
            record.update({"target": resolved["target"], "status": resolved["status"]})
            record.pop("generated_target", None)
            live_references.append(record)
            if mode == "remove":
                blocked = dict(record)
                blocked["reason"] = "removal_reference_semantics_unproven"
                blocked_references.append(blocked)
                continue
            if replacement_file is None or str(replacement.get("status")) != "ok":
                continue
            new_value = _replacement_for(
                record,
                project=project,
                owner=owner,
                source=source_file,
                target=replacement_file,
            )
            if new_value is None:
                blocked = dict(record)
                blocked["reason"] = "reference_style_not_representable"
                blocked_references.append(blocked)
                continue
            edit = dict(record)
            edit["old_value"] = edit.pop("raw_ref")
            edit["new_value"] = new_value
            proposed.append(edit)

    if mode == "remove" and live_references:
        blockers.append(_retirement_blocker("removal_without_replacement_unproven", message="Live references require an explicit future policy"))
    if blocked_references:
        blockers.append(_retirement_blocker("reference_rewrite_not_representable"))

    live_references.sort(key=lambda item: (str(item["owner_path"]), str(item["json_pointer"])))
    proposed.sort(key=lambda item: (str(item["owner_path"]), str(item["json_pointer"])))
    blocked_references.sort(key=lambda item: (str(item["owner_path"]), str(item["json_pointer"])))
    blockers.sort(key=lambda item: (str(item["code"]), str(item.get("path", "")), str(item.get("message", ""))))

    if blockers:
        decision = "refused"
        ready = False
    elif mode == "remove":
        decision = "unreferenced_delete_available"
        ready = False
    elif not live_references:
        decision = "unreferenced_delete_available"
        ready = False
    else:
        decision = "replacement_candidate"
        ready = True
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "mode": mode,
        "decision": decision,
        "ready_for_future_transaction": ready,
        "source": source,
        "replacement": replacement,
        "current_facts": {
            "asset_index": {
                "index_revision": index["index_revision"],
                "asset_count": index["asset_count"],
                "dependency_ready": index["dependencies"]["ready"],
                "export_ready": index["export"]["ready"],
            },
            "asset_registry": {
                "status": registry["status"],
                "registry_revision": registry.get("registry_revision"),
                "generation": registry.get("generation"),
            },
        },
        "live_references": live_references,
        "proposed_reference_edits": proposed,
        "blocked_references": blocked_references,
        "malformed_owners": malformed_owners,
        "blockers": blockers,
        "warnings": sorted(set(warnings)),
        "non_goals": [
            "No reference, asset, Registry, journal, backup, export, or undo mutation occurs during analysis.",
            "No generic remove-without-replacement semantics are inferred.",
            "No referenced asset deletion is authorized by this analysis.",
        ],
    }


def plan_asset_reference_mutation(
    project_root: str | Path,
    *,
    operation: str,
    source_path: str,
    target_path: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-only, non-mutating reference-impact plan.

    ``replace_referenced`` is deliberately narrower than a generic asset
    replacement: it rewrites only representable live references to an existing
    project file, then retires the source into the Registry tombstones.  It
    never copies, transforms, or otherwise mutates the replacement bytes.
    """

    project = _project_path(project_root)
    op = str(operation or "").strip().lower()
    if op not in {"rename", "delete", "replace_referenced"}:
        raise AssetReferenceTransactionError(
            "invalid_operation", "operation must be rename, delete, or replace_referenced"
        )
    source = _project_file(project, source_path)
    source_relative = _relative(project, source)
    if _protected(source_relative):
        raise AssetReferenceTransactionError("asset_path_protected", "Project metadata cannot be mutated as an asset")

    target: Path | None = None
    target_relative: str | None = None
    target_digest: str | None = None
    if op == "rename":
        target = _project_file(project, str(target_path or ""), must_exist=False)
        target_relative = _relative(project, target)
        if _protected(target_relative):
            raise AssetReferenceTransactionError("asset_path_protected", "Project metadata cannot be mutated as an asset")
        if target.exists():
            raise AssetReferenceTransactionError("asset_exists", "Target asset already exists", details={"path": target_relative})
        if not target.parent.is_dir():
            raise AssetReferenceTransactionError("asset_target_folder_not_found", "Target folder must already exist")
    elif op == "replace_referenced":
        target = _project_file(project, str(target_path or ""))
        target_relative = _relative(project, target)
        if _protected(target_relative):
            raise AssetReferenceTransactionError("asset_path_protected", "Project metadata cannot be mutated as an asset")
        if target == source:
            raise AssetReferenceTransactionError(
                "asset_replacement_same_as_source", "Replacement asset must differ from the source asset"
            )
        target_digest = _digest_file(target)

    edits: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    for location in _all_locations(project, strict_malformed=op == "replace_referenced"):
        owner = _owner_file(project, str(location["owner_path"]))
        resolved = resolve_project_asset_reference(
            project, owner, str(location["raw_ref"]), generated_target=location.get("generated_target")
        )
        if resolved["status"] != "ok" or resolved["target"] != source_relative:
            continue
        record = dict(location)
        record.update({"target": resolved["target"], "status": resolved["status"]})
        if op == "delete":
            blocked.append(record)
            continue
        replacement = _replacement_for(record, project=project, owner=owner, source=source, target=target)
        if replacement is None:
            record["reason"] = "reference_style_not_representable"
            blocked.append(record)
            continue
        record["old_value"] = record.pop("raw_ref")
        record["new_value"] = replacement
        record.pop("generated_target", None)
        edits.append(record)

    owner_digests: dict[str, str] = {}
    for item in [*edits, *blocked]:
        owner_label = str(item["owner_path"])
        owner = _owner_file(project, owner_label)
        owner_digests.setdefault(owner_label, _digest_file(owner))
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "operation": op,
        "source_path": source_relative,
        "target_path": target_relative,
        "source_sha256": _digest_file(source),
        "target_sha256": target_digest,
        "reference_edits": sorted(edits, key=lambda item: (item["owner_path"], item["json_pointer"])),
        "blocked_references": sorted(blocked, key=lambda item: (item["owner_path"], item["json_pointer"])),
        "owner_digests": {path: owner_digests[path] for path in sorted(owner_digests)},
        "malformed_scenes": malformed,
        "ready": not blocked,
    }

def _verify_replacement_reference_facts(project: Path, plan: Mapping[str, Any]) -> None:
    """Refuse a stale replacement plan instead of leaving a newly added reference dangling."""

    current = plan_asset_reference_mutation(
        project,
        operation="replace_referenced",
        source_path=str(plan["source_path"]),
        target_path=str(plan.get("target_path") or ""),
    )
    expected = {
        "source_sha256": plan.get("source_sha256"),
        "target_sha256": plan.get("target_sha256"),
        "reference_edits": list(plan.get("reference_edits") or []),
        "blocked_references": list(plan.get("blocked_references") or []),
        "owner_digests": dict(plan.get("owner_digests") or {}),
    }
    observed = {key: current.get(key) for key in expected}
    if not current["ready"] or observed != expected:
        raise AssetReferenceTransactionError(
            "asset_transaction_conflict",
            "Referenced asset replacement facts changed since planning",
            details={
                "blocked_references": list(current.get("blocked_references") or []),
                "reference_edit_count": len(current.get("reference_edits") or []),
            },
        )


def _verify_plan(project: Path, plan: Mapping[str, Any], *, state: str) -> None:
    source = _project_file(project, str(plan["source_path"]), must_exist=state in {"before", "redo"})
    expected_source = str(plan["source_sha256"])
    if state in {"before", "redo"} and _digest_file(source) != expected_source:
        raise AssetReferenceTransactionError("asset_transaction_conflict", "Source asset changed since planning")

    operation = str(plan.get("operation"))
    if operation not in {"rename", "delete", "replace_referenced"}:
        raise AssetReferenceTransactionError("invalid_operation", "Unsupported asset transaction operation")
    if operation == "rename":
        target = _project_file(project, str(plan.get("target_path") or ""), must_exist=False)
        if target.exists():
            raise AssetReferenceTransactionError(
                "asset_transaction_conflict",
                "Rename target was created since planning",
                details={"path": _relative(project, target)},
            )
    elif operation == "replace_referenced":
        target = _project_file(project, str(plan.get("target_path") or ""))
        expected_target = str(plan.get("target_sha256") or "")
        if not expected_target or _digest_file(target) != expected_target:
            raise AssetReferenceTransactionError(
                "asset_transaction_conflict",
                "Replacement asset changed since planning",
                details={"path": _relative(project, target)},
            )

    expected = dict(plan.get("owner_digests") or {})
    for owner_path, digest in expected.items():
        owner = _owner_file(project, str(owner_path))
        if _digest_file(owner) != str(digest):
            raise AssetReferenceTransactionError(
                "asset_transaction_conflict", "Reference owner changed since planning", details={"path": owner_path}
            )

def _build_file_records(project: Path, edits: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_owner: dict[str, list[Mapping[str, Any]]] = {}
    for edit in edits:
        by_owner.setdefault(str(edit["owner_path"]), []).append(edit)
    records: list[dict[str, Any]] = []
    for owner_path in sorted(by_owner):
        owner = _owner_file(project, owner_path)
        before = owner.read_bytes()
        data = _read_json(owner)
        for edit in by_owner[owner_path]:
            _set_location(data, list(edit["location_tokens"]), str(edit["new_value"]))
        after = _json_bytes(data)
        records.append(
            {
                "path": owner_path,
                "before_sha256": _digest_bytes(before),
                "after_sha256": _digest_bytes(after),
                "before_base64": base64.b64encode(before).decode("ascii"),
                "after_base64": base64.b64encode(after).decode("ascii"),
            }
        )
    return records


def _registry_asset_id(snapshot: Mapping[str, Any], path: str) -> str:
    for row in snapshot.get("asset_projection", []):
        if row.get("path") == path:
            return str(row["asset_id"])
    raise AssetReferenceTransactionError("asset_registry_identity_missing", "Registry has no identity for source asset")


def _decode(record: Mapping[str, Any], key: str) -> bytes:
    return base64.b64decode(str(record[key]).encode("ascii"))


def _apply_prepared(project: Path, journal_path: Path, journal: dict[str, Any]) -> dict[str, Any]:
    plan = dict(journal["plan"])
    source = _project_file(project, str(plan["source_path"]))
    operation = str(plan["operation"])
    target = (
        _project_file(project, str(plan.get("target_path") or ""), must_exist=False)
        if operation == "rename"
        else None
    )
    replacement = (
        _project_file(project, str(plan.get("target_path") or ""))
        if operation == "replace_referenced"
        else None
    )
    if operation == "rename" and target is not None and target.exists():
        raise AssetReferenceTransactionError(
            "asset_transaction_conflict",
            "Rename target was created before transaction apply",
            details={"path": _relative(project, target)},
        )
    if operation == "replace_referenced" and (
        replacement is None or _digest_file(replacement) != str(plan.get("target_sha256") or "")
    ):
        raise AssetReferenceTransactionError("asset_transaction_conflict", "Replacement asset changed before transaction apply")

    try:
        if operation == "rename":
            source.replace(target)
            for file_record in journal["files"]:
                _write_atomic(_owner_file(project, str(file_record["path"])), _decode(file_record, "after_base64"))
            registry = refresh_project_asset_registry(
                project, rename_hints={str(plan["source_path"]): str(plan["target_path"])}
            )
        else:
            backup = _transaction_root(project) / f"{journal['transaction_id']}.asset"
            if backup.exists():
                if not backup.is_file() or _digest_file(backup) != str(plan["source_sha256"]):
                    raise AssetReferenceTransactionError(
                        "asset_transaction_backup_changed",
                        "Asset backup changed after transaction planning",
                        details={"path": _relative(project, backup)},
                    )
            else:
                _write_atomic(backup, source.read_bytes())
            journal["asset_backup"] = _relative(project, backup)
            _write_journal(journal_path, journal)
            source.unlink()
            if operation == "replace_referenced":
                for file_record in journal["files"]:
                    _write_atomic(_owner_file(project, str(file_record["path"])), _decode(file_record, "after_base64"))
            registry = refresh_project_asset_registry(project)
        journal["state"] = "applied"
        journal["registry_revision_after"] = registry["registry_revision"]
        _write_journal(journal_path, journal)
        return {"state": "applied", "registry": registry}
    except Exception as exc:
        try:
            for file_record in journal.get("files", []):
                _write_atomic(_owner_file(project, str(file_record["path"])), _decode(file_record, "before_base64"))
            if operation == "rename" and target is not None and target.is_file() and not source.exists():
                target.replace(source)
                refresh_project_asset_registry(
                    project, rename_hints={str(plan["target_path"]): str(plan["source_path"])}
                )
            elif operation in {"delete", "replace_referenced"} and not source.exists() and journal.get("asset_backup"):
                backup = _owner_file(project, str(journal["asset_backup"]))
                if backup.is_file() and _digest_file(backup) == str(plan["source_sha256"]):
                    _write_atomic(source, backup.read_bytes())
                    refresh_project_asset_registry(
                        project, restore_hints={str(journal["asset_id"]): str(plan["source_path"])}
                    )
        finally:
            journal["state"] = "failed_recoverable"
            _write_journal(journal_path, journal)
        if isinstance(exc, AssetReferenceTransactionError):
            raise
        raise AssetReferenceTransactionError(
            "asset_transaction_apply_failed",
            "Asset transaction failed and was compensated",
            details={"error": type(exc).__name__},
        ) from exc

@_mutation_interlocked("asset_reference.apply", preflight=_preflight_asset_reference_apply)
def apply_asset_reference_mutation(project_root: str | Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Apply a prepared plan and persist a durable receipt before mutation."""

    project = _project_path(project_root)
    if str(plan.get("project_path")) != str(project):
        raise AssetReferenceTransactionError("asset_transaction_project_mismatch", "Plan belongs to a different project")
    if not bool(plan.get("ready")):
        raise AssetReferenceTransactionError(
            "asset_references_blocking", "Asset mutation is blocked by live or non-rewritable references", details={"blocked_references": list(plan.get("blocked_references") or [])}
        )
    _verify_plan(project, plan, state="before")
    if str(plan.get("operation")) == "replace_referenced":
        _verify_replacement_reference_facts(project, plan)
    registry_before = refresh_project_asset_registry(project)
    asset_id = _registry_asset_id(registry_before, str(plan["source_path"]))
    transaction_id = uuid.uuid4().hex
    journal_path = _journal_path(project, transaction_id)
    journal = {
        "schema_version": SCHEMA_VERSION,
        "transaction_id": transaction_id,
        "state": "prepared",
        "plan": dict(plan),
        "asset_id": asset_id,
        "files": _build_file_records(project, list(plan.get("reference_edits") or [])),
    }
    _write_journal(journal_path, journal)
    result = _apply_prepared(project, journal_path, journal)
    return {
        "schema_version": SCHEMA_VERSION,
        "transaction_id": transaction_id,
        "state": result["state"],
        "operation": plan["operation"],
        "source_path": plan["source_path"],
        "target_path": plan.get("target_path"),
        "asset_id": asset_id,
        "reference_edits": list(plan.get("reference_edits") or []),
        "registry": result["registry"],
    }


def _verify_file_state(project: Path, records: list[Mapping[str, Any]], key: str) -> None:
    for record in records:
        owner = _owner_file(project, str(record["path"]))
        if _digest_file(owner) != str(record[key]):
            raise AssetReferenceTransactionError("asset_transaction_conflict", "Reference owner changed after transaction", details={"path": record["path"]})


@_mutation_interlocked("asset_reference.undo")
def undo_asset_reference_mutation(project_root: str | Path, transaction_id: str) -> dict[str, Any]:
    """Guardedly restore a completed transaction from its durable receipt."""

    project = _project_path(project_root)
    journal_path, journal = _read_journal(project, transaction_id)
    if journal.get("state") != "applied":
        raise AssetReferenceTransactionError("asset_transaction_not_applied", "Only an applied transaction can be undone")
    plan = dict(journal["plan"])
    operation = str(plan["operation"])
    source = _project_file(project, str(plan["source_path"]), must_exist=False)
    target = _project_file(project, str(plan.get("target_path") or ""), must_exist=False) if operation == "rename" else None
    _verify_file_state(project, list(journal.get("files") or []), "after_sha256")
    if operation == "rename":
        if source.exists():
            raise AssetReferenceTransactionError(
                "asset_transaction_conflict",
                "Original asset path was recreated after transaction",
                details={"path": str(plan["source_path"])},
            )
        if target is None or not target.is_file() or _digest_file(target) != str(plan["source_sha256"]):
            raise AssetReferenceTransactionError("asset_transaction_conflict", "Renamed asset changed after transaction")
        target.replace(source)
        for record in journal["files"]:
            _write_atomic(_owner_file(project, str(record["path"])), _decode(record, "before_base64"))
        registry = refresh_project_asset_registry(
            project, rename_hints={str(plan["target_path"]): str(plan["source_path"])}
        )
    else:
        if source.exists():
            raise AssetReferenceTransactionError("asset_transaction_conflict", "Deleted asset path was recreated")
        if operation == "replace_referenced":
            replacement = _project_file(project, str(plan.get("target_path") or ""))
            if _digest_file(replacement) != str(plan.get("target_sha256") or ""):
                raise AssetReferenceTransactionError("asset_transaction_conflict", "Replacement asset changed after transaction")
        backup = _owner_file(project, str(journal.get("asset_backup") or ""))
        if not backup.is_file() or _digest_file(backup) != str(plan["source_sha256"]):
            raise AssetReferenceTransactionError("asset_transaction_backup_missing", "Delete backup is unavailable or changed")
        _write_atomic(source, backup.read_bytes())
        if operation == "replace_referenced":
            for record in journal["files"]:
                _write_atomic(_owner_file(project, str(record["path"])), _decode(record, "before_base64"))
        registry = refresh_project_asset_registry(
            project, restore_hints={str(journal["asset_id"]): str(plan["source_path"])}
        )
    journal["state"] = "undone"
    journal["registry_revision_undone"] = registry["registry_revision"]
    _write_journal(journal_path, journal)
    return {
        "transaction_id": str(transaction_id),
        "state": "undone",
        "asset_id": journal["asset_id"],
        "registry": registry,
    }

@_mutation_interlocked("asset_reference.redo")
def redo_asset_reference_mutation(project_root: str | Path, transaction_id: str) -> dict[str, Any]:
    """Guardedly replay an undone transaction using the original durable receipt."""

    project = _project_path(project_root)
    journal_path, journal = _read_journal(project, transaction_id)
    if journal.get("state") != "undone":
        raise AssetReferenceTransactionError("asset_transaction_not_undone", "Only an undone transaction can be redone")
    plan = dict(journal["plan"])
    source = _project_file(project, str(plan["source_path"]))
    _verify_file_state(project, list(journal.get("files") or []), "before_sha256")
    if _digest_file(source) != str(plan["source_sha256"]):
        raise AssetReferenceTransactionError("asset_transaction_conflict", "Source asset changed after undo")
    operation = str(plan["operation"])
    if operation in {"delete", "replace_referenced"}:
        backup = _owner_file(project, str(journal.get("asset_backup") or ""))
        if not backup.is_file() or _digest_file(backup) != str(plan["source_sha256"]):
            raise AssetReferenceTransactionError(
                "asset_transaction_backup_changed",
                "Asset backup changed after undo",
                details={"path": str(journal.get("asset_backup") or "")},
            )
    if operation == "replace_referenced":
        replacement = _project_file(project, str(plan.get("target_path") or ""))
        if _digest_file(replacement) != str(plan.get("target_sha256") or ""):
            raise AssetReferenceTransactionError("asset_transaction_conflict", "Replacement asset changed after undo")
    journal["state"] = "redoing"
    _write_journal(journal_path, journal)
    result = _apply_prepared(project, journal_path, journal)
    return {
        "transaction_id": str(transaction_id),
        "state": result["state"],
        "asset_id": journal["asset_id"],
        "registry": result["registry"],
    }

TERMINAL_TRANSACTION_STATES = frozenset({"applied", "undone", "failed_acknowledged"})
RECOVERY_TRANSACTION_STATES = frozenset({"prepared", "redoing", "failed_recoverable"})


def _inspection_result(
    project: Path,
    *,
    transaction_id: str,
    journal_path: Path,
    journal_state: str | None,
    classification: str,
    recovery_required: bool,
    plan: Mapping[str, Any] | None = None,
    file_facts: list[dict[str, Any]] | None = None,
    legal_actions: list[str] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, JSON-only recovery inspection payload."""

    facts = sorted(list(file_facts or []), key=lambda item: (str(item["path"]), str(item["role"])))
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "transaction_id": str(transaction_id),
        "journal_path": _relative(project, journal_path),
        "journal_state": journal_state,
        "classification": str(classification),
        "recovery_required": bool(recovery_required),
        "plan": dict(plan or {}),
        "affected_paths": sorted({str(item["path"]) for item in facts} | {_relative(project, journal_path)}),
        "file_facts": facts,
        "legal_actions": sorted(str(action) for action in (legal_actions or [])),
        "conflicts": sorted(list(conflicts or []), key=lambda item: (str(item.get("path", "")), str(item.get("code", "")))),
    }


def _inspection_conflict(path: str, role: str, *, expected: str | None, current: str | None, code: str = "digest_mismatch") -> dict[str, Any]:
    return {
        "code": code,
        "path": str(path),
        "role": str(role),
        "expected_sha256": expected,
        "current_sha256": current,
    }


def _inspection_project_file(project: Path, path: str) -> Path | None:
    """Return a project-contained observation path, never trusting journal input."""

    try:
        return _project_file(project, path, must_exist=False)
    except AssetReferenceTransactionError:
        return None


def _observe_recovery_file(
    project: Path,
    *,
    path: str,
    role: str,
    expected_before: str | None,
    expected_after: str | None,
) -> tuple[dict[str, Any], str]:
    """Observe one durable receipt path without allowing it to escape the project."""

    candidate = _inspection_project_file(project, path)
    if candidate is None:
        fact = {
            "path": str(path),
            "role": str(role),
            "exists": False,
            "current_sha256": None,
            "expected_before_sha256": expected_before,
            "expected_after_sha256": expected_after,
            "status": "invalid_path",
        }
        return fact, "invalid_path"
    try:
        exists = candidate.exists()
        if exists and not candidate.is_file():
            fact = {
                "path": str(path),
                "role": str(role),
                "exists": True,
                "current_sha256": None,
                "expected_before_sha256": expected_before,
                "expected_after_sha256": expected_after,
                "status": "not_regular_file",
            }
            return fact, "not_regular_file"
        current = _digest_file(candidate) if exists else None
    except OSError:
        fact = {
            "path": str(path),
            "role": str(role),
            "exists": bool(candidate.exists()),
            "current_sha256": None,
            "expected_before_sha256": expected_before,
            "expected_after_sha256": expected_after,
            "status": "unreadable",
        }
        return fact, "unreadable"
    if current == expected_before:
        status = "before"
    elif current == expected_after:
        status = "after"
    else:
        status = "other"
    fact = {
        "path": str(path),
        "role": str(role),
        "exists": exists,
        "current_sha256": current,
        "expected_before_sha256": expected_before,
        "expected_after_sha256": expected_after,
        "status": status,
    }
    return fact, status


def _recovery_plan_summary(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Expose only stable plan facts needed by operator inspection."""

    owner_digests = plan.get("owner_digests")
    return {
        "operation": plan.get("operation"),
        "source_path": plan.get("source_path"),
        "target_path": plan.get("target_path"),
        "source_sha256": plan.get("source_sha256"),
        "target_sha256": plan.get("target_sha256"),
        "owner_digests": {
            str(path): str(owner_digests[path])
            for path in sorted(owner_digests)
        }
        if isinstance(owner_digests, Mapping)
        else {},
    }


def _is_canonical_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_safe_receipt_project_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != _slash(value):
        return False
    if value.startswith("/") or Path(value).is_absolute():
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts) and parts[0] != ".vitaloom"


def _is_canonical_base64(value: Any, digest: Any) -> bool:
    if not isinstance(value, str) or not _is_canonical_sha256(digest):
        return False
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError):
        return False
    return base64.b64encode(decoded).decode("ascii") == value and _digest_bytes(decoded) == digest


def _validate_recovery_journal(journal: Any, *, transaction_id: str) -> tuple[str | None, str | None]:
    """Validate all durable receipt facts before any consumer acts on them.

    The result form is deliberately shared with read-only recovery inspection:
    callers can surface deterministic malformed/unsupported/unknown classifications,
    while write-capable readers turn every non-null result into a structured refusal.
    """

    if not isinstance(journal, Mapping):
        return "malformed", "journal_not_object"
    if journal.get("schema_version") != SCHEMA_VERSION:
        return ("unsupported_schema", "schema_unsupported") if "schema_version" in journal else ("malformed", "schema_missing")
    if not isinstance(journal.get("transaction_id"), str) or journal["transaction_id"] != str(transaction_id):
        return "malformed", "transaction_id_mismatch"
    if not transaction_id or any(character in transaction_id for character in "\\/"):
        return "malformed", "transaction_id_invalid"

    allowed_root = {
        "schema_version", "transaction_id", "state", "plan", "asset_id", "files",
        "asset_backup", "registry_revision_after", "registry_revision_undone", "recovery_resolution",
    }
    if any(key not in allowed_root for key in journal):
        return "malformed", "journal_fields_unknown"
    state = journal.get("state")
    if not isinstance(state, str) or not state:
        return "malformed", "state_missing"
    if state not in TERMINAL_TRANSACTION_STATES | RECOVERY_TRANSACTION_STATES:
        return "unknown_state", "state_unknown"
    if not isinstance(journal.get("asset_id"), str) or not journal["asset_id"].strip():
        return "malformed", "asset_id_invalid"
    for revision_key in ("registry_revision_after", "registry_revision_undone"):
        if revision_key in journal and not _is_canonical_sha256(journal[revision_key]):
            return "malformed", "registry_revision_invalid"
    if "recovery_resolution" in journal and not isinstance(journal["recovery_resolution"], Mapping):
        return "malformed", "recovery_resolution_invalid"

    plan = journal.get("plan")
    expected_plan_fields = {
        "schema_version", "project_path", "operation", "source_path", "target_path", "source_sha256",
        "target_sha256", "reference_edits", "blocked_references", "owner_digests", "malformed_scenes", "ready",
    }
    if not isinstance(plan, Mapping) or set(plan) != expected_plan_fields:
        return "malformed", "plan_fields_invalid"
    if plan.get("schema_version") != SCHEMA_VERSION or not isinstance(plan.get("project_path"), str) or not plan["project_path"]:
        return "malformed", "plan_schema_or_project_invalid"
    operation = plan.get("operation")
    if operation not in {"rename", "delete", "replace_referenced"}:
        return "malformed", "plan_operation_invalid"
    source_path = plan.get("source_path")
    if not _is_safe_receipt_project_path(source_path) or not _is_canonical_sha256(plan.get("source_sha256")):
        return "malformed", "plan_source_invalid"
    target_path = plan.get("target_path")
    target_digest = plan.get("target_sha256")
    if operation == "delete":
        if target_path is not None or target_digest is not None:
            return "malformed", "delete_target_invalid"
    elif not _is_safe_receipt_project_path(target_path) or target_path == source_path:
        return "malformed", "plan_target_invalid"
    elif operation == "rename" and target_digest is not None:
        return "malformed", "rename_target_digest_invalid"
    elif operation == "replace_referenced" and not _is_canonical_sha256(target_digest):
        return "malformed", "replace_target_digest_invalid"
    for list_key in ("reference_edits", "blocked_references", "malformed_scenes"):
        if not isinstance(plan[list_key], list):
            return "malformed", "plan_list_invalid"
    if not isinstance(plan.get("owner_digests"), Mapping) or plan.get("ready") is not True:
        return "malformed", "plan_owner_or_ready_invalid"
    for owner_path, owner_digest in plan["owner_digests"].items():
        if not _is_safe_receipt_project_path(owner_path) or not _is_canonical_sha256(owner_digest):
            return "malformed", "plan_owner_digest_invalid"

    has_backup = "asset_backup" in journal
    if operation == "rename":
        if has_backup:
            return "malformed", "rename_backup_invalid"
    else:
        expected_backup = f"{TRANSACTION_DIRECTORY}/{transaction_id}.asset"
        if has_backup and journal.get("asset_backup") != expected_backup:
            return "malformed", "asset_backup_invalid"
        if state in {"applied", "undone", "redoing"} and not has_backup:
            return "malformed", "asset_backup_missing"

    files = journal.get("files")
    if not isinstance(files, list):
        return "malformed", "files_invalid"
    seen_paths: set[str] = set()
    expected_record_fields = {"path", "before_sha256", "after_sha256", "before_base64", "after_base64"}
    for record in files:
        if not isinstance(record, Mapping) or set(record) != expected_record_fields:
            return "malformed", "file_record_invalid"
        path = record.get("path")
        if not _is_safe_receipt_project_path(path):
            return "malformed", "file_record_path_invalid"
        if path in seen_paths:
            return "malformed", "file_record_duplicate_path"
        seen_paths.add(path)
        if not _is_canonical_base64(record.get("before_base64"), record.get("before_sha256")):
            return "malformed", "file_record_before_payload_invalid"
        if not _is_canonical_base64(record.get("after_base64"), record.get("after_sha256")):
            return "malformed", "file_record_after_payload_invalid"
    return None, None

def _inspect_valid_recovery_journal(project: Path, transaction_id: str, journal_path: Path, journal: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect one structurally valid journal using only current digest evidence."""

    plan = dict(journal["plan"])
    operation = str(plan["operation"])
    source_path = str(plan["source_path"])
    source_digest = str(plan["source_sha256"])
    facts: list[dict[str, Any]] = []
    primary_statuses: list[str] = []
    source, source_status = _observe_recovery_file(
        project,
        path=source_path,
        role="source_asset",
        expected_before=source_digest,
        expected_after=None,
    )
    facts.append(source)
    primary_statuses.append(source_status)
    if operation == "rename":
        target, target_status = _observe_recovery_file(
            project,
            path=str(plan["target_path"]),
            role="target_asset",
            expected_before=None,
            expected_after=source_digest,
        )
        facts.append(target)
        primary_statuses.append(target_status)
    for record in journal["files"]:
        fact, status = _observe_recovery_file(
            project,
            path=str(record["path"]),
            role="reference_owner",
            expected_before=str(record["before_sha256"]),
            expected_after=str(record["after_sha256"]),
        )
        facts.append(fact)
        primary_statuses.append(status)
    backup_status: str | None = None
    replacement_status: str | None = None
    if operation == "replace_referenced":
        replacement, replacement_status = _observe_recovery_file(
            project,
            path=str(plan["target_path"]),
            role="replacement_asset",
            expected_before=str(plan["target_sha256"]),
            expected_after=str(plan["target_sha256"]),
        )
        facts.append(replacement)
    if operation in {"delete", "replace_referenced"} and journal.get("asset_backup") is not None:
        backup, backup_status = _observe_recovery_file(
            project,
            path=str(journal["asset_backup"]),
            role="asset_backup",
            expected_before=None,
            expected_after=source_digest,
        )
        facts.append(backup)

    before_state = bool(primary_statuses) and all(status == "before" for status in primary_statuses)
    after_state = bool(primary_statuses) and all(status == "after" for status in primary_statuses)
    backup_safe = backup_status in {None, "before", "after"}
    replacement_safe = replacement_status in {None, "before", "after"}
    journal_state = str(journal["state"])
    conflicts: list[dict[str, Any]] = []
    if (not before_state and not after_state) or not backup_safe or not replacement_safe:
        for fact in facts:
            if fact["status"] not in {"before", "after"}:
                expected = fact["expected_before_sha256"]
                if expected is None:
                    expected = fact["expected_after_sha256"]
                conflicts.append(
                    _inspection_conflict(
                        str(fact["path"]),
                        str(fact["role"]),
                        expected=expected,
                        current=fact["current_sha256"],
                        code=str(fact["status"]),
                    )
                )
        if not conflicts:
            conflicts.append(
                _inspection_conflict(
                    source_path,
                    "transaction_state",
                    expected=source_digest,
                    current=source["current_sha256"],
                    code="mixed_state",
                )
            )

    classification: str
    recovery_required: bool
    legal_actions: list[str]
    if journal_state == "applied":
        classification = "terminal_applied" if after_state and backup_safe and replacement_safe else "terminal_conflict"
        recovery_required = False
        legal_actions = []
    elif journal_state == "undone":
        classification = "terminal_undone" if before_state and backup_safe and replacement_safe else "terminal_conflict"
        recovery_required = False
        legal_actions = []
    elif journal_state == "failed_acknowledged":
        classification = (
            "terminal_failed_acknowledged" if before_state and backup_safe and replacement_safe else "terminal_conflict"
        )
        recovery_required = False
        legal_actions = []
    elif (not before_state and not after_state) or not backup_safe or not replacement_safe:
        classification = "conflict"
        recovery_required = True
        legal_actions = []
    elif journal_state == "prepared":
        classification = "prepared_before_state" if before_state else "prepared_after_state"
        recovery_required = True
        legal_actions = ["rollback"] if before_state and backup_status in {None, "before", "after"} else []
    elif journal_state == "redoing":
        classification = "redoing_before_state" if before_state else "redoing_after_state"
        recovery_required = True
        legal_actions = ["rollback"] if before_state else []
    else:
        classification = "failed_recoverable_before_state" if before_state else "failed_recoverable_after_state"
        recovery_required = True
        legal_actions = ["acknowledge_failure"] if before_state else []

    return _inspection_result(
        project,
        transaction_id=transaction_id,
        journal_path=journal_path,
        journal_state=journal_state,
        classification=classification,
        recovery_required=recovery_required,
        plan=_recovery_plan_summary(plan),
        file_facts=facts,
        legal_actions=legal_actions,
        conflicts=conflicts,
    )


def inspect_asset_reference_transaction(project_root: str | Path, transaction_id: str) -> dict[str, Any]:
    """Read-only, digest-grounded inspection of one durable transaction journal.

    This function intentionally never resumes, rolls back, acknowledges, deletes,
    or rewrites a journal.  It is the single Authority for recovery facts that
    ProjectManager and future command adapters must consume.
    """

    project = _project_path(project_root)
    journal_path = _journal_path(project, transaction_id)
    if not journal_path.is_file():
        raise AssetReferenceTransactionError("asset_transaction_not_found", "Transaction journal does not exist")
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _inspection_result(
            project,
            transaction_id=transaction_id,
            journal_path=journal_path,
            journal_state=None,
            classification="malformed",
            recovery_required=True,
            conflicts=[_inspection_conflict(_relative(project, journal_path), "journal", expected=None, current=None, code="journal_unreadable")],
        )
    classification, error_code = _validate_recovery_journal(journal, transaction_id=str(transaction_id))
    if classification is not None:
        journal_state = journal.get("state") if isinstance(journal, Mapping) and isinstance(journal.get("state"), str) else None
        return _inspection_result(
            project,
            transaction_id=transaction_id,
            journal_path=journal_path,
            journal_state=journal_state,
            classification=classification,
            recovery_required=True,
            conflicts=[
                _inspection_conflict(
                    _relative(project, journal_path),
                    "journal",
                    expected=None,
                    current=None,
                    code=str(error_code),
                )
            ],
        )
    return _inspect_valid_recovery_journal(project, str(transaction_id), journal_path, journal)


@_mutation_interlocked("asset_reference.resolve")
def resolve_asset_reference_transaction(
    project_root: str | Path,
    transaction_id: str,
    *,
    action: str,
) -> dict[str, Any]:
    """Perform one explicitly permitted, no-overwrite recovery resolution.

    Phase 7D deliberately supports only state-finalization actions proven by the
    inspection model.  It never resumes an ambiguous write sequence and never
    rewrites an asset, a reference owner, or a private backup during recovery.
    """

    project = _project_path(project_root)
    requested = str(action or "").strip().lower()
    if requested not in {"rollback", "acknowledge_failure"}:
        raise AssetReferenceTransactionError(
            "invalid_asset_transaction_recovery_action",
            "Unsupported asset transaction recovery action",
            details={"action": requested, "supported_actions": ["acknowledge_failure", "rollback"]},
        )
    inspection = inspect_asset_reference_transaction(project, transaction_id)
    if requested not in inspection["legal_actions"]:
        raise AssetReferenceTransactionError(
            "asset_transaction_recovery_action_not_safe",
            "Recovery action is not safe for the current journal and file digests",
            details={
                "transaction_id": str(transaction_id),
                "action": requested,
                "classification": inspection["classification"],
                "legal_actions": list(inspection["legal_actions"]),
                "conflicts": list(inspection["conflicts"]),
            },
        )
    journal_path, journal = _read_journal(project, transaction_id)
    refreshed = inspect_asset_reference_transaction(project, transaction_id)
    if requested not in refreshed["legal_actions"] or str(journal.get("state")) != str(refreshed["journal_state"]):
        raise AssetReferenceTransactionError(
            "asset_transaction_recovery_action_not_safe",
            "Journal or filesystem facts changed during recovery inspection",
            details={"transaction_id": str(transaction_id), "action": requested},
        )
    if requested == "rollback":
        state = "undone"
    else:
        state = "failed_acknowledged"
    journal["state"] = state
    journal["recovery_resolution"] = {
        "action": requested,
        "from_state": str(refreshed["journal_state"]),
        "to_state": state,
        "reason": "filesystem_before_state",
    }
    _write_journal(journal_path, journal)
    return {
        "schema_version": SCHEMA_VERSION,
        "transaction_id": str(transaction_id),
        "action": requested,
        "state": state,
        "inspection": inspect_asset_reference_transaction(project, transaction_id),
    }


def _retention_disposition(inspection: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Return a conservative, non-authorizing retention disposition."""

    classification = str(inspection.get("classification") or "")
    if classification in {"malformed", "unsupported_schema", "unknown_state"}:
        return "protected", ["malformed_or_unsupported_receipt", classification]
    if bool(inspection.get("recovery_required")):
        return "protected", ["recovery_required", classification or "recovery_classification_missing"]
    if classification == "terminal_conflict":
        return "protected", ["terminal_conflict", "user_or_filesystem_conflict"]
    if classification in {"terminal_applied", "terminal_undone", "terminal_failed_acknowledged"}:
        return "retained", ["terminal_receipt_retained", "explicit_prune_authorization_missing"]
    return "protected", ["unrecognized_receipt_classification", classification or "missing_classification"]


def analyze_asset_transaction_retention_policy(project_root: str | Path) -> dict[str, Any]:
    """Inventory durable transaction artifacts without authorizing or performing cleanup.

    The Authority is intentionally conservative: durable receipts/backups preserve
    guarded undo/redo, recovery, and audit evidence.  Until a future separately
    proven operator-controlled mutation gate exists, it returns no safe-prune
    candidate even for a terminal receipt.
    """

    project = _project_path(project_root)
    root = _transaction_root(project)
    artifacts: list[dict[str, Any]] = []
    journal_facts: dict[str, tuple[str, list[str], dict[str, Any]]] = {}
    if root.is_dir():
        for journal_path in sorted(root.glob("*.json"), key=lambda path: path.name):
            transaction_id = journal_path.stem
            inspection = inspect_asset_reference_transaction(project, transaction_id)
            disposition, reasons = _retention_disposition(inspection)
            plan = inspection.get("plan")
            operation = plan.get("operation") if isinstance(plan, Mapping) else None
            journal_facts[transaction_id] = (disposition, reasons, inspection)
            artifacts.append(
                {
                    "path": _relative(project, journal_path),
                    "kind": "journal",
                    "transaction_id": transaction_id,
                    "operation": operation,
                    "journal_state": inspection.get("journal_state"),
                    "classification": inspection.get("classification"),
                    "recovery_required": bool(inspection.get("recovery_required")),
                    "digest_sha256": _digest_file(journal_path),
                    "disposition": disposition,
                    "reasons": list(reasons),
                    "safe_prune": False,
                }
            )
        for backup_path in sorted(root.glob("*.asset"), key=lambda path: path.name):
            transaction_id = backup_path.stem
            linked = journal_facts.get(transaction_id)
            if linked is None:
                disposition = "not_prunable"
                reasons = ["orphan_private_backup", "provenance_unproven", "explicit_prune_authorization_missing"]
                classification = None
                recovery_required = False
            else:
                journal_disposition, _journal_reasons, inspection = linked
                disposition = "protected" if journal_disposition == "protected" else "retained"
                reasons = [
                    "linked_journal",
                    "linked_recovery_protected" if disposition == "protected" else "linked_terminal_journal",
                    "explicit_prune_authorization_missing",
                ]
                classification = inspection.get("classification")
                recovery_required = bool(inspection.get("recovery_required"))
            artifacts.append(
                {
                    "path": _relative(project, backup_path),
                    "kind": "private_asset_backup",
                    "transaction_id": transaction_id,
                    "classification": classification,
                    "recovery_required": recovery_required,
                    "digest_sha256": _digest_file(backup_path),
                    "disposition": disposition,
                    "reasons": reasons,
                    "safe_prune": False,
                }
            )
        for artifact_path in sorted(root.iterdir(), key=lambda path: path.name):
            if artifact_path.suffix in {".json", ".asset"}:
                continue
            artifacts.append(
                {
                    "path": _relative(project, artifact_path),
                    "kind": "unknown_transaction_artifact",
                    "transaction_id": None,
                    "classification": None,
                    "recovery_required": False,
                    "digest_sha256": _digest_file(artifact_path) if artifact_path.is_file() else None,
                    "disposition": "not_prunable",
                    "reasons": ["unknown_transaction_artifact", "provenance_unproven", "explicit_prune_authorization_missing"],
                    "safe_prune": False,
                }
            )
    artifacts.sort(key=lambda item: (str(item["path"]), str(item["kind"])))
    review_candidates: list[dict[str, Any]] = []
    for transaction_id, (disposition, _reasons, inspection) in sorted(journal_facts.items()):
        if disposition != "retained":
            continue
        bundle = [
            {
                "path": str(artifact["path"]),
                "digest_sha256": str(artifact["digest_sha256"]),
                "kind": str(artifact["kind"]),
            }
            for artifact in artifacts
            if artifact.get("transaction_id") == transaction_id
            and artifact.get("kind") in {"journal", "private_asset_backup"}
        ]
        journal_rows = [row for row in bundle if row["kind"] == "journal"]
        if len(journal_rows) != 1:
            continue
        review_candidates.append(
            {
                "transaction_id": transaction_id,
                "operation": (inspection.get("plan") or {}).get("operation") if isinstance(inspection.get("plan"), Mapping) else None,
                "classification": inspection.get("classification"),
                "artifact_paths": [row["path"] for row in bundle],
                "expected_digests": {row["path"]: row["digest_sha256"] for row in bundle},
                "reasons": [
                    "strict_valid_terminal_receipt",
                    "complete_known_transaction_bundle",
                    "operator_confirmation_and_apply_revalidation_required",
                ],
                "safe_prune": False,
            }
        )
    summary = {"protected": 0, "retained": 0, "review_candidate": 0, "not_prunable": 0}
    for artifact in artifacts:
        summary[str(artifact["disposition"])] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "transaction_root": TRANSACTION_DIRECTORY,
        "read_only": True,
        "prune_authorized": False,
        "artifacts": artifacts,
        "summary": summary,
        "review_candidates": review_candidates,
        "safe_prune_candidates": [],
        "non_goals": [
            "No journal, backup, Registry, owner, asset, export, or command-audit mutation occurs during analysis.",
            "No automatic cleanup, deletion, repair, or compaction permission is inferred.",
            "Terminal transaction evidence remains retained until a future explicit operator-controlled mutation authority is proven.",
        ],
    }



def _prune_root(project: Path) -> Path:
    return project / PRUNE_DIRECTORY


def _prune_failure(code: str, message: str, *, details: Mapping[str, Any] | None = None) -> AssetReferenceTransactionError:
    return AssetReferenceTransactionError(code, message, details=details)


def _normalize_prune_request(
    project: Path,
    artifact_paths: Sequence[str],
    expected_digests: Mapping[str, str],
) -> tuple[list[str], dict[str, str]]:
    if isinstance(artifact_paths, (str, bytes)) or not isinstance(artifact_paths, Sequence):
        raise _prune_failure("asset_transaction_prune_bundle_mismatch", "artifact_paths must name one complete transaction bundle")
    raw_paths = [str(value or "").strip() for value in artifact_paths]
    if len(raw_paths) not in {1, 2} or not all(raw_paths) or len(set(raw_paths)) != len(raw_paths):
        raise _prune_failure("asset_transaction_prune_bundle_mismatch", "Prune must name every artifact of exactly one transaction bundle")
    if not isinstance(expected_digests, Mapping):
        raise _prune_failure("asset_transaction_prune_bundle_mismatch", "expected_digests must bind every requested artifact")
    digest_map = {str(key or "").strip(): str(value or "").strip() for key, value in expected_digests.items()}
    if set(digest_map) != set(raw_paths) or any(not _is_canonical_sha256(value) for value in digest_map.values()):
        raise _prune_failure("asset_transaction_prune_bundle_mismatch", "Every requested artifact needs one canonical expected digest")
    clean_paths: list[str] = []
    for raw in raw_paths:
        if not raw.startswith(TRANSACTION_DIRECTORY + "/"):
            raise _prune_failure("asset_transaction_prune_bundle_mismatch", "Only transaction-root files may be named for pruning")
        artifact = _project_file(project, raw)
        if artifact.is_symlink() or not artifact.is_file():
            raise _prune_failure("asset_transaction_prune_bundle_mismatch", "Prune artifacts must be ordinary files")
        relative = _relative(project, artifact)
        if relative != raw:
            raise _prune_failure("asset_transaction_prune_bundle_mismatch", "Prune paths must be canonical project-relative paths")
        clean_paths.append(relative)
    clean_paths.sort()
    return clean_paths, {path: digest_map[path] for path in clean_paths}


def _find_prune_candidate(
    policy: Mapping[str, Any],
    artifact_paths: Sequence[str],
    expected_digests: Mapping[str, str],
) -> dict[str, Any]:
    candidates = policy.get("review_candidates")
    if not isinstance(candidates, list):
        raise _prune_failure("asset_transaction_prune_not_reviewable", "Retention policy supplied no review candidates")
    requested = set(artifact_paths)
    related = False
    for raw in candidates:
        if not isinstance(raw, Mapping):
            continue
        paths = raw.get("artifact_paths")
        digests = raw.get("expected_digests")
        if not isinstance(paths, list) or not isinstance(digests, Mapping):
            continue
        candidate_paths = [str(path) for path in paths]
        if requested.intersection(candidate_paths):
            related = True
        candidate_digests = {str(key): str(value) for key, value in digests.items()}
        if set(candidate_paths) == requested and candidate_digests == dict(expected_digests):
            return dict(raw)
    raise _prune_failure(
        "asset_transaction_prune_bundle_mismatch" if related else "asset_transaction_prune_not_reviewable",
        "Requested artifacts are not one exact policy-reviewable transaction bundle",
    )



def _audit_entry_targets_project(entry: Mapping[str, Any], project: Path) -> bool:
    raw = str(entry.get("project_path") or "").strip()
    if not raw:
        return False
    try:
        return Path(raw).expanduser().resolve() == project
    except OSError:
        return False
def _read_prune_provenance(project: Path, transaction_id: str) -> dict[str, str]:
    try:
        entries = read_project_command_audit_entries(project, strict=True)
    except CommandAuditHistoryError as exc:
        raise _prune_failure(
            "asset_transaction_prune_provenance_unproven",
            "Command audit cannot prove prune provenance",
        ) from exc
    if not entries:
        raise _prune_failure(
            "asset_transaction_prune_provenance_unproven",
            "A matching command-audit entry is required",
        )
    source_entries = [
        entry
        for entry in entries
        if str(entry.get("action") or "execute") == "execute"
        and str(entry.get("command_id") or "") in {"asset.rename", "asset.delete", "asset.referenced.replace"}
        and isinstance(entry.get("result"), Mapping)
        and str(entry["result"].get("transaction_id") or "") == transaction_id
        and _audit_entry_targets_project(entry, project)
        and str(entry.get("audit_id") or "")
    ]
    if len(source_entries) != 1:
        raise _prune_failure("asset_transaction_prune_provenance_unproven", "Transaction must have exactly one source command-audit entry")
    source = source_entries[0]
    source_id = str(source["audit_id"])
    for entry in entries:
        if str(entry.get("source_audit_id") or "") != source_id:
            continue
        if str(entry.get("action") or "") in {"undo", "redo", "durable_undo", "durable_redo"}:
            raise _prune_failure("asset_transaction_prune_provenance_unproven", "Transaction has an unresolved undo or redo relation")
    return {"source_audit_id": source_id, "source_command_id": str(source["command_id"])}

def _prune_confirmation(
    project: Path,
    transaction_id: str,
    artifact_paths: Sequence[str],
    expected_digests: Mapping[str, str],
    snapshot_digest: str,
) -> str:
    manifest = ";".join(f"{path}:{expected_digests[path]}" for path in sorted(artifact_paths))
    return (
        "VITALOOM-PRUNE "
        f"project={project} transaction={transaction_id} snapshot={snapshot_digest} "
        f"artifacts={manifest} irreversible_durable_undo_redo_revocation"
    )


def plan_asset_transaction_artifact_prune(
    project_root: str | Path,
    *,
    artifact_paths: Sequence[str],
    expected_digests: Mapping[str, str],
) -> dict[str, Any]:
    """Read-only intent for one exact terminal transaction artifact bundle."""

    project = _project_path(project_root)
    clean_paths, clean_digests = _normalize_prune_request(project, artifact_paths, expected_digests)
    policy = analyze_asset_transaction_retention_policy(project)
    candidate = _find_prune_candidate(policy, clean_paths, clean_digests)
    transaction_id = str(candidate.get("transaction_id") or "")
    if not transaction_id:
        raise _prune_failure("asset_transaction_prune_not_reviewable", "Review candidate has no transaction id")
    for path in clean_paths:
        if _digest_file(_project_file(project, path)) != clean_digests[path]:
            raise _prune_failure("asset_transaction_prune_stale", "Artifact changed before prune planning", details={"path": path})
    provenance = _read_prune_provenance(project, transaction_id)
    snapshot_digest = _digest_bytes(
        _json_bytes(
            {
                "transaction_id": transaction_id,
                "candidate": candidate,
                "artifact_paths": clean_paths,
                "expected_digests": clean_digests,
                "provenance": provenance,
            }
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "read_only": True,
        "prune_authorized": False,
        "transaction_id": transaction_id,
        "artifact_paths": clean_paths,
        "expected_digests": clean_digests,
        "policy_snapshot_digest": snapshot_digest,
        "operator_confirmation_required": _prune_confirmation(
            project, transaction_id, clean_paths, clean_digests, snapshot_digest
        ),
        "provenance": provenance,
    }


def _prune_receipt_path(project: Path, prune_id: str) -> Path:
    clean = str(prune_id or "").strip()
    if not clean or any(character in clean for character in "\\/"):
        raise _prune_failure("invalid_asset_transaction_prune_id", "Invalid asset transaction prune id")
    return _prune_root(project) / f"{clean}.json"


def _prune_staging_path(project: Path, prune_id: str) -> Path:
    return _prune_root(project) / f"{prune_id}.staging"


def _prune_staged_path(staging: Path, relative: str) -> Path:
    return staging / Path(relative).name


def _write_prune_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _write_atomic(path, _json_bytes(dict(receipt)))


def _read_prune_receipt(project: Path, prune_id: str) -> tuple[Path, dict[str, Any]]:
    path = _prune_receipt_path(project, prune_id)
    if not path.is_file():
        raise _prune_failure("asset_transaction_prune_receipt_not_found", "Prune receipt does not exist")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt cannot be read") from exc
    if not isinstance(value, dict):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt must be an object")
    required = {
        "schema_version",
        "prune_id",
        "state",
        "transaction_id",
        "artifact_paths",
        "expected_digests",
        "policy_snapshot_digest",
        "confirmation_digest",
        "provenance",
    }
    if set(value) != required or value.get("schema_version") != SCHEMA_VERSION or str(value.get("prune_id") or "") != str(prune_id):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt schema is invalid")
    state = str(value.get("state") or "")
    if state not in {"prepared", "staged", "staged_cleanup_incomplete", "compensated", "recovered", "pruned"}:
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt state is unsupported")
    if not str(value.get("transaction_id") or "") or not _is_canonical_sha256(str(value.get("policy_snapshot_digest") or "")) or not _is_canonical_sha256(str(value.get("confirmation_digest") or "")):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt identity binding is invalid")
    raw_paths = value.get("artifact_paths")
    raw_digests = value.get("expected_digests")
    if not isinstance(raw_paths, list) or not isinstance(raw_digests, Mapping):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt manifest is invalid")
    paths = [str(item or "").strip() for item in raw_paths]
    digests = {str(key or "").strip(): str(digest or "").strip() for key, digest in raw_digests.items()}
    if paths != sorted(paths) or len(paths) not in {1, 2} or len(set(paths)) != len(paths):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt paths are not canonical")
    if set(paths) != set(digests) or any(not _is_canonical_sha256(digest) for digest in digests.values()):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt digests are invalid")
    for relative in paths:
        if not relative.startswith(TRANSACTION_DIRECTORY + "/") or Path(relative).name != relative.rsplit("/", 1)[-1]:
            raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt contains an invalid artifact path")
    provenance = value.get("provenance")
    if not isinstance(provenance, Mapping) or not str(provenance.get("source_audit_id") or "") or not str(provenance.get("source_command_id") or ""):
        raise _prune_failure("asset_transaction_prune_receipt_malformed", "Prune receipt provenance is invalid")
    return path, value


def list_asset_transaction_artifact_prune_receipts(project_root: str | Path) -> dict[str, Any]:
    """List only strict prune receipts suitable for durable replay revocation checks.

    This is intentionally read-only.  Malformed or provenance-inconsistent files
    are reported but never treated as authority to suppress a project undo/redo.
    """

    project = _project_path(project_root)
    root = _prune_root(project)
    receipts: list[dict[str, Any]] = []
    malformed: list[str] = []
    if root.is_dir():
        for receipt_path in sorted(root.glob("*.json"), key=lambda item: item.name):
            try:
                _path, receipt = _read_prune_receipt(project, receipt_path.stem)
                provenance = _read_prune_provenance(project, str(receipt["transaction_id"]))
                recorded = receipt["provenance"]
                if (
                    str(recorded.get("source_audit_id") or "") != provenance["source_audit_id"]
                    or str(recorded.get("source_command_id") or "") != provenance["source_command_id"]
                ):
                    raise _prune_failure(
                        "asset_transaction_prune_receipt_malformed",
                        "Prune receipt provenance does not match command audit facts",
                    )
            except AssetReferenceTransactionError:
                malformed.append(_relative(project, receipt_path))
                continue
            receipts.append(
                {
                    "prune_id": str(receipt["prune_id"]),
                    "state": str(receipt["state"]),
                    "transaction_id": str(receipt["transaction_id"]),
                    "source_audit_id": provenance["source_audit_id"],
                    "source_command_id": provenance["source_command_id"],
                }
            )
    return {
        "project_path": str(project),
        "receipts": receipts,
        "malformed_receipts": malformed,
    }


def _move_prune_artifact(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _remove_prune_staged_artifact(path: Path) -> None:
    path.unlink()


def _prune_artifact_facts(project: Path, receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    staging = _prune_staging_path(project, str(receipt["prune_id"]))
    facts: list[dict[str, Any]] = []
    for relative in receipt["artifact_paths"]:
        source = project / str(relative)
        staged = _prune_staged_path(staging, str(relative))
        expected = str(receipt["expected_digests"][relative])
        facts.append(
            {
                "path": str(relative),
                "expected_digest": expected,
                "source_exists": source.is_file(),
                "source_digest_matches": source.is_file() and _digest_file(source) == expected,
                "staged_exists": staged.is_file(),
                "staged_digest_matches": staged.is_file() and _digest_file(staged) == expected,
            }
        )
    return facts


def inspect_asset_transaction_artifact_prune(project_root: str | Path, prune_id: str) -> dict[str, Any]:
    """Read one strict prune receipt and expose only explicit recovery facts."""

    project = _project_path(project_root)
    receipt_path, receipt = _read_prune_receipt(project, prune_id)
    facts = _prune_artifact_facts(project, receipt)
    state = str(receipt["state"])
    all_staged = bool(facts) and all(item["staged_exists"] and item["staged_digest_matches"] and not item["source_exists"] for item in facts)
    recovery_required = state in {"staged", "staged_cleanup_incomplete"}
    legal_actions = ["restore_staged"] if recovery_required and all_staged else []
    conflicts = [
        item["path"]
        for item in facts
        if (item["source_exists"] and not item["source_digest_matches"])
        or (item["staged_exists"] and not item["staged_digest_matches"])
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_path": str(project),
        "prune_id": str(receipt["prune_id"]),
        "receipt_path": _relative(project, receipt_path),
        "state": state,
        "transaction_id": str(receipt["transaction_id"]),
        "artifact_paths": list(receipt["artifact_paths"]),
        "recovery_required": recovery_required,
        "legal_actions": legal_actions,
        "artifact_facts": facts,
        "conflicts": conflicts,
    }


def list_asset_transaction_artifact_prune_recovery(project_root: str | Path) -> dict[str, Any]:
    """List strict prune receipts that still need an explicit recovery decision."""

    project = _project_path(project_root)
    root = _prune_root(project)
    inspections: list[dict[str, Any]] = []
    malformed: list[str] = []
    if root.is_dir():
        for receipt_path in sorted(root.glob("*.json"), key=lambda item: item.name):
            try:
                inspection = inspect_asset_transaction_artifact_prune(project, receipt_path.stem)
            except AssetReferenceTransactionError:
                malformed.append(_relative(project, receipt_path))
                continue
            if inspection["recovery_required"]:
                inspections.append(inspection)
    return {
        "project_path": str(project),
        "recovery_required": bool(inspections) or bool(malformed),
        "prunes": inspections,
        "malformed_receipts": malformed,
    }


@_mutation_interlocked("asset_transaction_prune.resolve")
def resolve_asset_transaction_artifact_prune(
    project_root: str | Path,
    prune_id: str,
    *,
    action: str,
) -> dict[str, Any]:
    """Restore a wholly staged bundle only; never silently resume pruning."""

    project = _project_path(project_root)
    if str(action or "").strip().lower() != "restore_staged":
        raise _prune_failure("invalid_asset_transaction_prune_recovery_action", "Only restore_staged is supported")
    inspection = inspect_asset_transaction_artifact_prune(project, prune_id)
    if "restore_staged" not in inspection["legal_actions"]:
        raise _prune_failure(
            "asset_transaction_prune_recovery_action_not_safe",
            "Staged prune artifacts cannot be restored safely",
            details={"prune_id": str(prune_id), "state": inspection["state"], "conflicts": inspection["conflicts"]},
        )
    receipt_path, receipt = _read_prune_receipt(project, prune_id)
    fresh = inspect_asset_transaction_artifact_prune(project, prune_id)
    if "restore_staged" not in fresh["legal_actions"]:
        raise _prune_failure("asset_transaction_prune_recovery_action_not_safe", "Prune recovery facts changed before restore")
    staging = _prune_staging_path(project, str(receipt["prune_id"]))
    moved: list[tuple[Path, Path]] = []
    try:
        for relative in receipt["artifact_paths"]:
            source = project / str(relative)
            staged = _prune_staged_path(staging, str(relative))
            _move_prune_artifact(staged, source)
            moved.append((source, staged))
    except Exception as exc:
        for source, staged in reversed(moved):
            if source.exists() and not staged.exists():
                _move_prune_artifact(source, staged)
        raise _prune_failure("asset_transaction_prune_recovery_failed", "Staged prune restore failed and was compensated") from exc
    receipt["state"] = "recovered"
    _write_prune_receipt(receipt_path, receipt)
    try:
        staging.rmdir()
    except OSError:
        pass
    return {"schema_version": SCHEMA_VERSION, "prune_id": str(prune_id), "state": "recovered", "inspection": inspect_asset_transaction_artifact_prune(project, prune_id)}


@_mutation_interlocked("asset_transaction_prune.apply")
def apply_asset_transaction_artifact_prune(
    project_root: str | Path,
    prune_plan: Mapping[str, Any],
    *,
    operator_confirmation: str,
) -> dict[str, Any]:
    """Prune a freshly revalidated bundle only after exact operator confirmation."""

    if not isinstance(prune_plan, Mapping):
        raise _prune_failure("asset_transaction_prune_plan_invalid", "prune_plan must be a mapping")
    project = _project_path(project_root)
    if str(prune_plan.get("project_path") or "") != str(project):
        raise _prune_failure("asset_transaction_prune_project_mismatch", "Prune plan belongs to a different project")
    raw_digests = prune_plan.get("expected_digests")
    if not isinstance(raw_digests, Mapping):
        raise _prune_failure("asset_transaction_prune_plan_invalid", "prune_plan has no digest manifest")
    paths, digests = _normalize_prune_request(project, prune_plan.get("artifact_paths"), raw_digests)  # type: ignore[arg-type]
    for relative in paths:
        if _digest_file(_project_file(project, relative)) != digests[relative]:
            raise _prune_failure("asset_transaction_prune_stale", "Artifact changed after prune planning", details={"path": relative})
    confirmation = str(prune_plan.get("operator_confirmation_required") or "")
    if not confirmation or operator_confirmation != confirmation:
        raise _prune_failure("asset_transaction_prune_confirmation_invalid", "Exact operator confirmation is required")
    fresh = plan_asset_transaction_artifact_prune(project, artifact_paths=paths, expected_digests=digests)
    if (
        str(prune_plan.get("transaction_id") or "") != fresh["transaction_id"]
        or str(prune_plan.get("policy_snapshot_digest") or "") != fresh["policy_snapshot_digest"]
        or confirmation != fresh["operator_confirmation_required"]
    ):
        raise _prune_failure("asset_transaction_prune_stale", "Prune plan no longer matches policy or provenance facts")

    prune_id = uuid.uuid4().hex
    receipt_path = _prune_receipt_path(project, prune_id)
    staging = _prune_staging_path(project, prune_id)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prune_id": prune_id,
        "state": "prepared",
        "transaction_id": fresh["transaction_id"],
        "artifact_paths": paths,
        "expected_digests": digests,
        "policy_snapshot_digest": fresh["policy_snapshot_digest"],
        "confirmation_digest": _digest_bytes(operator_confirmation.encode("utf-8")),
        "provenance": fresh["provenance"],
    }
    _write_prune_receipt(receipt_path, receipt)
    moved: list[tuple[Path, Path]] = []
    try:
        staging.mkdir(parents=True, exist_ok=False)
        for relative in paths:
            source = _project_file(project, relative)
            destination = _prune_staged_path(staging, relative)
            _move_prune_artifact(source, destination)
            moved.append((source, destination))
        receipt["state"] = "staged"
        _write_prune_receipt(receipt_path, receipt)
    except Exception as exc:
        compensation_complete = True
        for source, destination in reversed(moved):
            if destination.exists() and not source.exists():
                try:
                    _move_prune_artifact(destination, source)
                except OSError:
                    compensation_complete = False
        receipt["state"] = "compensated" if compensation_complete else "staged_cleanup_incomplete"
        _write_prune_receipt(receipt_path, receipt)
        if compensation_complete:
            try:
                staging.rmdir()
            except OSError:
                pass
            raise _prune_failure("asset_transaction_prune_io_failed", "Prune staging failed and was compensated") from exc
        raise _prune_failure("asset_transaction_prune_recovery_required", "Prune staging failed and needs explicit recovery") from exc
    try:
        for _source, destination in moved:
            _remove_prune_staged_artifact(destination)
    except OSError as exc:
        receipt["state"] = "staged_cleanup_incomplete"
        _write_prune_receipt(receipt_path, receipt)
        raise _prune_failure("asset_transaction_prune_recovery_required", "Prune staging needs explicit recovery") from exc
    receipt["state"] = "pruned"
    _write_prune_receipt(receipt_path, receipt)
    try:
        staging.rmdir()
    except OSError:
        pass
    return {
        "schema_version": SCHEMA_VERSION,
        "prune_id": prune_id,
        "state": "pruned",
        "transaction_id": fresh["transaction_id"],
        "artifact_paths": paths,
        "receipt_path": _relative(project, receipt_path),
        "provenance": fresh["provenance"],
    }


def list_asset_reference_transaction_recovery(project_root: str | Path) -> dict[str, Any]:
    """List only journals that need explicit operator recovery attention."""

    project = _project_path(project_root)
    root = _transaction_root(project)
    inspections: list[dict[str, Any]] = []
    if root.is_dir():
        for journal_path in sorted(root.glob("*.json"), key=lambda path: path.name):
            inspection = inspect_asset_reference_transaction(project, journal_path.stem)
            if inspection["recovery_required"]:
                inspections.append(inspection)
    inspections.sort(key=lambda item: (str(item["journal_path"]), str(item["transaction_id"])))
    return {
        "project_path": str(project),
        "recovery_required": bool(inspections),
        "pending_journals": [str(item["journal_path"]) for item in inspections],
        "transactions": inspections,
    }


def recover_asset_reference_mutations(project_root: str | Path) -> dict[str, Any]:
    """Backward-compatible read-only recovery summary delegated to the Authority."""

    return list_asset_reference_transaction_recovery(project_root)
