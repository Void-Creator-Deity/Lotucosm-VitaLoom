from __future__ import annotations
import json
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(Path(__file__).resolve().parents[1])

from core.Lotucosm.runtime.world_bridge_e316_checkpoint_restore_witness import build_worldbridge_e316_checkpoint_restore_witness
if __name__ == "__main__":
 print(json.dumps(build_worldbridge_e316_checkpoint_restore_witness(), ensure_ascii=False, indent=2, sort_keys=True))
