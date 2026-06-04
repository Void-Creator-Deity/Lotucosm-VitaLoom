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
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.systems.organism_builder import equip_ps_organism
from builtin.systems.pvaec_orchestrator import PVAECOrchestrator
from builtin.systems.selection import SelectionSystem
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.pond import Pond
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PsExperimentRunner")


class PsExperimentRunner:
    """无头莲池实验：可复现、可导出、可对比参数。"""

    def __init__(self, config: PsExperimentConfig):
        self.config = config
        self.snapshots: List[Dict[str, Any]] = []

    def build_pond(self) -> Pond:
        """按配置构造莲池并装配初始种群。"""
        cfg = self.config
        orch: Any = None
        if cfg.enable_generation_orchestrator and cfg.evolution_generation_interval > 0:
            orch = PVAECOrchestrator(maintain_population_size=True)
            orch.mutation_system.set_mutation_rate(cfg.mutation_rate)
            orch.selection_system.set_selection_pressure(cfg.selection_pressure)
            orch.selection_system.set_elitism_rate(cfg.elitism_rate)

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
        )

        import numpy as np

        for i in range(cfg.initial_organisms):
            pos = tuple((np.random.rand(2) * np.array(cfg.pond_size)).tolist())
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
            pond.add_organism(org)
        return pond

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
            }

        sel = SelectionSystem()
        energies = [float(getattr(o, "energy", 0.0)) for o in orgs]
        healths = [float(getattr(o, "health", 0.0)) for o in orgs]
        fitness = [sel._calculate_fitness(o) for o in orgs]
        mem_counts = []
        for o in orgs:
            ms = getattr(o, "memory_system", None)
            mem_counts.append(len(ms.memories) if ms and hasattr(ms, "memories") else 0)
        dead = sum(1 for o in orgs if getattr(o, "dead", False))

        return {
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
        }

    def run(self, pond: Optional[Pond] = None) -> Dict[str, Any]:
        """执行实验并返回摘要 dict。"""
        if self.config.seed is not None:
            random.seed(self.config.seed)
            try:
                import numpy as np

                np.random.seed(int(self.config.seed))
            except Exception:
                pass

        pond = pond or self.build_pond()
        cfg = self.config
        self.snapshots.clear()

        for tick in range(1, cfg.ticks + 1):
            # PVAEC 六步循环在 Organism.update(environment=pond) 内执行（enable_pvaec_cycle_per_tick）
            pond.update()
            if tick % cfg.snapshot_interval == 0 or tick == cfg.ticks:
                self.snapshots.append(self._collect_metrics(pond, tick))

        summary = {
            "config": cfg.to_dict(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "final": self._collect_metrics(pond, cfg.ticks),
            "snapshots": self.snapshots,
        }
        logger.info(
            "实验完成 %s: pop=%s iteration=%s avg_energy=%.2f",
            cfg.name,
            summary["final"]["population"],
            summary["final"]["iteration"],
            summary["final"]["avg_energy"],
        )
        return summary

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
