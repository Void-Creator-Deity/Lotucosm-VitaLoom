"""PS 世代内组件/属性随机变异（PVAECOrchestrator._variation_phase）。

排错: 见 `builtin/README.md`。
"""
from typing import Dict, Any, Optional
import random
import numpy as np
from builtin.entity_types.organism import Organism
from builtin.components.components_base import ComponentBase
from core.Lotucosm.randomness import random_normal, random_uniform, random_unit


class MutationSystem:
    """变异系统 - 处理生物体的变异

    负责处理生物体的随机变异，包括：
    - 组件变异
    - 基因强度变异
    - 变异率控制
    """

    def __init__(self, *, randomness_rng=None):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self.randomness_owner_mode = "runtime" if randomness_rng is not None else "detached"
        self.randomness_rng = randomness_rng if randomness_rng is not None else random.Random(12345)
        self.mutation_rate = 0.01  # 基础变异率
        self.mutation_strength = 0.1  # 变异强度

    def set_mutation_rate(self, rate: float) -> None:
        """设置变异率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.mutation_rate = max(0.0, min(1.0, rate))

    def set_mutation_strength(self, strength: float) -> None:
        """设置变异强度。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.mutation_strength = max(0.0, min(1.0, strength))

    def mutate(self, organism: Organism) -> Organism:
        """对生物体应用变异。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 对每个组件应用变异
        for component in list(organism.components.values()):
            if random_unit(self.randomness_rng) < self.mutation_rate:
                self._mutate_component(component)

        # 旧版生物体属性微变异（能耗、变异率、遗传率）
        if random_unit(self.randomness_rng) < self.mutation_rate:
            organism.energy_consumption_rate = max(
                0.001,
                float(organism.energy_consumption_rate)
                + random_normal(self.randomness_rng, 0, 0.002),
            )
        if random_unit(self.randomness_rng) < self.mutation_rate:
            organism.mutation_rate = max(
                0.001,
                min(1.0, float(organism.mutation_rate)
                    + random_normal(self.randomness_rng, 0, 0.003)),
            )
        if random_unit(self.randomness_rng) < self.mutation_rate:
            organism.inheritance_rate = max(
                0.5,
                min(0.99, float(organism.inheritance_rate)
                    + random_normal(self.randomness_rng, 0, 0.01)),
            )

        # 旧版 mutate_memories：按 mutation_rate 对 memory_genes 尝试 mutate()
        for memory_gene in list(getattr(organism, "memory_genes", []) or []):
            if random_unit(self.randomness_rng) < self.mutation_rate:
                memory_gene.mutate(randomness_rng=self.randomness_rng)

        return organism

    def _mutate_component(self, component: ComponentBase) -> None:
        """变异组件

        参数:
            component: ComponentBase - 组件
        """
        # 变异遗传强度
        strength_change = random_uniform(
            self.randomness_rng,
            -self.mutation_strength,
            self.mutation_strength,
        )
        component.genetic_strength = max(0.0, min(1.0, component.genetic_strength + strength_change))

        # 变异变异率
        rate_change = random_uniform(
            self.randomness_rng,
            -self.mutation_strength * 0.5,
            self.mutation_strength * 0.5,
        )
        component.mutation_rate = max(0.0, min(1.0, component.mutation_rate + rate_change))

    def get_status(self) -> Dict[str, Any]:
        """获取变异系统状态。

        
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
            'mutation_rate': self.mutation_rate,
            'mutation_strength': self.mutation_strength
        }
