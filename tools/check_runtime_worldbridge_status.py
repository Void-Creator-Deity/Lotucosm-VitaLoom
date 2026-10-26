#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge/unified Pond gate evidence."""
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

from core.VitaLoom.simulation.runtime_worldbridge_status import (  # noqa: E402
    build_runtime_worldbridge_status,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", type=Path)
    args = parser.parse_args(argv)
    status = build_runtime_worldbridge_status(args.project_path)
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    expected = bool(status["read_only"]) and not bool(status["default_ready"])
    expected = expected and "full_unified_runtime_replay" in set(status["do_not_claim"])
    if args.project_path is None:
        expected = expected and status["runtime_mode"] == "dual"
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
