# -*- coding: utf-8 -*-
"""Project-local script bootstrap for the post-war PVAEC sample."""
from __future__ import annotations

import sys
from pathlib import Path

_CELL_SCRIPTS = Path(__file__).resolve().parent


def ensure_cell_evolution_scripts_path() -> Path:
    if _CELL_SCRIPTS.is_dir() and str(_CELL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_CELL_SCRIPTS))
    return _CELL_SCRIPTS
