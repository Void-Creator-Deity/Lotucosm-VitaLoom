# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("case_name", "expected_entities"),
    (
        ("sr2d_dense", 160),
        ("sr2d_sparse", 60),
    ),
)
def test_sr2d_benchmark_variants_report_native_metadata(
    case_name: str,
    expected_entities: int,
) -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/benchmark_engine.py", "--case", case_name, "--repeats", "1"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    result = data["cases"][0]["last_result"]
    assert result["entities"] == expected_entities
    assert "adapter" in result
    assert "native_available" in result
    assert "cpp_available" in result
    assert "rust_available" in result
    assert "iterations" in result
    assert "first_position" in result
    assert result["pvaec_broadphase"] == "bruteforce"
    assert result["pvaec_pair_count"] >= 0
    assert result["pvaec_spatial_pair_count"] >= 0
    assert result["pvaec_debug_pair_count"] >= result["pvaec_pair_count"]
    assert result["pvaec_pair_count"] == result["pvaec_debug_pair_count"]
    assert result["pvaec_spatial_pair_count"] <= result["pvaec_debug_pair_count"]


def test_sr2d_spatial_benchmark_case_is_explicit() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/benchmark_engine.py",
            "--case",
            "sr2d_sparse_spatial",
            "--repeats",
            "1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    result = data["cases"][0]["last_result"]
    assert result["variant"] == "sparse"
    assert result["pvaec_broadphase"] == "spatial_hash"
    assert result["pvaec_pair_count"] == result["pvaec_spatial_pair_count"]
    assert result["pvaec_pair_count"] <= result["pvaec_debug_pair_count"]
