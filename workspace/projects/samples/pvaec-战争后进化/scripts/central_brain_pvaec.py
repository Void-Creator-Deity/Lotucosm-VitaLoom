# -*- coding: utf-8 -*-
"""PVAEC 战后进化样例兼容入口：复用产品 runtime 的 central brain Implementation。

职责:
    保留既有 Project World 脚本路径，使场景动态脚本加载 seam 能继续发现
    ``CentralBrainPvaec``，但不在工程目录复制引擎算法。

排错:
    导入失败时检查 Hub 是否已把锁定产品版本的 runtime 加入 ``PYTHONPATH``。
"""
from core.Lotucosm.sr_central_brain_pvaec import CentralBrainPvaec

__all__ = ["CentralBrainPvaec"]
