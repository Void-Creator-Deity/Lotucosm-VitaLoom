# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from core.Lotucosm.sr_physics2d import (
    PythonSrPhysics2DAdapter,
    is_cpp_sr2d_available,
    is_rust_sr2d_available,
    make_default_adapter,
)
from tools import benchmark_engine


def test_explicit_python_request_selects_python_adapter() -> None:
    adapter = benchmark_engine._select_sr2d_adapter("python")

    assert isinstance(adapter, PythonSrPhysics2DAdapter)


def test_auto_request_preserves_existing_adapter_policy(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "python")

    expected_type = type(make_default_adapter())
    selected = benchmark_engine._select_sr2d_adapter("auto")

    assert type(selected) is expected_type


@pytest.mark.parametrize(
    ("adapter_request", "available"),
    (
        ("cpp", is_cpp_sr2d_available),
        ("rust", is_rust_sr2d_available),
    ),
)
def test_explicit_unavailable_native_request_fails_instead_of_falling_back(
    adapter_request: str,
    available,
) -> None:
    if available():
        pytest.skip(f"{adapter_request} SR2D extension is available in this environment")

    with pytest.raises(RuntimeError):
        benchmark_engine._select_sr2d_adapter(adapter_request)


def test_sr2d_result_reports_requested_and_selected_adapter(monkeypatch) -> None:
    monkeypatch.setenv("VITALOOM_SR2D_ADAPTER", "rust")
    before = os.environ["VITALOOM_SR2D_ADAPTER"]

    result = benchmark_engine._bench_sr2d_step(adapter_request="python")

    assert result["requested_adapter"] == "python"
    assert result["selected_adapter"] == "PythonSrPhysics2DAdapter"
    assert result["adapter"] == result["selected_adapter"]
    assert os.environ["VITALOOM_SR2D_ADAPTER"] == before


def test_sr2d_cli_reports_explicit_python_selection() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/benchmark_engine.py",
            "--case",
            "sr2d",
            "--sr2d-adapter",
            "python",
            "--repeats",
            "1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)["cases"][0]["last_result"]
    assert result["requested_adapter"] == "python"
    assert result["selected_adapter"] == "PythonSrPhysics2DAdapter"

