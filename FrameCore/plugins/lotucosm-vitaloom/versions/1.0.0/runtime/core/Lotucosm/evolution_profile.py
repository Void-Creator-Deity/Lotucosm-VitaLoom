# -*- coding: utf-8
"""EvolutionProfile：SR/PS 共用演化参数字典（Phase C）。

职责: 从 project.json evolution_defaults 与脚本 props.evo 合并为单一 profile；
      供 InheritanceSystem、SR 繁殖、Dock 写回共用。
排错: 见 docs/pvaec_inheritance_alignment.md Phase C。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple

from core.Lotucosm.sr_mind_gene import GENE_KEYS

_FLOAT_KEYS = (
    "mutation_rate",
    "selection_pressure",
    "elitism_rate",
    "memory_gene_inheritance_rate",
    "memory_gene_mutation_rate",
    "mutation_sigma",
)
_INT_KEYS = (
    "evolution_generation_interval",
    "max_population",
    "initial_organisms",
    "ticks",
)


@dataclass(frozen=True)
class EvolutionProfile:
    """工程级演化默认（C.1 扩展 + MemoryGene / SR mind 对齐）。"""

    mutation_rate: float = 0.08
    selection_pressure: float = 0.5
    elitism_rate: float = 0.1
    evolution_generation_interval: int = 5
    max_population: int = 200
    initial_organisms: int = 24
    ticks: int = 500
    memory_gene_inheritance_rate: float = 0.8
    memory_gene_mutation_rate: float = 0.01
    mutation_sigma: float = 0.38
    gene_keys: Tuple[str, ...] = GENE_KEYS


def _float(raw: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return float(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def _int(raw: Mapping[str, Any], key: str, default: int) -> int:
    try:
        return int(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def evolution_profile_from_mapping(*layers: Optional[Mapping[str, Any]]) -> EvolutionProfile:
    """按层合并 defaults / evo / 覆盖项，后层优先。"""
    merged: Dict[str, Any] = {}
    for layer in layers:
        if not layer:
            continue
        merged.update(dict(layer))
    base = EvolutionProfile()
    mut_rate = _float(merged, "mutation_rate", base.mutation_rate)
    if "memory_gene_mutation_rate" in merged:
        mem_mut_rate = _float(merged, "memory_gene_mutation_rate", base.memory_gene_mutation_rate)
    else:
        mem_mut_rate = mut_rate
    if "mutation_sigma" in merged:
        mut_sigma = _float(merged, "mutation_sigma", base.mutation_sigma)
    else:
        mut_sigma = max(0.05, mut_rate * 4.75)
    raw_keys = merged.get("gene_keys")
    gene_keys: Tuple[str, ...] = base.gene_keys
    if isinstance(raw_keys, (list, tuple)) and raw_keys:
        gene_keys = tuple(str(k) for k in raw_keys)
    return EvolutionProfile(
        mutation_rate=mut_rate,
        selection_pressure=_float(merged, "selection_pressure", base.selection_pressure),
        elitism_rate=_float(merged, "elitism_rate", base.elitism_rate),
        evolution_generation_interval=_int(
            merged, "evolution_generation_interval", base.evolution_generation_interval
        ),
        max_population=_int(merged, "max_population", base.max_population),
        initial_organisms=_int(merged, "initial_organisms", base.initial_organisms),
        ticks=_int(merged, "ticks", base.ticks),
        memory_gene_inheritance_rate=_float(
            merged, "memory_gene_inheritance_rate", base.memory_gene_inheritance_rate
        ),
        memory_gene_mutation_rate=mem_mut_rate,
        mutation_sigma=mut_sigma,
        gene_keys=gene_keys,
    )


def evolution_profile_to_defaults(profile: EvolutionProfile) -> Dict[str, Any]:
    """写入 project.json evolution_defaults 的 dict。"""
    out: Dict[str, Any] = {}
    for name in _FLOAT_KEYS + _INT_KEYS:
        out[name] = getattr(profile, name)
    out["gene_keys"] = list(profile.gene_keys)
    return out


def apply_profile_to_evo_props(
    evo: Optional[MutableMapping[str, Any]],
    profile: EvolutionProfile,
    *,
    fill_missing_only: bool = True,
) -> Dict[str, Any]:
    """将 profile 合并进 SR 脚本 props['evo']。"""
    out: Dict[str, Any] = dict(evo) if isinstance(evo, dict) else {}
    mapping = {
        "mutation_rate": profile.mutation_rate,
        "mutation_sigma": profile.mutation_sigma,
        "memory_gene_inheritance_rate": profile.memory_gene_inheritance_rate,
        "memory_gene_mutation_rate": profile.memory_gene_mutation_rate,
        "selection_pressure": profile.selection_pressure,
        "elitism_rate": profile.elitism_rate,
        "generation_interval": profile.evolution_generation_interval,
    }

    for key, val in mapping.items():
        if fill_missing_only and key in out:
            continue
        out[key] = val
    return out


def apply_profile_to_inheritance_system(inheritance_system: Any, profile: EvolutionProfile) -> None:
    """PS InheritanceSystem 与 profile 对齐。"""
    if hasattr(inheritance_system, "set_mutation_rate"):
        inheritance_system.set_mutation_rate(profile.memory_gene_mutation_rate)
    if hasattr(inheritance_system, "set_memory_gene_inheritance_rate"):
        inheritance_system.set_memory_gene_inheritance_rate(profile.memory_gene_inheritance_rate)


def resolve_sr_reproduction_rates(
    evo_props: Optional[Mapping[str, Any]],
    project_defaults: Optional[Mapping[str, Any]] = None,
) -> EvolutionProfile:
    """SR 繁殖：合并 project defaults 与 props.evo。"""
    return evolution_profile_from_mapping(project_defaults, evo_props)
