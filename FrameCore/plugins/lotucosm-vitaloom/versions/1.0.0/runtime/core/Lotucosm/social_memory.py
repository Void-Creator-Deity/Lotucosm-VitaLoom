# -*- coding: utf-8
"""社会学习最小模块：观察同伴行动 → 带 social 标签的 MemoryGene。

职责: S3+ 个体将 peer 行动模式写入 memory_genes；代际按率继承；不替代 verify。
时机: PVAECCycle 验证成功后可选记录；InheritanceSystem 繁殖时拷贝 social 基因。
排错: 见 docs/pvaec_developmental_research.md §20。
"""
from __future__ import annotations

import random
from typing import Any, Dict, Mapping, Optional

from core.Lotucosm.memory import MemoryGene

SOCIAL_SITUATION_PREFIX = "social:"
MIN_STAGE_FOR_SOCIAL = 3
DEFAULT_SOCIAL_STRENGTH = 0.72
DEFAULT_SOCIAL_INHERITANCE_RATE = 0.45


def social_learning_enabled(organism: Any) -> bool:
    return bool(getattr(organism, "social_learning_enabled", False))


def social_stage_ready(subject: Any) -> bool:
    if not bool(getattr(subject, "social_learning_enabled", False)):
        return False
    if bool(getattr(subject, "developmental_ladder_enabled", False)):
        return int(getattr(subject, "developmental_stage", 0)) >= MIN_STAGE_FOR_SOCIAL
    return True


def _pattern_from_action(action_pattern: Mapping[str, Any]) -> Dict[str, float]:
    pattern: Dict[str, float] = {}
    for key, val in action_pattern.items():
        if isinstance(val, dict):
            try:
                pattern[str(key)] = float(val.get("signal", val.get("command", 0.5)) or 0.5)
            except (TypeError, ValueError):
                pattern[str(key)] = 0.5
        else:
            try:
                pattern[str(key)] = float(val)
            except (TypeError, ValueError):
                pattern[str(key)] = 0.5
    return pattern


def _pattern_from_sr_decision(decision: Mapping[str, Any]) -> Dict[str, float]:
    try:
        ax = float(decision.get("ax", 0.0) or 0.0)
        ay = float(decision.get("ay", 0.0) or 0.0)
    except (TypeError, ValueError):
        ax, ay = 0.0, 0.0
    return {"ax": ax, "ay": ay}


def make_social_situation(peer_id: str, context: str = "") -> str:
    peer = str(peer_id or "unknown")
    ctx = str(context or "").strip()
    if ctx:
        return f"{SOCIAL_SITUATION_PREFIX}{peer}|{ctx}"
    return f"{SOCIAL_SITUATION_PREFIX}{peer}"


def is_social_memory_gene(gene: Any) -> bool:
    situation = str(getattr(gene, "situation", "") or "")
    return situation.startswith(SOCIAL_SITUATION_PREFIX)


def observe_peer_action(
    organism: Any,
    peer_id: str,
    action_pattern: Mapping[str, Any],
    success_rate: float,
    *,
    context: str = "",
    strength: float = DEFAULT_SOCIAL_STRENGTH,
) -> Optional[MemoryGene]:
    """将同伴行动写入 organism.memory_genes（须 S3+ 且 social_learning_enabled）。"""
    if not social_stage_ready(organism):
        return None
    if not isinstance(getattr(organism, "memory_genes", None), list):
        return None
    pattern = _pattern_from_action(action_pattern)
    gene = MemoryGene(
        make_social_situation(peer_id, context),
        pattern,
        max(0.0, min(1.0, float(success_rate))),
    )
    gene.strength = max(0.0, min(1.0, float(strength)))
    organism.adopt_memory_gene(gene)
    return gene


def inherit_social_memory_genes(
    parent: Any,
    child: Any,
    *,
    rate: float = DEFAULT_SOCIAL_INHERITANCE_RATE,
    rng: random.Random | None = None,
) -> int:
    """子代继承父代 social MemoryGene（独立率控；非 social 基因走原 _inherit_memory_genes）。"""
    rnd = rng if rng is not None else random.Random(0)
    parent_genes = getattr(parent, "memory_genes", None)
    if not isinstance(parent_genes, list) or not isinstance(getattr(child, "memory_genes", None), list):
        return 0
    copied = 0
    for gene in parent_genes:
        if not is_social_memory_gene(gene):
            continue
        if rnd.random() >= max(0.0, min(1.0, float(rate))):
            continue
        clone = gene.copy()
        clone.strength = float(gene.strength) * 0.85
        child.adopt_memory_gene(clone)
        copied += 1
    return copied


def _organism_position(organism: Any) -> tuple[float, float] | None:
    pos = getattr(organism, "position", None)
    if pos is None:
        return None
    try:
        if hasattr(pos, "x") and hasattr(pos, "y"):
            return float(pos.x), float(pos.y)
        return float(pos[0]), float(pos[1])
    except (TypeError, ValueError, IndexError):
        return None


def nearest_peer_id(organism: Any, environment: Any) -> Optional[str]:
    """返回最近同伴 id（排除自身）。"""
    my_pos = _organism_position(organism)
    if my_pos is None or environment is None:
        return None
    orgs = getattr(environment, "organisms", None)
    if not isinstance(orgs, dict):
        return None
    best_id: Optional[str] = None
    best_dist = float("inf")
    my_id = str(getattr(organism, "id", "") or getattr(organism, "organism_id", ""))
    for oid, other in list(orgs.items()):
        if str(oid) == my_id or other is organism:
            continue
        op = _organism_position(other)
        if op is None:
            continue
        dx = op[0] - my_pos[0]
        dy = op[1] - my_pos[1]
        dist = dx * dx + dy * dy
        if dist < best_dist:
            best_dist = dist
            best_id = str(oid)
    return best_id


def maybe_record_peer_from_environment(
    organism: Any,
    environment: Any,
    action: Mapping[str, Any],
    success: float,
    *,
    threshold: float = 0.55,
) -> Optional[MemoryGene]:
    """验证成功后，将最近同伴上下文下的本行动写入 social MemoryGene。"""
    if float(success) < float(threshold):
        return None
    peer_id = nearest_peer_id(organism, environment)
    if not peer_id:
        return None
    return observe_peer_action(
        organism,
        peer_id,
        action,
        float(success),
        context="peer_near",
    )


def social_memories(organism: Any) -> list[MemoryGene]:
    genes = getattr(organism, "memory_genes", None)
    if not isinstance(genes, list):
        return []
    return [g for g in genes if is_social_memory_gene(g)]


def observe_peer_action_sr(
    entity: Any,
    peer_id: str,
    decision: Mapping[str, Any],
    success_rate: float,
    *,
    context: str = "",
    strength: float = DEFAULT_SOCIAL_STRENGTH,
) -> Optional[MemoryGene]:
    """SR：将同伴决策 ax/ay 写入 entity.sr_memory_genes。"""
    from core.Lotucosm.sr_memory_gene_bridge import adopt_entity_memory_gene

    pattern = _pattern_from_sr_decision(decision)
    gene = MemoryGene(
        make_social_situation(peer_id, context),
        pattern,
        max(0.0, min(1.0, float(success_rate))),
    )
    gene.strength = max(0.0, min(1.0, float(strength)))
    adopt_entity_memory_gene(entity, gene)
    return gene


def maybe_record_peer_from_sr_ctx(
    script: Any,
    ctx: Any,
    decision: Mapping[str, Any],
    success: float,
    *,
    threshold: float = 0.55,
) -> Optional[MemoryGene]:
    """SR PvaecScript：verify 成功后记录最近 peer 上下文下的决策。"""
    if float(success) < float(threshold):
        return None
    if not social_stage_ready(script):
        return None
    ent = getattr(script, "entity", None)
    peers = getattr(ctx, "peers", None)
    if ent is None or not peers:
        return None
    peer_id = str(getattr(peers[0], "id", "") or "peer")
    gene = observe_peer_action_sr(
        ent,
        peer_id,
        decision,
        float(success),
        context="sr_peer",
    )
    if gene is not None:
        hud = getattr(ent, "sr_debug_hud", None)
        if not isinstance(hud, dict):
            hud = {}
        hud["social_memory_count"] = len(sr_social_memories(ent))
        ent.sr_debug_hud = hud
    return gene


def sr_social_memories(entity: Any) -> list[MemoryGene]:
    from core.Lotucosm.sr_memory_gene_bridge import ensure_entity_memory_genes

    return [g for g in ensure_entity_memory_genes(entity) if is_social_memory_gene(g)]


def inherit_social_sr_memory_genes(
    parent_genes: list[MemoryGene],
    *,
    rate: float = DEFAULT_SOCIAL_INHERITANCE_RATE,
    rng: random.Random | None = None,
) -> list[MemoryGene]:
    """SR 繁殖：从父代 sr_memory_genes 拷贝 social 标签基因。"""
    # Detached tooling remains deterministic, but must not borrow the process
    # global module state. Runtime reproduction passes its owner explicitly.
    rnd = rng if rng is not None else random.Random(0)
    child: list[MemoryGene] = []
    inherit_p = max(0.0, min(1.0, float(rate)))
    for gene in parent_genes:
        if not is_social_memory_gene(gene):
            continue
        if rnd.random() >= inherit_p:
            continue
        clone = gene.copy()
        clone.strength = float(gene.strength) * 0.85
        child.append(clone)
    return child


def retrieve_social_memory_bias(
    genes: list[MemoryGene],
    *,
    blend: float = 0.08,
) -> tuple[float, float]:
    """从 social MemoryGene 聚合 ax/ay 偏置（S3+ think 用）。"""
    social = [g for g in genes if is_social_memory_gene(g)]
    if not social:
        return 0.0, 0.0
    best = max(social, key=lambda g: float(g.strength) * float(g.success_rate))
    ap = best.action_pattern or {}
    try:
        return float(ap.get("ax", 0.0)) * blend, float(ap.get("ay", 0.0)) * blend
    except (TypeError, ValueError):
        return 0.0, 0.0


def _best_ps_social_gene(organism: Any) -> Optional[MemoryGene]:
    genes = social_memories(organism)
    if not genes:
        return None
    return max(genes, key=lambda g: float(g.strength) * float(g.success_rate))


def apply_ps_social_action_bias(
    organism: Any,
    action: Mapping[str, Any],
    *,
    blend: float = 0.22,
) -> Dict[str, Any]:
    """PS generate_action：S3+ 时将 social MemoryGene 标量偏置混入首组件 signal。"""
    if not social_stage_ready(organism):
        return dict(action)
    best = _best_ps_social_gene(organism)
    if best is None:
        return dict(action)
    ap = best.action_pattern or {}
    if not ap:
        return dict(action)
    try:
        bias = float(next(iter(ap.values())))
    except (StopIteration, TypeError, ValueError):
        bias = 0.5
    out: Dict[str, Any] = dict(action)
    if not out:
        return out
    first_key = next(iter(out.keys()))
    details = out.get(first_key)
    if not isinstance(details, dict):
        details = {}
    merged = dict(details)
    try:
        old = float(merged.get("signal", 0.35) or 0.35)
    except (TypeError, ValueError):
        old = 0.35
    merged["signal"] = max(0.0, min(1.0, old + bias * blend))
    merged.setdefault("command", "explore")
    out[first_key] = merged
    return out
