from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.pond import Pond


def verify() -> dict[str, object]:
    pond = Pond(initial_organisms=0, initial_components=0, initialize=False)
    observed: list[float] = []
    pond.root_entities.append(SimpleNamespace(update=lambda delta: observed.append(float(delta))))
    pond.update(0.05)
    result = {
        "status": "worldbridge_e401_shared_delta_contract",
        "contract_valid": pond.time == 1 and pond.simulation_time == 0.05 and observed == [0.05],
        "pond_tick_counter_preserved": pond.time == 1,
        "shared_simulation_time": pond.simulation_time == 0.05,
        "root_entity_received_shared_delta": observed == [0.05],
        "shared_clock_admitted": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
