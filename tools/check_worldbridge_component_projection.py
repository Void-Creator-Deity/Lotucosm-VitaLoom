#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge component projection evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_component_projection import (  # noqa: E402
    build_worldbridge_component_projection,
)


def main() -> int:
    projection = build_worldbridge_component_projection()
    json.dumps(projection, ensure_ascii=False, sort_keys=True)
    print(json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True))
    expected = bool(projection["read_only"])
    expected = expected and not bool(projection["maps_live_components"])
    expected = expected and not bool(projection["default_ready"])
    expected = expected and "live_component_graph_mapping" in set(
        projection["do_not_claim"]
    )
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
