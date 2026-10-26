# -*- coding: utf-8 -*-
"""Bootstrap product-version runtime imports for repository tools."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def install_runtime_paths(root: str | Path) -> tuple[Path, Path, Path]:
    app_root = Path(root).resolve()
    suite_root = app_root / "FrameCore" / "plugins" / "lotucosm-vitaloom"
    version_root = (
        suite_root / "versions" / "1.0.0"
    )
    runtime_root = version_root / "runtime"
    os.environ.setdefault("FRAMECORE_ROOT", str(app_root / "FrameCore"))
    os.environ.setdefault("VITALOOM_SUITE_ROOT", str(suite_root))
    os.environ.setdefault("VITALOOM_PRODUCT_VERSION_ROOT", str(version_root))
    os.environ.setdefault("VITALOOM_APP_ROOT", str(app_root))
    for path in (app_root, runtime_root, suite_root):
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
    return suite_root, version_root, runtime_root
