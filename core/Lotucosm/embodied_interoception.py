# -*- coding: utf-8 -*-
"""兼容重导出：请改用 core.Lotucosm.sr_interoception。"""
from core.Lotucosm.sr_interoception import (  # noqa: F401
    homeostatic_success,
    interoception_for_entity,
    interoception_from_environment,
)

__all__ = (
    "homeostatic_success",
    "interoception_for_entity",
    "interoception_from_environment",
)
