"""变异机制实现"""

from typing import Dict, List, Any, Optional
import random
import numpy as np
from vitalloom.components.components_base import ComponentBase
from vitalloom.core.memory import MemoryGene


class MutationSystem:
    """变异系统 - 管理生物体的变异机制
    
    负责：
    1. 组件变异
    2. 记忆变异
    3. 特性变异
    """
    
    def __init__(self):
        """初始化变异系统"""
        self.general_mutation_rate = 0.1  # 通用变异率
        self.component_mutation_rate = 0.2  # 组件变异率
        self.memory_mutation_rate = 0.1  # 记忆变异率
        self.trait_mutation_rate = 0.05  # 特性变异率
    
    def mutate_components(self, components: List[ComponentBase], mutation_rate: Optional[float] = None) -> List[ComponentBase]:
        """变异组件
        
        参数:
            components: List[ComponentBase] - 组件列表
            mutation_rate: Optional[float] - 变异率（如果提供，覆盖默认值）
        
        返回:
            List[ComponentBase] - 变异后的组件列表
        """
        mutated_components: List[ComponentBase] = []
        current_mutation_rate = mutation_rate if mutation_rate is not None else self.component_mutation_rate
        
        for component in components:
            if random.random() < current_mutation_rate:
                # 克隆组件并变异
                mutated_component = component.clone()
                mutated_component.mutate()
                mutated_components.append(mutated_component)
            else:
                mutated_components.append(component)
        
        return mutated_components
    
    def mutate_memories(self, memories: List[MemoryGene], mutation_rate: Optional[float] = None) -> List[MemoryGene]:
        """变异记忆
        
        参数:
            memories: List[MemoryGene] - 记忆列表
            mutation_rate: Optional[float] - 变异率（如果提供，覆盖默认值）
        
        返回:
            List[MemoryGene] - 变异后的记忆列表
        """
        mutated_memories: List[MemoryGene] = []
        current_mutation_rate = mutation_rate if mutation_rate is not None else self.memory_mutation_rate
        
        for memory in memories:
            mutated_memory = MemoryGene(
                situation=memory.situation,
                action_pattern=memory.action_pattern.copy(),
                success_rate=memory.success_rate
            )
            
            if random.random() < current_mutation_rate:
                mutated_memory.mutate()
            
            mutated_memories.append(mutated_memory)
        
        return mutated_memories
    
    def mutate_traits(self, traits: Dict[str, Any], mutation_rate: Optional[float] = None) -> Dict[str, Any]:
        """变异特性
        
        参数:
            traits: Dict[str, Any] - 特性字典
            mutation_rate: Optional[float] - 变异率（如果提供，覆盖默认值）
        
        返回:
            Dict[str, Any] - 变异后的特性字典
        """
        mutated_traits: Dict[str, Any] = traits.copy()
        current_mutation_rate = mutation_rate if mutation_rate is not None else self.trait_mutation_rate
        
        for trait_name, trait_value in traits.items():
            if isinstance(trait_value, (int, float)):
                # 数值型特性变异
                if random.random() < current_mutation_rate:
                    # 高斯分布变异，变异幅度与当前值成正比
                    mutation_std = trait_value * 0.1 if trait_value != 0 else 0.1
                    mutated_value = trait_value + np.random.normal(0, mutation_std)
                    mutated_traits[trait_name] = mutated_value
            elif isinstance(trait_value, bool):
                # 布尔型特性变异
                if random.random() < current_mutation_rate:
                    mutated_traits[trait_name] = not trait_value
            elif isinstance(trait_value, str):
                # 字符串型特性变异（简单的随机替换）
                if random.random() < current_mutation_rate:
                    # 随机替换一个字符
                    if len(trait_value) > 0:
                        index = random.randint(0, len(trait_value) - 1)
                        new_char = chr(random.randint(97, 122))  # 随机小写字母
                        mutated_traits[trait_name] = trait_value[:index] + new_char + trait_value[index+1:]
        
        return mutated_traits
    
    def create_new_trait(self, base_traits: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建新特性
        
        参数:
            base_traits: Dict[str, Any] - 基础特性字典
        
        返回:
            Optional[Dict[str, Any]] - 新特性字典，如果创建成功；否则返回None
        """
        # 10%的概率创建新特性
        if random.random() < 0.1:
            # 随机选择特性类型
            trait_type = random.choice(["numeric", "boolean", "string"])
            
            new_trait = {}
            new_trait_name = f"trait_{random.randint(1000, 9999)}"
            
            if trait_type == "numeric":
                new_trait[new_trait_name] = random.uniform(-10, 10)
            elif trait_type == "boolean":
                new_trait[new_trait_name] = random.choice([True, False])
            elif trait_type == "string":
                new_trait[new_trait_name] = f"new_trait_{random.randint(1, 100)}"
            
            return new_trait  # type: ignore
        
        return None
    
    def set_mutation_rate(self, rate: float) -> None:
        """设置通用变异率
        
        参数:
            rate: float - 通用变异率（0-1之间）
        """
        self.general_mutation_rate = max(0.0, min(1.0, rate))
    
    def set_component_mutation_rate(self, rate: float) -> None:
        """设置组件变异率
        
        参数:
            rate: float - 组件变异率（0-1之间）
        """
        self.component_mutation_rate = max(0.0, min(1.0, rate))
    
    def set_memory_mutation_rate(self, rate: float) -> None:
        """设置记忆变异率
        
        参数:
            rate: float - 记忆变异率（0-1之间）
        """
        self.memory_mutation_rate = max(0.0, min(1.0, rate))
    
    def set_trait_mutation_rate(self, rate: float) -> None:
        """设置特性变异率
        
        参数:
            rate: float - 特性变异率（0-1之间）
        """
        self.trait_mutation_rate = max(0.0, min(1.0, rate))