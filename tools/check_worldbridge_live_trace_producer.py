#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print and guard the E216 live dual-lane trace producer contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_live_trace_producer import (  # noqa: E402
    build_worldbridge_live_trace_producer_contract,
)


def main() -> int:
    contract = build_worldbridge_live_trace_producer_contract()
    print(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True))
    expected = bool(contract.get("read_only")) and bool(contract.get("contract_valid"))
    expected = expected and contract.get("atomic_checkpoint") is False
    expected = expected and contract.get("tick_merge_admitted") is False
    expected = expected and contract.get("replay_admitted") is False
    expected = expected and contract.get("default_ready") is False
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
