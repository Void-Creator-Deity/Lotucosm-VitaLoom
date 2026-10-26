# -*- coding: utf-8 -*-
"""Qt-free authority for creating one Project World scaffold."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from core.VitaLoom.project.project_manifest import LOOM_EDITOR_VERSION


class ProjectWorldCreationError(RuntimeError):
    """Project World scaffold creation failed without a usable result."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def normalize_project_type(value: str) -> str:
    key = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "": "sr2d",
        "default": "sr2d",
        "2d": "sr2d",
        "sr": "sr2d",
        "sr_2d": "sr2d",
        "pvaec_cell": "pvaec",
        "cell": "pvaec",
        "tutorial_roguelike": "roguelike",
        "mini_roguelike": "roguelike",
    }
    return aliases.get(
        key,
        key if key in {"blank", "sr2d", "pvaec", "roguelike"} else "sr2d",
    )


def default_required_capabilities(project_type: str) -> dict[str, str]:
    required = {
        "vitalloom.core.platform": ">=1.0.0",
        "vitalloom.editor_essentials": ">=1.0.0",
    }
    if project_type != "blank":
        required.update(
            {
                "vitalloom.lotuspond.runtime": ">=1.0.0",
                "vitalloom.engine.sr2d": ">=1.0.0",
            }
        )
    if project_type == "pvaec":
        required["vitalloom.pvaec.simulation"] = ">=1.0.0"
    return required


def default_capability_tags(project_type: str) -> list[str]:
    tags = ["project_plugins"]
    if project_type != "blank":
        tags.extend(["sr2d", "game_script"])
    if project_type in {"pvaec", "roguelike"}:
        tags.append(project_type)
    return tags


def create_project_world(
    name: str,
    target: str | Path,
    *,
    template: str | None = None,
    templates_dir: str | Path | None = None,
    description: str = "",
    project_type: str = "sr2d",
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Create one L4 Project World without importing a concrete Host Adapter."""

    project_path = Path(target)
    if project_path.exists():
        raise ProjectWorldCreationError(
            "project_target_exists",
            f"project target already exists: {project_path}",
        )

    project_type_key = normalize_project_type(project_type or template or "sr2d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    created_project_root = False

    try:
        project_path.mkdir(parents=True, exist_ok=False)
        created_project_root = True
        for folder in ("assets", "scripts", "scenes"):
            (project_path / folder).mkdir()

        manifest = {
            "name": str(name),
            "description": str(description),
            "version": "1.0.0",
            "project_type": project_type_key,
            "suite_id": "lotucosm.vitaloom.suite",
            "product_id": "lotucosm-vitaloom",
            "loom_editor_version": LOOM_EDITOR_VERSION,
            "manifest_validation_mode": "warn",
            "capabilities": default_capability_tags(project_type_key),
            "required_capabilities": default_required_capabilities(project_type_key),
            "package_state": {
                "installed": {},
                "version_overrides": {},
                "operation_log": [],
                "history": [],
                "rollback_points": [],
            },
            "enabled_plugins": [],
            "disabled_plugins": [],
            "active_scene": "main_scene.pond",
            "created_at": timestamp,
            "modified_at": timestamp,
            "settings": {
                "auto_save": True,
                "auto_save_interval": 300,
                "backup_enabled": True,
                "backup_count": 5,
            },
        }
        (project_path / "project.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        template_root = (
            Path(templates_dir) / str(template)
            if templates_dir is not None and template
            else None
        )
        if template_root is not None and template_root.is_dir():
            for item in template_root.iterdir():
                destination = project_path / item.name
                if item.is_dir():
                    shutil.copytree(item, destination, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, destination)
        else:
            default_scene = {
                "name": "主场景",
                "version": "1.0",
                "pond_config": {
                    "name": "默认莲池",
                    "size": [1200, 800],
                    "initial_components": 50,
                    "initial_organisms": 10,
                },
                "entities": [],
                "components": [],
                "resources": [],
            }
            (project_path / "scenes" / "main_scene.pond").write_text(
                json.dumps(default_scene, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        if repo_root is not None:
            try:
                from core.VitaLoom.suite.project_lock import ensure_project_lock

                ensure_project_lock(
                    project_path,
                    repo_root=Path(repo_root),
                    overwrite=True,
                )
            except Exception as exc:
                raise ProjectWorldCreationError(
                    "project_lock_creation_failed",
                    f"{type(exc).__name__}: {exc}",
                ) from exc

        return {
            "status": "created",
            "project_path": str(project_path.resolve()),
            "project_type": project_type_key,
            "lock_error": "",
        }
    except Exception as exc:
        if created_project_root and project_path.exists():
            shutil.rmtree(project_path, ignore_errors=True)
        if isinstance(exc, ProjectWorldCreationError):
            raise
        raise ProjectWorldCreationError(
            "project_creation_failed",
            f"{type(exc).__name__}: {exc}",
        ) from exc
