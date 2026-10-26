#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge mapping-loss audit evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_mapping_audit import (  # noqa: E402
    build_worldbridge_mapping_audit,
)


def main() -> int:
    audit = build_worldbridge_mapping_audit()
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    expected = bool(audit["read_only"]) and not bool(audit["lossless"])
    expected = expected and not bool(audit["default_ready"])
    expected = expected and "lossless_worldbridge_mapping" in set(audit["do_not_claim"])
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
