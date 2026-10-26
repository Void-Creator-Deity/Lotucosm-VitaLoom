#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only SR/PS/PS_REPLAY runtime replay evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.VitaLoom.simulation.runtime_replay_status import (  # noqa: E402
    build_runtime_replay_status,
)

build_status = build_runtime_replay_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", type=Path)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args(argv)
    status = build_runtime_replay_status(args.project_path, args.run_dir)
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    expected = status["read_only"] and not status["unified_pond_enabled"]
    expected = expected and {"sr_play", "ps_batch", "ps_replay"}.issubset(
        set(status["lanes"]["defined"])
    )
    expected = expected and {"unified_pond", "sr_ps_tick_merge"}.issubset(
        set(status["do_not_claim"])
    )
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
