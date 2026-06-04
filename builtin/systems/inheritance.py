"""PS 繁殖继承：子代组件与基因从父代拷贝/变异（PVAECOrchestrator 繁殖阶段）。

排错: 见 `builtin/README.md`。
"""
from typing import List, Dict, Any, Optional
import random
import numpy as np
from builtin.entity_types.organism import Organism
from builtin.components.components_base import ComponentBase
from core.VitaLoom.core.logger import get_logger

logger = get_logger("InheritanceSystem")


class InheritanceSystem:
    """子代 Organism 构造与组件/属性继承；由编排器 `_conception_phase` 调用。

    负责处理生物体繁殖时的基因继承，包括：
    - 先天组件的继承
    - 后天组件的继承
    - 基因变异
    - 记忆基因的继承
    """

    def __init__(self):
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
        self.congenital_component_inheritance_rate = 0.95  # 先天组件继承率
        self.acquired_component_inheritance_rate = 0.3  # 后天组件继承率
        self.memory_gene_inheritance_rate = 0.8  # 记忆基因继承率
        self.mutation_rate = 0.01  # 变异率

    def set_congenital_component_inheritance_rate(self, rate: float) -> None:
        """设置先天组件继承率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.congenital_component_inheritance_rate = max(0.0, min(1.0, rate))

    def set_acquired_component_inheritance_rate(self, rate: float) -> None:
        """设置后天组件继承率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.acquired_component_inheritance_rate = max(0.0, min(1.0, rate))

    def set_memory_gene_inheritance_rate(self, rate: float) -> None:
        """设置记忆基因继承率。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.memory_gene_inheritance_rate = max(0.0, min(1.0, rate))

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

    def inherit(self, parent: Organism, position: tuple) -> Organism:
        """继承父生物体的基因。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 创建子生物体
        child_id = f"{parent.id}_child_{random.randint(1000, 9999)}"
        max_h = float(getattr(parent, "max_health", 100.0) or 100.0)
        max_h = max(1.0, max_h)
        ph = float(getattr(parent, "health", max_h) or max_h)
        child = Organism(
            organism_id=child_id,
            position=position,
            generation=parent.generation + 1,
            max_energy=float(getattr(parent, "max_energy", 200.0) or 200.0),
            max_health=max_h,
            health=max(1.0, min(max_h, ph * 0.9)),
            mutation_rate=float(getattr(parent, "mutation_rate", 0.01) or 0.01),
            inheritance_rate=float(getattr(parent, "inheritance_rate", 0.8) or 0.8),
            energy_consumption_rate=float(getattr(parent, "energy_consumption_rate", 0.05) or 0.05),
        )

        # 继承组件
        self._inherit_components(parent, child)

        # 继承记忆基因
        self._inherit_memory_genes(parent, child)
        self._inherit_runtime_memories(parent, child)
        self._inherit_evolvable_traits(parent, child)

        # 应用变异
        self._apply_mutation(child)

        return child

    def _inherit_components(self, parent: Organism, child: Organism) -> None:
        """继承组件

        参数:
            parent: Organism - 父生物体
            child: Organism - 子生物体
        """
        for component_id, component in parent.components.items():
            # 根据组件类型决定是否继承
            if component.congenital:
                # 先天组件：高概率继承
                if random.random() < self.congenital_component_inheritance_rate:
                    self._add_inherited_component(child, component)
            else:
                # 后天组件：低概率继承
                if random.random() < self.acquired_component_inheritance_rate:
                    self._add_inherited_component(child, component)

    def _add_inherited_component(self, child: Organism, component: ComponentBase) -> None:
        """添加继承的组件

        参数:
            child: Organism - 子生物体
            component: ComponentBase - 要继承的组件
        """
        try:
            # 创建组件的副本（优先保留常用构造参数）
            position = component.position.copy() if hasattr(component.position, "copy") else component.position
            new_component = component.__class__(
                component_id=f"{component.id}_inherited",
                organism_id=child.organism_id,
                position=position,
                size=getattr(component, "size", 10.0),
                component_type=getattr(component, "component_type", "generic"),
            )

            # 继承组件的关键属性
            if hasattr(component, "genetic_strength"):
                new_component.genetic_strength = component.genetic_strength
            if hasattr(component, "mutation_rate"):
                new_component.mutation_rate = component.mutation_rate
            if getattr(component, "is_pvaec_engine", False) and hasattr(component, "associations"):
                try:
                    assoc = getattr(component, "associations", {}) or {}
                    if isinstance(assoc, dict):
                        new_component.associations = {
                            str(sk): {str(ak): float(av) for ak, av in (sv or {}).items()}
                            for sk, sv in assoc.items()
                        }
                    if hasattr(component, "success_threshold"):
                        new_component.success_threshold = float(getattr(component, "success_threshold", 0.5))
                    for attr in ("learning_rate", "exploration_rate"):
                        if hasattr(component, attr) and hasattr(new_component, attr):
                            setattr(new_component, attr, float(getattr(component, attr)))
                except Exception:
                    pass

            # 添加到子生物体
            child.add_component(new_component)
        except Exception as e:
            # 不让单个组件拷贝失败阻断整个继承过程
            logger.warning("继承组件失败 %s: %s", getattr(component, 'id', 'unknown'), e)



    def _inherit_evolvable_traits(self, parent: Organism, child: Organism) -> None:
        src = getattr(parent, "evolvable_traits", None) or {}
        if not isinstance(src, dict) or not src:
            return
        dst: dict[str, object] = {}
        for name, val in src.items():
            if isinstance(val, (int, float)):
                nv = float(val)
                if random.random() < self.mutation_rate:
                    nv += random.gauss(0, abs(nv) * 0.1 + 1e-6)
                dst[str(name)] = nv
            else:
                dst[str(name)] = val
        child.evolvable_traits = dst

    def _inherit_memory_genes(self, parent: Organism, child: Organism) -> None:
        """继承记忆基因

        参数:
            parent: Organism - 父生物体
            child: Organism - 子生物体
        """
        for memory_gene in parent.memory_genes:
            # 与旧版 inherit_memories 一致：遗传概率 = 基础率 × 记忆强度
            strength = float(getattr(memory_gene, "strength", 1.0) or 1.0)
            p = self.memory_gene_inheritance_rate * max(0.0, min(1.0, strength))
            if random.random() >= p:
                continue
            new_memory_gene = memory_gene.copy()
            if random.random() < self.mutation_rate:
                new_memory_gene.mutate()
            child.memory_genes.append(new_memory_gene)

    def _inherit_runtime_memories(self, parent: Organism, child: Organism) -> None:
        """父代 MemorySystem 记忆按强度加权概率拷贝到子代。"""
        parent_ms = getattr(parent, "memory_system", None)
        memories = getattr(parent_ms, "memories", None) if parent_ms is not None else None
        if not memories:
            return
        from core.Lotucosm.memory import MemorySystem

        if child.memory_system is None:
            child.memory_system = MemorySystem()
        for memory in list(memories):
            p = self.memory_gene_inheritance_rate * float(getattr(memory, "strength", 1.0))
            p = max(0.0, min(1.0, p))
            if random.random() >= p:
                continue
            clone = memory.copy()
            clone.strength = max(0.1, float(getattr(clone, "strength", 1.0)) * 0.8)
            child.memory_system.memories.append(clone)

    def _apply_mutation(self, organism: Organism) -> None:
        """应用变异

        参数:
            organism: Organism - 生物体
        """
        # 对每个组件应用变异
        for component in organism.components.values():
            if random.random() < self.mutation_rate:
                mutated_component = component.mutate()
                organism.remove_component(component.id)
                organism.add_component(mutated_component)

    def get_status(self) -> Dict[str, Any]:
        """获取继承系统状态。

        
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
            'congenital_component_inheritance_rate': self.congenital_component_inheritance_rate,
            'acquired_component_inheritance_rate': self.acquired_component_inheritance_rate,
            'memory_gene_inheritance_rate': self.memory_gene_inheritance_rate,
            'mutation_rate': self.mutation_rate
        }
