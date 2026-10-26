#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge maximum-capacity decision evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_capacity_decision import (  # noqa: E402
    build_worldbridge_capacity_decision,
)


def main() -> int:
    decision = build_worldbridge_capacity_decision()
    fields = decision["fields"]
    expected = bool(decision["read_only"]) and not bool(decision["default_ready"])
    expected = expected and decision["decision"] == "creation_seed_only"
    expected = expected and all(
        item == {
            "mapping_state": "creation_only",
            "direction": "sr_to_ps",
            "continuous_sync": False,
        }
        for item in fields.values()
    )
    expected = expected and "continuous_capacity_synchronization" in set(
        decision["do_not_claim"]
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
