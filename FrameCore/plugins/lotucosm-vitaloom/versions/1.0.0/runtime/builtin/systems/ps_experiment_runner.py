# -*- coding: utf-8 -*-
"""PS 莲池无头实验运行器：批跑 tick、采集指标、导出 JSON/CSV。

架构（双循环）::

    帧循环: Pond.update → Organism.update → 可选 PVAECCycle.run_cycle（单体内六步）
    世代循环: time % interval → PVAECOrchestrator.run_cycle（遗传/变异/选择/繁殖）

参考: EVAAA 内稳态变量驱动适应度；本实现用 energy/health 作内在验证信号。

排错: 见 docs/experiment_guide.md。
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.systems.organism_builder import equip_ps_organism
from builtin.systems.pvaec_orchestrator import PVAECOrchestrator
from builtin.systems.selection import SelectionSystem
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.ps_developmental import ensure_ps_developmental_state
from core.Lotucosm.sr_developmental_ladder import clamp_stage
from core.Lotucosm.pond import Pond
from core.Lotucosm.randomness import random_uniform_array
from core.Lotucosm.runtime.ps_runtime_snapshot_authority import (
    PsRuntimeSnapshotAuthority,
)
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PsExperimentRunner")


class PsExperimentRunner:
    """无头莲池实验：可复现、可导出、可对比参数。"""

    def __init__(
        self,
        config: PsExperimentConfig,
        *,
        snapshot_authority: PsRuntimeSnapshotAuthority | None = None,
        identity_source: DeterministicIdentitySource | None = None,
    ):
        self.config = config
        self.snapshots: List[Dict[str, Any]] = []
        self._cancel_requested = False
        self._population_at_war_end: Optional[int] = None
        self._war_pop_min: Optional[int] = None
        self._last_disaster_phase: str = "peace"
        if snapshot_authority is not None and identity_source is not None:
            raise ValueError("identity_source must be owned by the supplied snapshot_authority")
        self._snapshot_authority = snapshot_authority or PsRuntimeSnapshotAuthority(
            identity_source=identity_source
        )
        self._runtime_run_id: str | None = None
        self._randomness_rng: Any = None

    def _reset_randomness_owner(self) -> Any:
        """Create the run-local NumPy owner without touching process globals."""

        seed = self.config.seed
        if seed is None:
            self._randomness_rng = None
            return None
        try:
            seed_int = int(seed)
        except (TypeError, ValueError) as exc:
            raise ValueError("PS experiment seed must be an integer or null") from exc
        self._randomness_rng = np.random.Generator(np.random.PCG64(seed_int))
        return self._randomness_rng

    def _bind_randomness_owner(self, pond: Pond) -> None:
        """Bind the current run owner to a provided or newly built Pond."""

        owner = self._randomness_rng
        if owner is None:
            return
        pond.set_randomness_owner(owner)
        orchestrator = getattr(pond, "pvaec_orchestrator", None)
        setter = getattr(orchestrator, "set_randomness_owner", None)
        if callable(setter):
            setter(owner)
        elif orchestrator is not None:
            orchestrator.randomness_rng = owner

    def _apply_disaster_window(self, tick: int, pond: Pond) -> None:
        dw = self.config.disaster_window
        if dw is None:
            return
        phase = dw.phase_at_tick(tick)
        in_war = phase == "war"
        if phase == "recovery" and self._last_disaster_phase == "war":
            self._population_at_war_end = len(pond.organisms)
        self._last_disaster_phase = phase
        cfg = self.config
        if in_war:
            if dw.max_population_cap > 0:
                pond.max_population = min(cfg.max_population, dw.max_population_cap)
            orch = pond.pvaec_orchestrator
            if orch is not None:
                orch.selection_system.set_selection_pressure(
                    cfg.selection_pressure + dw.selection_pressure_boost
                )
            pop = len(pond.organisms)
            if self._war_pop_min is None or pop < self._war_pop_min:
                self._war_pop_min = pop
        else:
            pond.max_population = cfg.max_population
            orch = pond.pvaec_orchestrator
            if orch is not None:
                orch.selection_system.set_selection_pressure(cfg.selection_pressure)

    def request_cancel(self) -> None:
        """请求中断 run() 循环（协作式，下一 tick 边界生效）。"""
        self._cancel_requested = True

    def reset_cancel(self) -> None:
        self._cancel_requested = False

    def current_runtime_run_id(self) -> str | None:
        """Return the active opaque PS run ID, if this Authority has one."""
        return self._snapshot_authority.current_run_id()

    def query_runtime_organism_snapshot(self, identity: object) -> Dict[str, Any]:
        """Query the injected Authority without exposing Pond or Organism objects."""
        return self._snapshot_authority.query(identity)

    def _reset_run_state(self) -> None:
        self.reset_cancel()
        self.snapshots.clear()
        self._population_at_war_end = None
        self._war_pop_min = None
        self._last_disaster_phase = "peace"

    @staticmethod
    def _runtime_position(organism: Any) -> list[float]:
        position = getattr(organism, "position", None)
        if hasattr(position, "x") and hasattr(position, "y"):
            return [float(position.x), float(position.y)]
        try:
            return [float(position[0]), float(position[1])]
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError("PS organism position must contain two numeric values") from exc

    @staticmethod
    def _component_kind(component_type: str) -> str:
        lowered = component_type.lower()
        for kind in ("membrane", "sensor", "actuator"):
            if lowered == kind or kind in lowered:
                return kind
        return lowered

    @staticmethod
    def _component_number(component: object, field: str) -> float | None:
        value = getattr(component, field, None)
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError(f"PS component {field} must be numeric")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"PS component {field} must be numeric") from exc
        if not math.isfinite(number):
            raise ValueError(f"PS component {field} must be finite")
        return number

    @classmethod
    def _component_runtime_facts(cls, organism: Any) -> list[dict[str, Any]]:
        """Read fixed PS component attributes without invoking component methods."""
        components = getattr(organism, "components", None)
        if components is None:
            return []
        if not isinstance(components, dict):
            raise TypeError("PS organism components must be a dictionary")
        field_names = {
            "membrane": ("radius", "ingest_threshold", "efficiency"),
            "sensor": ("signal_threshold", "sensing_range"),
            "actuator": ("energy_cost",),
        }
        facts: list[dict[str, Any]] = []
        for registry_id, component in sorted(
            components.items(), key=lambda item: str(item[0])
        ):
            component_id = str(
                getattr(component, "id", None)
                or getattr(component, "component_id", None)
                or registry_id
            ).strip()
            component_type = str(getattr(component, "component_type", "")).strip()
            location = str(getattr(component, "location", "")).strip()
            if not component_id or not component_type or not location:
                raise ValueError("PS component facts require id, type, and location")
            attach_point = getattr(component, "attach_point", None)
            if attach_point is not None:
                if not isinstance(attach_point, str):
                    raise ValueError("PS component attach_point must be a string or null")
                attach_point = attach_point.strip() or None
            connections = getattr(component, "connections", ())
            if not isinstance(connections, (list, tuple)):
                raise TypeError("PS component connections must be a list or tuple")
            kind = cls._component_kind(component_type)
            fields: dict[str, float] = {}
            for field in field_names.get(kind, ()):
                value = cls._component_number(component, field)
                if value is not None:
                    fields[field] = value
            acquired = getattr(component, "acquired", False)
            congenital = getattr(component, "congenital", False)
            if not isinstance(acquired, bool) or not isinstance(congenital, bool):
                raise ValueError("PS component acquired/congenital must be booleans")
            facts.append(
                {
                    "source": "ps_component_registry",
                    "identity_relation": "ps_component_registry_member",
                    "component_id": component_id,
                    "component_type": component_type,
                    "location": location,
                    "acquired": acquired,
                    "congenital": congenital,
                    "attach_point": attach_point,
                    "connection_count": len(connections),
                    "inspectable_properties": dict(sorted(fields.items())),
                    "component_fields": dict(sorted(fields.items())),
                }
            )
        facts.sort(key=lambda item: item["component_id"])
        return facts

    @classmethod
    def _organism_runtime_snapshot(cls, registry_id: object, organism: Any) -> Dict[str, Any]:
        raw_id = (
            getattr(organism, "organism_id", None)
            or getattr(organism, "id", None)
            or registry_id
        )
        organism_id = str(raw_id).strip()
        if not organism_id:
            raise ValueError("PS organism runtime snapshot requires organism_id")
        entity_type = str(
            getattr(organism, "entity_type", organism.__class__.__name__)
        ).strip()
        if not entity_type:
            entity_type = organism.__class__.__name__
        return {
            "organism_id": organism_id,
            "entity_type": entity_type,
            "position": cls._runtime_position(organism),
            "energy": float(getattr(organism, "energy", 0.0)),
            "max_energy": float(getattr(organism, "max_energy", 0.0)),
            "health": float(getattr(organism, "health", 0.0)),
            "max_health": float(getattr(organism, "max_health", 0.0)),
            "age": int(getattr(organism, "age", 0)),
            "generation": int(getattr(organism, "generation", 0)),
            "developmental_stage": int(getattr(organism, "developmental_stage", 0)),
            "dead": bool(getattr(organism, "dead", False)),
            "component_facts": cls._component_runtime_facts(organism),
        }

    def _publish_runtime_population(self, run_id: str, pond: Pond) -> int:
        snapshots = [
            self._organism_runtime_snapshot(registry_id, organism)
            for registry_id, organism in sorted(
                pond.organisms.items(), key=lambda item: str(item[0])
            )
        ]
        return self._snapshot_authority.publish(run_id, snapshots)

    def build_pond(self, *, attach_initial: bool = True) -> Pond:
        """按配置构造莲池并装配初始种群。"""
        cfg = self.config
        if self._randomness_rng is None:
            self._reset_randomness_owner()
        orch: Any = None
        if cfg.enable_generation_orchestrator and cfg.evolution_generation_interval > 0:
            orch = PVAECOrchestrator(
                maintain_population_size=True,
                randomness_rng=self._randomness_rng,
            )
            orch.mutation_system.set_mutation_rate(cfg.mutation_rate)
            orch.selection_system.set_selection_pressure(cfg.selection_pressure)
            orch.selection_system.set_elitism_rate(cfg.elitism_rate)
            from core.Lotucosm.evolution_profile import (
                apply_profile_to_inheritance_system,
                evolution_profile_from_mapping,
            )

            apply_profile_to_inheritance_system(
                orch.inheritance_system,
                evolution_profile_from_mapping(
                    {
                        "mutation_rate": cfg.mutation_rate,
                        "selection_pressure": cfg.selection_pressure,
                        "elitism_rate": cfg.elitism_rate,
                    }
                ),
            )

        pond = Pond(
            name=cfg.name,
            size=cfg.pond_size,
            max_population=cfg.max_population,
            initial_organisms=0,
            initial_components=cfg.initial_components,
            evolution_generation_interval=cfg.evolution_generation_interval
            if cfg.enable_generation_orchestrator
            else None,
            pvaec_orchestrator=orch,
            randomness_rng=self._randomness_rng,
        )

        if attach_initial:
            self._attach_initial_population(pond)
        return pond

    def _attach_initial_population(self, pond: Pond) -> None:
        cfg = self.config

        for i in range(cfg.initial_organisms):
            pos = tuple(
                (
                    random_uniform_array(self._randomness_rng, 0.0, 1.0, 2)
                    * np.asarray(cfg.pond_size, dtype=float)
                ).tolist()
            )
            org = IntelligentOrganism(
                f"exp_{i + 1}",
                list(pos),
                energy=120.0,
                max_energy=200.0,
                health=90.0,
                max_health=100.0,
            )
            if cfg.equip_sensor_actuator or cfg.enable_pvaec_cycle_per_tick:
                equip_ps_organism(
                    org,
                    enable_pvaec_cycle=cfg.enable_pvaec_cycle_per_tick,
                    with_pvaec_engine=cfg.equip_pvaec_engine,
                )
            ensure_ps_developmental_state(org)
            org.developmental_ladder_enabled = bool(cfg.developmental_ladder_enabled)
            org.developmental_stage = clamp_stage(cfg.developmental_initial_stage)
            org.use_ps_verify_triple = bool(
                cfg.use_verify_triple or cfg.developmental_ladder_enabled
            )
            org.social_learning_enabled = bool(cfg.social_learning_enabled)
            pond.add_organism(org)

    def build_unified_bridge(self) -> tuple[Pond, list[Any]]:
        """WorldBridge 无头试点：SR 实体壳 + unified_pond_step 驱动同一 Pond。"""
        from core.Lotucosm.runtime.world_bridge import (
            BRIDGE_ORGANISM_ATTR,
            apply_bridge_profile_to_organism,
            sr_entity_to_organism,
        )

        cfg = self.config
        pond = self.build_pond(attach_initial=False)
        profile: dict[str, Any] = {}
        if cfg.developmental_ladder_enabled:
            profile["developmental"] = {
                "enabled": True,
                "initial_stage": cfg.developmental_initial_stage,
            }
        if cfg.social_learning_enabled:
            profile["social"] = {"enabled": True}

        entities: list[Any] = []
        for i in range(cfg.initial_organisms):
            pos = tuple(
                (
                    random_uniform_array(self._randomness_rng, 0.0, 1.0, 2)
                    * np.asarray(cfg.pond_size, dtype=float)
                ).tolist()
            )

            class _BridgeEnt:
                def __init__(self, eid: str, xy: tuple[float, float]) -> None:
                    self.id = eid
                    self.entity_type = "organism"
                    self.position = [float(xy[0]), float(xy[1])]
                    self.energy = 120.0
                    self.health = 90.0
                    self.sr_debug_hud: dict[str, Any] = {}

            ent = _BridgeEnt(f"hub_{i + 1}", pos)
            sr_entity_to_organism(
                ent,
                pond,
                profile=profile or None,
                equip_pvaec=bool(cfg.equip_sensor_actuator or cfg.enable_pvaec_cycle_per_tick),
            )
            if profile:
                oid = getattr(ent, BRIDGE_ORGANISM_ATTR, None)
                if oid and str(oid) in pond.organisms:
                    apply_bridge_profile_to_organism(pond.organisms[str(oid)], profile)
                    org = pond.organisms[str(oid)]
                    ensure_ps_developmental_state(org)
                    org.use_ps_verify_triple = bool(
                        cfg.use_verify_triple or cfg.developmental_ladder_enabled
                    )
            entities.append(ent)
        return pond, entities

    def run_unified_bridge(
        self,
        pond: Optional[Pond] = None,
        entities: Optional[list[Any]] = None,
        *,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        snapshot_ticks: Optional[tuple[int, ...]] = None,
    ) -> Dict[str, Any]:
        """Run the unified Pond bridge under one run-scoped snapshot lifetime."""
        from core.Lotucosm.runtime.world_bridge import unified_pond_step

        self._reset_run_state()
        self._reset_randomness_owner()

        if pond is None or entities is None:
            pond, entities = self.build_unified_bridge()
        else:
            self._bind_randomness_owner(pond)
        cfg = self.config
        cancelled = False
        last_completed_tick = 0
        run_id = self._snapshot_authority.begin()
        self._runtime_run_id = run_id
        try:
            self._publish_runtime_population(run_id, pond)
            for tick in range(1, cfg.ticks + 1):
                if self._cancel_requested:
                    cancelled = True
                    break
                self._apply_disaster_window(tick, pond)
                unified_pond_step(pond, entities, delta_time=1.0)
                last_completed_tick = tick
                self._publish_runtime_population(run_id, pond)
                metrics = self._collect_metrics(pond, tick)
                if progress_callback is not None:
                    progress_callback(metrics)
                if self._should_capture_snapshot(tick, snapshot_ticks):
                    self.snapshots.append(metrics)

            return {
                "mode": "unified_bridge",
                "config": cfg.to_dict(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "cancelled": cancelled,
                "final": self._collect_metrics(pond, last_completed_tick),
                "snapshots": self.snapshots,
            }
        finally:
            self._snapshot_authority.end(run_id)
            self._runtime_run_id = None

    def _should_capture_snapshot(
        self,
        tick: int,
        snapshot_ticks: Optional[tuple[int, ...]],
    ) -> bool:
        if snapshot_ticks is not None:
            return tick in snapshot_ticks
        return tick % max(1, self.config.snapshot_interval) == 0 or tick == self.config.ticks

    def _collect_metrics(self, pond: Pond, tick: int) -> Dict[str, Any]:
        orgs = list(pond.organisms.values())
        n = len(orgs)
        if not n:
            return {
                "tick": tick,
                "time": pond.time,
                "iteration": pond.iteration,
                "population": 0,
                "avg_energy": 0.0,
                "avg_health": 0.0,
                "avg_fitness": 0.0,
                "dead_fraction": 0.0,
                "avg_memory_count": 0.0,
                "avg_memory_gene_count": 0.0,
                "avg_social_memory_count": 0.0,
                "avg_developmental_stage": 0.0,
                "pct_at_stage_s4": 0.0,
                "developmental_ladder_enabled": bool(self.config.developmental_ladder_enabled),
                "reproduction_events": int(getattr(pond, "reproduction_events", 0) or 0),
            }

        sel = SelectionSystem(randomness_rng=getattr(pond, "randomness_rng", None))
        energies = [float(getattr(o, "energy", 0.0)) for o in orgs]
        healths = [float(getattr(o, "health", 0.0)) for o in orgs]
        fitness = [sel._calculate_fitness(o) for o in orgs]
        mem_counts = []
        mem_gene_counts = []
        social_counts: list[int] = []
        stages: list[int] = []
        verify_scores: list[float] = []
        for o in orgs:
            ms = getattr(o, "memory_system", None)
            mem_counts.append(len(ms.memories) if ms and hasattr(ms, "memories") else 0)
            genes = getattr(o, "memory_genes", None)
            mem_gene_counts.append(len(genes) if isinstance(genes, list) else 0)
            from core.Lotucosm.social_memory import social_memories

            social_counts.append(len(social_memories(o)))
            if bool(getattr(o, "developmental_ladder_enabled", False)):
                try:
                    stages.append(int(getattr(o, "developmental_stage", 0)))
                except (TypeError, ValueError):
                    stages.append(0)
            last_v = getattr(o, "_ps_last_verify_success", None)
            if last_v is not None:
                try:
                    verify_scores.append(float(last_v))
                except (TypeError, ValueError):
                    pass
        dead = sum(1 for o in orgs if getattr(o, "dead", False))
        stage_n = len(stages)

        metrics = {
            "tick": tick,
            "time": pond.time,
            "iteration": pond.iteration,
            "population": n,
            "avg_energy": sum(energies) / n,
            "avg_health": sum(healths) / n,
            "avg_fitness": sum(fitness) / n,
            "max_fitness": max(fitness),
            "dead_fraction": dead / n,
            "avg_memory_count": sum(mem_counts) / n,
            "avg_memory_gene_count": sum(mem_gene_counts) / n,
            "avg_social_memory_count": sum(social_counts) / n,
            "avg_developmental_stage": sum(stages) / stage_n if stage_n else 0.0,
            "pct_at_stage_s4": (
                sum(1 for s in stages if s >= 4) / stage_n if stage_n else 0.0
            ),
            "developmental_ladder_enabled": bool(self.config.developmental_ladder_enabled),
        }
        metrics["reproduction_events"] = int(getattr(pond, "reproduction_events", 0) or 0)
        dw = self.config.disaster_window
        if dw is not None:
            metrics["war_phase"] = dw.phase_at_tick(tick)
            if self._population_at_war_end is not None:
                metrics["population_at_war_end"] = int(self._population_at_war_end)
            if self._war_pop_min is not None:
                metrics["war_population_min"] = int(self._war_pop_min)
        if verify_scores:
            metrics["avg_verify_success"] = sum(verify_scores) / len(verify_scores)
        cfg = self.config
        if tick == cfg.ticks or tick % max(1, cfg.snapshot_interval) == 0:
            metrics["positions_norm"] = self._positions_norm(pond, cap=120)
        return metrics

    def _positions_norm(self, pond: Pond, cap: int = 120) -> list[list[float]]:
        """将生物体位置归一化到 [0,1]（用于 replay ghost）。"""
        w = max(1.0, float(getattr(pond, "width", 800) or 800))
        h = max(1.0, float(getattr(pond, "height", 600) or 600))
        out: list[list[float]] = []
        for org in list(pond.organisms.values())[:cap]:
            pos = getattr(org, "position", None)
            if pos is None:
                continue
            try:
                if hasattr(pos, "x") and hasattr(pos, "y"):
                    px, py = float(pos.x), float(pos.y)
                else:
                    px, py = float(pos[0]), float(pos[1])
            except (TypeError, ValueError, IndexError):
                continue
            out.append([min(1.0, max(0.0, px / w)), min(1.0, max(0.0, py / h))])
        return out

    def run(
        self,
        pond: Optional[Pond] = None,
        *,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        snapshot_ticks: Optional[tuple[int, ...]] = None,
    ) -> Dict[str, Any]:
        """Run a PS experiment under one run-scoped snapshot lifetime."""
        self._reset_run_state()
        self._reset_randomness_owner()

        pond = pond or self.build_pond()
        self._bind_randomness_owner(pond)
        cfg = self.config
        cancelled = False
        last_completed_tick = 0
        run_id = self._snapshot_authority.begin()
        self._runtime_run_id = run_id
        try:
            self._publish_runtime_population(run_id, pond)
            for tick in range(1, cfg.ticks + 1):
                if self._cancel_requested:
                    cancelled = True
                    break
                self._apply_disaster_window(tick, pond)
                # The optional organism-level PVAEC cycle runs inside Pond.update().
                pond.update()
                last_completed_tick = tick
                self._publish_runtime_population(run_id, pond)
                metrics = self._collect_metrics(pond, tick)
                if progress_callback is not None:
                    progress_callback(metrics)
                if self._should_capture_snapshot(tick, snapshot_ticks):
                    self.snapshots.append(metrics)

            summary = {
                "config": cfg.to_dict(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "cancelled": cancelled,
                "final": self._collect_metrics(pond, last_completed_tick),
                "snapshots": self.snapshots,
            }
            logger.info(
                "Experiment finished %s: pop=%s iteration=%s avg_energy=%.2f cancelled=%s",
                cfg.name,
                summary["final"]["population"],
                summary["final"]["iteration"],
                summary["final"]["avg_energy"],
                cancelled,
            )
            return summary
        finally:
            self._snapshot_authority.end(run_id)
            self._runtime_run_id = None

    def export(self, summary: Dict[str, Any], run_dir: Optional[Path] = None) -> Path:
        """写入 summary.json 与 metrics.csv。"""
        cfg = self.config
        base = Path(cfg.output_dir)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = run_dir or (base / f"{cfg.name}_{stamp}")
        out.mkdir(parents=True, exist_ok=True)

        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        rows = summary.get("snapshots", [])
        if rows:
            with (out / "metrics.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
        return out
