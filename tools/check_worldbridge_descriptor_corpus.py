#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only diagnostic for WorldBridge descriptor corpus coverage."""
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

from core.Lotucosm.runtime.world_bridge_descriptor_corpus import (  # noqa: E402
    diagnose_descriptor_corpus,
    discover_canonical_ponds,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "workspace" / "projects" / "samples")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or discover_canonical_ponds(args.root)
    diagnostic = diagnose_descriptor_corpus(paths)
    print(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if diagnostic["sample_count"] > 0 and diagnostic["all_round_trip_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
