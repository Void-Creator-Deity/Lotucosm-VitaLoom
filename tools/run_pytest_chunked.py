#!/usr/bin/env python3
"""Run the full pytest suite in bounded, isolated process chunks."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
PYTEST_ARTIFACT_ROOT = ROOT / "artifacts" / "pytest"


@dataclass(frozen=True)
class PytestChunk:
    modules: tuple[str, ...]
    test_count: int


def collect_node_ids() -> list[str]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/",
            "-p",
            "no:cacheprovider",
        ],
        cwd=ROOT,
        env=_pytest_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "pytest collection failed:\n"
            + result.stdout[-4000:]
            + result.stderr[-4000:]
        )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    ]


def build_chunks(
    node_ids: Iterable[str],
    *,
    max_tests: int,
) -> list[PytestChunk]:
    if max_tests <= 0:
        raise ValueError("max_tests must be positive")
    module_counts: OrderedDict[str, int] = OrderedDict()
    for node_id in node_ids:
        module = node_id.split("::", 1)[0]
        module_counts[module] = module_counts.get(module, 0) + 1

    chunks: list[PytestChunk] = []
    modules: list[str] = []
    count = 0
    for module, amount in module_counts.items():
        if modules and count + amount > max_tests:
            chunks.append(PytestChunk(tuple(modules), count))
            modules = []
            count = 0
        modules.append(module)
        count += amount
    if modules:
        chunks.append(PytestChunk(tuple(modules), count))
    return chunks


def run_chunks(
    chunks: Sequence[PytestChunk],
    *,
    keep_temp: bool,
) -> int:
    env = _pytest_env()
    PYTEST_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    for index, chunk in enumerate(chunks, 1):
        temp = Path(
            tempfile.mkdtemp(
                prefix=f"chunk-{index:02d}-",
                dir=PYTEST_ARTIFACT_ROOT,
            )
        )
        print(
            f"CHUNK {index}/{len(chunks)} "
            f"tests={chunk.test_count} modules={len(chunk.modules)}",
            flush=True,
        )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--tb=short",
                    *chunk.modules,
                    f"--basetemp={temp}",
                    "-p",
                    "no:cacheprovider",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            tail = "\n".join(result.stdout.splitlines()[-8:])
            if tail:
                print(tail, flush=True)
            if result.returncode != 0:
                print(result.stdout[-12000:], file=sys.stderr)
                print(result.stderr[-4000:], file=sys.stderr)
                return int(result.returncode)
            print(f"CHUNK {index} OK", flush=True)
        finally:
            if not keep_temp:
                shutil.rmtree(temp, ignore_errors=True)
            else:
                print(f"CHUNK {index} TEMP RETAINED: {temp}", flush=True)
    print(f"ALL CHUNKS PASSED: {len(chunks)} processes")
    return 0


def _pytest_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    return env


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="maximum collected tests assigned to one subprocess",
    )
    parser.add_argument(
        "--list-chunks",
        action="store_true",
        help="collect and print the process split without running tests",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="retain per-chunk pytest temp directories",
    )
    parser.add_argument(
        "--start-chunk",
        type=int,
        default=1,
        help="one-based first chunk to run",
    )
    parser.add_argument(
        "--stop-chunk",
        type=int,
        default=None,
        help="one-based last chunk to run (default: final chunk)",
    )
    args = parser.parse_args(argv)

    node_ids = collect_node_ids()
    chunks = build_chunks(node_ids, max_tests=args.chunk_size)
    if args.list_chunks:
        for index, chunk in enumerate(chunks, 1):
            print(
                f"{index}: tests={chunk.test_count} "
                f"first={chunk.modules[0]} last={chunk.modules[-1]}"
            )
        print(f"TOTAL tests={len(node_ids)} chunks={len(chunks)}")
        return 0
    if args.start_chunk < 1 or args.start_chunk > len(chunks):
        parser.error("--start-chunk must select an existing chunk")
    stop_chunk = len(chunks) if args.stop_chunk is None else args.stop_chunk
    if stop_chunk < args.start_chunk or stop_chunk > len(chunks):
        parser.error("--stop-chunk must be between --start-chunk and final chunk")
    selected = chunks[args.start_chunk - 1 : stop_chunk]
    return run_chunks(selected, keep_temp=args.keep_temp)


if __name__ == "__main__":
    raise SystemExit(main())
