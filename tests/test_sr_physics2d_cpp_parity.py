# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib

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
    is_cpp_sr2d_available,
    make_default_adapter,
)


def test_cpp_auto_mode_uses_python_fallback_when_cpp_is_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "auto")

    if is_cpp_sr2d_available():
        pytest.skip("C++ SR2D extension is available in this environment")

    assert not isinstance(make_default_adapter(), CppSrPhysics2DAdapter)


@pytest.mark.parametrize("case", SR2D_PARITY_CASES, ids=lambda case: case.name)
def test_cpp_adapter_matches_python_when_extension_is_available(case) -> None:
    if not is_cpp_sr2d_available():
        pytest.skip("C++ SR2D extension is not built in this environment")

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

def _cpp_module_or_skip():
    if not is_cpp_sr2d_available():
        pytest.skip("C++ SR2D extension is not built in this environment")
    return importlib.import_module("_vitalloom_sr2d_cpp")


def _direct_cpp_step(module, *, broadphase="bruteforce"):
    return module.step_pvaec_circles(
        [(50.0, 50.0)],
        [(12.0, -4.0)],
        [18.0],
        ["organism"],
        [False],
        [False],
        1.0 / 60.0,
        320.0,
        240.0,
        {"pvaec_broadphase": broadphase},
    )


@pytest.mark.parametrize("broadphase", [" SPATIAL_HASH ", "", " BRUTEFORCE "])
def test_cpp_direct_abi_normalizes_broadphase_like_python(broadphase) -> None:
    module = _cpp_module_or_skip()

    result = _direct_cpp_step(module, broadphase=broadphase)

    assert len(result["positions"]) == 1
    assert len(result["velocities"]) == 1


def test_cpp_direct_abi_empty_input_is_noop_before_broadphase_validation() -> None:
    module = _cpp_module_or_skip()

    result = module.step_pvaec_circles(
        [],
        [],
        [],
        [],
        [],
        [],
        1.0 / 60.0,
        320.0,
        240.0,
        {"pvaec_broadphase": "invalid"},
    )

    assert result == {"positions": [], "velocities": []}


def test_cpp_direct_abi_rejects_mismatched_input_lengths() -> None:
    module = _cpp_module_or_skip()

    with pytest.raises(ValueError, match="velocities length"):
        module.step_pvaec_circles(
            [(50.0, 50.0)],
            [],
            [18.0],
            ["organism"],
            [False],
            [False],
            1.0 / 60.0,
            320.0,
            240.0,
            {},
        )


def test_cpp_direct_spatial_hash_rejects_non_finite_cell_coordinates() -> None:
    module = _cpp_module_or_skip()

    with pytest.raises(ValueError, match="finite"):
        module.step_pvaec_circles(
            [(float("nan"), 50.0)],
            [(0.0, 0.0)],
            [18.0],
            ["organism"],
            [False],
            [False],
            1.0 / 60.0,
            320.0,
            240.0,
            {"pvaec_broadphase": "spatial_hash"},
        )


