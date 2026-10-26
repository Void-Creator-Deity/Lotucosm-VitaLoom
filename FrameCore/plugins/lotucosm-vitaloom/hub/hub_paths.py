# -*- coding: utf-8 -*-
"""Suite Hub path helpers that do not import product runtime modules."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def application_root() -> Path:
    raw = os.environ.get("VITALOOM_APP_ROOT")
    if raw:
        return Path(raw).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[4]


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return application_root()


def suite_root() -> Path:
    raw = os.environ.get("VITALOOM_SUITE_ROOT")
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[1]


def workspace_root() -> Path:
    return application_root() / "workspace"


def projects_root() -> Path:
    return workspace_root() / "projects"


def extensions_root() -> Path:
    return workspace_root() / "extensions"


def system_state_root() -> Path:
    return workspace_root() / "state" / "system"


def hub_project_index_path() -> Path:
    return system_state_root() / "hub_projects.json"


def is_frozen_bundle() -> bool:
    return bool(getattr(sys, "frozen", False))


def is_under_application_root(path: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(application_root())
        return True
    except ValueError:
        return False
