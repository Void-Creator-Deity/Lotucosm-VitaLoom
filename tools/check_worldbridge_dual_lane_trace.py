#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the read-only WorldBridge dual-lane trace contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_dual_lane_trace import (  # noqa: E402
    build_worldbridge_dual_lane_trace_contract,
)


def main() -> int:
    contract = build_worldbridge_dual_lane_trace_contract()
    expected = bool(contract["read_only"]) and bool(contract["contract_valid"])
    expected = expected and not bool(contract["tick_merge_admitted"])
    expected = expected and not bool(contract["replay_admitted"])
    expected = expected and not bool(contract["default_ready"])
    print(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())