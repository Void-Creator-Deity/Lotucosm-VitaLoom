#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reject unadmitted live component/graph writes in WorldBridge integration code."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_static_boundary import (  # noqa: E402
    scan_worldbridge_live_mapping_boundary,
)


def main() -> int:
    runtime = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom" / "versions" / "1.0.0" / "runtime"
    result = scan_worldbridge_live_mapping_boundary(runtime)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
