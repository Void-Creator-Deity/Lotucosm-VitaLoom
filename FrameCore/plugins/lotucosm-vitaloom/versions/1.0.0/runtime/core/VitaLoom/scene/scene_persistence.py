# -*- coding: utf-8 -*-
"""Qt-free canonical `.pond` persistence primitives.

The legacy SceneManager may mirror a successful save into editor context and
signals, but it must not be the authority for validating or serializing a
project scene.  This module intentionally performs no Qt, EventBus, or
SceneManager work.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping


class ScenePersistenceError(ValueError):
    """A stable, caller-visible canonical persistence rejection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _json_snapshot(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        encoded = json.dumps(dict(value), ensure_ascii=False, sort_keys=True)
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ScenePersistenceError("scene_data_not_json", "Scene data must be JSON serializable") from exc
    if not isinstance(decoded, dict):
        raise ScenePersistenceError("invalid_scene_data", "Scene data must be an object")
    return decoded


def _workspace_root() -> Path:
    from core.VitaLoom.core.bundle_paths import application_root

    return (application_root() / "workspace").resolve()


def resolve_project_scene_path(raw_scene_path: str) -> tuple[Path, Path]:
    """Resolve one existing `.pond` located at `<project>/scenes/<file>`.

    The returned project root exists and contains `project.json`.  All checks
    happen before callers may touch host state or disk contents.
    """
    try:
        scene = Path(str(raw_scene_path or "")).expanduser()
        if not scene.is_absolute():
            from core.VitaLoom.core.bundle_paths import application_root

            scene = application_root() / scene
        scene = scene.resolve()
    except OSError as exc:
        raise ScenePersistenceError("path_outside_workspace", "Scene path must resolve under workspace/") from exc
    workspace = _workspace_root()
    if scene == workspace or workspace not in scene.parents:
        raise ScenePersistenceError("path_outside_workspace", "Scene path must exist under workspace/")
    if scene.suffix != ".pond" or not scene.is_file():
        raise ScenePersistenceError("scene_not_found", "Scene path must point to an existing .pond file")
    if scene.parent.name != "scenes":
        raise ScenePersistenceError("scene_outside_project", "Scene must live directly under a project's scenes/")
    project = scene.parent.parent
    if not (project / "project.json").is_file():
        raise ScenePersistenceError("project_not_found", "Scene must belong to a project with project.json")
    return scene, project


def read_project_scene_snapshot(scene: Path) -> dict[str, Any]:
    try:
        decoded = json.loads(scene.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenePersistenceError("scene_read_failed", "Scene file cannot be read as JSON") from exc
    if not isinstance(decoded, dict):
        raise ScenePersistenceError("invalid_scene_data", "Scene file must contain a JSON object")
    return _json_snapshot(decoded)


def persist_project_scene_snapshot(
    raw_scene_path: str,
    data: Mapping[str, Any],
    *,
    expected_scene: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically replace one project-local `.pond` after all stale checks.

    No host state, signal, manifest, or audit state is modified here.  The
    caller receives detached snapshots suitable for an audit or later history
    contract, but this primitive deliberately does not claim undoability.
    """
    scene, project = resolve_project_scene_path(raw_scene_path)
    next_scene = _json_snapshot(data)
    current_scene = read_project_scene_snapshot(scene)
    if expected_scene is not None:
        expected = _json_snapshot(expected_scene)
        if current_scene != expected:
            raise ScenePersistenceError(
                "stale_scene_snapshot",
                "Scene file no longer matches the expected canonical snapshot",
            )
    serialized = json.dumps(next_scene, ensure_ascii=False, indent=2) + "\n"
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(scene.parent), prefix=f".{scene.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(serialized)
            temp_name = handle.name
        os.replace(temp_name, scene)
    except OSError as exc:
        raise ScenePersistenceError("scene_write_failed", "Scene snapshot could not be persisted") from exc
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
    return {
        "scene_path": str(scene),
        "project_path": str(project),
        "previous_scene": current_scene,
        "scene_data": next_scene,
    }


def persist_scene_snapshot(
    raw_scene_path: str,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist a generic existing JSON scene path for legacy host adapters.

    Unlike `persist_project_scene_snapshot`, this preserves `save_scene_as`
    compatibility and does not impose workspace/project containment.  It still
    validates JSON before replacing the target and performs no host effects.
    """
    try:
        scene = Path(str(raw_scene_path or "")).expanduser().resolve()
    except OSError as exc:
        raise ScenePersistenceError("scene_write_failed", "Scene path cannot be resolved") from exc
    if scene.suffix != ".pond":
        raise ScenePersistenceError("scene_not_found", "Scene path must use the .pond extension")
    next_scene = _json_snapshot(data)
    if not scene.parent.is_dir():
        raise ScenePersistenceError("scene_write_failed", "Scene directory does not exist")
    serialized = json.dumps(next_scene, ensure_ascii=False, indent=2) + "\n"
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(scene.parent), prefix=f".{scene.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(serialized)
            temp_name = handle.name
        os.replace(temp_name, scene)
    except OSError as exc:
        raise ScenePersistenceError("scene_write_failed", "Scene snapshot could not be persisted") from exc
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
    return {"scene_path": str(scene), "scene_data": next_scene}
