#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge mapping-ledger closure evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from _runtime_bootstrap import install_runtime_paths  # noqa: E402

install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_ledger_closure import (  # noqa: E402
    build_worldbridge_ledger_closure,
)


def main() -> int:
    closure = build_worldbridge_ledger_closure()
    expected = bool(closure["read_only"]) and bool(closure["ledger_closed_for_review"])
    expected = expected and not bool(closure["unified_runtime_admitted"])
    expected = expected and not bool(closure["default_ready"])
    expected = expected and bool(closure["no_admission_claim"])
    print(json.dumps(closure, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
