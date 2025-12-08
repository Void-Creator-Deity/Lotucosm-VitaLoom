"""繁殖与分裂系统实现"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
from .organism import Organism
from vitalloom.components.components_base import ComponentBase

class ReproductionSystem:
    """繁殖与分裂系统 - 负责生物体的繁殖和分裂机制

    繁殖与分裂系统实现了生物体的繁殖逻辑，包括：
    1. 繁殖条件检查
    2. 子代生成
    3. 组件遗传
    4. 记忆遗传
    5. 变异处理
    """

    def __init__(self, **kwargs: Any):
        """初始化繁殖与分裂系统

        参数:
            kwargs: 其他参数
        """
        self.congenital_inheritance_rate = float(kwargs.get('congenital_inheritance_rate', 1.0))  # 先天组件遗传率
        self.acquired_inheritance_rate = float(kwargs.get('acquired_inheritance_rate', 0.3))  # 后天组件遗传率
        self.memory_inheritance_rate = float(kwargs.get('memory_inheritance_rate', 0.8))  # 记忆遗传率
        self.mutation_rate = float(kwargs.get('mutation_rate', 0.1))  # 变异率

    def check_reproduction_condition(self, organism: Organism) -> bool:
        """检查生物体是否满足繁殖条件

        参数:
            organism: Organism - 生物体实例

        返回:
            bool - 是否满足繁殖条件
        """
        # 基础繁殖条件：能量充足，健康良好
        if organism.energy < organism.max_energy * 0.6 or organism.health < organism.max_health * 0.8:
            return False

        # 年龄条件：达到成熟年龄
        if organism.age < 100:  # 简单的成熟年龄限制
            return False

        return True

    def reproduce(self, parent: Organism) -> Optional[Organism]:
        """繁殖，创建子代生物体

        参数:
            parent: Organism - 父代生物体

        返回:
            Optional[Organism] - 子代生物体，繁殖失败返回None
        """
        if not self.check_reproduction_condition(parent):
            return None

        # 消耗父代能量
        parent.energy -= parent.max_energy * 0.3

        # 创建子代
        offspring_id = f"{parent.id}_offspring_{parent.age}"
        # 子代初始位置在父代附近随机位置
        offspring_position = tuple((parent.position + np.random.randn(2) * 20).tolist())

        # 创建与父代相同类型的子代
        offspring = parent.__class__(offspring_id, offspring_position)

        # 遗传组件
        self.inherit_components(parent, offspring)

        # 遗传记忆
        self.inherit_memory(parent, offspring)

        # 应用变异
        self.apply_mutation(offspring)

        return offspring

    def inherit_components(self, parent: Organism, offspring: Organism):
        """
        遗传组件给子代

        参数:
            parent: Organism - 父代生物体
            offspring: Organism - 子代生物体
        """
        for _, comp in parent.components.items():
            # 检查是否应该遗传该组件
            if self.should_inherit_component(comp):
                # 复制组件
                component_copy = self.copy_component(comp, offspring.id)
                if component_copy:
                    # 添加到子代
                    offspring.add_component(component_copy)

    def should_inherit_component(self, component: ComponentBase) -> bool:
        """检查组件是否应该被遗传

        参数:
            component: ComponentBase - 组件实例

        返回:
            bool - 是否应该遗传
        """
        if component.congenital:
            # 先天组件高概率遗传
            return np.random.random() < self.congenital_inheritance_rate
        else:
            # 后天组件低概率遗传
            return np.random.random() < self.acquired_inheritance_rate

    def copy_component(self, component: ComponentBase, organism_id: str) -> Optional[ComponentBase]:
        """复制组件

        参数:
            component: ComponentBase - 要复制的组件
            organism_id: str - 子代生物体ID

        返回:
            Optional[ComponentBase] - 复制的组件实例
        """
        # 简单的组件复制实现
        # 实际项目中需要根据组件类型实现深拷贝
        import copy
        try:
            # 创建组件副本
            component_copy = copy.deepcopy(component)

            # 更新组件的生物体ID
            component_copy.organism_id = organism_id

            # 重置组件状态
            component_copy.activation = 0.0
            component_copy.state = "idle"
            component_copy.input_signals.clear()
            component_copy.output_signal = 0.0

            return component_copy
        except Exception as e:
            print(f"复制组件失败 {component.id}: {e}")
            return None

    def inherit_memory(self, parent: Organism, offspring: Organism):
        """遗传记忆给子代

        参数:
            parent: Organism - 父代生物体
            offspring: Organism - 子代生物体
        """
        if parent.memory_system and offspring.memory_system:
            # 父代记忆
            parent_memories = getattr(parent.memory_system, 'memories', [])

            # 记忆遗传
            for memory in parent_memories:
                if np.random.random() < self.memory_inheritance_rate:
                    # 复制记忆
                    memory_copy = self.copy_memory(memory)
                    if memory_copy:
                        # 添加到子代记忆系统
                        offspring.memory_system.store(memory_copy)

    def copy_memory(self, memory: Any) -> Optional[Dict[str, Any]]:
        """复制记忆

        参数:
            memory: Any - 记忆条目

        返回:
            Optional[Dict[str, Any]] - 复制的记忆条目
        """
        try:
            import copy
            memory_copy = copy.deepcopy(memory)

            # 调整记忆强度
            if hasattr(memory_copy, 'strength'):
                memory_copy.strength *= 0.8  # 记忆强度衰减

            return memory_copy
        except Exception as e:
            print(f"复制记忆失败: {e}")
            return None

    def apply_mutation(self, organism: Organism):
        """应用变异到子代生物体

        参数:
            organism: Organism - 子代生物体
        """
        # 生物体属性变异
        self.mutate_organism_attributes(organism)

        # 组件变异
        for component in organism.components.values():
            component.mutate()

    def mutate_organism_attributes(self, organism: Organism):
        """变异生物体属性

        参数:
            organism: Organism - 生物体实例
        """
        import random

        # 能量相关属性变异
        organism.energy_consumption_rate += random.gauss(0, 0.002)  # 能量消耗率变异
        organism.energy_consumption_rate = max(0.001, organism.energy_consumption_rate)  # 限制最小值

        # 遗传属性变异
        organism.mutation_rate += random.gauss(0, 0.02)  # 变异率变异
        organism.mutation_rate = max(0.01, min(0.5, organism.mutation_rate))  # 限制范围

        organism.inheritance_rate += random.gauss(0, 0.02)  # 遗传率变异
        organism.inheritance_rate = max(0.5, min(0.99, organism.inheritance_rate))  # 限制范围

        # 其他属性变异
        if hasattr(organism, 'learning_efficiency'):
            organism.learning_efficiency += random.gauss(0, 0.1)  # 学习效率变异
            organism.learning_efficiency = max(0.5, min(2.0, organism.learning_efficiency))  # 限制范围

        if hasattr(organism, 'exploration_bias'):
            organism.exploration_bias += random.gauss(0, 0.05)  # 探索偏差变异
            organism.exploration_bias = max(0.1, min(0.7, organism.exploration_bias))  # 限制范围

    def binary_fission(self, organism: Organism) -> Optional[Tuple[Organism, Organism]]:
        """二分裂 - 生物体分裂为两个相同的子代

        参数:
            organism: Organism - 生物体实例

        返回:
            Optional[Tuple[Organism, Organism]] - 两个子代生物体，分裂失败返回None
        """
        # 检查分裂条件
        if organism.energy < organism.max_energy * 0.8:
            return None  # 能量不足，无法分裂

        # 消耗能量
        organism.energy -= organism.max_energy * 0.4

        # 创建两个子代
        offspring1_id = f"{organism.id}_fission_1"
        offspring2_id = f"{organism.id}_fission_2"

        # 分裂位置
        offset1 = np.array([-10, 0])
        offset2 = np.array([10, 0])

        # 将numpy数组转换为元组，匹配构造函数的类型要求
        offspring1_position = tuple((organism.position + offset1).tolist())
        offspring2_position = tuple((organism.position + offset2).tolist())

        offspring1 = organism.__class__(offspring1_id, offspring1_position)
        offspring2 = organism.__class__(offspring2_id, offspring2_position)

        # 分配组件
        components = list(organism.components.values())
        mid_point = len(components) // 2

        # 分配组件给子代1
        for component in components[:mid_point]:
            component_copy = self.copy_component(component, offspring1.id)
            if component_copy:
                offspring1.add_component(component_copy)

        # 分配组件给子代2
        for component in components[mid_point:]:
            component_copy = self.copy_component(component, offspring2.id)
            if component_copy:
                offspring2.add_component(component_copy)

        # 遗传记忆
        self.inherit_memory(organism, offspring1)
        self.inherit_memory(organism, offspring2)

        # 应用变异
        self.apply_mutation(offspring1)
        self.apply_mutation(offspring2)

        return offspring1, offspring2

    def get_reproduction_statistics(self) -> Dict[str, Any]:
        """获取繁殖统计信息

        返回:
            Dict[str, Any] - 统计信息
        """
        return {
            'congenital_inheritance_rate': self.congenital_inheritance_rate,
            'acquired_inheritance_rate': self.acquired_inheritance_rate,
            'memory_inheritance_rate': self.memory_inheritance_rate,
            'mutation_rate': self.mutation_rate
        }
