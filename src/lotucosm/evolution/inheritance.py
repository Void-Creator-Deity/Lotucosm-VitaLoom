"""遗传机制实现"""

from typing import Dict, List, Any
import random
from vitalloom.core.memory import MemoryGene
from vitalloom.components.components_base import ComponentBase


class InheritanceSystem:
    """遗传系统 - 管理生物体的遗传机制
    
    负责：
    1. 记忆遗传
    2. 组件遗传
    3. 特性遗传
    """
    
    def __init__(self):
        """初始化遗传系统"""
        self.memory_inheritance_rate = 0.8  # 记忆遗传率
        self.component_inheritance_rate = 1.0  # 组件遗传率（先天组件100%遗传）
        self.acquired_component_inheritance_rate = 0.3  # 后天获得组件的遗传率
    
    def inherit_memories(self, parent_memories: List[MemoryGene], mutation_rate: float = 0.1) -> List[MemoryGene]:
        """继承记忆
        
        参数:
            parent_memories: List[MemoryGene] - 父代记忆列表
            mutation_rate: float - 变异率
        
        返回:
            List[MemoryGene] - 子代记忆列表
        """
        inherited_memories: List[MemoryGene] = []
        
        for memory in parent_memories:
            # 记忆按强度遗传，强度越高，遗传概率越大
            if random.random() < self.memory_inheritance_rate * memory.strength:
                # 复制记忆
                inherited_memory = MemoryGene(
                    situation=memory.situation,
                    action_pattern=memory.action_pattern.copy(),
                    success_rate=memory.success_rate
                )
                
                # 记忆变异
                if random.random() < mutation_rate:
                    inherited_memory.mutate()
                
                inherited_memories.append(inherited_memory)
        
        return inherited_memories
    
    def inherit_components(self, parent_components: Dict[str, ComponentBase], mutation_rate: float = 0.1) -> List[ComponentBase]:
        """继承组件
        
        参数:
            parent_components: Dict[str, ComponentBase] - 父代组件字典
            mutation_rate: float - 变异率
        
        返回:
            List[ComponentBase] - 子代组件列表
        """
        inherited_components: List[ComponentBase] = []
        
        for component in parent_components.values():
            # 先天组件100%遗传
            if component.congenital:
                if random.random() < self.component_inheritance_rate:
                    inherited_component = component.clone()
                    inherited_components.append(inherited_component)
            # 后天获得的组件按概率遗传
            else:
                if random.random() < self.acquired_component_inheritance_rate:
                    inherited_component = component.clone()
                    inherited_components.append(inherited_component)
        
        return inherited_components
    
    def inherit_traits(self, parent_traits: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        """继承特性
        
        参数:
            parent_traits: Dict[str, Any] - 父代特性字典
            mutation_rate: float - 变异率
        
        返回:
            Dict[str, Any] - 子代特性字典
        """
        inherited_traits: Dict[str, Any] = {}
        
        for trait_name, trait_value in parent_traits.items():
            if isinstance(trait_value, (int, float)):
                # 数值型特性，加入变异
                inherited_value = trait_value
                if random.random() < mutation_rate:
                    # 高斯分布变异
                    inherited_value += random.gauss(0, trait_value * 0.1)
                inherited_traits[trait_name] = inherited_value
            else:
                # 其他类型特性直接遗传
                inherited_traits[trait_name] = trait_value
        
        return inherited_traits
    
    def set_memory_inheritance_rate(self, rate: float):
        """设置记忆遗传率
        
        参数:
            rate: float - 记忆遗传率（0-1之间）
        """
        self.memory_inheritance_rate = max(0.0, min(1.0, rate))
    
    def set_component_inheritance_rate(self, rate: float):
        """设置组件遗传率
        
        参数:
            rate: float - 组件遗传率（0-1之间）
        """
        self.component_inheritance_rate = max(0.0, min(1.0, rate))
    
    def set_acquired_component_inheritance_rate(self, rate: float):
        """设置后天获得组件的遗传率
        
        参数:
            rate: float - 后天获得组件的遗传率（0-1之间）
        """
        self.acquired_component_inheritance_rate = max(0.0, min(1.0, rate))