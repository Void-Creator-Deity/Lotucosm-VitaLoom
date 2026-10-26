#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report read-only WorldBridge field-level live-mapping admission evidence."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from _runtime_bootstrap import install_runtime_paths  # noqa: E402
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_field_admission import (  # noqa: E402
    build_worldbridge_field_admission_matrix,
)


def main() -> int:
    matrix = build_worldbridge_field_admission_matrix()
    print(json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True))
    valid = matrix["read_only"] and not matrix["live_adapter_admitted"]
    valid = valid and not matrix["default_ready"] and not matrix["unified_undo_redo_runtime"]
    valid = valid and all(not field["live_adapter_admitted"] for field in matrix["fields"].values())
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
