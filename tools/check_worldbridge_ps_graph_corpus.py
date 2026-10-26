#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit read-only PS component graph facts."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_ps_graph_corpus import (  # noqa: E402
    build_worldbridge_ps_graph_corpus,
)


def main() -> int:
    result = build_worldbridge_ps_graph_corpus()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    evidence = result["evidence"]
    valid = result["read_only"] and not result["maps_live_objects"]
    valid = valid and evidence["organism_component_owner"]
    valid = valid and evidence["membrane_reference_owner"]
    valid = valid and evidence["connection_creation"]
    valid = valid and not evidence["cross_lane_replay"]
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
