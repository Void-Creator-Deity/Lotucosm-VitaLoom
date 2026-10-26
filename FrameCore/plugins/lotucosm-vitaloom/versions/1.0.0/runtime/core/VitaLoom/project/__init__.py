# -*- coding: utf-8 -*-
"""Project package exports.

Keep this package import side-effect free: metadata modules such as
project_manifest are used by release gates and Suite bootstrap.
"""
from __future__ import annotations

__all__ = [
    "ProjectManager",
    "get_project_manager",
    "ProjectWizard",
]


def __getattr__(name: str):
    if name in {"ProjectManager", "get_project_manager"}:
        from core.VitaLoom.project.project_manager import (
            ProjectManager,
            get_project_manager,
        )

        return {
            "ProjectManager": ProjectManager,
            "get_project_manager": get_project_manager,
        }[name]
    if name == "ProjectWizard":
        from core.VitaLoom.project.project_wizard import ProjectWizard

        return ProjectWizard
    raise AttributeError(name)
