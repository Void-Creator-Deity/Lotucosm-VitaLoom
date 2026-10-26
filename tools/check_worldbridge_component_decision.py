#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge component/membrane decision evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_component_decision import (  # noqa: E402
    build_worldbridge_component_decision,
)


def main() -> int:
    decision = build_worldbridge_component_decision()
    print(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True))
    expected = bool(decision["read_only"])
    expected = expected and not bool(decision["maps_live_components"])
    expected = expected and not bool(decision["default_ready"])
    expected = expected and "membrane_component_graph_mapping" in set(
        decision["do_not_claim"]
    )
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
