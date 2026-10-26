# -*- coding: utf-8 -*-
"""Qt-free Project World open preparation authority."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from core.VitaLoom.project.project_manifest import (
    ManifestIssue,
    ManifestValidationResult,
    get_loom_editor_version_from_pyproject,
    validate_project_manifest,
)


def _project_lock_admission_report(
    project: Path,
    *,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Resolve lock admission before any Host state is allowed to change."""

    from core.VitaLoom.suite.project_lock import resolve_project_runtime

    resolved = resolve_project_runtime(project, repo_root=repo_root)
    report = {
        "status": "ready" if not resolved.has_blocking_issues else "blocked",
        "admission": resolved.lock_admission_code,
        "lock_status": resolved.lock_status_text,
        "blocking_issue_codes": list(resolved.blocking_issue_codes),
        "blocking_issue_summary": resolved.blocking_issue_summary,
        "lock_missing": bool(resolved.lock_missing),
        "lock_legacy": bool(resolved.lock_legacy),
        "product_version": resolved.product_version,
        "resolved_capabilities": dict(resolved.resolved_capabilities),
    }
    warnings: list[dict[str, str]] = []
    if resolved.lock_legacy:
        warnings.append(
            {
                "code": "project_lock_legacy",
                "message": "project.lock.json uses the legacy schema",
            }
        )
    return report, warnings


_APPLICATION_STEPS = [
    "clear_host_scene",
    "apply_project_context",
    "load_active_scene",
    "publish_project_opened",
    "sync_project_plugins",
    "persist_recent_world",
    "refresh_asset_registry",
    "refresh_project_browser",
]


from core.VitaLoom.project.project_world_report import (
    finalize_project_world_report,
)


def finalize_project_world_open_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Compatibility alias for the shared Project World report authority."""

    return finalize_project_world_report(report)


def _finalize(report: Mapping[str, Any]) -> dict[str, Any]:
    return finalize_project_world_report(report)


def _blocked(
    project_path: Path,
    code: str,
    message: str,
    *,
    project_json_path: Path | None = None,
    project_data: Mapping[str, Any] | None = None,
    active_scene: str = "",
    scene_path: Path | None = None,
    manifest_validation: Mapping[str, Any] | None = None,
    warnings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return _finalize(
        {
            "status": "blocked",
            "code": str(code),
            "message": str(message),
            "project_path": str(project_path),
            "project_json_path": str(project_json_path or project_path / "project.json"),
            "project_data": dict(project_data or {}),
            "previous_project_path": "",
            "same_project": False,
            "flush": {
                "required": False,
                "project_path": "",
                "update_active_scene": False,
            },
            "active_scene": str(active_scene),
            "scene_path": str(scene_path or ""),
            "scene_exists": bool(scene_path and scene_path.is_file()),
            "manifest_validation": dict(manifest_validation or {}),
            "warnings": list(warnings or []),
            "application_steps": [],
        }
    )


def _manifest_validation_report(
    project_data: Mapping[str, Any],
    *,
    repo_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    mode = str(project_data.get("manifest_validation_mode", "warn") or "warn").lower()
    disabled = project_data.get("disabled_plugins", [])
    if not isinstance(disabled, list):
        disabled = []
    try:
        editor_version = get_loom_editor_version_from_pyproject(repo_root)
        result = validate_project_manifest(
            dict(project_data),
            repo_root=repo_root,
            editor_version=editor_version,
            disabled_plugins=disabled,
        )
        report = {
            "ok": bool(result.ok),
            "mode": mode,
            "editor_version": editor_version,
            "issues": [
                {
                    "level": str(issue.level),
                    "code": str(issue.code),
                    "message": str(issue.message),
                }
                for issue in result.issues
            ],
            "required_packages": [str(item) for item in result.required_packages],
            "missing_packages": [str(item) for item in result.missing_packages],
        }
    except Exception as exc:
        report = {
            "ok": True,
            "mode": mode,
            "editor_version": "",
            "issues": [],
            "required_packages": [],
            "missing_packages": [],
            "validation_error": f"{type(exc).__name__}: {exc}",
        }
        warnings.append(
            {
                "code": "manifest_validation_unavailable",
                "message": report["validation_error"],
            }
        )
    return report, warnings


def manifest_validation_result_from_report(
    report: Mapping[str, Any],
) -> ManifestValidationResult:
    """Rebuild the existing UI-facing validation value from JSON-safe evidence."""

    issues = []
    raw_issues = report.get("issues", [])
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, Mapping):
                continue
            issues.append(
                ManifestIssue(
                    level=str(item.get("level", "warning") or "warning"),
                    code=str(item.get("code", "manifest_issue") or "manifest_issue"),
                    message=str(item.get("message", "") or ""),
                )
            )
    required = report.get("required_packages", [])
    missing = report.get("missing_packages", [])
    return ManifestValidationResult(
        ok=bool(report.get("ok", True)),
        issues=issues,
        required_packages=[str(item) for item in required] if isinstance(required, list) else [],
        missing_packages=[str(item) for item in missing] if isinstance(missing, list) else [],
    )


def finalize_project_world_open_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a canonical JSON-safe preparation/application report."""

    return _finalize(dict(report))


def prepare_project_world_open(
    project_path: str | Path,
    *,
    previous_project_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Prepare deterministic facts before any concrete Host mutates state."""

    project = Path(project_path).expanduser().resolve()
    project_json = project / "project.json"
    if not project_json.is_file():
        return _blocked(
            project,
            "project_manifest_missing",
            "project.json not found",
            project_json_path=project_json,
        )

    try:
        raw_project_data = json.loads(project_json.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return _blocked(
            project,
            "project_manifest_invalid_json",
            f"invalid project.json: {exc}",
            project_json_path=project_json,
        )
    except OSError as exc:
        return _blocked(
            project,
            "project_manifest_unreadable",
            f"{type(exc).__name__}: {exc}",
            project_json_path=project_json,
        )
    if not isinstance(raw_project_data, dict):
        return _blocked(
            project,
            "project_manifest_not_object",
            "project.json root must be an object",
            project_json_path=project_json,
        )
    project_data = dict(raw_project_data)

    active_scene_raw = str(project_data.get("active_scene", "main_scene.pond") or "main_scene.pond")
    active_scene = active_scene_raw.replace("\\", "/").strip()
    active_path = PurePosixPath(active_scene)
    if active_path.is_absolute() or ".." in active_path.parts:
        return _blocked(
            project,
            "active_scene_outside_project",
            "active_scene must stay under the Project World scenes directory",
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
        )
    normalized_parts = [part for part in active_path.parts if part not in {"", "."}]
    if not normalized_parts:
        active_scene = "main_scene.pond"
        normalized_parts = [active_scene]
    else:
        active_scene = "/".join(normalized_parts)
    if PurePosixPath(active_scene).suffix.lower() != ".pond":
        return _blocked(
            project,
            "active_scene_not_pond",
            "active_scene must reference a .pond scene",
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
        )

    scenes_root = (project / "scenes").resolve()
    scene_path = (scenes_root / Path(*normalized_parts)).resolve()
    try:
        scene_path.relative_to(scenes_root)
    except ValueError:
        return _blocked(
            project,
            "active_scene_outside_project",
            "active_scene resolves outside the Project World scenes directory",
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
            scene_path=scene_path,
        )

    if repo_root is None:
        from core.VitaLoom.core.bundle_paths import resource_root

        validation_root = resource_root()
    else:
        validation_root = Path(repo_root).resolve()

    manifest_validation, warnings = _manifest_validation_report(
        project_data,
        repo_root=validation_root,
    )
    if (
        str(manifest_validation.get("mode", "warn")) == "block"
        and not bool(manifest_validation.get("ok", True))
    ):
        return _blocked(
            project,
            "manifest_validation_blocked",
            "project manifest validation blocked opening",
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
            scene_path=scene_path,
            manifest_validation=manifest_validation,
            warnings=warnings,
        )

    try:
        lock_admission, lock_warnings = _project_lock_admission_report(
            project,
            repo_root=validation_root,
        )
    except Exception as exc:
        return _blocked(
            project,
            "project_lock_admission_unavailable",
            f"project lock admission could not be verified: {type(exc).__name__}: {exc}",
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
            scene_path=scene_path,
        )
    warnings.extend(lock_warnings)
    if lock_admission["status"] != "ready":
        return _blocked(
            project,
            "project_lock_admission_blocked",
            str(lock_admission.get("blocking_issue_summary") or "project lock admission blocked"),
            project_json_path=project_json,
            project_data=project_data,
            active_scene=active_scene,
            scene_path=scene_path,
            manifest_validation=manifest_validation,
            warnings=warnings,
        ) | {"lock_admission": lock_admission}
    scene_exists = scene_path.is_file()
    if not scene_exists:
        warnings.append(
            {
                "code": "active_scene_missing",
                "message": f"active scene not found: {scene_path}",
            }
        )

    previous = (
        Path(previous_project_path).expanduser().resolve()
        if previous_project_path
        else None
    )
    same_project = bool(
        previous is not None
        and os.path.normcase(str(previous)) == os.path.normcase(str(project))
    )
    flush = {
        "required": previous is not None,
        "project_path": str(previous or ""),
        "update_active_scene": bool(previous is not None and not same_project),
    }
    application_steps = list(_APPLICATION_STEPS)
    if flush["required"]:
        application_steps.insert(0, "flush_previous_world")

    return _finalize(
        {
            "status": "ready",
            "code": "",
            "message": "Project World is ready for Host application",
            "project_path": str(project),
            "project_json_path": str(project_json),
            "project_data": project_data,
            "previous_project_path": str(previous or ""),
            "same_project": same_project,
            "flush": flush,
            "active_scene": active_scene,
            "scene_path": str(scene_path),
            "scene_exists": scene_exists,
            "manifest_validation": manifest_validation,
            "lock_admission": lock_admission,
            "warnings": warnings,
            "application_steps": application_steps,
        }
    )
