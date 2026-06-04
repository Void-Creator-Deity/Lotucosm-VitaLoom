"""兼容 re-export：旧 import 路径 `builtin.systems.lotus_pond` → 现行莲池 API。

排错: 新代码请直接用 `core.Lotucosm.pond`。
"""

from core.Lotucosm.pond import LotusPond, Pond

__all__ = ["Pond", "LotusPond"]
