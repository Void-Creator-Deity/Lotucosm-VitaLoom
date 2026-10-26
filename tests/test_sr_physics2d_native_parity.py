# -*- coding: utf-8 -*-
from __future__ import annotations

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
    RustSrPhysics2DAdapter,
    is_cpp_sr2d_available,
    is_native_sr2d_available,
    is_rust_sr2d_available,
    make_default_adapter,
)


def test_auto_mode_uses_python_fallback_when_native_is_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "auto")

    if is_native_sr2d_available():
        pytest.skip("native SR2D extension is available in this environment")

    assert isinstance(make_default_adapter(), PythonSrPhysics2DAdapter)


@pytest.mark.parametrize(
    ("adapter_cls", "available", "label"),
    (
        (CppSrPhysics2DAdapter, is_cpp_sr2d_available, "C++"),
        (RustSrPhysics2DAdapter, is_rust_sr2d_available, "Rust"),
    ),
)
@pytest.mark.parametrize("case", SR2D_PARITY_CASES, ids=lambda case: case.name)
def test_native_adapter_matches_python_when_extension_is_available(
    adapter_cls, available, label, case
) -> None:
    if not available():
        pytest.skip(f"{label} SR2D extension is not built in this environment")

    py_entities = clone_entities(case)
    native_entities = clone_entities(case)

    PythonSrPhysics2DAdapter().step(
        py_entities,
        dt=case.dt,
        width=case.width,
        height=case.height,
        mode=case.mode,
        springs=case.springs,
        config=case.config,
    )
    adapter_cls().step(
        native_entities,
        dt=case.dt,
        width=case.width,
        height=case.height,
        mode=case.mode,
        springs=case.springs,
        config=case.config,
    )

    assert_snapshots_close(snapshot(native_entities), snapshot(py_entities))
