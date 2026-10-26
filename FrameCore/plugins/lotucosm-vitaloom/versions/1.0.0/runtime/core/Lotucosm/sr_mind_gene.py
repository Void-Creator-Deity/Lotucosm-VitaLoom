# -*- coding: utf-8 -*-
"""SR 演化基因：将 MindProfile 子集当作可遗传、可突变向量（与 PS Organism 组件解耦）。

架构数据流::

    父代 mind dict 子集 → mind_dict_mutate → 子代基因 + delta 日志

gene_keys 可由 EvolutionProfile.gene_keys / project.json 配置；缺省为 GENE_KEYS 三键。
"""
from __future__ import annotations

import random
from typing import Dict, Mapping, Sequence, Tuple

from core.Lotucosm.sr_mind_profile import MindProfile

# 与 CentralBrainPvaec / 用户叙述对齐的默认可演化键。
GENE_KEYS: Tuple[str, ...] = ("wander_amp", "gain_high_stress", "mem_alpha")

_BOUNDS: Dict[str, Tuple[float, float]] = {
    "wander_amp": (4.0, 88.0),
    "gain_high_stress": (6.0, 128.0),
    "mem_alpha": (0.04, 0.88),
    "gain_low_stress": (2.0, 80.0),
    "max_speed": (40.0, 600.0),
    "field_flee_gain": (4.0, 60.0),
    "niche_stress_coeff": (0.01, 0.5),
}


def resolve_gene_keys(gene_keys: Sequence[str] | None) -> Tuple[str, ...]:
    if not gene_keys:
        return GENE_KEYS
    out = tuple(str(k) for k in gene_keys if k)
    return out or GENE_KEYS


def bounds_for_gene_key(key: str) -> Tuple[float, float]:
    if key in _BOUNDS:
        return _BOUNDS[key]
    defaults = MindProfile.default_main_world().to_dict()
    if key in defaults:
        v = float(defaults[key])
        span = max(abs(v) * 0.45, 1.0)
        return (v - span, v + span)
    return (0.0, 999.0)


def mind_dict_mutate(
    parent_slice: Mapping[str, float],
    sigma: float,
    rng: random.Random | None = None,
    *,
    gene_keys: Sequence[str] | None = None,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """对基因子集做高斯突变并钳制到 bounds（gene_keys 可来自 EvolutionProfile）。"""
    # Keep the legacy optional call shape deterministic without borrowing the
    # process-global random module. Runtime callers must pass their owner.
    rnd = rng if rng is not None else random.Random(0)
    keys = resolve_gene_keys(gene_keys)
    child: Dict[str, float] = {}
    deltas: Dict[str, float] = {}
    sig = max(0.0, float(sigma))
    for k in keys:
        if k not in parent_slice:
            continue
        old = float(parent_slice[k])
        delta = rnd.gauss(0.0, sig) if sig > 0 else 0.0
        new = old + delta
        lo, hi = bounds_for_gene_key(k)
        new = max(lo, min(hi, new))
        child[k] = new
        deltas[k] = new - old
    return child, deltas


def format_gene_deltas(
    deltas: Mapping[str, float],
    *,
    gene_keys: Sequence[str] | None = None,
) -> str:
    """将 delta 格式化为日志友好字符串。"""
    keys = resolve_gene_keys(gene_keys)
    parts = [f"{k}={deltas[k]:+.2f}" for k in keys if k in deltas]
    return ", ".join(parts) if parts else ""
