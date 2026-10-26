#!/usr/bin/env python3
"""Produce parity, provenance and benchmark evidence for native SR2D admission."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.sr_physics2d import (
    CppSrPhysics2DAdapter,
    Physics2DMode,
    PythonSrPhysics2DAdapter,
    SrPhysics2DConfig,
    is_cpp_sr2d_available,
    is_native_sr2d_available,
)
from tools.benchmark_engine import _make_sr2d_entities


DT = 1.0 / 60.0
WIDTH = 640.0
HEIGHT = 480.0
TICKS = 120
TOLERANCE = 1e-4


def _snapshot(entities: list[Any]) -> list[tuple[float, float, float, float]]:
    return [
        (
            float(entity.position[0]),
            float(entity.position[1]),
            float(entity.velocity[0]),
            float(entity.velocity[1]),
        )
        for entity in entities
    ]


def _max_delta(
    left: list[tuple[float, float, float, float]],
    right: list[tuple[float, float, float, float]],
) -> float:
    if len(left) != len(right):
        return float("inf")
    maximum = 0.0
    for left_row, right_row in zip(left, right):
        for left_value, right_value in zip(left_row, right_row):
            maximum = max(maximum, abs(left_value - right_value))
    return maximum


def _config(broadphase: str) -> SrPhysics2DConfig:
    return SrPhysics2DConfig(
        contact_iterations=2,
        pvaec_broadphase=broadphase,
    )


def _parity_scenario(name: str, variant: str, broadphase: str) -> dict[str, Any]:
    python_entities = _make_sr2d_entities(variant)
    native_entities = copy.deepcopy(python_entities)
    python = PythonSrPhysics2DAdapter()
    native = CppSrPhysics2DAdapter()
    config = _config(broadphase)
    first_mismatch_tick: int | None = None
    first_mismatch_delta: float | None = None
    maximum_delta = 0.0
    for tick in range(1, TICKS + 1):
        python.step(
            python_entities,
            dt=DT,
            width=WIDTH,
            height=HEIGHT,
            mode=Physics2DMode.PVAEC,
            springs=None,
            config=config,
        )
        native.step(
            native_entities,
            dt=DT,
            width=WIDTH,
            height=HEIGHT,
            mode=Physics2DMode.PVAEC,
            springs=None,
            config=config,
        )
        delta = _max_delta(
            _snapshot(python_entities),
            _snapshot(native_entities),
        )
        maximum_delta = max(maximum_delta, delta)
        if delta > TOLERANCE and first_mismatch_tick is None:
            first_mismatch_tick = tick
            first_mismatch_delta = delta
            break
    return {
        "name": name,
        "variant": variant,
        "broadphase": broadphase,
        "entities": len(python_entities),
        "ticks_compared": (
            TICKS if first_mismatch_tick is None else first_mismatch_tick
        ),
        "tolerance": TOLERANCE,
        "maximum_delta": maximum_delta,
        "first_mismatch_tick": first_mismatch_tick,
        "first_mismatch_delta": first_mismatch_delta,
        "parity": first_mismatch_tick is None,
    }


def _benchmark(
    adapter_label: str,
    variant: str,
    broadphase: str,
    *,
    repeats: int,
) -> dict[str, Any]:
    adapter = (
        PythonSrPhysics2DAdapter()
        if adapter_label == "python"
        else CppSrPhysics2DAdapter()
    )
    config = _config(broadphase)
    durations: list[float] = []
    first_position: list[float] | None = None
    for _ in range(repeats):
        entities = _make_sr2d_entities(variant)
        started = time.perf_counter()
        for _tick in range(TICKS):
            adapter.step(
                entities,
                dt=DT,
                width=WIDTH,
                height=HEIGHT,
                mode=Physics2DMode.PVAEC,
                springs=None,
                config=config,
            )
        durations.append((time.perf_counter() - started) * 1000.0)
        if first_position is None:
            first_position = [
                float(entities[0].position[0]),
                float(entities[0].position[1]),
            ]
    return {
        "adapter": adapter.__class__.__name__,
        "variant": variant,
        "broadphase": broadphase,
        "entities": len(entities),
        "ticks": TICKS,
        "repeats": repeats,
        "median_ms": statistics.median(durations),
        "min_ms": min(durations),
        "max_ms": max(durations),
        "durations_ms": durations,
        "first_position": first_position,
    }


def _module_provenance() -> dict[str, Any]:
    if not is_cpp_sr2d_available():
        return {"available": False}
    import _vitalloom_sr2d_cpp as module

    artifact = Path(module.__file__).resolve()
    return {
        "available": True,
        "module_name": module.__name__,
        "artifact": str(artifact),
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "abi_version": getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None),
        "entropy_contract": getattr(
            module,
            "VITALLOOM_SR2D_ENTROPY_CONTRACT",
            None,
        ),
        "kernel_callable": callable(
            getattr(module, "step_pvaec_circles", None)
        ),
    }


def verify(*, repeats: int) -> dict[str, Any]:
    scenarios = (
        ("default_bruteforce", "default", "bruteforce"),
        ("dense_spatial_hash", "dense", "spatial_hash"),
        ("sparse_spatial_hash", "sparse", "spatial_hash"),
    )
    parity = [
        _parity_scenario(name, variant, broadphase)
        for name, variant, broadphase in scenarios
    ]
    benchmarks = []
    for name, variant, broadphase in scenarios:
        python_result = _benchmark(
            "python",
            variant,
            broadphase,
            repeats=repeats,
        )
        native_result = _benchmark(
            "cpp",
            variant,
            broadphase,
            repeats=repeats,
        )
        benchmarks.append(
            {
                "name": name,
                "python": python_result,
                "native": native_result,
                "speedup": (
                    python_result["median_ms"] / native_result["median_ms"]
                    if native_result["median_ms"] > 0
                    else None
                ),
                "first_position_close": _max_delta(
                    [
                        (
                            python_result["first_position"][0],
                            python_result["first_position"][1],
                            0.0,
                            0.0,
                        )
                    ],
                    [
                        (
                            native_result["first_position"][0],
                            native_result["first_position"][1],
                            0.0,
                            0.0,
                        )
                    ],
                )
                <= TOLERANCE,
            }
        )
    parity_proven = all(item["parity"] is True for item in parity)
    provenance = _module_provenance()
    provenance_proven = (
        provenance.get("available") is True
        and provenance.get("abi_version") == 1
        and provenance.get("entropy_contract") == "none"
        and provenance.get("kernel_callable") is True
    )
    benchmark_proven = all(
        item["speedup"] is not None
        and item["speedup"] > 1.0
        and item["first_position_close"] is True
        for item in benchmarks
    )
    native_admitted = (
        is_native_sr2d_available()
        and provenance_proven
        and parity_proven
        and benchmark_proven
    )
    return {
        "schema_version": 1,
        "status": "sr2d_native_admission",
        "native_available": is_native_sr2d_available(),
        "provenance": provenance,
        "provenance_proven": provenance_proven,
        "parity": parity,
        "parity_proven": parity_proven,
        "benchmarks": benchmarks,
        "benchmark_proven": benchmark_proven,
        "native_admitted": native_admitted,
        "fallback": "PythonSrPhysics2DAdapter",
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result = verify(repeats=args.repeats)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["native_admitted"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
