# -*- coding: utf-8
"""工程级演化默认参数（C.1）：SR/PS 共用 project.json 字段。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from core.VitaLoom.project.project_world_capabilities import get_project_world_read_model

from core.Lotucosm.evolution_profile import (
    EvolutionProfile,
    apply_profile_to_evo_props,
    apply_profile_to_inheritance_system,
    evolution_profile_from_mapping,
    evolution_profile_to_defaults,
)
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.ps_developmental import (
    apply_developmental_profile_to_ps_config,
    load_developmental_profile,
)


def load_project_evolution_context(
    project_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """读取 project.json → evolution_defaults。"""
    if not project_config:
        return {}
    raw = project_config.get("evolution_defaults")
    return dict(raw) if isinstance(raw, dict) else {}


def load_evolution_profile(
    project_config: Optional[Dict[str, Any]] = None,
) -> EvolutionProfile:
    """project.json → EvolutionProfile（Phase C 统一读模型）。"""
    return evolution_profile_from_mapping(load_project_evolution_context(project_config))


def apply_evolution_defaults_to_ps_config(
    cfg: PsExperimentConfig,
    defaults: Dict[str, Any],
) -> PsExperimentConfig:
    """将工程 defaults 合并进 PS 实验配置（仅覆盖已声明键）。"""
    if not defaults:
        return cfg
    profile = evolution_profile_from_mapping(defaults)
    mapping = {
        "mutation_rate": profile.mutation_rate,
        "selection_pressure": profile.selection_pressure,
        "elitism_rate": profile.elitism_rate,
        "evolution_generation_interval": profile.evolution_generation_interval,
        "max_population": profile.max_population,
        "initial_organisms": profile.initial_organisms,
        "ticks": profile.ticks,
    }
    for src, val in mapping.items():
        if src in defaults:
            setattr(cfg, src, val)
    return cfg


def apply_developmental_profile_from_project(
    cfg: PsExperimentConfig,
    project_config: Optional[Dict[str, Any]] = None,
) -> PsExperimentConfig:
    """将 project.json → developmental_profile 合并进 PS 实验配置。"""
    profile = load_developmental_profile(project_config)
    if profile:
        apply_developmental_profile_to_ps_config(cfg, profile)
    return cfg


def evolution_defaults_from_ps_config(cfg: PsExperimentConfig) -> Dict[str, Any]:
    """从当前 PS 配置生成可写入 project.json 的 defaults（含 MemoryGene 字段）。"""
    profile = evolution_profile_from_mapping(
        {
            "mutation_rate": cfg.mutation_rate,
            "selection_pressure": cfg.selection_pressure,
            "elitism_rate": cfg.elitism_rate,
            "evolution_generation_interval": cfg.evolution_generation_interval,
            "max_population": cfg.max_population,
            "initial_organisms": cfg.initial_organisms,
            "ticks": cfg.ticks,
        }
    )
    return evolution_profile_to_defaults(profile)


def apply_evolution_defaults_to_sr_mind(
    mind: Optional[Dict[str, Any]],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """将 evolution_defaults 合并进 mind dict；pond/脚本已写键不覆盖。"""
    out = dict(mind) if isinstance(mind, dict) else {}
    if not defaults:
        return out
    profile = evolution_profile_from_mapping(defaults)
    evo = out.get("evo")
    if not isinstance(evo, dict):
        evo = {}
    out["evo"] = apply_profile_to_evo_props(evo, profile, fill_missing_only=True)
    for key in ("mutation_rate", "mem_alpha", "wander_amp"):
        if key in defaults and key not in out:
            out[key] = defaults[key]
    return out


def apply_evolution_defaults_to_sr_props(
    props: Optional[Dict[str, Any]],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """将 evolution_defaults 合并进脚本 properties（mind + evo）。"""
    out = dict(props) if isinstance(props, dict) else {}
    if not defaults:
        return out
    raw_mind = out.get("mind")
    out["mind"] = apply_evolution_defaults_to_sr_mind(
        raw_mind if isinstance(raw_mind, dict) else None,
        defaults,
    )
    profile = evolution_profile_from_mapping(defaults)
    evo = out.get("evo")
    if not isinstance(evo, dict):
        evo = {}
    out["evo"] = apply_profile_to_evo_props(evo, profile, fill_missing_only=True)
    return out


def merge_evolution_defaults_into_scene_data(
    scene_data: Dict[str, Any],
    project_config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """工程级 defaults 写入场景实体脚本的 properties（pond 显式值优先）。"""
    defaults = load_project_evolution_context(project_config)
    if not defaults:
        return scene_data
    entities = scene_data.get("entities")
    if not isinstance(entities, list):
        return scene_data
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        scripts = ent.get("scripts")
        if not isinstance(scripts, list):
            continue
        for script_data in scripts:
            if not isinstance(script_data, dict):
                continue
            props = script_data.get("properties")
            if not isinstance(props, dict):
                props = {}
                script_data["properties"] = props
            script_data["properties"] = apply_evolution_defaults_to_sr_props(props, defaults)
    return scene_data


def configure_inheritance_from_defaults(inheritance_system: Any, defaults: Dict[str, Any]) -> None:
    """PS InheritanceSystem ← evolution_defaults（MemoryGene 率对齐）。"""
    profile = evolution_profile_from_mapping(defaults)
    apply_profile_to_inheritance_system(inheritance_system, profile)


def load_project_evolution_context_from_read_model(
    project_world_read_model=None,
) -> Dict[str, Any]:
    """Load evolution defaults through the narrow Project World read Interface."""

    try:
        reader = project_world_read_model or get_project_world_read_model()
        return load_project_evolution_context(reader.current_project_world_config())
    except Exception:
        return {}


def load_project_evolution_context_from_manager() -> Dict[str, Any]:
    """Compatibility alias retained for older callers."""

    return load_project_evolution_context_from_read_model()
