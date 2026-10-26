# -*- coding: utf-8 -*-
"""Qt-free Project World session persistence and close-transition authority."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from core.VitaLoom.project.project_world_report import finalize_project_world_report


AUTOMATIC_SCENE_FLUSH_HISTORY_BOUNDARY = {
    "kind": "automatic_lifecycle_flush",
    "history_admission": "excluded",
    "audit_admission": "excluded",
    "reason": (
        "Project-World lifecycle persistence is not a user semantic command; "
        "it must not create user undo/redo history or command audit entries."
    ),
}


_CLOSE_APPLICATION_STEPS = [
    "flush_current_world",
    "teardown_project_addons",
    "clear_host_scene",
    "clear_project_context",
    "publish_project_closed",
]


def _project_path(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().resolve()


def _base_report(transition: str, project: Path) -> dict[str, Any]:
    return {
        "transition": transition,
        "status": "ready",
        "code": "",
        "message": "",
        "project_path": str(project),
        "project_json_path": str(project / "project.json"),
        "project_data": {},
        "next_project_data": {},
        "active_scene": "",
        "scene_path": "",
        "manifest_update_required": False,
        "warnings": [],
        "application_steps": [],
    }


def _blocked(
    transition: str,
    project: Path,
    code: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    report = _base_report(transition, project)
    report.update(
        {
            "status": "blocked",
            "code": str(code),
            "message": str(message),
            "application_steps": [],
        }
    )
    report.update(details)
    return finalize_project_world_report(report)


def _read_project_manifest(
    transition: str,
    project: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    manifest_path = project / "project.json"
    if not manifest_path.is_file():
        return None, _blocked(
            transition,
            project,
            "project_manifest_missing",
            f"project.json not found: {manifest_path}",
        )
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, _blocked(
            transition,
            project,
            "project_manifest_invalid_json",
            f"invalid project.json: {exc}",
        )
    except OSError as exc:
        return None, _blocked(
            transition,
            project,
            "project_manifest_unreadable",
            f"{type(exc).__name__}: {exc}",
        )
    if not isinstance(raw, dict):
        return None, _blocked(
            transition,
            project,
            "project_manifest_not_object",
            "project.json root must be an object",
        )
    return dict(raw), None


def _scene_relative_path(
    transition: str,
    project: Path,
    scene_path: str | os.PathLike[str],
) -> tuple[str | None, dict[str, Any] | None]:
    scene = Path(scene_path).expanduser().resolve()
    scenes_root = (project / "scenes").resolve()
    try:
        relative = scene.relative_to(scenes_root)
    except ValueError:
        return None, _blocked(
            transition,
            project,
            "active_scene_outside_project",
            "active scene must stay under the Project World scenes directory",
            scene_path=str(scene),
        )
    if relative.suffix.lower() != ".pond":
        return None, _blocked(
            transition,
            project,
            "active_scene_not_pond",
            "active scene must reference a .pond scene",
            scene_path=str(scene),
        )
    normalized = relative.as_posix()
    if not normalized or normalized == ".":
        return None, _blocked(
            transition,
            project,
            "active_scene_outside_project",
            "active scene must be a file below the Project World scenes directory",
            scene_path=str(scene),
        )
    return normalized, None


def prepare_project_world_save(
    project_path: str | os.PathLike[str],
    *,
    modified_at: str | None = None,
) -> dict[str, Any]:
    """Prepare a deterministic manifest save without importing a GUI Host."""

    project = _project_path(project_path)
    project_data, blocked = _read_project_manifest("save", project)
    if blocked is not None:
        return blocked
    assert project_data is not None
    stamp = str(modified_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    next_project_data = dict(project_data)
    next_project_data["modified_at"] = stamp
    report = _base_report("save", project)
    report.update(
        {
            "message": "Project World manifest is ready to save",
            "project_data": project_data,
            "next_project_data": next_project_data,
            "active_scene": str(project_data.get("active_scene", "") or ""),
            "modified_at": stamp,
            "manifest_update_required": True,
            "application_steps": ["atomic_replace_project_manifest"],
        }
    )
    return finalize_project_world_report(report)


def prepare_project_world_flush(
    project_path: str | os.PathLike[str],
    *,
    scene_path: str | os.PathLike[str] | None = None,
    update_active_scene: bool = True,
) -> dict[str, Any]:
    """Prepare active-scene persistence facts before Host scene mutation."""

    project = _project_path(project_path)
    report = _base_report("flush", project)
    report["scene_persistence_boundary"] = dict(AUTOMATIC_SCENE_FLUSH_HISTORY_BOUNDARY)
    report["message"] = "Project World is ready to flush"
    report["update_active_scene"] = bool(update_active_scene)
    report["scene_path"] = str(Path(scene_path).expanduser().resolve()) if scene_path else ""
    report["application_steps"] = ["persist_host_scene"] if scene_path else []
    if not scene_path:
        return finalize_project_world_report(report)

    active_scene, blocked = _scene_relative_path("flush", project, scene_path)
    if blocked is not None:
        return blocked
    assert active_scene is not None
    report["active_scene"] = active_scene
    if not update_active_scene:
        return finalize_project_world_report(report)

    project_data, blocked = _read_project_manifest("flush", project)
    if blocked is not None:
        blocked["scene_path"] = report["scene_path"]
        blocked["active_scene"] = active_scene
        return finalize_project_world_report(blocked)
    assert project_data is not None
    next_project_data = dict(project_data)
    next_project_data["active_scene"] = active_scene
    report.update(
        {
            "project_data": project_data,
            "next_project_data": next_project_data,
            "manifest_update_required": True,
            "application_steps": [
                "persist_host_scene",
                "atomic_replace_project_manifest",
            ],
        }
    )
    return finalize_project_world_report(report)


def prepare_project_world_close(
    project_path: str | os.PathLike[str] | None,
) -> dict[str, Any]:
    """Prepare deterministic close ordering; Host effects remain Adapter-owned."""

    if not project_path:
        report = _base_report("close", Path.cwd().resolve())
        report.update(
            {
                "status": "noop",
                "code": "no_current_project_world",
                "message": "No Project World is currently applied",
                "project_path": "",
                "project_json_path": "",
                "application_steps": [],
            }
        )
        return finalize_project_world_report(report)
    project = _project_path(project_path)
    report = _base_report("close", project)
    report.update(
        {
            "message": "Project World is ready for Host close application",
            "application_steps": list(_CLOSE_APPLICATION_STEPS),
        }
    )
    return finalize_project_world_report(report)


def commit_project_world_manifest(
    preparation: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically replace project.json from a ready Qt-free preparation report."""

    transition = str(preparation.get("transition", "persistence") or "persistence")
    report: dict[str, Any] = {
        "transition": transition,
        "status": "failed",
        "code": "",
        "message": "",
        "project_path": str(preparation.get("project_path", "") or ""),
        "project_json_path": str(preparation.get("project_json_path", "") or ""),
        "preparation_report_id": str(preparation.get("report_id", "") or ""),
        "actions": [],
    }
    if preparation.get("status") != "ready":
        report.update(
            {
                "status": "blocked",
                "code": str(preparation.get("code", "project_world_persistence_not_ready") or "project_world_persistence_not_ready"),
                "message": str(preparation.get("message", "Project World persistence is not ready") or ""),
            }
        )
        return finalize_project_world_report(report)
    if not bool(preparation.get("manifest_update_required", False)):
        report.update(
            {
                "status": "noop",
                "code": "manifest_update_not_required",
                "message": "Project World manifest does not require an update",
            }
        )
        return finalize_project_world_report(report)

    project_path = str(report["project_path"] or "")
    manifest_value = str(report["project_json_path"] or "")
    if not project_path or not manifest_value:
        report.update(
            {
                "status": "blocked",
                "code": "project_manifest_target_invalid",
                "message": "ready persistence preparation requires a Project World manifest target",
            }
        )
        return finalize_project_world_report(report)

    project = Path(project_path).expanduser().resolve()
    manifest_path = Path(manifest_value).expanduser().resolve()
    expected_manifest = (project / "project.json").resolve()
    if os.path.normcase(str(manifest_path)) != os.path.normcase(str(expected_manifest)):
        report.update(
            {
                "status": "blocked",
                "code": "project_manifest_target_invalid",
                "message": "project_json_path must resolve to <project_path>/project.json",
                "expected_project_json_path": str(expected_manifest),
            }
        )
        return finalize_project_world_report(report)

    project_data = preparation.get("next_project_data")
    if not isinstance(project_data, Mapping):
        report.update(
            {
                "code": "project_manifest_preparation_invalid",
                "message": "ready persistence preparation requires object next_project_data",
            }
        )
        return finalize_project_world_report(report)

    lock_path = project / "project.lock.json"
    manifest_before = manifest_path.read_bytes()
    lock_before = lock_path.read_bytes() if lock_path.is_file() else None

    temp_path: Path | None = None
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fd, raw_temp_path = tempfile.mkstemp(
            prefix=f".{manifest_path.name}.",
            suffix=".tmp",
            dir=str(manifest_path.parent),
        )
        temp_path = Path(raw_temp_path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(
                    dict(project_data),
                    handle,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
    except Exception as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        report.update(
            {
                "code": "project_manifest_atomic_write_failed",
                "message": f"{type(exc).__name__}: {exc}",
                "actions": [
                    {
                        "action": "write_temporary_project_manifest",
                        "status": "failed",
                        "error": type(exc).__name__,
                    }
                ],
            }
        )
        return finalize_project_world_report(report)

    try:
        os.replace(temp_path, manifest_path)
    except Exception as exc:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        report.update(
            {
                "code": "project_manifest_atomic_replace_failed",
                "message": f"{type(exc).__name__}: {exc}",
                "actions": [
                    {
                        "action": "atomic_replace_project_manifest",
                        "status": "failed",
                        "error": type(exc).__name__,
                    }
                ],
            }
        )
        return finalize_project_world_report(report)

    try:
        from core.VitaLoom.core.bundle_paths import resource_root
        from core.VitaLoom.project.project_write_authority import (
            project_write_interlock,
        )
        from core.VitaLoom.suite.project_lock import ensure_project_lock

        with project_write_interlock(
            project,
            authority_action="project_manifest_lock_refresh",
        ):
            ensure_project_lock(
                project,
                repo_root=resource_root(),
                overwrite=True,
            )
    except Exception as exc:
        try:
            manifest_path.write_bytes(manifest_before)
            if lock_before is None:
                lock_path.unlink(missing_ok=True)
            else:
                lock_path.write_bytes(lock_before)
        except OSError as restore_error:
            report.update(
                {
                    "code": "project_lock_refresh_rollback_failed",
                    "message": f"{type(exc).__name__}: {exc}; restore failed: {restore_error}",
                    "actions": [
                        {
                            "action": "restore_project_manifest_and_lock",
                            "status": "failed",
                            "error": type(restore_error).__name__,
                        }
                    ],
                }
            )
            return finalize_project_world_report(report)
        report.update(
            {
                "code": "project_lock_refresh_failed",
                "message": f"{type(exc).__name__}: {exc}; project manifest was rolled back",
                "actions": [
                    {
                        "action": "refresh_project_lock",
                        "status": "failed",
                        "error": type(exc).__name__,
                    },
                    {
                        "action": "restore_project_manifest_and_lock",
                        "status": "completed",
                    },
                ],
            }
        )
        return finalize_project_world_report(report)

    report.update(
        {
            "status": "persisted",
            "message": "Project World manifest persisted atomically",
            "project_data": dict(project_data),
            "actions": [
                {
                    "action": "atomic_replace_project_manifest",
                    "status": "completed",
                }
            ],
        }
    )
    return finalize_project_world_report(report)
