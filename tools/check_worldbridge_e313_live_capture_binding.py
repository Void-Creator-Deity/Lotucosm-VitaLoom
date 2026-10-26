#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths
install_runtime_paths(ROOT)
from core.Lotucosm.runtime.world_bridge_e313_live_capture_binding import build_worldbridge_e313_live_capture_binding

def main() -> int:
    result = build_worldbridge_e313_live_capture_binding()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["protocol_valid"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
