from __future__ import annotations

import json
import math
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import resolve_worldbridge_frame_delta


def verify() -> dict[str, object]:
    paused = resolve_worldbridge_frame_delta(3.0, paused=True)
    active = resolve_worldbridge_frame_delta(1.0, paused=False)
    invalid: dict[str, bool] = {}
    for name, value in (("nan", math.nan), ("infinity", math.inf), ("negative_infinity", -math.inf)):
        try:
            resolve_worldbridge_frame_delta(value, paused=False)
        except ValueError:
            invalid[name] = True
        else:
            invalid[name] = False
    result = {
        "status": "worldbridge_e402_delta_lifecycle",
        "contract_valid": paused == 0.0 and active == 0.05 and all(invalid.values()),
        "paused_delta_zero": paused == 0.0,
        "active_delta": active,
        "invalid_delta_rejected": invalid,
        "dropped_time_accumulation": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
