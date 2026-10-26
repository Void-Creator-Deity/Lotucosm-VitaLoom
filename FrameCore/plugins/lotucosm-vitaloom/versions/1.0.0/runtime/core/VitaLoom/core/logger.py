"""VitaLoom 统一日志门面；`VITALOOM_DEBUG_LOG=1` 升为 DEBUG。排错见 README.md。"""

from __future__ import annotations

import logging
import os

_CONFIGURED = False


def _setup_once():
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = logging.DEBUG if os.environ.get("VITALOOM_DEBUG_LOG", "0") == "1" else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s][%(name)s] %(message)s")
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _setup_once()
    return logging.getLogger(name)
