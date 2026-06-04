# -*- coding: utf-8 -*-
"""SR 演化基因：将 MindProfile 子集当作可遗传、可突变向量（与 PS Organism 组件解耦）。

架构数据流::

    父代 mind dict 子集 → mind_dict_mutate → 子代基因 + delta 日志

历史坑::

    - 仅 GENE_KEYS 三键参与突变；其余 MindProfile 字段由场景/脚本静态配置
"""
from __future__ import annotations

import random
from typing import Dict, Mapping, Tuple

# 与 CentralBrainPvaec / 用户叙述对齐的可演化键（先小步验证，后续可扩展）。
GENE_KEYS: Tuple[str, ...] = ("wander_amp", "gain_high_stress", "mem_alpha")

_BOUNDS: Dict[str, Tuple[float, float]] = {
    "wander_amp": (4.0, 88.0),
    "gain_high_stress": (6.0, 128.0),
    "mem_alpha": (0.04, 0.88),
}


def mind_dict_mutate(
    parent_slice: Mapping[str, float],
    sigma: float,
    rng: random.Random | None = None,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """对基因子集做高斯突变并钳制到 _BOUNDS。

    职责:
        仅处理 parent_slice 中存在的 GENE_KEYS，返回子代基因 dict 与各键 delta。

    时机:
        宿主繁殖/演化流水线在复制父代 mind 参数时调用。

    不变量:
        sigma < 0 视为 0；缺键跳过；输出值在 _BOUNDS 内。

    排错:
        子代行为无变化 → 父代 slice 缺键或 sigma=0；见 docs/sr_mind_profile_fields.md。
    """
    rnd = rng or random
    child: Dict[str, float] = {}
    deltas: Dict[str, float] = {}
    sig = max(0.0, float(sigma))
    for k in GENE_KEYS:
        if k not in parent_slice:
            continue
        old = float(parent_slice[k])
        delta = rnd.gauss(0.0, sig) if sig > 0 else 0.0
        new = old + delta
        if k in _BOUNDS:
            lo, hi = _BOUNDS[k]
            new = max(lo, min(hi, new))
        child[k] = new
        deltas[k] = new - old
    return child, deltas


def format_gene_deltas(deltas: Mapping[str, float]) -> str:
    """将 delta 格式化为日志友好字符串（按 GENE_KEYS 顺序）。

    职责:
        输出 ``wander_amp=+1.23, ...`` 或空串。

    时机:
        繁殖 HUD / 控制台记录子代基因变化时。

    不变量:
        仅包含 deltas 中且属于 GENE_KEYS 的键。

    排错:
        空串 → 无有效突变或父代未提供基因键。
    """
    parts = [f"{k}={deltas[k]:+.2f}" for k in GENE_KEYS if k in deltas]
    return ", ".join(parts) if parts else ""
