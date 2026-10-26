#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e313_bounded_replay_corpus import (
    build_worldbridge_e313_bounded_replay_corpus,
)


def main() -> int:
    corpus = build_worldbridge_e313_bounded_replay_corpus()
    print(json.dumps(corpus, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if corpus["protocol_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
