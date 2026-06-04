# -*- coding: utf-8 -*-
"""PS 莲池实验配置：JSON 驱动的 tick / 世代 / PVAEC 循环参数。

职责: 解析实验预设并供 PsExperimentRunner 构建 Pond 与种群。
时机: `tools/run_ps_experiment.py` 或脚本导入。
不变量: evolution_generation_interval<=0 表示关闭世代编排。
排错: 见 docs/experiment_guide.md。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PsExperimentConfig:
    """莲池（PS）无头实验配置。"""

    name: str = "pvaec_homeostasis"
    ticks: int = 500
    seed: Optional[int] = None
    pond_size: tuple[float, float] = (640.0, 480.0)
    max_population: int = 40
    initial_organisms: int = 8
    initial_components: int = 0
    evolution_generation_interval: int = 50
    enable_generation_orchestrator: bool = True
    enable_pvaec_cycle_per_tick: bool = True
    equip_sensor_actuator: bool = True
    equip_pvaec_engine: bool = False
    snapshot_interval: int = 10
    output_dir: str = "data/experiment_runs"
    selection_pressure: float = 0.5
    elitism_rate: float = 0.1
    mutation_rate: float = 0.05
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PsExperimentConfig":
        size = data.get("pond_size", [640, 480])
        if isinstance(size, (list, tuple)) and len(size) >= 2:
            pond_size = (float(size[0]), float(size[1]))
        else:
            pond_size = (640.0, 480.0)
        return cls(
            name=str(data.get("name", "experiment")),
            ticks=max(1, int(data.get("ticks", 500))),
            seed=data.get("seed"),
            pond_size=pond_size,
            max_population=max(1, int(data.get("max_population", 40))),
            initial_organisms=max(0, int(data.get("initial_organisms", 8))),
            initial_components=max(0, int(data.get("initial_components", 0))),
            evolution_generation_interval=int(data.get("evolution_generation_interval", 50)),
            enable_generation_orchestrator=bool(data.get("enable_generation_orchestrator", True)),
            enable_pvaec_cycle_per_tick=bool(data.get("enable_pvaec_cycle_per_tick", True)),
            equip_sensor_actuator=bool(data.get("equip_sensor_actuator", True)),
            equip_pvaec_engine=bool(data.get("equip_pvaec_engine", False)),
            snapshot_interval=max(1, int(data.get("snapshot_interval", 10))),
            output_dir=str(data.get("output_dir", "data/experiment_runs")),
            selection_pressure=float(data.get("selection_pressure", 0.5)),
            elitism_rate=float(data.get("elitism_rate", 0.1)),
            mutation_rate=float(data.get("mutation_rate", 0.05)),
            notes=str(data.get("notes", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ticks": self.ticks,
            "seed": self.seed,
            "pond_size": list(self.pond_size),
            "max_population": self.max_population,
            "initial_organisms": self.initial_organisms,
            "initial_components": self.initial_components,
            "evolution_generation_interval": self.evolution_generation_interval,
            "enable_generation_orchestrator": self.enable_generation_orchestrator,
            "enable_pvaec_cycle_per_tick": self.enable_pvaec_cycle_per_tick,
            "equip_sensor_actuator": self.equip_sensor_actuator,
            "equip_pvaec_engine": self.equip_pvaec_engine,
            "snapshot_interval": self.snapshot_interval,
            "output_dir": self.output_dir,
            "selection_pressure": self.selection_pressure,
            "elitism_rate": self.elitism_rate,
            "mutation_rate": self.mutation_rate,
            "notes": self.notes,
        }


def load_experiment_config(path: str | Path) -> PsExperimentConfig:
    """从 JSON 文件加载实验配置。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("实验配置须为 JSON 对象")
    return PsExperimentConfig.from_dict(data)
