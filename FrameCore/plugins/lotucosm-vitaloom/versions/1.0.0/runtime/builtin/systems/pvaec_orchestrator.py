"""PS PVAEC 世代编排：感知→变异→动作→评估→繁殖，替换整代种群。

架构数据流::

    EvolutionRunner → run_cycle → InheritanceSystem / SelectionSystem / MutationSystem

SR 边界: SR 世代与脚本在 GameViewport + PvaecScript；本模块仅服务 PS `Organism` 列表。

排错: 见 `builtin/README.md`（世代不触发、人口规模）。
"""
from __future__ import annotations

from typing import Any, Dict, List
import random
import numpy as np

from builtin.systems.inheritance import InheritanceSystem
from builtin.systems.mutation import MutationSystem
from builtin.systems.selection import SelectionSystem
from builtin.entity_types.organism import Organism
from core.Lotucosm.randomness import random_uniform_array


class PVAECOrchestrator:
    """PS 单世代流水线编排；`maintain_population_size` 控制是否保持上一代规模。"""

    def __init__(self, *, maintain_population_size: bool = True, randomness_rng: Any = None):
        """PVAECOrchestrator.__init__。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """
        detached_owner = randomness_rng is None
        if detached_owner:
            randomness_rng = random.Random(12345)
        self.inheritance_system = InheritanceSystem(randomness_rng=randomness_rng)
        self.mutation_system = MutationSystem(randomness_rng=randomness_rng)
        self.selection_system = SelectionSystem(randomness_rng=randomness_rng)
        self.cycle_count = 0
        self.organism_count = 0
        self.last_reproduction_count = 0
        self.maintain_population_size = maintain_population_size
        if randomness_rng is None:
            raise ValueError("PVAEC randomness owner cannot be cleared")
        if not callable(getattr(randomness_rng, "random", None)):
            raise TypeError("PVAEC randomness owner must expose random()")
        self.randomness_rng = randomness_rng
        self.randomness_owner_mode = "detached" if detached_owner else "runtime"
        if detached_owner:
            self.inheritance_system.randomness_owner_mode = "detached"
            self.mutation_system.randomness_owner_mode = "detached"
            self.selection_system.randomness_owner_mode = "detached"

    def set_randomness_owner(self, randomness_rng: Any = None) -> None:
        """Attach one explicit PS owner to every stochastic PVAEC phase.

        ``random.Random`` and NumPy ``Generator`` are both accepted through the
        core compatibility seam.  Passing ``None`` restores the legacy global
        fallback for callers that have not opted into an owner.
        """

        if randomness_rng is None:
            raise ValueError("PVAEC randomness owner cannot be cleared")
        if not callable(getattr(randomness_rng, "random", None)):
            raise TypeError("PVAEC randomness owner must expose random()")
        self.randomness_rng = randomness_rng
        self.randomness_owner_mode = "runtime"
        self.inheritance_system.randomness_rng = randomness_rng
        self.inheritance_system.randomness_owner_mode = "runtime"
        self.mutation_system.randomness_rng = randomness_rng
        self.mutation_system.randomness_owner_mode = "runtime"
        self.selection_system.randomness_rng = randomness_rng
        self.selection_system.randomness_owner_mode = "runtime"

    def configure_from_evolution_defaults(self, defaults: Dict[str, Any]) -> None:
        """将 project evolution_defaults 同步到 InheritanceSystem（Phase C）。"""
        from core.VitaLoom.project.evolution_context import configure_inheritance_from_defaults

        configure_inheritance_from_defaults(self.inheritance_system, defaults)

    @staticmethod
    def _env_size(environment: Any) -> tuple[float, float]:
        size = getattr(environment, "size", (1200.0, 800.0))
        try:
            w, h = float(size[0]), float(size[1])
        except (TypeError, IndexError, ValueError):
            return 1200.0, 800.0
        return max(w, 2.0), max(h, 2.0)

    def _child_position(self, parent: Organism, environment: Any) -> tuple[float, float]:
        w, h = self._env_size(environment)
        pos = np.asarray(parent.position, dtype=float).reshape(-1)[:2]
        rng = getattr(environment, "randomness_rng", None)
        if rng is None:
            rng = self.randomness_rng
        if rng is None:
            rng = getattr(getattr(environment, "pvaec_orchestrator", None), "randomness_rng", None)
        jitter = random_uniform_array(rng, -10.0, 10.0, 2)
        xy = pos + jitter
        x = float(np.clip(xy[0], 1.0, w - 1.0))
        y = float(np.clip(xy[1], 1.0, h - 1.0))
        return (x, y)

    def run_cycle(self, organisms: List[Organism], environment: Any) -> List[Organism]:
        """执行完整世代并返回新种群列表。

        职责: 五阶段流水线——全体 `sense`、变异、`organism.update`、适应度、精英+繁殖补足。
        时机: `EvolutionRunner.apply_generation` 在莲池 `iteration` 边界调用。
        不变量: 空输入返回 `[]`；输出规模受 `environment.max_population` 与 `maintain_population_size` 约束。
        排错: 人口骤减 → 查 `elitism_rate` 与 `selection_system`；无感知 → 组件无 `sense` 方法。
        """
        environment_rng = getattr(environment, "randomness_rng", None)
        if environment_rng is not None:
            self.set_randomness_owner(environment_rng)
        self.cycle_count += 1
        if not organisms:
            self.organism_count = 0
            self.last_reproduction_count = 0
            return []

        self._perception_phase(organisms, environment)
        self._variation_phase(organisms)
        self._action_phase(organisms, environment)
        fitness_scores = self._evaluation_phase(organisms)
        new_organisms = self._conception_phase(organisms, fitness_scores, environment)
        self.organism_count = len(new_organisms)
        return new_organisms

    def _perception_phase(self, organisms: List[Organism], environment: Any) -> None:
        for organism in organisms:
            for component in organism.components.values():
                if hasattr(component, "sense"):
                    component.sense(environment)

    def _variation_phase(self, organisms: List[Organism]) -> None:
        for organism in organisms:
            self.mutation_system.mutate(organism)

    def _action_phase(self, organisms: List[Organism], environment: Any) -> None:
        for organism in organisms:
            organism.update(1.0, environment)

    def _evaluation_phase(self, organisms: List[Organism]) -> List[float]:
        return [self.selection_system._calculate_fitness(org) for org in organisms]

    def _conception_phase(
        self,
        organisms: List[Organism],
        fitness_scores: List[float],
        environment: Any,
    ) -> List[Organism]:
        n = len(organisms)
        max_pop = int(getattr(environment, "max_population", n) or n)
        max_pop = max(1, max_pop)

        if self.maintain_population_size:
            target = min(max_pop, n)
        else:
            target = max(1, min(max_pop, max(1, n // 2)))
        target = max(1, target)

        pairs = sorted(zip(organisms, fitness_scores), key=lambda x: x[1], reverse=True)
        elite_n = int(round(n * float(self.selection_system.elitism_rate)))
        elite_n = min(max(0, elite_n), target)
        elites: List[Organism] = [org for org, _ in pairs[:elite_n]]

        selected_count = max(1, n // 2)
        selected = self.selection_system.select(organisms, selected_count)
        if not selected:
            selected = [pairs[0][0]]

        out: List[Organism] = list(elites)
        need = target - len(out)
        idx = 0
        repro = 0
        while need > 0:
            parent = selected[idx % len(selected)]
            idx += 1
            pos = self._child_position(parent, environment)
            child = self.inheritance_system.inherit(parent, pos)
            out.append(child)
            repro += 1
            need -= 1
            if len(out) >= max_pop:
                break

        self.last_reproduction_count = repro
        return out[:max_pop]

    def get_status(self) -> Dict[str, Any]:
        """PVAECOrchestrator.get_status。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return {
            "cycle_count": self.cycle_count,
            "organism_count": self.organism_count,
            "maintain_population_size": self.maintain_population_size,
            "inheritance_system": self.inheritance_system.get_status(),
            "mutation_system": self.mutation_system.get_status(),
            "selection_system": self.selection_system.get_status(),
        }
