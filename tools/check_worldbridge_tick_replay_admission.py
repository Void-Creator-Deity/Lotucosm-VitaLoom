#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge tick/replay admission evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (  # noqa: E402
    build_worldbridge_tick_replay_admission,
)


def main() -> int:
    evidence = build_worldbridge_tick_replay_admission()
    expected = bool(evidence["read_only"]) and evidence["runtime_mode"] == "dual"
    expected = expected and not bool(evidence["tick_merge_admitted"])
    expected = expected and not bool(evidence["full_unified_replay_admitted"])
    expected = expected and not bool(evidence["default_ready"])
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())