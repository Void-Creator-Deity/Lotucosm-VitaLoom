#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit read-only facts from every registered PS ComponentFactory type."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_ps_component_corpus import (  # noqa: E402
    build_worldbridge_ps_component_corpus,
    build_worldbridge_ps_component_persistence_audit,
)


def main() -> int:
    result = build_worldbridge_ps_component_corpus()
    persistence = build_worldbridge_ps_component_persistence_audit()
    result["persistence_audit"] = persistence
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    valid = result["read_only"] and not result["maps_live_objects"]
    valid = valid and result["component_type_count"] > 0
    valid = valid and not result["evidence"]["cross_lane_replay"]
    valid = valid and persistence["read_only"] and not persistence["evidence"]["cross_lane_replay"]
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
