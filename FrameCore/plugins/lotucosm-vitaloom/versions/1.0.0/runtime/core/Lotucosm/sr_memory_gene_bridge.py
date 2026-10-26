# -*- coding: utf-8
"""SR MemoryGene 桥接：与 PS InheritanceSystem 语义对齐的序列化与代际遗传。

职责: SR 实体 sr_memory_genes 读写、spawn props initial_memory_genes、remember 写入。
时机: CentralBrainPvaec.remember / EvoCentralBrainPvaec._try_reproduce / start。
不变量: 子代 ontogeny 仍从 S0；MemoryGene 仅传偏置经验，非全知地图。
排错: 见 docs/pvaec_inheritance_alignment.md Phase B。
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Mapping, MutableSequence, Optional, Sequence, Tuple

from core.Lotucosm.memory import MemoryGene

MAX_SR_MEMORY_GENES = 32
_DEFAULT_INHERITANCE_RATE = 0.8
_DEFAULT_MUTATION_RATE = 0.01
_SITUATION_KEYS: Tuple[str, ...] = (
    "sensor_pull",
    "actuator_pull",
    "niche_pressure",
    "intrinsic_speed",
    "ambient_field",
)


def memory_gene_to_dict(gene: MemoryGene) -> Dict[str, Any]:
    """MemoryGene → JSON 可序列化 dict（spawn / EcologySnapshot 用）。"""
    return {
        "situation": str(gene.situation),
        "action_pattern": {str(k): float(v) for k, v in (gene.action_pattern or {}).items()},
        "success_rate": float(gene.success_rate),
        "strength": float(gene.strength),
        "age": int(gene.age),
    }


def memory_gene_from_dict(data: Mapping[str, Any]) -> MemoryGene:
    """dict → MemoryGene；缺键时用安全默认。"""
    situation = str(data.get("situation", ""))
    raw_pattern = data.get("action_pattern", {})
    pattern: Dict[str, float] = {}
    if isinstance(raw_pattern, dict):
        for k, v in raw_pattern.items():
            try:
                pattern[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
    try:
        success_rate = float(data.get("success_rate", 0.5))
    except (TypeError, ValueError):
        success_rate = 0.5
    gene = MemoryGene(situation, pattern, success_rate)
    try:
        gene.strength = float(data.get("strength", 1.0))
    except (TypeError, ValueError):
        gene.strength = 1.0
    try:
        gene.age = int(data.get("age", 0))
    except (TypeError, ValueError):
        gene.age = 0
    return gene


def memory_genes_to_dicts(genes: Sequence[MemoryGene]) -> List[Dict[str, Any]]:
    return [memory_gene_to_dict(g) for g in genes]


def memory_genes_from_dicts(data: Sequence[Any]) -> List[MemoryGene]:
    out: List[MemoryGene] = []
    for item in data:
        if isinstance(item, dict):
            out.append(memory_gene_from_dict(item))
    return out


def ensure_entity_memory_genes(entity: Any) -> List[MemoryGene]:
    """返回实体上可变的 sr_memory_genes 列表（不存在则创建）。"""
    genes = getattr(entity, "sr_memory_genes", None)
    if isinstance(genes, list):
        return genes
    genes = []
    entity.sr_memory_genes = genes
    return genes


def adopt_entity_memory_gene(
    entity: Any,
    gene: MemoryGene,
    *,
    max_genes: int = MAX_SR_MEMORY_GENES,
) -> None:
    """由 SR bridge 接纳一个已构造 gene，并统一执行容量淘汰。"""
    if not isinstance(gene, MemoryGene):
        raise TypeError("gene must be a MemoryGene")
    genes = ensure_entity_memory_genes(entity)
    genes.append(gene)
    limit = max(0, int(max_genes))
    if limit == 0:
        genes.clear()
    elif len(genes) > limit:
        genes.sort(key=lambda item: float(getattr(item, "strength", 1.0)))
        del genes[: len(genes) - limit]


def replace_entity_memory_genes(
    entity: Any,
    genes: Sequence[MemoryGene],
    *,
    max_genes: int = MAX_SR_MEMORY_GENES,
) -> None:
    """原子替换 SR gene 集合，保留 hydration 的容量裁剪语义。"""
    replacement = list(genes)
    if any(not isinstance(gene, MemoryGene) for gene in replacement):
        raise TypeError("genes must contain only MemoryGene instances")
    limit = max(0, int(max_genes))
    if len(replacement) > limit:
        replacement.sort(key=lambda item: float(getattr(item, "strength", 1.0)))
        replacement = replacement[-limit:] if limit else []
    ensure_entity_memory_genes(entity)[:] = replacement


def clear_entity_memory_genes(entity: Any) -> None:
    """Clear and remove the SR-owned gene store through its owner boundary.

    WorldBridge compensation uses this when a failed value-copy batch must
    restore an entity that had no gene store before the batch began.
    """
    genes = getattr(entity, "sr_memory_genes", None)
    if isinstance(genes, list):
        genes.clear()
    try:
        delattr(entity, "sr_memory_genes")
    except AttributeError:
        try:
            getattr(entity, "sr_memory_genes")
        except AttributeError:
            return
        raise RuntimeError("SR memory-gene owner cannot restore an absent store")


def load_sr_memory_genes_from_props(entity: Any, props: Mapping[str, Any] | None) -> None:
    """从脚本 props.initial_memory_genes 注入实体 sr_memory_genes。"""
    if entity is None or not props:
        return
    raw = props.get("initial_memory_genes")
    if not isinstance(raw, (list, tuple)):
        return
    replace_entity_memory_genes(entity, memory_genes_from_dicts(raw))


def inherit_sr_memory_genes(
    parent_genes: Sequence[MemoryGene],
    *,
    inheritance_rate: float = _DEFAULT_INHERITANCE_RATE,
    mutation_rate: float = _DEFAULT_MUTATION_RATE,
    rng: random.Random | None = None,
) -> List[MemoryGene]:
    """对齐 PS InheritanceSystem._inherit_memory_genes 的概率 copy/mutate。"""
    rnd = rng if rng is not None else random.Random(0)
    rate = max(0.0, min(1.0, float(inheritance_rate)))
    mut = max(0.0, min(1.0, float(mutation_rate)))
    child: List[MemoryGene] = []
    from core.Lotucosm.social_memory import is_social_memory_gene

    for gene in parent_genes:
        if is_social_memory_gene(gene):
            continue
        strength = max(0.0, min(1.0, float(getattr(gene, "strength", 1.0) or 1.0)))
        p = rate * strength
        if rnd.random() >= p:
            continue
        clone = gene.copy()
        clone.strength = max(0.1, strength * 0.85)
        if rnd.random() < mut:
            clone.mutate(randomness_rng=rnd)
        child.append(clone)
    return child[:MAX_SR_MEMORY_GENES]


def situation_from_observation(observation: Mapping[str, Any]) -> str:
    """CentralBrain 情境字符串（与 MemorySystem.retrieve 子串匹配兼容）。"""
    parts = []
    for key in _SITUATION_KEYS:
        try:
            parts.append(f"{key}={float(observation.get(key, 0.0)):.3f}")
        except (TypeError, ValueError):
            parts.append(f"{key}=0.000")
    return "|".join(parts)


def store_sr_memory_from_pvaec(
    entity: Any,
    observation: Mapping[str, Any],
    decision: Mapping[str, Any],
    success: float,
    *,
    success_threshold: float = 0.55,
    max_genes: int = MAX_SR_MEMORY_GENES,
) -> None:
    """verify 成功后写入/更新 MemoryGene（action_pattern = ax/ay 偏置）。"""
    if float(success) < float(success_threshold):
        return
    genes = ensure_entity_memory_genes(entity)
    situation = situation_from_observation(observation)
    try:
        ax = float(decision.get("ax", 0.0))
        ay = float(decision.get("ay", 0.0))
    except (TypeError, ValueError):
        ax, ay = 0.0, 0.0
    pattern = {"ax": ax, "ay": ay}
    for gene in genes:
        if gene.situation == situation:
            gene.action_pattern = dict(pattern)
            gene.success_rate = max(gene.success_rate, float(success))
            gene.strength = min(1.0, float(gene.strength) + 0.05)
            return
    adopt_entity_memory_gene(
        entity,
        MemoryGene(situation, pattern, float(success)),
        max_genes=max_genes,
    )


def retrieve_sr_memory_bias(
    observation: Mapping[str, Any],
    genes: Sequence[MemoryGene],
    *,
    blend: float = 0.12,
) -> Tuple[float, float]:
    """按情境子串匹配检索最佳 MemoryGene，返回加速度偏置。"""
    if not genes:
        return 0.0, 0.0
    situation = situation_from_observation(observation)
    matches: List[MemoryGene] = []
    for gene in genes:
        if situation in gene.situation or gene.situation in situation:
            matches.append(gene)
    if not matches:
        return 0.0, 0.0
    best = max(matches, key=lambda g: float(g.strength) * float(g.success_rate))
    ap = best.action_pattern or {}
    try:
        bx = float(ap.get("ax", 0.0)) * blend
        by = float(ap.get("ay", 0.0)) * blend
    except (TypeError, ValueError):
        return 0.0, 0.0
    return bx, by


def count_entity_memory_genes(entity: Any) -> int:
    genes = getattr(entity, "sr_memory_genes", None)
    return len(genes) if isinstance(genes, list) else 0
