# -*- coding: utf-8 -*-
"""迁移吸收回归：Project World 仅保留 central brain 兼容 Adapter。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from core.Lotucosm.pvaec_script import PvaecScript
from core.Lotucosm.sr_central_brain_pvaec import CentralBrainPvaec


ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCRIPTS = (
    ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化" / "scripts" / "central_brain_pvaec.py",
    ROOT / "workspace" / "projects" / "samples" / "pvaec-战争后进化" / "scripts" / "central_brain_pvaec.py",
)


def _load_project_script(path: Path, index: int):
    spec = importlib.util.spec_from_file_location(f"test_project_central_brain_{index}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_engine_module_owns_central_brain_implementation() -> None:
    assert issubclass(CentralBrainPvaec, PvaecScript)
    assert CentralBrainPvaec.__module__ == "core.Lotucosm.sr_central_brain_pvaec"


def test_sample_project_scripts_reexport_engine_class() -> None:
    for index, path in enumerate(PROJECT_SCRIPTS):
        module = _load_project_script(path, index)
        assert module.CentralBrainPvaec is CentralBrainPvaec
        assert issubclass(module.CentralBrainPvaec, PvaecScript)
