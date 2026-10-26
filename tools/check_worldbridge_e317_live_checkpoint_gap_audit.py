from __future__ import annotations

import json
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths


install_runtime_paths(Path(__file__).resolve().parents[1])

from core.Lotucosm.runtime.world_bridge_e317_live_checkpoint_gap_audit import (
    build_worldbridge_e317_live_checkpoint_gap_audit,
)


if __name__ == "__main__":
    result = build_worldbridge_e317_live_checkpoint_gap_audit()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
