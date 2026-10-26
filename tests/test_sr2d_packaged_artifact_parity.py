# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

from fixtures.sr2d_parity_cases import (
    SR2D_PARITY_CASES,
    assert_snapshots_close,
    clone_entities,
    snapshot,
)
from core.Lotucosm.sr_physics2d import (
    CppSrPhysics2DAdapter,
    PythonSrPhysics2DAdapter,
)


EXPECTED_ROOT = os.environ.get("VITALOOM_SR2D_EXPECT_MODULE_ROOT", "").strip()
pytestmark = pytest.mark.skipif(
    not EXPECTED_ROOT,
    reason="packaged artifact root is provided only by the E31 isolated verifier",
)


def test_packaged_cpp_module_is_loaded_from_expected_install_root() -> None:
    module = importlib.import_module("_vitalloom_sr2d_cpp")
    module_path = Path(module.__file__).resolve()
    expected = Path(EXPECTED_ROOT).resolve()

    assert module_path.is_relative_to(expected)
    assert callable(getattr(module, "step_pvaec_circles", None))
    assert getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None) == 1


@pytest.mark.parametrize("case", SR2D_PARITY_CASES, ids=lambda case: case.name)
def test_packaged_cpp_adapter_matches_python_oracle(case) -> None:
    py_entities = clone_entities(case)
    cpp_entities = clone_entities(case)

    PythonSrPhysics2DAdapter().step(
        py_entities,
        dt=case.dt,
        width=case.width,
        height=case.height,
        mode=case.mode,
        springs=case.springs,
        config=case.config,
    )
    CppSrPhysics2DAdapter().step(
        cpp_entities,
        dt=case.dt,
        width=case.width,
        height=case.height,
        mode=case.mode,
        springs=case.springs,
        config=case.config,
    )

    assert_snapshots_close(snapshot(cpp_entities), snapshot(py_entities))
