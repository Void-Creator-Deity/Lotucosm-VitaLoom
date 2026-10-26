from __future__ import annotations

import json
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths


install_runtime_paths(Path(__file__).resolve().parents[1])

from core.Lotucosm.runtime.world_bridge_e366_live_checkpoint_admission import (
    build_worldbridge_e366_live_checkpoint_admission_contract,
    validate_worldbridge_e366_live_checkpoint_admission_contract,
)


if __name__ == "__main__":
    result = build_worldbridge_e366_live_checkpoint_admission_contract()
    valid = validate_worldbridge_e366_live_checkpoint_admission_contract(result)["valid"]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if valid and result["contract_valid"] else 1)
